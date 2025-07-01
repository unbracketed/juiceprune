# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Essential Commands
- `uv sync` - Install project dependencies
- `uv sync --dev` - Install with development dependencies
- `make test` - Run all tests using pytest
- `make test-coverage` - Run tests with coverage report
- `make lint` - Run ruff linting checks
- `make format` - Format code with ruff
- `make typecheck` - Run mypy type checking
- `make check` - Run all code quality checks (lint + typecheck)

### PruneJuice prj tool built-in Commands
- `uv run prj init` - Initialize a new prunejuice project
- `uv run prj status` - Show project status including worktrees and sessions
- `uv run prj list-commands` - List available commands
- `uv run prj run <command>` - Execute a command by name

### Testing Commands
- `uv run pytest` - Run all tests
- `uv run pytest -v` - Run tests with verbose output
- `uv run pytest --lf` - Rerun only failed tests
- `uv run pytest tests/test_cli.py -v` - Run specific test file
- `uv run pytest tests/test_integrations.py -v` - Run integration tests

## Architecture Overview

Prunejuice is a Python-based parallel agentic coding workflow orchestrator with the following key components:

### Core Architecture
- **CLI Layer** (`prunejuice.cli`): Typer-based command interface with rich console output
- **Core Models** (`prunejuice.core.models`): Pydantic models for configuration, commands, and execution
- **Action System** (`prunejuice.core.commands`): YAML-based action loading and execution with step orchestration
- **Database** (`prunejuice.core.database`): SQLite-based session and execution tracking
- **Executor** (`prunejuice.core.executor`): Async step execution engine

### Key Integrations
- **Worktree Management** (`prunejuice.worktree_utils`): Native Git worktree operations using GitPython
- **Session Management** (`prunejuice.session_utils`): Native tmux session lifecycle management
- **Action Loading** (`prunejuice.commands.loader`): YAML action definition parsing and validation

### Data Models
- **ActionDefintion**: YAML-based action specifications with steps, arguments, and environment
- **ActionStep**: Individual execution units with support for builtin, shell, and script types
- **ExecutionResult**: Tracking of action execution status and outputs
- **Session**: Persistent execution context with artifact management

### Action System Architecture
Actions are defined in YAML files with the following structure:
- `pre_steps`: Setup operations before main execution
- `steps`: Main command logic
- `post_steps`: Cleanup and finalization
- `cleanup_on_failure`: Error handling steps

Step types include:
- `builtin`: Internal Python functions
- `shell`: Shell command execution
- `script`: External script execution

### Project Structure
- `src/prunejuice/` - Main package source
- `src/prunejuice/core/` - Core orchestration logic
- `src/prunejuice/commands/` - Action system implementation
- `src/prunejuice/worktree_utils/` - Git worktree management
- `src/prunejuice/session_utils/` - Tmux session management
- `src/prunejuice/integrations/` - High-level integration interfaces
- `src/prunejuice/template_commands/` - Example YAML action definitions
- `src/prunejuice/template_steps/` - Example shell script steps
- `tests/` - Comprehensive test suite with pytest + pytest-asyncio

## Development Workflow

### Code Quality
- Uses `ruff` for linting and formatting
- Uses `mypy` for static type checking
- Uses `pytest` with `pytest-asyncio` for testing
- Comprehensive test coverage with integration tests

### Project Management
- Actions are defined in `.prj/commands/*.yaml` files
- Steps can be reusable shell scripts in `.prj/steps/`
- Sessions are automatically managed with tmux integration
- Worktrees are created and managed automatically for parallel development

### Key Development Patterns
- Async/await throughout for performance
- Pydantic models for data validation and serialization
- Rich console output for better user experience
- SQLite database for persistent state management
- Template-based command and step definitions