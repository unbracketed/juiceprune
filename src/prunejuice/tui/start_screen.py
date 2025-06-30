"""Screen for starting new worktree sessions."""

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Middle, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static
from textual.validation import ValidationResult, Validator


class WorktreeNameValidator(Validator):
    """Validator for worktree names."""
    
    def validate(self, value: str) -> ValidationResult:
        """Validate the worktree name."""
        if not value:
            return self.failure("Name is required")
        
        if not value.replace("-", "").replace("_", "").isalnum():
            return self.failure("Name must contain only letters, numbers, hyphens, and underscores")
        
        if value.startswith("-") or value.endswith("-"):
            return self.failure("Name cannot start or end with a hyphen")
        
        return self.success()


class BranchNameValidator(Validator):
    """Validator for branch names."""
    
    def validate(self, value: str) -> ValidationResult:
        """Validate the branch name."""
        # Branch name is optional
        if not value:
            return self.success()
        
        # Basic git branch name validation
        if value.startswith("-") or value.endswith("-"):
            return self.failure("Branch name cannot start or end with a hyphen")
        
        if ".." in value or value.startswith(".") or value.endswith("."):
            return self.failure("Invalid branch name format")
        
        return self.success()


class StartWorkTreeScreen(ModalScreen[Optional[dict]]):
    """Modal screen for collecting new worktree information."""
    
    CSS = """
    StartWorkTreeScreen {
        align: center middle;
    }
    
    #dialog {
        width: 60;
        height: 80%;
        border: thick $background 80%;
        background: $surface;
        padding: 1;
    }
    
    #dialog-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .input-group {
        margin-bottom: 1;
    }
    
    .input-label {
        margin-bottom: 1;
    }
    
    #button-container {
        margin-top: 1;
        width: 100%;
        text-align: center;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+c", "cancel", "Cancel"),
    ]
    
    def compose(self) -> ComposeResult:
        """Compose the start worktree screen."""
        yield Center(
            Middle(
                Vertical(
                    Static("Start New Worktree", id="dialog-title"),
                    
                    Vertical(
                        Label("Worktree name:", classes="input-label"),
                        Input(
                            placeholder="e.g., feature-xyz, bug-123",
                            validators=[WorktreeNameValidator()],
                            id="name-input"
                        ),
                        classes="input-group"
                    ),
                    
                    Vertical(
                        Label("Base branch (optional, defaults to 'main'):", classes="input-label"),
                        Input(
                            placeholder="main, develop, master, etc.",
                            validators=[BranchNameValidator()],
                            id="branch-input"
                        ),
                        classes="input-group"
                    ),
                    
                    Vertical(
                        Button("Create & Connect", variant="primary", id="create-btn"),
                        Button("Cancel", variant="default", id="cancel-btn"),
                        id="button-container"
                    ),
                    
                    id="dialog"
                )
            )
        )
    
    def on_mount(self) -> None:
        """Focus the name input when the screen is mounted."""
        self.query_one("#name-input", Input).focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "create-btn":
            self.action_submit()
        elif event.button.id == "cancel-btn":
            self.action_cancel()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if event.input.id == "name-input":
            # Move focus to branch input
            self.query_one("#branch-input", Input).focus()
        elif event.input.id == "branch-input":
            # Submit the form
            self.action_submit()
    
    def action_submit(self) -> None:
        """Submit the form with validation."""
        name_input = self.query_one("#name-input", Input)
        branch_input = self.query_one("#branch-input", Input)
        
        # Validate name
        if not name_input.is_valid:
            name_input.focus()
            return
        
        name = name_input.value.strip()
        if not name:
            name_input.focus()
            return
        
        # Validate branch (if provided)
        if not branch_input.is_valid:
            branch_input.focus()
            return
        
        branch = branch_input.value.strip() or "main"
        
        # Return the collected data
        self.dismiss({
            "name": name,
            "base_branch": branch
        })
    
    def action_cancel(self) -> None:
        """Cancel the dialog."""
        self.dismiss(None)