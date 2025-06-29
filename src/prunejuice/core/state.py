"""State management for command execution."""

from typing import Dict, Any, Optional
import logging
import json
from datetime import datetime, timezone

from .database import Database
from .models import StepStatus

logger = logging.getLogger(__name__)


class StateManager:
    """Manages execution state across steps."""
    
    def __init__(self, db: Database):
        """Initialize state manager."""
        self.db = db
        self._step_states: Dict[str, Dict[str, Any]] = {}
    
    async def begin_step(self, session_id: str, step_name: str):
        """Mark step as started."""
        if session_id not in self._step_states:
            self._step_states[session_id] = {}
        
        self._step_states[session_id][step_name] = {
            'status': StepStatus.RUNNING,
            'start_time': datetime.now(timezone.utc),
            'output': []
        }
        
        logger.info(f"Started step '{step_name}' in session {session_id}")
    
    async def complete_step(self, session_id: str, step_name: str, output: Optional[str] = None):
        """Mark step as completed."""
        if session_id in self._step_states and step_name in self._step_states[session_id]:
            self._step_states[session_id][step_name].update({
                'status': StepStatus.COMPLETED,
                'end_time': datetime.now(timezone.utc),
                'output': output or ""
            })
        
        logger.info(f"Completed step '{step_name}' in session {session_id}")
    
    async def fail_step(self, session_id: str, step_name: str, error: str):
        """Mark step as failed."""
        if session_id in self._step_states and step_name in self._step_states[session_id]:
            self._step_states[session_id][step_name].update({
                'status': StepStatus.FAILED,
                'end_time': datetime.now(timezone.utc),
                'error': error
            })
        
        logger.error(f"Failed step '{step_name}' in session {session_id}: {error}")
    
    async def skip_step(self, session_id: str, step_name: str, reason: str):
        """Mark step as skipped."""
        if session_id not in self._step_states:
            self._step_states[session_id] = {}
        
        self._step_states[session_id][step_name] = {
            'status': StepStatus.SKIPPED,
            'reason': reason,
            'timestamp': datetime.now(timezone.utc)
        }
        
        logger.info(f"Skipped step '{step_name}' in session {session_id}: {reason}")
    
    def get_step_status(self, session_id: str, step_name: str) -> Optional[StepStatus]:
        """Get status of a specific step."""
        if session_id in self._step_states and step_name in self._step_states[session_id]:
            return self._step_states[session_id][step_name].get('status')
        return None
    
    def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get complete state for a session."""
        return self._step_states.get(session_id, {})
    
    async def cleanup_session(self, session_id: str):
        """Clean up session state."""
        if session_id in self._step_states:
            del self._step_states[session_id]
        
        logger.info(f"Cleaned up session state for {session_id}")