"""Branch naming and pattern utilities."""

import re
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BranchPatternValidator:
    """Validates and formats branch names according to patterns."""
    
    def __init__(self):
        """Initialize the validator."""
        pass
    
    def format_branch_name(
        self,
        pattern: str,
        suffix: str,
        username: Optional[str] = None,
        branch_type: Optional[str] = None
    ) -> str:
        """Format a branch name according to a pattern.
        
        Args:
            pattern: Branch naming pattern (e.g., "{username}/{suffix}")
            suffix: Branch suffix/name
            username: GitHub username
            branch_type: Type of branch (feature, fix, etc.)
            
        Returns:
            Formatted branch name
        """
        # Sanitize the suffix
        safe_suffix = self.sanitize_branch_name(suffix)
        
        # Replace pattern variables
        formatted = pattern
        formatted = formatted.replace("{suffix}", safe_suffix)
        
        if username:
            formatted = formatted.replace("{username}", username)
        else:
            # Remove username patterns if no username provided
            formatted = re.sub(r'\{username\}/?', '', formatted)
        
        if branch_type:
            formatted = formatted.replace("{type}", branch_type)
        else:
            # Remove type patterns if no type provided
            formatted = re.sub(r'\{type\}/?', '', formatted)
        
        # Clean up any double slashes
        formatted = re.sub(r'/+', '/', formatted)
        
        # Remove leading/trailing slashes
        formatted = formatted.strip('/')
        
        return formatted
    
    def sanitize_branch_name(self, name: str) -> str:
        """Sanitize a branch name to be Git-compatible.
        
        Args:
            name: Raw branch name
            
        Returns:
            Sanitized branch name
        """
        # Convert to lowercase
        sanitized = name.lower()
        
        # Replace spaces and special characters with hyphens
        sanitized = re.sub(r'[^a-z0-9-_.]', '-', sanitized)
        
        # Collapse multiple hyphens
        sanitized = re.sub(r'-+', '-', sanitized)
        
        # Remove leading/trailing hyphens
        sanitized = sanitized.strip('-')
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = "branch"
        
        return sanitized
    
    def validate_branch_name(self, name: str) -> Dict[str, Any]:
        """Validate a branch name against Git rules.
        
        Args:
            name: Branch name to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check for empty name
        if not name or not name.strip():
            result["valid"] = False
            result["errors"].append("Branch name cannot be empty")
            return result
        
        # Check for invalid characters
        if re.search(r'[~^:?*\[\]\\]', name):
            result["valid"] = False
            result["errors"].append("Branch name contains invalid characters")
        
        # Check for double dots
        if ".." in name:
            result["valid"] = False
            result["errors"].append("Branch name cannot contain '..'")
        
        # Check for leading/trailing dots or slashes
        if name.startswith('.') or name.endswith('.'):
            result["valid"] = False
            result["errors"].append("Branch name cannot start or end with '.'")
        
        if name.startswith('/') or name.endswith('/'):
            result["valid"] = False
            result["errors"].append("Branch name cannot start or end with '/'")
        
        # Check for control characters
        if re.search(r'[\x00-\x1f\x7f]', name):
            result["valid"] = False
            result["errors"].append("Branch name contains control characters")
        
        # Check for spaces (warning, not error)
        if ' ' in name:
            result["warnings"].append("Branch name contains spaces (will be converted to hyphens)")
        
        # Check length
        if len(name) > 250:
            result["valid"] = False
            result["errors"].append("Branch name is too long (max 250 characters)")
        
        return result
    
    def suggest_branch_name(
        self,
        description: str,
        username: Optional[str] = None,
        branch_type: str = "feature"
    ) -> str:
        """Suggest a branch name based on a description.
        
        Args:
            description: Description of the work
            username: GitHub username
            branch_type: Type of branch
            
        Returns:
            Suggested branch name
        """
        # Extract meaningful words
        words = re.findall(r'\w+', description.lower())
        
        # Limit to first 3-4 meaningful words
        meaningful_words = [w for w in words if len(w) > 2][:4]
        
        if not meaningful_words:
            suffix = "update"
        else:
            suffix = "-".join(meaningful_words)
        
        # Apply pattern
        if username:
            pattern = "{username}/{type}/{suffix}"
        else:
            pattern = "{type}/{suffix}"
        
        return self.format_branch_name(pattern, suffix, username, branch_type)
    
    def extract_branch_info(self, branch_name: str) -> Dict[str, Optional[str]]:
        """Extract information from a branch name.
        
        Args:
            branch_name: Full branch name
            
        Returns:
            Dictionary with extracted information
        """
        info = {
            "username": None,
            "type": None,
            "suffix": None
        }
        
        parts = branch_name.split('/')
        
        if len(parts) == 1:
            # Simple branch name
            info["suffix"] = parts[0]
        elif len(parts) == 2:
            # Could be username/suffix or type/suffix
            if parts[0] in ["feature", "fix", "hotfix", "bugfix", "chore", "docs"]:
                info["type"] = parts[0]
                info["suffix"] = parts[1]
            else:
                info["username"] = parts[0]
                info["suffix"] = parts[1]
        elif len(parts) == 3:
            # username/type/suffix
            info["username"] = parts[0]
            info["type"] = parts[1]
            info["suffix"] = parts[2]
        else:
            # Complex structure, take last part as suffix
            info["suffix"] = parts[-1]
            if len(parts) > 1:
                info["type"] = parts[-2]
            if len(parts) > 2:
                info["username"] = parts[0]
        
        return info