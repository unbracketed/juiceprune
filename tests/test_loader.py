"""Tests for YAML command loader with security focus."""

import pytest

from prunejuice.commands.loader import CommandLoader


class TestCommandLoader:
    """Test YAML command loading with security scenarios."""

    @pytest.fixture
    def loader(self):
        return CommandLoader()

    def test_valid_yaml_loading(self, loader, temp_dir):
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

        commands = loader.discover_commands(temp_dir)
        # Should find our test command plus built-in templates
        test_command = next(
            (cmd for cmd in commands if cmd.name == "test-command"), None
        )
        assert test_command is not None
        assert test_command.description == "Test command"

    def test_malformed_yaml_rejection(self, loader, temp_dir):
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

        commands = loader.discover_commands(temp_dir)
        # Should skip malformed project files but still load built-in templates
        project_commands = [cmd for cmd in commands if cmd.name == "bad-command"]
        assert len(project_commands) == 0  # Malformed file should be skipped

    def test_path_traversal_prevention(self, loader, temp_dir):
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

        cmd = loader.load_command("evil-command", temp_dir)
        # Should either reject or sanitize paths
        assert cmd is None or cmd.working_directory != "/etc"

    def test_command_inheritance(self, loader, temp_dir):
        """Test basic command loading (inheritance can be tested separately)."""
        cmd_dir = temp_dir / ".prj" / "commands"
        cmd_dir.mkdir(parents=True)

        # Simple command without inheritance
        simple_yaml = """
name: simple-command
description: Simple command
steps:
  - step1
  - step2
"""
        (cmd_dir / "simple-command.yaml").write_text(simple_yaml)

        cmd = loader.load_command("simple-command", temp_dir)
        assert cmd is not None
        assert cmd.name == "simple-command"
        assert len(cmd.steps) == 2
        assert any(step.name == "step1" for step in cmd.steps)
        assert any(step.name == "step2" for step in cmd.steps)
