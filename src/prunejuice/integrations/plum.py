"""Integration with worktree management - Native Python implementation."""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
import json

from ..worktree_utils import GitWorktreeManager, FileManager, BranchPatternValidator

logger = logging.getLogger(__name__)


class PlumIntegration:
    """Integration with worktree management using native Python implementation."""
    
    def __init__(self, plum_path: Optional[Path] = None):
        """Initialize worktree integration.
        
        Args:
            plum_path: Legacy parameter for compatibility (ignored)
        """
        # Use native implementations instead of shell scripts
        self._use_native = True
    
    async def create_worktree(
        self,
        project_path: Path,
        branch_name: str
    ) -> Path:
        """Create a new worktree and return its path using native Git operations."""
        try:
            # Use native Git worktree manager
            git_manager = GitWorktreeManager(project_path)
            file_manager = FileManager(project_path)
            
            # Create the worktree
            worktree_path = await git_manager.create_worktree(branch_name)
            
            # Copy default files to the new worktree
            default_files = file_manager.get_default_files_to_copy()
            await file_manager.copy_files(worktree_path, default_files)
            
            # Handle MCP templates if they exist
            await file_manager.handle_mcp_templates(worktree_path)
            
            logger.info(f"Created worktree with native Python: {worktree_path}")
            return worktree_path
            
        except Exception as e:
            logger.error(f"Failed to create worktree: {e}")
            raise RuntimeError(f"Failed to create worktree: {e}")
    
    async def list_worktrees(self, project_path: Path) -> List[Dict[str, Any]]:
        """List all worktrees for the project using native Git operations."""
        try:
            git_manager = GitWorktreeManager(project_path)
            worktrees = await git_manager.list_worktrees()
            
            logger.debug(f"Listed {len(worktrees)} worktrees using native Python")
            return worktrees
            
        except Exception as e:
            logger.error(f"Failed to list worktrees: {e}")
            return []
    
    async def remove_worktree(self, project_path: Path, worktree_path: Path) -> bool:
        """Remove a worktree using native Git operations."""
        try:
            git_manager = GitWorktreeManager(project_path)
            success = await git_manager.remove_worktree(worktree_path)
            
            if success:
                logger.info(f"Removed worktree with native Python: {worktree_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to remove worktree: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if worktree functionality is available."""
        # Always available since we use native Python + Git
        return True