"""Integration tests for unified agrx command."""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path

from agr.cli.run import app
from agr.fetcher import ResourceType, DiscoveredResource, DiscoveryResult


runner = CliRunner()


class TestAgrxUnifiedCommand:
    """Tests for the unified agrx command."""

    @patch("agr.cli.run._run_resource")
    def test_explicit_type_skill(self, mock_run):
        """Test that --type skill delegates to skill runner."""
        result = runner.invoke(app, ["--type", "skill", "testuser/hello-world"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][1] == ResourceType.SKILL

    @patch("agr.cli.run._run_resource")
    def test_explicit_type_command(self, mock_run):
        """Test that --type command delegates to command runner."""
        result = runner.invoke(app, ["--type", "command", "testuser/hello"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][1] == ResourceType.COMMAND

    def test_invalid_type_shows_error(self):
        """Test that invalid --type shows an error."""
        result = runner.invoke(app, ["--type", "invalid", "testuser/hello"])

        assert result.exit_code == 1
        assert "Unknown resource type" in result.output

    @patch("agr.cli.run.downloaded_repo")
    @patch("agr.cli.run.discover_runnable_resource")
    def test_not_found_shows_error(self, mock_discover, mock_download, tmp_path):
        """Test that not found resources show a helpful error."""
        mock_download.return_value.__enter__ = MagicMock(return_value=tmp_path)
        mock_download.return_value.__exit__ = MagicMock(return_value=None)

        mock_discover.return_value = DiscoveryResult(resources=[])

        result = runner.invoke(app, ["testuser/nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    @patch("agr.cli.run.downloaded_repo")
    @patch("agr.cli.run.discover_runnable_resource")
    def test_ambiguous_resource_shows_error(self, mock_discover, mock_download, tmp_path):
        """Test that ambiguous resources show an error with --type suggestion."""
        mock_download.return_value.__enter__ = MagicMock(return_value=tmp_path)
        mock_download.return_value.__exit__ = MagicMock(return_value=None)

        mock_discover.return_value = DiscoveryResult(
            resources=[
                DiscoveredResource(
                    name="hello",
                    resource_type=ResourceType.SKILL,
                    path_segments=["hello"]
                ),
                DiscoveredResource(
                    name="hello",
                    resource_type=ResourceType.COMMAND,
                    path_segments=["hello"]
                ),
            ]
        )

        result = runner.invoke(app, ["testuser/hello"])

        assert result.exit_code == 1
        assert "multiple types" in result.output.lower()
        assert "--type" in result.output


class TestDeprecatedAgrxCommands:
    """Tests for deprecated agrx subcommands."""

    @patch("agr.cli.run._run_resource")
    def test_agrx_skill_shows_deprecation_warning(self, mock_run):
        """Test that 'agrx skill' shows deprecation warning."""
        result = runner.invoke(app, ["skill", "testuser/hello-world"])

        assert "deprecated" in result.output.lower()
        assert "agrx testuser/hello-world" in result.output

    @patch("agr.cli.run._run_resource")
    def test_agrx_command_shows_deprecation_warning(self, mock_run):
        """Test that 'agrx command' shows deprecation warning."""
        result = runner.invoke(app, ["command", "testuser/hello"])

        assert "deprecated" in result.output.lower()
        assert "agrx testuser/hello" in result.output

    @patch("agr.cli.run._run_resource")
    def test_deprecated_skill_still_works(self, mock_run):
        """Test that deprecated commands call runner."""
        result = runner.invoke(app, ["skill", "testuser/hello-world"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][1] == ResourceType.SKILL

    @patch("agr.cli.run._run_resource")
    def test_deprecated_commands_pass_interactive(self, mock_run):
        """Test deprecated commands pass interactive flag."""
        result = runner.invoke(app, ["--interactive", "skill", "testuser/hello-world"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][3] is True  # interactive=True

    @patch("agr.cli.run._run_resource")
    def test_deprecated_commands_with_prompt(self, mock_run):
        """Test deprecated commands pass prompt argument."""
        result = runner.invoke(app, ["skill", "testuser/hello-world", "my prompt"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][2] == "my prompt"  # prompt_or_args
