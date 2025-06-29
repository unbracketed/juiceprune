"""Tests for step models and execution types."""

import pytest
from prunejuice.core.models import CommandStep, StepType, CommandDefinition


class TestCommandStep:
    """Test CommandStep model functionality."""
    
    def test_step_from_string_builtin(self):
        """Test creating builtin step from string."""
        step = CommandStep.from_string("setup-environment")
        assert step.name == "setup-environment"
        assert step.type == StepType.BUILTIN
        assert step.action == "setup-environment"
    
    def test_step_from_string_shell(self):
        """Test creating shell step from string."""
        step = CommandStep.from_string("echo hello world")
        assert step.name == "echo hello world"
        assert step.type == StepType.SHELL
        assert step.action == "echo hello world"
    
    def test_step_from_string_script(self):
        """Test creating script step from string."""
        step = CommandStep.from_string("setup.sh")
        assert step.name == "setup.sh"
        assert step.type == StepType.SCRIPT
        assert step.action == "setup.sh"
    
    def test_step_serialization(self):
        """Test step serialization to dict."""
        step = CommandStep.from_string("sleep 5")
        data = step.model_dump()
        assert data['type'] == 'shell'  # Should be string, not enum
        assert data['name'] == 'sleep 5'
        assert data['action'] == 'sleep 5'
    
    def test_step_type_validation(self):
        """Test step type validation from string."""
        step = CommandStep(name="test", type="builtin", action="test")
        assert step.type == StepType.BUILTIN
        
        step = CommandStep(name="test", type="invalid", action="test")
        assert step.type == StepType.BUILTIN  # Should default to builtin


class TestCommandDefinition:
    """Test CommandDefinition with new step support."""
    
    def test_command_with_string_steps(self):
        """Test command definition with string steps."""
        cmd = CommandDefinition(
            name="test-cmd",
            description="Test command",
            steps=["setup-environment", "echo hello", "cleanup.sh"]
        )
        
        all_steps = cmd.get_all_steps()
        assert len(all_steps) == 3
        assert all_steps[0].type == StepType.BUILTIN
        assert all_steps[1].type == StepType.SHELL
        assert all_steps[2].type == StepType.SCRIPT
    
    def test_command_with_mixed_steps(self):
        """Test command definition with mixed step types."""
        custom_step = CommandStep(
            name="custom",
            type=StepType.SHELL,
            action="ls -la",
            timeout=60
        )
        
        cmd = CommandDefinition(
            name="test-cmd",
            description="Test command",
            steps=["setup-environment", custom_step]
        )
        
        all_steps = cmd.get_all_steps()
        assert len(all_steps) == 2
        assert all_steps[0].type == StepType.BUILTIN
        assert all_steps[1].type == StepType.SHELL
        assert all_steps[1].timeout == 60
    
    def test_command_serialization(self):
        """Test command serialization preserves step types as strings."""
        cmd = CommandDefinition(
            name="test-cmd",
            description="Test command",
            steps=["setup-environment", "echo hello"]
        )
        
        data = cmd.model_dump()
        assert len(data['steps']) == 2
        assert data['steps'][0]['type'] == 'builtin'
        assert data['steps'][1]['type'] == 'shell'
    
    def test_yaml_roundtrip(self):
        """Test YAML serialization and deserialization."""
        import yaml
        
        cmd = CommandDefinition(
            name="test-cmd",
            description="Test command",
            steps=["setup-environment", "echo hello"]
        )
        
        # Serialize to YAML
        yaml_str = yaml.dump(cmd.model_dump())
        
        # Parse back from YAML
        data = yaml.safe_load(yaml_str)
        cmd2 = CommandDefinition(**data)
        
        # Should preserve step structure
        all_steps = cmd2.get_all_steps()
        assert len(all_steps) == 2
        assert all_steps[0].type == StepType.BUILTIN
        assert all_steps[1].type == StepType.SHELL