"""Command execution engine for PruneJuice."""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
import subprocess
import json
import logging
import os

from .database import Database
from .models import CommandDefinition, ExecutionEvent, StepStatus, ExecutionResult, StepError
from .state import StateManager
from ..commands.loader import CommandLoader
from ..integrations.plum import PlumIntegration
from ..integrations.pots import PotsIntegration
from ..utils.artifacts import ArtifactStore

logger = logging.getLogger(__name__)


class StepExecutor:
    """Executes individual steps with proper isolation."""
    
    def __init__(self, builtin_steps: Dict[str, callable]):
        """Initialize step executor with built-in steps."""
        self.builtin_steps = builtin_steps
    
    async def execute(
        self,
        step_name: str,
        context: Dict[str, Any],
        timeout: int = 300
    ) -> Tuple[bool, str]:
        """Execute a step and return (success, output)."""
        if step_name in self.builtin_steps:
            # Execute built-in step
            try:
                result = await asyncio.wait_for(
                    self.builtin_steps[step_name](context),
                    timeout=timeout
                )
                return True, str(result)
            except asyncio.TimeoutError:
                return False, f"Step '{step_name}' timed out after {timeout}s"
            except Exception as e:
                return False, f"Step '{step_name}' failed: {e}"
        else:
            # Look for custom step script
            step_paths = [
                context['project_path'] / ".prj" / "steps" / f"{step_name}.py",
                context['project_path'] / ".prj" / "steps" / f"{step_name}.sh",
            ]
            
            for step_path in step_paths:
                if step_path.exists():
                    return await self._execute_script(step_path, context, timeout)
            
            # Fallback to template steps
            try:
                from importlib import resources
                template_steps = resources.files("prunejuice.template_steps")
                for ext in [".py", ".sh"]:
                    template_step = template_steps / f"{step_name}{ext}"
                    if template_step.is_file():
                        # Copy template step to temporary location and execute
                        import tempfile
                        with tempfile.NamedTemporaryFile(mode='w', suffix=ext, delete=False) as tmp:
                            tmp.write(template_step.read_text())
                            tmp.flush()
                            temp_path = Path(tmp.name)
                            temp_path.chmod(0o755)
                            try:
                                return await self._execute_script(temp_path, context, timeout)
                            finally:
                                temp_path.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to load template step {step_name}: {e}")
            
            return False, f"Step '{step_name}' not found"
    
    async def _execute_script(
        self,
        script_path: Path,
        context: Dict[str, Any],
        timeout: int
    ) -> Tuple[bool, str]:
        """Execute external script with context."""
        env = os.environ.copy()
        
        # Add context to environment
        for key, value in context.items():
            if key == 'args' and isinstance(value, dict):
                # Flatten args into individual environment variables
                for arg_key, arg_value in value.items():
                    if isinstance(arg_value, (str, int, float, bool)):
                        env[f"PRUNEJUICE_ARG_{arg_key.upper()}"] = str(arg_value)
            elif isinstance(value, (str, int, float, bool)):
                env[f"PRUNEJUICE_{key.upper()}"] = str(value)
        
        try:
            if script_path.suffix == ".py":
                cmd = ["python", str(script_path)]
            else:
                cmd = ["bash", str(script_path)]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=context.get('working_directory', context['project_path'])
            )
            
            stdout, _ = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
            
            return proc.returncode == 0, stdout.decode()
        except asyncio.TimeoutError:
            return False, f"Script timed out after {timeout}s"
        except Exception as e:
            return False, f"Script execution failed: {e}"


class Executor:
    """Main command orchestration engine - simple sequential execution."""
    
    def __init__(self, settings):
        """Initialize executor with settings."""
        self.settings = settings
        self.db = Database(settings.db_path)
        self.loader = CommandLoader()
        self.state = StateManager(self.db)
        self.artifacts = ArtifactStore(settings.artifacts_dir)
        self.plum = PlumIntegration(settings.plum_path)
        self.pots = PotsIntegration(settings.pots_path)
        
        # Register built-in steps
        self.step_executor = StepExecutor({
            "setup-environment": self._setup_environment,
            "validate-prerequisites": self._validate_prerequisites,
            "create-worktree": self._create_worktree,
            "start-session": self._start_session,
            "gather-context": self._gather_context,
            "store-artifacts": self._store_artifacts,
            "cleanup": self._cleanup,
        })
    
    async def execute_command(
        self,
        command_name: str,
        project_path: Path,
        args: Dict[str, Any],
        dry_run: bool = False
    ) -> ExecutionResult:
        """Execute a command with full lifecycle management."""
        # Initialize database if needed
        try:
            await self.db.initialize()
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
        
        # Load command definition
        command = await self.loader.load_command(command_name, project_path)
        if not command:
            return ExecutionResult(
                success=False,
                error=f"Command '{command_name}' not found"
            )
        
        # Validate arguments
        validation_errors = self._validate_arguments(command, args)
        if validation_errors:
            return ExecutionResult(
                success=False,
                error=f"Invalid arguments: {', '.join(validation_errors)}"
            )
        
        # Create execution context
        session_id = f"{project_path.name}-{int(datetime.now().timestamp())}"
        artifact_dir = self.artifacts.create_session_dir(
            project_path, session_id, command_name
        )
        
        context = {
            'command': command,
            'project_path': project_path,
            'session_id': session_id,
            'artifact_dir': artifact_dir,
            'args': args,
            'environment': {**os.environ, **command.environment},
            'working_directory': command.working_directory or str(project_path)
        }
        
        if dry_run:
            return self._dry_run(command, context)
        
        # Start event tracking
        try:
            event_id = await self.db.start_event(
                command=command_name,
                project_path=str(project_path),
                session_id=session_id,
                artifacts_path=str(artifact_dir)
            )
            context['event_id'] = event_id
        except Exception as e:
            logger.warning(f"Failed to start event tracking: {e}")
            context['event_id'] = None
        
        # Execute command with simple sequential execution
        try:
            # Execute all steps sequentially
            all_steps = command.pre_steps + command.steps + command.post_steps
            
            for i, step in enumerate(all_steps):
                logger.info(f"Executing step {i+1}/{len(all_steps)}: {step}")
                
                await self.state.begin_step(session_id, step)
                success, output = await self.step_executor.execute(
                    step, context, command.timeout
                )
                
                # Store step output as artifact
                if output:
                    self.artifacts.store_content(
                        artifact_dir, output, f"step-{i+1}-{step}.log", "logs"
                    )
                
                if success:
                    await self.state.complete_step(session_id, step, output)
                else:
                    await self.state.fail_step(session_id, step, output)
                    raise StepError(f"Step '{step}' failed: {output}")
            
            # Mark success
            if context.get('event_id'):
                try:
                    await self.db.end_event(context['event_id'], "completed", 0)
                except Exception as e:
                    logger.warning(f"Failed to mark event as completed: {e}")
            
            return ExecutionResult(
                success=True,
                artifacts_path=str(artifact_dir)
            )
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            
            # Run cleanup steps
            for step in command.cleanup_on_failure:
                try:
                    await self.step_executor.execute(step, context, 60)
                except Exception:
                    logger.error(f"Cleanup step '{step}' failed")
            
            # Mark failure
            if context.get('event_id'):
                try:
                    await self.db.end_event(context['event_id'], "failed", 1, str(e))
                except Exception as db_e:
                    logger.warning(f"Failed to mark event as failed: {db_e}")
            
            return ExecutionResult(
                success=False,
                error=str(e),
                artifacts_path=str(artifact_dir)
            )
    
    def _validate_arguments(self, command: CommandDefinition, args: Dict[str, Any]) -> List[str]:
        """Validate command arguments."""
        errors = []
        
        for arg_def in command.arguments:
            if arg_def.required and arg_def.name not in args:
                errors.append(f"Required argument '{arg_def.name}' missing")
        
        return errors
    
    def _dry_run(self, command: CommandDefinition, context: Dict[str, Any]) -> ExecutionResult:
        """Perform a dry run showing what would be executed."""
        output = f"Dry run for command: {command.name}\n"
        output += f"Description: {command.description}\n"
        output += f"Project path: {context['project_path']}\n"
        output += f"Arguments: {context['args']}\n\n"
        
        all_steps = command.pre_steps + command.steps + command.post_steps
        output += f"Steps to execute ({len(all_steps)}):\n"
        for i, step in enumerate(all_steps, 1):
            output += f"  {i}. {step}\n"
        
        if command.cleanup_on_failure:
            output += f"\nCleanup steps on failure:\n"
            for step in command.cleanup_on_failure:
                output += f"  - {step}\n"
        
        return ExecutionResult(
            success=True,
            output=output
        )
    
    # Built-in step implementations
    async def _setup_environment(self, context: Dict[str, Any]) -> str:
        """Setup execution environment."""
        artifact_dir = context['artifact_dir']
        artifact_dir.mkdir(parents=True, exist_ok=True)
        (artifact_dir / "logs").mkdir(exist_ok=True)
        (artifact_dir / "outputs").mkdir(exist_ok=True)
        return "Environment setup complete"
    
    async def _validate_prerequisites(self, context: Dict[str, Any]) -> str:
        """Validate prerequisites for command execution."""
        issues = []
        
        # Check if we're in a git repository
        project_path = context['project_path']
        if not (project_path / ".git").exists():
            issues.append("Not in a git repository")
        
        # Check for required tools
        if context['command'].name.startswith('worktree-') and not self.plum.is_available():
            issues.append("Plum worktree manager not available")
        
        if issues:
            raise RuntimeError(f"Prerequisites not met: {', '.join(issues)}")
        
        return "Prerequisites validated"
    
    async def _create_worktree(self, context: Dict[str, Any]) -> str:
        """Create worktree via plum integration."""
        branch_name = context['args'].get(
            'branch_name',
            f"pj-{context['command'].name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        
        worktree_path = await self.plum.create_worktree(
            context['project_path'],
            branch_name
        )
        
        context['worktree_path'] = worktree_path
        context['branch_name'] = branch_name
        return f"Created worktree at {worktree_path}"
    
    async def _start_session(self, context: Dict[str, Any]) -> str:
        """Start tmux session via pots integration."""
        session_name = await self.pots.create_session(
            context.get('worktree_path', context['project_path']),
            context['command'].name
        )
        
        context['tmux_session'] = session_name
        return f"Started tmux session: {session_name}"
    
    async def _gather_context(self, context: Dict[str, Any]) -> str:
        """Gather context information for the command."""
        # This could be expanded to gather git status, recent commits, etc.
        project_path = context['project_path']
        
        context_info = {
            "project_name": project_path.name,
            "git_branch": "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Try to get git branch
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            context_info["git_branch"] = result.stdout.strip()
        except subprocess.CalledProcessError:
            pass
        
        # Store context as artifact
        self.artifacts.store_content(
            context['artifact_dir'],
            json.dumps(context_info, indent=2),
            "context.json",
            "specs"
        )
        
        return f"Context gathered for {context_info['project_name']}"
    
    async def _store_artifacts(self, context: Dict[str, Any]) -> str:
        """Store artifacts for the session."""
        # Mark artifacts in database
        if context.get('event_id'):
            try:
                await self.db.store_artifact(
                    context['event_id'],
                    "session",
                    str(context['artifact_dir']),
                    0
                )
            except Exception as e:
                logger.warning(f"Failed to store artifact info: {e}")
        
        return f"Artifacts stored in {context['artifact_dir']}"
    
    async def _cleanup(self, context: Dict[str, Any]) -> str:
        """Cleanup session resources."""
        await self.state.cleanup_session(context['session_id'])
        return "Cleanup completed"