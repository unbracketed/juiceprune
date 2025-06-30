"""Tmux session management operations."""

import subprocess
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TmuxManager:
    """Native Python implementation of tmux operations."""

    def __init__(self):
        """Initialize the tmux manager."""
        pass

    def check_tmux_available(self) -> bool:
        """Check if tmux is available and working.

        Returns:
            True if tmux is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["tmux", "-V"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all tmux sessions.

        Returns:
            List of session information dictionaries
        """
        try:
            result = subprocess.run(
                [
                    "tmux",
                    "list-sessions",
                    "-F",
                    "#{session_name}|#{session_path}|#{session_created}|#{session_attached}",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            stdout, stderr = result.stdout, result.stderr

            if result.returncode != 0:
                if "no server running" in stderr.decode().lower():
                    return []  # No tmux server running, no sessions
                raise RuntimeError(f"Failed to list sessions: {stderr.decode()}")

            sessions = []
            for line in stdout.decode().strip().splitlines():
                if not line:
                    continue

                parts = line.split("|")
                if len(parts) >= 4:
                    sessions.append(
                        {
                            "name": parts[0],
                            "path": parts[1],
                            "created": parts[2],
                            "attached": parts[3] == "1",
                        }
                    )

            return sessions

        except Exception as e:
            logger.error(f"Failed to list tmux sessions: {e}")
            return []

    def session_exists(self, session_name: str) -> bool:
        """Check if a tmux session exists.

        Args:
            session_name: Name of the session to check

        Returns:
            True if session exists, False otherwise
        """
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", session_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def create_session(
        self, session_name: str, working_dir: Path, auto_attach: bool = False
    ) -> bool:
        """Create a new tmux session.

        Args:
            session_name: Name for the new session
            working_dir: Working directory for the session
            auto_attach: Whether to attach to the session after creation

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if session already exists
            if self.session_exists(session_name):
                logger.warning(f"Session '{session_name}' already exists")
                return False

            # Create session
            args = ["tmux", "new-session"]
            if not auto_attach:
                args.append("-d")  # Detached
            args.extend(["-s", session_name, "-c", str(working_dir)])

            result = subprocess.run(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
            )
            stderr = result.stderr

            if result.returncode != 0:
                raise RuntimeError(f"Failed to create session: {stderr.decode()}")

            logger.info(f"Created tmux session: {session_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create session '{session_name}': {e}")
            return False

    def create_session_with_tui_return(
        self, session_name: str, working_dir: Path, tui_session_name: str, auto_attach: bool = False
    ) -> bool:
        """Create a new tmux session with a custom keybinding to return to TUI.

        Args:
            session_name: Name for the new session
            working_dir: Working directory for the session
            tui_session_name: Name of the TUI session to return to
            auto_attach: Whether to attach to the session after creation

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create the session first
            if not self.create_session(session_name, working_dir, auto_attach=False):
                return False

            # Add custom keybinding for returning to TUI (prefix + x)
            result = subprocess.run(
                [
                    "tmux", "bind-key", "-T", "prefix", "x",
                    "switch-client", "-t", tui_session_name
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            if result.returncode != 0:
                logger.warning(f"Failed to set custom keybinding for session '{session_name}'")

            # Set a status message about the custom keybinding
            subprocess.run(
                [
                    "tmux", "set-option", "-t", session_name,
                    "status-right", "#[fg=yellow]Press prefix+x to return to TUI#[default] | %H:%M"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            if auto_attach:
                return self.attach_session(session_name)

            logger.info(f"Created tmux session with TUI return: {session_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create session with TUI return '{session_name}': {e}")
            return False

    def attach_session(self, session_name: str) -> bool:
        """Attach to an existing tmux session.

        Args:
            session_name: Name of the session to attach to

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.session_exists(session_name):
                logger.error(f"Session '{session_name}' does not exist")
                return False

            # Use subprocess.run for interactive attachment
            result = subprocess.run(
                ["tmux", "attach-session", "-t", session_name], check=False
            )

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Failed to attach to session '{session_name}': {e}")
            return False

    def switch_session(self, session_name: str) -> bool:
        """Switch to an existing tmux session.

        Args:
            session_name: Name of the session to switch to

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.session_exists(session_name):
                logger.error(f"Session '{session_name}' does not exist")
                return False

            # Use switch-client to change to the target session
            result = subprocess.run(
                ["tmux", "switch-client", "-t", session_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            if result.returncode != 0:
                stderr = result.stderr.decode() if result.stderr else "Unknown error"
                logger.error(f"Failed to switch to session '{session_name}': {stderr}")
                return False

            logger.info(f"Switched to tmux session: {session_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to switch to session '{session_name}': {e}")
            return False

    def kill_session(self, session_name: str) -> bool:
        """Kill a tmux session.

        Args:
            session_name: Name of the session to kill

        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                ["tmux", "kill-session", "-t", session_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            stderr = result.stderr

            if result.returncode != 0:
                raise RuntimeError(f"Failed to kill session: {stderr.decode()}")

            logger.info(f"Killed tmux session: {session_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to kill session '{session_name}': {e}")
            return False

    def sanitize_session_name(self, name: str) -> str:
        """Sanitize session name for tmux compatibility.

        Args:
            name: Raw session name

        Returns:
            Sanitized session name
        """
        # Convert to lowercase
        sanitized = name.lower()

        # Replace invalid characters with hyphens
        sanitized = re.sub(r"[^a-z0-9-_]", "-", sanitized)

        # Collapse multiple hyphens
        sanitized = re.sub(r"-+", "-", sanitized)

        # Remove leading/trailing hyphens
        sanitized = sanitized.strip("-")

        # Ensure it's not empty
        if not sanitized:
            sanitized = "session"

        return sanitized

    def format_session_name(
        self, project: str, worktree: str, task: str = "dev"
    ) -> str:
        """Format a session name according to convention.

        Args:
            project: Project name
            worktree: Worktree/branch name
            task: Task identifier

        Returns:
            Formatted session name
        """
        # Sanitize each component
        safe_project = self.sanitize_session_name(project)
        safe_worktree = self.sanitize_session_name(worktree)
        safe_task = self.sanitize_session_name(task)

        # Format as project-worktree-task
        session_name = f"{safe_project}-{safe_worktree}-{safe_task}"

        # Ensure length is reasonable
        if len(session_name) > 50:
            # Truncate worktree part if too long
            max_worktree_len = 50 - len(safe_project) - len(safe_task) - 2
            if max_worktree_len > 5:
                safe_worktree = safe_worktree[:max_worktree_len]
                session_name = f"{safe_project}-{safe_worktree}-{safe_task}"

        return session_name

    def get_session_info(self, session_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a session.

        Args:
            session_name: Name of the session

        Returns:
            Session information dictionary or None if not found
        """
        sessions = self.list_sessions()

        for session in sessions:
            if session["name"] == session_name:
                return session

        return None
