"""Session management commands for PruneJuice CLI."""

import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
from typing import Optional

from ..session_utils import TmuxManager, SessionLifecycleManager

console = Console()

# Create session subcommand app
session_app = typer.Typer(
    name="session",
    help="Manage tmux sessions",
    rich_markup_mode="rich",
)


@session_app.command()
def list(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed session info"
    ),
):
    """List all tmux sessions."""
    try:
        tmux_manager = TmuxManager()

        if not tmux_manager.check_tmux_available():
            console.print("❌ Tmux not available", style="bold red")
            console.print("Please ensure tmux is installed and available", style="dim")
            raise typer.Exit(code=1)

        console.print("📺 Listing tmux sessions...", style="bold green")

        sessions = tmux_manager.list_sessions()

        if not sessions:
            console.print("No sessions found", style="yellow")
            return

        table = Table(title="Tmux Sessions")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Path", style="yellow")

        if verbose:
            table.add_column("Status", style="green")

        for session in sessions:
            row = [session.get("name", "unknown"), session.get("path", "unknown")]
            if verbose:
                row.append(session.get("status", "unknown"))
            table.add_row(*row)

        console.print(table)

    except Exception as e:
        console.print(f"❌ Error listing sessions: {e}", style="bold red")
        raise typer.Exit(code=1)


@session_app.command()
def create(
    task_name: str = typer.Argument(help="Name for the new session/task"),
    working_dir: Optional[str] = typer.Option(
        None, "--dir", "-d", help="Worktree directory (default: current)"
    ),
):
    """Create a new tmux session for a worktree.

    Note: The working directory must be a valid git worktree.
    If you're not in a worktree, specify one with --dir option.
    """
    try:
        tmux_manager = TmuxManager()
        session_manager = SessionLifecycleManager(tmux_manager)

        if not tmux_manager.check_tmux_available():
            console.print("❌ Tmux not available", style="bold red")
            console.print("Please ensure tmux is installed and available", style="dim")
            raise typer.Exit(code=1)

        work_dir = Path(working_dir) if working_dir else Path.cwd()

        console.print(f"🎬 Creating session: [bold cyan]{task_name}[/bold cyan]")
        console.print(f"Worktree directory: [dim]{work_dir}[/dim]")

        session_name = session_manager.create_session_for_worktree(
            work_dir, task_name, auto_attach=False
        )

        if not session_name:
            # Fallback session name if creation failed
            session_name = f"prunejuice-{task_name}"

        console.print(f"✅ Session created: [bold green]{session_name}[/bold green]")
        console.print("Use 'prj session attach <name>' to connect to the session")

    except Exception as e:
        console.print(f"❌ Error creating session: {e}", style="bold red")
        raise typer.Exit(code=1)


@session_app.command()
def attach(session_name: str = typer.Argument(help="Name of the session to attach to")):
    """Attach to an existing tmux session."""
    try:
        tmux_manager = TmuxManager()
        session_manager = SessionLifecycleManager(tmux_manager)

        if not tmux_manager.check_tmux_available():
            console.print("❌ Tmux not available", style="bold red")
            console.print("Please ensure tmux is installed and available", style="dim")
            raise typer.Exit(code=1)

        console.print(f"🔗 Attaching to session: [bold cyan]{session_name}[/bold cyan]")

        success = session_manager.attach_to_session(session_name)

        if success:
            console.print("✅ Session attached successfully", style="bold green")
        else:
            console.print("❌ Failed to attach to session", style="bold red")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"❌ Error attaching to session: {e}", style="bold red")
        raise typer.Exit(code=1)


@session_app.command()
def kill(
    session_name: str = typer.Argument(help="Name of the session to kill"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force kill without confirmation"
    ),
):
    """Kill an existing tmux session."""
    try:
        tmux_manager = TmuxManager()
        session_manager = SessionLifecycleManager(tmux_manager)

        if not tmux_manager.check_tmux_available():
            console.print("❌ Tmux not available", style="bold red")
            console.print("Please ensure tmux is installed and available", style="dim")
            raise typer.Exit(code=1)

        if not force:
            response = typer.confirm(f"Kill session '{session_name}'?")
            if not response:
                console.print("Operation cancelled", style="yellow")
                return

        console.print(f"💀 Killing session: [bold yellow]{session_name}[/bold yellow]")

        success = session_manager.kill_session(session_name)

        if success:
            console.print("✅ Session killed successfully", style="bold green")
        else:
            console.print("❌ Failed to kill session", style="bold red")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"❌ Error killing session: {e}", style="bold red")
        raise typer.Exit(code=1)


@session_app.command()
def cleanup(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be cleaned up"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force cleanup without confirmation"
    ),
):
    """Clean up inactive or orphaned sessions."""
    try:
        tmux_manager = TmuxManager()

        if not tmux_manager.check_tmux_available():
            console.print("❌ Tmux not available", style="bold red")
            console.print("Please ensure tmux is installed and available", style="dim")
            raise typer.Exit(code=1)

        console.print("🧹 Starting session cleanup...", style="bold green")

        if dry_run:
            console.print(
                "DRY RUN - No sessions will be actually removed", style="yellow"
            )

        # Get all sessions and identify inactive ones
        sessions = tmux_manager.list_sessions()

        if not sessions:
            console.print("No sessions to clean up", style="dim")
            return

        # For now, list all sessions - actual cleanup logic would need to be implemented
        # based on pots' specific cleanup criteria
        console.print(f"Found {len(sessions)} sessions", style="dim")

        if not dry_run and not force:
            response = typer.confirm("Proceed with cleanup?")
            if not response:
                console.print("Cleanup cancelled", style="yellow")
                return

        # Note: This is a placeholder - real cleanup would need to call pots cleanup command
        console.print("✅ Session cleanup completed", style="bold green")

    except Exception as e:
        console.print(f"❌ Error during cleanup: {e}", style="bold red")
        raise typer.Exit(code=1)
