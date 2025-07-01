# PruneJuice Architecture Diagrams

This directory contains comprehensive Mermaid diagrams that visualize the PruneJuice Python codebase architecture and entity relationships.

## Diagram Overview

### 1. [System Architecture](01-system-architecture.md)
**Purpose**: Shows the overall system structure with layered separation between CLI, core logic, integrations, and utilities.

**Key Insights**:
- Clear separation of concerns across layers
- Async-first design throughout the execution pipeline
- Factory and strategy patterns for extensibility
- Native Python implementations replacing shell dependencies

### 2. [Domain Models](02-domain-models.md)
**Purpose**: Illustrates the core domain models and their relationships using a UML class diagram.

**Key Entities**:
- `ActionDefintion`: YAML-based command specifications
- `Session`: Runtime execution context with state management
- `ExecutionEvent`: Persistent database records for tracking
- `CommandStep`: Individual execution units with type safety

### 3. [Execution Flow](03-execution-flow.md)
**Purpose**: Demonstrates the complete command execution sequence from CLI invocation to completion.

**Flow Phases**:
- Initialization and validation
- Command factory selection
- Resource management (worktrees/sessions)
- Step-by-step execution with error handling
- Persistence and cleanup

### 4. [Integration Components](04-integration-components.md)
**Purpose**: Details the integration layer and how it connects to native Python utilities and external systems.

**Architecture Benefits**:
- Cross-platform compatibility through native Python
- Better error handling and debugging capabilities
- Improved performance with reduced subprocess overhead
- Enhanced testing and maintainability

### 5. [Command Hierarchy](05-command-hierarchy.md)
**Purpose**: Shows the command type hierarchy and automatic lifecycle management patterns.

**Command Types**:
- `StandardCommand`: Basic execution
- `SessionCommand`: + Tmux lifecycle management  
- `WorktreeCommand`: + Git worktree lifecycle management

## Architectural Strengths

The PruneJuice system demonstrates excellent architectural design:

1. **Separation of Concerns**: Clean boundaries between CLI, core logic, and integrations
2. **Type Safety**: Comprehensive use of Pydantic models for validation
3. **Async Design**: Performance-oriented with proper timeout handling
4. **Error Handling**: Robust failure management with automatic cleanup
5. **Extensibility**: Factory patterns enable easy addition of new command types
6. **Native Implementation**: Reduced external dependencies for better reliability

## Design Patterns Used

- **Factory Pattern**: Command type selection based on definition analysis
- **Strategy Pattern**: Multiple step execution strategies (builtin/shell/script)
- **Repository Pattern**: Database operations abstraction
- **Builder Pattern**: Session and artifact management
- **Template Method**: Command execution lifecycle with customizable phases

## Viewing the Diagrams

These diagrams use Mermaid syntax and can be viewed in:
- GitHub (native Mermaid support)
- VS Code with Mermaid extensions
- Online Mermaid editors
- Documentation systems that support Mermaid (GitBook, Notion, etc.)

Each diagram file includes both the visual representation and explanatory text to provide context and insights about the architectural decisions.