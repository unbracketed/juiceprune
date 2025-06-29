"""Pydantic data models for PruneJuice."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class StepStatus(str, Enum):
    """Status of a command step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CommandArgument(BaseModel):
    """Definition of a command argument."""
    name: str
    required: bool = True
    type: str = "string"
    default: Optional[Any] = None
    description: Optional[str] = None


class CommandStep(BaseModel):
    """Individual step in a command."""
    name: str
    args: Dict[str, Any] = Field(default_factory=dict)
    script: Optional[str] = None
    timeout: int = 300


class CommandDefinition(BaseModel):
    """Complete command definition."""
    name: str
    description: str
    extends: Optional[str] = None
    category: str = "workflow"
    arguments: List[CommandArgument] = Field(default_factory=list)
    environment: Dict[str, str] = Field(default_factory=dict)
    pre_steps: List[str] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    post_steps: List[str] = Field(default_factory=list)
    cleanup_on_failure: List[str] = Field(default_factory=list)
    working_directory: Optional[str] = None
    timeout: int = 1800


class ExecutionEvent(BaseModel):
    """Event tracking for command execution."""
    id: Optional[int] = None
    command: str
    project_path: str
    worktree_name: Optional[str] = None
    session_id: str
    artifacts_path: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: str = "running"
    exit_code: Optional[int] = None
    error_message: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None


class ExecutionResult(BaseModel):
    """Result of command execution."""
    success: bool
    error: Optional[str] = None
    output: Optional[str] = None
    artifacts_path: Optional[str] = None


class StepError(Exception):
    """Exception raised when a step fails."""
    pass