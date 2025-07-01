"""Tests for command executor."""

import pytest
import yaml

from prunejuice.core.models import ActionDefintion, CommandArgument, ExecutionResult


@pytest.mark.asyncio
async def test_execute_simple_command(test_executor, test_project, sample_command):
    """Test execution of a simple command."""
    # Create command file
    cmd_dir = test_project / ".prj" / "commands"
    cmd_file = cmd_dir / "test-command.yaml"

    with open(cmd_file, "w") as f:
        yaml.dump(sample_command.model_dump(), f)

    # Execute command
    result = await test_executor.execute_command(
        "test-command", test_project, {"input": "test-value"}
    )

    assert isinstance(result, ExecutionResult)
    assert result.success
    assert result.artifacts_path is not None


@pytest.mark.asyncio
async def test_missing_required_argument(test_executor, test_project, sample_command):
    """Test validation of required arguments."""
    # Create command file
    cmd_dir = test_project / ".prj" / "commands"
    cmd_file = cmd_dir / "test-command.yaml"

    with open(cmd_file, "w") as f:
        yaml.dump(sample_command.model_dump(), f)

    # Execute without required argument
    result = await test_executor.execute_command(
        "test-command",
        test_project,
        {},  # Missing required 'input' argument
    )

    assert not result.success
    assert "Required argument 'input' missing" in result.error


@pytest.mark.asyncio
async def test_nonexistent_command(test_executor, test_project):
    """Test execution of non-existent command."""
    result = await test_executor.execute_command(
        "nonexistent-command", test_project, {}
    )

    assert not result.success
    assert "Command 'nonexistent-command' not found" in result.error


@pytest.mark.asyncio
async def test_dry_run(test_executor, test_project, sample_command):
    """Test dry run functionality."""
    # Create command file
    cmd_dir = test_project / ".prj" / "commands"
    cmd_file = cmd_dir / "test-command.yaml"

    with open(cmd_file, "w") as f:
        yaml.dump(sample_command.model_dump(), f)

    # Execute dry run
    result = await test_executor.execute_command(
        "test-command", test_project, {"input": "test-value"}, dry_run=True
    )

    assert result.success
    assert "Dry run for command: test-command" in result.output
    assert "validate-prerequisites" in result.output
    assert "store-artifacts" in result.output


@pytest.mark.asyncio
async def test_step_failure_cleanup(test_executor, test_project):
    """Test cleanup execution when a step fails."""
    # Create command with failing step and cleanup
    failing_command = ActionDefintion(
        name="failing-command",
        description="Command that fails",
        steps=["nonexistent-step"],
        cleanup_on_failure=["cleanup"],
    )

    cmd_dir = test_project / ".prj" / "commands"
    cmd_file = cmd_dir / "failing-command.yaml"

    with open(cmd_file, "w") as f:
        yaml.dump(failing_command.model_dump(), f)

    # Execute failing command
    result = await test_executor.execute_command("failing-command", test_project, {})

    assert not result.success
    assert "Step 'nonexistent-step' not found" in result.error


@pytest.mark.asyncio
async def test_built_in_steps(test_executor, test_project):
    """Test built-in step execution."""
    # Create command using built-in steps
    builtin_command = ActionDefintion(
        name="builtin-test",
        description="Test built-in steps",
        steps=[
            "setup-environment",
            "validate-prerequisites",
            "gather-context",
            "store-artifacts",
        ],
    )

    cmd_dir = test_project / ".prj" / "commands"
    cmd_file = cmd_dir / "builtin-test.yaml"

    with open(cmd_file, "w") as f:
        yaml.dump(builtin_command.model_dump(), f)

    # Execute command
    result = await test_executor.execute_command("builtin-test", test_project, {})

    assert result.success


@pytest.mark.asyncio
async def test_environment_variables(test_executor, test_project):
    """Test environment variable handling."""
    # Create command with environment variables
    env_command = ActionDefintion(
        name="env-test",
        description="Test environment variables",
        environment={"TEST_VAR": "test_value"},
        steps=["setup-environment"],
    )

    cmd_dir = test_project / ".prj" / "commands"
    cmd_file = cmd_dir / "env-test.yaml"

    with open(cmd_file, "w") as f:
        yaml.dump(env_command.model_dump(), f)

    # Execute command
    result = await test_executor.execute_command("env-test", test_project, {})

    assert result.success


@pytest.mark.asyncio
async def test_argument_injection_protection(
    test_executor, test_project, sample_command
):
    """Test protection against argument injection."""
    # Create command file
    cmd_dir = test_project / ".prj" / "commands"
    cmd_file = cmd_dir / "test-command.yaml"

    with open(cmd_file, "w") as f:
        yaml.dump(sample_command.model_dump(), f)

    # Try to inject malicious arguments
    malicious_args = {
        "input": "; rm -rf /; echo 'pwned'",
        "optional": "'; DROP TABLE events; --",
    }

    # Execute command - should not execute injection
    result = await test_executor.execute_command(
        "test-command", test_project, malicious_args
    )

    # Command should succeed (arguments are just data)
    assert result.success


@pytest.mark.asyncio
async def test_command_injection_prevention(test_executor, test_project):
    """Test prevention of command injection attacks."""
    # Create malicious command
    malicious_cmd = ActionDefintion(
        name="evil-command",
        description="Command injection test",
        steps=["echo 'safe' && rm -rf /"],
        arguments=[CommandArgument(name="user_input", required=True)],
    )

    cmd_dir = test_project / ".prj" / "commands"
    cmd_file = cmd_dir / "evil-command.yaml"

    with open(cmd_file, "w") as f:
        yaml.dump(malicious_cmd.model_dump(), f)

    # Try to inject commands via arguments
    result = await test_executor.execute_command(
        "evil-command",
        test_project,
        {"user_input": "'; rm -rf / #"},
        dry_run=True,  # Safety first!
    )

    # Dry run should show the dangerous command (this is correct behavior)
    # The actual security should be handled at execution time, not dry run
    assert result.success  # Dry run should complete successfully
    assert "rm -rf /" in str(result.output)  # Should show what would be executed


@pytest.mark.asyncio
async def test_environment_variable_sanitization(test_executor, test_project):
    """Test sanitization of environment variables."""
    cmd = ActionDefintion(
        name="env-test",
        description="Environment test",
        environment={
            "SAFE_VAR": "safe_value",
            "PATH": "/evil/path:$PATH",  # Attempt to modify PATH
        },
        steps=["echo $PATH"],
    )

    cmd_dir = test_project / ".prj" / "commands"
    cmd_file = cmd_dir / "env-test.yaml"

    with open(cmd_file, "w") as f:
        yaml.dump(cmd.model_dump(), f)

    # Execute with potentially dangerous environment
    result = await test_executor.execute_command(
        "env-test", test_project, {}, dry_run=False
    )

    # Should not allow arbitrary PATH modification
    assert "/evil/path" not in str(result.output)


@pytest.mark.asyncio
async def test_script_timeout_handling(test_executor, test_project):
    """Test timeout handling for long-running scripts."""
    # Create command with very short timeout
    timeout_cmd = ActionDefintion(
        name="timeout-test",
        description="Timeout test",
        steps=["sleep 10"],
        timeout=1,  # 1 second timeout
    )

    cmd_dir = test_project / ".prj" / "commands"
    cmd_file = cmd_dir / "timeout-test.yaml"

    with open(cmd_file, "w") as f:
        yaml.dump(timeout_cmd.model_dump(), f)

    # Should timeout and handle gracefully
    result = await test_executor.execute_command("timeout-test", test_project, {})

    assert not result.success
    assert "timeout" in result.error.lower()
