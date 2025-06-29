# Running Your First Command

This comprehensive guide walks you through executing your first Prunejuice command, from understanding the command structure to interpreting output and exploring the artifacts created during execution.

## Understanding Command Structure

Before running commands, it's helpful to understand how Prunejuice commands are structured and what happens during execution.

### Command Anatomy

Every Prunejuice command consists of:

```yaml
# .prj/commands/example-command.yaml
name: example-command              # Command identifier
description: What this command does # Human-readable description
category: development              # Organizational category (optional)

# Execution steps (required)
steps:
  - step-one                      # References a step file
  - step-two

# Optional configurations
arguments:                        # Command-line arguments
  - name: feature_name
    required: true
    type: string
    description: Name of the feature

environment:                      # Environment variables
  DEBUG: "true"
  NODE_ENV: "development"

timeout: 300                      # Maximum execution time (seconds)
```

### Step Files

Steps are the actual work units, typically shell scripts:

```bash
#!/bin/bash
# .prj/steps/example-step.sh
echo "Executing example step..."
# Your actual work here
```

## Getting Started: Basic Command Execution

### 1. Initialize Your Project (if not done already)

```bash
# Navigate to your project directory
cd your-project

# Initialize Prunejuice
prj init
```

### 2. Explore Available Commands

```bash
# List all available commands
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

### 3. Check Project Status

```bash
prj status
```

**Expected Output:**
```
📊 PruneJuice Project Status

🔧 Project: your-project
📁 Root: /path/to/your-project
🌿 Current Branch: main

📋 Available Commands: 7
🌳 Active Worktrees: 0
🖥️  Active Sessions: 0

📈 Recent Activity: No executions yet
```

## Running Your First Simple Command

### The Simplest Command: echo-hello

Start with the most basic command to understand the execution flow:

```bash
prj run echo-hello
```

**Detailed Output Breakdown:**

```
🧃 Executing command: echo-hello              # Command identification
📝 Description: Simple echo command example   # Command description

🔄 Step 1/1: echo-hello-step                 # Step progress indicator
   ▶ Executing: echo-hello-step.sh           # Current step execution
   hello                                      # Step output

✅ Command completed successfully in 0.2s     # Success indicator with timing
💾 Artifacts saved to: .prj/artifacts/echo-hello-20240315-143022  # Artifact location
```

### Understanding What Happened

1. **Command Resolution**: Prunejuice found `echo-hello.yaml` in `.prj/commands/`
2. **Step Execution**: It executed the `echo-hello-step` referenced in the command
3. **Output Capture**: All output was captured and displayed
4. **Artifact Storage**: Execution details were saved for future reference
5. **Success Reporting**: Command completed successfully with timing information

## Running Commands with Arguments

### Command with Simple Arguments

```bash
prj run echo-arg message="Hello, World!"
```

**Expected Output:**
```
🧃 Executing command: echo-arg
📝 Description: Echo command with arguments

🔄 Step 1/1: echo-arg-step
   ▶ Executing: echo-arg-step.sh
   Hello, World!

✅ Command completed successfully in 0.1s
💾 Artifacts saved to: .prj/artifacts/echo-arg-20240315-143045
```

### Complex Command with Multiple Arguments

```bash
prj run feature-branch feature_name="user-authentication" issue_number="123"
```

**Note**: This command may require additional setup (worktree creation) so let's first explore it with a dry run.

## Using Dry Run for Command Preview

Dry run shows you what a command will do without actually executing it:

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

### Understanding Dry Run Output

- **Command Configuration**: Shows all parameters and settings
- **Planned Execution Steps**: Lists all steps that would be executed
- **Environment Variables**: Shows environment that would be set
- **Timeout**: Maximum execution time allowed

## Understanding Command Output and Artifacts

### Real-time Output

During command execution, you see:

```
🧃 Executing command: your-command           # Command start
📝 Description: Command description

🔄 Step 1/3: first-step                     # Progress indicator
   ▶ Executing: first-step.sh               # Current step
   [step output appears here]               # Step's actual output

🔄 Step 2/3: second-step                    # Next step
   ▶ Executing: second-step.sh
   [step output appears here]

🔄 Step 3/3: final-step                     # Final step
   ▶ Executing: final-step.sh
   [step output appears here]

✅ Command completed successfully in 2.3s    # Success summary
💾 Artifacts saved to: .prj/artifacts/your-command-20240315-143022
```

### Execution Artifacts

Every command execution creates detailed artifacts:

```bash
# Navigate to the artifacts directory
cd .prj/artifacts/echo-hello-20240315-143022

# List all artifacts
ls -la
```

**Artifact Structure:**
```
echo-hello-20240315-143022/
├── execution.log          # Complete execution log
├── output.txt            # Captured command output
├── metadata.json         # Execution metadata
├── environment.json      # Environment variables used
├── timing.json          # Step-by-step timing information
└── command-config.yaml  # Full command configuration used
```

### Examining Artifacts

**View the execution log:**
```bash
cat .prj/artifacts/echo-hello-*/execution.log
```

**Example log content:**
```
2024-03-15 14:30:22 [INFO] Starting command execution: echo-hello
2024-03-15 14:30:22 [INFO] Command description: Simple echo command example
2024-03-15 14:30:22 [INFO] Step 1/1: echo-hello-step
2024-03-15 14:30:22 [INFO] Executing step: echo-hello-step.sh
2024-03-15 14:30:22 [INFO] Step completed successfully
2024-03-15 14:30:22 [INFO] Command completed in 0.2s
```

**View execution metadata:**
```bash
cat .prj/artifacts/echo-hello-*/metadata.json
```

**Example metadata:**
```json
{
  "command_name": "echo-hello",
  "execution_id": "echo-hello-20240315-143022",
  "start_time": "2024-03-15T14:30:22.123456Z",
  "end_time": "2024-03-15T14:30:22.345678Z",
  "duration_seconds": 0.222222,
  "status": "completed",
  "exit_code": 0,
  "steps_executed": 1,
  "artifacts_path": "/path/to/.prj/artifacts/echo-hello-20240315-143022"
}
```

## Exploring Session-Based Commands

### Running a Session Command

Try a command that demonstrates session management:

```bash
prj run echo-hello-in-session
```

**Expected Output:**
```
🧃 Executing command: echo-hello-in-session
📝 Description: Demonstrate session workflow - create detached session, send commands, destroy session

🔄 Step 1/3: session-create
   ▶ Executing: session-create.sh
   Created tmux session: prj-echo-hello-session

🔄 Step 2/3: session-echo-hello
   ▶ Executing: session-echo-hello.sh
   Sent command to session: echo "Hello from session!"
   Session output: Hello from session!

🔄 Step 3/3: session-destroy
   ▶ Executing: session-destroy.sh
   Destroyed tmux session: prj-echo-hello-session

✅ Command completed successfully in 1.2s
💾 Artifacts saved to: .prj/artifacts/echo-hello-in-session-20240315-143100
```

### Understanding Session Management

This command demonstrates:
1. **Session Creation**: Creates a tmux session for isolated execution
2. **Command Execution**: Runs commands within the session
3. **Session Cleanup**: Properly destroys the session after completion

## Advanced Command Execution Options

### Custom Working Directory

```bash
# Run command in a specific directory
prj run echo-hello --cwd /path/to/specific/directory
```

### Environment Variable Override

```bash
# Set additional environment variables
DEBUG=true VERBOSE=1 prj run echo-hello
```

### Command Execution with Timeout

Some commands have built-in timeouts, but you can also interrupt:

```bash
# Start a long-running command
prj run long-running-command

# Interrupt with Ctrl+C if needed
# Prunejuice will handle cleanup gracefully
```

## Working with Worktrees and Sessions

### Understanding Worktree Commands

List current worktrees:

```bash
prj run worktree-list
```

**Expected Output:**
```
🧃 Executing command: worktree-list
📝 Description: List project worktrees

🔄 Step 1/1: list-project-worktrees
   ▶ Executing: list-project-worktrees.sh
   Active worktrees:
   /path/to/your-project  (main)
   
   No additional worktrees found.

✅ Command completed successfully in 0.1s
```

### Creating Feature Branches with Worktrees

When you're ready for more advanced workflows:

```bash
# This will create a new git worktree and tmux session
prj run feature-branch feature_name="my-new-feature"
```

**Expected Process:**
1. Creates a new Git worktree in a separate directory
2. Switches to the new branch
3. Sets up a development environment
4. Creates a tmux session for development
5. Provides you with the session name to attach to

## Troubleshooting Common Issues

### Command Not Found

```bash
prj run non-existent-command
```

**Error Output:**
```
❌ Error: Command 'non-existent-command' not found
📋 Available commands:
   - echo-hello
   - echo-arg
   - echo-hello-in-session
   [... other commands ...]

💡 Use 'prj list-commands' to see all available commands
```

### Step Execution Failure

If a step fails, you'll see detailed error information:

```
🧃 Executing command: failing-command

🔄 Step 1/2: working-step
   ▶ Executing: working-step.sh
   This step works fine

🔄 Step 2/2: failing-step
   ▶ Executing: failing-step.sh
   ❌ Step failed with exit code 1
   Error output: some error message

❌ Command failed at step 2/2: failing-step
💾 Artifacts saved to: .prj/artifacts/failing-command-20240315-143200
🔍 Check the execution log for details: .prj/artifacts/failing-command-20240315-143200/execution.log
```

### Permission Issues

```bash
# If you get permission denied errors
chmod +x .prj/steps/*.sh
```

### Path Issues

```bash
# If prj command is not found
which prj

# Add to PATH if needed (for uv tool install)
export PATH="$HOME/.local/share/uv/bin:$PATH"
```

## Command Execution Best Practices

### 1. Start Simple

Always begin with basic commands:
```bash
prj run echo-hello          # Test basic functionality
prj status                  # Check project state
prj list-commands           # Explore available options
```

### 2. Use Dry Run for Complex Commands

```bash
prj run complex-command --dry-run  # Preview before execution
```

### 3. Monitor Artifacts

```bash
# Check recent executions
ls -t .prj/artifacts/ | head -5

# Review logs for troubleshooting
tail -f .prj/artifacts/*/execution.log
```

### 4. Understand Command Dependencies

Some commands may require:
- Clean git working directory
- Specific branch states
- Environment setup
- External tools (docker, npm, etc.)

### 5. Session Management

For commands that create sessions:
```bash
# List active tmux sessions
tmux list-sessions

# Attach to a session created by Prunejuice
tmux attach-session -t session-name

# Detach from session: Ctrl+b, then d
```

## Next Steps and Advanced Usage

### Custom Command Creation

Create your own command:

```yaml
# .prj/commands/my-command.yaml
name: my-command
description: My custom command
category: custom
steps:
  - my-custom-step
environment:
  MY_VAR: "custom-value"
```

```bash
#!/bin/bash
# .prj/steps/my-custom-step.sh
echo "Running my custom step with MY_VAR: $MY_VAR"
```

### Integration with Development Workflow

```bash
# Development setup
prj run setup-dev

# Run tests
prj run run-tests

# Code analysis
prj run analyze-issue

# Code review
prj run code-review
```

### Monitoring and Debugging

```bash
# Check overall project status
prj status

# View execution history
ls -la .prj/artifacts/

# Analyze command performance
grep "duration" .prj/artifacts/*/metadata.json
```

## Related Documentation

- **[Command Definition Guide](../guides/command-definition.md)**: Learn to create complex commands
- **[Step Creation Guide](../guides/step-creation.md)**: Build reusable step components
- **[Worktrees Concept](../concepts/worktrees.md)**: Understand parallel development
- **[Sessions Concept](../concepts/sessions.md)**: Learn tmux integration
- **[Project Setup Guide](../guides/project-setup.md)**: Advanced configuration

## Summary

You've successfully learned how to:

1. ✅ **Run basic commands** with `prj run echo-hello`
2. ✅ **Use command arguments** with `prj run echo-arg message="text"`
3. ✅ **Preview commands** with `--dry-run` flag
4. ✅ **Understand command output** and execution flow
5. ✅ **Explore artifacts** created during execution
6. ✅ **Work with sessions** using session-based commands
7. ✅ **Troubleshoot common issues** and understand error messages

Prunejuice commands are powerful building blocks for automating your development workflow. Start with simple commands and gradually work up to more complex workflows involving worktrees, sessions, and multi-step processes.

**Next recommended actions:**
- Try creating a custom command for your specific workflow
- Explore the feature-branch command for parallel development
- Integrate Prunejuice commands into your daily development routine