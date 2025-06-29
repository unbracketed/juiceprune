"""Artifact storage utilities."""

from pathlib import Path
from typing import Optional
import shutil
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ArtifactStore:
    """Manages artifact storage and organization."""
    
    def __init__(self, base_dir: Path):
        """Initialize artifact store."""
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def create_session_dir(
        self,
        project_path: Path,
        session_id: str,
        command_name: str
    ) -> Path:
        """Create a session-specific artifact directory."""
        # Create directory structure: base/project_name/session_id/
        project_name = project_path.name
        session_dir = self.base_dir / project_name / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (session_dir / "logs").mkdir(exist_ok=True)
        (session_dir / "outputs").mkdir(exist_ok=True)
        (session_dir / "prompts").mkdir(exist_ok=True)
        (session_dir / "specs").mkdir(exist_ok=True)
        
        # Create session metadata
        metadata_file = session_dir / "session.info"
        metadata_file.write_text(f"""Session: {session_id}
Command: {command_name}
Project: {project_path}
Created: {datetime.now(timezone.utc).isoformat()}
""")
        
        logger.info(f"Created artifact directory: {session_dir}")
        return session_dir
    
    def store_file(
        self,
        session_dir: Path,
        file_path: Path,
        artifact_type: str = "output"
    ) -> Path:
        """Store a file in the appropriate artifact subdirectory."""
        target_dir = session_dir / artifact_type
        target_dir.mkdir(exist_ok=True)
        
        target_path = target_dir / file_path.name
        shutil.copy2(file_path, target_path)
        
        logger.info(f"Stored artifact: {target_path}")
        return target_path
    
    def store_content(
        self,
        session_dir: Path,
        content: str,
        filename: str,
        artifact_type: str = "output"
    ) -> Path:
        """Store text content as an artifact file."""
        target_dir = session_dir / artifact_type
        target_dir.mkdir(exist_ok=True)
        
        target_path = target_dir / filename
        target_path.write_text(content)
        
        logger.info(f"Stored content artifact: {target_path}")
        return target_path
    
    def get_session_artifacts(self, session_dir: Path) -> dict:
        """Get list of all artifacts in a session directory."""
        artifacts = {}
        
        for subdir in session_dir.iterdir():
            if subdir.is_dir() and subdir.name in ["logs", "outputs", "prompts", "specs"]:
                artifacts[subdir.name] = list(subdir.glob("*"))
        
        return artifacts
    
    def cleanup_old_sessions(self, days: int = 30):
        """Clean up session directories older than specified days."""
        cutoff = datetime.now(timezone.utc).timestamp() - (days * 24 * 60 * 60)
        
        for project_dir in self.base_dir.iterdir():
            if not project_dir.is_dir():
                continue
            
            for session_dir in project_dir.iterdir():
                if not session_dir.is_dir():
                    continue
                
                if session_dir.stat().st_mtime < cutoff:
                    try:
                        shutil.rmtree(session_dir)
                        logger.info(f"Cleaned up old session: {session_dir}")
                    except Exception as e:
                        logger.error(f"Failed to cleanup {session_dir}: {e}")