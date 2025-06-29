"""SQLite database layer with secure parameter binding."""

import aiosqlite
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import logging
import json
from datetime import datetime

from .models import ExecutionEvent

logger = logging.getLogger(__name__)


class Database:
    """Async SQLite database manager with secure parameter binding."""
    
    def __init__(self, db_path: Path):
        """Initialize database manager."""
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @asynccontextmanager
    async def connection(self):
        """Async context manager for database connections."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            yield db
    
    async def initialize(self):
        """Initialize database with schema."""
        schema_path = Path(__file__).parent.parent / "schema.sql"
        async with self.connection() as db:
            with open(schema_path, 'r') as f:
                await db.executescript(f.read())
            await db.commit()
    
    async def start_event(
        self,
        command: str,
        project_path: str,
        session_id: str,
        artifacts_path: str,
        worktree_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Create new event with proper parameter binding."""
        async with self.connection() as db:
            cursor = await db.execute(
                """
                INSERT INTO events 
                (command, project_path, worktree_name, session_id, 
                 artifacts_path, metadata)
                VALUES (?, ?, ?, ?, ?, json(?))
                """,
                (command, project_path, worktree_name, session_id,
                 artifacts_path, json.dumps(metadata or {}))
            )
            await db.commit()
            return cursor.lastrowid
    
    async def end_event(
        self,
        event_id: int,
        status: str,
        exit_code: int,
        error_message: Optional[str] = None
    ):
        """Update event status with secure parameters."""
        async with self.connection() as db:
            await db.execute(
                """
                UPDATE events 
                SET status = ?, exit_code = ?, error_message = ?,
                    end_time = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, exit_code, error_message, event_id)
            )
            await db.commit()
    
    async def get_recent_events(self, limit: int = 10) -> List[ExecutionEvent]:
        """Get recent events with secure parameter binding."""
        async with self.connection() as db:
            cursor = await db.execute(
                """
                SELECT id, command, project_path, worktree_name, session_id,
                       start_time, end_time, status, artifacts_path, exit_code,
                       error_message, metadata
                FROM events 
                ORDER BY start_time DESC 
                LIMIT ?
                """,
                (limit,)
            )
            rows = await cursor.fetchall()
            
            events = []
            for row in rows:
                # Parse metadata safely
                try:
                    metadata = json.loads(row[11]) if row[11] else {}
                except json.JSONDecodeError:
                    metadata = {}
                
                event = ExecutionEvent(
                    id=row[0],
                    command=row[1],
                    project_path=row[2],
                    worktree_name=row[3],
                    session_id=row[4],
                    start_time=datetime.fromisoformat(row[5]) if row[5] else datetime.utcnow(),
                    end_time=datetime.fromisoformat(row[6]) if row[6] else None,
                    status=row[7],
                    artifacts_path=row[8],
                    exit_code=row[9],
                    error_message=row[10],
                    metadata=metadata
                )
                events.append(event)
            
            return events
    
    async def get_active_events(self) -> List[ExecutionEvent]:
        """Get currently running events."""
        async with self.connection() as db:
            cursor = await db.execute(
                """
                SELECT id, command, project_path, worktree_name, session_id,
                       start_time, end_time, status, artifacts_path, exit_code,
                       error_message, metadata
                FROM events 
                WHERE status = 'running'
                ORDER BY start_time DESC
                """
            )
            rows = await cursor.fetchall()
            
            events = []
            for row in rows:
                try:
                    metadata = json.loads(row[11]) if row[11] else {}
                except json.JSONDecodeError:
                    metadata = {}
                
                event = ExecutionEvent(
                    id=row[0],
                    command=row[1],
                    project_path=row[2],
                    worktree_name=row[3],
                    session_id=row[4],
                    start_time=datetime.fromisoformat(row[5]) if row[5] else datetime.utcnow(),
                    end_time=datetime.fromisoformat(row[6]) if row[6] else None,
                    status=row[7],
                    artifacts_path=row[8],
                    exit_code=row[9],
                    error_message=row[10],
                    metadata=metadata
                )
                events.append(event)
            
            return events
    
    async def store_artifact(
        self,
        event_id: int,
        artifact_type: str,
        file_path: str,
        file_size: Optional[int] = None
    ):
        """Store artifact information with secure binding."""
        async with self.connection() as db:
            await db.execute(
                """
                INSERT INTO artifacts (event_id, artifact_type, file_path, file_size)
                VALUES (?, ?, ?, ?)
                """,
                (event_id, artifact_type, file_path, file_size)
            )
            await db.commit()
    
    async def store_command_definition(
        self,
        name: str,
        description: str,
        yaml_path: str,
        yaml_hash: str
    ):
        """Store or update command definition with secure binding."""
        async with self.connection() as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO command_definitions 
                (name, description, yaml_path, yaml_hash, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (name, description, yaml_path, yaml_hash)
            )
            await db.commit()