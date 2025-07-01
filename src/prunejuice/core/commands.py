"""Base Action hierarchy for automatic lifecycle management."""

from abc import ABC, abstractmethod
import logging

from .models import CommandDefinition, ExecutionResult
from .session import ActionContext, ActionStatus

logger = logging.getLogger(__name__)


class BaseAction(ABC):
    """Base interface for all actions"""

    def __init__(
        self,
        definition: CommandDefinition,
        context: ActionContext,
        step_executor,
        builtin_steps,
    ):
        self.definition = definition
        self.context = context
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
                logger.info(f"Executing step {i + 1}/{len(all_steps)}: {step.name}")

                success, output = await self.step_executor.execute(
                    step, self.context.get_context(), self.definition.timeout
                )

                # Store step output as artifact
                if output:
                    self.builtin_steps.artifacts.store_content(
                        self.context.artifact_dir,
                        output,
                        f"step-{i + 1}-{step.name}.log",
                        "logs",
                    )

                # Record step result in session
                self.context.add_step_result(step.name, success, output)

                if not success:
                    self.context.status = ActionStatus.FAILED
                    raise RuntimeError(f"Step '{step.name}' failed: {output}")

            self.context.status = ActionStatus.COMPLETED
            return ExecutionResult(
                success=True, artifacts_path=str(self.context.artifact_dir)
            )

        except Exception as e:
            self.context.status = ActionStatus.FAILED

            # Run cleanup steps
            for step in self.definition.cleanup_on_failure:
                try:
                    await self.step_executor.execute(
                        step, self.context.get_context(), 60
                    )
                except Exception:
                    logger.error(f"Cleanup step '{step}' failed")

            return ExecutionResult(
                success=False,
                error=str(e),
                artifacts_path=str(self.context.artifact_dir),
            )


class StandardAction(BaseAction):
    """Standard action execution without automatic session/worktree management"""

    async def execute(self) -> ExecutionResult:
        """Execute steps directly"""
        return await self._run_steps()


class SessionAction(BaseAction):
    """Action that automatically manages tmux session lifecycle"""

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
        logger.info(f"Creating tmux session for action: {self.definition.name}")
        await self.builtin_steps.start_session(self.context)

    async def _cleanup_session(self):
        """Cleanup tmux session"""
        if self.context.tmux_session_name:
            logger.info(f"Cleaning up tmux session: {self.context.tmux_session_name}")
            try:
                # Use pots integration to kill session
                success = await self.builtin_steps.pots.kill_session(
                    self.context.tmux_session_name
                )
                if not success:
                    logger.warning(
                        f"Failed to cleanup session: {self.context.tmux_session_name}"
                    )
            except Exception as e:
                logger.error(f"Error cleaning up session: {e}")


class WorktreeAction(SessionAction):
    """Action that automatically manages worktree + session lifecycle"""

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
        logger.info(f"Creating worktree for action: {self.definition.name}")
        await self.builtin_steps.create_worktree(self.context)

    async def _cleanup_worktree(self):
        """Cleanup git worktree"""
        if self.context.worktree_path:
            logger.info(f"Cleaning up worktree: {self.context.worktree_path}")
            try:
                # Use plum integration to remove worktree
                success = await self.builtin_steps.plum.remove_worktree(
                    self.context.project_path, self.context.worktree_path
                )
                if not success:
                    logger.warning(
                        f"Failed to cleanup worktree: {self.context.worktree_path}"
                    )
            except Exception as e:
                logger.error(f"Error cleaning up worktree: {e}")


def create_action(
    definition: CommandDefinition, context: ActionContext, step_executor, builtin_steps
) -> BaseAction:
    """Factory function to create appropriate action type based on definition"""

    # Determine command type based on steps or metadata
    all_steps = definition.get_all_steps()
    step_actions = [step.action for step in all_steps] + [
        step.name for step in all_steps
    ]

    needs_worktree = any(step_name in ["create-worktree"] for step_name in step_actions)

    needs_session = any(
        step_name in ["start-session", "session-create"] for step_name in step_actions
    )

    # Check if command name indicates worktree/session needs
    if (
        "worktree" in definition.name.lower()
        or "feature-branch" in definition.name.lower()
    ):
        needs_worktree = True

    if "session" in definition.name.lower() or needs_worktree:
        needs_session = True

    if needs_worktree:
        logger.info(f"Creating WorktreeAction for: {definition.name}")
        return WorktreeAction(definition, context, step_executor, builtin_steps)
    elif needs_session:
        logger.info(f"Creating SessionAction for: {definition.name}")
        return SessionAction(definition, context, step_executor, builtin_steps)
    else:
        logger.info(f"Creating StandardAction for: {definition.name}")
        return StandardAction(definition, context, step_executor, builtin_steps)
