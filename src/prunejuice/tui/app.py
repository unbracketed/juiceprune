"""Main TUI application for prunejuice."""

from pathlib import Path
from typing import List, Dict, Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, ListView, ListItem, Label, Static
from textual.containers import Horizontal, Vertical
from textual import work

from prunejuice.worktree_utils import GitWorktreeManager


class PrunejuiceApp(App):
    """Main TUI application for prunejuice."""

    CSS = """
    Screen {
        background: $surface;
    }

    #sidebar {
        width: 30%;
        border: solid $primary;
    }

    #main-content {
        width: 70%;
        border: solid $secondary;
        padding: 1;
    }

    ListView {
        height: 100%;
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
        self.worktrees = []  # Store worktree data for reference

    def compose(self) -> ComposeResult:
        """Create application layout."""
        yield Header()
        yield Horizontal(
            Vertical(
                ListView(
                    ListItem(Label("Loading worktrees...")),
                    id="worktree-list",
                ),
                id="sidebar",
            ),
            Vertical(
                Static("It helps the PM go smoother", id="main-content"),
            ),
        )
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app when mounted."""
        self.title = "PruneJuice TUI"
        # Start loading worktrees
        self.load_worktrees()

    @work(exclusive=True)
    async def load_worktrees(self) -> None:
        """Load worktrees in the background."""
        try:
            worktrees = await self.fetch_worktrees()
            self.app.call_later(self.update_worktree_list, worktrees)
        except Exception:
            # Handle errors gracefully
            self.app.call_later(self.update_worktree_list, [])

    async def fetch_worktrees(self) -> List[Dict[str, Any]]:
        """Fetch worktrees from git."""
        return self.git_manager.list_worktrees()

    def update_worktree_list(self, worktrees: List[Dict[str, Any]]) -> None:
        """Update the worktree list view."""
        self.worktrees = worktrees  # Store for later reference
        list_view = self.query_one("#worktree-list", ListView)
        list_view.clear()

        if not worktrees:
            list_view.append(ListItem(Label("No worktrees found")))
            return

        # Get project name for prefix removal
        project_name = self.project_path.name

        for i, worktree in enumerate(worktrees):
            branch = worktree.get("branch", "detached")
            path = worktree.get("path", "")

            # Extract and clean up worktree name
            if path:
                worktree_name = Path(path).name
                # Remove project prefix if present (e.g., "juiceprune-feature" -> "feature")
                if worktree_name.startswith(f"{project_name}-"):
                    display_name = worktree_name[len(project_name) + 1:]
                elif worktree_name != branch:
                    display_name = worktree_name
                else:
                    display_name = branch
            else:
                display_name = branch

            # Create list item with index for tracking
            item = ListItem(Label(display_name), id=f"worktree-{i}")
            list_view.append(item)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Handle when a list item is highlighted."""
        if event.list_view.id == "worktree-list" and event.item and event.item.id:
            # Extract index from item id
            try:
                index = int(event.item.id.split("-")[1])
                if 0 <= index < len(self.worktrees):
                    worktree = self.worktrees[index]
                    path = worktree.get("path", "No path available")
                    branch = worktree.get("branch", "unknown")
                    
                    # Update main content with worktree details
                    main_content = self.query_one("#main-content", Static)
                    main_content.update(f"Branch: {branch}\nPath: {path}")
            except (ValueError, IndexError):
                # Handle any parsing errors gracefully
                pass
