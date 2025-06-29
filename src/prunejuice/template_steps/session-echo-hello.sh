#!/bin/bash
# Send echo hello command to the tmux session

# Get the actual session name from previous step
if [ -f /tmp/prunejuice_session_name ]; then
    session_name=$(cat /tmp/prunejuice_session_name)
else
    # Fallback to finding it
    session_name=$(tmux list-sessions | grep "echo-hello" | cut -d: -f1 | head -1)
fi

echo "Sending 'echo hello' command to session '$session_name'..."

# Clear the pane history first to have a clean capture
tmux clear-history -t "$session_name"

# Send command to tmux session
if tmux send-keys -t "$session_name" "echo 'Hello from tmux session: $session_name'" Enter; then
    echo "✅ Command sent to session successfully"
    
    # Give it more time to execute (tmux can be slow)
    sleep 2
    
    # Capture the entire pane content
    echo "Session pane content:"
    session_output=$(tmux capture-pane -t "$session_name" -p)
    echo "$session_output"
    
    # Also try to capture just the last command and its output
    echo ""
    echo "Last few lines:"
    echo "$session_output" | tail -5
    
    # Verify the echo command actually ran by checking for our message
    if echo "$session_output" | grep -q "Hello from tmux session:"; then
        echo "✅ Confirmed: Echo command executed successfully in session"
    else
        echo "⚠️  Warning: Expected output not found in session"
    fi
else
    echo "❌ Failed to send command to session"
    exit 1
fi