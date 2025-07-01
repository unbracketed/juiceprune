"""Tests for worktree operations."""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import shutil

from prunejuice.worktree_utils.operations import (
    WorktreeOperations,
    OperationResult,
    CommitResult,
    MergeResult,
    PRResult,
    DeleteResult,
)
from prunejuice.worktree_utils.commit import (
    CommitStatusAnalyzer,
    InteractiveStaging,
    CommitMessageEditor,
    CommitExecutor,
    FileStatus,
    FileInfo,
    CommitAnalysis,
)


class TestWorktreeOperations:
    """Test cases for WorktreeOperations class."""

    @pytest.fixture
    def temp_project_path(self):
        """Create a temporary project path for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def worktree_operations(self, temp_project_path):
        """Create a WorktreeOperations instance for testing."""
        return WorktreeOperations(temp_project_path)

    @pytest.mark.asyncio
    async def test_commit_changes_no_worktree(self, worktree_operations):
        """Test commit_changes with non-existent worktree."""
        non_existent_path = Path("/non/existent/path")
        
        result = await worktree_operations.commit_changes(non_existent_path)
        
        assert result.status == OperationResult.FAILURE
        assert "does not exist" in result.error

    @pytest.mark.asyncio
    async def test_commit_changes_no_message_non_interactive(self, worktree_operations, temp_project_path):
        """Test commit_changes without message in non-interactive mode."""
        # Create a mock worktree directory
        worktree_path = temp_project_path / "test_worktree"
        worktree_path.mkdir()
        
        with patch('git.Repo') as mock_repo:
            # Mock the repo to make the path appear as a valid git repo
            mock_repo.return_value = Mock()
            
            result = await worktree_operations.commit_changes(
                worktree_path,
                message=None,
                interactive=False
            )
            
            assert result.status == OperationResult.FAILURE
            assert "No commit message provided" in result.error

    def test_commit_result_initialization(self):
        """Test CommitResult dataclass initialization."""
        result = CommitResult(status=OperationResult.SUCCESS)
        
        assert result.status == OperationResult.SUCCESS
        assert result.commit_hash is None
        assert result.message is None
        assert result.files_committed == []  # Should be initialized by __post_init__
        assert result.error is None

    def test_merge_result_initialization(self):
        """Test MergeResult dataclass initialization."""
        result = MergeResult(status=OperationResult.CONFLICT)
        
        assert result.status == OperationResult.CONFLICT
        assert result.merge_commit is None
        assert result.target_branch is None
        assert result.conflicts == []  # Should be initialized by __post_init__
        assert result.error is None


class TestCommitStatusAnalyzer:
    """Test cases for CommitStatusAnalyzer class."""

    @pytest.fixture
    def temp_worktree_path(self):
        """Create a temporary worktree path for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_file_info_creation(self):
        """Test FileInfo dataclass creation."""
        file_info = FileInfo(
            path="test.py",
            status=FileStatus.MODIFIED,
            staged=True,
            lines_added=10,
            lines_removed=5
        )
        
        assert file_info.path == "test.py"
        assert file_info.status == FileStatus.MODIFIED
        assert file_info.staged is True
        assert file_info.lines_added == 10
        assert file_info.lines_removed == 5

    def test_commit_analysis_creation(self):
        """Test CommitAnalysis dataclass creation."""
        staged_files = [FileInfo("file1.py", FileStatus.MODIFIED, staged=True)]
        unstaged_files = [FileInfo("file2.py", FileStatus.ADDED, staged=False)]
        untracked_files = [FileInfo("file3.py", FileStatus.UNTRACKED, staged=False)]
        
        analysis = CommitAnalysis(
            staged_files=staged_files,
            unstaged_files=unstaged_files,
            untracked_files=untracked_files,
            total_changes=3,
            can_commit=True,
            has_conflicts=False,
            current_branch="feature/test"
        )
        
        assert len(analysis.staged_files) == 1
        assert len(analysis.unstaged_files) == 1
        assert len(analysis.untracked_files) == 1
        assert analysis.total_changes == 3
        assert analysis.can_commit is True
        assert analysis.has_conflicts is False
        assert analysis.current_branch == "feature/test"

    @patch('git.Repo')
    def test_analyze_with_mocked_repo(self, mock_repo_class, temp_worktree_path):
        """Test analyze method with mocked git repo."""
        # Mock the git repo and its methods
        mock_repo = Mock()
        mock_repo.git.status.return_value = "M  modified_file.py\n?? untracked_file.py"
        mock_repo.active_branch.name = "test_branch"
        mock_repo_class.return_value = mock_repo
        
        analyzer = CommitStatusAnalyzer(temp_worktree_path)
        result = analyzer.analyze()
        
        assert isinstance(result, CommitAnalysis)
        assert result.current_branch == "test_branch"
        # Note: Detailed file parsing would require more complex mocking


class TestInteractiveStaging:
    """Test cases for InteractiveStaging class."""

    @pytest.fixture
    def temp_worktree_path(self):
        """Create a temporary worktree path for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @patch('git.Repo')
    @pytest.mark.asyncio
    async def test_stage_files_success(self, mock_repo_class, temp_worktree_path):
        """Test successful file staging."""
        mock_repo = Mock()
        mock_repo.git.add = Mock()
        mock_repo_class.return_value = mock_repo
        
        staging = InteractiveStaging(temp_worktree_path)
        result = await staging.stage_files(["file1.py", "file2.py"])
        
        assert result is True
        assert mock_repo.git.add.call_count == 2

    @patch('git.Repo')
    @pytest.mark.asyncio
    async def test_stage_all_changes_success(self, mock_repo_class, temp_worktree_path):
        """Test successful staging of all changes."""
        mock_repo = Mock()
        mock_repo.git.add = Mock()
        mock_repo_class.return_value = mock_repo
        
        staging = InteractiveStaging(temp_worktree_path)
        result = await staging.stage_all_changes()
        
        assert result is True
        mock_repo.git.add.assert_called_once_with(".")


class TestCommitMessageEditor:
    """Test cases for CommitMessageEditor class."""

    @pytest.fixture
    def temp_worktree_path(self):
        """Create a temporary worktree path for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @patch('git.Repo')
    def test_validate_commit_message_valid(self, mock_repo_class, temp_worktree_path):
        """Test validation of a valid commit message."""
        mock_repo_class.return_value = Mock()
        
        editor = CommitMessageEditor(temp_worktree_path)
        is_valid, error = editor.validate_commit_message("feat: add new feature")
        
        assert is_valid is True
        assert error is None

    @patch('git.Repo')
    def test_validate_commit_message_empty(self, mock_repo_class, temp_worktree_path):
        """Test validation of an empty commit message."""
        mock_repo_class.return_value = Mock()
        
        editor = CommitMessageEditor(temp_worktree_path)
        is_valid, error = editor.validate_commit_message("")
        
        assert is_valid is False
        assert "cannot be empty" in error

    @patch('git.Repo')
    def test_validate_commit_message_too_long(self, mock_repo_class, temp_worktree_path):
        """Test validation of a commit message that's too long."""
        mock_repo_class.return_value = Mock()
        
        editor = CommitMessageEditor(temp_worktree_path)
        long_message = "x" * 80  # Exceeds 72 character limit
        is_valid, error = editor.validate_commit_message(long_message)
        
        assert is_valid is False
        assert "72 characters" in error

    @patch('git.Repo')
    def test_generate_conventional_commit_template(self, mock_repo_class, temp_worktree_path):
        """Test generation of conventional commit templates."""
        mock_repo_class.return_value = Mock()
        
        editor = CommitMessageEditor(temp_worktree_path)
        
        # Test basic template
        template = editor.generate_conventional_commit_template("feat")
        assert template == "feat: "
        
        # Test with scope
        template = editor.generate_conventional_commit_template("fix", scope="api")
        assert template == "fix(api): "
        
        # Test with breaking change
        template = editor.generate_conventional_commit_template("feat", breaking=True)
        assert template == "feat!: "
        
        # Test with scope and breaking change
        template = editor.generate_conventional_commit_template(
            "feat", scope="cli", breaking=True
        )
        assert template == "feat(cli)!: "


class TestCommitExecutor:
    """Test cases for CommitExecutor class."""

    @pytest.fixture
    def temp_worktree_path(self):
        """Create a temporary worktree path for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @patch('git.Repo')
    @pytest.mark.asyncio
    async def test_execute_commit_no_staged_changes(self, mock_repo_class, temp_worktree_path):
        """Test commit execution with no staged changes."""
        mock_repo = Mock()
        mock_repo.git.status.return_value = ""  # No changes
        mock_repo_class.return_value = mock_repo
        
        executor = CommitExecutor(temp_worktree_path)
        success, commit_hash, error = await executor.execute_commit("test message")
        
        assert success is False
        assert commit_hash is None
        assert "No staged changes" in error

    @patch('git.Repo')
    @pytest.mark.asyncio
    async def test_execute_commit_allow_empty(self, mock_repo_class, temp_worktree_path):
        """Test commit execution allowing empty commits."""
        mock_repo = Mock()
        mock_repo.git.status.return_value = ""  # No changes
        mock_repo.git.commit = Mock()
        mock_repo.head.commit.hexsha = "abc123def456"
        mock_repo_class.return_value = mock_repo
        
        executor = CommitExecutor(temp_worktree_path)
        success, commit_hash, error = await executor.execute_commit(
            "test message", allow_empty=True
        )
        
        assert success is True
        assert commit_hash == "abc123def456"
        assert error is None
        mock_repo.git.commit.assert_called_once_with("-m", "test message", "--allow-empty")


# Integration tests would go here in a real implementation
class TestWorktreeOperationsIntegration:
    """Integration tests for worktree operations."""

    @pytest.mark.skip(reason="Requires real git repository setup")
    def test_full_commit_workflow(self):
        """Test complete commit workflow end-to-end."""
        # This would test the full workflow with a real git repository
        # Including file creation, staging, committing, etc.
        pass

    @pytest.mark.skip(reason="Requires GitHub CLI and authentication")
    def test_pull_request_creation(self):
        """Test pull request creation workflow."""
        # This would test PR creation with real GitHub CLI
        pass