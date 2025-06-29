#!/bin/bash
# Create a detached tmux session for echo-hello demo

session_name="echo-hello"

echo "Creating detached tmux session: $session_name"

# Capture the output to check for actual success
output=$(prj session create "$session_name" 2>&1)
create_exit_code=$?

echo "$output"

# Check if session was actually created by verifying it exists
actual_session=$(tmux list-sessions 2>/dev/null | grep "echo-hello" | cut -d: -f1 | head -1)

if [ -n "$actual_session" ]; then
    echo "✅ Detached session created successfully with name: $actual_session"
    echo "📋 Session is running in background, ready for commands"
    # Store it for other steps to use
    echo "$actual_session" > /tmp/prunejuice_session_name
elif echo "$output" | grep -q "not a valid worktree"; then
    echo "❌ Failed to create session: Current directory is not a valid git worktree"
    echo "💡 Tip: Run this command from within a git worktree directory"
    exit 1
elif echo "$output" | grep -q "Error:"; then
    echo "❌ Failed to create session due to error in output"
    exit 1
elif [ $create_exit_code -ne 0 ]; then
    echo "❌ Session creation command failed with exit code $create_exit_code"
    exit 1
else
    echo "❌ Session creation appears to have failed - no session found"
    echo "Command output: $output"
    exit 1
fi