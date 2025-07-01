# PruneJuice Core Domain Models

This class diagram shows the core domain models and their relationships, representing the main entities that define command execution, session management, and step tracking.

```mermaid
classDiagram
    %% Core Models
    class ActionDefintion {
        +String name
        +String description
        +String category
        +List~CommandArgument~ arguments
        +Dict environment
        +List~CommandStep~ pre_steps
        +List~CommandStep~ steps
        +List~CommandStep~ post_steps
        +List~CommandStep~ cleanup_on_failure
        +int timeout
        +get_all_steps() List~CommandStep~
    }
    
    class CommandStep {
        +String name
        +StepType type
        +String action
        +Dict args
        +String script
        +int timeout
        +from_string(str) CommandStep
    }
    
    class StepType {
        <<enumeration>>
        BUILTIN
        SCRIPT
        SHELL
    }
    
    class CommandArgument {
        +String name
        +bool required
        +String type
        +Any default
        +String description
    }
    
    class Session {
        +String id
        +String command_name
        +Path project_path
        +Path worktree_path
        +String tmux_session_name
        +Dict shared_data
        +List~StepExecution~ step_history
        +Path artifact_dir
        +SessionStatus status
        +DateTime created_at
        +get_context() Dict
        +add_step_result(name, success, output, error)
        +set_shared_data(key, value)
        +get_shared_data(key, default)
    }
    
    class SessionStatus {
        <<enumeration>>
        ACTIVE
        COMPLETED
        FAILED
    }
    
    class StepExecution {
        +String name
        +StepStatus status
        +DateTime start_time
        +DateTime end_time
        +String output
        +String error
    }
    
    class StepStatus {
        <<enumeration>>
        PENDING
        RUNNING
        COMPLETED
        FAILED
        SKIPPED
    }
    
    class ExecutionEvent {
        +int id
        +String command
        +String project_path
        +String worktree_name
        +String session_id
        +String artifacts_path
        +Dict metadata
        +String status
        +int exit_code
        +String error_message
        +DateTime start_time
        +DateTime end_time
    }
    
    class ExecutionResult {
        +bool success
        +String error
        +String output
        +String artifacts_path
    }
    
    %% Relationships
    ActionDefintion ||--o{ CommandStep : contains
    ActionDefintion ||--o{ CommandArgument : has
    CommandStep ||--|| StepType : typed_as
    Session ||--o{ StepExecution : tracks
    Session ||--|| SessionStatus : has_status
    StepExecution ||--|| StepStatus : has_status
    Session ||--|| ExecutionEvent : persisted_as
```

## Key Model Relationships

- **ActionDefintion**: The central configuration model loaded from YAML files, containing all steps and metadata
- **CommandStep**: Individual execution units that can be builtin functions, shell commands, or external scripts
- **Session**: Runtime execution context that tracks state, shared data, and step history
- **ExecutionEvent**: Persistent database record of command execution for history and tracking
- **StepExecution**: Individual step execution records within a session