/zen:planner
Add a new command. The main goal of the goal is to allow for easily tranistioning between different worktrees and/or sessions within the project, regardless of where you are in the filesystem relative to the project (project dir vs. worktree dirs). The items listed and options should be the same whether you are in the project root or in a worktree so it feels seamless to jump around
`prj resume` shows a selectable list of worktrees and open tmux sessions, if any. Use icons/emoji to distinguish between the two types in the list
If a worktree is selected, present options to cd to it in current shell, or in a new tmux session
If a session is selected, present options to attach to it, or to cd to worktree dir in current shell
If nothing available, print "Nothing simmering. Use --help for help"
Can we use `prj` with no arguments can as a shorthand for `prj resume`? What would the impact to the existing commands be?
