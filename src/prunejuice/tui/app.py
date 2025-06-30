"""Main TUI application for prunejuice."""

from pathlib import Path
from typing import List, Dict, Any
import os
import subprocess

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, ListView, ListItem, Label, Static
from textual.containers import Horizontal, Vertical
from textual import work

from prunejuice.worktree_utils import GitWorktreeManager
from prunejuice.session_utils import SessionLifecycleManager
from .start_screen import StartWorkTreeScreen


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
        Binding("c", "connect", "Connect", priority=True),
        Binding("s", "start", "Start", priority=True),
        Binding("q", "quit", "Quit", priority=True),
    ]

    def __init__(self, project_path: Path | None = None):
        """Initialize the app with project path."""
        super().__init__()
        self.project_path = project_path or Path.cwd()
        self.git_manager = GitWorktreeManager(self.project_path)
        self.session_manager = SessionLifecycleManager()
        self.worktrees: List[Dict[str, Any]] = []  # Store worktree data for reference
        self.highlighted_index = -1  # Track currently highlighted worktree
        self.is_in_tmux = os.getenv("TMUX") is not None
        self.current_tmux_session = self._get_current_tmux_session() if self.is_in_tmux else None

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

    def _get_current_tmux_session(self) -> str | None:
        """Get the name of the current tmux session."""
        try:
            result = subprocess.run(
                ["tmux", "display-message", "-p", "#S"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.decode().strip()
        except Exception:
            pass
        return None

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
                    self.highlighted_index = index  # Store highlighted index
                    worktree = self.worktrees[index]
                    path = worktree.get("path", "No path available")
                    branch = worktree.get("branch", "unknown")
                    
                    # Update main content with worktree details
                    main_content = self.query_one("#main-content", Static)
                    main_content.update(f"Branch: {branch}\nPath: {path}\n\nPress 'c' to connect to tmux session")
            except (ValueError, IndexError):
                # Handle any parsing errors gracefully
                pass

    def action_connect(self) -> None:
        """Connect to the highlighted worktree's tmux session."""
        if self.highlighted_index >= 0 and self.highlighted_index < len(self.worktrees):
            worktree = self.worktrees[self.highlighted_index]
            worktree_path = worktree.get("path")
            branch = worktree.get("branch", "unknown")
            
            if worktree_path:
                try:
                    if self.is_in_tmux and self.current_tmux_session:
                        # We're in tmux, use switch-client for better UX
                        session_name = self.session_manager.create_session_for_worktree_with_tui_return(
                            Path(worktree_path),
                            self.current_tmux_session,
                            branch
                        )
                        
                        if session_name:
                            # Switch to the worktree session
                            success = self.session_manager.switch_to_session(session_name)
                            if not success:
                                main_content = self.query_one("#main-content", Static)
                                main_content.update("Failed to switch to tmux session")
                        else:
                            main_content = self.query_one("#main-content", Static)
                            main_content.update("Failed to create tmux session")
                    else:
                        # Not in tmux, use the old approach
                        session_name = self.session_manager.create_session_for_worktree(
                            Path(worktree_path), 
                            branch,
                            auto_attach=False
                        )
                        
                        if session_name:
                            # Exit the TUI app cleanly first
                            self.exit()
                            # Use os.execvp to replace the current process with tmux attach
                            os.execvp("tmux", ["tmux", "attach-session", "-t", session_name])
                        else:
                            # Update main content to show error
                            main_content = self.query_one("#main-content", Static)
                            main_content.update("Failed to create tmux session")
                        
                except Exception as e:
                    # Update main content to show error
                    main_content = self.query_one("#main-content", Static)
                    main_content.update(f"Error connecting to session: {str(e)}")
        else:
            # Update main content to show message
            main_content = self.query_one("#main-content", Static)
            main_content.update("Please select a worktree first")

    def action_start(self) -> None:
        """Show the start worktree screen."""
        def handle_result(result):
            """Handle the result from the start worktree screen."""
            if result:  # User didn't cancel
                self.start_new_worktree(result["name"], result["base_branch"])
        
        self.push_screen(StartWorkTreeScreen(), handle_result)

    def start_new_worktree(self, name: str, base_branch: str) -> None:
        """Create a new worktree and start a tmux session."""
        main_content = self.query_one("#main-content", Static)
        
        try:
            # Update UI to show progress
            main_content.update(f"Creating worktree '{name}' from '{base_branch}'...")
            
            # Create worktree
            worktree_path = self.git_manager.create_worktree(name, base_branch)
            main_content.update(f"Worktree created at: {worktree_path}\n\nCreating tmux session...")
            
            # Create tmux session
            if self.is_in_tmux and self.current_tmux_session:
                # We're in tmux, use the TUI return approach
                session_name = self.session_manager.create_session_for_worktree_with_tui_return(
                    worktree_path,
                    self.current_tmux_session,
                    name
                )
                
                if session_name:
                    main_content.update(f"Session '{session_name}' created!\n\nSwitching to session...")
                    # Switch to the new session
                    success = self.session_manager.switch_to_session(session_name)
                    if not success:
                        main_content.update(f"Session created but failed to switch. Run: tmux attach -t {session_name}")
                else:
                    main_content.update("Failed to create tmux session")
            else:
                # Not in tmux, use the standard approach
                session_name = self.session_manager.create_session_for_worktree(
                    worktree_path, 
                    name,
                    auto_attach=False
                )
                
                if session_name:
                    main_content.update(f"Session '{session_name}' created!\n\nExiting TUI and attaching to session...")
                    # Exit the TUI app cleanly first
                    self.exit()
                    # Use os.execvp to replace the current process with tmux attach
                    os.execvp("tmux", ["tmux", "attach-session", "-t", session_name])
                else:
                    main_content.update("Failed to create tmux session")
            
            # Refresh the worktree list to include the new worktree
            self.load_worktrees()
            
        except Exception as e:
            main_content.update(f"Error creating worktree: {str(e)}")
            # Try to clean up the worktree if it was created but session failed
            try:
                self.git_manager.remove_worktree(Path(name))
                main_content.update(f"Error creating worktree: {str(e)}\n\nCleaned up partial worktree.")
            except Exception:
                # If cleanup also fails, just show the original error
                pass
