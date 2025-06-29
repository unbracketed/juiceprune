# Shared Project Database Refactor

## Problem Statement

Currently, each worktree in a PruneJuice project creates its own `.prj/prunejuice.db` database file, causing event history to be isolated per worktree. This prevents users from seeing the full history of events across all worktrees within a project.

**Example of Current Problematic Behavior:**
```bash
# Main project shows no history
brian /tmp/ghgh [main] $ prj history
No history found matching criteria.

# Worktree has its own isolated history
brian /tmp/ghgh-uuu [ghgh-uuu] $ prj history
┏━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ ID   ┃ Command    ┃ Status    ┃ Start Time  ┃ Duration ┃ Project  ┃
┡━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ 1    │ echo-hello │ completed │ 06/29 14:24 │ 0.0s     │ ghgh-uuu │
└──────┴────────────┴───────────┴─────────────┴──────────┴──────────┘
```

## Root Cause Analysis

The issue stems from the `Settings` class in `src/prunejuice/core/config.py` using `Path.cwd()` for database path resolution:

```python
# config.py:13-16 - PROBLEMATIC CODE
db_path: Path = Field(
    default_factory=lambda: Path.cwd() / ".prj" / "prunejuice.db",
    description="Path to SQLite database"
)
```

This creates worktree-specific databases because each worktree has its own working directory.

## Critical Issues Identified

### High Priority
1. **Database Path Resolution** (`config.py:14`)
   - Uses `Path.cwd()` causing separate databases per worktree
   - Should use main Git repository root instead

2. **Scattered Settings Instantiation** (6 locations in `cli.py`)
   - Lines: 122, 184, 262, 304, 418, 447
   - No centralized path context management
   - Each creates Settings without project awareness

### Medium Priority
3. **Inconsistent Git Detection**
   - `builtin_steps.py:38` uses `(project_path / ".git").exists()`
   - Should use `GitWorktreeManager` consistently

4. **Direct Git Subprocess Calls**
   - `builtin_steps.py:78-89` uses subprocess instead of GitWorktreeManager
   - Inconsistent with existing Git abstraction layer

### Low Priority
5. **Missing Fallback Mechanism**
   - No graceful handling for non-Git projects
   - Could break existing workflows

## Solution Architecture

The refactoring uses a three-tier approach:

1. **ProjectPathResolver** - Centralized Git-aware path resolution
2. **Enhanced Settings** - Project-aware configuration with fallbacks  
3. **Updated Instantiation** - Consistent Settings creation across codebase

## Implementation Plan

### Step 1: Create ProjectPathResolver Utility

**File:** `src/prunejuice/utils/path_resolver.py`

```python
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
```

### Step 2: Refactor Settings Class

**File:** `src/prunejuice/core/config.py`

**Current problematic code (lines 13-16, 19-22):**
```python
# BEFORE - PROBLEMATIC
db_path: Path = Field(
    default_factory=lambda: Path.cwd() / ".prj" / "prunejuice.db",
    description="Path to SQLite database"
)

artifacts_dir: Path = Field(
    default_factory=lambda: Path.cwd() / ".prj" / "artifacts", 
    description="Directory for storing artifacts"
)
```

**Refactored implementation:**
```python
# AFTER - FIXED
from typing import Optional
from ..utils.path_resolver import ProjectPathResolver

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database settings
    db_path: Path = Field(
        default_factory=lambda: ProjectPathResolver.resolve_database_path(),
        description="Path to SQLite database"
    )
    
    # Artifact storage  
    artifacts_dir: Path = Field(
        default_factory=lambda: ProjectPathResolver.resolve_artifacts_path(),
        description="Directory for storing artifacts"
    )
    
    # ... rest of fields unchanged ...
    
    def __init__(self, project_path: Optional[Path] = None, **kwargs):
        """Initialize settings with optional project path override.
        
        Args:
            project_path: Override project root path (for testing/special cases)
            **kwargs: Additional settings overrides
        """
        # Override paths if project_path is provided
        if project_path is not None:
            kwargs.setdefault('db_path', project_path / ".prj" / "prunejuice.db")
            kwargs.setdefault('artifacts_dir', project_path / ".prj" / "artifacts")
            
        super().__init__(**kwargs)
        
        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
```

### Step 3: Update Settings Instantiation Points

**File:** `src/prunejuice/cli.py`

Update all Settings instantiations to be project-aware:

```python
# Lines to update: 122, 184, 262, 304, 418, 447

# BEFORE
settings = Settings()

# AFTER  
settings = Settings()  # Now automatically Git-aware via ProjectPathResolver
```

**File:** `src/prunejuice/core/executor.py`

```python
# Line 217 - Already correct, but ensure consistency
self.db = Database(settings.db_path)  # This will now use main repo path
```

### Step 4: Enhance Git Operations Consistency

**File:** `src/prunejuice/core/builtin_steps.py`

Replace inconsistent Git detection:

```python
# BEFORE (line 38)
if project_path and not (project_path / ".git").exists():

# AFTER  
from ..worktree_utils import GitWorktreeManager
try:
    manager = GitWorktreeManager(project_path)
    if not manager.is_git_repository():
        issues.append("Not in a git repository")
except Exception:
    issues.append("Not in a git repository")
```

Replace direct subprocess calls (lines 78-89):

```python
# BEFORE
result = subprocess.run(
    ["git", "branch", "--show-current"],
    cwd=project_path,
    capture_output=True,
    text=True,
    check=True
)

# AFTER
try:
    manager = GitWorktreeManager(project_path)
    context_info["git_branch"] = manager.get_current_branch() or "unknown"
except Exception:
    context_info["git_branch"] = "unknown"
```

### Step 5: Update Module Imports

**File:** `src/prunejuice/utils/__init__.py`

```python
from .path_resolver import ProjectPathResolver

__all__ = ["ProjectPathResolver"]
```

## Expected Behavior After Refactoring

After implementation, all worktrees will share the main project's database:

```bash
# Both main project and worktrees show same history
brian /tmp/ghgh [main] $ prj history
┏━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ ID   ┃ Command    ┃ Status    ┃ Start Time  ┃ Duration ┃ Project  ┃
┡━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ 1    │ echo-hello │ completed │ 06/29 14:24 │ 0.0s     │ ghgh     │
└──────┴────────────┴───────────┴─────────────┴──────────┴──────────┘

brian /tmp/ghgh-uuu [ghgh-uuu] $ prj history  
┏━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ ID   ┃ Command    ┃ Status    ┃ Start Time  ┃ Duration ┃ Project  ┃
┡━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ 1    │ echo-hello │ completed │ 06/29 14:24 │ 0.0s     │ ghgh     │
└──────┴────────────┴───────────┴─────────────┴──────────┴──────────┘
```

## Testing Strategy

1. **Unit Tests**: Test ProjectPathResolver with various Git repository structures
2. **Integration Tests**: Verify Settings instantiation works in both Git and non-Git projects  
3. **Regression Tests**: Ensure existing functionality remains intact
4. **Worktree Tests**: Verify shared database behavior across multiple worktrees

## Backward Compatibility

- Non-Git projects continue to work (fallback to current directory)
- Existing Settings API remains unchanged (constructor signature enhanced but optional)
- All environment variable overrides still function
- Database schema and structure unchanged

## Migration Notes

- **Automatic**: Most users will see immediate improvement without action
- **Manual Migration**: Users with existing worktree databases can manually copy events between databases if desired
- **No Breaking Changes**: All existing commands and workflows continue to function

## Implementation Checklist

- [ ] Create `src/prunejuice/utils/path_resolver.py`
- [ ] Refactor `Settings` class in `src/prunejuice/core/config.py`
- [ ] Update Settings instantiations in `src/prunejuice/cli.py`
- [ ] Enhance Git operations in `src/prunejuice/core/builtin_steps.py`
- [ ] Update module imports in `src/prunejuice/utils/__init__.py`
- [ ] Add unit tests for ProjectPathResolver
- [ ] Add integration tests for Settings with Git repositories
- [ ] Test worktree database sharing behavior
- [ ] Update documentation if needed

## Files Modified

| File | Change Type | Lines Modified | Description |
|------|-------------|----------------|-------------|
| `src/prunejuice/utils/path_resolver.py` | **New** | N/A | ProjectPathResolver utility |
| `src/prunejuice/core/config.py` | **Major** | 13-16, 19-22, 69-73 | Git-aware Settings class |
| `src/prunejuice/cli.py` | **Minor** | 122, 184, 262, 304, 418, 447 | Settings instantiation |
| `src/prunejuice/core/builtin_steps.py` | **Minor** | 38, 78-89 | Consistent Git operations |
| `src/prunejuice/utils/__init__.py` | **Minor** | N/A | Module imports |

---

**Implementation Priority:** High  
**Estimated Effort:** 4-6 hours  
**Risk Level:** Low (backward compatible)  
**Testing Required:** Medium (Git repository variations)