#!/bin/bash
# Verify session exists and can be accessed

# Get the actual session name from previous step
if [ -f /tmp/prunejuice_session_name ]; then
    session_name=$(cat /tmp/prunejuice_session_name)
else
    # Fallback to finding it
    session_name=$(tmux list-sessions | grep "echo-hello" | cut -d: -f1 | head -1)
fi

echo "Checking if session '$session_name' exists..."

# Check if session exists
if tmux has-session -t "$session_name" 2>/dev/null; then
    echo "✅ Session '$session_name' exists and is accessible"
    echo "Session info:"
    tmux list-sessions | grep "$session_name"
else
    echo "❌ Session '$session_name' not found"
    echo "Available sessions:"
    tmux list-sessions 2>/dev/null || echo "No sessions found"
    exit 1
fi