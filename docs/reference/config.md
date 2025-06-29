# Configuration Options

This document provides a comprehensive reference for all PruneJuice configuration options, including global settings, project-specific configuration, and environment variables.

## Overview

PruneJuice uses a hierarchical configuration system with multiple levels of precedence:

1. **Environment Variables** (highest precedence)
2. **Project Configuration Files** (`.env` files)
3. **Default Values** (lowest precedence)

## Configuration Structure

PruneJuice configuration is managed through the `Settings` class in `src/prunejuice/core/config.py`, which uses Pydantic Settings for validation and environment variable support.

## Configuration Options

### Database Settings

#### `db_path`
- **Type**: Path
- **Default**: `{current_directory}/.prj/prunejuice.db`
- **Environment Variable**: `PRUNEJUICE_DB_PATH`
- **Description**: Path to the SQLite database file that stores execution history and metadata

**Example**:
```bash
# Environment variable
export PRUNEJUICE_DB_PATH="/custom/path/to/prunejuice.db"
```

```yaml
# .env file
PRUNEJUICE_DB_PATH=/custom/path/to/prunejuice.db
```

### Artifact Storage

#### `artifacts_dir`
- **Type**: Path
- **Default**: `{current_directory}/.prj/artifacts`
- **Environment Variable**: `PRUNEJUICE_ARTIFACTS_DIR`
- **Description**: Directory for storing command execution artifacts, logs, and outputs

**Example**:
```bash
# Environment variable
export PRUNEJUICE_ARTIFACTS_DIR="/var/lib/prunejuice/artifacts"
```

```yaml
# .env file
PRUNEJUICE_ARTIFACTS_DIR=/var/lib/prunejuice/artifacts
```

### Integration Settings

#### `plum_path`
- **Type**: Optional[Path]
- **Default**: `None` (auto-discovery)
- **Environment Variable**: `PRUNEJUICE_PLUM_PATH`
- **Description**: Path to the plum executable for worktree management

**Example**:
```bash
# Environment variable
export PRUNEJUICE_PLUM_PATH="/usr/local/bin/plum"
```

#### `pots_path`
- **Type**: Optional[Path]
- **Default**: `None` (auto-discovery)
- **Environment Variable**: `PRUNEJUICE_POTS_PATH`
- **Description**: Path to the pots executable for tmux session management

**Example**:
```bash
# Environment variable
export PRUNEJUICE_POTS_PATH="/usr/local/bin/pots"
```

### Execution Settings

#### `default_timeout`
- **Type**: int
- **Default**: `1800` (30 minutes)
- **Environment Variable**: `PRUNEJUICE_DEFAULT_TIMEOUT`
- **Description**: Default command timeout in seconds

**Example**:
```bash
# Environment variable
export PRUNEJUICE_DEFAULT_TIMEOUT=3600  # 1 hour
```

#### `max_parallel_steps`
- **Type**: int
- **Default**: `1`
- **Environment Variable**: `PRUNEJUICE_MAX_PARALLEL_STEPS`
- **Description**: Maximum number of parallel steps (currently only 1 is supported)

**Note**: Parallel execution is not yet implemented. This setting is reserved for future use.

### Environment Settings

#### `github_username`
- **Type**: Optional[str]
- **Default**: `None`
- **Environment Variable**: `PRUNEJUICE_GITHUB_USERNAME`
- **Description**: GitHub username for pull request operations and integration features

**Example**:
```bash
# Environment variable
export PRUNEJUICE_GITHUB_USERNAME="your-github-username"
```

#### `editor`
- **Type**: str
- **Default**: `"code"`
- **Environment Variable**: `PRUNEJUICE_EDITOR`
- **Description**: Default editor command for opening files

**Example**:
```bash
# Environment variable
export PRUNEJUICE_EDITOR="vim"
# or
export PRUNEJUICE_EDITOR="subl"
```

#### `base_dir`
- **Type**: Optional[Path]
- **Default**: `None`
- **Environment Variable**: `PRUNEJUICE_BASE_DIR`
- **Description**: Base directory for worktree creation and management

**Example**:
```bash
# Environment variable
export PRUNEJUICE_BASE_DIR="/workspace/projects"
```

## Configuration Files

### Global Configuration

PruneJuice looks for configuration in the following locations:

1. **Environment variables** with the `PRUNEJUICE_` prefix
2. **`.env` file** in the current working directory
3. **Built-in defaults**

### Project Configuration

Each project can have its own `.env` file in the project root that overrides global settings for that specific project.

### Configuration File Format

Configuration files use the standard `.env` format:

```bash
# Database configuration
PRUNEJUICE_DB_PATH=/custom/path/to/prunejuice.db
PRUNEJUICE_ARTIFACTS_DIR=/custom/artifacts/path

# Integration paths
PRUNEJUICE_PLUM_PATH=/usr/local/bin/plum
PRUNEJUICE_POTS_PATH=/usr/local/bin/pots

# Execution settings
PRUNEJUICE_DEFAULT_TIMEOUT=3600
PRUNEJUICE_MAX_PARALLEL_STEPS=1

# Environment settings
PRUNEJUICE_GITHUB_USERNAME=your-username
PRUNEJUICE_EDITOR=code
PRUNEJUICE_BASE_DIR=/workspace
```

## Configuration Inheritance and Precedence

Configuration values are resolved in the following order (highest to lowest precedence):

1. **Environment Variables**: Direct environment variables take highest precedence
2. **Project .env File**: Project-specific `.env` file in the current directory
3. **Default Values**: Built-in default values defined in the Settings class

### Example Configuration Scenarios

#### Development Environment
```bash
# .env file for development
PRUNEJUICE_DEFAULT_TIMEOUT=600
PRUNEJUICE_EDITOR=code
PRUNEJUICE_GITHUB_USERNAME=dev-user
PRUNEJUICE_ARTIFACTS_DIR=./dev-artifacts
```

#### Production Environment
```bash
# .env file for production
PRUNEJUICE_DEFAULT_TIMEOUT=7200
PRUNEJUICE_ARTIFACTS_DIR=/var/lib/prunejuice/artifacts
PRUNEJUICE_DB_PATH=/var/lib/prunejuice/prunejuice.db
PRUNEJUICE_MAX_PARALLEL_STEPS=1
```

#### CI/CD Environment
```bash
# CI/CD environment variables
export PRUNEJUICE_DEFAULT_TIMEOUT=3600
export PRUNEJUICE_ARTIFACTS_DIR=/tmp/prunejuice-artifacts
export PRUNEJUICE_GITHUB_USERNAME=ci-bot
export PRUNEJUICE_EDITOR=nano
```

## Directory Structure Configuration

PruneJuice automatically creates the following directory structure based on configuration:

```
{project_root}/
├── .prj/
│   ├── prunejuice.db          # Database file (db_path)
│   ├── artifacts/             # Artifacts directory (artifacts_dir)
│   │   ├── session-{id}/      # Session-specific artifacts
│   │   │   ├── logs/          # Execution logs
│   │   │   ├── outputs/       # Command outputs
│   │   │   └── specs/         # Specifications and context
│   │   └── ...
│   ├── commands/              # Project-specific commands
│   ├── steps/                 # Project-specific steps
│   └── configs/               # Project-specific configurations
```

## Validation Rules

The configuration system enforces the following validation rules:

- **Path fields**: Must be valid filesystem paths
- **Timeout values**: Must be positive integers
- **Optional fields**: Can be `None` or empty
- **Environment prefix**: All environment variables must use the `PRUNEJUICE_` prefix

## Troubleshooting Configuration

### Common Issues

1. **Permission Errors**: Ensure the user has write permissions to the configured paths
2. **Path Not Found**: Verify that parent directories exist for configured paths
3. **Invalid Timeout**: Timeout values must be positive integers
4. **Tool Not Found**: Ensure plum/pots executables are in PATH or specify full paths

### Debugging Configuration

To debug configuration issues, you can check the resolved settings:

```python
from prunejuice.core.config import Settings

settings = Settings()
print(f"Database path: {settings.db_path}")
print(f"Artifacts directory: {settings.artifacts_dir}")
print(f"Default timeout: {settings.default_timeout}")
```

### Environment Variable Testing

Test environment variables:

```bash
# Test if environment variables are set correctly
echo $PRUNEJUICE_DB_PATH
echo $PRUNEJUICE_ARTIFACTS_DIR

# List all PruneJuice environment variables
env | grep PRUNEJUICE_
```

## Migration and Compatibility

When upgrading PruneJuice versions:

1. **Backup Configuration**: Save your current `.env` files
2. **Check New Options**: Review new configuration options in release notes
3. **Test Configuration**: Verify configuration loads correctly with `prj status`
4. **Update Paths**: Ensure all paths are still valid after upgrade

## Security Considerations

- **File Permissions**: Ensure configuration files have appropriate permissions (600 or 644)
- **Sensitive Data**: Avoid storing sensitive information in configuration files
- **Path Traversal**: Use absolute paths to prevent path traversal issues
- **Environment Variables**: Be cautious with environment variables in shared environments