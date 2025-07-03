"""Worktree detail widget that composes git status and action widgets."""

from typing import Dict, Any
from textual.reactive import reactive
from textual.widgets import Label

from .base import BaseReactiveWidget
from .git_status import GitStatusWidget
from .actions import ActionListWidget


class WorktreeDetailWidget(BaseReactiveWidget):
    """Main container widget for worktree details, git status, and actions."""
    
    worktree_data: reactive[Dict[str, Any]] = reactive({}, recompose=True)
    git_status: reactive[str] = reactive("", recompose=True)
    
    def __init__(self, **kwargs) -> None:
        """Initialize the worktree detail widget."""
        super().__init__(**kwargs)
        
    def compose(self):
        """Compose the widget content with sub-widgets."""
        # Show welcome message if no worktree selected
        if not self.worktree_data:
            yield Label(self._get_welcome_message())
            return
        
        # Show simple message if this is a message display
        if "_message" in self.worktree_data:
            yield Label(self.worktree_data["_message"])
            return
        
        # Worktree info section
        yield Label(self._render_worktree_info())
        yield Label("")  # Spacing
        
        # Git status section
        yield Label("[bold bright_magenta]Git Status:[/]")
        yield GitStatusWidget(git_status=self.git_status)
        yield Label("")  # Spacing
        
        # Actions section
        yield ActionListWidget()
    
    def _render_worktree_info(self) -> str:
        """Render basic worktree information."""
        if not self.worktree_data:
            return self.render_info("No worktree selected")
        
        branch = self.worktree_data.get("branch", "unknown")
        path = self.worktree_data.get("path", "No path available")
        
        # Clean up branch name (remove refs/heads/ prefix)
        if branch.startswith("refs/heads/"):
            clean_branch = branch[11:]
        else:
            clean_branch = branch
        
        return (
            f"[bold bright_blue]Branch:[/] {clean_branch}\\n"
            f"[bold bright_blue]Path:[/] {path}"
        )
    
    def _get_welcome_message(self) -> str:
        """Get the welcome message when no worktree is selected."""
        return (
            "Welcome to PruneJuice TUI!\\n\\n"
            "Select a worktree to see details and available actions.\\n\\n"
            "Key Bindings:\\n"
            "  [s] Start new worktree\\n"
            "  [c] Commit changes\\n"
            "  [m] Merge to parent\\n"
            "  [p] Create pull request\\n"
            "  [d] Delete worktree\\n"
            "  [r] Refresh list\\n"
            "  [q] Quit"
        )
    
    def set_worktree_data(self, worktree_data: Dict[str, Any], git_status: str = "") -> None:
        """Update worktree data and git status, triggering recomposition."""
        self.worktree_data = worktree_data
        self.git_status = git_status
    
    def show_message(self, message: str) -> None:
        """Show a simple text message by clearing worktree data."""
        self.worktree_data = {"_message": message}
        self.git_status = ""