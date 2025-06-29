"""Tests for external tool integrations."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from prunejuice.integrations.plum import PlumIntegration
from prunejuice.integrations.pots import PotsIntegration


class TestPlumIntegration:
    """Tests for Plum worktree integration."""
    
    def test_plum_integration_available(self):
        """Test that plum integration is available (native implementation)."""
        plum = PlumIntegration()
        assert plum.is_available()  # Native implementation is always available
    
    @patch('prunejuice.worktree_utils.GitWorktreeManager.create_worktree')
    def test_create_worktree_success(self, mock_create, temp_dir):
        """Test successful worktree creation."""
        # Mock the native Git worktree creation
        expected_path = temp_dir / "test-worktree"
        mock_create.return_value = expected_path
        
        plum = PlumIntegration()
        result = plum.create_worktree(temp_dir, "test-branch")
        
        assert result == expected_path
        mock_create.assert_called_once_with("test-branch")
    
    @patch('prunejuice.worktree_utils.GitWorktreeManager.create_worktree')
    def test_create_worktree_failure(self, mock_create, temp_dir):
        """Test worktree creation failure."""
        # Mock native Git operation failure
        mock_create.side_effect = RuntimeError("Branch already exists")
        
        plum = PlumIntegration()
        
        with pytest.raises(RuntimeError, match="Failed to create worktree"):
            plum.create_worktree(temp_dir, "existing-branch")
    
    @patch('prunejuice.worktree_utils.GitWorktreeManager.list_worktrees')
    def test_list_worktrees(self, mock_list, temp_dir):
        """Test listing worktrees."""
        # Mock native Git worktree listing
        mock_list.return_value = [
            {"path": "/path/to/worktree1", "branch": "branch1"},
            {"path": "/path/to/worktree2", "branch": "branch2"}
        ]
        
        plum = PlumIntegration()
        result = plum.list_worktrees(temp_dir)
        
        assert len(result) == 2
        assert result[0]["path"] == "/path/to/worktree1"
        assert result[0]["branch"] == "branch1"
        assert result[1]["path"] == "/path/to/worktree2"
        assert result[1]["branch"] == "branch2"
    
    @patch('prunejuice.worktree_utils.GitWorktreeManager.create_worktree')
    def test_create_worktree_native_implementation(self, mock_create, temp_dir):
        """Test native implementation (no fallback needed)."""
        expected_path = temp_dir / "test-worktree"
        mock_create.return_value = expected_path
        
        plum = PlumIntegration()
        result = plum.create_worktree(temp_dir, "test-branch")
        
        assert result == expected_path


class TestPotsIntegration:
    """Tests for Pots tmux integration."""
    
    @patch('prunejuice.session_utils.TmuxManager.check_tmux_available')
    def test_pots_availability(self, mock_check):
        """Test pots integration availability check."""
        mock_check.return_value = True
        
        pots = PotsIntegration()
        assert pots.is_available()
    
    @patch('prunejuice.session_utils.SessionLifecycleManager.create_session_for_worktree')
    def test_create_session_success(self, mock_create, temp_dir):
        """Test successful session creation."""
        # Mock native tmux session creation
        mock_create.return_value = "test-session"
        
        pots = PotsIntegration()
        result = pots.create_session(temp_dir, "test-task")
        
        assert result == "test-session"
        mock_create.assert_called_once_with(temp_dir, "test-task", auto_attach=False)
    
    @patch('prunejuice.session_utils.SessionLifecycleManager.create_session_for_worktree')
    def test_create_session_failure(self, mock_create, temp_dir):
        """Test session creation failure - should return fallback."""
        # Mock native session creation failure
        mock_create.return_value = None
        
        pots = PotsIntegration()
        result = pots.create_session(temp_dir, "test-task")
        
        # Should return fallback session name
        assert result == "prunejuice-test-task"
    
    @patch('prunejuice.session_utils.TmuxManager.list_sessions')
    def test_list_sessions(self, mock_list, temp_dir):
        """Test listing sessions."""
        # Mock native tmux session listing
        mock_list.return_value = [
            {"name": "session1", "path": "/path1", "attached": True},
            {"name": "session2", "path": "/path2", "attached": False}
        ]
        
        pots = PotsIntegration()
        result = pots.list_sessions()
        
        assert len(result) == 2
        assert result[0]["name"] == "session1"
        assert result[0]["path"] == "/path1"
        assert result[0]["attached"] == True
    
    @patch('prunejuice.session_utils.SessionLifecycleManager.create_session_for_worktree')
    def test_create_session_with_exception(self, mock_create, temp_dir):
        """Test session creation with exception - should return fallback."""
        # Mock exception during session creation
        mock_create.side_effect = Exception("Tmux not available")
        
        pots = PotsIntegration()
        result = pots.create_session(temp_dir, "test-task")
        
        # Should return fallback session name
        assert result == "prunejuice-test-task"
    
    @patch('prunejuice.session_utils.SessionLifecycleManager.kill_session')
    def test_kill_session(self, mock_kill, temp_dir):
        """Test killing a session."""
        # Mock successful session kill
        mock_kill.return_value = True
        
        pots = PotsIntegration()
        result = pots.kill_session("test-session")
        
        assert result is True
        mock_kill.assert_called_once_with("test-session")
    
    @patch('prunejuice.session_utils.SessionLifecycleManager.kill_session')
    def test_kill_session_failure(self, mock_kill, temp_dir):
        """Test session kill failure."""
        # Mock session kill failure
        mock_kill.return_value = False
        
        pots = PotsIntegration()
        result = pots.kill_session("nonexistent-session")
        
        assert result is False