"""Environment utilities for worktree-aware virtual environment management."""

import os
from pathlib import Path
from typing import Dict, Optional

import git


def is_in_worktree() -> bool:
    """Check if the current directory is inside a Git worktree."""
    try:
        repo = git.Repo(search_parent_directories=True)
        return repo.git_dir != str(Path(repo.working_dir) / ".git")
    except (git.InvalidGitRepositoryError, git.GitCommandError):
        return False


def get_project_root() -> Path:
    """Get the root directory of the current project (worktree or main repo)."""
    try:
        repo = git.Repo(search_parent_directories=True)
        return Path(repo.working_dir)
    except (git.InvalidGitRepositoryError, git.GitCommandError):
        return Path.cwd()


def get_current_venv_path() -> Path:
    """Get the virtual environment path for the current context."""
    project_root = get_project_root()
    return project_root / ".venv"


def prepare_clean_environment() -> Dict[str, str]:
    """Prepare a clean environment dict without conflicting VIRTUAL_ENV."""
    env = os.environ.copy()
    
    # Remove any existing VIRTUAL_ENV to prevent conflicts
    env.pop("VIRTUAL_ENV", None)
    
    # Set the correct virtual environment path for the current context
    venv_path = get_current_venv_path()
    if venv_path.exists():
        env["VIRTUAL_ENV"] = str(venv_path)
    
    return env


def is_uv_command(command: str) -> bool:
    """Check if a command is a uv command that needs environment handling."""
    if not command:
        return False
    
    # Split command and check the first part
    parts = command.strip().split()
    if not parts:
        return False
    
    first_part = parts[0]
    
    # Direct uv commands
    if first_part == "uv":
        return True
    
    # uv run commands
    if len(parts) >= 2 and first_part == "uv" and parts[1] == "run":
        return True
    
    return False


def get_worktree_info() -> Optional[Dict[str, str]]:
    """Get information about the current worktree."""
    try:
        repo = git.Repo(search_parent_directories=True)
        
        if not is_in_worktree():
            return None
        
        worktree_path = Path(repo.working_dir)
        main_repo_path = Path(repo.git_dir).parent
        
        return {
            "worktree_path": str(worktree_path),
            "main_repo_path": str(main_repo_path),
            "worktree_name": worktree_path.name,
            "branch": repo.active_branch.name if repo.active_branch else "detached",
        }
    except (git.InvalidGitRepositoryError, git.GitCommandError):
        return None