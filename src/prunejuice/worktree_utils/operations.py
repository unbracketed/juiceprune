"""Worktree operations service for advanced Git operations."""

import asyncio
import logging
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

import git
from git.exc import GitCommandError

from .git_operations import GitWorktreeManager

logger = logging.getLogger(__name__)


class OperationResult(Enum):
    """Result status for worktree operations."""

    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    CONFLICT = "conflict"


@dataclass
class CommitResult:
    """Result of a commit operation."""

    status: OperationResult
    commit_hash: Optional[str] = None
    message: Optional[str] = None
    files_committed: Optional[List[str]] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.files_committed is None:
            self.files_committed = []


@dataclass
class MergeResult:
    """Result of a merge operation."""

    status: OperationResult
    merge_commit: Optional[str] = None
    target_branch: Optional[str] = None
    conflicts: Optional[List[str]] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []


@dataclass
class PRResult:
    """Result of a pull request operation."""

    status: OperationResult
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    error: Optional[str] = None


@dataclass
class DeleteResult:
    """Result of a delete operation."""

    status: OperationResult
    deleted_path: Optional[str] = None
    cleanup_performed: bool = False
    error: Optional[str] = None


class WorktreeOperations:
    """Service class for advanced worktree operations."""

    def __init__(self, project_path: Path):
        """Initialize with project path."""
        self.project_path = project_path
        self.git_manager = GitWorktreeManager(project_path)

    async def commit_changes(
        self,
        worktree_path: Path,
        message: Optional[str] = None,
        interactive: bool = True,
        stage_all: bool = False,
        files_to_stage: Optional[List[str]] = None,
    ) -> CommitResult:
        """Commit changes in a worktree.

        Args:
            worktree_path: Path to the worktree
            message: Commit message (if None, will prompt for one)
            interactive: Whether to use interactive mode
            stage_all: Whether to stage all changes
            files_to_stage: Specific files to stage (if provided)

        Returns:
            CommitResult with operation details
        """
        try:
            # Validate worktree exists
            if not worktree_path.exists():
                return CommitResult(
                    status=OperationResult.FAILURE,
                    error=f"Worktree path does not exist: {worktree_path}",
                )

            # Get worktree repo
            worktree_repo = git.Repo(worktree_path)

            # Get current status (not used but could be for validation)
            # status = self.git_manager.get_worktree_status(worktree_path)

            # Handle staging
            if stage_all:
                # Stage all changes
                worktree_repo.git.add(".")
                logger.info("Staged all changes")
            elif files_to_stage:
                # Stage specific files
                for file_path in files_to_stage:
                    worktree_repo.git.add(file_path)
                logger.info(f"Staged {len(files_to_stage)} files")

            # Check if there are staged changes
            updated_status = self.git_manager.get_worktree_status(worktree_path)
            if not updated_status.get("staged_files"):
                return CommitResult(
                    status=OperationResult.FAILURE, error="No staged changes to commit"
                )

            # Handle commit message
            if not message:
                if interactive:
                    message = await self._get_commit_message_interactive()
                else:
                    return CommitResult(
                        status=OperationResult.FAILURE,
                        error="No commit message provided",
                    )

            # Perform the commit
            commit = worktree_repo.index.commit(message)

            # Get list of committed files
            committed_files = list(commit.stats.files.keys())

            logger.info(f"Successfully committed {commit.hexsha[:8]}")

            return CommitResult(
                status=OperationResult.SUCCESS,
                commit_hash=commit.hexsha,
                message=message,
                files_committed=committed_files,
            )

        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            return CommitResult(status=OperationResult.FAILURE, error=str(e))

    async def merge_to_parent(
        self,
        worktree_path: Path,
        delete_after: bool = False,
        target_branch: Optional[str] = None,
    ) -> MergeResult:
        """Merge worktree branch to parent branch.

        Args:
            worktree_path: Path to the worktree
            delete_after: Whether to delete worktree after merge
            target_branch: Target branch to merge into (auto-detect if None)

        Returns:
            MergeResult with operation details
        """
        try:
            # Get worktree info
            worktree_info = self.git_manager.get_worktree_info(worktree_path)
            if not worktree_info:
                return MergeResult(
                    status=OperationResult.FAILURE,
                    error=f"Worktree not found: {worktree_path}",
                )

            source_branch = worktree_info.get("branch")
            if not source_branch:
                return MergeResult(
                    status=OperationResult.FAILURE,
                    error="Could not determine source branch",
                )

            # Determine target branch
            if not target_branch:
                target_branch = await self._detect_parent_branch(worktree_path)

            # Switch to main repo and target branch
            main_repo = self.git_manager.repo
            main_repo.git.checkout(target_branch)

            # Ensure we're up to date
            try:
                main_repo.git.pull("origin", target_branch)
            except GitCommandError:
                logger.warning(f"Could not pull latest {target_branch}")

            # Perform merge
            try:
                main_repo.git.merge(source_branch, "--no-ff")

                # Get merge commit hash
                merge_commit = main_repo.head.commit.hexsha

                logger.info(f"Successfully merged {source_branch} into {target_branch}")

                # Optionally delete worktree
                if delete_after:
                    delete_result = await self.delete_worktree(worktree_path)
                    if delete_result.status != OperationResult.SUCCESS:
                        logger.warning(
                            f"Failed to delete worktree: {delete_result.error}"
                        )

                return MergeResult(
                    status=OperationResult.SUCCESS,
                    merge_commit=merge_commit,
                    target_branch=target_branch,
                )

            except GitCommandError as e:
                if "conflict" in str(e).lower():
                    # Handle merge conflicts
                    conflicts = await self._get_merge_conflicts(main_repo)
                    return MergeResult(
                        status=OperationResult.CONFLICT,
                        target_branch=target_branch,
                        conflicts=conflicts,
                        error=f"Merge conflicts detected: {e}",
                    )
                else:
                    raise

        except Exception as e:
            logger.error(f"Failed to merge worktree: {e}")
            return MergeResult(status=OperationResult.FAILURE, error=str(e))

    async def create_pull_request(
        self,
        worktree_path: Path,
        title: Optional[str] = None,
        body: Optional[str] = None,
        draft: bool = False,
    ) -> PRResult:
        """Create a pull request for the worktree branch.

        Args:
            worktree_path: Path to the worktree
            title: PR title (auto-generated if None)
            body: PR body
            draft: Whether to create as draft

        Returns:
            PRResult with operation details
        """
        try:
            # Get worktree info
            worktree_info = self.git_manager.get_worktree_info(worktree_path)
            if not worktree_info:
                return PRResult(
                    status=OperationResult.FAILURE,
                    error=f"Worktree not found: {worktree_path}",
                )

            source_branch = worktree_info.get("branch")
            if not source_branch:
                return PRResult(
                    status=OperationResult.FAILURE,
                    error="Could not determine source branch",
                )

            # Ensure branch is pushed to remote
            worktree_repo = git.Repo(worktree_path)
            try:
                worktree_repo.git.push("origin", source_branch)
            except GitCommandError as e:
                if "up-to-date" not in str(e):
                    logger.warning(f"Failed to push branch: {e}")

            # Generate title if not provided
            if not title:
                title = await self._generate_pr_title(worktree_path)

            # Use GitHub CLI to create PR
            cmd = ["gh", "pr", "create", "--title", title, "--head", source_branch]

            if body:
                cmd.extend(["--body", body])

            if draft:
                cmd.append("--draft")

            # Execute GitHub CLI command
            result = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                stdout_str = stdout.decode() if isinstance(stdout, bytes) else stdout
                pr_url = stdout_str.strip()
                # Extract PR number from URL
                pr_number = None
                if "/pull/" in pr_url:
                    try:
                        pr_number = int(pr_url.split("/pull/")[-1])
                    except ValueError:
                        pass

                return PRResult(
                    status=OperationResult.SUCCESS, pr_url=pr_url, pr_number=pr_number
                )
            else:
                error_msg = stderr.decode().strip()
                return PRResult(
                    status=OperationResult.FAILURE,
                    error=f"GitHub CLI error: {error_msg}",
                )

        except Exception as e:
            logger.error(f"Failed to create pull request: {e}")
            return PRResult(status=OperationResult.FAILURE, error=str(e))

    async def delete_worktree(
        self,
        worktree_path: Path,
        force: bool = False,
        cleanup_sessions: bool = True,
    ) -> DeleteResult:
        """Delete a worktree and perform cleanup.

        Args:
            worktree_path: Path to the worktree to delete
            force: Force deletion even if dirty
            cleanup_sessions: Whether to cleanup associated tmux sessions

        Returns:
            DeleteResult with operation details
        """
        try:
            # Check if worktree exists
            if not worktree_path.exists():
                return DeleteResult(
                    status=OperationResult.FAILURE,
                    error=f"Worktree does not exist: {worktree_path}",
                )

            # Get worktree info before deletion
            worktree_info = self.git_manager.get_worktree_info(worktree_path)

            # Check for uncommitted changes unless force is specified
            if not force:
                status = self.git_manager.get_worktree_status(worktree_path)
                if not status.get("is_clean", True):
                    return DeleteResult(
                        status=OperationResult.FAILURE,
                        error="Worktree has uncommitted changes. Use --force to override.",
                    )

            # Cleanup tmux sessions if requested
            cleanup_performed = False
            if cleanup_sessions and worktree_info:
                branch_name = worktree_info.get("branch")
                if branch_name:
                    cleanup_performed = await self._cleanup_tmux_sessions(branch_name)

            # Remove the worktree
            success = self.git_manager.remove_worktree(worktree_path, force=force)

            if success:
                return DeleteResult(
                    status=OperationResult.SUCCESS,
                    deleted_path=str(worktree_path),
                    cleanup_performed=cleanup_performed,
                )
            else:
                return DeleteResult(
                    status=OperationResult.FAILURE, error="Failed to remove worktree"
                )

        except Exception as e:
            logger.error(f"Failed to delete worktree: {e}")
            return DeleteResult(status=OperationResult.FAILURE, error=str(e))

    # Private helper methods

    async def _get_commit_message_interactive(self) -> str:
        """Get commit message interactively."""
        # This would typically open an editor or prompt
        # For now, return a placeholder
        return "Interactive commit message (TODO: implement editor)"

    async def _detect_parent_branch(self, worktree_path: Path) -> str:
        """Detect the parent branch for a worktree."""
        try:
            worktree_repo = git.Repo(worktree_path)

            # Try to find the merge base with common branches
            common_branches = ["main", "master", "develop"]

            for branch in common_branches:
                try:
                    # Check if branch exists
                    worktree_repo.git.rev_parse("--verify", branch)

                    # Check if there's a merge base
                    merge_base = worktree_repo.git.merge_base(branch, "HEAD")
                    if merge_base:
                        return branch
                except GitCommandError:
                    continue

            # Default to main
            return "main"

        except Exception:
            return "main"

    async def _get_merge_conflicts(self, repo: git.Repo) -> List[str]:
        """Get list of files with merge conflicts."""
        try:
            status = repo.git.status("--porcelain")
            conflicts = []

            for line in status.splitlines():
                if line.startswith("UU "):  # Both modified
                    conflicts.append(line[3:])
                elif line.startswith("AA "):  # Both added
                    conflicts.append(line[3:])
                elif line.startswith("DD "):  # Both deleted
                    conflicts.append(line[3:])

            return conflicts
        except Exception:
            return []

    async def _generate_pr_title(self, worktree_path: Path) -> str:
        """Generate a PR title based on commits."""
        try:
            worktree_repo = git.Repo(worktree_path)

            # Get recent commits
            commits = list(worktree_repo.iter_commits("HEAD", max_count=5))

            if commits:
                # Use the most recent commit message as title
                return commits[0].message.split("\n")[0]
            else:
                # Fallback to branch name
                branch_name = worktree_repo.active_branch.name
                return f"Changes from {branch_name}"

        except Exception:
            return "Pull request from worktree"

    async def _cleanup_tmux_sessions(self, branch_name: str) -> bool:
        """Cleanup tmux sessions associated with the branch."""
        try:
            # Kill tmux sessions that match the branch name pattern
            cmd = ["tmux", "kill-session", "-t", f"*{branch_name}*"]

            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            await result.communicate()
            return result.returncode == 0

        except Exception:
            return False
