# PruneJuice Integration Components

This diagram shows the integration layer and how it connects to native Python utilities and external systems. The system has migrated from shell script dependencies to robust native Python implementations.

```mermaid
graph LR
    %% Integration Layer
    subgraph "Integration Layer"
        PLUM["`**PlumIntegration**
        - create_worktree()
        - list_worktrees()
        - remove_worktree()
        - is_available()`"]
        
        POTS["`**PotsIntegration**
        - create_session()
        - list_sessions()
        - attach_session()
        - kill_session()
        - is_available()`"]
    end
    
    %% Native Implementation Layer
    subgraph "Native Python Utils"
        WTMGR["`**GitWorktreeManager**
        - create_worktree()
        - list_worktrees()
        - remove_worktree()
        - get_current_branch()
        - is_git_repository()`"]
        
        FILEMGR["`**FileManager**
        - get_default_files_to_copy()
        - copy_files()
        - handle_mcp_templates()`"]
        
        TMUXMGR["`**TmuxManager**
        - create_session()
        - list_sessions()
        - attach_session()
        - kill_session()
        - check_tmux_available()`"]
        
        SESSLC["`**SessionLifecycleManager**
        - create_session_for_worktree()
        - attach_to_session()
        - kill_session()`"]
    end
    
    %% Storage and Persistence
    subgraph "Storage Layer"
        ARTIFACTS["`**ArtifactStore**
        - create_session_dir()
        - store_file()
        - store_content()
        - get_session_artifacts()
        - cleanup_old_sessions()`"]
        
        DATABASE["`**Database**
        - start_event()
        - end_event()
        - get_recent_events()
        - get_active_events()
        - store_artifact()
        - get_events()`"]
    end
    
    %% External Systems
    subgraph "External Systems"
        GIT["`**Git**
        Worktree Operations`"]
        TMUX["`**Tmux**
        Session Management`"]
        SQLITE["`**SQLite**
        Event Persistence`"]
        FILESYSTEM["`**File System**
        Artifact Storage`"]
    end
    
    %% Relationships
    PLUM --> WTMGR
    PLUM --> FILEMGR
    POTS --> TMUXMGR
    POTS --> SESSLC
    
    WTMGR --> GIT
    TMUXMGR --> TMUX
    DATABASE --> SQLITE
    ARTIFACTS --> FILESYSTEM
    
    classDef integration fill:#fff3e0
    classDef native fill:#e8f5e8
    classDef storage fill:#f3e5f5
    classDef external fill:#ffebee
    
    class PLUM,POTS integration
    class WTMGR,FILEMGR,TMUXMGR,SESSLC native
    class ARTIFACTS,DATABASE storage
    class GIT,TMUX,SQLITE,FILESYSTEM external
```

## Integration Architecture Benefits

1. **Native Python Implementation**: Replaced shell script dependencies with robust Python modules
2. **Clean Abstraction**: Integration layer provides simple interfaces while native utils handle complexity
3. **Cross-Platform Support**: Native Python implementations work across different operating systems
4. **Better Error Handling**: Python implementations provide more detailed error information
5. **Improved Testing**: Native Python code is easier to unit test than shell scripts
6. **Performance**: Reduced subprocess overhead by using native Git and system operations

## Key Components

- **PlumIntegration**: Git worktree management with native GitPython operations
- **PotsIntegration**: Tmux session lifecycle management with native tmux API calls
- **ArtifactStore**: Organized file storage with automatic cleanup and session management
- **Database**: Async SQLite operations for event tracking and history