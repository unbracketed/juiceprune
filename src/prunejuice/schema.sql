-- PruneJuice Event Tracking Database Schema
-- This schema tracks SDLC command execution and session management

-- Main events table for tracking command execution
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command TEXT NOT NULL,
    project_path TEXT NOT NULL,
    worktree_name TEXT,
    session_id TEXT,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    status TEXT CHECK(status IN ('running', 'completed', 'failed', 'cancelled')) DEFAULT 'running',
    artifacts_path TEXT,
    exit_code INTEGER,
    error_message TEXT,
    metadata TEXT -- JSON blob for additional command-specific data
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS idx_events_project_path ON events(project_path);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_events_start_time ON events(start_time);
CREATE INDEX IF NOT EXISTS idx_events_worktree ON events(worktree_name);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);

-- Command definitions table for storing YAML command metadata
CREATE TABLE IF NOT EXISTS command_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    yaml_path TEXT NOT NULL,
    yaml_hash TEXT, -- For detecting changes
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Artifacts table for tracking generated files and outputs
CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    artifact_type TEXT NOT NULL, -- 'spec', 'log', 'output', 'prompt', etc.
    file_path TEXT NOT NULL,
    file_size INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

-- Sessions table for tracking tmux/development sessions
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_name TEXT UNIQUE NOT NULL,
    project_path TEXT NOT NULL,
    worktree_name TEXT,
    tmux_session_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT CHECK(status IN ('active', 'detached', 'killed')) DEFAULT 'active'
);

-- Project settings table for storing project-specific configurations
CREATE TABLE IF NOT EXISTS project_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_path TEXT UNIQUE NOT NULL,
    config_json TEXT, -- JSON blob for project configuration
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Views for common queries
CREATE VIEW IF NOT EXISTS active_events AS
SELECT * FROM events WHERE status = 'running';

CREATE VIEW IF NOT EXISTS recent_events AS
SELECT * FROM events 
ORDER BY start_time DESC 
LIMIT 50;

CREATE VIEW IF NOT EXISTS event_summary AS
SELECT 
    project_path,
    command,
    COUNT(*) as execution_count,
    AVG(CASE WHEN end_time IS NOT NULL THEN 
        (julianday(end_time) - julianday(start_time)) * 24 * 60 * 60 
        ELSE NULL END) as avg_duration_seconds,
    MAX(start_time) as last_execution
FROM events 
GROUP BY project_path, command;