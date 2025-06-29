#!/bin/bash
# Kill/destroy the tmux session

# Get the actual session name from previous step
if [ -f /tmp/prunejuice_session_name ]; then
    session_name=$(cat /tmp/prunejuice_session_name)
else
    # Fallback to finding it
    session_name=$(tmux list-sessions | grep "echo-hello" | cut -d: -f1 | head -1)
fi

echo "Destroying tmux session: $session_name"

# Use tmux directly since prj session kill expects the original name
tmux kill-session -t "$session_name" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Session '$session_name' destroyed successfully"
else
    echo "❌ Failed to destroy session '$session_name'"
    # Don't exit with error - session might not exist
fi

# Verify it's gone
if ! tmux has-session -t "$session_name" 2>/dev/null; then
    echo "✅ Confirmed: Session '$session_name' no longer exists"
else
    echo "⚠️  Warning: Session '$session_name' still exists"
fi

# Cleanup temp file
rm -f /tmp/prunejuice_session_name