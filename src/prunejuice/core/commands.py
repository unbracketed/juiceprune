"""Base Command hierarchy for automatic lifecycle management."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any
import logging

from .models import CommandDefinition, ExecutionResult
from .session import Session, SessionStatus

logger = logging.getLogger(__name__)


class BaseCommand(ABC):
    """Base interface for all commands"""
    
    def __init__(self, definition: CommandDefinition, session: Session, step_executor, builtin_steps):
        self.definition = definition
        self.session = session
        self.step_executor = step_executor
        self.builtin_steps = builtin_steps
    
    @abstractmethod
    async def execute(self) -> ExecutionResult:
        """Execute the command"""
        pass
    
    async def _run_steps(self) -> ExecutionResult:
        """Common step execution logic"""
        try:
            all_steps = self.definition.get_all_steps()
            
            for i, step in enumerate(all_steps):
                logger.info(f"Executing step {i+1}/{len(all_steps)}: {step.name}")
                
                success, output = await self.step_executor.execute(
                    step, self.session.get_context(), self.definition.timeout
                )
                
                # Store step output as artifact
                if output:
                    self.builtin_steps.artifacts.store_content(
                        self.session.artifact_dir, 
                        output, 
                        f"step-{i+1}-{step.name}.log", 
                        "logs"
                    )
                
                # Record step result in session
                self.session.add_step_result(step.name, success, output)
                
                if not success:
                    self.session.status = SessionStatus.FAILED
                    raise RuntimeError(f"Step '{step.name}' failed: {output}")
            
            self.session.status = SessionStatus.COMPLETED
            return ExecutionResult(
                success=True,
                artifacts_path=str(self.session.artifact_dir)
            )
            
        except Exception as e:
            self.session.status = SessionStatus.FAILED
            
            # Run cleanup steps
            for step in self.definition.cleanup_on_failure:
                try:
                    await self.step_executor.execute(step, self.session.get_context(), 60)
                except Exception:
                    logger.error(f"Cleanup step '{step}' failed")
            
            return ExecutionResult(
                success=False,
                error=str(e),
                artifacts_path=str(self.session.artifact_dir)
            )


class StandardCommand(BaseCommand):
    """Standard command execution without automatic session/worktree management"""
    
    async def execute(self) -> ExecutionResult:
        """Execute steps directly"""
        return await self._run_steps()


class SessionCommand(BaseCommand):
    """Command that automatically manages tmux session lifecycle"""
    
    async def execute(self) -> ExecutionResult:
        """Execute with automatic session lifecycle management"""
        try:
            # Create detached tmux session automatically
            await self._create_session()
            
            # Run steps inside the session
            return await self._run_steps()
            
        finally:
            # Always cleanup session
            await self._cleanup_session()
    
    async def _create_session(self):
        """Create detached tmux session"""
        logger.info(f"Creating tmux session for command: {self.definition.name}")
        await self.builtin_steps.start_session(self.session)
    
    async def _cleanup_session(self):
        """Cleanup tmux session"""
        if self.session.tmux_session_name:
            logger.info(f"Cleaning up tmux session: {self.session.tmux_session_name}")
            try:
                # Use pots integration to kill session
                success = await self.builtin_steps.pots.kill_session(self.session.tmux_session_name)
                if not success:
                    logger.warning(f"Failed to cleanup session: {self.session.tmux_session_name}")
            except Exception as e:
                logger.error(f"Error cleaning up session: {e}")


class WorktreeCommand(SessionCommand):
    """Command that automatically manages worktree + session lifecycle"""
    
    async def execute(self) -> ExecutionResult:
        """Execute with automatic worktree and session lifecycle management"""
        try:
            # Create worktree automatically
            await self._create_worktree()
            
            # Create detached tmux session in the worktree
            await self._create_session()
            
            # Run steps inside the session
            return await self._run_steps()
            
        finally:
            # Always cleanup in reverse order
            await self._cleanup_session()
            await self._cleanup_worktree()
    
    async def _create_worktree(self):
        """Create git worktree automatically"""
        logger.info(f"Creating worktree for command: {self.definition.name}")
        await self.builtin_steps.create_worktree(self.session)
    
    async def _cleanup_worktree(self):
        """Cleanup git worktree"""
        if self.session.worktree_path:
            logger.info(f"Cleaning up worktree: {self.session.worktree_path}")
            try:
                # Use plum integration to remove worktree
                success = await self.builtin_steps.plum.remove_worktree(
                    self.session.project_path, 
                    self.session.worktree_path
                )
                if not success:
                    logger.warning(f"Failed to cleanup worktree: {self.session.worktree_path}")
            except Exception as e:
                logger.error(f"Error cleaning up worktree: {e}")


def create_command(definition: CommandDefinition, session: Session, step_executor, builtin_steps) -> BaseCommand:
    """Factory function to create appropriate command type based on definition"""
    
    # Determine command type based on steps or metadata
    all_steps = definition.get_all_steps()
    step_actions = [step.action for step in all_steps] + [step.name for step in all_steps]
    
    needs_worktree = any(
        step_name in ['create-worktree'] 
        for step_name in step_actions
    )
    
    needs_session = any(
        step_name in ['start-session', 'session-create'] 
        for step_name in step_actions
    )
    
    # Check if command name indicates worktree/session needs
    if 'worktree' in definition.name.lower() or 'feature-branch' in definition.name.lower():
        needs_worktree = True
    
    if 'session' in definition.name.lower() or needs_worktree:
        needs_session = True
    
    if needs_worktree:
        logger.info(f"Creating WorktreeCommand for: {definition.name}")
        return WorktreeCommand(definition, session, step_executor, builtin_steps)
    elif needs_session:
        logger.info(f"Creating SessionCommand for: {definition.name}")
        return SessionCommand(definition, session, step_executor, builtin_steps)
    else:
        logger.info(f"Creating StandardCommand for: {definition.name}")
        return StandardCommand(definition, session, step_executor, builtin_steps)