"""Pytest configuration and fixtures."""

import pytest
import pytest_asyncio
import asyncio
from pathlib import Path
import tempfile
import shutil

from prunejuice.core.config import Settings
from prunejuice.core.database import Database
from prunejuice.core.executor import Executor
from prunejuice.core.models import ActionDefintion, ActionArgument


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def test_settings(temp_dir):
    """Create test settings with temporary directories."""
    return Settings(db_path=temp_dir / "test.db", artifacts_dir=temp_dir / "artifacts")


@pytest_asyncio.fixture
async def test_database(test_settings):
    """Create and initialize test database."""
    db = Database(test_settings.db_path)
    await db.initialize()
    return db


@pytest_asyncio.fixture
async def test_executor(test_settings):
    """Create test executor with initialized database."""
    executor = Executor(test_settings)
    await executor.db.initialize()
    return executor


@pytest.fixture
def sample_command():
    """Sample command definition for testing."""
    return ActionDefintion(
        name="test-command",
        description="Test command for unit tests",
        arguments=[
            ActionArgument(name="input", required=True),
            ActionArgument(name="optional", required=False, default="default_value"),
        ],
        steps=["validate-prerequisites", "store-artifacts"],
    )


@pytest.fixture
def sample_action():
    """Sample action definition for testing."""
    return ActionDefintion(
        name="test-action",
        description="Test action for unit tests",
        arguments=[
            ActionArgument(name="input", required=True),
            ActionArgument(name="optional", required=False, default="default_value"),
        ],
        steps=["validate-prerequisites", "store-artifacts"],
    )


@pytest.fixture
def test_project(temp_dir):
    """Create a test project structure."""
    project_path = temp_dir / "test-project"
    project_path.mkdir()

    # Initialize real git repo
    import subprocess

    try:
        subprocess.run(
            ["git", "init"], cwd=project_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=project_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=project_path,
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        # Fallback to fake .git directory if git is not available
        (project_path / ".git").mkdir()

    # Create .prj structure
    prj_dir = project_path / ".prj"
    prj_dir.mkdir()
    (prj_dir / "actions").mkdir()
    (prj_dir / "steps").mkdir()

    return project_path
