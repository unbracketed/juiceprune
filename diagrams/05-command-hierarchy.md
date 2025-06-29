# PruneJuice Command Type Hierarchy

This diagram shows the command hierarchy and how different command types provide automatic lifecycle management for different use cases.

```mermaid
classDiagram
    class BaseCommand {
        <<abstract>>
        +CommandDefinition definition
        +Session session
        +StepExecutor step_executor
        +BuiltinSteps builtin_steps
        +execute()* ExecutionResult
        #_run_steps() ExecutionResult
    }
    
    class StandardCommand {
        +execute() ExecutionResult
        Note: Basic execution without automatic lifecycle management
    }
    
    class SessionCommand {
        +execute() ExecutionResult
        #_create_session()
        #_cleanup_session()
        Note: Automatically manages tmux session lifecycle
    }
    
    class WorktreeCommand {
        +execute() ExecutionResult
        #_create_worktree()
        #_cleanup_worktree()
        Note: Automatically manages worktree + session lifecycle
    }
    
    class CommandFactory {
        <<utility>>
        +create_command(definition, session, step_executor, builtin_steps) BaseCommand
        Note: Factory method that analyzes command definition to select appropriate type
    }
    
    %% Inheritance
    BaseCommand <|-- StandardCommand
    BaseCommand <|-- SessionCommand
    SessionCommand <|-- WorktreeCommand
    
    %% Factory relationship
    CommandFactory ..> BaseCommand : creates
    CommandFactory ..> StandardCommand : creates
    CommandFactory ..> SessionCommand : creates
    CommandFactory ..> WorktreeCommand : creates
    
    %% Step execution relationship
    BaseCommand --> StepExecutor : uses
    
    class StepExecutor {
        +execute(step, context, timeout) Tuple[bool, str]
        #_execute_builtin(step, context, timeout)
        #_execute_script_step(step, context, timeout)
        #_execute_shell_command(step, context, timeout)
    }
```

## Command Type Selection Logic

The `CommandFactory.create_command()` method automatically selects the appropriate command type based on:

1. **Step Analysis**: Examines all steps for specific action names:
   - `create-worktree` → triggers WorktreeCommand
   - `start-session` or `session-create` → triggers SessionCommand

2. **Command Name Patterns**:
   - Contains `worktree` or `feature-branch` → WorktreeCommand
   - Contains `session` → SessionCommand

3. **Dependency Chain**:
   - WorktreeCommand includes session management (inherits from SessionCommand)
   - SessionCommand includes basic execution (inherits from StandardCommand)

## Lifecycle Management

Each command type provides automatic resource management:

- **StandardCommand**: Basic step execution with no automatic lifecycle
- **SessionCommand**: Creates and cleans up tmux sessions automatically
- **WorktreeCommand**: Creates/cleans up both git worktrees AND tmux sessions

This design ensures that resources are properly managed regardless of whether steps succeed or fail.