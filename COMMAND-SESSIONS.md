# Command Sessions Implementation Plan

## Overview

This document outlines the implementation plan for three new features in PruneJuice:

1. **prompt_file property** - Add location of text/markdown file containing prompt text to Commands
2. **Session model** - Create a unified Session type/model for running Commands with shared session data and step history
3. **Base Command hierarchy** - Implement Commands/Base Command that automatically creates worktree and starts detached session before running steps

## Current Architecture Analysis

### Strengths
- Good modular design with separate concerns (models, execution, integrations)
- Existing tmux and worktree utilities are well-implemented (`TmuxManager`, `GitWorktreeManager`)
- Strong foundation with `ActionDefintion`, `ActionStep` models
- Database integration for execution tracking
- Artifact management system

### Issues Identified
1. **Monolithic Executor** (500+ lines) - handles orchestration, validation, built-in steps
2. **Missing Session Abstraction** - no unified model for session data/history
3. **Context Coupling** - untyped dictionary passed everywhere
4. **Manual vs Programmatic Separation** - CLI session commands vs automatic session management

## Implementation Roadmap

### Phase 1: Foundation Features (1-2 days)

#### 1.1 Add prompt_file Property
**File**: `src/prunejuice/core/models.py` (line 81)
```python
class ActionDefintion(BaseModel):
    name: str
    description: str
    prompt_file: Optional[str] = None  # NEW: location of prompt text/markdown file
    extends: Optional[str] = None
    category: str = "workflow"
    arguments: List[CommandArgument] = Field(default_factory=list)
    environment: Dict[str, str] = Field(default_factory=dict)
    pre_steps: List[Union[str, ActionStep]] = Field(default_factory=list)
    steps: List[Union[str, ActionStep]] = Field(default_factory=list)
    post_steps: List[Union[str, ActionStep]] = Field(default_factory=list)
    cleanup_on_failure: List[Union[str, ActionStep]] = Field(default_factory=list)
    working_directory: Optional[str] = None
    timeout: int = 1800
```

#### 1.2 Create Session Model
**New File**: `src/prunejuice/core/session.py`
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
from enum import Enum

from .models import StepStatus

class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"

class StepExecution(BaseModel):
    name: str
    status: StepStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    output: Optional[str] = None
    error: Optional[str] = None

class Session(BaseModel):
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
        """Get execution context for steps - replaces manual context building"""
        return {
            'session_id': self.id,
            'command_name': self.command_name,
            'project_path': self.project_path,
            'worktree_path': self.worktree_path,
            'tmux_session': self.tmux_session_name,
            'artifact_dir': self.artifact_dir,
            'shared_data': self.shared_data,
            'step_history': self.step_history
        }
    
    def add_step_result(self, step_name: str, success: bool, output: str, error: Optional[str] = None):
        """Record step execution result"""
        step_execution = StepExecution(
            name=step_name,
            status=StepStatus.COMPLETED if success else StepStatus.FAILED,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            output=output,
            error=error
        )
        self.step_history.append(step_execution)
    
    def set_shared_data(self, key: str, value: Any):
        """Store shared data for steps to access"""
        self.shared_data[key] = value
    
    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """Retrieve shared data"""
        return self.shared_data.get(key, default)
    
    async def create_tmux_session(self, pots_integration) -> str:
        """Create tmux session and store session name"""
        session_name = await pots_integration.create_session(
            self.worktree_path or self.project_path,
            self.command_name
        )
        self.tmux_session_name = session_name
        return session_name
    
    async def create_worktree(self, plum_integration, branch_name: str) -> Path:
        """Create worktree and store worktree path"""
        worktree_path = await plum_integration.create_worktree(
            self.project_path,
            branch_name
        )
        self.worktree_path = worktree_path
        return worktree_path
```

### Phase 2: Base Command Architecture (2-3 days)

#### 2.1 Extract Built-in Steps
**New File**: `src/prunejuice/core/builtin_steps.py`
```python
"""Built-in step implementations extracted from Executor class."""

import asyncio
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import json
import logging

from .session import Session

logger = logging.getLogger(__name__)

class BuiltinSteps:
    """Built-in step implementations - extracted from Executor class (lines 390-496)"""
    
    def __init__(self, db, artifacts, plum, pots):
        self.db = db
        self.artifacts = artifacts
        self.plum = plum
        self.pots = pots
    
    async def setup_environment(self, session: Session) -> str:
        """Setup execution environment."""
        artifact_dir = session.artifact_dir
        artifact_dir.mkdir(parents=True, exist_ok=True)
        (artifact_dir / "logs").mkdir(exist_ok=True)
        (artifact_dir / "outputs").mkdir(exist_ok=True)
        return "Environment setup complete"
    
    async def validate_prerequisites(self, session: Session) -> str:
        """Validate prerequisites for command execution."""
        issues = []
        
        # Check if we're in a git repository
        project_path = session.project_path
        if not (project_path / ".git").exists():
            issues.append("Not in a git repository")
        
        # Check for required tools
        if session.command_name.startswith('worktree-') and not self.plum.is_available():
            issues.append("Plum worktree manager not available")
        
        if issues:
            raise RuntimeError(f"Prerequisites not met: {', '.join(issues)}")
        
        return "Prerequisites validated"
    
    async def create_worktree(self, session: Session) -> str:
        """Create worktree via plum integration."""
        branch_name = session.get_shared_data(
            'branch_name',
            f"pj-{session.command_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        
        worktree_path = await session.create_worktree(self.plum, branch_name)
        session.set_shared_data('branch_name', branch_name)
        
        return f"Created worktree at {worktree_path}"
    
    async def start_session(self, session: Session) -> str:
        """Start tmux session via pots integration."""
        session_name = await session.create_tmux_session(self.pots)
        return f"Started tmux session: {session_name}"
    
    async def gather_context(self, session: Session) -> str:
        """Gather context information for the command."""
        project_path = session.project_path
        
        context_info = {
            "project_name": project_path.name,
            "git_branch": "unknown",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Try to get git branch
        try:
            import subprocess
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            context_info["git_branch"] = result.stdout.strip()
        except subprocess.CalledProcessError:
            pass
        
        # Store context as artifact
        self.artifacts.store_content(
            session.artifact_dir,
            json.dumps(context_info, indent=2),
            "context.json",
            "specs"
        )
        
        session.set_shared_data('context_info', context_info)
        return f"Context gathered for {context_info['project_name']}"
    
    async def store_artifacts(self, session: Session) -> str:
        """Store artifacts for the session."""
        # Mark artifacts in database
        try:
            await self.db.store_artifact(
                session.get_shared_data('event_id'),
                "session",
                str(session.artifact_dir),
                0
            )
        except Exception as e:
            logger.warning(f"Failed to store artifact info: {e}")
        
        return f"Artifacts stored in {session.artifact_dir}"
    
    async def cleanup(self, session: Session) -> str:
        """Cleanup session resources."""
        # This would be implemented based on state manager requirements
        return "Cleanup completed"
```

#### 2.2 Implement Base Command Hierarchy
**New File**: `src/prunejuice/core/commands.py`
```python
"""Base Command hierarchy for automatic lifecycle management."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any
import logging

from .models import ActionDefintion, ExecutionResult
from .session import Session, SessionStatus

logger = logging.getLogger(__name__)

class BaseCommand(ABC):
    """Base interface for all commands"""
    
    def __init__(self, definition: ActionDefintion, session: Session, step_executor, builtin_steps):
        self.definition = definition
        self.session = session
        self.step_executor = step_executor
        self.builtin_steps = builtin_steps
    
    @abstractmethod
    async def execute(self) -> ExecutionResult:
        """Execute the command"""
        pass
    
    async def _run_steps(self) -> ExecutionResult:
        """Common step execution logic"""
        try:
            all_steps = self.definition.get_all_steps()
            
            for i, step in enumerate(all_steps):
                logger.info(f"Executing step {i+1}/{len(all_steps)}: {step.name}")
                
                success, output = await self.step_executor.execute(
                    step, self.session.get_context(), self.definition.timeout
                )
                
                # Store step output as artifact
                if output:
                    self.builtin_steps.artifacts.store_content(
                        self.session.artifact_dir, 
                        output, 
                        f"step-{i+1}-{step.name}.log", 
                        "logs"
                    )
                
                # Record step result in session
                self.session.add_step_result(step.name, success, output)
                
                if not success:
                    self.session.status = SessionStatus.FAILED
                    raise RuntimeError(f"Step '{step.name}' failed: {output}")
            
            self.session.status = SessionStatus.COMPLETED
            return ExecutionResult(
                success=True,
                artifacts_path=str(self.session.artifact_dir)
            )
            
        except Exception as e:
            self.session.status = SessionStatus.FAILED
            
            # Run cleanup steps
            for step in self.definition.cleanup_on_failure:
                try:
                    await self.step_executor.execute(step, self.session.get_context(), 60)
                except Exception:
                    logger.error(f"Cleanup step '{step}' failed")
            
            return ExecutionResult(
                success=False,
                error=str(e),
                artifacts_path=str(self.session.artifact_dir)
            )

class StandardCommand(BaseCommand):
    """Standard command execution without automatic session/worktree management"""
    
    async def execute(self) -> ExecutionResult:
        """Execute steps directly"""
        return await self._run_steps()

class SessionCommand(BaseCommand):
    """Command that automatically manages tmux session lifecycle"""
    
    async def execute(self) -> ExecutionResult:
        """Execute with automatic session lifecycle management"""
        try:
            # Create detached tmux session automatically
            await self._create_session()
            
            # Run steps inside the session
            return await self._run_steps()
            
        finally:
            # Always cleanup session
            await self._cleanup_session()
    
    async def _create_session(self):
        """Create detached tmux session"""
        logger.info(f"Creating tmux session for command: {self.definition.name}")
        await self.builtin_steps.start_session(self.session)
    
    async def _cleanup_session(self):
        """Cleanup tmux session"""
        if self.session.tmux_session_name:
            logger.info(f"Cleaning up tmux session: {self.session.tmux_session_name}")
            # Implementation would use pots integration to kill session

class WorktreeCommand(SessionCommand):
    """Command that automatically manages worktree + session lifecycle"""
    
    async def execute(self) -> ExecutionResult:
        """Execute with automatic worktree and session lifecycle management"""
        try:
            # Create worktree automatically
            await self._create_worktree()
            
            # Create detached tmux session in the worktree
            await self._create_session()
            
            # Run steps inside the session
            return await self._run_steps()
            
        finally:
            # Always cleanup in reverse order
            await self._cleanup_session()
            await self._cleanup_worktree()
    
    async def _create_worktree(self):
        """Create git worktree automatically"""
        logger.info(f"Creating worktree for command: {self.definition.name}")
        await self.builtin_steps.create_worktree(self.session)
    
    async def _cleanup_worktree(self):
        """Cleanup git worktree"""
        if self.session.worktree_path:
            logger.info(f"Cleaning up worktree: {self.session.worktree_path}")
            # Implementation would use plum integration to remove worktree

def create_command(definition: ActionDefintion, session: Session, step_executor, builtin_steps) -> BaseCommand:
    """Factory function to create appropriate command type based on definition"""
    
    # Determine command type based on steps or metadata
    needs_worktree = any(
        step_name in ['create-worktree'] 
        for step in definition.get_all_steps() 
        for step_name in [step.action, step.name]
    )
    
    needs_session = any(
        step_name in ['start-session', 'session-create'] 
        for step in definition.get_all_steps() 
        for step_name in [step.action, step.name]
    )
    
    if needs_worktree:
        return WorktreeCommand(definition, session, step_executor, builtin_steps)
    elif needs_session:
        return SessionCommand(definition, session, step_executor, builtin_steps)
    else:
        return StandardCommand(definition, session, step_executor, builtin_steps)
```

### Phase 3: Integration & Testing (1-2 days)

#### 3.1 Update Executor
**Modifications to**: `src/prunejuice/core/executor.py`

- Remove built-in step methods (lines 390-496) 
- Simplify from 500+ lines to ~200 lines
- Use Session object instead of context dict
- Integrate with Base Command hierarchy
- Update `execute_command` method to use new Session and Command classes

#### 3.2 Comprehensive Testing

**New Test Files:**
```
tests/test_session_model.py      # Session lifecycle, shared data
tests/test_base_commands.py      # Command hierarchy
tests/test_prompt_file.py        # Prompt file loading
tests/test_builtin_steps.py      # Extracted built-in steps
tests/test_integration.py        # End-to-end workflows
```

## Implementation Priority

### High Impact, Low Effort (Day 1)
1. **Add prompt_file property** (2 hours)
   - Simple model field addition
   - Update command loader to handle prompt files

2. **Extract built-in steps** (3 hours)
   - Move methods from Executor to BuiltinSteps
   - Update method signatures to use Session

### High Impact, Medium Effort (Days 2-3)
3. **Create Session model** (6 hours)
   - Implement Session class with all methods
   - Update step execution to use Session context

4. **Implement Base Command hierarchy** (8 hours)
   - Create BaseCommand, SessionCommand, WorktreeCommand
   - Implement automatic lifecycle management
   - Add command factory function

### Medium Impact, High Effort (Days 4-5)
5. **Refactor Executor** (12 hours)
   - Integrate with new Session and Command classes
   - Simplify and reduce complexity
   - Maintain backward compatibility

6. **Comprehensive testing** (8 hours)
   - Unit tests for all new components
   - Integration tests for lifecycle management
   - Regression tests for existing functionality

## Testing Strategy

### Backward Compatibility Tests
- All existing YAML commands must continue working
- Existing CLI session/worktree commands unchanged
- No breaking changes to public API

### New Feature Tests
- Session data sharing between steps
- Automatic worktree/session lifecycle
- Prompt file loading and usage
- Step history tracking

### Integration Tests
- WorktreeCommand with real git operations
- SessionCommand with tmux integration
- Error handling and cleanup scenarios

## Risk Assessment

### Low Risk (Additive changes)
- prompt_file property addition
- Session model creation
- BuiltinSteps extraction

### Medium Risk (New functionality)
- Base Command hierarchy implementation
- Session lifecycle management

### High Risk (Major refactoring)
- Executor decomposition (can be done incrementally)
- Context dict replacement with Session

## Success Criteria

1. ✅ Commands can specify prompt_file location in YAML
2. ✅ Session model tracks shared data and step history
3. ✅ WorktreeCommand automatically creates worktree + tmux session
4. ✅ SessionCommand automatically manages tmux session lifecycle
5. ✅ All existing commands continue to work unchanged
6. ✅ Code complexity reduced (Executor: 500+ → ~200 lines)
7. ✅ Comprehensive test coverage for new features

**Total Estimated Implementation Time**: 5-7 days with comprehensive testing

This plan provides a clean, incremental approach with full backward compatibility and systematic testing coverage.