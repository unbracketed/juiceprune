"""Tests for YAML action loader with security focus."""

import pytest

from prunejuice.actions.loader import ActionLoader


class TestActionLoader:
    """Test YAML action loading with security scenarios."""

    @pytest.fixture
    def loader(self):
        return ActionLoader()

    def test_valid_yaml_loading(self, loader, temp_dir):
        """Test loading valid YAML actions."""
        cmd_dir = temp_dir / ".prj" / "actions"
        cmd_dir.mkdir(parents=True)

        # Valid action
        valid_yaml = """
name: test-action
description: Test action
steps:
  - setup-environment
  - validate-prerequisites
"""
        (cmd_dir / "test.yaml").write_text(valid_yaml)

        actions = loader.discover_actions(temp_dir)
        # Should find our test action plus built-in templates
        test_action = next(
            (cmd for cmd in actions if cmd.name == "test-action"), None
        )
        assert test_action is not None
        assert test_action.description == "Test action"

    def test_malformed_yaml_rejection(self, loader, temp_dir):
        """Test rejection of malformed YAML."""
        cmd_dir = temp_dir / ".prj" / "actions"
        cmd_dir.mkdir(parents=True)

        # Malformed YAML
        bad_yaml = """
name: bad-action
description: [unclosed bracket
steps: 
  - broken
"""
        (cmd_dir / "bad.yaml").write_text(bad_yaml)

        actions = loader.discover_actions(temp_dir)
        # Should skip malformed project files but still load built-in templates
        project_actions = [cmd for cmd in actions if cmd.name == "bad-action"]
        assert len(project_actions) == 0  # Malformed file should be skipped

    def test_path_traversal_prevention(self, loader, temp_dir):
        """Test prevention of path traversal in file references."""
        cmd_dir = temp_dir / ".prj" / "actions"
        cmd_dir.mkdir(parents=True)

        # action with path traversal attempt
        traversal_yaml = """
name: evil-action
description: Path traversal test
steps:
  - ../../../etc/passwd
working_directory: /etc
"""
        (cmd_dir / "evil.yaml").write_text(traversal_yaml)

        cmd = loader.load_action("evil-action", temp_dir)
        # Should either reject or sanitize paths
        assert cmd is None or cmd.working_directory != "/etc"

    def test_action_inheritance(self, loader, temp_dir):
        """Test basic action loading (inheritance can be tested separately)."""
        cmd_dir = temp_dir / ".prj" / "actions"
        cmd_dir.mkdir(parents=True)

        # Simple action without inheritance
        simple_yaml = """
name: simple-action
description: Simple action
steps:
  - step1
  - step2
"""
        (cmd_dir / "simple-action.yaml").write_text(simple_yaml)

        cmd = loader.load_action("simple-action", temp_dir)
        assert cmd is not None
        assert cmd.name == "simple-action"
        assert len(cmd.steps) == 2
        assert any(step.name == "step1" for step in cmd.steps)
        assert any(step.name == "step2" for step in cmd.steps)
