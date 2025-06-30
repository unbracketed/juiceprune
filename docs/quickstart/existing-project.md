# Adding Prunejuice to Existing Project

This guide shows you how to integrate Prunejuice into an existing project, including migration strategies, configuration best practices, and team adoption approaches.

## Prerequisites and Requirements

Before adding Prunejuice to your existing project, ensure you have:

### Essential Requirements
- **Git Repository**: Your project must be a Git repository
- **Python 3.8+**: Required for running Prunejuice
- **Clean Working Directory**: Recommended to commit or stash changes before initialization

### Optional but Recommended
- **tmux**: For session management features
- **Team Consensus**: If working in a team, discuss adoption strategy
- **Backup**: Consider backing up your current workflow configurations

### Project Structure Compatibility

Prunejuice works with any project structure, but integrates particularly well with:
- Python projects using `uv`, `pip`, or `poetry`
- Node.js projects with `npm` or `yarn`
- Go, Rust, Java, or other language projects
- Multi-language monorepos
- Existing CI/CD configurations

## Installation in Existing Project

### 1. Install Prunejuice

Choose your preferred installation method:

```bash
# Option 1: Using uv (recommended for Python projects)
uv add prunejuice --dev

# Option 2: Using pip in existing virtual environment
pip install prunejuice

# Option 3: Global installation
uv tool install prunejuice
# or
pip install --user prunejuice
```

### 2. Verify Installation

```bash
# Test the installation
prj --help

# Check current project status (before initialization)
git status
```

### 3. Initialize Prunejuice

Navigate to your project root and initialize:

```bash
# From your project root directory
cd /path/to/your-existing-project
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
[... template steps ...]
✨ Project initialized successfully!
```

## Understanding Integration Impact

### What Gets Added

Prunejuice adds a `.prj/` directory to your project:

```
your-existing-project/
├── src/                    # Your existing code
├── tests/                  # Your existing tests
├── package.json           # Your existing config
├── README.md              # Your existing docs
├── .gitignore             # Your existing git config
└── .prj/                  # 🆕 New: Prunejuice directory
    ├── commands/          # Workflow definitions
    ├── steps/             # Reusable components
    ├── configs/           # Project-specific settings
    ├── artifacts/         # Execution outputs
    └── database.db        # Execution history
```

### What Doesn't Change

Prunejuice is designed to be non-invasive:
- ✅ Your existing code remains untouched
- ✅ Your build process continues to work
- ✅ Your CI/CD pipelines are unaffected
- ✅ Your development environment stays the same
- ✅ Your team's workflow remains optional

### Git Integration

Add `.prj/` to your repository:

```bash
# Check what was created
git status

# Add the .prj directory to your repository
git add .prj/

# Consider adding artifacts to .gitignore
echo ".prj/artifacts/" >> .gitignore
echo ".prj/database.db" >> .gitignore

# Commit the new structure
git commit -m "Add Prunejuice workflow orchestration

- Initialize .prj directory with example commands
- Add workflow automation capabilities
- Ignore execution artifacts and database"
```

## Setting Up Project-Specific Configuration

### 1. Project Configuration

Create a `.env` file in your project root to customize Prunejuice settings:

```bash
# .env - Project-specific Prunejuice configuration
PRUNEJUICE_BASE_DIR=.worktrees
PRUNEJUICE_GITHUB_USERNAME=your-github-username
PRUNEJUICE_EDITOR=code
PRUNEJUICE_DEFAULT_TIMEOUT=3600

# Project-specific environment variables
NODE_ENV=development
ENVIRONMENT=dev
DEBUG=true
```

For staging and production, use separate `.env.staging` and `.env.production` files or set environment variables directly:

```bash
# .env.production
PRUNEJUICE_BASE_DIR=/var/worktrees
PRUNEJUICE_DEFAULT_TIMEOUT=7200
NODE_ENV=production
ENVIRONMENT=prod
DEBUG=false
```

See the [Configuration Reference](../reference/config.md) for all available options.

### 2. Language-Specific Setup

#### Python Projects

```yaml
# .prj/commands/python-setup.yaml
name: python-setup
description: Set up Python development environment
category: development
steps:
  - install-python-deps
  - setup-pre-commit
  - run-tests
environment:
  PYTHONPATH: "src"
  PYTEST_ARGS: "-v"
```

```bash
#!/bin/bash
# .prj/steps/install-python-deps.sh
echo "Installing Python dependencies..."
if [ -f "pyproject.toml" ]; then
    uv sync --dev
elif [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
    fi
else
    echo "No dependency file found"
fi
```

#### Node.js Projects

```yaml
# .prj/commands/node-setup.yaml
name: node-setup
description: Set up Node.js development environment
category: development
steps:
  - install-node-deps
  - run-linting
  - run-tests
environment:
  NODE_ENV: "development"
```

```bash
#!/bin/bash
# .prj/steps/install-node-deps.sh
echo "Installing Node.js dependencies..."
if [ -f "package-lock.json" ]; then
    npm ci
elif [ -f "yarn.lock" ]; then
    yarn install --frozen-lockfile
elif [ -f "pnpm-lock.yaml" ]; then
    pnpm install --frozen-lockfile
else
    npm install
fi
```

## Migrating Existing Workflows

### 1. Identify Current Workflows

Document your existing development workflows:

```bash
# Common development tasks to migrate:
# - Setting up development environment
# - Running tests
# - Code linting and formatting
# - Building and deployment
# - Database migrations
# - Documentation generation
```

### 2. Create Migration Commands

#### Migrate Build Scripts

If you have existing build scripts:

```json
// package.json (existing)
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "test": "jest",
    "lint": "eslint . --fix"
  }
}
```

Create equivalent Prunejuice commands:

```yaml
# .prj/commands/dev-server.yaml
name: dev-server
description: Start development server
category: development
steps:
  - start-dev-server
environment:
  NODE_ENV: "development"
```

```bash
#!/bin/bash
# .prj/steps/start-dev-server.sh
npm run dev
```

#### Migrate CI/CD Steps

Convert CI/CD pipeline steps to Prunejuice commands:

```yaml
# .prj/commands/ci-pipeline.yaml
name: ci-pipeline
description: Run complete CI pipeline locally
category: testing
steps:
  - install-dependencies
  - run-linting
  - run-tests
  - build-project
  - run-security-scan
timeout: 1800
```

### 3. Create Team Onboarding Command

```yaml
# .prj/commands/team-onboarding.yaml
name: team-onboarding
description: Complete team member onboarding setup
category: setup
arguments:
  - name: developer_name
    required: true
    type: string
    description: Name of the new team member
steps:
  - clone-dependencies
  - setup-environment
  - install-tools
  - run-welcome-tests
  - create-first-branch
post_steps:
  - send-welcome-message
```

## Integration with Existing Tools

### 1. IDE Integration

#### VS Code Settings

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Prunejuice: Setup Dev",
      "type": "shell",
      "command": "prj",
      "args": ["run", "setup-dev"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    },
    {
      "label": "Prunejuice: Run Tests",
      "type": "shell",
      "command": "prj",
      "args": ["run", "test-suite"],
      "group": "test"
    }
  ]
}
```

#### JetBrains IDEs

Add external tools in your IDE settings:
- **Name**: Prunejuice Status
- **Program**: `prj`
- **Arguments**: `status`
- **Working Directory**: `$ProjectFileDir$`

### 2. Git Hooks Integration

```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running Prunejuice pre-commit checks..."
prj run pre-commit-checks
```

### 3. Docker Integration

```yaml
# .prj/commands/docker-dev.yaml
name: docker-dev
description: Set up Docker development environment
category: development
steps:
  - build-docker-image
  - start-containers
  - run-migrations
  - seed-database
```

```bash
#!/bin/bash
# .prj/steps/build-docker-image.sh
docker-compose build
docker-compose up -d
```

## Best Practices for Team Adoption

### 1. Gradual Introduction

**Phase 1: Optional Usage**
```bash
# Start with simple, non-critical commands
prj run echo-hello  # Test basic functionality
prj run project-status  # Non-invasive status check
```

**Phase 2: Development Workflows**
```bash
# Introduce development convenience commands
prj run setup-dev  # Development environment setup
prj run run-tests   # Test execution
```

**Phase 3: Advanced Features**
```bash
# Add worktree and session management
prj run feature-branch feature_name="new-feature"
prj run code-review pr_number="123"
```

### 2. Documentation and Training

Create team documentation:

```markdown
# Team Prunejuice Guide

## Quick Start
1. Install: `uv tool install prunejuice`
2. Status: `prj status`
3. Available commands: `prj list-commands`

## Common Commands
- `prj run setup-dev` - Set up development environment
- `prj run run-tests` - Run test suite
- `prj run feature-branch feature_name="my-feature"` - Start feature work

## Getting Help
- `prj --help` - General help
- `prj run --help` - Command execution help
- Ask in #dev-tools Slack channel
```

### 3. Configuration Management

**Team Configuration**: Share common settings via project `.env` file (checked into git)
**Personal Configuration**: Keep personal settings in shell profile or personal `.env` file

```bash
# ~/.bashrc or ~/.zshrc (personal configuration)
export PRUNEJUICE_EDITOR="code"  # or "vim", "emacs"
export PRUNEJUICE_BASE_DIR="$HOME/dev/worktrees"
export PRUNEJUICE_DEFAULT_TIMEOUT=3600

# Or create a personal .env file that's not checked in
# .env.local (add to .gitignore)
PRUNEJUICE_EDITOR=vim
PRUNEJUICE_BASE_DIR=/Users/yourname/worktrees
```

## Troubleshooting Integration Issues

### Common Integration Problems

**1. Conflicting Scripts**
```bash
# If you have existing scripts with same names
# Rename Prunejuice commands to avoid conflicts
mv .prj/commands/test.yaml .prj/commands/prj-test.yaml
```

**2. Environment Variable Conflicts**
```yaml
# Use prefixed environment variables
environment:
  PRJ_NODE_ENV: "development"  # Instead of NODE_ENV
  PRJ_DEBUG: "true"
```

**3. Path Issues**
```bash
# Ensure PATH includes Prunejuice
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
# or for uv tool install
echo 'export PATH="$HOME/.local/share/uv/bin:$PATH"' >> ~/.bashrc
```

**4. Permission Issues**
```bash
# Make sure step files are executable
find .prj/steps -name "*.sh" -exec chmod +x {} \;
```

### Getting Help

```bash
# Check Prunejuice status
prj status

# Validate your configuration
prj list-commands

# Debug specific command
prj run your-command --dry-run

# Check logs
cat .prj/artifacts/*/execution.log
```

## Next Steps

### Immediate Actions
1. **Test Basic Functionality**: Run `prj status` and `prj list-commands`
2. **Create First Custom Command**: Migrate one existing workflow
3. **Document Team Usage**: Create internal documentation

### Short-term Goals
1. **Migrate Key Workflows**: Convert 3-5 common development tasks
2. **Team Training**: Introduce to team members gradually
3. **Integration**: Connect with existing CI/CD and development tools

### Long-term Integration
1. **Advanced Workflows**: Implement complex multi-step processes
2. **Worktree Usage**: Leverage parallel development capabilities
3. **Session Management**: Use tmux integration for development environments

## Related Guides

- **[Running Your First Command](first-command.md)**: Deep dive into command execution
- **[Command Definition Guide](../guides/command-definition.md)**: Learn advanced command creation
- **[Project Setup Guide](../guides/project-setup.md)**: Advanced configuration options
- **[Troubleshooting Guide](../advanced/troubleshooting.md)**: Solutions to common problems

Successfully integrating Prunejuice into your existing project enhances your development workflow without disrupting your current processes. Start small, document your approach, and gradually expand usage as your team becomes comfortable with the tool.