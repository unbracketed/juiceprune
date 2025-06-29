"""Built-in step implementations extracted from Executor class."""

from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import json
import logging

from .session import Session
from ..worktree_utils import GitWorktreeManager

logger = logging.getLogger(__name__)


class BuiltinSteps:
    """Built-in step implementations - extracted from Executor class (lines 390-496)"""

    def __init__(self, db, artifacts):
        self.db = db
        self.artifacts = artifacts

    async def setup_environment(self, session: Session) -> str:
        """Setup execution environment."""
        artifact_dir = session.artifact_dir
        artifact_dir.mkdir(parents=True, exist_ok=True)
        (artifact_dir / "logs").mkdir(exist_ok=True)
        (artifact_dir / "outputs").mkdir(exist_ok=True)
        return "Environment setup complete"

    async def validate_prerequisites(self, session: Session) -> str:
        """Validate prerequisites for command execution."""
        issues = []

        # Check if we're in a git repository
        project_path = session.project_path
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

    async def create_worktree(self, session: Session) -> str:
        """Create worktree using native implementation."""
        branch_name = session.get_shared_data(
            "branch_name",
            f"pj-{session.command_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        )

        worktree_path = await session.create_worktree(branch_name)
        session.set_shared_data("branch_name", branch_name)

        return f"Created worktree at {worktree_path}"

    async def start_session(self, session: Session) -> str:
        """Start tmux session using native implementation."""
        session_name = await session.create_tmux_session()
        return f"Started tmux session: {session_name}"

    async def gather_context(self, session: Session) -> str:
        """Gather context information for the command."""
        project_path = session.project_path

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
            session.artifact_dir,
            json.dumps(context_info, indent=2),
            "context.json",
            "specs",
        )

        session.set_shared_data("context_info", context_info)
        return f"Context gathered for {context_info['project_name']}"

    async def store_artifacts(self, session: Session) -> str:
        """Store artifacts for the session."""
        # Mark artifacts in database
        event_id = session.get_shared_data("event_id")
        if event_id:
            try:
                await self.db.store_artifact(
                    event_id, "session", str(session.artifact_dir), 0
                )
            except Exception as e:
                logger.warning(f"Failed to store artifact info: {e}")

        return f"Artifacts stored in {session.artifact_dir}"

    async def cleanup(self, session: Session) -> str:
        """Cleanup session resources."""
        # This would be implemented based on state manager requirements
        return "Cleanup completed"

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
        }

    def _wrap_session_method(self, session_method):
        """Wrap a session method to work with StepExecutor's context dict."""

        async def wrapper(context: Dict[str, Any]) -> str:
            # For now, we need to create a minimal Session from context
            # This is a transitional approach until we fully migrate StepExecutor
            from .session import Session, SessionStatus

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

            session = Session(
                id=context.get("session_id", "unknown"),
                command_name=context.get("command_name", "unknown"),
                project_path=project_path,
                artifact_dir=artifact_dir,
                status=SessionStatus.ACTIVE,
            )

            # Copy context data to session
            if "shared_data" in context:
                session.shared_data = context["shared_data"]
            if "args" in context:
                session.set_shared_data("args", context["args"])
            if "environment" in context:
                session.set_shared_data("environment", context["environment"])
            if "event_id" in context:
                session.set_shared_data("event_id", context["event_id"])
            if "worktree_path" in context and context["worktree_path"] is not None:
                session.worktree_path = Path(context["worktree_path"])
            if "tmux_session" in context and context["tmux_session"] is not None:
                session.tmux_session_name = context["tmux_session"]

            # Call the session method
            result = await session_method(session)

            # Update context with any changes from session
            if session.worktree_path:
                context["worktree_path"] = session.worktree_path
            if session.tmux_session_name:
                context["tmux_session"] = session.tmux_session_name
            context["shared_data"] = session.shared_data

            return result

        return wrapper
