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

from prunejuice.worktree_utils import GitWorktreeManager, WorktreeOperations
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
        Binding("enter", "connect", "Connect", priority=True),
        Binding("s", "start", "Start new worktree", priority=True),
        Binding("c", "commit", "Commit changes", priority=True),
        Binding("m", "merge", "Merge to parent", priority=True),
        Binding("p", "pull_request", "Create PR", priority=True),
        Binding("d", "delete", "Delete worktree", priority=True),
        Binding("r", "refresh", "Refresh", priority=True),
        Binding("q", "quit", "Quit", priority=True),
    ]

    def __init__(self, project_path: Path | None = None):
        """Initialize the app with project path."""
        super().__init__()
        self.project_path = project_path or Path.cwd()
        self.git_manager = GitWorktreeManager(self.project_path)
        self.session_manager = SessionLifecycleManager()
        self.worktree_ops = WorktreeOperations(self.project_path)
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
                Static("Welcome to PruneJuice TUI!\n\nSelect a worktree to see details and available actions.\n\nKey Bindings:\n  [s] Start new worktree\n  [c] Commit changes\n  [m] Merge to parent\n  [p] Create pull request\n  [d] Delete worktree\n  [r] Refresh list\n  [q] Quit", id="main-content"),
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

    def _get_git_status(self, worktree_path: str) -> str:
        """Get git status for a worktree."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", "--branch"],
                cwd=worktree_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                if not output:
                    return "Working tree clean"
                return output
            else:
                return f"Git status error: {result.stderr.strip()}"
        except Exception as e:
            return f"Error getting git status: {str(e)}"

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
        # project_name = self.project_path.name  # Currently unused

        for i, worktree in enumerate(worktrees):
            branch = worktree.get("branch", "detached")
            # path = worktree.get("path", "")  # Currently unused

            # Clean up branch name (remove refs/heads/ prefix)
            if branch.startswith("refs/heads/"):
                clean_branch = branch[11:]  # Remove 'refs/heads/' prefix
            else:
                clean_branch = branch

            # Use the clean branch name as display name
            display_name = clean_branch

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
                    
                    # Get git status for this worktree
                    git_status = self._get_git_status(path)
                    
                    # Update main content with worktree details and git status
                    main_content = self.query_one("#main-content", Static)
                    content = f"Branch: {branch}\nPath: {path}\n\nGit Status:\n{git_status}\n\n"
                    content += "Available Actions:\n"
                    content += "  [c] Commit changes\n"
                    content += "  [m] Merge to parent branch\n"
                    content += "  [p] Create pull request\n"
                    content += "  [d] Delete worktree\n"
                    content += "  [Enter] Connect to tmux session\n"
                    main_content.update(content)
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

    def action_commit(self) -> None:
        """Commit changes in the selected worktree."""
        if self.highlighted_index >= 0 and self.highlighted_index < len(self.worktrees):
            worktree = self.worktrees[self.highlighted_index]
            worktree_path = worktree.get("path", "")
            
            if worktree_path:
                # Update main content to show status
                main_content = self.query_one("#main-content", Static)
                main_content.update(f"Opening commit interface for: {worktree_path}\n\nNote: Full interactive commit UI coming soon!\nFor now, use: prj worktree commit {worktree_path}")
                
                # TODO: Implement full interactive commit dialog
                # For now, just show the command the user can run
            else:
                main_content = self.query_one("#main-content", Static)
                main_content.update("Invalid worktree selection")
        else:
            main_content = self.query_one("#main-content", Static)
            main_content.update("Please select a worktree first")

    def action_merge(self) -> None:
        """Merge the selected worktree to its parent branch."""
        if self.highlighted_index >= 0 and self.highlighted_index < len(self.worktrees):
            worktree = self.worktrees[self.highlighted_index]
            worktree_path = worktree.get("path", "")
            branch = worktree.get("branch", "unknown")
            
            if worktree_path:
                main_content = self.query_one("#main-content", Static)
                main_content.update(f"Merge operation for branch '{branch}'\n\nRun: prj worktree merge {worktree_path}")
                
                # TODO: Add confirmation dialog and execute merge
            else:
                main_content = self.query_one("#main-content", Static)
                main_content.update("Invalid worktree selection")
        else:
            main_content = self.query_one("#main-content", Static)
            main_content.update("Please select a worktree first")

    def action_pull_request(self) -> None:
        """Create a pull request for the selected worktree."""
        if self.highlighted_index >= 0 and self.highlighted_index < len(self.worktrees):
            worktree = self.worktrees[self.highlighted_index]
            worktree_path = worktree.get("path", "")
            branch = worktree.get("branch", "unknown")
            
            if worktree_path:
                main_content = self.query_one("#main-content", Static)
                main_content.update(f"Create PR for branch '{branch}'\n\nRun: prj worktree pull-request {worktree_path}")
                
                # TODO: Add PR creation dialog
            else:
                main_content = self.query_one("#main-content", Static)
                main_content.update("Invalid worktree selection")
        else:
            main_content = self.query_one("#main-content", Static)
            main_content.update("Please select a worktree first")

    def action_delete(self) -> None:
        """Delete the selected worktree."""
        if self.highlighted_index >= 0 and self.highlighted_index < len(self.worktrees):
            worktree = self.worktrees[self.highlighted_index]
            worktree_path = worktree.get("path", "")
            branch = worktree.get("branch", "unknown")
            
            if worktree_path:
                main_content = self.query_one("#main-content", Static)
                main_content.update(f"Delete worktree '{branch}'?\n\nRun: prj worktree delete {worktree_path}")
                
                # TODO: Add confirmation dialog and execute delete
            else:
                main_content = self.query_one("#main-content", Static)
                main_content.update("Invalid worktree selection")
        else:
            main_content = self.query_one("#main-content", Static)
            main_content.update("Please select a worktree first")

    def action_refresh(self) -> None:
        """Refresh the worktree list."""
        self.load_worktrees()
        main_content = self.query_one("#main-content", Static)
        main_content.update("Worktree list refreshed")
