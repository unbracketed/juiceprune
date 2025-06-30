# Git Worktree Integration

Prunejuice provides native Python-based Git worktree management that enables parallel development workflows across multiple working directories. This replaces traditional shell-based approaches with a robust, type-safe implementation built on GitPython.

## Overview

Git worktrees allow you to check out multiple branches of the same repository simultaneously, each in its own working directory. Prunejuice automates worktree creation, management, and cleanup as part of command execution workflows.

## Core Features

### Native Python Implementation

- **Pure Python**: Built with GitPython and asyncio, no shell script dependencies
- **Type Safety**: Full type hints throughout the worktree management system
- **Better Error Handling**: Structured error handling with detailed logging
- **Cross-Platform**: Works on macOS, Linux, and Windows

### Automatic Worktree Management

- **On-Demand Creation**: Worktrees are created automatically when commands specify worktree requirements
- **Smart Naming**: Follows consistent naming patterns: `{project}-{branch}`
- **Directory Organization**: Organized in a dedicated worktrees directory structure
- **Lifecycle Management**: Automatic cleanup when workflows complete

## Worktree Configuration

### Environment Variable Configuration

Configure worktree base directory using environment variables:

```bash
# Set worktree base directory (relative to project root)
export PRUNEJUICE_BASE_DIR=".worktrees"

# Or set absolute path
export PRUNEJUICE_BASE_DIR="/workspace/worktrees"
```

### Project-Level Configuration

Use a `.env` file in your project root for project-specific settings:

```bash
# .env file in project root
PRUNEJUICE_BASE_DIR=.worktrees
PRUNEJUICE_GITHUB_USERNAME=your-username
PRUNEJUICE_EDITOR=code
```

### Global Configuration

Set system-wide defaults using environment variables:

```bash
# In your shell profile (.bashrc, .zshrc, etc.)
export PRUNEJUICE_BASE_DIR="$HOME/worktrees"
export PRUNEJUICE_EDITOR="code"
export PRUNEJUICE_DEFAULT_TIMEOUT=3600
```

For a complete list of configuration options, see the [Configuration Reference](../reference/config.md).

## Directory Structure

Prunejuice organizes worktrees in a predictable structure. The base directory can be configured via `PRUNEJUICE_BASE_DIR`:

**Default Structure (../worktrees):**
```
project-root/
├── .git/
├── main-code/
└── ../worktrees/
    ├── project-feature-auth/
    ├── project-hotfix-bug123/
    └── project-experiment-perf/
```

**Custom Structure (.worktrees in project):**
```bash
# With PRUNEJUICE_BASE_DIR=.worktrees
export PRUNEJUICE_BASE_DIR=.worktrees
```
```
project-root/
├── .git/
├── main-code/
└── .worktrees/
    ├── project-feature-auth/
    ├── project-hotfix-bug123/
    └── project-experiment-perf/
```

### Naming Conventions

- **Pattern**: `{project-name}-{branch-name}`
- **Sanitization**: Special characters replaced with hyphens
- **Length Limits**: Truncated if too long while preserving readability
- **Uniqueness**: Conflicts automatically resolved with suffixes

## Technical Implementation

### GitWorktreeManager Class

The core worktree management is handled by the `GitWorktreeManager` class:

```python
from prunejuice.worktree_utils import GitWorktreeManager
from prunejuice.core.config import Settings
from pathlib import Path

# Initialize with settings
settings = Settings()
manager = GitWorktreeManager(project_path)

# Create a new worktree using configured base directory
worktree_path = manager.create_worktree(
    branch_name="feature-auth",
    base_branch="main",
    parent_dir=settings.base_dir  # Uses PRUNEJUICE_BASE_DIR
)

# Or specify custom directory
worktree_path = manager.create_worktree(
    branch_name="feature-auth",
    base_branch="main",
    parent_dir=Path(".worktrees")  # Custom directory
)

# List all worktrees
worktrees = manager.list_worktrees()

# Remove a worktree
manager.remove_worktree(worktree_path, force=False)
```

### Key Methods

- **`create_worktree()`**: Creates new worktree with branch
- **`list_worktrees()`**: Returns all worktrees with metadata
- **`remove_worktree()`**: Safely removes worktree and branch
- **`get_worktree_info()`**: Gets detailed worktree information
- **`is_git_repository()`**: Validates Git repository status

### Error Handling

```python
try:
    worktree_path = manager.create_worktree("new-feature", "main")
except RuntimeError as e:
    # Handle worktree creation failures
    logger.error(f"Failed to create worktree: {e}")
except ValueError as e:
    # Handle invalid branch names or missing base branches
    logger.error(f"Invalid worktree configuration: {e}")
```

## Integration with Commands

### Automatic Creation

When a command specifies worktree requirements, Prunejuice:

1. **Validates** base branch exists
2. **Creates** new branch from base
3. **Sets up** worktree directory
4. **Configures** working directory for command execution
5. **Tracks** worktree in project state

### Template Variables

Worktree configurations support template variables:

```yaml
worktree:
  branch: "{{task_type}}-{{issue_number}}"
  base_branch: "{{base_branch | default('main')}}"
```

Available variables:
- `{{project}}`: Project name
- `{{task_id}}`: Task identifier
- `{{timestamp}}`: Current timestamp
- `{{user}}`: Current user
- Command arguments as variables

## Workflow Examples

### Feature Development

```bash
# Command with worktree creation
prj run start-feature task_id=user-auth

# Creates:
# - Branch: feature-user-auth
# - Worktree: ../worktrees/myproject-feature-user-auth/
# - Session: myproject-feature-user-auth-dev
```

### Hotfix Workflow

```bash
# Emergency hotfix
prj run hotfix issue=critical-bug base_branch=production

# Creates:
# - Branch: hotfix-critical-bug
# - Worktree: ../worktrees/myproject-hotfix-critical-bug/
# - Based on production branch
```

### Code Review

```bash
# Review PR in isolated environment
prj run review-pr pr_number=456

# Creates:
# - Branch: review-pr-456
# - Worktree: ../worktrees/myproject-review-pr-456/
# - Checks out PR branch for review
```

## Best Practices

### Branch Naming

- Use descriptive, hierarchical names: `feature/user-auth`, `hotfix/memory-leak`
- Include issue numbers: `feature/gh-123-user-auth`
- Use consistent prefixes: `feature/`, `hotfix/`, `experiment/`

### Directory Management

- Keep worktrees in dedicated parent directory
- Use consistent naming patterns
- Enable auto-cleanup for temporary worktrees
- Regular cleanup of stale worktrees

### Performance Optimization

- **Shared Objects**: Worktrees share Git objects, saving disk space
- **Sparse Checkout**: Use sparse-checkout for large repositories
- **Cleanup Strategy**: Remove worktrees promptly after use

## Troubleshooting

### Common Issues

**Worktree Creation Fails**
```bash
# Check if base branch exists
git branch -a | grep main

# Verify repository state
prj status

# Check available disk space
df -h
```

**Branch Already Exists**
```bash
# List existing branches
git branch -a

# Force cleanup if needed
prj run cleanup-worktree branch=feature-name --force
```

**Permission Issues**
```bash
# Check directory permissions
ls -la ../worktrees/

# Fix permissions if needed
chmod -R 755 ../worktrees/
```

### Debugging

Enable debug logging for detailed worktree operations:

```bash
# Enable debug mode
export PRJ_LOG_LEVEL=DEBUG
prj run your-command

# Check logs
tail -f ~/.local/share/prunejuice/logs/debug.log
```

### Recovery

Recover from corrupted worktree state:

```bash
# List all worktrees
git worktree list

# Remove corrupted worktree
git worktree remove --force path/to/worktree

# Prune dangling references
git worktree prune
```

## Advanced Usage

### Custom Worktree Locations

You can override the base directory on a per-command basis or use different locations for different purposes:

```bash
# Temporary experiments
export PRUNEJUICE_BASE_DIR="/tmp/experiments"
prj worktree create experiment-feature

# Project-specific worktrees
export PRUNEJUICE_BASE_DIR=".worktrees"
prj worktree create feature-auth

# System-wide worktrees
export PRUNEJUICE_BASE_DIR="$HOME/worktrees"
prj worktree create shared-feature
```

### Dynamic Configuration

Use different base directories for different project types:

```bash
# In your shell profile
if [[ $(pwd) == *"/experiments/"* ]]; then
    export PRUNEJUICE_BASE_DIR="/tmp/worktrees"
elif [[ $(pwd) == *"/client-projects/"* ]]; then
    export PRUNEJUICE_BASE_DIR=".worktrees"
else
    export PRUNEJUICE_BASE_DIR="$HOME/worktrees"
fi
```

## Migration from Shell Scripts

If migrating from shell-based worktree management:

1. **Audit existing scripts** for worktree operations
2. **Map shell commands** to Prunejuice configurations
3. **Test workflows** in isolated environment
4. **Update CI/CD** to use Prunejuice commands
5. **Train team** on new workflow patterns

### Common Migration Patterns

```bash
# Old shell script
git worktree add ../feature-branch feature-branch
cd ../feature-branch

# New Prunejuice command
prj run start-feature branch=feature-branch
```

## Security Considerations

- **Path Validation**: All paths are validated and sanitized
- **Branch Verification**: Base branches are verified before creation
- **Permission Checks**: Directory permissions are validated
- **Cleanup Tracking**: All created worktrees are tracked for cleanup

## Performance Monitoring

Monitor worktree performance through built-in metrics:

```bash
# View worktree statistics
prj status --detailed

# Check recent worktree operations
prj history --filter=worktree

# Analyze disk usage
prj analyze-disk-usage
```

The native Python worktree implementation provides a robust foundation for parallel development workflows, enabling teams to work efficiently across multiple branches while maintaining consistency and reliability.