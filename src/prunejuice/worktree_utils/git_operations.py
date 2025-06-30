"""Git operations for worktree management."""

from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import re

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
        parent_dir: Optional[Path] = None,
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
            logger.info(
                f"Creating worktree at {worktree_path} with branch {branch_name}"
            )

            # Use GitPython for worktree creation
            self.repo.git.worktree(
                "add", "-b", branch_name, str(worktree_path), base_branch
            )

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
            current_worktree: Dict[str, Any] = {}

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
        # Get list of all worktrees
        worktrees = self.list_worktrees()

        # The main worktree is the first one in the list
        if worktrees:
            return Path(worktrees[0]["path"])

        # Fallback to current working directory
        return Path(self.repo.working_dir)

    def get_worktree_diff(
        self, 
        worktree_path: Path, 
        base_branch: str = "main", 
        context_lines: int = 3,
        staged_only: bool = False,
        unstaged_only: bool = False
    ) -> str:
        """Get git diff between worktree branch and base branch.
        
        Args:
            worktree_path: Path to the worktree
            base_branch: Base branch to compare against
            context_lines: Number of context lines in diff
            staged_only: Show only staged changes
            unstaged_only: Show only unstaged changes
            
        Returns:
            Formatted diff string
        """
        try:
            # Create a repo object for the worktree
            worktree_repo = git.Repo(worktree_path)
            
            if staged_only:
                # Show only staged changes
                diff_output = worktree_repo.git.diff("--cached", f"-U{context_lines}")
            elif unstaged_only:
                # Show only unstaged changes  
                diff_output = worktree_repo.git.diff(f"-U{context_lines}")
            else:
                # Compare worktree branch against base branch
                current_branch = worktree_repo.active_branch.name
                
                # Check if base branch exists
                try:
                    worktree_repo.git.rev_parse("--verify", f"{base_branch}")
                except GitCommandError:
                    # Try origin/base_branch if base_branch doesn't exist
                    try:
                        worktree_repo.git.rev_parse("--verify", f"origin/{base_branch}")
                        base_branch = f"origin/{base_branch}"
                    except GitCommandError:
                        raise ValueError(f"Base branch '{base_branch}' not found")
                
                diff_output = worktree_repo.git.diff(base_branch, current_branch, f"-U{context_lines}")
            
            return diff_output
            
        except Exception as e:
            logger.error(f"Failed to get diff for worktree {worktree_path}: {e}")
            raise RuntimeError(f"Failed to get diff: {e}")

    def get_diff_summary(
        self, 
        worktree_path: Path, 
        base_branch: str = "main",
        staged_only: bool = False,
        unstaged_only: bool = False
    ) -> Dict[str, Any]:
        """Get summary statistics of differences.
        
        Args:
            worktree_path: Path to the worktree
            base_branch: Base branch to compare against
            staged_only: Show only staged changes
            unstaged_only: Show only unstaged changes
            
        Returns:
            Dictionary with diff statistics
        """
        try:
            worktree_repo = git.Repo(worktree_path)
            
            if staged_only:
                # Get staged changes summary
                stat_output = worktree_repo.git.diff("--cached", "--stat")
            elif unstaged_only:
                # Get unstaged changes summary
                stat_output = worktree_repo.git.diff("--stat")
            else:
                # Compare against base branch
                current_branch = worktree_repo.active_branch.name
                
                # Check if base branch exists
                try:
                    worktree_repo.git.rev_parse("--verify", f"{base_branch}")
                except GitCommandError:
                    try:
                        worktree_repo.git.rev_parse("--verify", f"origin/{base_branch}")
                        base_branch = f"origin/{base_branch}"
                    except GitCommandError:
                        base_branch = "main"  # Fallback
                
                stat_output = worktree_repo.git.diff(base_branch, current_branch, "--stat")
            
            # Parse the stat output to extract numbers
            files_changed = 0
            insertions = 0
            deletions = 0
            
            if stat_output.strip():
                lines = stat_output.strip().split('\n')
                if lines:
                    # Last line usually contains summary like "1 file changed, 2 insertions(+), 1 deletion(-)"
                    summary_line = lines[-1]
                    
                    # Count files changed
                    files_changed = len([line for line in lines[:-1] if '|' in line])
                    
                    # Parse insertions and deletions from summary
                    if 'insertion' in summary_line:
                        insertions_match = re.search(r'(\d+) insertion', summary_line)
                        if insertions_match:
                            insertions = int(insertions_match.group(1))
                    
                    if 'deletion' in summary_line:
                        deletions_match = re.search(r'(\d+) deletion', summary_line)
                        if deletions_match:
                            deletions = int(deletions_match.group(1))
            
            return {
                "files_changed": files_changed,
                "insertions": insertions,
                "deletions": deletions,
                "has_changes": bool(stat_output.strip()),
                "base_branch": base_branch,
                "current_branch": worktree_repo.active_branch.name if not staged_only and not unstaged_only else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get diff summary for worktree {worktree_path}: {e}")
            return {
                "files_changed": 0,
                "insertions": 0,
                "deletions": 0,
                "has_changes": False,
                "error": str(e)
            }

    def get_worktree_status(self, worktree_path: Path) -> Dict[str, Any]:
        """Get working directory status (staged/unstaged changes).
        
        Args:
            worktree_path: Path to the worktree
            
        Returns:
            Dictionary with status information
        """
        try:
            worktree_repo = git.Repo(worktree_path)
            
            # Get status using git status --porcelain
            status_output = worktree_repo.git.status("--porcelain")
            
            staged_files = []
            unstaged_files = []
            untracked_files = []
            
            for line in status_output.splitlines():
                if len(line) >= 2:
                    staged_status = line[0]
                    unstaged_status = line[1]
                    filename = line[3:]  # Skip status chars and space
                    
                    if staged_status != ' ':
                        staged_files.append({"file": filename, "status": staged_status})
                    
                    if unstaged_status != ' ':
                        if unstaged_status == '?':
                            untracked_files.append(filename)
                        else:
                            unstaged_files.append({"file": filename, "status": unstaged_status})
            
            return {
                "staged_files": staged_files,
                "unstaged_files": unstaged_files,
                "untracked_files": untracked_files,
                "is_clean": len(staged_files) == 0 and len(unstaged_files) == 0 and len(untracked_files) == 0,
                "current_branch": worktree_repo.active_branch.name
            }
            
        except Exception as e:
            logger.error(f"Failed to get status for worktree {worktree_path}: {e}")
            return {
                "staged_files": [],
                "unstaged_files": [],
                "untracked_files": [],
                "is_clean": True,
                "error": str(e)
            }
