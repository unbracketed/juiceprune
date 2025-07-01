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
import os
import subprocess

from .core.config import Settings
from .core.database import Database
from .commands.loader import CommandLoader
from .utils.logging import setup_logging
from .commands.worktree import worktree_app
from .commands.session import session_app
from .worktree_utils import GitWorktreeManager
from .session_utils import TmuxManager, SessionLifecycleManager
from .utils.path_resolver import ProjectPathResolver
from .utils.diff_display import (
    display_diff_summary,
    display_diff_with_pager,
    display_worktree_status,
    get_diff_type_menu,
    display_diff_error,
)

# Create Typer app
app = typer.Typer(
    name="prunejuice",
    help="🧃 PruneJuice SDLC Orchestrator - Parallel Agentic Coding Workflow Manager",
    rich_markup_mode="rich",
    no_args_is_help=False,  # Allow handling no arguments
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
        "cancelled": "dim",
    }.get(status, "white")


# Add subcommand groups
app.add_typer(worktree_app, name="worktree")
app.add_typer(session_app, name="session")


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    help: bool = typer.Option(False, "--help", "-h", help="Show help message"),
):
    """Handle invocation with no subcommand - default to resume."""
    if help:
        # Show help when explicitly requested
        print(ctx.get_help())
        ctx.exit()
    elif ctx.invoked_subcommand is None:
        # No subcommand provided, invoke resume
        resume()
        ctx.exit()


@app.command()
def init(
    path: Optional[Path] = typer.Argument(None, help="Project path to initialize"),
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
        template_names = [
            "analyze-issue.yaml",
            "code-review.yaml",
            "feature-branch.yaml",
            "echo-hello.yaml",
            "echo-arg.yaml",
            "worktree-list.yaml",
            "echo-hello-in-session.yaml",
        ]

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
                    console.print(
                        f"Warning: Could not copy template {template_name}: {e}",
                        style="yellow",
                    )
        else:
            console.print(
                "Templates not found - project initialized without example commands",
                style="dim",
            )
    except Exception as e:
        console.print(f"Note: Template commands not available: {e}", style="dim")

    # Copy template steps (optional - project can work without them)
    try:
        from importlib import resources

        template_steps = resources.files("prunejuice.template_steps")
        step_names = [
            "echo-hello-step.sh",
            "echo-arg-step.sh",
            "list-project-worktrees.sh",
            "session-create.sh",
            "session-echo-hello.sh",
            "session-destroy.sh",
        ]

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
                    console.print(
                        f"Warning: Could not copy step {step_name}: {e}", style="yellow"
                    )
        else:
            console.print(
                "Template steps not found - project initialized without example steps",
                style="dim",
            )
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
    what: Optional[str] = typer.Argument(
        "events", help="What to list: 'events' (default) or 'commands'"
    ),
    limit: int = typer.Option(
        10, "--limit", "-n", help="Number of events to show (events only)"
    ),
    status: Optional[str] = typer.Option(
        None, "--status", help="Filter by status (events only)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed info"),
):
    """List recent events (default) or available commands."""
    if what == "commands":
        _list_commands(verbose)
    elif what == "events":
        _list_events(limit, status, verbose)
    else:
        console.print(
            f"❌ Unknown list type: {what}. Use 'events' or 'commands'.",
            style="bold red",
        )
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

        events = asyncio.run(
            db.get_events(limit=limit, status=status, project_path=project_filter)
        )

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
                duration_str,
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
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed info"),
):
    """List available SDLC commands (deprecated: use 'list commands')."""
    console.print(
        "Note: 'list-commands' is deprecated. Use 'list commands' instead.", style="dim"
    )
    _list_commands(verbose)


@app.command()
def run(
    command: str = typer.Argument(help="Command name to execute"),
    args: Optional[List[str]] = typer.Argument(
        None, help="Command arguments in key=value format"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be executed"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
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
                console.print(
                    f"❌ Invalid argument format: {arg}. Use key=value",
                    style="bold red",
                )
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
                console.print(
                    f"Artifacts stored in: {result.artifacts_path}", style="dim"
                )
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
        "project_name": Path.cwd().name,  # fallback
        "project_root": Path.cwd(),
        "current_worktree": None,
        "is_git_repo": False,
    }

    try:
        # Get Git-aware project root
        project_root = ProjectPathResolver.get_project_root()
        context["project_root"] = project_root
        context["project_name"] = project_root.name

        # Check if we're in a Git repository
        manager = GitWorktreeManager(Path.cwd())
        if manager.is_git_repository():
            context["is_git_repo"] = True

            # Check if current location is a worktree
            current_path = Path.cwd()
            worktree_info = manager.get_worktree_info(current_path)
            if worktree_info:
                # Extract branch name from refs/heads/branch-name format
                branch = worktree_info.get("branch", "")
                if branch.startswith("refs/heads/"):
                    branch = branch[11:]  # Remove 'refs/heads/' prefix
                context["current_worktree"] = {
                    "branch": branch,
                    "path": worktree_info.get("path"),
                    "is_main": current_path == project_root,
                }
    except Exception:
        # Fallback to current directory if Git operations fail
        pass

    return context


@app.command()
def status(
    all_worktrees: bool = typer.Option(
        False,
        "-a",
        "--all",
        help="Show events from all worktrees (default: current worktree only when in worktree)",
    ),
):
    """Show PruneJuice project status."""
    try:
        # Get project and worktree context
        context = _get_project_context()
        settings = Settings(project_path=context["project_root"])

        # Check if project is initialized - use project root, not current directory
        project_root = context["project_root"]
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
        if context["current_worktree"] and not context["current_worktree"]["is_main"]:
            console.print(
                f"Current worktree: {context['current_worktree']['branch']}",
                style="cyan",
            )

        if not is_initialized:
            console.print("❌ Project not initialized", style="bold red")
            console.print(f"Database: {settings.db_path} (missing)", style="dim")
            console.print(f"Artifacts: {settings.artifacts_dir} (missing)", style="dim")
            console.print(
                "\n💡 Run 'prj init' to initialize this project", style="bold yellow"
            )
        else:
            console.print(f"Database: {settings.db_path}")
            console.print(f"Artifacts: {settings.artifacts_dir}")

            # Show recent events only if initialized
            db = Database(settings.db_path)

            # Determine filtering based on worktree context
            worktree_filter = None
            if (
                not all_worktrees
                and context["current_worktree"]
                and not context["current_worktree"]["is_main"]
            ):
                # Filter to current worktree only
                worktree_filter = context["current_worktree"]["branch"]

            events = asyncio.run(db.get_events(limit=5, worktree=worktree_filter))

            if events:
                table = Table(title="Recent Events")
                table.add_column("Command", style="cyan")
                table.add_column("Status", style="yellow")
                table.add_column("Start Time", style="green")
                table.add_column("Duration", style="blue")
                table.add_column("Worktree", style="dim")

                for event in events:
                    duration_str = _format_duration(event.start_time, event.end_time)
                    status_style = _get_status_style(event.status)

                    # Display worktree name or "main" for main branch
                    worktree_display = event.worktree_name or "main"

                    table.add_row(
                        event.command,
                        f"[{status_style}]{event.status}[/{status_style}]",
                        event.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                        duration_str,
                        worktree_display,
                    )

                console.print(table)
            else:
                console.print("No recent events found.", style="dim")

            # Show active events
            active_events = asyncio.run(db.get_active_events())
            if active_events:
                console.print(
                    f"\n🔄 Active Events: {len(active_events)}", style="bold yellow"
                )
                for event in active_events:
                    console.print(f"  - {event.command} (session: {event.session_id})")

        # Show worktree information (always show, regardless of init status)
        console.print("\n🌳 Worktree Status", style="bold")
        if context["is_git_repo"]:
            try:
                manager = GitWorktreeManager(project_root)
                worktrees = manager.list_worktrees()
                if worktrees:
                    console.print(f"  Active worktrees: {len(worktrees)}")
                    for wt in worktrees[:3]:  # Show first 3
                        # Format branch name (remove refs/heads/ prefix)
                        branch = wt.get("branch", "unknown")
                        if branch.startswith("refs/heads/"):
                            branch = branch[11:]
                        console.print(
                            f"    - {branch} at {wt.get('path', 'unknown')}",
                            style="dim",
                        )
                    if len(worktrees) > 3:
                        console.print(
                            f"    ... and {len(worktrees) - 3} more", style="dim"
                        )
                else:
                    console.print("  No worktrees found", style="dim")
            except Exception:
                console.print("  Error retrieving worktree info", style="yellow")
        else:
            console.print("  Not a Git repository", style="dim")

        # Show session information (always show, regardless of init status)
        console.print("\n📺 Session Status", style="bold")
        tmux_manager = TmuxManager()
        if tmux_manager.check_tmux_available():
            try:
                sessions = tmux_manager.list_sessions()
                if sessions:
                    console.print(f"  Active sessions: {len(sessions)}")
                    for session in sessions[:3]:  # Show first 3
                        console.print(
                            f"    - {session.get('name', 'unknown')} at {session.get('path', 'unknown')}",
                            style="dim",
                        )
                    if len(sessions) > 3:
                        console.print(
                            f"    ... and {len(sessions) - 3} more", style="dim"
                        )
                else:
                    console.print("  No sessions found", style="dim")
            except Exception:
                console.print("  Error retrieving session info", style="yellow")
        else:
            console.print("  Tmux not available", style="dim")

    except Exception as e:
        console.print(f"❌ Error getting status: {e}", style="bold red")
        raise typer.Exit(code=1)


@app.command()
def resume():
    """Show available worktrees and sessions for quick navigation."""
    try:
        # Get project context
        context = _get_project_context()

        # Collect available items
        items = []

        # Add worktrees
        if context["is_git_repo"]:
            try:
                git_manager = GitWorktreeManager(context["project_root"])
                worktrees = git_manager.list_worktrees()

                for wt in worktrees:
                    # Format branch name (remove refs/heads/ prefix)
                    branch = wt.get("branch", "unknown")
                    if branch.startswith("refs/heads/"):
                        branch = branch[11:]

                    # Skip if this is the current worktree
                    if context["current_worktree"] and context["current_worktree"][
                        "path"
                    ] == wt.get("path"):
                        continue

                    items.append(
                        {
                            "type": "worktree",
                            "display": f"🌳 {branch}",
                            "branch": branch,
                            "path": wt.get("path"),
                            "is_main": Path(wt.get("path", ""))
                            == context["project_root"],
                        }
                    )
            except Exception as e:
                console.print(f"Warning: Could not list worktrees: {e}", style="yellow")

        # Add tmux sessions
        try:
            tmux_manager = TmuxManager()
            if tmux_manager.check_tmux_available():
                sessions = tmux_manager.list_sessions()

                for session in sessions:
                    items.append(
                        {
                            "type": "session",
                            "display": f"📺 {session.get('name', 'unknown')}",
                            "name": session.get("name", "unknown"),
                            "path": session.get("path", ""),
                            "attached": session.get("attached", False),
                        }
                    )
        except Exception as e:
            console.print(f"Warning: Could not list sessions: {e}", style="yellow")

        # Check if anything is available
        if not items:
            console.print("Nothing simmering. Use --help for help", style="dim")
            return

        # Display items for selection
        console.print("Available items:", style="bold")
        for i, item in enumerate(items, 1):
            console.print(f"  {i}. {item['display']}")

        # Get user selection
        try:
            selection = typer.prompt("\nSelect an item (number)")
            selection_idx = int(selection) - 1

            if selection_idx < 0 or selection_idx >= len(items):
                console.print("Invalid selection", style="red")
                return

            selected_item = items[selection_idx]

        except (ValueError, KeyboardInterrupt):
            console.print("\nCancelled", style="yellow")
            return

        # Handle selection based on type
        if selected_item["type"] == "worktree":
            # Show worktree options
            console.print(
                f"\nSelected worktree: {selected_item['branch']}", style="cyan"
            )
            console.print("Options:")
            console.print("  1. Show worktree path (for copying)")
            console.print("  2. Open in new tmux session")
            console.print("  3. View git diff")

            try:
                action = typer.prompt("Choose action (1-3)")

                if action == "1":
                    # Display path for easy copying
                    console.print("\nWorktree path:", style="bold")
                    console.print(f"{selected_item['path']}", style="green")
                    console.print(
                        f"Copy the path above to navigate to worktree: {selected_item['branch']}",
                        style="dim",
                    )

                elif action == "2":
                    # Create new tmux session and attach to it
                    try:
                        tmux_manager = TmuxManager()
                        session_manager = SessionLifecycleManager(tmux_manager)
                        session_name = session_manager.create_session_for_worktree(
                            Path(selected_item["path"]),
                            selected_item["branch"],
                            auto_attach=False,
                        )
                        if not session_name:
                            session_name = f"prunejuice-{selected_item['branch']}"
                        console.print(
                            f"Created tmux session: {session_name}", style="green"
                        )

                        # Immediately attach to the new session
                        console.print("Attaching to session...", style="dim")
                        success = session_manager.attach_to_session(session_name)
                        if success:
                            console.print(
                                f"Attached to session: {session_name}", style="green"
                            )
                        else:
                            console.print(
                                f"Created session but failed to attach. Run: tmux attach -t {session_name}",
                                style="yellow",
                            )
                    except Exception as e:
                        console.print(f"Failed to create session: {e}", style="red")

                elif action == "3":
                    # Show git diff options and display diff
                    try:
                        diff_choice = get_diff_type_menu()

                        git_manager = GitWorktreeManager(context["project_root"])
                        worktree_path = Path(selected_item["path"])

                        if diff_choice == "1":
                            # Compare against main branch
                            console.print(
                                "\nGenerating diff against main branch...", style="dim"
                            )
                            summary = git_manager.get_diff_summary(
                                worktree_path, "main"
                            )
                            display_diff_summary(summary)

                            if summary.get("has_changes"):
                                diff_text = git_manager.get_worktree_diff(
                                    worktree_path, "main"
                                )
                                display_diff_with_pager(
                                    diff_text,
                                    f"Diff: {selected_item['branch']} vs main",
                                )

                        elif diff_choice == "2":
                            # Compare against origin/main
                            console.print(
                                "\nGenerating diff against origin/main...", style="dim"
                            )
                            summary = git_manager.get_diff_summary(
                                worktree_path, "origin/main"
                            )
                            display_diff_summary(summary)

                            if summary.get("has_changes"):
                                diff_text = git_manager.get_worktree_diff(
                                    worktree_path, "origin/main"
                                )
                                display_diff_with_pager(
                                    diff_text,
                                    f"Diff: {selected_item['branch']} vs origin/main",
                                )

                        elif diff_choice == "3":
                            # Show staged changes only
                            console.print("\nShowing staged changes...", style="dim")
                            summary = git_manager.get_diff_summary(
                                worktree_path, staged_only=True
                            )
                            display_diff_summary(summary)

                            if summary.get("has_changes"):
                                diff_text = git_manager.get_worktree_diff(
                                    worktree_path, staged_only=True
                                )
                                display_diff_with_pager(
                                    diff_text,
                                    f"Staged changes: {selected_item['branch']}",
                                )

                        elif diff_choice == "4":
                            # Show unstaged changes only
                            console.print("\nShowing unstaged changes...", style="dim")
                            summary = git_manager.get_diff_summary(
                                worktree_path, unstaged_only=True
                            )
                            display_diff_summary(summary)

                            if summary.get("has_changes"):
                                diff_text = git_manager.get_worktree_diff(
                                    worktree_path, unstaged_only=True
                                )
                                display_diff_with_pager(
                                    diff_text,
                                    f"Unstaged changes: {selected_item['branch']}",
                                )

                        elif diff_choice == "5":
                            # Show working directory status
                            console.print(
                                "\nShowing working directory status...", style="dim"
                            )
                            status = git_manager.get_worktree_status(worktree_path)
                            display_worktree_status(status)

                        else:
                            console.print("Invalid diff choice", style="red")

                    except Exception as e:
                        display_diff_error(f"Failed to generate diff: {e}")

                else:
                    console.print("Invalid action", style="red")

            except (ValueError, KeyboardInterrupt):
                console.print("\nCancelled", style="yellow")
                return

        elif selected_item["type"] == "session":
            # Show session options
            console.print(f"\nSelected session: {selected_item['name']}", style="cyan")
            console.print("Options:")
            console.print("  1. Attach to session")
            if selected_item["path"]:
                console.print("  2. Show session path (for copying)")

            try:
                max_option = 2 if selected_item["path"] else 1
                action = typer.prompt(f"Choose action (1-{max_option})")

                if action == "1":
                    # Attach to session
                    try:
                        tmux_manager = TmuxManager()
                        session_manager = SessionLifecycleManager(tmux_manager)
                        success = session_manager.attach_to_session(
                            selected_item["name"]
                        )
                        if success:
                            console.print(
                                f"Attached to session: {selected_item['name']}",
                                style="green",
                            )
                        else:
                            console.print(
                                f"Failed to attach to session: {selected_item['name']}",
                                style="red",
                            )
                    except Exception as e:
                        console.print(f"Failed to attach: {e}", style="red")

                elif action == "2" and selected_item["path"]:
                    # Display path for easy copying
                    console.print("\nSession path:", style="bold")
                    console.print(f"{selected_item['path']}", style="green")
                    console.print(
                        "Copy the path above to navigate to session directory",
                        style="dim",
                    )

                else:
                    console.print("Invalid action", style="red")

            except (ValueError, KeyboardInterrupt):
                console.print("\nCancelled", style="yellow")
                return

    except Exception as e:
        console.print(f"❌ Error in resume command: {e}", style="bold red")
        raise typer.Exit(code=1)


@app.command()
def start(
    name: str = typer.Argument(help="Name for the worktree and branch"),
    base_branch: str = typer.Option(
        "main", "--base", "-b", help="Base branch to create worktree from"
    ),
    no_attach: bool = typer.Option(
        False, "--no-attach", help="Create without attaching to tmux session"
    ),
):
    """Create a worktree and start a tmux session in it."""
    try:
        console.print(
            f"🚀 Starting new development environment: [bold cyan]{name}[/bold cyan]"
        )

        # Get project context
        context = _get_project_context()
        if not context["is_git_repo"]:
            console.print("❌ Not in a Git repository", style="bold red")
            raise typer.Exit(code=1)

        project_root = context["project_root"]

        # Create worktree
        console.print(f"Creating worktree '{name}' from '{base_branch}'...")
        git_manager = GitWorktreeManager(project_root)

        # Create worktree
        try:
            worktree_path = git_manager.create_worktree(name, base_branch)
            console.print(f"✅ Worktree created at: {worktree_path}", style="green")
        except Exception as e:
            console.print(f"❌ Failed to create worktree: {e}", style="bold red")
            raise typer.Exit(code=1)

        # Create tmux session
        console.print(f"Creating tmux session for '{name}'...")
        try:
            tmux_manager = TmuxManager()
            session_manager = SessionLifecycleManager(tmux_manager)

            session_name = session_manager.create_session_for_worktree(
                worktree_path, name, auto_attach=False
            )

            if not session_name:
                session_name = f"prunejuice-{name}"

            console.print(f"✅ Session created: {session_name}", style="green")

            # Attach to session if requested
            if not no_attach:
                console.print("Attaching to session...", style="dim")
                success = session_manager.attach_to_session(session_name)
                if success:
                    console.print(
                        f"✅ Attached to session: {session_name}", style="bold green"
                    )
                else:
                    console.print(
                        f"⚠️  Session created but attachment failed. Run: tmux attach -t {session_name}",
                        style="yellow",
                    )
            else:
                console.print(
                    f"Session ready. Attach with: tmux attach -t {session_name}",
                    style="dim",
                )

        except Exception as e:
            console.print(f"❌ Failed to create session: {e}", style="bold red")
            # Clean up worktree if session creation failed
            try:
                git_manager.remove_worktree(name)
                console.print("Cleaned up worktree after session failure", style="dim")
            except Exception:
                pass
            raise typer.Exit(code=1)

        console.print(
            f"🎉 Development environment '{name}' is ready!", style="bold green"
        )

    except Exception as e:
        console.print(
            f"❌ Error starting development environment: {e}", style="bold red"
        )
        raise typer.Exit(code=1)


@app.command()
def cleanup(
    days: int = typer.Option(30, help="Clean up artifacts older than N days"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
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

        console.print(
            f"✅ Cleaned up artifacts older than {days} days", style="bold green"
        )

    except Exception as e:
        console.print(f"❌ Error during cleanup: {e}", style="bold red")
        raise typer.Exit(code=1)


@app.command()
def history(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of events to show"),
    status: Optional[str] = typer.Option(
        None, "--status", help="Filter by status (completed, failed, running)"
    ),
    command: Optional[str] = typer.Option(
        None, "--command", help="Filter by command name"
    ),
    worktree: Optional[str] = typer.Option(
        None, "--worktree", help="Filter by worktree name"
    ),
    project: bool = typer.Option(
        False, "--project", help="Filter to current project only"
    ),
    all_worktrees: bool = typer.Option(
        False,
        "-a",
        "--all",
        help="Show events from all worktrees (default: current worktree only when in worktree)",
    ),
):
    """Show command execution history with filtering options."""
    try:
        # Get project and worktree context
        context = _get_project_context()
        settings = Settings(project_path=context["project_root"])
        db = Database(settings.db_path)

        # Get project filter if requested
        project_filter = str(Path.cwd()) if project else None

        # Determine worktree filtering
        worktree_filter = worktree  # Start with explicit --worktree flag
        if (
            worktree_filter is None
            and not all_worktrees
            and context["current_worktree"]
            and not context["current_worktree"]["is_main"]
        ):
            # Auto-filter to current worktree only when not explicitly overridden
            worktree_filter = context["current_worktree"]["branch"]

        events = asyncio.run(
            db.get_events(
                limit=limit,
                status=status,
                command=command,
                worktree=worktree_filter,
                project_path=project_filter,
            )
        )

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

            # Display project-worktree combination if worktree exists
            project_name = Path(event.project_path).name
            if event.worktree_name:
                project_display = f"{project_name}-{event.worktree_name}"
            else:
                project_display = project_name

            table.add_row(
                str(event.id),
                event.command,
                f"[{status_style}]{event.status}[/{status_style}]",
                event.start_time.strftime("%m/%d %H:%M"),
                duration_str,
                project_display,
            )

        console.print(table)

    except Exception as e:
        console.print(f"❌ Error fetching history: {e}", style="bold red")
        raise typer.Exit(code=1)


@app.command()
def tui(
    path: Optional[Path] = typer.Option(
        None, "--path", "-p", help="Path to project (defaults to current directory)"
    ),
):
    """Launch the interactive TUI for worktree management."""
    try:
        from prunejuice.tui import PrunejuiceApp

        # Get project path - use current directory by default to support worktrees
        project_path = path or Path.cwd()

        # Create and run the TUI app
        tui_app = PrunejuiceApp(project_path=project_path)
        tui_app.run()

    except ImportError:
        console.print(
            "❌ TUI dependencies not installed. Please install with: pip install textual",
            style="bold red",
        )
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"❌ Error launching TUI: {e}", style="bold red")
        raise typer.Exit(code=1)


@app.command()
def tui_session(
    path: Optional[Path] = typer.Option(
        None, "--path", "-p", help="Path to project (defaults to current directory)"
    ),
):
    """Launch the TUI in a dedicated tmux session with seamless worktree switching."""
    try:
        from prunejuice.tui import PrunejuiceApp

        # Get working directory (where we're running from, not project root)
        working_dir = path or Path.cwd()
        # Get project name from the detected project root for session naming
        project_root = ProjectPathResolver.get_project_root()
        project_name = project_root.name

        # Create session manager
        tmux_manager = TmuxManager()

        # Check if tmux is available
        if not tmux_manager.check_tmux_available():
            console.print("❌ tmux is not available. Please install tmux first.", style="bold red")
            raise typer.Exit(code=1)

        # Generate TUI session name
        tui_session_name = f"{project_name}-tui"

        # Check if we're already in the TUI session
        current_session = None
        if os.getenv("TMUX"):
            try:
                result = subprocess.run(
                    ["tmux", "display-message", "-p", "#S"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                if result.returncode == 0:
                    current_session = result.stdout.decode().strip()
            except Exception:
                pass

        if current_session == tui_session_name:
            # Already in TUI session, just run the app
            tui_app = PrunejuiceApp(project_path=working_dir)
            tui_app.run()
        else:
            # Create or attach to TUI session
            if tmux_manager.session_exists(tui_session_name):
                console.print(f"📺 Attaching to existing TUI session: {tui_session_name}", style="green")
                os.execvp("tmux", ["tmux", "attach-session", "-t", tui_session_name])
            else:
                console.print(f"📺 Creating new TUI session: {tui_session_name}", style="green")
                # Create the session in the current working directory
                success = tmux_manager.create_session(tui_session_name, working_dir, auto_attach=False)
                if success:
                    # Set the session title and hide status bar
                    subprocess.run([
                        "tmux", "set-option", "-t", tui_session_name,
                        "set-titles-string", "PRUNEJUICE TUI"
                    ], check=False)
                    subprocess.run([
                        "tmux", "set-option", "-t", tui_session_name,
                        "status", "off"
                    ], check=False)
                    # Send the TUI command to the session (will run from working_dir)
                    # Use cd to ensure we're in the right directory and then run the command
                    subprocess.run([
                        "tmux", "send-keys", "-t", tui_session_name,
                        f"cd {working_dir} && uv run prj tui", "Enter"
                    ], check=False)
                    # Attach to the session
                    os.execvp("tmux", ["tmux", "attach-session", "-t", tui_session_name])
                else:
                    console.print("❌ Failed to create TUI session", style="bold red")
                    raise typer.Exit(code=1)

    except ImportError:
        console.print(
            "❌ TUI dependencies not installed. Please install with: pip install textual",
            style="bold red",
        )
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"❌ Error launching TUI session: {e}", style="bold red")
        raise typer.Exit(code=1)


@app.command()
def show(event_id: int = typer.Argument(..., help="The ID of the event to show")):
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

        panel = Panel(
            text, title=f"Event Details (ID: {event.id})", border_style="blue"
        )
        console.print(panel)

    except Exception as e:
        console.print(f"❌ Error showing event: {e}", style="bold red")
        raise typer.Exit(code=1)


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
