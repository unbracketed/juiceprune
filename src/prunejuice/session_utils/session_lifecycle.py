"""Session lifecycle management and integration with worktrees."""

from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from .tmux_manager import TmuxManager

logger = logging.getLogger(__name__)


class SessionLifecycleManager:
    """Manages the complete lifecycle of tmux sessions for worktrees."""

    def __init__(self, tmux_manager: Optional[TmuxManager] = None):
        """Initialize with optional tmux manager.

        Args:
            tmux_manager: TmuxManager instance (creates new if None)
        """
        self.tmux = tmux_manager or TmuxManager()
        self.default_task = "dev"

    def create_session_for_worktree(
        self,
        worktree_path: Path,
        task_name: Optional[str] = None,
        auto_attach: bool = False,
    ) -> Optional[str]:
        """Create a tmux session for a specific worktree.

        Args:
            worktree_path: Path to the worktree
            task_name: Task identifier (defaults to 'dev')
            auto_attach: Whether to attach after creation

        Returns:
            Session name if successful, None otherwise
        """
        try:
            if not worktree_path.exists():
                logger.error(f"Worktree path does not exist: {worktree_path}")
                return None

            # Extract project and worktree names
            project_name = self._extract_project_name(worktree_path)
            worktree_name = self._extract_worktree_name(worktree_path)
            task = task_name or self.default_task

            # Generate session name
            session_name = self.tmux.format_session_name(
                project_name, worktree_name, task
            )

            # Check if session already exists
            if self.tmux.session_exists(session_name):
                logger.info(f"Session '{session_name}' already exists")
                return session_name

            # Create the session
            success = self.tmux.create_session(session_name, worktree_path, auto_attach)

            if success:
                logger.info(
                    f"Created session '{session_name}' for worktree {worktree_path}"
                )
                return session_name
            else:
                logger.error(f"Failed to create session for worktree {worktree_path}")
                return None

        except Exception as e:
            logger.error(f"Error creating session for worktree {worktree_path}: {e}")
            return None

    def cleanup_orphaned_sessions(
        self, project_filter: Optional[str] = None, dry_run: bool = False
    ) -> Dict[str, Any]:
        """Clean up sessions for non-existent worktrees.

        Args:
            project_filter: Only clean sessions for specific project
            dry_run: If True, show what would be cleaned without doing it

        Returns:
            Dictionary with cleanup results
        """
        results = {
            "checked": [],
            "orphaned": [],
            "cleaned": [],
            "failed": [],
            "total_checked": 0,
            "total_cleaned": 0,
            "total_failed": 0,
        }

        try:
            sessions = self.tmux.list_sessions()

            for session in sessions:
                session_name = session["name"]
                session_path = Path(session["path"])

                results["checked"].append(session_name)
                results["total_checked"] += 1

                # Apply project filter if specified
                if project_filter:
                    if not session_name.startswith(f"{project_filter}-"):
                        continue

                # Check if the session's working directory exists
                if not session_path.exists():
                    results["orphaned"].append(
                        {
                            "name": session_name,
                            "path": str(session_path),
                            "reason": "Working directory does not exist",
                        }
                    )

                    if not dry_run:
                        # Kill the orphaned session
                        if self.tmux.kill_session(session_name):
                            results["cleaned"].append(session_name)
                            results["total_cleaned"] += 1
                            logger.info(f"Cleaned orphaned session: {session_name}")
                        else:
                            results["failed"].append(
                                {
                                    "name": session_name,
                                    "error": "Failed to kill session",
                                }
                            )
                            results["total_failed"] += 1

            if dry_run:
                logger.info(
                    f"Dry run: Would clean {len(results['orphaned'])} orphaned sessions"
                )
            else:
                logger.info(
                    f"Cleanup complete: {results['total_cleaned']} cleaned, "
                    f"{results['total_failed']} failed"
                )

            return results

        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
            results["failed"].append({"error": str(e)})
            return results

    def list_project_sessions(
        self, project_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List sessions for a specific project or all projects.

        Args:
            project_name: Project name to filter by (optional)

        Returns:
            List of session information with parsed metadata
        """
        try:
            sessions = self.tmux.list_sessions()
            project_sessions = []

            for session in sessions:
                session_name = session["name"]

                # Parse session name to extract project info
                parsed = self._parse_session_name(session_name)

                # Apply project filter
                if project_name and parsed.get("project") != project_name:
                    continue

                # Add parsed information to session data
                enhanced_session = {
                    **session,
                    **parsed,
                    "working_dir_exists": Path(session["path"]).exists(),
                }

                project_sessions.append(enhanced_session)

            return project_sessions

        except Exception as e:
            logger.error(f"Error listing project sessions: {e}")
            return []

    def attach_to_session(self, session_name: str) -> bool:
        """Attach to a session with validation.

        Args:
            session_name: Name of the session to attach to

        Returns:
            True if successful, False otherwise
        """
        return self.tmux.attach_session(session_name)

    def kill_session(self, session_name: str) -> bool:
        """Kill a session with validation.

        Args:
            session_name: Name of the session to kill

        Returns:
            True if successful, False otherwise
        """
        return self.tmux.kill_session(session_name)

    def _extract_project_name(self, worktree_path: Path) -> str:
        """Extract project name from worktree path.

        Args:
            worktree_path: Path to the worktree

        Returns:
            Project name
        """
        # Try to extract from path structure
        # Assumes format like: /path/to/project-worktree or /path/to/worktrees/project-branch
        path_name = worktree_path.name

        # If it looks like project-branch, extract project part
        if "-" in path_name:
            parts = path_name.split("-")
            if len(parts) >= 2:
                return parts[0]

        # Otherwise use parent directory name or path name
        if worktree_path.parent.name == "worktrees":
            return worktree_path.parent.parent.name

        return path_name

    def _extract_worktree_name(self, worktree_path: Path) -> str:
        """Extract worktree/branch name from worktree path.

        Args:
            worktree_path: Path to the worktree

        Returns:
            Worktree name
        """
        path_name = worktree_path.name

        # If it looks like project-branch, extract branch part
        if "-" in path_name:
            parts = path_name.split("-", 1)  # Split only on first hyphen
            if len(parts) >= 2:
                return parts[1]

        return path_name

    def _parse_session_name(self, session_name: str) -> Dict[str, Optional[str]]:
        """Parse a session name to extract components.

        Args:
            session_name: Session name to parse

        Returns:
            Dictionary with parsed components
        """
        parts = session_name.split("-")

        parsed = {"project": None, "worktree": None, "task": None}

        if len(parts) >= 1:
            parsed["project"] = parts[0]
        if len(parts) >= 2:
            parsed["worktree"] = parts[1]
        if len(parts) >= 3:
            parsed["task"] = parts[2]

        return parsed
