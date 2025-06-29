"""Integration with tmux session management - Native Python implementation."""

from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from ..session_utils import TmuxManager, SessionLifecycleManager

logger = logging.getLogger(__name__)


class PotsIntegration:
    """Integration with tmux session management using native Python implementation."""
    
    def __init__(self, pots_path: Optional[Path] = None):
        """Initialize session integration.
        
        Args:
            pots_path: Legacy parameter for compatibility (ignored)
        """
        # Use native implementations instead of shell scripts
        self.tmux_manager = TmuxManager()
        self.session_manager = SessionLifecycleManager(self.tmux_manager)
    
    def create_session(
        self,
        working_dir: Path,
        task_name: str
    ) -> str:
        """Create a new tmux session using native Python implementation."""
        try:
            # Use native session lifecycle manager
            session_name = self.session_manager.create_session_for_worktree(
                working_dir,
                task_name,
                auto_attach=False
            )
            
            if session_name:
                logger.info(f"Created session with native Python: {session_name}")
                return session_name
            else:
                # Fallback session name if creation failed
                fallback_name = f"prunejuice-{task_name}"
                logger.warning(f"Session creation failed, returning fallback name: {fallback_name}")
                return fallback_name
                
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            # Don't fail the whole operation if tmux isn't available
            return f"prunejuice-{task_name}"
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all tmux sessions using native Python implementation."""
        try:
            sessions = self.tmux_manager.list_sessions()
            
            logger.debug(f"Listed {len(sessions)} sessions using native Python")
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []
    
    def attach_session(self, session_name: str) -> bool:
        """Attach to an existing session using native Python implementation."""
        try:
            success = self.session_manager.attach_to_session(session_name)
            
            if success:
                logger.info(f"Attached to session with native Python: {session_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to attach to session: {e}")
            return False
    
    def kill_session(self, session_name: str) -> bool:
        """Kill a session using native Python implementation."""
        try:
            success = self.session_manager.kill_session(session_name)
            
            if success:
                logger.info(f"Killed session with native Python: {session_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to kill session: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if session functionality is available."""
        # Check if tmux is available on the system
        import asyncio
        try:
            # Run the check in the current event loop if one exists
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, we can't await here
                # Return True and let the actual operations handle tmux availability
                return True
            else:
                return self.tmux_manager.check_tmux_available()
        except RuntimeError:
            # No event loop, create one
            return self.tmux_manager.check_tmux_available()