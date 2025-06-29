# Prunejuice

A unified Python implementation of a parallel agentic coding workflow orchestrator. Prunejuice helps manage development workflows across git worktrees with integrated tmux session management.

## Features

- **Native Python Implementation**: Fully integrated worktree and session management without shell script dependencies
- **Git Worktree Integration**: Create, manage, and remove git worktrees seamlessly
- **Tmux Session Management**: Automatic session creation and lifecycle management for development environments
- **Command-Based Workflow**: Define and execute complex development workflows through YAML configurations
- **Modern Python Stack**: Built with asyncio, Pydantic, Typer, and GitPython

## Installation

```bash
# Using uv (recommended)
uv add prunejuice

# Or with pip
pip install prunejuice
```

## Quick Start

### 1. Initialize a Project

```bash
# Initialize prunejuice in your current directory
prj init

# Or use the longer form
prunejuice init
```

This creates a `.prj/` directory with:
- `commands/` - YAML command definitions
- `steps/` - Reusable step implementations
- `configs/` - Project configuration files

### 2. Check Project Status

```bash
prj status
```

Shows:
- Current project configuration
- Available commands
- Git worktree status
- Active tmux sessions

### 3. List Available Commands

```bash
prj list-commands
```

### 4. Run Commands

```bash
# Run a command by name
prj run setup-dev

# Run with arguments
prj run deploy target=staging

# Dry run to see what would happen
prj run deploy --dry-run

# Run with custom working directory
prj run tests --cwd /path/to/directory
```

## Core Commands

### Project Management

```bash
prj init                    # Initialize new project
prj status                  # Show project status
prj list-commands           # List available commands
prj run <command>           # Execute a command
prj run <command> --dry-run # Preview command execution
```

### Worktree Operations

Prunejuice provides native Git worktree management:

```bash
# These operations use the native Python implementation
# (No shell scripts required)

# Create worktree - handled automatically by commands
# that specify worktree requirements

# List worktrees via status
prj status

# Remove worktrees - handled by cleanup commands
```

### Session Management

Automatic tmux session integration:

```bash
# Sessions are created automatically when commands
# specify session requirements

# List active sessions
prj status

# Sessions follow naming convention:
# project-worktree-task
```

## Command Definition

Commands are defined in YAML files in `.prj/commands/`:

```yaml
# .prj/commands/setup-dev.yaml
name: setup-dev
description: Set up development environment
category: development

# Optional: Create a worktree for this command
worktree:
  branch: "dev-{{task_id}}"
  base_branch: "main"

# Optional: Create tmux session
session:
  name_template: "{{project}}-{{worktree}}-dev"
  working_directory: "{{worktree_path}}"

# Define the workflow steps
steps:
  - setup-environment
  - install-dependencies
  - configure-dev-tools
  - run-initial-tests

# Optional: Environment variables
environment:
  NODE_ENV: development
  DEBUG: "true"

# Optional: Command arguments
arguments:
  - name: skip_tests
    description: Skip running initial tests
    type: boolean
    default: false
```

### Step Definitions

Reusable steps in `.prj/steps/`:

```yaml
# .prj/steps/setup-environment.yaml
name: setup-environment
description: Set up development environment

# Shell commands to execute
commands:
  - echo "Setting up environment..."
  - uv sync --dev
  - cp .env.example .env

# Optional: Step-specific environment
environment:
  SETUP_MODE: "development"

# Optional: Success criteria
success_criteria:
  - command: "uv run python --version"
    expected_output_contains: "Python 3."
```

## Development Workflow Examples

### 1. Feature Development

```bash
# Initialize project
prj init

# Start feature development (creates worktree + session)
prj run start-feature branch=user-auth

# Run tests in the feature branch
prj run test-feature

# Deploy to staging
prj run deploy target=staging

# Clean up when done
prj run cleanup-feature branch=user-auth
```

### 2. Bug Fix Workflow

```bash
# Create hotfix branch
prj run start-hotfix issue=bug-123

# Reproduce the bug
prj run reproduce-bug test_case=auth_failure

# Apply fix and test
prj run test-fix

# Deploy hotfix
prj run deploy-hotfix
```

### 3. Code Review Setup

```bash
# Check out PR for review
prj run review-pr pr_number=456

# Run full test suite
prj run full-tests

# Performance benchmarks
prj run benchmark baseline=main
```

## Advanced Configuration

### Project Configuration

`.prj/configs/project.yaml`:

```yaml
project:
  name: my-awesome-project
  default_base_branch: main
  
worktrees:
  base_directory: "../worktrees"
  naming_pattern: "{{project}}-{{branch}}"
  
sessions:
  tmux_config: ".tmux.conf"
  default_task: "dev"
  
environments:
  development:
    NODE_ENV: development
    DEBUG: "true"
  production:
    NODE_ENV: production
    DEBUG: "false"
```

### Global Configuration

`~/.config/prunejuice/config.yaml`:

```yaml
defaults:
  editor: code
  shell: zsh
  tmux_session_prefix: "prj"

git:
  worktree_base: "~/worktrees"
  auto_cleanup: true

tmux:
  auto_attach: false
  session_timeout: "24h"
```

## Development Setup

This project uses `uv` for dependency management and includes a comprehensive Makefile:

```bash
# Development setup
make dev-setup          # Install deps, run checks and tests
make install             # Install project and dependencies
make dev-install         # Install with dev dependencies

# Testing
make test                # Run all tests
make test-coverage       # Run tests with coverage
make test-integration    # Run integration tests only
make test-cli           # Run CLI tests only

# Code quality
make lint                # Run linting
make format              # Format code
make typecheck           # Run type checking
make check               # Run all quality checks

# Project commands
make init                # Initialize new project
make status              # Show project status
make list-commands       # List available commands

# Utilities
make clean               # Clean build artifacts
make build               # Build the package
```

## Architecture

Prunejuice is built with a modular architecture:

- **CLI Layer** (`prunejuice.cli`): Typer-based command interface
- **Core Models** (`prunejuice.core`): Pydantic models for configuration and commands
- **Command System** (`prunejuice.commands`): YAML-based command loading and execution
- **Worktree Utils** (`prunejuice.worktree_utils`): Native Git worktree management
- **Session Utils** (`prunejuice.session_utils`): Native tmux session management
- **Integrations** (`prunejuice.integrations`): High-level integration interfaces

### Native Implementation Benefits

- **No Shell Dependencies**: Pure Python implementation using GitPython and asyncio
- **Better Error Handling**: Structured error handling with detailed logging
- **Type Safety**: Full type hints throughout the codebase
- **Async Support**: Native async/await for better performance
- **Cross-Platform**: Works on macOS, Linux, and Windows (where tmux is available)

## Contributing

1. Install development dependencies: `make dev-install`
2. Run tests: `make test`
3. Check code quality: `make check`
4. Submit pull request

## License

MIT License - see LICENSE file for details.