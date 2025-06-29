"""Tests for artifact storage and file operations."""

import pytest

from prunejuice.utils.artifacts import ArtifactStore


class TestArtifactStore:
    """Test artifact storage with focus on file safety."""
    
    @pytest.fixture
    def store(self, temp_dir):
        return ArtifactStore(temp_dir / "artifacts")
    
    def test_safe_file_storage(self, store, temp_dir):
        """Test safe file storage operations."""
        project_path = temp_dir / "project"
        project_path.mkdir()
        
        # Create session directory
        session_dir = store.create_session_dir(
            project_path,
            "test-session",
            "test-command"
        )
        
        # Verify structure
        assert session_dir.exists()
        assert (session_dir / "logs").exists()
        assert (session_dir / "outputs").exists()
        
        # Test file storage
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        stored = store.store_file(session_dir, test_file, "output")
        assert stored.exists()
        assert stored.read_text() == "test content"
    
    def test_path_validation(self, store, temp_dir):
        """Test path traversal prevention."""
        session_dir = temp_dir / "session"
        session_dir.mkdir()
        
        # Attempt path traversal
        with pytest.raises((ValueError, OSError)):
            store.store_content(
                session_dir,
                "evil content",
                "../../../etc/passwd",
                "output"
            )
    
    def test_cleanup_operations(self, store, temp_dir):
        """Test safe cleanup of old artifacts."""
        # Create old sessions
        for i in range(3):
            session_dir = store.create_session_dir(
                temp_dir,
                f"session-{i}",
                "test"
            )
            (session_dir / "test.txt").write_text("data")
        
        # Cleanup should work safely
        initial_count = len(list(store.base_dir.glob("**/session-*")))
        store.cleanup_old_sessions(days=0)  # Clean all
        
        # Verify cleanup
        remaining = list(store.base_dir.glob("**/session-*"))
        assert len(remaining) < initial_count