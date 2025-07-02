## Definitions

### Project

A thing being built, researched, or worked on. In PruneJuice, the canonical definition is a directory containing a Git repository. 

### Workspace

Work within the project happens in Workspaces, which is typically associated with a Git worktree and may have any of:

- Tmux sessions running processes
- A log of recent workspace actions and changes
- Logs / output from processes and agent sessions
- Artifacts generated like input prompts, context used, spec files, diagrams

A workspace provides an isolated, documented environment for doing some work, and the lifetime of a Workspace can vary from ephemeral - created temporarily as part of a one-shot task - to long-running. Workspaces can be created from each other (aka Git branching) to allow for nested lines of exploration, and they are designed to work well for trialing multiple runs of the same task in parallel and comparing the results at the end.

## Tools

### PruneJuice CLI

### PruneJuice TUI



## Database and Events Logging

One shared DB per project, used by all worktrees

Additional sqlite DBs can be specified as external to receive event writes


## Actions

