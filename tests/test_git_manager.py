import os
import pytest
from unittest.mock import patch, MagicMock
from core.git_manager import GitManager

@patch("core.git_manager.git.Repo")
def test_get_diff(mock_repo_class):
    """Test get_diff combines staged and unstaged changes."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    
    mock_repo.git.diff.side_effect = lambda *args: "staged_diff" if '--cached' in args else "unstaged_diff"
    
    git_manager = GitManager("/fake/path")
    diff = git_manager.get_diff()
    
    assert "staged_diff" in diff
    assert "unstaged_diff" in diff

@patch("core.git_manager.git.Repo")
def test_get_modified_files(mock_repo_class):
    """Test get_modified_files combines correctly."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    
    mock_repo.git.diff.side_effect = lambda *args: "file1.py" if '--cached' in args else "file2.py"
    
    git_manager = GitManager("/fake/path")
    files = git_manager.get_modified_files()
    
    assert "file1.py" in files
    assert "file2.py" in files
    assert len(files) == 2

@patch("core.git_manager.git.Repo")
def test_get_file_content_success(mock_repo_class, tmp_path):
    """Test reading file content from local disk."""
    mock_repo_class.return_value = MagicMock()
    
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    test_file = repo_dir / "test.py"
    test_file.write_text("print('hello')")
    
    git_manager = GitManager(str(repo_dir))
    content = git_manager.get_file_content("test.py")
    
    assert content == "print('hello')"

@patch("core.git_manager.git.Repo")
def test_get_file_content_error(mock_repo_class):
    """Test handling file that doesn't exist."""
    mock_repo_class.return_value = MagicMock()
    
    git_manager = GitManager("/fake/path")
    content = git_manager.get_file_content("nonexistent.py")
    
    assert content.startswith("Error reading file")

@patch("core.git_manager.git.Repo")
def test_git_init_error(mock_repo_class):
    """Test error handling when git is not installed or invalid repo."""
    import git
    mock_repo_class.side_effect = git.exc.InvalidGitRepositoryError("Not a repo")
    
    with pytest.raises(git.exc.InvalidGitRepositoryError):
        GitManager("/invalid/repo/path")
