"""Tests for worktree and session utilities."""

import pytest
from pathlib import Path
from unittest.mock import patch

from prunejuice.worktree_utils import GitWorktreeManager
from prunejuice.session_utils import TmuxManager, SessionLifecycleManager


class TestWorktreeUtils:
    """Tests for Git worktree utilities."""

    @patch("prunejuice.worktree_utils.GitWorktreeManager.create_worktree")
    def test_create_worktree_success(self, mock_create, temp_dir):
        """Test successful worktree creation."""
        expected_path = temp_dir / "test-worktree"
        mock_create.return_value = expected_path

        git_manager = GitWorktreeManager(temp_dir)
        result = git_manager.create_worktree("test-branch")

        assert result == expected_path
        mock_create.assert_called_once_with("test-branch")

    @patch("prunejuice.worktree_utils.GitWorktreeManager.create_worktree")
    def test_create_worktree_failure(self, mock_create, temp_dir):
        """Test worktree creation failure."""
        mock_create.side_effect = RuntimeError("Branch already exists")

        git_manager = GitWorktreeManager(temp_dir)

        with pytest.raises(RuntimeError, match="Branch already exists"):
            git_manager.create_worktree("existing-branch")

    @patch("prunejuice.worktree_utils.GitWorktreeManager.list_worktrees")
    def test_list_worktrees(self, mock_list, temp_dir):
        """Test listing worktrees."""
        mock_list.return_value = [
            {"path": "/path/to/worktree1", "branch": "branch1"},
            {"path": "/path/to/worktree2", "branch": "branch2"},
        ]

        git_manager = GitWorktreeManager(temp_dir)
        result = git_manager.list_worktrees()

        assert len(result) == 2
        assert result[0]["branch"] == "branch1"
        assert result[1]["branch"] == "branch2"

    @patch("prunejuice.worktree_utils.GitWorktreeManager.remove_worktree")
    def test_remove_worktree(self, mock_remove, temp_dir):
        """Test removing a worktree."""
        mock_remove.return_value = True

        git_manager = GitWorktreeManager(temp_dir)
        result = git_manager.remove_worktree(Path("/path/to/worktree"))

        assert result is True
        mock_remove.assert_called_once()


class TestSessionUtils:
    """Tests for tmux session utilities."""

    @patch("prunejuice.session_utils.TmuxManager.check_tmux_available")
    def test_tmux_available(self, mock_check):
        """Test checking tmux availability."""
        mock_check.return_value = True

        tmux_manager = TmuxManager()
        assert tmux_manager.check_tmux_available()

    @patch("prunejuice.session_utils.TmuxManager.check_tmux_available")
    def test_tmux_not_available(self, mock_check):
        """Test when tmux is not available."""
        mock_check.return_value = False

        tmux_manager = TmuxManager()
        assert not tmux_manager.check_tmux_available()

    @patch(
        "prunejuice.session_utils.SessionLifecycleManager.create_session_for_worktree"
    )
    def test_create_session_success(self, mock_create, temp_dir):
        """Test successful session creation."""
        mock_create.return_value = "test-session"

        tmux_manager = TmuxManager()
        session_manager = SessionLifecycleManager(tmux_manager)

        result = session_manager.create_session_for_worktree(
            temp_dir, "test-task", auto_attach=False
        )

        assert result == "test-session"
        mock_create.assert_called_once()

    @patch(
        "prunejuice.session_utils.SessionLifecycleManager.create_session_for_worktree"
    )
    def test_create_session_failure(self, mock_create, temp_dir):
        """Test session creation failure."""
        mock_create.return_value = None

        tmux_manager = TmuxManager()
        session_manager = SessionLifecycleManager(tmux_manager)

        result = session_manager.create_session_for_worktree(
            temp_dir, "test-task", auto_attach=False
        )

        assert result is None

    @patch("prunejuice.session_utils.TmuxManager.list_sessions")
    def test_list_sessions(self, mock_list):
        """Test listing tmux sessions."""
        mock_list.return_value = [
            {"name": "session1", "path": "/path/to/dir1"},
            {"name": "session2", "path": "/path/to/dir2"},
        ]

        tmux_manager = TmuxManager()
        result = tmux_manager.list_sessions()

        assert len(result) == 2
        assert result[0]["name"] == "session1"
        assert result[1]["name"] == "session2"

    @patch("prunejuice.session_utils.SessionLifecycleManager.attach_to_session")
    def test_attach_session(self, mock_attach):
        """Test attaching to a session."""
        mock_attach.return_value = True

        tmux_manager = TmuxManager()
        session_manager = SessionLifecycleManager(tmux_manager)

        result = session_manager.attach_to_session("test-session")

        assert result is True
        mock_attach.assert_called_once_with("test-session")

    @patch("prunejuice.session_utils.SessionLifecycleManager.kill_session")
    def test_kill_session(self, mock_kill):
        """Test killing a session."""
        mock_kill.return_value = True

        tmux_manager = TmuxManager()
        session_manager = SessionLifecycleManager(tmux_manager)

        result = session_manager.kill_session("test-session")

        assert result is True
        mock_kill.assert_called_once_with("test-session")
