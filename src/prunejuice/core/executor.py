"""Command execution engine for PruneJuice."""

import asyncio
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import logging
import os

from .database import Database
from .models import ActionDefintion, ExecutionResult, CommandStep, StepType
from .state import StateManager
from .session import ActionContext
from .builtin_steps import BuiltinSteps
from .commands import create_action
from ..commands.loader import CommandLoader
from ..utils.artifacts import ArtifactStore
from ..worktree_utils import GitWorktreeManager
from ..env_utils import prepare_clean_environment, is_uv_command

logger = logging.getLogger(__name__)


class StepExecutor:
    """Executes individual steps with proper isolation."""

    def __init__(self, builtin_steps: Dict[str, callable]):
        """Initialize step executor with built-in steps."""
        self.builtin_steps = builtin_steps

    async def execute(
        self, step: CommandStep, context: Dict[str, Any], timeout: int = 300
    ) -> Tuple[bool, str]:
        """Execute a step and return (success, output)."""
        # Use the minimum of command timeout and step timeout (favor more restrictive)
        step_timeout = min(timeout, step.timeout) if step.timeout > 0 else timeout

        if step.type == StepType.BUILTIN:
            return await self._execute_builtin(step, context, step_timeout)
        elif step.type == StepType.SCRIPT:
            return await self._execute_script_step(step, context, step_timeout)
        elif step.type == StepType.SHELL:
            return await self._execute_shell_command(step, context, step_timeout)
        else:
            return False, f"Unknown step type: {step.type}"

    async def _execute_builtin(
        self, step: CommandStep, context: Dict[str, Any], timeout: int
    ) -> Tuple[bool, str]:
        """Execute a built-in step."""
        if step.action in self.builtin_steps:
            try:
                result = await asyncio.wait_for(
                    self.builtin_steps[step.action](context), timeout=timeout
                )
                return True, str(result)
            except asyncio.TimeoutError:
                return False, f"Step '{step.name}' timeout after {timeout}s"
            except Exception as e:
                return False, f"Step '{step.name}' failed: {e}"
        else:
            # Look for custom step script
            step_paths = [
                context["project_path"] / ".prj" / "steps" / f"{step.action}.py",
                context["project_path"] / ".prj" / "steps" / f"{step.action}.sh",
            ]

            for step_path in step_paths:
                if step_path.exists():
                    return await self._execute_script(step_path, context, timeout)

            # Fallback to template steps
            try:
                from importlib import resources

                template_steps = resources.files("prunejuice.template_steps")
                for ext in [".py", ".sh"]:
                    template_step = template_steps / f"{step.action}{ext}"
                    if template_step.is_file():
                        # Copy template step to temporary location and execute
                        import tempfile

                        with tempfile.NamedTemporaryFile(
                            mode="w", suffix=ext, delete=False
                        ) as tmp:
                            tmp.write(template_step.read_text())
                            tmp.flush()
                            temp_path = Path(tmp.name)
                            temp_path.chmod(0o755)
                            try:
                                return await self._execute_script(
                                    temp_path, context, timeout
                                )
                            finally:
                                temp_path.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to load template step {step.action}: {e}")

            return False, f"Step '{step.name}' not found"

    async def _execute_script_step(
        self, step: CommandStep, context: Dict[str, Any], timeout: int
    ) -> Tuple[bool, str]:
        """Execute a script step."""
        script_path = Path(step.action)
        if not script_path.is_absolute():
            # Look for script in project steps directory
            script_path = context["project_path"] / ".prj" / "steps" / step.action

        if script_path.exists():
            return await self._execute_script(script_path, context, timeout)
        else:
            return False, f"Script not found: {step.action}"

    async def _execute_shell_command(
        self, step: CommandStep, context: Dict[str, Any], timeout: int
    ) -> Tuple[bool, str]:
        """Execute a shell command directly."""
        # Use clean environment for uv commands, regular environment otherwise
        if is_uv_command(step.action):
            env = prepare_clean_environment()
        else:
            env = os.environ.copy()

        # Add context to environment
        for key, value in context.items():
            if key == "args" and isinstance(value, dict):
                # Flatten args into individual environment variables
                for arg_key, arg_value in value.items():
                    if isinstance(arg_value, (str, int, float, bool)):
                        env[f"PRUNEJUICE_ARG_{arg_key.upper()}"] = str(arg_value)
            elif isinstance(value, (str, int, float, bool)):
                env[f"PRUNEJUICE_{key.upper()}"] = str(value)

        # Add step args to environment
        for key, value in step.args.items():
            if isinstance(value, (str, int, float, bool)):
                env[f"PRUNEJUICE_STEP_{key.upper()}"] = str(value)

        try:
            # Execute using bash -c for full shell support
            proc = await asyncio.create_subprocess_exec(
                "bash",
                "-c",
                step.action,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=context.get("working_directory", context["project_path"]),
            )

            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)

            return proc.returncode == 0, stdout.decode()
        except asyncio.TimeoutError:
            return False, f"Command timeout after {timeout}s"
        except Exception as e:
            return False, f"Command execution failed: {e}"

    async def _execute_script(
        self, script_path: Path, context: Dict[str, Any], timeout: int
    ) -> Tuple[bool, str]:
        """Execute external script with context."""
        # Check if the script contains uv commands by reading its content
        try:
            script_content = script_path.read_text()
            if any(is_uv_command(line.strip()) for line in script_content.split("\n")):
                env = prepare_clean_environment()
            else:
                env = os.environ.copy()
        except Exception:
            # Fallback to regular environment if we can't read the script
            env = os.environ.copy()

        # Add context to environment
        for key, value in context.items():
            if key == "args" and isinstance(value, dict):
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
                cwd=context.get("working_directory", context["project_path"]),
            )

            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)

            return proc.returncode == 0, stdout.decode()
        except asyncio.TimeoutError:
            return False, f"Script timeout after {timeout}s"
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

        # Initialize built-in steps
        self.builtin_steps = BuiltinSteps(self.db, self.artifacts)

        # Register built-in steps with step executor
        self.step_executor = StepExecutor(self.builtin_steps.get_step_registry())

    async def execute_command(
        self,
        command_name: str,
        project_path: Path,
        args: Dict[str, Any],
        dry_run: bool = False,
    ) -> ExecutionResult:
        """Execute a command with full lifecycle management."""
        # Initialize database if needed
        try:
            await self.db.initialize()
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")

        # Load command definition
        command = self.loader.load_command(command_name, project_path)
        if not command:
            return ExecutionResult(
                success=False, error=f"Command '{command_name}' not found"
            )

        # Validate arguments
        validation_errors = self._validate_arguments(command, args)
        if validation_errors:
            return ExecutionResult(
                success=False,
                error=f"Invalid arguments: {', '.join(validation_errors)}",
            )

        # Create session
        session_id = f"{project_path.name}-{int(datetime.now().timestamp())}"
        artifact_dir = self.artifacts.create_session_dir(
            project_path, session_id, command_name
        )

        context = ActionContext(
            id=session_id,
            command_name=command_name,
            project_path=project_path,
            artifact_dir=artifact_dir,
        )

        # Store command arguments in context shared data
        context.set_shared_data("args", args)
        context.set_shared_data("environment", {**os.environ, **command.environment})

        if dry_run:
            return self._dry_run(command, context)

        # Detect current worktree context
        worktree_name = None
        try:
            manager = GitWorktreeManager(project_path)
            if manager.is_git_repository():
                current_path = Path.cwd()
                worktree_info = manager.get_worktree_info(current_path)
                if worktree_info:
                    # Extract branch name from refs/heads/branch-name format
                    branch = worktree_info.get("branch", "")
                    if branch.startswith("refs/heads/"):
                        branch = branch[11:]  # Remove 'refs/heads/' prefix
                    # Only set worktree_name if not in main worktree
                    if current_path != manager.get_main_worktree_path():
                        worktree_name = branch
        except Exception as e:
            logger.debug(f"Failed to detect worktree context: {e}")

        # Start event tracking
        try:
            event_id = await self.db.start_event(
                command=command_name,
                project_path=str(project_path),
                session_id=session_id,
                artifacts_path=str(artifact_dir),
                worktree_name=worktree_name,
            )
            context.set_shared_data("event_id", event_id)
        except Exception as e:
            logger.warning(f"Failed to start event tracking: {e}")
            context.set_shared_data("event_id", None)

        # Create appropriate command type and execute
        try:
            command_instance = create_action(
                command, context, self.step_executor, self.builtin_steps
            )
            result = await command_instance.execute()

            # Mark success in event tracking
            event_id = context.get_shared_data("event_id")
            if event_id:
                try:
                    status = "completed" if result.success else "failed"
                    await self.db.end_event(
                        event_id, status, 0 if result.success else 1
                    )
                except Exception as e:
                    logger.warning(f"Failed to mark event as {status}: {e}")

            return result

        except Exception as e:
            logger.error(f"Command execution failed: {e}")

            # Mark failure in event tracking
            event_id = context.get_shared_data("event_id")
            if event_id:
                try:
                    await self.db.end_event(event_id, "failed", 1, str(e))
                except Exception as db_e:
                    logger.warning(f"Failed to mark event as failed: {db_e}")

            return ExecutionResult(
                success=False, error=str(e), artifacts_path=str(context.artifact_dir)
            )

    def _validate_arguments(
        self, command: ActionDefintion, args: Dict[str, Any]
    ) -> List[str]:
        """Validate command arguments."""
        errors = []

        for arg_def in command.arguments:
            if arg_def.required and arg_def.name not in args:
                errors.append(f"Required argument '{arg_def.name}' missing")

        return errors

    def _dry_run(
        self, command: ActionDefintion, context: ActionContext
    ) -> ExecutionResult:
        """Perform a dry run showing what would be executed."""
        output = f"Dry run for command: {command.name}\n"
        output += f"Description: {command.description}\n"
        output += f"Project path: {context.project_path}\n"
        output += f"Arguments: {context.get_shared_data('args')}\n\n"

        all_steps = command.get_all_steps()
        output += f"Steps to execute ({len(all_steps)}):\n"
        for i, step in enumerate(all_steps, 1):
            output += f"  {i}. {step.name} ({step.type.value}): {step.action}\n"

        if command.cleanup_on_failure:
            output += "\nCleanup steps on failure:\n"
            for step_item in command.cleanup_on_failure:
                if isinstance(step_item, str):
                    step = CommandStep.from_string(step_item)
                else:
                    step = step_item
                output += f"  - {step.name} ({step.type.value}): {step.action}\n"

        return ExecutionResult(success=True, output=output)
