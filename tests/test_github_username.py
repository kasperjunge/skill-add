"""Unit tests for git remote username extraction."""

import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from agr.github import get_username_from_git_remote


class TestGetUsernameFromGitRemote:
    """Tests for get_username_from_git_remote function."""

    def test_extracts_username_from_ssh_remote(self, tmp_path, monkeypatch):
        """Test extracting username from SSH-style remote."""
        monkeypatch.chdir(tmp_path)

        # Mock subprocess to return SSH remote
        mock_result = MagicMock()
        mock_result.stdout = "git@github.com:kasperjunge/agent-resources.git\n"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            username = get_username_from_git_remote(tmp_path)

        assert username == "kasperjunge"
        mock_run.assert_called_once()

    def test_extracts_username_from_https_remote(self, tmp_path, monkeypatch):
        """Test extracting username from HTTPS-style remote."""
        monkeypatch.chdir(tmp_path)

        mock_result = MagicMock()
        mock_result.stdout = "https://github.com/alice/my-repo.git\n"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            username = get_username_from_git_remote(tmp_path)

        assert username == "alice"

    def test_extracts_username_from_https_without_git_suffix(self, tmp_path, monkeypatch):
        """Test extracting username from HTTPS remote without .git suffix."""
        monkeypatch.chdir(tmp_path)

        mock_result = MagicMock()
        mock_result.stdout = "https://github.com/bob/cool-repo\n"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            username = get_username_from_git_remote(tmp_path)

        assert username == "bob"

    def test_returns_none_when_no_git_repo(self, tmp_path, monkeypatch):
        """Test returning None when not in a git repo."""
        monkeypatch.chdir(tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 128  # git error code
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            username = get_username_from_git_remote(tmp_path)

        assert username is None

    def test_returns_none_when_no_remote(self, tmp_path, monkeypatch):
        """Test returning None when git repo has no origin remote."""
        monkeypatch.chdir(tmp_path)

        # git remote get-url origin fails when no remote
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(128, "git")):
            username = get_username_from_git_remote(tmp_path)

        assert username is None

    def test_handles_subprocess_timeout(self, tmp_path, monkeypatch):
        """Test handling subprocess timeout gracefully."""
        monkeypatch.chdir(tmp_path)

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 30)):
            username = get_username_from_git_remote(tmp_path)

        assert username is None

    def test_handles_git_not_installed(self, tmp_path, monkeypatch):
        """Test handling when git is not installed."""
        monkeypatch.chdir(tmp_path)

        with patch("subprocess.run", side_effect=FileNotFoundError):
            username = get_username_from_git_remote(tmp_path)

        assert username is None

    def test_uses_current_directory_when_no_path_provided(self):
        """Test that current directory is used when no path is provided."""
        mock_result = MagicMock()
        mock_result.stdout = "git@github.com:testuser/repo.git\n"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            username = get_username_from_git_remote()

        assert username == "testuser"
        # Verify cwd was used (no specific path in command)
        call_args = mock_run.call_args
        assert "cwd" in call_args.kwargs or call_args.kwargs.get("cwd") is None

    def test_handles_gitlab_remote(self, tmp_path, monkeypatch):
        """Test handling GitLab-style remote (should still extract username)."""
        monkeypatch.chdir(tmp_path)

        mock_result = MagicMock()
        mock_result.stdout = "git@gitlab.com:company/project.git\n"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            username = get_username_from_git_remote(tmp_path)

        # Should still extract the "company" as username
        assert username == "company"

    def test_handles_remote_with_nested_path(self, tmp_path, monkeypatch):
        """Test handling remote with nested org/repo path (takes first segment)."""
        monkeypatch.chdir(tmp_path)

        mock_result = MagicMock()
        mock_result.stdout = "https://github.com/org/subgroup/repo.git\n"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            username = get_username_from_git_remote(tmp_path)

        # Should take first path segment as username
        assert username == "org"
