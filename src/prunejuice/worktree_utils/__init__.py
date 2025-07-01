"""Worktree management utilities - Native Python implementation replacing plum shell scripts."""

from .git_operations import GitWorktreeManager
from .file_operations import FileManager
from .branch_utils import BranchPatternValidator
from .operations import WorktreeOperations, CommitResult, MergeResult, PRResult, DeleteResult
from .commit import (
    CommitStatusAnalyzer,
    InteractiveStaging,
    CommitMessageEditor,
    CommitExecutor,
    FileInfo,
    CommitAnalysis,
)

__all__ = [
    "GitWorktreeManager",
    "FileManager", 
    "BranchPatternValidator",
    "WorktreeOperations",
    "CommitResult",
    "MergeResult", 
    "PRResult",
    "DeleteResult",
    "CommitStatusAnalyzer",
    "InteractiveStaging",
    "CommitMessageEditor",
    "CommitExecutor",
    "FileInfo",
    "CommitAnalysis",
]
