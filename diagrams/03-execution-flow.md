# PruneJuice Command Execution Flow

This sequence diagram shows the complete flow of command execution from CLI invocation through to completion, including the interactions between all major components.

```mermaid
sequenceDiagram
    participant CLI
    participant Executor
    participant CommandLoader
    participant CommandFactory as Command Factory
    participant Command
    participant StepExecutor
    participant Session
    participant Database
    participant Integrations
    
    CLI->>Executor: execute_command(name, path, args)
    Executor->>Database: initialize()
    Executor->>CommandLoader: load_command(name, path)
    CommandLoader-->>Executor: CommandDefinition
    
    Executor->>Executor: validate_arguments()
    Executor->>Session: create(id, command_name, path)
    Executor->>Database: start_event()
    Database-->>Executor: event_id
    
    Executor->>CommandFactory: create_command(definition, session)
    CommandFactory-->>Executor: Command instance
    
    Executor->>Command: execute()
    
    alt WorktreeCommand
        Command->>Integrations: create_worktree()
        Command->>Integrations: create_session()
    else SessionCommand
        Command->>Integrations: create_session()
    end
    
    Command->>Command: _run_steps()
    loop for each step
        Command->>StepExecutor: execute(step, context)
        StepExecutor->>StepExecutor: determine step type
        
        alt builtin step
            StepExecutor->>Integrations: call builtin function
        else shell step
            StepExecutor->>StepExecutor: execute shell command
        else script step
            StepExecutor->>StepExecutor: execute external script
        end
        
        StepExecutor-->>Command: (success, output)
        Command->>Session: add_step_result()
        
        alt step failed
            Command->>Command: run cleanup steps
            Command-->>Executor: ExecutionResult(failed)
        end
    end
    
    Command-->>Executor: ExecutionResult(success)
    Executor->>Database: end_event(status, exit_code)
    Executor-->>CLI: ExecutionResult
```

## Execution Flow Phases

1. **Initialization**: Database setup and command loading from YAML
2. **Validation**: Argument validation and session creation
3. **Command Factory**: Automatic selection of command type (Standard/Session/Worktree)
4. **Resource Management**: Automatic creation of worktrees and tmux sessions as needed
5. **Step Execution**: Sequential execution of pre_steps → steps → post_steps
6. **Error Handling**: Automatic cleanup on failure
7. **Persistence**: Event tracking and artifact storage

The flow demonstrates the system's robust error handling and automatic resource management capabilities.