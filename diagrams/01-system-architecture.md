# PruneJuice System Architecture

This diagram shows the overall system architecture with clear layered separation between CLI, core logic, integrations, and utilities.

```mermaid
graph TB
    %% CLI Layer
    CLI["`**CLI Layer**
    - Typer App
    - Rich Console
    - Command Handlers`"]
    
    %% Core Layer
    EXEC["`**Executor**
    - Command Orchestration
    - Async Execution
    - Error Handling`"]
    
    LOADER["`**ActionLoader**
    - YAML Parsing
    - Command Discovery
    - Inheritance Support`"]
    
    %% Command Types
    BASECMD["`**BaseCommand**
    (Abstract)`"]
    STDCMD["`**StandardCommand**
    Basic Execution`"]
    SESSCMD["`**SessionCommand**
    + Tmux Management`"]
    WTCMD["`**WorktreeCommand**
    + Git Worktree`"]
    
    %% Step Execution
    STEPEXEC["`**StepExecutor**
    - Builtin Steps
    - Shell Commands
    - Script Execution`"]
    
    BUILTIN["`**BuiltinSteps**
    - Environment Setup
    - Worktree Creation
    - Session Management`"]
    
    %% Session & State
    SESSION["`**Session**
    - Execution Context
    - Shared Data
    - Step History`"]
    
    %% Data Layer
    DB["`**Database**
    - SQLite Async
    - Event Tracking
    - Artifact References`"]
    
    ARTIFACTS["`**ArtifactStore**
    - File Organization
    - Session Dirs
    - Cleanup Management`"]
    
    %% Integrations
    PLUM["`**PlumIntegration**
    Git Worktree Mgmt`"]
    POTS["`**PotsIntegration**
    Tmux Session Mgmt`"]
    
    %% Utilities
    WTUTILS["`**WorktreeUtils**
    - GitWorktreeManager
    - FileManager`"]
    
    SESSUTILS["`**SessionUtils**
    - TmuxManager
    - SessionLifecycle`"]
    
    %% Relationships
    CLI --> EXEC
    CLI --> LOADER
    
    EXEC --> BASECMD
    BASECMD --> STDCMD
    BASECMD --> SESSCMD
    BASECMD --> WTCMD
    
    EXEC --> STEPEXEC
    EXEC --> SESSION
    EXEC --> DB
    EXEC --> ARTIFACTS
    
    STEPEXEC --> BUILTIN
    BUILTIN --> PLUM
    BUILTIN --> POTS
    
    PLUM --> WTUTILS
    POTS --> SESSUTILS
    
    SESSION --> DB
    SESSION --> ARTIFACTS
    
    classDef cliLayer fill:#e1f5fe
    classDef coreLayer fill:#f3e5f5
    classDef dataLayer fill:#e8f5e8
    classDef integration fill:#fff3e0
    
    class CLI cliLayer
    class EXEC,LOADER,BASECMD,STDCMD,SESSCMD,WTCMD,STEPEXEC,BUILTIN,SESSION coreLayer
    class DB,ARTIFACTS dataLayer
    class PLUM,POTS,WTUTILS,SESSUTILS integration
```

## Key Architectural Patterns

1. **Layered Architecture**: Clear separation between CLI, core logic, integrations, and utilities
2. **Factory Pattern**: Used for creating appropriate command types (Standard/Session/Worktree)
3. **Strategy Pattern**: Step execution supports multiple types (builtin/shell/script)
4. **Repository Pattern**: Database operations are properly abstracted
5. **Async-First Design**: Throughout the execution pipeline for performance