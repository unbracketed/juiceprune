"""Worktree management commands for PruneJuice CLI."""

import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from pathlib import Path
from typing import Optional, List

from ..worktree_utils import (
    GitWorktreeManager, 
    FileManager, 
    WorktreeOperations,
    CommitStatusAnalyzer,
    InteractiveStaging,
    CommitMessageEditor,
)
from ..worktree_utils.operations import OperationResult
from ..core.config import Settings

console = Console()

# Create worktree subcommand app
worktree_app = typer.Typer(
    name="worktree",
    help="Manage git worktrees using plum integration",
    rich_markup_mode="rich",
)


@worktree_app.command()
def list(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed worktree info"
    ),
):
    """List all worktrees for the current project."""
    try:
        git_manager = GitWorktreeManager(Path.cwd())

        console.print("🌳 Listing worktrees...", style="bold green")

        worktrees = git_manager.list_worktrees()

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
    base_branch: Optional[str] = typer.Option(
        None, "--base", "-b", help="Base branch to create from"
    ),
):
    """Create a new worktree with the specified branch."""
    try:
        git_manager = GitWorktreeManager(Path.cwd())
        file_manager = FileManager(Path.cwd())

        console.print(
            f"🌱 Creating worktree for branch: [bold cyan]{branch_name}[/bold cyan]"
        )

        # Get settings and base_dir
        settings = Settings()

        # Create the worktree
        worktree_path = git_manager.create_worktree(
            branch_name, base_branch or "main", parent_dir=settings.base_dir
        )

        # Copy default files to the new worktree
        default_files = file_manager.get_default_files_to_copy()
        file_manager.copy_files(worktree_path, default_files)

        # Handle MCP templates if they exist
        file_manager.handle_mcp_templates(worktree_path)

        console.print(
            f"✅ Worktree created at: [bold green]{worktree_path}[/bold green]"
        )

    except Exception as e:
        console.print(f"❌ Error creating worktree: {e}", style="bold red")
        raise typer.Exit(code=1)


@worktree_app.command()
def remove(
    worktree_path: str = typer.Argument(help="Path to the worktree to remove"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force removal without confirmation"
    ),
):
    """Remove an existing worktree."""
    try:
        git_manager = GitWorktreeManager(Path.cwd())

        worktree_path_obj = Path(worktree_path)

        if not force:
            response = typer.confirm(f"Remove worktree at {worktree_path}?")
            if not response:
                console.print("Operation cancelled", style="yellow")
                return

        console.print(
            f"🗑️  Removing worktree: [bold yellow]{worktree_path}[/bold yellow]"
        )

        success = git_manager.remove_worktree(worktree_path_obj)

        if success:
            console.print("✅ Worktree removed successfully", style="bold green")
        else:
            console.print("❌ Failed to remove worktree", style="bold red")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"❌ Error removing worktree: {e}", style="bold red")
        raise typer.Exit(code=1)


@worktree_app.command()
def commit(
    worktree_path: str = typer.Argument(help="Path to the worktree"),
    message: Optional[str] = typer.Option(
        None, "--message", "-m", help="Commit message"
    ),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", help="Use interactive mode"
    ),
    all: bool = typer.Option(
        False, "--all", "-a", help="Stage all changes before committing"
    ),
    files: Optional[List[str]] = typer.Option(
        None, "--file", "-f", help="Specific files to stage and commit"
    ),
    template: Optional[str] = typer.Option(
        None, "--template", "-t", help="Commit message template"
    ),
    conventional: bool = typer.Option(
        False, "--conventional", "-c", help="Use conventional commit format"
    ),
):
    """Commit changes in a worktree with interactive staging and message editing."""
    try:
        worktree_path_obj = Path(worktree_path)
        
        if not worktree_path_obj.exists():
            console.print(f"❌ Worktree path does not exist: {worktree_path}", style="bold red")
            raise typer.Exit(code=1)

        operations = WorktreeOperations(Path.cwd())
        
        # Show current status
        analyzer = CommitStatusAnalyzer(worktree_path_obj)
        analysis = analyzer.analyze()
        
        console.print(f"📊 Commit Status for [bold cyan]{worktree_path}[/bold cyan]")
        _display_commit_status(analysis)

        if analysis.has_conflicts:
            console.print("❌ Cannot commit with merge conflicts", style="bold red")
            raise typer.Exit(code=1)

        # Handle file staging
        staging = InteractiveStaging(worktree_path_obj)
        
        if all:
            console.print("📥 Staging all changes...")
            success = asyncio.run(staging.stage_all_changes())
            if not success:
                console.print("❌ Failed to stage all changes", style="bold red")
                raise typer.Exit(code=1)
        elif files:
            console.print(f"📥 Staging {len(files)} specific files...")
            success = asyncio.run(staging.stage_files(files))
            if not success:
                console.print("❌ Failed to stage specified files", style="bold red")
                raise typer.Exit(code=1)

        # Handle commit message
        if not message and interactive:
            editor = CommitMessageEditor(worktree_path_obj)
            
            if conventional:
                template = editor.generate_conventional_commit_template()
            
            console.print("✏️  Opening editor for commit message...")
            message = asyncio.run(editor.get_commit_message_interactive(template))
            
            if not message:
                console.print("❌ Commit cancelled - no message provided", style="yellow")
                raise typer.Exit(code=0)

        if not message:
            console.print("❌ No commit message provided", style="bold red")
            raise typer.Exit(code=1)

        # Validate commit message
        editor = CommitMessageEditor(worktree_path_obj)
        is_valid, error = editor.validate_commit_message(message)
        if not is_valid:
            console.print(f"❌ Invalid commit message: {error}", style="bold red")
            raise typer.Exit(code=1)

        # Perform the commit
        console.print("💾 Committing changes...")
        result = asyncio.run(operations.commit_changes(
            worktree_path_obj,
            message=message,
            interactive=False,  # Already handled interactivity
            stage_all=False,    # Already handled staging
        ))

        if result.status == OperationResult.SUCCESS:
            hash_display = result.commit_hash[:8] if result.commit_hash else "unknown"
            console.print(f"✅ Successfully committed: [bold green]{hash_display}[/bold green]")
            console.print(f"📝 Message: {result.message}")
            files_count = len(result.files_committed) if result.files_committed else 0
            console.print(f"📁 Files committed: {files_count}")
        else:
            console.print(f"❌ Commit failed: {result.error}", style="bold red")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"❌ Error during commit: {e}", style="bold red")
        raise typer.Exit(code=1)


@worktree_app.command()
def merge(
    worktree_path: str = typer.Argument(help="Path to the worktree to merge"),
    target_branch: Optional[str] = typer.Option(
        None, "--target", "-t", help="Target branch to merge into"
    ),
    delete_after: bool = typer.Option(
        False, "--delete", "-d", help="Delete worktree after successful merge"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force merge without confirmation"
    ),
):
    """Merge worktree branch to parent branch."""
    try:
        worktree_path_obj = Path(worktree_path)
        
        if not worktree_path_obj.exists():
            console.print(f"❌ Worktree path does not exist: {worktree_path}", style="bold red")
            raise typer.Exit(code=1)

        operations = WorktreeOperations(Path.cwd())
        
        # Show confirmation unless force is specified
        if not force:
            merge_target = target_branch or "auto-detected parent"
            response = typer.confirm(
                f"Merge worktree at {worktree_path} into {merge_target}?"
            )
            if not response:
                console.print("Operation cancelled", style="yellow")
                return

        console.print(f"🔀 Merging worktree: [bold cyan]{worktree_path}[/bold cyan]")
        
        result = asyncio.run(operations.merge_to_parent(
            worktree_path_obj,
            delete_after=delete_after,
            target_branch=target_branch
        ))

        if result.status == OperationResult.SUCCESS:
            console.print(f"✅ Successfully merged into [bold green]{result.target_branch}[/bold green]")
            merge_hash = result.merge_commit[:8] if result.merge_commit else "unknown"
            console.print(f"📝 Merge commit: {merge_hash}")
        elif result.status == OperationResult.CONFLICT:
            console.print(f"⚠️  Merge conflicts detected in [bold yellow]{result.target_branch}[/bold yellow]")
            console.print("📋 Conflicted files:")
            for conflict in (result.conflicts or []):
                console.print(f"  - {conflict}")
            console.print("🔧 Resolve conflicts manually and run 'git commit' to complete the merge")
        else:
            console.print(f"❌ Merge failed: {result.error}", style="bold red")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"❌ Error during merge: {e}", style="bold red")
        raise typer.Exit(code=1)


@worktree_app.command("pull-request")
def pull_request(
    worktree_path: str = typer.Argument(help="Path to the worktree"),
    title: Optional[str] = typer.Option(
        None, "--title", "-t", help="Pull request title"
    ),
    body: Optional[str] = typer.Option(
        None, "--body", "-b", help="Pull request body"
    ),
    draft: bool = typer.Option(
        False, "--draft", "-d", help="Create as draft pull request"
    ),
):
    """Create a pull request for the worktree branch."""
    try:
        worktree_path_obj = Path(worktree_path)
        
        if not worktree_path_obj.exists():
            console.print(f"❌ Worktree path does not exist: {worktree_path}", style="bold red")
            raise typer.Exit(code=1)

        operations = WorktreeOperations(Path.cwd())
        
        console.print(f"🔗 Creating pull request for: [bold cyan]{worktree_path}[/bold cyan]")
        
        result = asyncio.run(operations.create_pull_request(
            worktree_path_obj,
            title=title,
            body=body,
            draft=draft
        ))

        if result.status == OperationResult.SUCCESS:
            console.print("✅ Pull request created successfully!")
            console.print(f"🔗 URL: [bold blue]{result.pr_url}[/bold blue]")
            if result.pr_number:
                console.print(f"📝 PR Number: #{result.pr_number}")
        else:
            console.print(f"❌ Failed to create pull request: {result.error}", style="bold red")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"❌ Error creating pull request: {e}", style="bold red")
        raise typer.Exit(code=1)


@worktree_app.command()
def delete(
    worktree_path: str = typer.Argument(help="Path to the worktree to delete"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force deletion without confirmation"
    ),
    cleanup_sessions: bool = typer.Option(
        True, "--cleanup-sessions/--no-cleanup-sessions", 
        help="Cleanup associated tmux sessions"
    ),
):
    """Delete a worktree and perform cleanup."""
    try:
        worktree_path_obj = Path(worktree_path)
        
        if not worktree_path_obj.exists():
            console.print(f"❌ Worktree path does not exist: {worktree_path}", style="bold red")
            raise typer.Exit(code=1)

        operations = WorktreeOperations(Path.cwd())
        
        # Show confirmation unless force is specified
        if not force:
            response = typer.confirm(f"Delete worktree at {worktree_path}?")
            if not response:
                console.print("Operation cancelled", style="yellow")
                return

        console.print(f"🗑️  Deleting worktree: [bold yellow]{worktree_path}[/bold yellow]")
        
        result = asyncio.run(operations.delete_worktree(
            worktree_path_obj,
            force=force,
            cleanup_sessions=cleanup_sessions
        ))

        if result.status == OperationResult.SUCCESS:
            console.print("✅ Successfully deleted worktree")
            if result.cleanup_performed:
                console.print("🧹 Cleaned up associated tmux sessions")
        else:
            console.print(f"❌ Delete failed: {result.error}", style="bold red")
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"❌ Error deleting worktree: {e}", style="bold red")
        raise typer.Exit(code=1)


@worktree_app.command()
def status(
    worktree_path: str = typer.Argument(help="Path to the worktree"),
    show_diff: bool = typer.Option(
        False, "--diff", "-d", help="Show diff of changes"
    ),
):
    """Show detailed status of a worktree."""
    try:
        worktree_path_obj = Path(worktree_path)
        
        if not worktree_path_obj.exists():
            console.print(f"❌ Worktree path does not exist: {worktree_path}", style="bold red")
            raise typer.Exit(code=1)

        analyzer = CommitStatusAnalyzer(worktree_path_obj)
        analysis = analyzer.analyze()
        
        console.print(f"📊 Status for [bold cyan]{worktree_path}[/bold cyan]")
        _display_commit_status(analysis)

        if show_diff:
            staging = InteractiveStaging(worktree_path_obj)
            
            # Show staged diff
            if analysis.staged_files:
                console.print("\n📝 [bold green]Staged Changes:[/bold green]")
                for file_info in analysis.staged_files[:5]:  # Limit to first 5
                    diff = staging.get_file_diff(file_info.path, staged=True, context_lines=2)
                    if diff:
                        console.print(Panel(diff, title=f"📄 {file_info.path}", expand=False))

            # Show unstaged diff
            if analysis.unstaged_files:
                console.print("\n📝 [bold yellow]Unstaged Changes:[/bold yellow]")
                for file_info in analysis.unstaged_files[:5]:  # Limit to first 5
                    diff = staging.get_file_diff(file_info.path, staged=False, context_lines=2)
                    if diff:
                        console.print(Panel(diff, title=f"📄 {file_info.path}", expand=False))

    except Exception as e:
        console.print(f"❌ Error getting worktree status: {e}", style="bold red")
        raise typer.Exit(code=1)


def _display_commit_status(analysis):
    """Display commit status in a formatted table."""
    # Create status overview
    status_text = Text()
    status_text.append("Branch: ", style="bold")
    status_text.append(f"{analysis.current_branch}\n", style="cyan")
    status_text.append("Total changes: ", style="bold")
    status_text.append(f"{analysis.total_changes}\n", style="white")
    status_text.append("Can commit: ", style="bold")
    status_text.append("✅ Yes" if analysis.can_commit else "❌ No", 
                      style="green" if analysis.can_commit else "red")
    
    if analysis.has_conflicts:
        status_text.append("\n", style="white")
        status_text.append("⚠️  Has conflicts", style="bold red")

    console.print(Panel(status_text, title="📋 Overview", expand=False))

    # Create files table
    if analysis.total_changes > 0:
        table = Table(title="📁 File Changes")
        table.add_column("Status", style="bold", width=8)
        table.add_column("Type", width=10)
        table.add_column("File", style="cyan")
        table.add_column("Changes", width=12)

        # Add staged files
        for file_info in analysis.staged_files:
            changes = ""
            if file_info.lines_added is not None and file_info.lines_removed is not None:
                changes = f"+{file_info.lines_added} -{file_info.lines_removed}"
            
            table.add_row(
                file_info.status.value,
                "[green]Staged[/green]",
                file_info.path,
                changes
            )

        # Add unstaged files
        for file_info in analysis.unstaged_files:
            changes = ""
            if file_info.lines_added is not None and file_info.lines_removed is not None:
                changes = f"+{file_info.lines_added} -{file_info.lines_removed}"
            
            table.add_row(
                file_info.status.value,
                "[yellow]Unstaged[/yellow]",
                file_info.path,
                changes
            )

        # Add untracked files
        for file_info in analysis.untracked_files:
            table.add_row(
                "?",
                "[blue]Untracked[/blue]",
                file_info.path,
                ""
            )

        console.print(table)
    else:
        console.print("✨ Working directory is clean", style="green")
