"""Main TUI application for prunejuice."""

from pathlib import Path
from typing import List, Dict, Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, ListView, ListItem, Label
from textual.containers import Container
from textual import work

from prunejuice.worktree_utils import GitWorktreeManager


class PrunejuiceApp(App):
    """Main TUI application for prunejuice."""

    CSS = """
    Screen {
        background: $surface;
    }

    ListView {
        height: 100%;
        border: solid $primary;
    }

    ListItem {
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
    ]

    def __init__(self, project_path: Path | None = None):
        """Initialize the app with project path."""
        super().__init__()
        self.project_path = project_path or Path.cwd()
        self.git_manager = GitWorktreeManager(self.project_path)

    def compose(self) -> ComposeResult:
        """Create application layout."""
        yield Header()
        yield Container(
            ListView(
                ListItem(Label("Loading worktrees...")),
                id="worktree-list",
            ),
        )
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app when mounted."""
        self.title = "Prunejuice TUI"
        self.sub_title = "Worktree Management"
        # Start loading worktrees
        self.load_worktrees()

    @work(exclusive=True)
    async def load_worktrees(self) -> None:
        """Load worktrees in the background."""
        try:
            worktrees = await self.fetch_worktrees()
            self.app.call_later(self.update_worktree_list, worktrees)
        except Exception as e:
            # Handle errors gracefully
            self.app.call_later(self.update_worktree_list, [])

    async def fetch_worktrees(self) -> List[Dict[str, Any]]:
        """Fetch worktrees from git."""
        return self.git_manager.list_worktrees()

    def update_worktree_list(self, worktrees: List[Dict[str, Any]]) -> None:
        """Update the worktree list view."""
        list_view = self.query_one("#worktree-list", ListView)
        list_view.clear()

        if not worktrees:
            list_view.append(ListItem(Label("No worktrees found")))
            return

        for worktree in worktrees:
            branch = worktree.get("branch", "detached")
            path = worktree.get("path", "")

            # Create a formatted label for each worktree
            if branch == "detached":
                branch_label = f"[red]detached[/red] ({worktree.get('commit', '')[:8]})"
            else:
                branch_label = f"[bold cyan]{branch}[/bold cyan]"

            label_text = f"{branch_label} - [dim]{path}[/dim]"
            list_view.append(ListItem(Label(label_text, markup=True)))
