"""Tests for CLI interface."""

import pytest
from typer.testing import CliRunner
from pathlib import Path
import yaml

from prunejuice.cli import app
from prunejuice.core.models import CommandDefinition


runner = CliRunner()


def test_init_command(temp_dir):
    """Test project initialization."""
    # Change to temp directory
    original_cwd = Path.cwd()
    import os
    os.chdir(temp_dir)
    
    try:
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert "Project initialized successfully" in result.stdout
        
        # Verify project structure
        assert (temp_dir / ".prj").exists()
        assert (temp_dir / ".prj" / "commands").exists()
        assert (temp_dir / ".prj" / "steps").exists()
        assert (temp_dir / ".prj" / "configs").exists()
        
    finally:
        os.chdir(original_cwd)


def test_list_commands_empty(temp_dir):
    """Test listing commands in empty project."""
    original_cwd = Path.cwd()
    import os
    os.chdir(temp_dir)
    
    try:
        result = runner.invoke(app, ["list-commands"])
        assert result.exit_code == 0
        assert "No commands found" in result.stdout
        
    finally:
        os.chdir(original_cwd)


def test_list_commands_with_commands(test_project):
    """Test listing commands when commands exist."""
    # Create a test command
    sample_command = CommandDefinition(
        name="test-cmd",
        description="Test command",
        category="test",
        steps=["setup-environment"]
    )
    
    cmd_file = test_project / ".prj" / "commands" / "test-cmd.yaml"
    with open(cmd_file, 'w') as f:
        yaml.dump(sample_command.model_dump(), f)
    
    original_cwd = Path.cwd()
    import os
    os.chdir(test_project)
    
    try:
        result = runner.invoke(app, ["list-commands"])
        assert result.exit_code == 0
        assert "test-cmd" in result.stdout
        assert "Test command" in result.stdout
        
    finally:
        os.chdir(original_cwd)


def test_run_command_missing_args(test_project):
    """Test running command with missing arguments."""
    # Create a command that requires arguments
    sample_command = CommandDefinition(
        name="arg-cmd",
        description="Command with args",
        arguments=[{"name": "required_arg", "required": True}],
        steps=["setup-environment"]
    )
    
    cmd_file = test_project / ".prj" / "commands" / "arg-cmd.yaml"
    with open(cmd_file, 'w') as f:
        yaml.dump(sample_command.model_dump(), f)
    
    original_cwd = Path.cwd()
    import os
    os.chdir(test_project)
    
    try:
        result = runner.invoke(app, ["run", "arg-cmd"])
        assert result.exit_code == 1
        assert "Required argument" in result.stdout
        
    finally:
        os.chdir(original_cwd)


def test_run_nonexistent_command(test_project):
    """Test running non-existent command."""
    original_cwd = Path.cwd()
    import os
    os.chdir(test_project)
    
    try:
        result = runner.invoke(app, ["run", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.stdout
        
    finally:
        os.chdir(original_cwd)


def test_dry_run(test_project):
    """Test dry run functionality."""
    sample_command = CommandDefinition(
        name="dry-test",
        description="Dry run test",
        steps=["setup-environment"]
    )
    
    cmd_file = test_project / ".prj" / "commands" / "dry-test.yaml"
    with open(cmd_file, 'w') as f:
        yaml.dump(sample_command.model_dump(), f)
    
    original_cwd = Path.cwd()
    import os
    os.chdir(test_project)
    
    try:
        result = runner.invoke(app, ["run", "dry-test", "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run for command" in result.stdout
        
    finally:
        os.chdir(original_cwd)


def test_status_command(test_project):
    """Test status command."""
    original_cwd = Path.cwd()
    import os
    os.chdir(test_project)
    
    try:
        # First initialize the project
        runner.invoke(app, ["init"])
        
        # Then check status
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "Project Status" in result.stdout
        
    finally:
        os.chdir(original_cwd)


def test_invalid_argument_format(test_project):
    """Test handling of invalid argument format."""
    sample_command = CommandDefinition(
        name="arg-test",
        description="Test args",
        steps=["setup-environment"]
    )
    
    cmd_file = test_project / ".prj" / "commands" / "arg-test.yaml"
    with open(cmd_file, 'w') as f:
        yaml.dump(sample_command.model_dump(), f)
    
    original_cwd = Path.cwd()
    import os
    os.chdir(test_project)
    
    try:
        # Invalid argument format (no = sign)
        result = runner.invoke(app, ["run", "arg-test", "invalid_arg"])
        assert result.exit_code == 1
        assert "Invalid argument format" in result.stdout
        
    finally:
        os.chdir(original_cwd)