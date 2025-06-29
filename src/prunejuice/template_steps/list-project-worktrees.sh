#!/bin/bash
# List project worktrees step

# Check if prj command exists and has worktree list functionality
if command -v prj >/dev/null 2>&1; then
    if prj --help 2>/dev/null | grep -q "worktree"; then
        prj worktree list
    else
        echo "prj command found but worktree functionality not available"
        echo "Falling back to git worktree list:"
        git worktree list 2>/dev/null || echo "No git worktrees found"
    fi
else
    echo "prj command not found, using git worktree list:"
    git worktree list 2>/dev/null || echo "No git worktrees found"
fi