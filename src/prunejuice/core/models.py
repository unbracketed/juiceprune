"""Pydantic data models for PruneJuice."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Union
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


class StepType(str, Enum):
    """Type of step execution."""

    BUILTIN = "builtin"
    SCRIPT = "script"
    SHELL = "shell"


class CommandStep(BaseModel):
    """Individual step in a command."""

    name: str
    type: StepType = StepType.BUILTIN
    action: str
    args: Dict[str, Any] = Field(default_factory=dict)
    script: Optional[str] = None
    timeout: int = 300

    @field_validator("type", mode="before")
    @classmethod
    def validate_step_type(cls, v):
        """Handle both string and StepType values."""
        if isinstance(v, str):
            try:
                return StepType(v)
            except ValueError:
                # Default to BUILTIN for unknown types
                return StepType.BUILTIN
        return v

    def model_dump(self, **kwargs):
        """Custom model dump that serializes enums as their values."""
        data = super().model_dump(**kwargs)
        if "type" in data and hasattr(data["type"], "value"):
            data["type"] = data["type"].value
        return data

    @classmethod
    def from_string(cls, step_str: str) -> "CommandStep":
        """Create a CommandStep from a string (for backward compatibility)."""
        # Auto-detect step type based on content
        if " " in step_str or any(
            op in step_str for op in ["|", "&&", ";", ">", "<", "$"]
        ):
            return cls(name=step_str, type=StepType.SHELL, action=step_str)
        elif step_str.endswith(".py") or step_str.endswith(".sh"):
            return cls(name=step_str, type=StepType.SCRIPT, action=step_str)
        else:
            return cls(name=step_str, type=StepType.BUILTIN, action=step_str)


class ActionDefintion(BaseModel):
    """Complete command definition."""

    name: str
    description: str
    prompt_file: Optional[str] = None
    extends: Optional[str] = None
    category: str = "workflow"
    arguments: List[CommandArgument] = Field(default_factory=list)
    environment: Dict[str, str] = Field(default_factory=dict)
    pre_steps: List[Union[str, CommandStep]] = Field(default_factory=list)
    steps: List[Union[str, CommandStep]] = Field(default_factory=list)
    post_steps: List[Union[str, CommandStep]] = Field(default_factory=list)
    cleanup_on_failure: List[Union[str, CommandStep]] = Field(default_factory=list)
    working_directory: Optional[str] = None
    timeout: int = 1800

    @field_validator(
        "pre_steps", "steps", "post_steps", "cleanup_on_failure", mode="before"
    )
    @classmethod
    def convert_string_steps(cls, v):
        """Convert string steps to CommandStep objects for backward compatibility."""
        if isinstance(v, list):
            return [
                CommandStep.from_string(step) if isinstance(step, str) else step
                for step in v
            ]
        return v

    def model_dump(self, **kwargs):
        """Custom model dump that properly serializes step enums."""
        data = super().model_dump(**kwargs)

        # Fix step enum serialization
        for step_list_key in ["pre_steps", "steps", "post_steps", "cleanup_on_failure"]:
            if step_list_key in data and isinstance(data[step_list_key], list):
                for step in data[step_list_key]:
                    if (
                        isinstance(step, dict)
                        and "type" in step
                        and hasattr(step["type"], "value")
                    ):
                        step["type"] = step["type"].value

        return data

    def get_all_steps(self) -> List[CommandStep]:
        """Get all steps as CommandStep objects."""
        all_steps = []
        for step_list in [self.pre_steps, self.steps, self.post_steps]:
            for step in step_list:
                if isinstance(step, str):
                    all_steps.append(CommandStep.from_string(step))
                else:
                    all_steps.append(step)
        return all_steps


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
