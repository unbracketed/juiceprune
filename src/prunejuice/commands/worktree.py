"""Worktree management commands for PruneJuice CLI."""

import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
from typing import Optional

from ..integrations.plum import PlumIntegration

console = Console()

# Create worktree subcommand app
worktree_app = typer.Typer(
    name="worktree",
    help="Manage git worktrees using plum integration",
    rich_markup_mode="rich"
)


@worktree_app.command()
def list(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed worktree info")
):
    """List all worktrees for the current project."""
    try:
        plum = PlumIntegration()
        
        if not plum.is_available():
            console.print("❌ Plum integration not available", style="bold red")
            console.print("Please ensure plum is installed and accessible", style="dim")
            raise typer.Exit(code=1)
        
        console.print("🌳 Listing worktrees...", style="bold green")
        
        worktrees = plum.list_worktrees(Path.cwd())
        
        if not worktrees:
            console.print("No worktrees found", style="yellow")
            return
        
        table = Table(title="Git Worktrees")
        table.add_column("Path", style="cyan", no_wrap=True)
        table.add_column("Branch", style="yellow")
        
        if verbose:
            table.add_column("Commit", style="blue")
        
        for worktree in worktrees:
            row = [worktree.get("path", "unknown"), worktree.get("branch", "unknown")]
            if verbose:
                row.append(worktree.get("commit", "unknown"))
            table.add_row(*row)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Error listing worktrees: {e}", style="bold red")
        raise typer.Exit(code=1)


@worktree_app.command()
def create(
    branch_name: str = typer.Argument(help="Branch name for the new worktree"),
    base_branch: Optional[str] = typer.Option(None, "--base", "-b", help="Base branch to create from")
):
    """Create a new worktree with the specified branch."""
    try:
        plum = PlumIntegration()
        
        if not plum.is_available():
            console.print("❌ Plum integration not available", style="bold red")
            console.print("Please ensure plum is installed and accessible", style="dim")
            raise typer.Exit(code=1)
        
        console.print(f"🌱 Creating worktree for branch: [bold cyan]{branch_name}[/bold cyan]")
        
        worktree_path = plum.create_worktree(Path.cwd(), branch_name)
        
        console.print(f"✅ Worktree created at: [bold green]{worktree_path}[/bold green]")
        
    except Exception as e:
        console.print(f"❌ Error creating worktree: {e}", style="bold red")
        raise typer.Exit(code=1)


@worktree_app.command()
def remove(
    worktree_path: str = typer.Argument(help="Path to the worktree to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Force removal without confirmation")
):
    """Remove an existing worktree."""
    try:
        plum = PlumIntegration()
        
        if not plum.is_available():
            console.print("❌ Plum integration not available", style="bold red")
            console.print("Please ensure plum is installed and accessible", style="dim")
            raise typer.Exit(code=1)
        
        worktree_path_obj = Path(worktree_path)
        
        if not force:
            response = typer.confirm(f"Remove worktree at {worktree_path}?")
            if not response:
                console.print("Operation cancelled", style="yellow")
                return
        
        console.print(f"🗑️  Removing worktree: [bold yellow]{worktree_path}[/bold yellow]")
        
        success = plum.remove_worktree(Path.cwd(), worktree_path_obj)
        
        if success:
            console.print("✅ Worktree removed successfully", style="bold green")
        else:
            console.print("❌ Failed to remove worktree", style="bold red")
            raise typer.Exit(code=1)
        
    except Exception as e:
        console.print(f"❌ Error removing worktree: {e}", style="bold red")
        raise typer.Exit(code=1)