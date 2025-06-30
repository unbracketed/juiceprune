/zen:planner
We need some additional operations to help the workflow for worktrees: merge, pull request, and delete

Merge: this should perform a merge operation back to the parent branch; if successful, ask the user if they want to also delete the worktree or leave it
Pull Request: this should push the branch to origin (Github) and open a Pull Request against the parent branch
Delete: Cleanup the worktree directory and branch

These operations should be supported both in the CLI `prj worktree` and in the TUI as menu options for selected worktrees: "m" = Merge, "p" = Pull request, "d" or "D" if uppercase / shift+letter is supported