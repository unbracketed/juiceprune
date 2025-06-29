"""Git operations for worktree management."""

from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

import git
from git.exc import GitCommandError, InvalidGitRepositoryError

logger = logging.getLogger(__name__)


class GitWorktreeManager:
    """Native Python implementation of Git worktree operations."""
    
    def __init__(self, project_path: Path):
        """Initialize with project path."""
        self.project_path = project_path
        self._repo: Optional[git.Repo] = None
    
    @property
    def repo(self) -> git.Repo:
        """Get or initialize Git repository."""
        if self._repo is None:
            try:
                self._repo = git.Repo(self.project_path, search_parent_directories=True)
            except InvalidGitRepositoryError:
                raise RuntimeError(f"Not a git repository: {self.project_path}")
        return self._repo
    
    def create_worktree(
        self,
        branch_name: str,
        base_branch: str = "main",
        parent_dir: Optional[Path] = None
    ) -> Path:
        """Create a new Git worktree.
        
        Args:
            branch_name: Name for the new branch
            base_branch: Base branch to create from
            parent_dir: Parent directory for worktree (default: ../worktrees)
            
        Returns:
            Path to the created worktree
        """
        if parent_dir is None:
            parent_dir = self.project_path.parent / "worktrees"
        
        parent_dir.mkdir(parents=True, exist_ok=True)
        worktree_path = parent_dir / f"{self.project_path.name}-{branch_name}"
        
        try:
            # Check if base branch exists
            if base_branch not in [ref.name for ref in self.repo.refs]:
                raise ValueError(f"Base branch '{base_branch}' does not exist")
            
            # Create new branch and worktree
            logger.info(f"Creating worktree at {worktree_path} with branch {branch_name}")
            
            # Use GitPython for worktree creation
            self.repo.git.worktree("add", "-b", branch_name, str(worktree_path), base_branch)
            
            logger.info(f"Successfully created worktree: {worktree_path}")
            return worktree_path
            
        except GitCommandError as e:
            raise RuntimeError(f"Failed to create worktree: {e}")
    
    def list_worktrees(self) -> List[Dict[str, Any]]:
        """List all worktrees for the repository.
        
        Returns:
            List of worktree information dictionaries
        """
        try:
            # Use git worktree list --porcelain for structured output
            result = self.repo.git.worktree("list", "--porcelain")
            
            worktrees = []
            current_worktree = {}
            
            for line in result.splitlines():
                if line.startswith("worktree "):
                    if current_worktree:
                        worktrees.append(current_worktree)
                    current_worktree = {"path": line[9:]}  # Remove "worktree " prefix
                elif line.startswith("HEAD "):
                    current_worktree["commit"] = line[5:]
                elif line.startswith("branch "):
                    current_worktree["branch"] = line[7:]  # Remove "branch " prefix
                elif line == "bare":
                    current_worktree["bare"] = True
                elif line == "detached":
                    current_worktree["detached"] = True
            
            # Add the last worktree
            if current_worktree:
                worktrees.append(current_worktree)
            
            return worktrees
            
        except GitCommandError as e:
            logger.error(f"Failed to list worktrees: {e}")
            return []
    
    def remove_worktree(self, worktree_path: Path, force: bool = False) -> bool:
        """Remove a Git worktree.
        
        Args:
            worktree_path: Path to the worktree to remove
            force: Force removal even if worktree is dirty
            
        Returns:
            True if successful, False otherwise
        """
        try:
            args = ["remove", str(worktree_path)]
            if force:
                args.insert(1, "--force")
            
            self.repo.git.worktree(*args)
            logger.info(f"Successfully removed worktree: {worktree_path}")
            return True
            
        except GitCommandError as e:
            logger.error(f"Failed to remove worktree {worktree_path}: {e}")
            return False
    
    def get_worktree_info(self, worktree_path: Path) -> Optional[Dict[str, Any]]:
        """Get information about a specific worktree.
        
        Args:
            worktree_path: Path to the worktree
            
        Returns:
            Worktree information dictionary or None if not found
        """
        worktrees = self.list_worktrees()
        
        for worktree in worktrees:
            if Path(worktree["path"]) == worktree_path:
                return worktree
        
        return None
    
    def is_git_repository(self) -> bool:
        """Check if the project path is a Git repository."""
        try:
            git.Repo(self.project_path, search_parent_directories=True)
            return True
        except InvalidGitRepositoryError:
            return False
    
    def get_current_branch(self) -> Optional[str]:
        """Get the current branch name."""
        try:
            return self.repo.active_branch.name
        except Exception:
            return None
    
    def get_main_worktree_path(self) -> Path:
        """Get the path to the main worktree (repository root)."""
        return Path(self.repo.working_dir)