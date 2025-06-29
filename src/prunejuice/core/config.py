"""Configuration management for PruneJuice."""

from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from typing import Optional
from ..utils.path_resolver import ProjectPathResolver


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database settings
    db_path: Path = Field(
        default_factory=lambda: ProjectPathResolver.resolve_database_path(),
        description="Path to SQLite database",
    )

    # Artifact storage
    artifacts_dir: Path = Field(
        default_factory=lambda: ProjectPathResolver.resolve_artifacts_path(),
        description="Directory for storing artifacts",
    )

    # Execution settings
    default_timeout: int = Field(
        default=1800, description="Default command timeout in seconds"
    )

    max_parallel_steps: int = Field(
        default=1, description="Maximum parallel steps (currently only 1 supported)"
    )

    # Environment
    github_username: Optional[str] = Field(
        default=None, description="GitHub username for PR operations"
    )

    editor: str = Field(default="code", description="Editor command")

    base_dir: Optional[Path] = Field(
        default=None, description="Base directory for worktrees"
    )

    model_config = {
        "env_prefix": "PRUNEJUICE_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def __init__(self, project_path: Optional[Path] = None, **kwargs):
        """Initialize settings with optional project path override.

        Args:
            project_path: Override project root path (for testing/special cases)
            **kwargs: Additional settings overrides
        """
        # Override paths if project_path is provided
        if project_path is not None:
            kwargs.setdefault("db_path", project_path / ".prj" / "prunejuice.db")
            kwargs.setdefault("artifacts_dir", project_path / ".prj" / "artifacts")

        super().__init__(**kwargs)

        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
