"""Built-in step implementations extracted from Executor class."""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import json
import logging

from .session import ActionContext
from ..worktree_utils import GitWorktreeManager

logger = logging.getLogger(__name__)


class BuiltinSteps:
    """Built-in step implementations - extracted from Executor class (lines 390-496)"""

    def __init__(self, db, artifacts):
        self.db = db
        self.artifacts = artifacts

    async def setup_environment(self, context: ActionContext) -> str:
        """Setup execution environment."""
        artifact_dir = context.artifact_dir
        artifact_dir.mkdir(parents=True, exist_ok=True)
        (artifact_dir / "logs").mkdir(exist_ok=True)
        (artifact_dir / "outputs").mkdir(exist_ok=True)
        return "Environment setup complete"

    async def validate_prerequisites(self, context: ActionContext) -> str:
        """Validate prerequisites for command execution."""
        issues = []

        # Check if we're in a git repository
        project_path = context.project_path
        if project_path:
            try:
                manager = GitWorktreeManager(project_path)
                if not manager.is_git_repository():
                    issues.append("Not in a git repository")
            except Exception:
                issues.append("Not in a git repository")

        # Check for required tools (removed plum check - native implementation always available)

        if issues:
            raise RuntimeError(f"Prerequisites not met: {', '.join(issues)}")

        return "Prerequisites validated"

    async def create_worktree(self, context: ActionContext) -> str:
        """Create worktree using native implementation."""
        branch_name = context.get_shared_data(
            "branch_name",
            f"pj-{context.command_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        )

        worktree_path = await context.create_worktree(branch_name)
        context.set_shared_data("branch_name", branch_name)

        return f"Created worktree at {worktree_path}"

    async def start_session(self, context: ActionContext) -> str:
        """Start tmux session using native implementation."""
        session_name = await context.create_tmux_session()
        return f"Started tmux session: {session_name}"

    async def gather_context(self, context: ActionContext) -> str:
        """Gather context information for the command."""
        project_path = context.project_path

        context_info = {
            "project_name": project_path.name,
            "git_branch": "unknown",
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Try to get git branch
        try:
            manager = GitWorktreeManager(project_path)
            context_info["git_branch"] = manager.get_current_branch() or "unknown"
        except Exception:
            context_info["git_branch"] = "unknown"

        # Store context as artifact
        self.artifacts.store_content(
            context.artifact_dir,
            json.dumps(context_info, indent=2),
            "context.json",
            "specs",
        )

        context.set_shared_data("context_info", context_info)
        return f"Context gathered for {context_info['project_name']}"

    async def store_artifacts(self, context: ActionContext) -> str:
        """Store artifacts for the action context."""
        # Mark artifacts in database
        event_id = context.get_shared_data("event_id")
        if event_id:
            try:
                await self.db.store_artifact(
                    event_id, "session", str(context.artifact_dir), 0
                )
            except Exception as e:
                logger.warning(f"Failed to store artifact info: {e}")

        return f"Artifacts stored in {context.artifact_dir}"

    async def cleanup(self, context: ActionContext) -> str:
        """Cleanup action context resources."""
        # This would be implemented based on state manager requirements
        return "Cleanup completed"

    async def start_worktree_session(self, context: ActionContext) -> str:
        """Create a worktree and start a tmux session in it, optionally attaching."""
        # Get arguments
        args = context.get_shared_data("args", {})
        name = args.get("name")
        base_branch = args.get("base_branch", "main")
        no_attach = args.get("no_attach", False)

        if not name:
            raise ValueError("'name' argument is required for start command")

        # Create worktree with the specified name
        logger.info(f"Creating worktree '{name}' from base branch '{base_branch}'")
        worktree_path = await context.create_worktree(name, base_branch)
        context.set_shared_data("branch_name", name)
        logger.info(f"Created worktree at {worktree_path}")

        # Create tmux session in the worktree
        logger.info(f"Creating tmux session for worktree '{name}'")
        session_name = await context.create_tmux_session()
        logger.info(f"Created tmux session: {session_name}")

        # Attach to the session if requested
        if not no_attach:
            logger.info(f"Attaching to tmux session: {session_name}")
            from ..session_utils import TmuxManager

            tmux = TmuxManager()
            tmux.attach_session(session_name)
            return (
                f"Attached to session '{session_name}' in worktree at {worktree_path}"
            )
        else:
            return f"Created worktree at {worktree_path} and session '{session_name}' (not attached)"

    def get_step_registry(self) -> Dict[str, callable]:
        """Get the registry of built-in steps for StepExecutor."""
        return {
            "setup-environment": self._wrap_session_method(self.setup_environment),
            "validate-prerequisites": self._wrap_session_method(
                self.validate_prerequisites
            ),
            "create-worktree": self._wrap_session_method(self.create_worktree),
            "start-session": self._wrap_session_method(self.start_session),
            "gather-context": self._wrap_session_method(self.gather_context),
            "store-artifacts": self._wrap_session_method(self.store_artifacts),
            "cleanup": self._wrap_session_method(self.cleanup),
            "start-worktree-session": self._wrap_session_method(
                self.start_worktree_session
            ),
        }

    def _wrap_session_method(self, context_method):
        """Wrap an action context method to work with StepExecutor's context dict."""

        async def wrapper(context: Dict[str, Any]) -> str:
            # For now, we need to create a minimal ActionContext from context
            # This is a transitional approach until we fully migrate StepExecutor
            from .session import ActionContext, ActionStatus

            # Handle potential None values in context
            project_path = context.get("project_path")
            if project_path is None:
                project_path = Path(".")
            elif not isinstance(project_path, Path):
                project_path = Path(project_path)

            artifact_dir = context.get("artifact_dir")
            if artifact_dir is None:
                artifact_dir = Path(".")
            elif not isinstance(artifact_dir, Path):
                artifact_dir = Path(artifact_dir)

            action_context = ActionContext(
                id=context.get("session_id", "unknown"),
                action_name=context.get("action_name", "unknown"),
                project_path=project_path,
                artifact_dir=artifact_dir,
                status=ActionStatus.ACTIVE,
            )

            # Copy context data to action context
            if "shared_data" in context:
                action_context.shared_data = context["shared_data"]
            if "args" in context:
                action_context.set_shared_data("args", context["args"])
            if "environment" in context:
                action_context.set_shared_data("environment", context["environment"])
            if "event_id" in context:
                action_context.set_shared_data("event_id", context["event_id"])
            if "worktree_path" in context and context["worktree_path"] is not None:
                action_context.worktree_path = Path(context["worktree_path"])
            if "tmux_session" in context and context["tmux_session"] is not None:
                action_context.tmux_session_name = context["tmux_session"]

            # Call the action context method
            result = await context_method(action_context)

            # Update context with any changes from action context
            if action_context.worktree_path:
                context["worktree_path"] = action_context.worktree_path
            if action_context.tmux_session_name:
                context["tmux_session"] = action_context.tmux_session_name
            context["shared_data"] = action_context.shared_data

            return result

        return wrapper
