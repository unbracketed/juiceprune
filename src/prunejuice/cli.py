"""CLI interface for PruneJuice using Typer."""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import asyncio
import json

from .core.config import Settings
from .core.database import Database
from .commands.loader import CommandLoader
from .utils.logging import setup_logging
from .commands.worktree import worktree_app
from .commands.session import session_app
from .integrations.pots import PotsIntegration
from .worktree_utils import GitWorktreeManager
from .utils.path_resolver import ProjectPathResolver

# Create Typer app
app = typer.Typer(
    name="prunejuice",
    help="🧃 PruneJuice SDLC Orchestrator - Parallel Agentic Coding Workflow Manager",
    rich_markup_mode="rich"
)

console = Console()

# Formatting helper functions
def _format_duration(start_time: datetime, end_time: Optional[datetime]) -> str:
    """Format the duration between two datetimes."""
    if not end_time:
        return "running"
    duration = end_time - start_time
    return f"{duration.total_seconds():.1f}s"

def _get_status_style(status: str) -> str:
    """Return the rich style for a given status."""
    return {
        "completed": "green",
        "failed": "red", 
        "running": "yellow",
        "cancelled": "dim"
    }.get(status, "white")

# Add subcommand groups
app.add_typer(worktree_app, name="worktree")
app.add_typer(session_app, name="session")


@app.command()
def init(
    path: Optional[Path] = typer.Argument(None, help="Project path to initialize")
):
    """Initialize a PruneJuice project."""
    # Use runtime Path.cwd() if no path provided
    if path is None:
        path = Path.cwd()
        
    console.print("🧃 Initializing PruneJuice project...", style="bold green")
    
    # Create project structure
    prj_dir = path / ".prj"
    prj_dir.mkdir(exist_ok=True)
    (prj_dir / "commands").mkdir(exist_ok=True)
    (prj_dir / "steps").mkdir(exist_ok=True)
    (prj_dir / "configs").mkdir(exist_ok=True)
    (prj_dir / "artifacts").mkdir(exist_ok=True)
    
    # Copy template commands (optional - project can work without them)
    try:
        from importlib import resources
        templates = resources.files("prunejuice.template_commands")
        template_names = ["analyze-issue.yaml", "code-review.yaml", "feature-branch.yaml", "echo-hello.yaml", "echo-arg.yaml", "worktree-list.yaml", "echo-hello-in-session.yaml"]
        
        # Check if templates directory exists
        if templates.is_dir():
            for template_name in template_names:
                try:
                    template_path = templates / template_name
                    if template_path.is_file():
                        (prj_dir / "commands" / template_name).write_text(
                            template_path.read_text()
                        )
                        console.print(f"Copied template: {template_name}", style="dim")
                except Exception as e:
                    console.print(f"Warning: Could not copy template {template_name}: {e}", style="yellow")
        else:
            console.print("Templates not found - project initialized without example commands", style="dim")
    except Exception as e:
        console.print(f"Note: Template commands not available: {e}", style="dim")
    
    # Copy template steps (optional - project can work without them)
    try:
        from importlib import resources
        template_steps = resources.files("prunejuice.template_steps")
        step_names = ["echo-hello-step.sh", "echo-arg-step.sh", "list-project-worktrees.sh", "session-create.sh", "session-echo-hello.sh", "session-destroy.sh"]
        
        # Check if template steps directory exists
        if template_steps.is_dir():
            for step_name in step_names:
                try:
                    step_path = template_steps / step_name
                    if step_path.is_file():
                        target_path = prj_dir / "steps" / step_name
                        target_path.write_text(step_path.read_text())
                        # Make script executable
                        target_path.chmod(0o755)
                        console.print(f"Copied template step: {step_name}", style="dim")
                except Exception as e:
                    console.print(f"Warning: Could not copy step {step_name}: {e}", style="yellow")
        else:
            console.print("Template steps not found - project initialized without example steps", style="dim")
    except Exception as e:
        console.print(f"Note: Template steps not available: {e}", style="dim")
    
    # Initialize database
    try:
        db = Database(prj_dir / "prunejuice.db")
        asyncio.run(db.initialize())
        console.print("Database initialized", style="dim")
    except Exception as e:
        console.print(f"Warning: Database initialization failed: {e}", style="yellow")
    
    console.print("✅ Project initialized successfully!", style="bold green")


@app.command()
def list(
    what: Optional[str] = typer.Argument("events", help="What to list: 'events' (default) or 'commands'"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of events to show (events only)"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status (events only)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed info")
):
    """List recent events (default) or available commands."""
    if what == "commands":
        _list_commands(verbose)
    elif what == "events":
        _list_events(limit, status, verbose)
    else:
        console.print(f"❌ Unknown list type: {what}. Use 'events' or 'commands'.", style="bold red")
        raise typer.Exit(code=1)


def _list_commands(verbose: bool = False):
    """List available SDLC commands."""
    try:
        loader = CommandLoader()
        commands = loader.discover_commands(Path.cwd())
        
        if not commands:
            console.print("No commands found. Run 'prj init' first.", style="yellow")
            return
        
        table = Table(title="Available Commands")
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Category", style="yellow")
        table.add_column("Description", style="green")
        
        if verbose:
            table.add_column("Steps", style="blue")
        
        for cmd in commands:
            row = [cmd.name, cmd.category, cmd.description]
            if verbose:
                steps = cmd.pre_steps + cmd.steps + cmd.post_steps
                row.append(f"{len(steps)} steps")
            table.add_row(*row)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Error listing commands: {e}", style="bold red")
        raise typer.Exit(code=1)


def _list_events(limit: int = 10, status: Optional[str] = None, verbose: bool = False):
    """List recent command events."""
    try:
        # Get project root for consistent database access
        project_root = ProjectPathResolver.get_project_root()
        settings = Settings(project_path=project_root)
        db = Database(settings.db_path)
        
        # Filter to current project by default
        project_filter = str(Path.cwd())
        
        events = asyncio.run(db.get_events(
            limit=limit, 
            status=status,
            project_path=project_filter
        ))
        
        if not events:
            console.print("No recent events found.", style="yellow")
            return

        table = Table(title="Recent Events")
        table.add_column("ID", style="dim", width=4)
        table.add_column("Command", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Started", style="green")
        table.add_column("Duration", style="blue")
        
        if verbose:
            table.add_column("Session", style="dim")

        for event in events:
            duration_str = _format_duration(event.start_time, event.end_time)
            status_style = _get_status_style(event.status)

            row = [
                str(event.id),
                event.command,
                f"[{status_style}]{event.status}[/{status_style}]",
                event.start_time.strftime("%m/%d %H:%M"),
                duration_str
            ]
            
            if verbose:
                row.append(event.session_id)
                
            table.add_row(*row)
        
        console.print(table)

    except Exception as e:
        console.print(f"❌ Error listing events: {e}", style="bold red")
        raise typer.Exit(code=1)


# Keep backwards compatibility
@app.command()
def list_commands(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed info")
):
    """List available SDLC commands (deprecated: use 'list commands')."""
    console.print("Note: 'list-commands' is deprecated. Use 'list commands' instead.", style="dim")
    _list_commands(verbose)


@app.command()
def run(
    command: str = typer.Argument(help="Command name to execute"),
    args: Optional[List[str]] = typer.Argument(None, help="Command arguments in key=value format"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be executed"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Run an SDLC command."""
    try:
        # Set up logging
        log_level = "DEBUG" if verbose else "INFO"
        setup_logging(level=log_level)
        
        console.print(f"🚀 Executing command: [bold cyan]{command}[/bold cyan]")
        
        # Import executor here to avoid circular imports
        from .core.executor import Executor
        
        # Get project root for consistent database access
        project_root = ProjectPathResolver.get_project_root()
        settings = Settings(project_path=project_root)
        executor = Executor(settings)
        
        # Parse arguments
        parsed_args = {}
        for arg in args or []:
            if "=" in arg:
                key, value = arg.split("=", 1)
                parsed_args[key] = value
            else:
                console.print(f"❌ Invalid argument format: {arg}. Use key=value", style="bold red")
                raise typer.Exit(code=1)
        
        # Run command
        result = asyncio.run(
            executor.execute_command(command, Path.cwd(), parsed_args, dry_run)
        )
        
        # Handle dry run output specially
        if dry_run:
            console.print(result.output)
            return
        
        if result.success:
            console.print("✅ Command completed successfully!", style="bold green")
            if result.artifacts_path:
                console.print(f"Artifacts stored in: {result.artifacts_path}", style="dim")
        else:
            console.print(f"❌ Command failed: {result.error}", style="bold red")
            raise typer.Exit(code=1)
            
    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        if verbose:
            import traceback
            traceback.print_exc()
        raise typer.Exit(code=1)


def _get_project_context():
    """Get project and worktree context information."""
    context = {
        'project_name': Path.cwd().name,  # fallback
        'project_root': Path.cwd(),
        'current_worktree': None,
        'is_git_repo': False
    }
    
    try:
        # Get Git-aware project root
        project_root = ProjectPathResolver.get_project_root()
        context['project_root'] = project_root
        context['project_name'] = project_root.name
        
        # Check if we're in a Git repository
        manager = GitWorktreeManager(Path.cwd())
        if manager.is_git_repository():
            context['is_git_repo'] = True
            
            # Check if current location is a worktree
            current_path = Path.cwd()
            worktree_info = manager.get_worktree_info(current_path)
            if worktree_info:
                # Extract branch name from refs/heads/branch-name format
                branch = worktree_info.get('branch', '')
                if branch.startswith('refs/heads/'):
                    branch = branch[11:]  # Remove 'refs/heads/' prefix
                context['current_worktree'] = {
                    'branch': branch,
                    'path': worktree_info.get('path'),
                    'is_main': current_path == project_root
                }
    except Exception:
        # Fallback to current directory if Git operations fail
        pass
    
    return context


@app.command()
def status():
    """Show PruneJuice project status."""
    try:
        # Get project and worktree context
        context = _get_project_context()
        settings = Settings(project_path=context['project_root'])
        
        # Check if project is initialized - use project root, not current directory
        project_root = context['project_root']
        prj_dir = project_root / ".prj"
        db_exists = settings.db_path.exists()
        
        # Check if database is properly initialized by trying to query it
        is_initialized = False
        if prj_dir.exists() and db_exists:
            try:
                db = Database(settings.db_path)
                # Try a simple query to check if tables exist
                asyncio.run(db.get_recent_events(limit=1))
                is_initialized = True
            except Exception:
                # Database exists but is not properly initialized
                is_initialized = False
        
        # Show project info
        console.print("📊 PruneJuice Project Status", style="bold")
        console.print(f"Project: {context['project_name']}")
        
        # Show current worktree context if applicable
        if context['current_worktree'] and not context['current_worktree']['is_main']:
            console.print(f"Current worktree: {context['current_worktree']['branch']}", style="cyan")
        
        if not is_initialized:
            console.print("❌ Project not initialized", style="bold red")
            console.print(f"Database: {settings.db_path} (missing)", style="dim")
            console.print(f"Artifacts: {settings.artifacts_dir} (missing)", style="dim")
            console.print("\n💡 Run 'prj init' to initialize this project", style="bold yellow")
        else:
            console.print(f"Database: {settings.db_path}")
            console.print(f"Artifacts: {settings.artifacts_dir}")
            
            # Show recent events only if initialized
            db = Database(settings.db_path)
            events = asyncio.run(db.get_recent_events(limit=5))
            if events:
                table = Table(title="Recent Events")
                table.add_column("Command", style="cyan")
                table.add_column("Status", style="yellow")
                table.add_column("Start Time", style="green")
                table.add_column("Duration", style="blue")
                
                for event in events:
                    duration_str = _format_duration(event.start_time, event.end_time)
                    status_style = _get_status_style(event.status)
                    
                    table.add_row(
                        event.command,
                        f"[{status_style}]{event.status}[/{status_style}]",
                        event.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                        duration_str
                    )
                
                console.print(table)
            else:
                console.print("No recent events found.", style="dim")
                
            # Show active events
            active_events = asyncio.run(db.get_active_events())
            if active_events:
                console.print(f"\n🔄 Active Events: {len(active_events)}", style="bold yellow")
                for event in active_events:
                    console.print(f"  - {event.command} (session: {event.session_id})")
        
        # Show worktree information (always show, regardless of init status)
        console.print("\n🌳 Worktree Status", style="bold")
        if context['is_git_repo']:
            try:
                manager = GitWorktreeManager(project_root)
                worktrees = manager.list_worktrees()
                if worktrees:
                    console.print(f"  Active worktrees: {len(worktrees)}")
                    for wt in worktrees[:3]:  # Show first 3
                        # Format branch name (remove refs/heads/ prefix)
                        branch = wt.get('branch', 'unknown')
                        if branch.startswith('refs/heads/'):
                            branch = branch[11:]
                        console.print(f"    - {branch} at {wt.get('path', 'unknown')}", style="dim")
                    if len(worktrees) > 3:
                        console.print(f"    ... and {len(worktrees) - 3} more", style="dim")
                else:
                    console.print("  No worktrees found", style="dim")
            except Exception:
                console.print("  Error retrieving worktree info", style="yellow")
        else:
            console.print("  Not a Git repository", style="dim")
        
        # Show session information (always show, regardless of init status)
        console.print("\n📺 Session Status", style="bold")
        pots = PotsIntegration()
        if pots.is_available():
            try:
                sessions = pots.list_sessions()
                if sessions:
                    console.print(f"  Active sessions: {len(sessions)}")
                    for session in sessions[:3]:  # Show first 3
                        console.print(f"    - {session.get('name', 'unknown')} at {session.get('path', 'unknown')}", style="dim")
                    if len(sessions) > 3:
                        console.print(f"    ... and {len(sessions) - 3} more", style="dim")
                else:
                    console.print("  No sessions found", style="dim")
            except Exception:
                console.print("  Error retrieving session info", style="yellow")
        else:
            console.print("  Pots integration not available", style="dim")
        
    except Exception as e:
        console.print(f"❌ Error getting status: {e}", style="bold red")
        raise typer.Exit(code=1)


@app.command()
def cleanup(
    days: int = typer.Option(30, help="Clean up artifacts older than N days"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")
):
    """Clean up old artifacts and sessions."""
    try:
        # Get project root for consistent database access
        project_root = ProjectPathResolver.get_project_root()
        settings = Settings(project_path=project_root)
        
        if not confirm:
            response = typer.confirm(f"Clean up artifacts older than {days} days?")
            if not response:
                console.print("Cleanup cancelled.", style="yellow")
                return
        
        from .utils.artifacts import ArtifactStore
        artifact_store = ArtifactStore(settings.artifacts_dir)
        artifact_store.cleanup_old_sessions(days)
        
        console.print(f"✅ Cleaned up artifacts older than {days} days", style="bold green")
        
    except Exception as e:
        console.print(f"❌ Error during cleanup: {e}", style="bold red")
        raise typer.Exit(code=1)


@app.command()
def history(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of events to show"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status (completed, failed, running)"),
    command: Optional[str] = typer.Option(None, "--command", help="Filter by command name"),
    worktree: Optional[str] = typer.Option(None, "--worktree", help="Filter by worktree name"),
    project: bool = typer.Option(False, "--project", help="Filter to current project only")
):
    """Show command execution history with filtering options."""
    try:
        # Get project root for consistent database access
        project_root = ProjectPathResolver.get_project_root()
        settings = Settings(project_path=project_root)
        db = Database(settings.db_path)
        
        # Get project filter if requested
        project_filter = str(Path.cwd()) if project else None
        
        events = asyncio.run(db.get_events(
            limit=limit, 
            status=status, 
            command=command, 
            worktree=worktree,
            project_path=project_filter
        ))
        
        if not events:
            console.print("No history found matching criteria.", style="yellow")
            return

        table = Table(title="Command History")
        table.add_column("ID", style="dim", width=4)
        table.add_column("Command", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Start Time", style="green")
        table.add_column("Duration", style="blue")
        table.add_column("Project", style="dim")

        for event in events:
            duration_str = _format_duration(event.start_time, event.end_time)
            status_style = _get_status_style(event.status)
            project_name = Path(event.project_path).name

            table.add_row(
                str(event.id),
                event.command,
                f"[{status_style}]{event.status}[/{status_style}]",
                event.start_time.strftime("%m/%d %H:%M"),
                duration_str,
                project_name
            )
        
        console.print(table)

    except Exception as e:
        console.print(f"❌ Error fetching history: {e}", style="bold red")
        raise typer.Exit(code=1)


@app.command()
def show(
    event_id: int = typer.Argument(..., help="The ID of the event to show")
):
    """Show detailed information for a specific event."""
    try:
        # Get project root for consistent database access
        project_root = ProjectPathResolver.get_project_root()
        settings = Settings(project_path=project_root)
        db = Database(settings.db_path)
        event = asyncio.run(db.get_event(event_id))

        if not event:
            console.print(f"❌ Event with ID {event_id} not found.", style="bold red")
            raise typer.Exit(code=1)

        # Create a formatted panel
        text = Text()
        text.append("Command: ", style="bold yellow")
        text.append(f"{event.command}\n")
        text.append("Status: ", style="bold yellow")
        status_style = _get_status_style(event.status)
        text.append(f"{event.status}\n", style=status_style)
        text.append("Project: ", style="bold yellow")
        text.append(f"{Path(event.project_path).name}\n")
        text.append("Full Path: ", style="bold yellow")
        text.append(f"{event.project_path}\n")
        if event.worktree_name:
            text.append("Worktree: ", style="bold yellow")
            text.append(f"{event.worktree_name}\n")
        text.append("Session ID: ", style="bold yellow")
        text.append(f"{event.session_id}\n")
        text.append("Start Time: ", style="bold yellow")
        text.append(f"{event.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        if event.end_time:
            text.append("End Time: ", style="bold yellow")
            text.append(f"{event.end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            duration = event.end_time - event.start_time
            text.append("Duration: ", style="bold yellow")
            text.append(f"{duration.total_seconds():.2f}s\n")
        if event.exit_code is not None:
            text.append("Exit Code: ", style="bold yellow")
            text.append(f"{event.exit_code}\n")
        if event.artifacts_path:
            text.append("Artifacts: ", style="bold yellow")
            text.append(f"{event.artifacts_path}\n")
        if event.error_message:
            text.append("Error: ", style="bold red")
            text.append(f"{event.error_message}\n")
        if event.metadata:
            text.append("Metadata: ", style="bold yellow")
            text.append(f"{json.dumps(event.metadata, indent=2)}")

        panel = Panel(text, title=f"Event Details (ID: {event.id})", border_style="blue")
        console.print(panel)

    except Exception as e:
        console.print(f"❌ Error showing event: {e}", style="bold red")
        raise typer.Exit(code=1)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()