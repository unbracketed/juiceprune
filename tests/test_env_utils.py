"""Tests for environment utilities."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import git

from prunejuice.env_utils import (
    is_in_worktree,
    get_project_root,
    get_current_venv_path,
    prepare_clean_environment,
    is_uv_command,
    get_worktree_info,
)


class TestWorktreeDetection:
    """Test worktree detection functionality."""

    @patch("prunejuice.env_utils.git.Repo")
    def test_is_in_worktree_true(self, mock_repo):
        """Test detection of worktree directory."""
        mock_repo_instance = MagicMock()
        mock_repo_instance.git_dir = "/path/to/main/.git/worktrees/branch"
        mock_repo_instance.working_dir = "/path/to/worktree"
        mock_repo.return_value = mock_repo_instance
        
        assert is_in_worktree() is True

    @patch("prunejuice.env_utils.git.Repo")
    def test_is_in_worktree_false(self, mock_repo):
        """Test detection of main repository."""
        mock_repo_instance = MagicMock()
        mock_repo_instance.git_dir = "/path/to/main/.git"
        mock_repo_instance.working_dir = "/path/to/main"
        mock_repo.return_value = mock_repo_instance
        
        assert is_in_worktree() is False

    @patch("prunejuice.env_utils.git.Repo")
    def test_is_in_worktree_no_git(self, mock_repo):
        """Test behavior when not in a git repository."""
        mock_repo.side_effect = git.InvalidGitRepositoryError
        
        assert is_in_worktree() is False


class TestProjectRoot:
    """Test project root detection."""

    @patch("prunejuice.env_utils.git.Repo")
    def test_get_project_root_success(self, mock_repo):
        """Test getting project root from git repository."""
        mock_repo_instance = MagicMock()
        mock_repo_instance.working_dir = "/path/to/project"
        mock_repo.return_value = mock_repo_instance
        
        result = get_project_root()
        assert result == Path("/path/to/project")

    @patch("prunejuice.env_utils.git.Repo")
    @patch("prunejuice.env_utils.Path.cwd")
    def test_get_project_root_no_git(self, mock_cwd, mock_repo):
        """Test fallback to current directory when not in git repo."""
        mock_repo.side_effect = git.InvalidGitRepositoryError
        mock_cwd.return_value = Path("/current/dir")
        
        result = get_project_root()
        assert result == Path("/current/dir")


class TestVenvPath:
    """Test virtual environment path resolution."""

    @patch("prunejuice.env_utils.get_project_root")
    def test_get_current_venv_path(self, mock_get_project_root):
        """Test venv path construction."""
        mock_get_project_root.return_value = Path("/project/root")
        
        result = get_current_venv_path()
        assert result == Path("/project/root/.venv")


class TestEnvironmentPreparation:
    """Test environment preparation for commands."""

    def test_prepare_clean_environment_removes_virtual_env(self):
        """Test that VIRTUAL_ENV is removed from environment."""
        with patch.dict(os.environ, {"VIRTUAL_ENV": "/old/venv", "OTHER_VAR": "value"}):
            with patch("prunejuice.env_utils.get_current_venv_path") as mock_venv_path:
                mock_venv_path.return_value = Path("/nonexistent")
                
                env = prepare_clean_environment()
                
                assert "VIRTUAL_ENV" not in env
                assert env["OTHER_VAR"] == "value"

    def test_prepare_clean_environment_sets_existing_venv(self):
        """Test that VIRTUAL_ENV is set when venv exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            venv_path = Path(temp_dir) / ".venv"
            venv_path.mkdir()
            
            with patch("prunejuice.env_utils.get_current_venv_path") as mock_venv_path:
                mock_venv_path.return_value = venv_path
                
                env = prepare_clean_environment()
                
                assert env["VIRTUAL_ENV"] == str(venv_path)

    def test_prepare_clean_environment_no_venv_exists(self):
        """Test behavior when venv doesn't exist."""
        with patch("prunejuice.env_utils.get_current_venv_path") as mock_venv_path:
            mock_venv_path.return_value = Path("/nonexistent/.venv")
            
            env = prepare_clean_environment()
            
            assert "VIRTUAL_ENV" not in env


class TestUvCommandDetection:
    """Test UV command detection."""

    @pytest.mark.parametrize("command,expected", [
        ("uv sync", True),
        ("uv run python script.py", True),
        ("uv add package", True),
        ("python script.py", False),
        ("pip install package", False),
        ("", False),
        ("   ", False),
        ("not-uv command", False),
    ])
    def test_is_uv_command(self, command, expected):
        """Test UV command detection with various inputs."""
        assert is_uv_command(command) is expected


class TestWorktreeInfo:
    """Test worktree information gathering."""

    @patch("prunejuice.env_utils.is_in_worktree")
    @patch("prunejuice.env_utils.git.Repo")
    def test_get_worktree_info_success(self, mock_repo, mock_is_in_worktree):
        """Test successful worktree info retrieval."""
        mock_is_in_worktree.return_value = True
        
        mock_repo_instance = MagicMock()
        mock_repo_instance.working_dir = "/path/to/worktree/branch-name"
        mock_repo_instance.git_dir = "/path/to/main/.git/worktrees/branch-name"
        mock_repo_instance.active_branch.name = "feature-branch"
        mock_repo.return_value = mock_repo_instance
        
        result = get_worktree_info()
        
        assert result is not None
        assert result["worktree_path"] == "/path/to/worktree/branch-name"
        assert result["main_repo_path"] == "/path/to/main/.git/worktrees"
        assert result["worktree_name"] == "branch-name"
        assert result["branch"] == "feature-branch"

    @patch("prunejuice.env_utils.is_in_worktree")
    def test_get_worktree_info_not_in_worktree(self, mock_is_in_worktree):
        """Test when not in a worktree."""
        mock_is_in_worktree.return_value = False
        
        result = get_worktree_info()
        assert result is None

    @patch("prunejuice.env_utils.git.Repo")
    def test_get_worktree_info_no_git(self, mock_repo):
        """Test when not in a git repository."""
        mock_repo.side_effect = git.InvalidGitRepositoryError
        
        result = get_worktree_info()
        assert result is None