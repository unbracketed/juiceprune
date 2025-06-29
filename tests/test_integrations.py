"""Tests for external tool integrations."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

from prunejuice.integrations.plum import PlumIntegration
from prunejuice.integrations.pots import PotsIntegration


class TestPlumIntegration:
    """Tests for Plum worktree integration."""
    
    def test_find_plum_not_found(self):
        """Test when plum is not found."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "which")
            
            plum = PlumIntegration()
            assert plum.plum_path is None
            assert not plum.is_available()
    
    @patch('subprocess.run')
    async def test_create_worktree_success(self, mock_run, temp_dir):
        """Test successful worktree creation."""
        # Mock plum executable
        mock_plum = temp_dir / "plum"
        mock_plum.touch()
        
        # Mock subprocess output
        mock_run.return_value = MagicMock(
            stdout="Worktree created at: /path/to/worktree\n",
            stderr="",
            returncode=0
        )
        
        plum = PlumIntegration(mock_plum)
        result = await plum.create_worktree(temp_dir, "test-branch")
        
        assert result == Path("/path/to/worktree")
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    async def test_create_worktree_failure(self, mock_run, temp_dir):
        """Test worktree creation failure."""
        mock_plum = temp_dir / "plum"
        mock_plum.touch()
        
        # Mock subprocess failure
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "plum", stderr="Branch already exists"
        )
        
        plum = PlumIntegration(mock_plum)
        
        with pytest.raises(RuntimeError, match="Failed to create worktree"):
            await plum.create_worktree(temp_dir, "existing-branch")
    
    @patch('subprocess.run')
    async def test_list_worktrees(self, mock_run, temp_dir):
        """Test listing worktrees."""
        mock_plum = temp_dir / "plum"
        mock_plum.touch()
        
        # Mock subprocess output
        mock_run.return_value = MagicMock(
            stdout="/path/to/worktree1 branch1\n/path/to/worktree2 branch2\n",
            stderr="",
            returncode=0
        )
        
        plum = PlumIntegration(mock_plum)
        result = await plum.list_worktrees(temp_dir)
        
        assert len(result) == 2
        assert result[0]["path"] == "/path/to/worktree1"
        assert result[0]["branch"] == "branch1"
        assert result[1]["path"] == "/path/to/worktree2"
        assert result[1]["branch"] == "branch2"
    
    async def test_create_worktree_without_plum(self, temp_dir):
        """Test fallback when plum is not available."""
        plum = PlumIntegration(None)
        result = await plum.create_worktree(temp_dir, "test-branch")
        
        # Should fall back to project path
        assert result == temp_dir


class TestPotsIntegration:
    """Tests for Pots tmux integration."""
    
    def test_find_pots_not_found(self):
        """Test when pots is not found."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "which")
            
            pots = PotsIntegration()
            assert pots.pots_path is None
            assert not pots.is_available()
    
    @patch('subprocess.run')
    async def test_create_session_success(self, mock_run, temp_dir):
        """Test successful session creation."""
        mock_pots = temp_dir / "pots"
        mock_pots.touch()
        
        # Mock subprocess output
        mock_run.return_value = MagicMock(
            stdout="Session created: test-session\n",
            stderr="",
            returncode=0
        )
        
        pots = PotsIntegration(mock_pots)
        result = await pots.create_session(temp_dir, "test-task")
        
        assert result == "test-session"
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    async def test_create_session_failure(self, mock_run, temp_dir):
        """Test session creation failure - should not raise exception."""
        mock_pots = temp_dir / "pots"
        mock_pots.touch()
        
        # Mock subprocess failure
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "pots", stderr="Tmux not available"
        )
        
        pots = PotsIntegration(mock_pots)
        result = await pots.create_session(temp_dir, "test-task")
        
        # Should return fallback session name
        assert result == "prunejuice-test-task"
    
    @patch('subprocess.run')
    async def test_list_sessions(self, mock_run, temp_dir):
        """Test listing sessions."""
        mock_pots = temp_dir / "pots"
        mock_pots.touch()
        
        # Mock subprocess output
        mock_run.return_value = MagicMock(
            stdout="session1 /path1 active\nsession2 /path2 detached\n",
            stderr="",
            returncode=0
        )
        
        pots = PotsIntegration(mock_pots)
        result = await pots.list_sessions()
        
        assert len(result) == 2
        assert result[0]["name"] == "session1"
        assert result[0]["path"] == "/path1"
        assert result[0]["status"] == "active"
    
    async def test_create_session_without_pots(self, temp_dir):
        """Test fallback when pots is not available."""
        pots = PotsIntegration(None)
        result = await pots.create_session(temp_dir, "test-task")
        
        # Should return fallback session name
        assert result == "prunejuice-test-task"
    
    @patch('subprocess.run')
    async def test_kill_session(self, mock_run, temp_dir):
        """Test killing a session."""
        mock_pots = temp_dir / "pots"
        mock_pots.touch()
        
        # Mock successful kill
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="",
            returncode=0
        )
        
        pots = PotsIntegration(mock_pots)
        result = await pots.kill_session("test-session")
        
        assert result is True
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    async def test_kill_session_failure(self, mock_run, temp_dir):
        """Test session kill failure."""
        mock_pots = temp_dir / "pots"
        mock_pots.touch()
        
        # Mock subprocess failure
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "pots", stderr="Session not found"
        )
        
        pots = PotsIntegration(mock_pots)
        result = await pots.kill_session("nonexistent-session")
        
        assert result is False