"""CLI interface for PruneJuice using Typer."""

import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
from typing import Optional, List
import asyncio
import sys

from .core.config import Settings
from .core.database import Database
from .commands.loader import CommandLoader
from .utils.logging import setup_logging
from .commands.worktree import worktree_app
from .commands.session import session_app
from .integrations.plum import PlumIntegration
from .integrations.pots import PotsIntegration

# Create Typer app
app = typer.Typer(
    name="prunejuice",
    help="🧃 PruneJuice SDLC Orchestrator - Parallel Agentic Coding Workflow Manager",
    rich_markup_mode="rich"
)

console = Console()

# Add subcommand groups
app.add_typer(worktree_app, name="worktree")
app.add_typer(session_app, name="session")


@app.command()
def init(
    path: Path = typer.Argument(Path.cwd(), help="Project path to initialize")
):
    """Initialize a PruneJuice project."""
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
        settings = Settings()
        db = Database(prj_dir / "prunejuice.db")
        asyncio.run(db.initialize())
        console.print("Database initialized", style="dim")
    except Exception as e:
        console.print(f"Warning: Database initialization failed: {e}", style="yellow")
    
    console.print("✅ Project initialized successfully!", style="bold green")


@app.command()
def list_commands(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed info")
):
    """List available SDLC commands."""
    try:
        loader = CommandLoader()
        commands = asyncio.run(loader.discover_commands(Path.cwd()))
        
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
        
        settings = Settings()
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


@app.command()
def status():
    """Show PruneJuice project status."""
    try:
        settings = Settings()
        
        # Check if project is initialized
        prj_dir = Path.cwd() / ".prj"
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
        console.print(f"Project: {Path.cwd().name}")
        
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
                    # Calculate duration
                    if event.end_time:
                        duration = event.end_time - event.start_time
                        duration_str = f"{duration.total_seconds():.1f}s"
                    else:
                        duration_str = "running"
                    
                    # Format status with color
                    status_style = {
                        "completed": "green",
                        "failed": "red",
                        "running": "yellow"
                    }.get(event.status, "white")
                    
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
        plum = PlumIntegration()
        if plum.is_available():
            try:
                worktrees = asyncio.run(plum.list_worktrees(Path.cwd()))
                if worktrees:
                    console.print(f"  Active worktrees: {len(worktrees)}")
                    for wt in worktrees[:3]:  # Show first 3
                        console.print(f"    - {wt.get('branch', 'unknown')} at {wt.get('path', 'unknown')}", style="dim")
                    if len(worktrees) > 3:
                        console.print(f"    ... and {len(worktrees) - 3} more", style="dim")
                else:
                    console.print("  No worktrees found", style="dim")
            except Exception:
                console.print("  Error retrieving worktree info", style="yellow")
        else:
            console.print("  Plum integration not available", style="dim")
        
        # Show session information (always show, regardless of init status)
        console.print("\n📺 Session Status", style="bold")
        pots = PotsIntegration()
        if pots.is_available():
            try:
                sessions = asyncio.run(pots.list_sessions())
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
        settings = Settings()
        
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


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()