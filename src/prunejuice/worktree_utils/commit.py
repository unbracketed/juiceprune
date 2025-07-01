"""Specialized commit operations and components for worktree management."""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import git
from git.exc import GitCommandError

logger = logging.getLogger(__name__)


class FileStatus(Enum):
    """Git file status indicators."""

    ADDED = "A"
    MODIFIED = "M"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"
    UPDATED_UNMERGED = "U"
    UNTRACKED = "?"


@dataclass
class FileInfo:
    """Information about a file in the git working directory."""

    path: str
    status: FileStatus
    staged: bool = False
    size: Optional[int] = None
    lines_added: Optional[int] = None
    lines_removed: Optional[int] = None


@dataclass
class CommitAnalysis:
    """Analysis of the current commit state."""

    staged_files: List[FileInfo]
    unstaged_files: List[FileInfo]
    untracked_files: List[FileInfo]
    total_changes: int
    can_commit: bool
    has_conflicts: bool
    current_branch: Optional[str] = None


class CommitStatusAnalyzer:
    """Analyzes the current state of a worktree for commit operations."""

    def __init__(self, worktree_path: Path):
        """Initialize with worktree path."""
        self.worktree_path = worktree_path
        self.repo = git.Repo(worktree_path)

    def analyze(self) -> CommitAnalysis:
        """Analyze the current commit state.

        Returns:
            CommitAnalysis with complete status information
        """
        try:
            # Get git status
            status_output = self.repo.git.status("--porcelain=v1")

            staged_files = []
            unstaged_files = []
            untracked_files = []
            has_conflicts = False

            for line in status_output.splitlines():
                if len(line) >= 3:
                    staged_status = line[0]
                    unstaged_status = line[1]
                    filepath = line[3:]

                    # Check for conflicts
                    if staged_status == "U" or unstaged_status == "U":
                        has_conflicts = True

                    # Process staged changes
                    if staged_status != " " and staged_status != "?":
                        file_info = self._create_file_info(
                            filepath, FileStatus(staged_status), staged=True
                        )
                        staged_files.append(file_info)

                    # Process unstaged changes
                    if unstaged_status != " ":
                        if unstaged_status == "?":
                            file_info = FileInfo(
                                path=filepath, status=FileStatus.UNTRACKED, staged=False
                            )
                            untracked_files.append(file_info)
                        else:
                            file_info = self._create_file_info(
                                filepath, FileStatus(unstaged_status), staged=False
                            )
                            unstaged_files.append(file_info)

            # Calculate totals
            total_changes = (
                len(staged_files) + len(unstaged_files) + len(untracked_files)
            )
            can_commit = len(staged_files) > 0 and not has_conflicts

            # Get current branch
            current_branch = None
            try:
                current_branch = self.repo.active_branch.name
            except Exception:
                # Handle detached HEAD
                current_branch = "HEAD (detached)"

            return CommitAnalysis(
                staged_files=staged_files,
                unstaged_files=unstaged_files,
                untracked_files=untracked_files,
                total_changes=total_changes,
                can_commit=can_commit,
                has_conflicts=has_conflicts,
                current_branch=current_branch,
            )

        except Exception as e:
            logger.error(f"Failed to analyze commit status: {e}")
            return CommitAnalysis(
                staged_files=[],
                unstaged_files=[],
                untracked_files=[],
                total_changes=0,
                can_commit=False,
                has_conflicts=False,
            )

    def _create_file_info(
        self, filepath: str, status: FileStatus, staged: bool
    ) -> FileInfo:
        """Create FileInfo with additional metadata."""
        file_info = FileInfo(path=filepath, status=status, staged=staged)

        try:
            # Get file size if it exists
            full_path = self.worktree_path / filepath
            if full_path.exists() and full_path.is_file():
                file_info.size = full_path.stat().st_size

            # Get diff stats for modifications
            if status in [FileStatus.MODIFIED, FileStatus.ADDED]:
                diff_stats = self._get_file_diff_stats(filepath, staged)
                file_info.lines_added = diff_stats.get("lines_added", 0)
                file_info.lines_removed = diff_stats.get("lines_removed", 0)

        except Exception as e:
            logger.debug(f"Could not get file metadata for {filepath}: {e}")

        return file_info

    def _get_file_diff_stats(self, filepath: str, staged: bool) -> Dict[str, int]:
        """Get diff statistics for a file."""
        try:
            if staged:
                # Staged changes (diff between index and HEAD)
                diff_output = self.repo.git.diff(
                    "--cached", "--numstat", "--", filepath
                )
            else:
                # Unstaged changes (diff between working tree and index)
                diff_output = self.repo.git.diff("--numstat", "--", filepath)

            if diff_output.strip():
                parts = diff_output.strip().split("\t")
                if len(parts) >= 2:
                    return {
                        "lines_added": int(parts[0]) if parts[0] != "-" else 0,
                        "lines_removed": int(parts[1]) if parts[1] != "-" else 0,
                    }

        except Exception as e:
            logger.debug(f"Could not get diff stats for {filepath}: {e}")

        return {"lines_added": 0, "lines_removed": 0}


class InteractiveStaging:
    """Handles interactive staging of files for commits."""

    def __init__(self, worktree_path: Path):
        """Initialize with worktree path."""
        self.worktree_path = worktree_path
        self.repo = git.Repo(worktree_path)
        self.analyzer = CommitStatusAnalyzer(worktree_path)

    async def stage_files(self, filepaths: List[str]) -> bool:
        """Stage specific files.

        Args:
            filepaths: List of file paths to stage

        Returns:
            True if successful, False otherwise
        """
        try:
            for filepath in filepaths:
                self.repo.git.add(filepath)
            logger.info(f"Staged {len(filepaths)} files")
            return True
        except GitCommandError as e:
            logger.error(f"Failed to stage files: {e}")
            return False

    async def unstage_files(self, filepaths: List[str]) -> bool:
        """Unstage specific files.

        Args:
            filepaths: List of file paths to unstage

        Returns:
            True if successful, False otherwise
        """
        try:
            for filepath in filepaths:
                self.repo.git.reset("HEAD", "--", filepath)
            logger.info(f"Unstaged {len(filepaths)} files")
            return True
        except GitCommandError as e:
            logger.error(f"Failed to unstage files: {e}")
            return False

    async def stage_all_changes(self) -> bool:
        """Stage all changes including untracked files.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.repo.git.add(".")
            logger.info("Staged all changes")
            return True
        except GitCommandError as e:
            logger.error(f"Failed to stage all changes: {e}")
            return False

    async def unstage_all_changes(self) -> bool:
        """Unstage all currently staged changes.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.repo.git.reset("HEAD")
            logger.info("Unstaged all changes")
            return True
        except GitCommandError as e:
            logger.error(f"Failed to unstage all changes: {e}")
            return False

    def get_file_diff(
        self, filepath: str, staged: bool = False, context_lines: int = 3
    ) -> str:
        """Get diff for a specific file.

        Args:
            filepath: Path to the file
            staged: Whether to show staged or unstaged diff
            context_lines: Number of context lines

        Returns:
            Diff output as string
        """
        try:
            if staged:
                return self.repo.git.diff(
                    "--cached", f"-U{context_lines}", "--", filepath
                )
            else:
                return self.repo.git.diff(f"-U{context_lines}", "--", filepath)
        except GitCommandError as e:
            logger.error(f"Failed to get diff for {filepath}: {e}")
            return ""


class CommitMessageEditor:
    """Handles commit message creation and validation."""

    def __init__(self, worktree_path: Path):
        """Initialize with worktree path."""
        self.worktree_path = worktree_path
        self.repo = git.Repo(worktree_path)

    async def get_commit_message_interactive(
        self, template: Optional[str] = None, include_diff: bool = False
    ) -> Optional[str]:
        """Get commit message using interactive editor.

        Args:
            template: Optional message template
            include_diff: Whether to include diff in editor

        Returns:
            Commit message or None if cancelled
        """
        try:
            # Create temporary file for commit message
            with tempfile.NamedTemporaryFile(
                mode="w+", suffix=".txt", prefix="COMMIT_EDITMSG_", delete=False
            ) as f:
                # Write template if provided
                if template:
                    f.write(template)
                    f.write("\n\n")

                # Add helpful comments
                f.write("\n# Please enter the commit message for your changes.\n")
                f.write("# Lines starting with '#' will be ignored.\n")
                f.write("# An empty message aborts the commit.\n")

                # Add file status information
                analysis = CommitStatusAnalyzer(self.worktree_path).analyze()
                if analysis.staged_files:
                    f.write("#\n# Changes to be committed:\n")
                    for file_info in analysis.staged_files:
                        f.write(f"#\t{file_info.status.value}:\t{file_info.path}\n")

                if analysis.unstaged_files:
                    f.write("#\n# Changes not staged for commit:\n")
                    for file_info in analysis.unstaged_files:
                        f.write(f"#\t{file_info.status.value}:\t{file_info.path}\n")

                if analysis.untracked_files:
                    f.write("#\n# Untracked files:\n")
                    for file_info in analysis.untracked_files:
                        f.write(f"#\t{file_info.path}\n")

                # Include diff if requested
                if include_diff:
                    try:
                        diff_output = self.repo.git.diff("--cached")
                        if diff_output:
                            f.write("#\n# Diff of changes to be committed:\n")
                            for line in diff_output.split("\n"):
                                f.write(f"# {line}\n")
                    except Exception:
                        pass

                temp_file_path = f.name

            # Open editor
            editor = os.environ.get("EDITOR", "nano")
            process = await asyncio.create_subprocess_exec(
                editor,
                temp_file_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            await process.communicate()

            # Read the result
            with open(temp_file_path, "r") as f:
                content = f.read()

            # Clean up temp file
            os.unlink(temp_file_path)

            # Process the commit message
            message = self._process_commit_message(content)

            return message if message.strip() else None

        except Exception as e:
            logger.error(f"Failed to get interactive commit message: {e}")
            return None

    def _process_commit_message(self, raw_message: str) -> str:
        """Process raw commit message by removing comments and empty lines."""
        lines = []
        for line in raw_message.split("\n"):
            # Skip comment lines
            if line.startswith("#"):
                continue
            lines.append(line)

        # Join lines and strip trailing whitespace
        message = "\n".join(lines).rstrip()
        return message

    def validate_commit_message(self, message: str) -> Tuple[bool, Optional[str]]:
        """Validate commit message format.

        Args:
            message: Commit message to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not message.strip():
            return False, "Commit message cannot be empty"

        lines = message.split("\n")

        # Check first line length (conventional limit is 50 chars for subject)
        if len(lines[0]) > 72:
            return False, "First line should be 72 characters or less"

        # Check for blank line after subject if there's a body
        if len(lines) > 1 and lines[1].strip():
            return False, "Second line should be blank to separate subject from body"

        return True, None

    def generate_conventional_commit_template(
        self,
        commit_type: str = "feat",
        scope: Optional[str] = None,
        breaking: bool = False,
    ) -> str:
        """Generate a conventional commit message template.

        Args:
            commit_type: Type of commit (feat, fix, docs, etc.)
            scope: Optional scope for the commit
            breaking: Whether this is a breaking change

        Returns:
            Conventional commit template
        """
        template = commit_type

        if scope:
            template += f"({scope})"

        if breaking:
            template += "!"

        template += ": "

        return template


class CommitExecutor:
    """Executes commit operations with rollback capability."""

    def __init__(self, worktree_path: Path):
        """Initialize with worktree path."""
        self.worktree_path = worktree_path
        self.repo = git.Repo(worktree_path)

    async def execute_commit(
        self, message: str, author: Optional[str] = None, allow_empty: bool = False
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Execute a commit with the given message.

        Args:
            message: Commit message
            author: Optional author override
            allow_empty: Whether to allow empty commits

        Returns:
            Tuple of (success, commit_hash, error_message)
        """
        try:
            # Validate that there are staged changes unless allowing empty
            if not allow_empty:
                status = self.repo.git.status("--porcelain")
                staged_changes = [
                    line
                    for line in status.split("\n")
                    if line and line[0] != " " and line[0] != "?"
                ]

                if not staged_changes:
                    return False, None, "No staged changes to commit"

            # Prepare commit arguments
            commit_args = ["-m", message]

            if author:
                commit_args.extend(["--author", author])

            if allow_empty:
                commit_args.append("--allow-empty")

            # Execute the commit
            self.repo.git.commit(*commit_args)

            # Get the commit hash
            commit_hash = self.repo.head.commit.hexsha

            logger.info(f"Successfully created commit: {commit_hash[:8]}")
            return True, commit_hash, None

        except GitCommandError as e:
            error_msg = str(e)
            logger.error(f"Failed to execute commit: {error_msg}")
            return False, None, error_msg

    async def amend_last_commit(
        self, new_message: Optional[str] = None, no_edit: bool = False
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Amend the last commit.

        Args:
            new_message: New commit message (if None, keeps existing)
            no_edit: Don't open editor for message

        Returns:
            Tuple of (success, commit_hash, error_message)
        """
        try:
            commit_args = ["--amend"]

            if no_edit:
                commit_args.append("--no-edit")

            if new_message:
                commit_args.extend(["-m", new_message])

            self.repo.git.commit(*commit_args)
            commit_hash = self.repo.head.commit.hexsha

            logger.info(f"Successfully amended commit: {commit_hash[:8]}")
            return True, commit_hash, None

        except GitCommandError as e:
            error_msg = str(e)
            logger.error(f"Failed to amend commit: {error_msg}")
            return False, None, error_msg

    def get_last_commit_info(self) -> Dict[str, Any]:
        """Get information about the last commit.

        Returns:
            Dictionary with commit information
        """
        try:
            last_commit = self.repo.head.commit

            return {
                "hash": last_commit.hexsha,
                "short_hash": last_commit.hexsha[:8],
                "message": last_commit.message.strip(),
                "author": str(last_commit.author),
                "date": last_commit.committed_datetime.isoformat(),
                "files_changed": len(last_commit.stats.files),
            }

        except Exception as e:
            logger.error(f"Failed to get last commit info: {e}")
            return {}
