# Tmux Session Management

Prunejuice provides comprehensive tmux session management that creates, organizes, and maintains persistent development environments. This native Python implementation replaces shell-based session handling with a robust, programmatic approach.

## Overview

Tmux sessions in Prunejuice serve as persistent workspaces that maintain your development environment across command executions. Each session is automatically configured with the appropriate working directory, environment variables, and lifecycle management.

## Core Features

### Native Python Implementation

- **Pure Python**: Built with subprocess and asyncio, no shell dependencies
- **Type Safety**: Comprehensive type hints throughout session management
- **Error Handling**: Robust error handling with detailed logging
- **Cross-Platform**: Works wherever tmux is available

### Automatic Session Lifecycle

- **On-Demand Creation**: Sessions created when commands specify session requirements
- **Intelligent Naming**: Follows consistent patterns: `{project}-{worktree}-{task}`
- **Environment Setup**: Automatic environment variable configuration
- **Persistent State**: Sessions survive command completion for continued work

## Session Configuration

### Command-Level Configuration

Define session requirements in command YAML:

```yaml
# .prj/commands/dev-session.yaml
name: dev-session
description: Start development session with tmux

# Session specification
session:
  name_template: "{{project}}-{{worktree}}-dev"
  working_directory: "{{worktree_path}}"
  auto_attach: false
  
steps:
  - setup-environment
  - start-development-tools
```

### Project-Level Configuration

Configure session defaults in `.prj/configs/project.yaml`:

```yaml
project:
  name: my-project
  
sessions:
  tmux_config: ".tmux.conf"
  default_task: "dev"
  naming_pattern: "{{project}}-{{branch}}-{{task}}"
  auto_cleanup: true
  
environments:
  development:
    NODE_ENV: development
    DEBUG: "true"
    LOG_LEVEL: "debug"
```

### Global Configuration

Set system-wide session preferences:

```yaml
# ~/.config/prunejuice/config.yaml
defaults:
  shell: zsh
  tmux_session_prefix: "prj"
  
tmux:
  auto_attach: false
  session_timeout: "24h"
  default_window_name: "main"
```

## Session Naming Conventions

Prunejuice uses structured session names for organization and identification:

### Standard Pattern

```
{project}-{worktree}-{task}
```

**Examples:**
- `myapp-main-dev` - Main development session
- `myapp-feature-auth-dev` - Feature development
- `myapp-hotfix-123-fix` - Hotfix session
- `myapp-review-pr456-review` - Code review session

### Name Sanitization

Session names are automatically sanitized for tmux compatibility:

- **Lowercase conversion**: All names converted to lowercase
- **Character replacement**: Invalid characters replaced with hyphens
- **Length limits**: Long names truncated intelligently
- **Uniqueness**: Conflicts resolved with numeric suffixes

## Technical Implementation

### TmuxManager Class

Core session management through the `TmuxManager` class:

```python
from prunejuice.session_utils import TmuxManager

manager = TmuxManager()

# Create a new session
success = manager.create_session(
    session_name="myproject-main-dev",
    working_dir=Path("/path/to/project"),
    auto_attach=False
)

# List all sessions
sessions = manager.list_sessions()

# Attach to existing session
manager.attach_session("myproject-main-dev")

# Clean up session
manager.kill_session("myproject-main-dev")
```

### Key Methods

- **`create_session()`**: Creates new tmux session with configuration
- **`list_sessions()`**: Returns all sessions with metadata
- **`session_exists()`**: Checks if session exists
- **`attach_session()`**: Attaches to existing session
- **`kill_session()`**: Terminates session safely
- **`get_session_info()`**: Retrieves detailed session information

### SessionLifecycleManager

Higher-level session lifecycle management:

```python
from prunejuice.session_utils import SessionLifecycleManager

lifecycle = SessionLifecycleManager()

# Complete session setup with environment
session_info = lifecycle.create_session_with_environment(
    project="myproject",
    worktree="feature-auth",
    task="dev",
    working_dir=Path("/path/to/worktree"),
    environment={"NODE_ENV": "development"}
)
```

## Session Integration Patterns

### Automatic Session Creation

When a command specifies session requirements, Prunejuice:

1. **Validates** tmux availability
2. **Generates** unique session name
3. **Creates** session with working directory
4. **Configures** environment variables
5. **Tracks** session in project state
6. **Optionally** attaches to session

### Template Variables

Session configurations support dynamic template variables:

```yaml
session:
  name_template: "{{project}}-{{branch}}-{{task_type}}"
  working_directory: "{{worktree_path | default(project_path)}}"
```

Available variables:
- `{{project}}`: Project name
- `{{worktree}}`: Worktree/branch name
- `{{task}}`: Task identifier
- `{{timestamp}}`: Current timestamp
- `{{user}}`: Current user
- Command arguments as variables

### Environment Management

Sessions automatically inherit and configure environments:

```yaml
# Command-level environment
environment:
  NODE_ENV: development
  API_URL: "http://localhost:3000"
  
# Combined with project environment
session:
  inherit_project_env: true
  additional_env:
    DEBUG_SESSION: "true"
```

## Workflow Examples

### Development Session

```bash
# Start development with persistent session
prj run start-dev

# Creates session: myproject-main-dev
# Working directory: /path/to/project
# Environment: development settings loaded
```

### Feature Development

```bash
# Feature work in isolated session
prj run feature-branch branch=user-auth

# Creates:
# - Worktree: ../worktrees/myproject-user-auth/
# - Session: myproject-user-auth-dev
# - Environment: feature-specific settings
```

### Multi-Task Workflow

```bash
# Start multiple related sessions
prj run start-frontend    # myproject-main-frontend
prj run start-backend     # myproject-main-backend
prj run start-database    # myproject-main-database

# Each session configured for specific task
```

### Code Review Session

```bash
# Review PR in dedicated session
prj run review-pr pr=456

# Creates:
# - Session: myproject-review-pr456-review
# - Configured with review tools and environment
```

## Session Management Commands

### Status and Listing

```bash
# View all active sessions
prj status

# List sessions for current project
prj list-sessions

# Detailed session information
prj session-info myproject-main-dev
```

### Session Control

```bash
# Attach to existing session
prj attach myproject-main-dev

# Kill specific session
prj kill-session myproject-main-dev

# Clean up all project sessions
prj cleanup-sessions
```

### Session Persistence

```bash
# Detach from current session (keeps running)
# Ctrl+B, then D

# List detached sessions
tmux list-sessions

# Reattach later
prj attach myproject-main-dev
```

## Advanced Session Configuration

### Custom Window Layouts

```yaml
session:
  name_template: "{{project}}-{{task}}"
  windows:
    - name: "editor"
      command: "$EDITOR ."
    - name: "server"
      command: "npm run dev"
    - name: "tests"
      command: "npm run test:watch"
```

### Session Hooks

```yaml
session:
  name_template: "{{project}}-dev"
  pre_create_steps:
    - validate-environment
  post_create_steps:
    - setup-development-tools
    - start-background-services
  cleanup_steps:
    - stop-services
    - save-session-state
```

### Environment Inheritance

```yaml
# Project-level environments
environments:
  development:
    NODE_ENV: development
    LOG_LEVEL: debug
  testing:
    NODE_ENV: test
    CI: true

# Session inherits from specified environment
session:
  environment: "{{env | default('development')}}"
  additional_env:
    SESSION_ID: "{{session_name}}"
```

## Integration with Worktrees

Sessions are tightly integrated with worktree management:

### Automatic Coordination

```yaml
# Command creates both worktree and session
worktree:
  branch: "feature-{{name}}"
  base_branch: "main"
  
session:
  name_template: "{{project}}-{{branch}}-dev"
  working_directory: "{{worktree_path}}"
```

### Lifecycle Synchronization

- **Creation**: Session created after worktree setup
- **Configuration**: Working directory set to worktree path
- **Cleanup**: Session terminated when worktree removed
- **State Tracking**: Both tracked in project database

## Troubleshooting

### Common Issues

**Tmux Not Available**
```bash
# Check tmux installation
which tmux
tmux -V

# Install if missing (macOS)
brew install tmux

# Install if missing (Ubuntu)
sudo apt-get install tmux
```

**Session Creation Fails**
```bash
# Check tmux server status
tmux list-sessions

# Kill tmux server if corrupted
tmux kill-server

# Check available disk space
df -h /tmp
```

**Session Name Conflicts**
```bash
# List existing sessions
tmux list-sessions

# Kill conflicting session
tmux kill-session -t session-name

# Use unique task identifiers
prj run command task_id=unique-identifier
```

### Debugging

Enable detailed session logging:

```bash
# Debug mode
export PRJ_LOG_LEVEL=DEBUG
prj run your-command

# Check session logs
tail -f ~/.local/share/prunejuice/logs/sessions.log
```

### Recovery

Recover from session issues:

```bash
# List orphaned sessions
tmux list-sessions | grep -v attached

# Clean up orphaned sessions
for session in $(tmux list-sessions -F '#{session_name}'); do
  tmux kill-session -t "$session"
done

# Reset session state
prj reset-sessions
```

## Best Practices

### Session Organization

- **Consistent Naming**: Use descriptive, hierarchical names
- **Task Separation**: One session per logical task/context
- **Environment Isolation**: Separate sessions for different environments
- **Resource Management**: Regular cleanup of unused sessions

### Performance Optimization

- **Session Reuse**: Reuse existing sessions when appropriate
- **Resource Limits**: Set reasonable timeouts for automatic cleanup
- **Memory Management**: Monitor session memory usage
- **Background Processes**: Clean shutdown of background processes

### Security Considerations

- **Environment Variables**: Careful handling of sensitive environment data
- **Session Isolation**: Proper user permission isolation
- **Cleanup**: Secure cleanup of session data and temporary files

## Monitoring and Analytics

Track session usage and performance:

```bash
# Session statistics
prj stats sessions

# Active session monitoring
prj monitor sessions

# Session history analysis
prj analyze session-usage --timeframe=7d
```

### Database Integration

Session activities are tracked in the project database:

- **Creation/termination events** logged
- **Session duration** tracked
- **Resource usage** monitored
- **Error conditions** recorded

## Migration from Shell Scripts

Transitioning from shell-based session management:

### Assessment

1. **Audit existing scripts** for tmux operations
2. **Identify session patterns** and naming conventions
3. **Map environment setup** procedures
4. **Document workflow dependencies**

### Migration Steps

```bash
# Old shell approach
tmux new-session -d -s "project-dev" -c /path/to/project
tmux send-keys "export NODE_ENV=development" Enter
tmux send-keys "npm run dev" Enter

# New Prunejuice command
prj run start-dev  # Handles all the above automatically
```

### Validation

- **Test all workflows** in isolated environment
- **Verify environment setup** matches previous behavior
- **Confirm session lifecycle** works as expected
- **Update documentation** and team training

The native Python tmux session management provides a robust foundation for persistent development environments, enabling developers to maintain context and state across command executions while ensuring consistency and reliability.