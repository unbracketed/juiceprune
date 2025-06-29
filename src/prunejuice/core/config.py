"""Configuration management for PruneJuice."""

from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database settings
    db_path: Path = Field(
        default_factory=lambda: Path.cwd() / ".prj" / "prunejuice.db",
        description="Path to SQLite database"
    )
    
    # Artifact storage
    artifacts_dir: Path = Field(
        default_factory=lambda: Path.cwd() / ".prj" / "artifacts",
        description="Directory for storing artifacts"
    )
    
    # Integration paths
    plum_path: Optional[Path] = Field(
        default=None,
        description="Path to plum executable"
    )
    
    pots_path: Optional[Path] = Field(
        default=None,
        description="Path to pots executable"
    )
    
    # Execution settings
    default_timeout: int = Field(
        default=1800,
        description="Default command timeout in seconds"
    )
    
    max_parallel_steps: int = Field(
        default=1,
        description="Maximum parallel steps (currently only 1 supported)"
    )
    
    # Environment
    github_username: Optional[str] = Field(
        default=None,
        description="GitHub username for PR operations"
    )
    
    editor: str = Field(
        default="code",
        description="Editor command"
    )
    
    base_dir: Optional[Path] = Field(
        default=None,
        description="Base directory for worktrees"
    )
    
    model_config = {
        "env_prefix": "PRUNEJUICE_",
        "env_file": ".env", 
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }
        
    def __init__(self, **kwargs):
        """Initialize settings and create directories."""
        super().__init__(**kwargs)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)