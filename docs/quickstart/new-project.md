# Starting Fresh with Prunejuice

This guide walks you through setting up Prunejuice in a new project from scratch. You'll learn how to install Prunejuice, initialize a project, understand the created structure, and run your first command.

## Prerequisites

- **Git**: Prunejuice uses Git worktrees for parallel development workflows
- **Python 3.8+**: Required for running Prunejuice
- **tmux** (optional): For session management features
- **uv** (recommended): For Python package management

## Installation

### Using uv (Recommended)

```bash
# Install globally
uv tool install prunejuice

# Or add to a project
uv add prunejuice
```

### Using pip

```bash
# Install globally
pip install prunejuice

# Or in a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install prunejuice
```

### Verify Installation

```bash
# Check that prunejuice is installed
prj --help

# Or use the full command name
prunejuice --help
```

You should see the help output showing available commands.

## Creating Your First Project

### 1. Create a New Project Directory

```bash
# Create and navigate to your project directory
mkdir my-awesome-project
cd my-awesome-project

# Initialize as a Git repository (required)
git init
git branch -M main
```

> **Note**: Prunejuice requires a Git repository to function, as it uses Git worktrees for parallel development workflows.

### 2. Initialize Prunejuice

```bash
# Initialize prunejuice in your current directory
prj init
```

**Expected Output:**
```
🧃 Initializing PruneJuice project...
Copied template: analyze-issue.yaml
Copied template: code-review.yaml
Copied template: feature-branch.yaml
Copied template: echo-hello.yaml
Copied template: echo-arg.yaml
Copied template: worktree-list.yaml
Copied template: echo-hello-in-session.yaml
Copied template step: echo-hello-step.sh
Copied template step: echo-arg-step.sh
Copied template step: list-project-worktrees.sh
Copied template step: session-create.sh
Copied template step: session-echo-hello.sh
Copied template step: session-destroy.sh
✨ Project initialized successfully!
```

## Understanding the Created Structure

The `prj init` command creates a `.prj/` directory with the following structure:

```
.prj/
├── commands/           # YAML command definitions
│   ├── analyze-issue.yaml
│   ├── code-review.yaml
│   ├── echo-hello.yaml
│   ├── feature-branch.yaml
│   └── ...
├── steps/              # Reusable step implementations
│   ├── echo-hello-step.sh
│   ├── session-create.sh
│   └── ...
├── configs/            # Project configuration files
├── artifacts/          # Command execution artifacts
└── database.db         # SQLite database for execution history
```

### Key Directories Explained

- **`commands/`**: Contains YAML files defining your workflows. Each command specifies steps, environment variables, and execution parameters.
- **`steps/`**: Contains reusable script files that can be shared across multiple commands.
- **`configs/`**: Stores project-specific configuration files.
- **`artifacts/`**: Stores outputs, logs, and artifacts from command executions.

## Running Your First Command

### 1. Check Project Status

```bash
prj status
```

**Expected Output:**
```
📊 PruneJuice Project Status

🔧 Project: my-awesome-project
📁 Root: /path/to/my-awesome-project
🌿 Current Branch: main

📋 Available Commands: 7
🌳 Active Worktrees: 0
🖥️  Active Sessions: 0

📈 Recent Activity: No executions yet
```

### 2. List Available Commands

```bash
prj list-commands
```

**Expected Output:**
```
📋 Available Commands

Example Commands:
├── echo-hello          Simple echo command example
├── echo-arg           Echo command with arguments
└── echo-hello-in-session  Session workflow demonstration

Development Commands:
├── analyze-issue      Analyze and understand project issues
├── code-review        Comprehensive code review workflow
└── feature-branch     Create feature branch with development environment

Utility Commands:
└── worktree-list      List project worktrees
```

### 3. Run Your First Simple Command

Let's start with the simplest command:

```bash
prj run echo-hello
```

**Expected Output:**
```
🧃 Executing command: echo-hello
📝 Description: Simple echo command example - outputs hello

🔄 Step 1/1: echo-hello-step
   ▶ Executing: echo-hello-step.sh
   hello

✅ Command completed successfully in 0.2s
💾 Artifacts saved to: .prj/artifacts/echo-hello-20240315-143022
```

### 4. Try a Command with Arguments

```bash
prj run echo-arg message="Hello, Prunejuice!"
```

**Expected Output:**
```
🧃 Executing command: echo-arg
📝 Description: Echo command with arguments

🔄 Step 1/1: echo-arg-step
   ▶ Executing: echo-arg-step.sh
   Hello, Prunejuice!

✅ Command completed successfully in 0.1s
💾 Artifacts saved to: .prj/artifacts/echo-arg-20240315-143045
```

### 5. Preview Commands with Dry Run

Before running complex commands, you can preview what they'll do:

```bash
prj run feature-branch --dry-run feature_name="user-authentication"
```

**Expected Output:**
```
🧃 Dry Run: feature-branch
📝 Description: Create feature branch with full development environment

📋 Command Configuration:
   Arguments: feature_name=user-authentication
   Environment: PRUNEJUICE_TASK=feature-development
   Timeout: 1800s

🔄 Planned Execution Steps:
   Pre-steps:
   1. setup-environment
   2. validate-prerequisites
   
   Main steps:
   3. gather-context
   4. create-worktree
   5. start-session
   
   Post-steps:
   6. store-artifacts

⚠️  This is a dry run - no changes will be made
```

## Understanding Command Output and Artifacts

### Execution Artifacts

Every command execution creates artifacts in `.prj/artifacts/`:

```bash
# View recent artifacts
ls -la .prj/artifacts/

# Example output:
echo-hello-20240315-143022/
├── execution.log       # Detailed execution log
├── output.txt         # Command output
├── metadata.json      # Execution metadata
└── environment.json   # Environment variables used
```

### Viewing Execution History

```bash
prj status
```

The status command shows recent execution history and provides insights into your project's activity.

## Next Steps

Now that you have Prunejuice running, you can:

### 1. Create Custom Commands

Create a new command file in `.prj/commands/`:

```yaml
# .prj/commands/my-first-command.yaml
name: my-first-command
description: My first custom command
category: custom
steps:
  - echo-hello-step
environment:
  MY_VAR: "custom-value"
```

### 2. Explore Advanced Features

- **[Command Definition Guide](../guides/command-definition.md)**: Learn to create complex workflows
- **[Step Creation Guide](../guides/step-creation.md)**: Build reusable step components
- **[Worktrees Concept](../concepts/worktrees.md)**: Understand parallel development workflows
- **[Sessions Concept](../concepts/sessions.md)**: Learn about tmux session management

### 3. Try Development Workflows

```bash
# Create a feature branch with full development environment
prj run feature-branch feature_name="my-feature"

# Analyze project issues
prj run analyze-issue

# Perform code review
prj run code-review
```

### 4. Integration with Existing Tools

Prunejuice integrates well with:
- **Git workflows**: Automatic worktree and branch management
- **CI/CD pipelines**: Run as part of automated workflows
- **IDEs**: Use commands to set up development environments
- **Team workflows**: Share command definitions across teams

## Troubleshooting

### Common Issues

**Command not found: `prj`**
```bash
# Ensure prunejuice is in your PATH
which prj
# If not found, try:
python -m prunejuice --help
```

**Permission denied on step execution**
```bash
# Make sure step files are executable
chmod +x .prj/steps/*.sh
```

**Git repository required**
```bash
# Initialize git if you haven't already
git init
git branch -M main
```

### Getting Help

```bash
# General help
prj --help

# Command-specific help
prj run --help

# List all available commands
prj list-commands
```

## What's Next?

- **[Adding Prunejuice to Existing Project](existing-project.md)**: If you want to add Prunejuice to an existing codebase
- **[Running Your First Command](first-command.md)**: Deep dive into command execution
- **[Project Setup Guide](../guides/project-setup.md)**: Advanced project configuration options

Congratulations! You've successfully set up your first Prunejuice project and run your first commands. You're now ready to explore more advanced workflows and integrate Prunejuice into your development process.