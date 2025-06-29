"""File operations for worktree management."""

import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class FileManager:
    """Native Python implementation of file operations for worktrees."""
    
    def __init__(self, source_root: Path):
        """Initialize with source root directory."""
        self.source_root = source_root
    
    def copy_files(
        self,
        target_root: Path,
        files_to_copy: List[str],
        create_target_dirs: bool = True
    ) -> Dict[str, Any]:
        """Copy files from source to target worktree.
        
        Args:
            target_root: Target worktree directory
            files_to_copy: List of relative file paths to copy
            create_target_dirs: Whether to create target directories
            
        Returns:
            Dictionary with copy results and statistics
        """
        results = {
            "copied": [],
            "failed": [],
            "skipped": [],
            "copied_count": 0,
            "failed_count": 0,
            "skipped_count": 0
        }
        
        logger.info(f"Copying {len(files_to_copy)} files to {target_root}")
        
        for file_path in files_to_copy:
            source_file = self.source_root / file_path
            target_file = target_root / file_path
            
            try:
                if not source_file.exists():
                    results["skipped"].append(file_path)
                    results["skipped_count"] += 1
                    logger.debug(f"Skipped missing file: {file_path}")
                    continue
                
                if create_target_dirs:
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                
                if source_file.is_file():
                    shutil.copy2(source_file, target_file)
                    results["copied"].append(file_path)
                    results["copied_count"] += 1
                    logger.debug(f"Copied file: {file_path}")
                elif source_file.is_dir():
                    shutil.copytree(source_file, target_file, dirs_exist_ok=True)
                    results["copied"].append(file_path)
                    results["copied_count"] += 1
                    logger.debug(f"Copied directory: {file_path}")
                else:
                    results["skipped"].append(file_path)
                    results["skipped_count"] += 1
                    logger.debug(f"Skipped non-file/directory: {file_path}")
                    
            except Exception as e:
                results["failed"].append({"path": file_path, "error": str(e)})
                results["failed_count"] += 1
                logger.error(f"Failed to copy {file_path}: {e}")
        
        logger.info(f"Copy results: {results['copied_count']} copied, "
                   f"{results['failed_count']} failed, {results['skipped_count']} skipped")
        
        return results
    
    def copy_files_with_patterns(
        self,
        target_root: Path,
        patterns: List[str]
    ) -> Dict[str, Any]:
        """Copy files matching glob patterns.
        
        Args:
            target_root: Target worktree directory
            patterns: List of glob patterns to match
            
        Returns:
            Dictionary with copy results and statistics
        """
        results = {
            "copied": [],
            "failed": [],
            "copied_count": 0,
            "failed_count": 0
        }
        
        logger.info(f"Copying files matching {len(patterns)} patterns to {target_root}")
        
        for pattern in patterns:
            try:
                matched_files = list(self.source_root.glob(pattern))
                
                for source_file in matched_files:
                    if not source_file.is_file():
                        continue
                    
                    # Get relative path
                    rel_path = source_file.relative_to(self.source_root)
                    target_file = target_root / rel_path
                    
                    try:
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_file, target_file)
                        results["copied"].append(str(rel_path))
                        results["copied_count"] += 1
                        logger.debug(f"Copied pattern match: {rel_path}")
                        
                    except Exception as e:
                        results["failed"].append({"path": str(rel_path), "error": str(e)})
                        results["failed_count"] += 1
                        logger.error(f"Failed to copy {rel_path}: {e}")
                        
            except Exception as e:
                logger.error(f"Failed to process pattern '{pattern}': {e}")
        
        logger.info(f"Pattern copy results: {results['copied_count']} copied, "
                   f"{results['failed_count']} failed")
        
        return results
    
    def handle_mcp_templates(
        self,
        target_root: Path,
        template_dir: str = "mcp-json-templates",
        template_name: Optional[str] = None
    ) -> bool:
        """Handle MCP template copying and activation.
        
        Args:
            target_root: Target worktree directory
            template_dir: Directory containing MCP templates
            template_name: Specific template to activate (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            source_template_dir = self.source_root / template_dir
            
            if not source_template_dir.exists():
                logger.debug(f"MCP template directory not found: {source_template_dir}")
                return True  # Not an error if no templates exist
            
            target_template_dir = target_root / template_dir
            
            # Copy the entire template directory
            if source_template_dir.is_dir():
                shutil.copytree(source_template_dir, target_template_dir, dirs_exist_ok=True)
                logger.info(f"Copied MCP templates to {target_template_dir}")
            
            # Activate specific template if requested
            if template_name:
                template_file = target_template_dir / f".mcp.{template_name}.json"
                active_template = target_root / ".mcp.json"
                
                if template_file.exists():
                    shutil.copy2(template_file, active_template)
                    logger.info(f"Activated MCP template: {template_name}")
                else:
                    logger.warning(f"MCP template not found: {template_name}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle MCP templates: {e}")
            return False
    
    def get_default_files_to_copy(self) -> List[str]:
        """Get default list of files to copy to new worktrees.
        
        Returns:
            List of default file paths
        """
        return [
            ".vscode/tasks.json",
            ".vscode/settings.json", 
            ".vscode/launch.json",
            "mcp-json-templates/.secrets",
            ".env.example",
            ".gitignore"
        ]
    
    def validate_file_paths(self, file_paths: List[str]) -> List[str]:
        """Validate and filter file paths for security.
        
        Args:
            file_paths: List of file paths to validate
            
        Returns:
            List of validated file paths
        """
        validated = []
        
        for file_path in file_paths:
            path = Path(file_path)
            
            # Check for path traversal attempts
            if ".." in path.parts:
                logger.warning(f"Skipping path with traversal: {file_path}")
                continue
            
            # Check for absolute paths
            if path.is_absolute():
                logger.warning(f"Skipping absolute path: {file_path}")
                continue
            
            validated.append(file_path)
        
        return validated