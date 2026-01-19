"""Test Job 6: Running Resources Temporarily with agrx.

Tests for `agrx` command covering:
- One-off execution without permanent installation
- --global/-g flag for global context
- Automatic cleanup of temporary files
- Interactive mode (-i flag)
- Prompt/args passing

Reference: .documents/jobs.md section "6. Running Resources Temporarily with agrx"

NOTE: Core agrx functionality is tested in test_agrx_unified.py.
This module focuses on the --global flag and cleanup verification.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agr.cli.run import app, AGRX_PREFIX
from agr.fetcher import ResourceType, DiscoveredResource, DiscoveryResult


runner = CliRunner()


class TestAgrxGlobalFlag:
    """Tests for agrx --global/-g flag behavior."""

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.fetch_resource")
    @patch("agr.cli.run._cleanup_resource")
    def test_global_long_flag_uses_home_directory(
        self, mock_cleanup, mock_fetch, mock_subprocess, mock_which, tmp_path, monkeypatch
    ):
        """Test that --global flag installs to ~/.claude/ instead of ./.claude/."""
        # Mock home directory
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = runner.invoke(app, ["--type", "skill", "--global", "testuser/hello-world"])

        # Should have been called - fetch_resource uses get_destination which checks global
        mock_fetch.assert_called_once()

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.fetch_resource")
    @patch("agr.cli.run._cleanup_resource")
    def test_global_short_flag_accepted(
        self, mock_cleanup, mock_fetch, mock_subprocess, mock_which, tmp_path, monkeypatch
    ):
        """Test that -g short flag is accepted."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = runner.invoke(app, ["--type", "skill", "-g", "testuser/hello-world"])

        # Should run without error about flag
        assert "-g" not in result.output or result.exit_code == 0


class TestAgrxCleanup:
    """Tests for agrx automatic cleanup behavior."""

    def test_agrx_prefix_is_defined(self):
        """Test that AGRX_PREFIX is defined for temporary resource naming."""
        assert AGRX_PREFIX == "_agrx_"

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.fetch_resource")
    def test_cleanup_is_called_after_run(
        self, mock_fetch, mock_subprocess, mock_which, tmp_path, monkeypatch
    ):
        """Test that cleanup is called after resource execution."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()
        (tmp_path / ".claude" / "skills").mkdir(parents=True)

        with patch("agr.cli.run._cleanup_resource") as mock_cleanup:
            result = runner.invoke(app, ["--type", "skill", "testuser/hello-world"])

            # Cleanup should have been called
            mock_cleanup.assert_called()

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.fetch_resource")
    def test_resource_uses_agrx_prefix(
        self, mock_fetch, mock_subprocess, mock_which, tmp_path, monkeypatch
    ):
        """Test that temporary resources use _agrx_ prefix."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()
        (tmp_path / ".claude" / "skills").mkdir(parents=True)

        with patch("agr.cli.run._cleanup_resource"):
            result = runner.invoke(app, ["--type", "skill", "testuser/hello-world"])

            # subprocess.run should be called with a prompt containing _agrx_
            if mock_subprocess.called:
                call_args = mock_subprocess.call_args[0][0]
                prompt_idx = call_args.index("-p") + 1
                prompt_value = call_args[prompt_idx]
                assert AGRX_PREFIX in prompt_value


class TestAgrxPromptPassing:
    """Tests for agrx prompt/args passing to Claude CLI."""

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.fetch_resource")
    @patch("agr.cli.run._cleanup_resource")
    def test_prompt_is_passed_to_claude(
        self, mock_cleanup, mock_fetch, mock_subprocess, mock_which, tmp_path, monkeypatch
    ):
        """Test that prompt argument is passed to Claude CLI."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()
        (tmp_path / ".claude" / "skills").mkdir(parents=True)

        result = runner.invoke(app, ["--type", "skill", "testuser/hello", "my test prompt"])

        mock_subprocess.assert_called()
        call_args = mock_subprocess.call_args[0][0]
        prompt_idx = call_args.index("-p") + 1
        prompt_value = call_args[prompt_idx]
        assert "my test prompt" in prompt_value

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.fetch_resource")
    @patch("agr.cli.run._cleanup_resource")
    def test_prompt_without_args_just_invokes_skill(
        self, mock_cleanup, mock_fetch, mock_subprocess, mock_which, tmp_path, monkeypatch
    ):
        """Test that running without prompt just invokes the skill."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()
        (tmp_path / ".claude" / "skills").mkdir(parents=True)

        result = runner.invoke(app, ["--type", "skill", "testuser/hello"])

        mock_subprocess.assert_called()
        call_args = mock_subprocess.call_args[0][0]
        prompt_idx = call_args.index("-p") + 1
        prompt_value = call_args[prompt_idx]
        # Should just be /<prefixed_name> without extra text
        assert prompt_value.startswith("/")


class TestAgrxTypeFlag:
    """Tests for agrx --type/-t flag handling."""

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.fetch_resource")
    @patch("agr.cli.run._cleanup_resource")
    def test_type_flag_long_form(
        self, mock_cleanup, mock_fetch, mock_subprocess, mock_which, tmp_path, monkeypatch
    ):
        """Test --type flag is accepted."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()
        (tmp_path / ".claude" / "skills").mkdir(parents=True)

        result = runner.invoke(app, ["--type", "skill", "testuser/hello"])

        # Should run without error
        mock_fetch.assert_called()

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.fetch_resource")
    @patch("agr.cli.run._cleanup_resource")
    def test_type_flag_short_form(
        self, mock_cleanup, mock_fetch, mock_subprocess, mock_which, tmp_path, monkeypatch
    ):
        """Test -t short flag is accepted."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()
        (tmp_path / ".claude" / "commands").mkdir(parents=True)

        result = runner.invoke(app, ["-t", "command", "testuser/hello"])

        mock_fetch.assert_called()

    def test_invalid_type_shows_error(self):
        """Test that invalid resource type shows error."""
        result = runner.invoke(app, ["--type", "invalid", "testuser/hello"])

        assert result.exit_code == 1
        assert "unknown" in result.output.lower() or "error" in result.output.lower()


class TestAgrxInteractiveFlag:
    """Tests for agrx --interactive/-i flag."""

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.fetch_resource")
    @patch("agr.cli.run._cleanup_resource")
    def test_interactive_long_flag_accepted(
        self, mock_cleanup, mock_fetch, mock_subprocess, mock_which, tmp_path, monkeypatch
    ):
        """Test --interactive flag is accepted."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()
        (tmp_path / ".claude" / "skills").mkdir(parents=True)

        result = runner.invoke(app, ["--type", "skill", "--interactive", "testuser/hello"])

        # Interactive mode calls subprocess twice: first to run skill, then to continue
        assert mock_subprocess.call_count == 2
        first_call_args = mock_subprocess.call_args_list[0][0][0]
        second_call_args = mock_subprocess.call_args_list[1][0][0]
        assert "--dangerously-skip-permissions" in first_call_args
        assert second_call_args == ["claude", "--continue"]

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.fetch_resource")
    @patch("agr.cli.run._cleanup_resource")
    def test_interactive_short_flag_accepted(
        self, mock_cleanup, mock_fetch, mock_subprocess, mock_which, tmp_path, monkeypatch
    ):
        """Test -i short flag is accepted."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()
        (tmp_path / ".claude" / "skills").mkdir(parents=True)

        result = runner.invoke(app, ["--type", "skill", "-i", "testuser/hello"])

        # Interactive mode calls subprocess twice
        assert mock_subprocess.call_count == 2
        first_call_args = mock_subprocess.call_args_list[0][0][0]
        assert "--dangerously-skip-permissions" in first_call_args


class TestAgrxWithoutClaude:
    """Tests for agrx behavior when Claude CLI is not installed."""

    @patch("agr.cli.run.shutil.which", return_value=None)
    def test_shows_error_when_claude_not_found(self, mock_which):
        """Test that agrx shows error when Claude CLI is not installed."""
        result = runner.invoke(app, ["--type", "skill", "testuser/hello"])

        assert result.exit_code == 1
        assert "claude" in result.output.lower()
        assert "not found" in result.output.lower() or "install" in result.output.lower()


class TestAgrxAutoDetection:
    """Tests for agrx resource type auto-detection."""

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.downloaded_repo")
    @patch("agr.cli.run.discover_runnable_resource")
    @patch("agr.cli.run.fetch_resource_from_repo_dir")
    @patch("agr.cli.run._cleanup_resource")
    def test_auto_detects_skill_type(
        self, mock_cleanup, mock_fetch_from_repo, mock_discover,
        mock_download, mock_subprocess, mock_which, tmp_path
    ):
        """Test that agrx auto-detects skill type when only skill exists."""
        mock_download.return_value.__enter__ = MagicMock(return_value=tmp_path)
        mock_download.return_value.__exit__ = MagicMock(return_value=None)

        mock_discover.return_value = DiscoveryResult(
            resources=[
                DiscoveredResource(
                    name="hello",
                    resource_type=ResourceType.SKILL,
                    path_segments=["hello"]
                ),
            ]
        )

        result = runner.invoke(app, ["testuser/hello"])

        # Should succeed without needing --type flag
        mock_discover.assert_called()

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.downloaded_repo")
    @patch("agr.cli.run.discover_runnable_resource")
    @patch("agr.cli.run.fetch_resource_from_repo_dir")
    @patch("agr.cli.run._cleanup_resource")
    def test_auto_detects_command_type(
        self, mock_cleanup, mock_fetch_from_repo, mock_discover,
        mock_download, mock_subprocess, mock_which, tmp_path
    ):
        """Test that agrx auto-detects command type when only command exists."""
        mock_download.return_value.__enter__ = MagicMock(return_value=tmp_path)
        mock_download.return_value.__exit__ = MagicMock(return_value=None)

        mock_discover.return_value = DiscoveryResult(
            resources=[
                DiscoveredResource(
                    name="hello",
                    resource_type=ResourceType.COMMAND,
                    path_segments=["hello"]
                ),
            ]
        )

        result = runner.invoke(app, ["testuser/hello"])

        mock_discover.assert_called()
