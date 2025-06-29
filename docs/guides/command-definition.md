# How to Define Commands (PRIMARY FOCUS)

This comprehensive guide covers everything you need to know about defining commands in Prunejuice, including YAML syntax, command composition, and advanced patterns.

## Overview of SDLC Commands

SDLC (Software Development Life Cycle) commands are the core building blocks of Prunejuice workflows. They encapsulate common development tasks like code analysis, testing, branch management, and deployment into reusable, configurable units.

Each command is defined in YAML format and consists of:
- **Metadata**: Name, description, category
- **Arguments**: User-configurable inputs
- **Environment**: Variables passed to steps
- **Steps**: The actual work to be performed
- **Error handling**: Cleanup and failure recovery

Commands can be composed together, inherit from base commands, and integrate with external tools to create powerful automation workflows.

### Related Documentation

- **[Step Creation Guide](step-creation.md)** - Learn how to create custom step implementations
- **[YAML Schema Reference](../reference/yaml-schema.md)** - Complete schema documentation with validation rules
- **[Git Worktrees](../concepts/worktrees.md)** - Understanding worktree integration
- **[Tmux Sessions](../concepts/sessions.md)** - Session management concepts
- **[Configuration Options](../reference/config.md)** - Project and global configuration

## YAML Structure and Properties

### Basic Command Structure

```yaml
name: command-name
description: Brief description of what this command does
category: workflow
arguments:
  - name: arg_name
    required: true
    type: string
    description: Description of the argument
environment:
  VARIABLE_NAME: "value"
pre_steps:
  - setup-step
steps:
  - main-action-step
post_steps:
  - cleanup-step
cleanup_on_failure:
  - error-cleanup-step
timeout: 1800
```

### Core Properties

#### Required Properties
- **`name`** (string): Unique identifier for the command
- **`description`** (string): Human-readable description
- **`steps`** (list): Main execution steps

#### Optional Properties
- **`category`** (string): Grouping category (default: "workflow")
- **`arguments`** (list): Command-line arguments
- **`environment`** (dict): Environment variables
- **`pre_steps`** (list): Steps executed before main steps
- **`post_steps`** (list): Steps executed after main steps
- **`cleanup_on_failure`** (list): Steps executed when command fails
- **`timeout`** (integer): Maximum execution time in seconds (default: 1800)
- **`working_directory`** (string): Directory to execute command in
- **`extends`** (string): Inherit from base command
- **`prompt_file`** (string): Associated prompt file for AI integration

## Arguments and Environment Variables

### Defining Arguments

Arguments make commands flexible and reusable:

```yaml
arguments:
  - name: issue_number
    required: true
    type: string
    description: GitHub issue number to analyze
  - name: branch_name
    required: false
    type: string
    default: "main"
    description: Target branch for comparison
  - name: focus_areas
    required: false
    type: string
    description: Comma-separated areas to focus on
```

#### Argument Properties
- **`name`**: Argument identifier (becomes `PRUNEJUICE_ARG_<NAME>` environment variable)
- **`required`**: Whether argument is mandatory
- **`type`**: Data type ("string", "integer", "boolean")
- **`default`**: Default value if not provided
- **`description`**: Help text for users

### Environment Variables

Environment variables provide context to steps:

```yaml
environment:
  PRUNEJUICE_TASK: "code-review"
  TARGET_BRANCH: "main"
  REVIEW_MODE: "comprehensive"
```

Arguments are automatically converted to environment variables with the `PRUNEJUICE_ARG_` prefix:
- `issue_number` argument becomes `PRUNEJUICE_ARG_ISSUE_NUMBER`
- `branch_name` argument becomes `PRUNEJUICE_ARG_BRANCH_NAME`

## Step Definitions and Execution

### Step Types

Prunejuice supports three types of steps:

1. **Built-in Steps**: Predefined actions within Prunejuice
2. **Script Steps**: External shell scripts or executables
3. **Shell Steps**: Inline shell commands

### Step Definition Formats

#### Simple String Format (Auto-detected)
```yaml
steps:
  - echo-hello-step           # Built-in step
  - ./scripts/analyze.sh      # Script step
  - "git status && git log"   # Shell step
```

#### Explicit Format (Full Control)
```yaml
steps:
  - name: custom-analysis
    type: script
    action: ./scripts/analyze.sh
    args:
      target: "src/"
      depth: 3
    timeout: 600
```

### Step Execution Order

Commands execute steps in this order:
1. **`pre_steps`**: Setup and preparation
2. **`steps`**: Main command logic
3. **`post_steps`**: Cleanup and finalization
4. **`cleanup_on_failure`**: Error recovery (only on failure)

### Built-in Steps

Common built-in steps include:
- `setup-environment`: Initialize execution environment
- `validate-prerequisites`: Check system requirements
- `gather-context`: Collect project information
- `create-worktree`: Set up isolated git worktree
- `start-session`: Launch interactive session
- `store-artifacts`: Save execution results

## Real Examples from Template Files

### Simple Example Command
```yaml
# echo-hello.yaml
name: echo-hello
description: Simple echo command example - outputs hello
category: example
steps:
  - echo-hello-step
timeout: 300
```

### Command with Arguments
```yaml
# echo-arg.yaml
name: echo-arg
description: Echo command with argument example - echoes back provided message
category: example
arguments:
  - name: message
    required: true
    type: string
    description: Message to echo back
steps:
  - echo-arg-step
timeout: 300
```

### Complex Workflow Command
```yaml
# analyze-issue.yaml
name: analyze-issue
description: Analyze a GitHub issue and create implementation plan
category: analysis
arguments:
  - name: issue_number
    required: true
    type: string
    description: GitHub issue number to analyze
  - name: branch_name
    required: false
    type: string
    description: Optional branch name for worktree
environment:
  PRUNEJUICE_TASK: "analyze-issue"
pre_steps:
  - setup-environment
  - validate-prerequisites
steps:
  - gather-context
  - create-worktree
  - start-session
post_steps:
  - store-artifacts
cleanup_on_failure:
  - cleanup
timeout: 1800
```

### Session-based Command
```yaml
# echo-hello-in-session.yaml
name: echo-hello-in-session
description: Demonstrate session workflow - create detached session, send commands, destroy session
category: example
steps:
  - session-create
  - session-echo-hello
  - session-destroy
timeout: 600
```

## Command Inheritance and Base Commands

### Using the `extends` Property

Commands can inherit from base commands to reduce duplication:

```yaml
# Base command
name: base-analysis
description: Base analysis workflow
pre_steps:
  - setup-environment
  - validate-prerequisites
post_steps:
  - store-artifacts
cleanup_on_failure:
  - cleanup

# Derived command
name: security-analysis
description: Security-focused code analysis
extends: base-analysis
environment:
  ANALYSIS_TYPE: "security"
steps:
  - security-scan
  - vulnerability-check
```

### Inheritance Rules

- Child commands override parent properties
- Lists (steps, arguments) are merged unless overridden completely
- Environment variables are merged, with child values taking precedence
- Timeout and other scalar values are replaced, not merged

## Step Creation and Script Integration

### Creating Custom Steps

Steps are typically shell scripts stored in the project's `.prj/steps/` directory or Prunejuice's `template_steps/` directory.

#### Example Step Script
```bash
#!/bin/bash
# echo-arg-step.sh - Echo argument step

# Get the message argument from environment variable
message="${PRUNEJUICE_ARG_MESSAGE:-No message provided}"

echo "$message"
```

#### Session Management Step
```bash
#!/bin/bash
# session-create.sh - Create a detached tmux session

session_name="echo-hello"

echo "Creating detached tmux session: $session_name"

# Create session and capture output
output=$(prj session create "$session_name" 2>&1)
create_exit_code=$?

echo "$output"

# Verify session was created
actual_session=$(tmux list-sessions 2>/dev/null | grep "echo-hello" | cut -d: -f1 | head -1)

if [ -n "$actual_session" ]; then
    echo "✅ Detached session created successfully with name: $actual_session"
    # Store session name for other steps
    echo "$actual_session" > /tmp/prunejuice_session_name
else
    echo "❌ Session creation failed"
    exit 1
fi
```

### Step Discovery

Prunejuice discovers steps from:
1. Project-specific steps: `.prj/steps/`
2. Built-in template steps: `src/prunejuice/template_steps/`

Steps are matched by name, with project-specific steps taking precedence.

## Best Practices for Command Creation

### 1. Use Descriptive Names and Categories
```yaml
name: feature-branch-setup
description: Create feature branch with full development environment
category: development
```

### 2. Define Clear Arguments
```yaml
arguments:
  - name: feature_name
    required: true
    type: string
    description: Name of the feature to implement
  - name: issue_number
    required: false
    type: string
    description: Related GitHub issue number
```

### 3. Structure Steps Logically
```yaml
pre_steps:
  - setup-environment      # Environment preparation
  - validate-prerequisites # Dependency checking
steps:
  - gather-context         # Main workflow
  - create-worktree
  - start-session
post_steps:
  - store-artifacts        # Result preservation
cleanup_on_failure:
  - cleanup               # Error recovery
```

### 4. Set Appropriate Timeouts
```yaml
timeout: 1800  # 30 minutes for complex analysis
timeout: 300   # 5 minutes for simple operations
timeout: 600   # 10 minutes for session operations
```

### 5. Use Environment Variables Effectively
```yaml
environment:
  PRUNEJUICE_TASK: "feature-development"  # Task context
  DEBUG_MODE: "false"                     # Configuration
  LOG_LEVEL: "info"                       # Logging control
```

### 6. Implement Proper Error Handling
```yaml
cleanup_on_failure:
  - cleanup-worktree
  - remove-temp-files
  - notify-failure
```

### 7. Make Commands Composable

Design commands that can work together:
- Use consistent argument naming
- Maintain predictable output formats
- Store intermediate results for chaining

### 8. Document Command Purpose

Include comprehensive descriptions and argument help:
```yaml
description: |
  Analyze a GitHub issue and create implementation plan.
  
  This command creates an isolated worktree, analyzes the issue context,
  and starts an interactive session for development planning.
```

## Command Storage and Discovery

### Project Commands
Store custom commands in `.prj/commands/` directory:
```
project-root/
├── .prj/
│   ├── commands/
│   │   ├── my-workflow.yaml
│   │   └── custom-analysis.yaml
│   └── steps/
│       ├── my-step.sh
│       └── analysis-script.py
```

### Template Commands
Built-in commands are provided in `src/prunejuice/template_commands/`:
- `analyze-issue.yaml`
- `code-review.yaml`
- `feature-branch.yaml`
- Example commands for learning

### Command Priority
1. Project-specific commands (`.prj/commands/`)
2. Built-in template commands
3. Project commands override templates with same name

This comprehensive guide provides the foundation for creating powerful, reusable SDLC commands in Prunejuice. Start with simple examples and gradually build more complex workflows as you become familiar with the system.