/zen:planner
We need some additional operations to help the workflow for worktrees: merge, pull request, and delete

Merge: this should perform a merge operation back to the parent branch; if successful, ask the user if they want to also delete the worktree or leave it
Pull Request: this should push the branch to origin (Github) and open a Pull Request against the parent branch
Delete: Cleanup the worktree directory and branch

These operations should be supported both in the CLI `prj worktree` and in the TUI as menu options for selected worktrees: "m" = Merge, "p" = Pull request, "d" or "D" if uppercase / shift+letter is supported

Take consideration for cases where the user might want to be warned about the result of an operation like for untracked or unstaged or unmerged files, deletions, etc. and try to add checks in the code and prompts / warnings to the user


---

Implementation Plan: Worktree Operations Enhancement

  Overview

  This plan adds three essential worktree operations to prunejuice: merge, pull request, and delete.
  These operations will be available in both CLI and TUI interfaces with comprehensive safety checks
  and user confirmations.

  Architecture Approach

  Service Layer Pattern: Create a dedicated WorktreeOperations service that encapsulates all business
   logic, then integrate it into both CLI and TUI layers. This ensures consistent behavior,
  testability, and maintainability.

  Current Architecture:                    Enhanced Architecture:

  CLI Commands ──┐                       CLI Commands ──┐
                 ├── GitWorktreeManager                  ├── WorktreeOperations ──┐
  TUI Interface ─┘                       TUI Interface ─┘                        ├──
  GitWorktreeManager
                                                                                 ├── GitHub CLI (gh)
                                                                                 └── Safety
  Validators

  Implementation Phases

  Phase 1: Core Service Implementation

  Step 1: Create WorktreeOperations Service
  - File: src/prunejuice/worktree_utils/operations.py
  - Dependencies: GitWorktreeManager, subprocess (for gh CLI)

  Core Methods:
  class WorktreeOperations:
      async def merge_to_parent(self, worktree_path: Path, delete_after: bool = False) -> MergeResult
      async def create_pull_request(self, worktree_path: Path, title: str = None) -> PRResult
      async def delete_worktree(self, worktree_path: Path, force: bool = False) -> DeleteResult

  Step 2: Enhanced Safety Validation
  - Parent branch detection using git merge-base and branch tracking
  - Pre-flight checks for network connectivity, authentication, and conflicts
  - Comprehensive status analysis (uncommitted changes, unmerged commits, untracked files)
  - Graceful error recovery and rollback mechanisms

  Phase 2: CLI Integration

  Step 3: Extend CLI Commands
  - File: src/prunejuice/commands/worktree.py
  - Add three new subcommands to worktree_app:

  prj worktree merge <path> [--delete] [--force]
  prj worktree pull-request <path> [--title] [--draft]
  prj worktree delete <path> [--force]

  Command Features:
  - Interactive confirmations with detailed previews
  - Safety warnings for risky operations
  - Clear error messages and recovery instructions
  - Progress indicators for long-running operations

  Phase 3: TUI Integration

  Step 4: Extend TUI Interface
  - File: src/prunejuice/tui/app.py
  - Add key bindings: "m" (merge), "p" (pull request), "d" (delete)
  - Implement action methods with progress indicators

  Step 5: Create Confirmation Dialogs
  - File: src/prunejuice/tui/dialogs.py (new)
  - Modal dialogs for operation confirmation:
    - MergeConfirmationModal - shows changes, target branch, warnings
    - PRCreationModal - title input, target branch selection, draft option
    - DeleteConfirmationModal - safety warnings, consequences, confirmation

  Phase 4: Testing & Validation

  Step 6: Comprehensive Test Suite
  - File: tests/test_worktree_operations.py (new)
  - Test coverage for each operation:
    - Merge Tests: Clean merge, conflicts, uncommitted changes, invalid parent
    - PR Tests: Successful creation, auth failures, network issues, missing gh CLI
    - Delete Tests: Clean deletion, unmerged work, running sessions, force deletion
    - Integration Tests: CLI commands with mocked operations, TUI key bindings

  Step 7: Error Recovery Mechanisms
  - Failed merge recovery (reset to original state)
  - Failed PR creation cleanup (remove pushed branch if needed)
  - Partial deletion recovery (restore worktree if tmux cleanup fails)

  Operation Details

  Merge Operation

  1. Detect parent branch using git log analysis and branch tracking
  2. Check for uncommitted changes using existing get_worktree_status
  3. Switch to parent branch in main repository
  4. Attempt merge with --no-ff strategy
  5. Handle merge conflicts with clear resolution instructions
  6. Optional worktree deletion if merge successful and requested

  Pull Request Operation

  1. Verify gh CLI availability and authentication status
  2. Push current branch to origin repository
  3. Detect parent/target branch for PR creation
  4. Create PR with auto-generated or provided title
  5. Return PR URL and status information

  Delete Operation

  1. Enhanced safety analysis for unmerged commits and untracked files
  2. Check for associated tmux sessions and offer cleanup
  3. Show detailed warning with consequences of deletion
  4. Require explicit confirmation unless force flag used
  5. Execute deletion and clean up branch references

  Success Criteria

  Functional Requirements:
  - All operations work reliably in both CLI and TUI environments
  - Comprehensive safety checks prevent data loss
  - Clear error messages guide users through recovery
  - GitHub integration handles authentication and network issues properly

  User Experience Requirements:
  - Consistent behavior between CLI and TUI interfaces
  - Appropriate confirmation prompts for destructive operations
  - Progress indicators for long-running tasks
  - Intuitive key bindings and command structure

  Technical Requirements:
  - Service layer architecture enables easy testing and maintenance
  - Rollback mechanisms handle partial failures gracefully
  - Comprehensive test coverage validates all edge cases
  - Modular design allows incremental development

  Implementation Sequence

  Critical Path:
  1. Start with WorktreeOperations.merge_to_parent() (most complex, validates architecture)
  2. Add CLI merge command (easier testing than TUI)
  3. Create basic tests (ensure reliability before proceeding)
  4. Implement PR and delete operations (build on proven patterns)
  5. Add remaining CLI commands (complete CLI functionality)
  6. Implement TUI integration (add interactive layer)
  7. Create confirmation dialogs (enhance user experience)
  8. Comprehensive testing (full integration and edge cases)

  This modular approach allows for incremental development with validation at each step, ensuring
  robust and reliable functionality throughout the implementation process.