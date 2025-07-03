"""Action list widget for displaying available worktree actions."""

from typing import List, Dict
from textual.reactive import reactive

from .base import BaseReactiveWidget


class ActionListWidget(BaseReactiveWidget):
    """Widget to display formatted action lists based on worktree state."""
    
    actions: reactive[List[Dict[str, str]]] = reactive([], recompose=True)
    
    def __init__(self, actions: List[Dict[str, str]] | None = None, **kwargs) -> None:
        """Initialize the action list widget."""
        super().__init__(**kwargs)
        self.actions = actions or self._get_default_actions()
    
    def compose(self):
        """Compose the widget content."""
        from textual.widgets import Label
        
        yield Label("[bold bright_magenta]Available Actions:[/]")
        
        if not self.actions:
            yield Label(self.render_info("No actions available"))
            return
        
        for action in self.actions:
            key = action.get("key", "")
            description = action.get("description", "")
            rendered_action = self._render_action(key, description)
            yield Label(rendered_action)
    
    def _render_action(self, key: str, description: str) -> str:
        """Render an action with key highlighting."""
        if not key or not description:
            return self.render_info("Invalid action")
        
        return f"  [bold bright_white]\\[{key}][/] {description}"
    
    def set_actions(self, actions: List[Dict[str, str]]) -> None:
        """Update the action list and trigger recomposition."""
        self.actions = actions
    
    def _get_default_actions(self) -> List[Dict[str, str]]:
        """Get the default set of actions."""
        return [
            {"key": "c", "description": "Commit changes"},
            {"key": "m", "description": "Merge to parent branch"},
            {"key": "p", "description": "Create pull request"},
            {"key": "d", "description": "Delete worktree"},
            {"key": "Enter", "description": "Connect to tmux session"},
        ]