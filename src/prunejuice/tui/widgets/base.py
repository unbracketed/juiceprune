"""Base widget patterns for PruneJuice custom widgets."""

from textual.widget import Widget
from textual.reactive import reactive
from typing import Any


class BaseReactiveWidget(Widget):
    """Base class for reactive widgets with common patterns."""
    
    # Common reactive properties that subclasses can use
    data: reactive[Any] = reactive(None, recompose=True)
    
    def __init__(self, **kwargs) -> None:
        """Initialize the base reactive widget."""
        super().__init__(**kwargs)
    
    def set_data(self, data: Any) -> None:
        """Set reactive data, triggering recomposition."""
        self.data = data
    
    def render_error(self, message: str) -> str:
        """Render an error message with consistent styling."""
        return f"[bold red]Error:[/] [red]{message}[/]"
    
    def render_info(self, message: str) -> str:
        """Render an info message with consistent styling."""
        return f"[dim cyan]{message}[/]"
    
    def render_success(self, message: str) -> str:
        """Render a success message with consistent styling."""
        return f"[green]{message}[/]"