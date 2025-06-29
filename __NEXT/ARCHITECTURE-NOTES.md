Worktrees and Sessions can be treated as either ephemeral or long-running. The system is designed to work with each piece flexibly. For example, a Command can run 
without creating either a worktree or a Tmux session. Sometimes, Commands will use a Base Command which automatically creates a worktree, runs the steps in Tmux session, and clean up the worktree and session. Sometimes a Command will create a worktree and session, do some work and then wait for further input, making them long-running worktrees. 

## Database and Events Logging

One shared DB per project, used by all worktrees

Additional sqlite DBs can be specified as external to receive event writes