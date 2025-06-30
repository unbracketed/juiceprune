"""Session management for PruneJuice commands."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
from enum import Enum

from .models import StepStatus
from ..worktree_utils import GitWorktreeManager, FileManager
from ..session_utils import TmuxManager, SessionLifecycleManager


class SessionStatus(str, Enum):
    """Status of a command session."""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class StepExecution(BaseModel):
    """Record of a step execution."""

    name: str
    status: StepStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    output: Optional[str] = None
    error: Optional[str] = None


class Session(BaseModel):
    """Central session management for command execution."""

    id: str
    command_name: str
    project_path: Path
    worktree_path: Optional[Path] = None
    tmux_session_name: Optional[str] = None
    shared_data: Dict[str, Any] = Field(default_factory=dict)
    step_history: List[StepExecution] = Field(default_factory=list)
    artifact_dir: Path
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def get_context(self) -> Dict[str, Any]:
        """Get execution context for steps - replaces manual context building."""
        context = {
            "session_id": self.id,
            "command_name": self.command_name,
            "project_path": self.project_path,
            "worktree_path": self.worktree_path,
            "tmux_session": self.tmux_session_name,
            "artifact_dir": self.artifact_dir,
            "shared_data": self.shared_data,
            "step_history": self.step_history,
            "working_directory": str(self.worktree_path or self.project_path),
        }

        # Add data from shared_data to root level for backward compatibility
        if "args" in self.shared_data:
            context["args"] = self.shared_data["args"]
        if "environment" in self.shared_data:
            context["environment"] = self.shared_data["environment"]
        if "event_id" in self.shared_data:
            context["event_id"] = self.shared_data["event_id"]

        return context

    def add_step_result(
        self, step_name: str, success: bool, output: str, error: Optional[str] = None
    ):
        """Record step execution result."""
        step_execution = StepExecution(
            name=step_name,
            status=StepStatus.COMPLETED if success else StepStatus.FAILED,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            output=output,
            error=error,
        )
        self.step_history.append(step_execution)

    def set_shared_data(self, key: str, value: Any):
        """Store shared data for steps to access."""
        self.shared_data[key] = value

    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """Retrieve shared data."""
        return self.shared_data.get(key, default)

    async def create_tmux_session(self) -> str:
        """Create tmux session and store session name."""
        tmux_manager = TmuxManager()
        session_manager = SessionLifecycleManager(tmux_manager)

        session_name = session_manager.create_session_for_worktree(
            self.worktree_path or self.project_path,
            self.command_name,
            auto_attach=False,
        )

        if not session_name:
            # Fallback session name if creation failed
            session_name = f"prunejuice-{self.command_name}"

        self.tmux_session_name = session_name
        return session_name

    async def create_worktree(
        self, branch_name: str, base_branch: str = "main"
    ) -> Path:
        """Create worktree and store worktree path."""
        git_manager = GitWorktreeManager(self.project_path)
        file_manager = FileManager(self.project_path)

        # Create the worktree
        worktree_path = git_manager.create_worktree(branch_name, base_branch)

        # Copy default files to the new worktree
        default_files = file_manager.get_default_files_to_copy()
        file_manager.copy_files(worktree_path, default_files)

        # Handle MCP templates if they exist
        file_manager.handle_mcp_templates(worktree_path)

        self.worktree_path = worktree_path
        return worktree_path
