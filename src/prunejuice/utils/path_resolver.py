"""Project path resolution utilities for Git-aware configuration."""

from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ProjectPathResolver:
    """Centralized Git-aware path resolution for PruneJuice projects."""
    
    @staticmethod
    def get_project_root(start_path: Optional[Path] = None) -> Path:
        """Find main Git repository root, fallback to current path.
        
        Args:
            start_path: Starting path for search (defaults to current directory)
            
        Returns:
            Path to main Git repository root or start_path if not in Git repo
        """
        if start_path is None:
            start_path = Path.cwd()
            
        try:
            from ..worktree_utils import GitWorktreeManager
            
            manager = GitWorktreeManager(start_path)
            if manager.is_git_repository():
                main_path = manager.get_main_worktree_path()
                logger.debug(f"Found Git repository root: {main_path}")
                return main_path
        except Exception as e:
            logger.debug(f"Git repository detection failed: {e}")
            
        logger.debug(f"Using fallback path: {start_path}")
        return start_path
    
    @staticmethod
    def resolve_database_path(project_path: Optional[Path] = None) -> Path:
        """Resolve database path for project.
        
        Args:
            project_path: Project root path (auto-detected if None)
            
        Returns:
            Path to project database file
        """
        if project_path is None:
            project_path = ProjectPathResolver.get_project_root()
            
        return project_path / ".prj" / "prunejuice.db"
    
    @staticmethod
    def resolve_artifacts_path(project_path: Optional[Path] = None) -> Path:
        """Resolve artifacts directory path for project.
        
        Args:
            project_path: Project root path (auto-detected if None)
            
        Returns:
            Path to project artifacts directory
        """
        if project_path is None:
            project_path = ProjectPathResolver.get_project_root()
            
        return project_path / ".prj" / "artifacts"