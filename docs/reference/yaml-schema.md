# Command/Step YAML Schemas

This document provides detailed schema documentation for command and step YAML files, including all available fields, types, validation rules, and comprehensive examples.

## Overview

PruneJuice uses YAML files to define commands and their execution steps. The schema is based on Pydantic models that provide validation and type checking.

## Command Definition Schema

### Complete Schema Structure

```yaml
# Required fields
name: string                    # Command identifier
description: string             # Human-readable description

# Optional command metadata
category: string                # Command category (default: "workflow")
extends: string                 # Base command to inherit from
prompt_file: string             # Path to prompt file
timeout: integer                # Command timeout in seconds (default: 1800)
working_directory: string       # Working directory for execution

# Command arguments
arguments:
  - name: string                # Argument name
    required: boolean           # Whether argument is required (default: true)
    type: string               # Argument type (default: "string")
    default: any               # Default value
    description: string        # Argument description

# Environment variables
environment:
  KEY: "value"                 # Environment variable key-value pairs

# Step definitions
pre_steps:                     # Steps to run before main execution
  - step_definition            # Step definition (see Step Schema below)
steps:                         # Main execution steps
  - step_definition            # Step definition (see Step Schema below)
post_steps:                    # Steps to run after main execution
  - step_definition            # Step definition (see Step Schema below)
cleanup_on_failure:            # Steps to run if execution fails
  - step_definition            # Step definition (see Step Schema below)
```

## Field Definitions

### Core Fields

#### `name` (required)
- **Type**: `string`
- **Description**: Unique identifier for the command
- **Validation**: Must be a valid string
- **Example**: `"feature-branch"`, `"analyze-issue"`

#### `description` (required)
- **Type**: `string`
- **Description**: Human-readable description of what the command does
- **Example**: `"Create feature branch with full development environment"`

#### `category`
- **Type**: `string`
- **Default**: `"workflow"`
- **Description**: Categorization for command organization
- **Common Values**: `"workflow"`, `"development"`, `"analysis"`, `"example"`
- **Example**: `"development"`

#### `extends`
- **Type**: `string` (optional)
- **Description**: Name of a base command to inherit configuration from
- **Example**: `"base-development"`

#### `prompt_file`
- **Type**: `string` (optional)
- **Description**: Path to a prompt file for AI-driven commands
- **Example**: `"prompts/feature-development.md"`

#### `timeout`
- **Type**: `integer`
- **Default**: `1800` (30 minutes)
- **Description**: Maximum execution time in seconds
- **Example**: `3600` (1 hour)

#### `working_directory`
- **Type**: `string` (optional)
- **Description**: Working directory for command execution (relative to project root)
- **Example**: `"src"`, `"../other-project"`

### Argument Definitions

Arguments define the parameters that can be passed to a command.

```yaml
arguments:
  - name: "feature_name"        # Required: argument identifier
    required: true              # Optional: whether argument is mandatory
    type: "string"              # Optional: argument type validation
    default: null               # Optional: default value if not provided
    description: "Feature name" # Optional: human-readable description
```

#### Argument Types

- **`string`**: Text values (default)
- **`integer`**: Numeric values
- **`boolean`**: True/false values
- **`path`**: File system paths

#### Argument Examples

```yaml
arguments:
  # Required string argument
  - name: "issue_number"
    required: true
    type: "string"
    description: "GitHub issue number to analyze"
  
  # Optional argument with default
  - name: "branch_name"
    required: false
    type: "string"
    default: "auto-generated"
    description: "Custom branch name"
  
  # Boolean argument
  - name: "force"
    required: false
    type: "boolean"
    default: false
    description: "Force operation even if conflicts exist"
  
  # Simplified argument (name only)
  - name: "simple_arg"
```

### Environment Variables

Environment variables are set for the command execution context.

```yaml
environment:
  PRUNEJUICE_TASK: "feature-development"
  NODE_ENV: "development"
  DEBUG: "true"
  CUSTOM_PATH: "/custom/path"
```

## Step Schema

Steps can be defined in three formats:

### 1. Simple String Format (Legacy)

```yaml
steps:
  - "echo-hello-step"           # Simple step name
  - "git status"                # Shell command
  - "scripts/setup.py"          # Script path
```

### 2. Detailed Object Format

```yaml
steps:
  - name: "setup-environment"   # Step name
    type: "builtin"             # Step type (builtin, script, shell)
    action: "setup-environment" # Action to execute
    args:                       # Step arguments
      key: "value"
    timeout: 300                # Step timeout in seconds
    script: null                # Script content (for script types)
```

### 3. Mixed Format

```yaml
steps:
  - "simple-step"               # String format
  - name: "complex-step"        # Object format
    type: "shell"
    action: "npm install && npm test"
    timeout: 600
```

## Step Types

### `builtin`
- **Description**: Built-in PruneJuice operations
- **Available Actions**:
  - `setup-environment`: Initialize execution environment
  - `validate-prerequisites`: Check system requirements
  - `create-worktree`: Create git worktree via plum
  - `start-session`: Start tmux session via pots
  - `gather-context`: Collect project context information
  - `store-artifacts`: Store execution artifacts
  - `cleanup`: Clean up resources

### `script`
- **Description**: Execute a script file
- **Action**: Path to script file (relative to project or absolute)
- **Supported**: `.sh`, `.py`, `.js`, and other executable files

### `shell`
- **Description**: Execute shell commands directly
- **Action**: Shell command string
- **Features**: Supports pipes, redirects, and shell operators

## Step Arguments

Step arguments are passed to the step execution context:

```yaml
steps:
  - name: "custom-step"
    type: "script"
    action: "scripts/deploy.py"
    args:
      environment: "staging"
      region: "us-west-2"
      force: true
    timeout: 900
```

## Complete Examples

### Basic Command

```yaml
name: echo-hello
description: Simple echo command example
category: example
steps:
  - echo-hello-step
timeout: 300
```

### Command with Arguments

```yaml
name: echo-arg
description: Echo command with argument example
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

### Complex Development Command

```yaml
name: feature-branch
description: Create feature branch with full development environment
category: development
arguments:
  - name: feature_name
    required: true
    type: string
    description: Name of the feature to implement
  - name: issue_number
    required: false
    type: string
    description: Related GitHub issue number
  - name: force
    required: false
    type: boolean
    default: false
    description: Force creation even if branch exists
environment:
  PRUNEJUICE_TASK: "feature-development"
  NODE_ENV: "development"
  FEATURE_NAME: "{{ feature_name }}"
pre_steps:
  - name: "validate-environment"
    type: "builtin"
    action: "validate-prerequisites"
  - name: "check-git-status"
    type: "shell"
    action: "git status --porcelain"
    timeout: 30
steps:
  - name: "gather-project-context"
    type: "builtin"
    action: "gather-context"
  - name: "create-feature-worktree"
    type: "builtin"
    action: "create-worktree"
    args:
      branch_name: "{{ feature_name }}"
  - name: "setup-development-environment"
    type: "script"
    action: "scripts/setup-dev-env.sh"
    args:
      feature: "{{ feature_name }}"
      issue: "{{ issue_number }}"
    timeout: 600
  - name: "start-development-session"
    type: "builtin"
    action: "start-session"
post_steps:
  - name: "store-session-artifacts"
    type: "builtin"
    action: "store-artifacts"
  - name: "notify-completion"
    type: "shell"
    action: "echo 'Feature branch {{ feature_name }} ready for development'"
cleanup_on_failure:
  - name: "cleanup-failed-setup"
    type: "builtin"
    action: "cleanup"
  - name: "remove-partial-worktree"
    type: "shell"
    action: "git worktree remove --force {{ feature_name }} || true"
working_directory: "."
timeout: 1800
```

### Command with Inheritance

```yaml
# base-command.yaml
name: base-development
description: Base development command
category: base
environment:
  NODE_ENV: "development"
  DEBUG: "true"
pre_steps:
  - setup-environment
  - validate-prerequisites
post_steps:
  - store-artifacts
timeout: 1800
```

```yaml
# derived-command.yaml
name: custom-feature
description: Custom feature development
extends: base-development
category: development
arguments:
  - name: feature_type
    required: true
    type: string
    description: Type of feature to create
environment:
  FEATURE_TYPE: "{{ feature_type }}"
steps:
  - gather-context
  - create-worktree
  - start-session
```

## Validation Rules

### Command Validation

1. **Required Fields**: `name` and `description` must be present
2. **Name Format**: Command names should use lowercase with hyphens
3. **Timeout Values**: Must be positive integers
4. **Step Arrays**: All step arrays must contain valid step definitions

### Argument Validation

1. **Name Uniqueness**: Argument names must be unique within a command
2. **Type Validation**: Type must be one of: `string`, `integer`, `boolean`, `path`
3. **Required Logic**: Required arguments cannot have default values
4. **Default Types**: Default values must match the specified type

### Step Validation

1. **Type Validation**: Step type must be `builtin`, `script`, or `shell`
2. **Action Required**: All steps must have a valid action
3. **Timeout Limits**: Step timeouts must be positive and reasonable
4. **Script Paths**: Script actions must reference accessible files

## Error Examples

### Invalid Command Structure

```yaml
# ❌ Missing required fields
name: incomplete-command
# Missing description
steps:
  - invalid-step
```

```yaml
# ❌ Invalid timeout
name: bad-timeout
description: Command with invalid timeout
timeout: -100  # Negative timeout invalid
steps:
  - echo-hello
```

### Invalid Arguments

```yaml
# ❌ Duplicate argument names
name: duplicate-args
description: Command with duplicate argument names
arguments:
  - name: duplicate
    type: string
  - name: duplicate  # Duplicate name
    type: integer
steps:
  - echo-hello
```

```yaml
# ❌ Required argument with default value
name: invalid-required
description: Command with invalid required argument
arguments:
  - name: bad_arg
    required: true
    default: "should not have default"  # Invalid combination
steps:
  - echo-hello
```

### Invalid Steps

```yaml
# ❌ Invalid step type
name: bad-step-type
description: Command with invalid step type
steps:
  - name: invalid-step
    type: "unknown-type"  # Invalid step type
    action: "some-action"
```

```yaml
# ❌ Missing action
name: missing-action
description: Command with missing step action
steps:
  - name: incomplete-step
    type: "builtin"
    # Missing action field
```

## Best Practices

### Command Design

1. **Descriptive Names**: Use clear, hyphenated command names
2. **Meaningful Descriptions**: Provide comprehensive descriptions
3. **Appropriate Categories**: Use consistent categorization
4. **Reasonable Timeouts**: Set appropriate timeout values

### Argument Design

1. **Clear Names**: Use descriptive argument names
2. **Helpful Descriptions**: Provide clear argument descriptions
3. **Sensible Defaults**: Use reasonable default values
4. **Type Safety**: Specify appropriate argument types

### Step Organization

1. **Logical Grouping**: Group related steps together
2. **Error Handling**: Include cleanup steps for failure scenarios
3. **Clear Naming**: Use descriptive step names
4. **Appropriate Timeouts**: Set step-specific timeouts when needed

### Environment Variables

1. **Consistent Naming**: Use consistent environment variable naming
2. **Documentation**: Document custom environment variables
3. **Security**: Avoid sensitive data in YAML files
4. **Template Variables**: Use `{{ variable }}` syntax for argument substitution

## Migration from Legacy Formats

### String Steps to Object Steps

```yaml
# Old format
steps:
  - "simple-command"

# New format (recommended)
steps:
  - name: "simple-command"
    type: "builtin"
    action: "simple-command"
```

### Adding Type Information

```yaml
# Minimal
steps:
  - "git status"

# Enhanced
steps:
  - name: "check-git-status"
    type: "shell"
    action: "git status"
    timeout: 30
```

## Schema Evolution

The YAML schema continues to evolve. Future versions may include:

- **Conditional Steps**: Steps that execute based on conditions
- **Parallel Execution**: Support for parallel step execution
- **Step Dependencies**: Explicit step dependency management
- **Dynamic Arguments**: Runtime argument resolution
- **Enhanced Validation**: More sophisticated validation rules

For the latest schema updates, check the release notes and migration guides.