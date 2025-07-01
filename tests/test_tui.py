"""Tests for the TUI application."""

import pytest
from unittest.mock import Mock, patch

from prunejuice.tui.app import PrunejuiceApp


@pytest.fixture
def mock_worktrees():
    """Mock worktree data for testing."""
    return [
        {
            "path": "/path/to/project",
            "branch": "main",
            "commit": "abc123def456",
        },
        {
            "path": "/path/to/worktrees/feature-branch",
            "branch": "feature-branch",
            "commit": "def456ghi789",
        },
        {
            "path": "/path/to/worktrees/detached",
            "commit": "ghi789jkl012",
            "detached": True,
        },
    ]


@pytest.fixture
def mock_git_manager(mock_worktrees):
    """Mock GitWorktreeManager for testing."""
    manager = Mock()
    manager.list_worktrees.return_value = mock_worktrees
    return manager


class TestPrunejuiceApp:
    """Test the PrunejuiceApp TUI."""

    @pytest.mark.asyncio
    async def test_app_initialization(self, tmp_path):
        """Test that the app initializes correctly."""
        app = PrunejuiceApp(project_path=tmp_path)
        assert app.project_path == tmp_path
        # Title and subtitle are set in on_mount, not during initialization

    @pytest.mark.asyncio
    async def test_app_displays_worktrees(
        self, mock_git_manager, mock_worktrees, tmp_path
    ):
        """Test that the app displays worktrees correctly."""
        with patch(
            "prunejuice.tui.app.GitWorktreeManager", return_value=mock_git_manager
        ):
            app = PrunejuiceApp(project_path=tmp_path)

            async with app.run_test() as pilot:
                # Wait for the app to load and background tasks to complete
                await pilot.pause()
                await pilot.wait_for_scheduled_animations()

                # Check that the ListView exists
                list_view = app.query_one("#worktree-list")
                assert list_view is not None

                # Check that worktrees are displayed
                items = list_view.query("ListItem")
                assert len(items) == len(mock_worktrees)

    @pytest.mark.asyncio
    async def test_app_handles_no_worktrees(self, tmp_path):
        """Test that the app handles no worktrees gracefully."""
        mock_manager = Mock()
        mock_manager.list_worktrees.return_value = []

        with patch("prunejuice.tui.app.GitWorktreeManager", return_value=mock_manager):
            app = PrunejuiceApp(project_path=tmp_path)

            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.wait_for_scheduled_animations()

                # Check that "No worktrees found" is displayed
                list_view = app.query_one("#worktree-list")
                items = list_view.query("ListItem")
                assert len(items) == 1
                assert "No worktrees found" in str(items[0].children[0].renderable)

    @pytest.mark.asyncio
    async def test_quit_keybinding(self, tmp_path):
        """Test that pressing 'q' quits the app."""
        app = PrunejuiceApp(project_path=tmp_path)

        async with app.run_test() as pilot:
            # Press 'q' to quit
            await pilot.press("q")
            # The app should exit, so this test should complete

    @pytest.mark.asyncio
    async def test_worktree_formatting(self, mock_git_manager, tmp_path):
        """Test that worktrees are formatted correctly."""
        with patch(
            "prunejuice.tui.app.GitWorktreeManager", return_value=mock_git_manager
        ):
            app = PrunejuiceApp(project_path=tmp_path)

            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.wait_for_scheduled_animations()

                list_view = app.query_one("#worktree-list")
                items = list_view.query("ListItem")

                # Check main branch formatting - only branch name is displayed in list
                text0 = str(items[0].children[0].renderable)
                assert "main" in text0

                # Check feature branch formatting - only branch name is displayed in list
                text1 = str(items[1].children[0].renderable)
                assert "feature-branch" in text1

                # Check detached HEAD formatting - "detached" is displayed for detached HEAD
                text2 = str(items[2].children[0].renderable)
                assert "detached" in text2

    @pytest.mark.asyncio
    async def test_error_handling(self, tmp_path):
        """Test that the app handles errors gracefully."""
        mock_manager = Mock()
        mock_manager.list_worktrees.side_effect = Exception("Git error")

        with patch("prunejuice.tui.app.GitWorktreeManager", return_value=mock_manager):
            app = PrunejuiceApp(project_path=tmp_path)

            # The app should handle the error without crashing
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.wait_for_scheduled_animations()
                # App should still be running despite the error
