"""Utilities for displaying git diff output with rich formatting."""

from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()


def format_diff_line(line: str) -> Text:
    """Format a single diff line with appropriate styling.
    
    Args:
        line: A line from git diff output
        
    Returns:
        Rich Text object with styling
    """
    text = Text()
    
    if line.startswith('+++') or line.startswith('---'):
        # File headers
        text.append(line, style="bold blue")
    elif line.startswith('@@'):
        # Hunk headers
        text.append(line, style="bold cyan")
    elif line.startswith('+'):
        # Added lines
        text.append(line, style="green")
    elif line.startswith('-'):
        # Removed lines
        text.append(line, style="red")
    elif line.startswith('diff --git'):
        # Git diff headers
        text.append(line, style="bold yellow")
    elif line.startswith('index '):
        # Index lines
        text.append(line, style="dim")
    else:
        # Context lines
        text.append(line, style="white")
    
    return text


def format_diff_output(diff_text: str, max_lines: int = 1000) -> Text:
    """Format git diff with rich styling and syntax highlighting.
    
    Args:
        diff_text: Raw git diff output
        max_lines: Maximum number of lines to process
        
    Returns:
        Rich Text object with formatted diff
    """
    if not diff_text.strip():
        return Text("No differences found.", style="dim")
    
    formatted_text = Text()
    lines = diff_text.splitlines()
    
    # Truncate if too many lines
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        truncated = True
    else:
        truncated = False
    
    for line in lines:
        formatted_line = format_diff_line(line)
        formatted_text.append(formatted_line)
        formatted_text.append("\n")
    
    if truncated:
        formatted_text.append(
            f"\n... (truncated after {max_lines} lines)\n", 
            style="bold yellow"
        )
    
    return formatted_text


def display_diff_summary(summary: Dict[str, Any]) -> None:
    """Display diff statistics in formatted table.
    
    Args:
        summary: Dictionary with diff statistics
    """
    if not summary.get("has_changes", False):
        console.print("No changes found.", style="dim")
        return
    
    # Create summary table
    table = Table(title="Diff Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Files changed", str(summary.get("files_changed", 0)))
    table.add_row("Insertions", f"+{summary.get('insertions', 0)}")
    table.add_row("Deletions", f"-{summary.get('deletions', 0)}")
    
    if summary.get("base_branch"):
        table.add_row("Base branch", summary["base_branch"])
    
    if summary.get("current_branch"):
        table.add_row("Current branch", summary["current_branch"])
    
    console.print(table)


def display_worktree_status(status: Dict[str, Any]) -> None:
    """Display worktree status information.
    
    Args:
        status: Dictionary with worktree status
    """
    if status.get("is_clean", True):
        console.print("Working directory is clean.", style="green")
        return
    
    # Create status table
    table = Table(title="Worktree Status")
    table.add_column("Type", style="cyan")
    table.add_column("Files", style="yellow")
    
    staged_files = status.get("staged_files", [])
    unstaged_files = status.get("unstaged_files", [])
    untracked_files = status.get("untracked_files", [])
    
    if staged_files:
        staged_list = ", ".join([f"{f['file']} ({f['status']})" for f in staged_files])
        table.add_row("Staged", staged_list)
    
    if unstaged_files:
        unstaged_list = ", ".join([f"{f['file']} ({f['status']})" for f in unstaged_files])
        table.add_row("Unstaged", unstaged_list)
    
    if untracked_files:
        untracked_list = ", ".join(untracked_files)
        table.add_row("Untracked", untracked_list)
    
    console.print(table)


def display_diff_with_pager(diff_text: str, title: str = "Git Diff") -> None:
    """Display large diff output using rich pager.
    
    Args:
        diff_text: Raw git diff output
        title: Title for the diff display
    """
    if not diff_text.strip():
        console.print("No differences found.", style="dim")
        return
    
    # Format the diff
    formatted_diff = format_diff_output(diff_text, max_lines=10000)
    
    # Create a panel with the formatted diff
    panel = Panel(
        formatted_diff,
        title=title,
        border_style="blue",
        expand=False
    )
    
    # Use pager for large content
    lines = diff_text.count('\n')
    if lines > 50:  # Use pager for more than 50 lines
        with console.pager():
            console.print(panel)
    else:
        console.print(panel)


def get_diff_type_menu() -> str:
    """Display diff type selection menu and get user choice.
    
    Returns:
        Selected diff type as string
    """
    console.print("\nDiff options:", style="bold")
    console.print("  1. Compare against main branch")
    console.print("  2. Compare against origin/main")
    console.print("  3. Show staged changes only")
    console.print("  4. Show unstaged changes only")
    console.print("  5. Show working directory status")
    
    return console.input("\nChoose diff type (1-5): ")


def display_diff_error(error_msg: str) -> None:
    """Display diff error message with styling.
    
    Args:
        error_msg: Error message to display
    """
    panel = Panel(
        Text(error_msg, style="red"),
        title="Diff Error",
        border_style="red"
    )
    console.print(panel)