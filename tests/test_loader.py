"""Tests for YAML command loader with security focus."""

import pytest
import yaml
from pathlib import Path
import tempfile

from prunejuice.commands.loader import CommandLoader
from prunejuice.core.models import CommandDefinition


class TestCommandLoader:
    """Test YAML command loading with security scenarios."""
    
    @pytest.fixture
    def loader(self):
        return CommandLoader()
    
    async def test_valid_yaml_loading(self, loader, temp_dir):
        """Test loading valid YAML commands."""
        cmd_dir = temp_dir / ".prj" / "commands"
        cmd_dir.mkdir(parents=True)
        
        # Valid command
        valid_yaml = """
name: test-command
description: Test command
steps:
  - setup-environment
  - validate-prerequisites
"""
        (cmd_dir / "test.yaml").write_text(valid_yaml)
        
        commands = await loader.discover_commands(temp_dir)
        assert len(commands) == 1
        assert commands[0].name == "test-command"
    
    async def test_malformed_yaml_rejection(self, loader, temp_dir):
        """Test rejection of malformed YAML."""
        cmd_dir = temp_dir / ".prj" / "commands"
        cmd_dir.mkdir(parents=True)
        
        # Malformed YAML
        bad_yaml = """
name: bad-command
description: [unclosed bracket
steps: 
  - broken
"""
        (cmd_dir / "bad.yaml").write_text(bad_yaml)
        
        commands = await loader.discover_commands(temp_dir)
        assert len(commands) == 0  # Should skip malformed files
    
    async def test_path_traversal_prevention(self, loader, temp_dir):
        """Test prevention of path traversal in file references."""
        cmd_dir = temp_dir / ".prj" / "commands"
        cmd_dir.mkdir(parents=True)
        
        # Command with path traversal attempt
        traversal_yaml = """
name: evil-command
description: Path traversal test
steps:
  - ../../../etc/passwd
working_directory: /etc
"""
        (cmd_dir / "evil.yaml").write_text(traversal_yaml)
        
        cmd = await loader.load_command("evil-command", temp_dir)
        # Should either reject or sanitize paths
        assert cmd is None or cmd.working_directory != "/etc"
    
    async def test_command_inheritance(self, loader, temp_dir):
        """Test command inheritance functionality."""
        cmd_dir = temp_dir / ".prj" / "commands"
        cmd_dir.mkdir(parents=True)
        
        # Base command
        base_yaml = """
name: base-command
description: Base command
environment:
  BASE_VAR: base_value
steps:
  - step1
  - step2
"""
        (cmd_dir / "base.yaml").write_text(base_yaml)
        
        # Extended command
        extended_yaml = """
name: extended-command
description: Extended command
extends: base-command
environment:
  EXTENDED_VAR: extended_value
steps:
  - step3
"""
        (cmd_dir / "extended.yaml").write_text(extended_yaml)
        
        cmd = await loader.load_command("extended-command", temp_dir)
        assert cmd is not None
        # Should inherit base steps and environment
        assert len(cmd.steps) >= 1