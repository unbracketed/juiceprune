/zen:refactor

1. When `prj status` is executed from the project directory, the Recent Events should display a column with the worktree name

```
brian /tmp/sundae [main] $ /Users/brian/code/juiceprune/.venv/bin/prj status
📊 PruneJuice Project Status
Project: sundae
Database: /private/tmp/sundae/.prj/prunejuice.db
Artifacts: /private/tmp/sundae/.prj/artifacts
                       Recent Events
┏━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Command    ┃ Status    ┃ Start Time          ┃ Duration ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ echo-hello │ completed │ 2025-06-29 16:43:48 │ 0.0s     │
│ echo-hello │ completed │ 2025-06-29 16:43:15 │ 0.0s     │
└────────────┴───────────┴─────────────────────┴──────────┘

🌳 Worktree Status
  Active worktrees: 3
    - main at /private/tmp/sundae
    - munday at /private/tmp/worktrees/sundae-munday
    - tues at /private/tmp/worktrees/sundae-tues

📺 Session Status
  No sessions found
brian /tmp/sundae [main] $ /Users/brian/code/juiceprune/.venv/bin/prj history
                            Command History
┏━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ ID   ┃ Command    ┃ Status    ┃ Start Time  ┃ Duration ┃ Project     ┃
┡━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ 2    │ echo-hello │ completed │ 06/29 16:43 │ 0.0s     │ sundae      │
│ 1    │ echo-hello │ completed │ 06/29 16:43 │ 0.0s     │ sundae-tues │
└──────┴────────────┴───────────┴─────────────┴──────────┴─────────────┘
```

2. When `prj status` is run from a project worktree dir, only show the events for the worktree, _unless_ a `-a` or `--all` flag is passed, then include items from the whole project / all worktrees

```
brian /tmp/worktrees/sundae-tues [tues] $ /Users/brian/code/juiceprune/.venv/bin/prj status
📊 PruneJuice Project Status
Project: sundae
Current worktree: tues
Database: /private/tmp/sundae/.prj/prunejuice.db
Artifacts: /private/tmp/sundae/.prj/artifacts
                       Recent Events
┏━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Command    ┃ Status    ┃ Start Time          ┃ Duration ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ echo-hello │ completed │ 2025-06-29 16:43:48 │ 0.0s     │
│ echo-hello │ completed │ 2025-06-29 16:43:15 │ 0.0s     │
└────────────┴───────────┴─────────────────────┴──────────┘

🌳 Worktree Status
  Active worktrees: 3
    - main at /private/tmp/sundae
    - munday at /private/tmp/worktrees/sundae-munday
    - tues at /private/tmp/worktrees/sundae-tues

📺 Session Status
  No sessions found
brian /tmp/worktrees/sundae-tues [tues] $ /Users/brian/code/juiceprune/.venv/bin/prj history
                            Command History
┏━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ ID   ┃ Command    ┃ Status    ┃ Start Time  ┃ Duration ┃ Project     ┃
┡━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ 2    │ echo-hello │ completed │ 06/29 16:43 │ 0.0s     │ sundae      │
│ 1    │ echo-hello │ completed │ 06/29 16:43 │ 0.0s     │ sundae-tues │
└──────┴────────────┴───────────┴─────────────┴──────────┴─────────────┘
```

Make sure to plan each change and add supporting tests to validate