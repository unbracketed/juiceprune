"""Smoke tests for basic PruneJuice functionality."""

from typer.testing import CliRunner
from pathlib import Path

from prunejuice.cli import app


class TestSmoke:
    """Basic smoke tests to ensure core functionality works."""
    
    def test_full_workflow(self, temp_dir):
        """Test basic workflow: init -> list -> run."""
        runner = CliRunner()
        
        with runner.isolated_filesystem(temp_dir=temp_dir):
            # Initialize project
            result = runner.invoke(app, ["init"])
            assert result.exit_code == 0
            assert Path(".prj").exists()
            
            # List commands
            result = runner.invoke(app, ["list-commands"])
            assert result.exit_code == 0
            assert "echo-hello" in result.stdout
            
            # Run simple command
            result = runner.invoke(app, ["run", "echo-hello"])
            assert result.exit_code == 0
            assert "Command completed successfully" in result.stdout
    
    def test_help_available(self):
        """Ensure help is available for all commands."""
        runner = CliRunner()
        commands = ["init", "list-commands", "run", "status"]
        
        for cmd in commands:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0
            assert "help" in result.stdout.lower()