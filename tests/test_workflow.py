"""Integration tests for complete workflows."""

import pytest
from pathlib import Path

from prunejuice.core.executor import Executor


class TestWorkflows:
    """Test complete user workflows end-to-end."""

    @pytest.mark.asyncio
    async def test_multi_step_action_execution(self, test_project, test_settings):
        """Test execution of multi-step actions."""
        # Create multi-step action
        cmd_yaml = """
name: multi-step
description: Multi-step test
pre_steps:
  - setup-environment
steps:
  - validate-prerequisites
  - gather-context
  - store-artifacts
post_steps:
  - cleanup
"""
        cmd_file = test_project / ".prj" / "actions" / "multi-step.yaml"
        cmd_file.parent.mkdir(parents=True, exist_ok=True)
        cmd_file.write_text(cmd_yaml)

        # Execute action
        executor = Executor(test_settings)
        result = await executor.execute_action("multi-step", test_project, {})

        assert result.success
        assert Path(result.artifacts_path).exists()

    @pytest.mark.asyncio
    async def test_error_recovery(self, test_project, test_settings):
        """Test error recovery in workflows."""
        # Create action that fails mid-execution
        cmd_yaml = """
name: fail-recover
description: Failure recovery test
steps:
  - setup-environment
  - this-step-does-not-exist
  - store-artifacts
cleanup_on_failure:
  - cleanup
"""
        cmd_file = test_project / ".prj" / "actions" / "fail.yaml"
        cmd_file.parent.mkdir(parents=True, exist_ok=True)
        cmd_file.write_text(cmd_yaml)

        executor = Executor(test_settings)
        result = await executor.execute_action("fail-recover", test_project, {})

        assert not result.success
        assert "not found" in result.error
        # Cleanup should have run

    @pytest.mark.asyncio
    async def test_concurrent_actions(self, test_project, test_settings):
        """Test concurrent action execution."""
        # Create simple action
        cmd_yaml = """
name: concurrent-test
description: Concurrent execution test
steps:
  - echo "Running concurrent test"
"""
        cmd_file = test_project / ".prj" / "actions" / "concurrent-test.yaml"
        cmd_file.parent.mkdir(parents=True, exist_ok=True)
        cmd_file.write_text(cmd_yaml)

        executor = Executor(test_settings)

        # Run multiple actions concurrently
        import asyncio

        tasks = [
            executor.execute_action("concurrent-test", test_project, {"id": str(i)})
            for i in range(3)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed without interference
        assert all(r.success for r in results if not isinstance(r, Exception))
