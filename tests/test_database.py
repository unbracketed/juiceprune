"""Tests for database security and functionality."""

import pytest
import json
from datetime import datetime

from prunejuice.core.database import Database
from prunejuice.core.models import ExecutionEvent


@pytest.mark.asyncio
async def test_sql_injection_protection(test_database):
    """Verify SQL injection attacks are prevented."""
    # Attempt various SQL injection patterns
    malicious_inputs = [
        "'; DROP TABLE events; --",
        "' OR '1'='1",
        "'; DELETE FROM events; --",
        "' UNION SELECT * FROM sqlite_master; --",
        "\\'; DROP TABLE events; /*"
    ]
    
    for malicious_input in malicious_inputs:
        # Try injecting via event creation
        event_id = await test_database.start_event(
            command=malicious_input,
            project_path="/tmp",
            session_id="test",
            artifacts_path="/tmp"
        )
        
        # Verify the table still exists and data is stored safely
        async with test_database.connection() as conn:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='events'"
            )
            assert await cursor.fetchone() is not None
            
            # Verify the malicious input was stored as data, not executed
            cursor = await conn.execute(
                "SELECT command FROM events WHERE id = ?", (event_id,)
            )
            result = await cursor.fetchone()
            assert result[0] == malicious_input


@pytest.mark.asyncio
async def test_parameter_binding(test_database):
    """Test that all database operations use parameter binding."""
    # Test event creation with special characters
    special_chars = "'; SELECT * FROM events; /*"
    
    event_id = await test_database.start_event(
        command="test-command",
        project_path=special_chars,
        session_id="test-session",
        artifacts_path="/tmp",
        metadata={"special": special_chars}
    )
    
    # Verify data was stored correctly
    events = await test_database.get_recent_events(1)
    assert len(events) == 1
    assert events[0].project_path == special_chars
    assert events[0].metadata["special"] == special_chars


@pytest.mark.asyncio
async def test_event_lifecycle(test_database):
    """Test complete event lifecycle."""
    # Start event
    event_id = await test_database.start_event(
        command="test-command",
        project_path="/test/project",
        session_id="test-session-123",
        artifacts_path="/test/artifacts",
        metadata={"test": "data"}
    )
    
    assert event_id is not None
    
    # End event
    await test_database.end_event(
        event_id=event_id,
        status="completed",
        exit_code=0
    )
    
    # Verify event data
    events = await test_database.get_recent_events(1)
    assert len(events) == 1
    
    event = events[0]
    assert event.id == event_id
    assert event.command == "test-command"
    assert event.status == "completed"
    assert event.exit_code == 0
    assert event.metadata["test"] == "data"


@pytest.mark.asyncio
async def test_artifact_storage(test_database):
    """Test artifact storage with parameter binding."""
    # Create an event first
    event_id = await test_database.start_event(
        command="test",
        project_path="/test",
        session_id="test",
        artifacts_path="/test"
    )
    
    # Store artifact with potential injection
    malicious_path = "'; DROP TABLE artifacts; --"
    await test_database.store_artifact(
        event_id=event_id,
        artifact_type="test",
        file_path=malicious_path,
        file_size=1024
    )
    
    # Verify table still exists and data is correct
    async with test_database.connection() as conn:
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='artifacts'"
        )
        assert await cursor.fetchone() is not None
        
        cursor = await conn.execute(
            "SELECT file_path FROM artifacts WHERE event_id = ?", (event_id,)
        )
        result = await cursor.fetchone()
        assert result[0] == malicious_path


@pytest.mark.asyncio
async def test_json_metadata_handling(test_database):
    """Test safe JSON metadata handling."""
    # Test with complex metadata
    metadata = {
        "nested": {"data": "value"},
        "array": [1, 2, 3],
        "special_chars": "'; DROP TABLE events; --",
        "unicode": "🧃 PruneJuice",
        "null_value": None,
        "boolean": True
    }
    
    event_id = await test_database.start_event(
        command="test",
        project_path="/test",
        session_id="test",
        artifacts_path="/test",
        metadata=metadata
    )
    
    # Retrieve and verify
    events = await test_database.get_recent_events(1)
    assert len(events) == 1
    
    retrieved_metadata = events[0].metadata
    assert retrieved_metadata["nested"]["data"] == "value"
    assert retrieved_metadata["array"] == [1, 2, 3]
    assert retrieved_metadata["special_chars"] == "'; DROP TABLE events; --"
    assert retrieved_metadata["unicode"] == "🧃 PruneJuice"
    assert retrieved_metadata["boolean"] is True


@pytest.mark.asyncio
async def test_concurrent_operations(test_database):
    """Test database safety under concurrent operations."""
    import asyncio
    
    async def create_event(i):
        return await test_database.start_event(
            command=f"command-{i}",
            project_path=f"/project-{i}",
            session_id=f"session-{i}",
            artifacts_path=f"/artifacts-{i}"
        )
    
    # Create multiple events concurrently
    tasks = [create_event(i) for i in range(10)]
    event_ids = await asyncio.gather(*tasks)
    
    # Verify all events were created
    assert len(set(event_ids)) == 10  # All IDs should be unique
    
    events = await test_database.get_recent_events(20)
    assert len(events) >= 10