# Prunejuice Documentation

> It helps the PM go smoother

Welcome to the documentation for **Prunejuice** - a parallel agentic coding workflow orchestrator that helps manage development workflows across git worktrees with integrated tmux session management.

## What is Prunejuice?

Prunejuice is a unified Python implementation that provides:

- **Native Python Implementation**: Fully integrated worktree and session management without shell script dependencies
- **Git Worktree Integration**: Create, manage, and remove git worktrees seamlessly
- **Tmux Session Management**: Automatic session creation and lifecycle management for development environments
- **Command-Based Workflow**: Define and execute complex development workflows through YAML configurations
- **Modern Python Stack**: Built with asyncio, Pydantic, Typer, and GitPython

## Quick Navigation

### 🚀 Quickstart Guides
Get started quickly with Prunejuice in new or existing projects:

- **[New Project](quickstart/new-project.md)** - Start fresh with Prunejuice
- **[Existing Project](quickstart/existing-project.md)** - Add Prunejuice to your current project  
- **[First Command](quickstart/first-command.md)** - Run your first command and see results

### 📖 Essential Guides
Learn the core concepts and workflows:

- **[Command Definition](guides/command-definition.md)** - How to define and customize commands ⭐ *Primary Focus*
- **[Step Creation](guides/step-creation.md)** - Creating reusable step implementations
- **[Project Setup](guides/project-setup.md)** - Project configuration and organization
- **[Common Workflows](guides/workflows.md)** - Development workflow patterns

### 🔧 Core Concepts
Understand the architecture and components:

- **[Git Worktrees](concepts/worktrees.md)** - Native worktree integration and management
- **[Tmux Sessions](concepts/sessions.md)** - Session lifecycle and automation
- **[System Architecture](concepts/architecture.md)** - How all the pieces fit together

### 📚 Reference Documentation
Complete technical reference:

- **[CLI Commands](reference/commands.md)** - Complete command reference with examples
- **[Configuration](reference/config.md)** - All configuration options and settings
- **[YAML Schema](reference/yaml-schema.md)** - Command and step schema reference

### 🚀 Advanced Topics
Advanced integration and customization:

- **[Custom Integrations](advanced/custom-integrations.md)** - Extend Prunejuice with external tools
- **[MCP Server](advanced/mcp-server.md)** - Expose commands via Model Context Protocol
- **[Troubleshooting](advanced/troubleshooting.md)** - Solve common problems and debug issues

## Installation

```bash
# Using uv (recommended)
uv add prunejuice

# Or with pip
pip install prunejuice
```

## Quick Example

```bash
# Initialize prunejuice in your current directory
prj init

# Check project status
prj status

# List available commands
prj list-commands

# Run a command
prj run setup-dev
```

## Philosophy

Prunejuice follows these principles:

- Make each step of the SDLC scriptable and able to run independently
- Generate and store supporting artifacts with each step (plans, specs, analysis, reviews)
- Treat prompts and instructions as first-class items represented as template files
- Provide comprehensive Git worktree and Tmux session management

Ready to get started? Check out our [quickstart guides](quickstart/new-project.md)!