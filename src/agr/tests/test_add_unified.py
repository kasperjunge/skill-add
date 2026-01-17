"""Integration tests for unified add command."""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path

from agr.cli.main import app
from agr.fetcher import ResourceType, DiscoveredResource, DiscoveryResult


runner = CliRunner()


class TestAddUnifiedCommand:
    """Tests for the unified add command."""

    @patch("agr.cli.common.downloaded_repo")
    @patch("agr.cli.common.discover_resource_type_from_dir")
    @patch("agr.cli.common.fetch_resource_from_repo_dir")
    def test_auto_detects_skill(self, mock_fetch, mock_discover, mock_download, tmp_path):
        """Test that auto-detection correctly identifies a skill."""
        mock_download.return_value.__enter__ = MagicMock(return_value=tmp_path)
        mock_download.return_value.__exit__ = MagicMock(return_value=None)

        mock_discover.return_value = DiscoveryResult(
            resources=[
                DiscoveredResource(
                    name="hello-world",
                    resource_type=ResourceType.SKILL,
                    path_segments=["hello-world"]
                )
            ]
        )

        result = runner.invoke(app, ["add", "testuser/hello-world"])

        # Verify the skill type was detected
        mock_discover.assert_called_once()
        mock_fetch.assert_called_once()
        # Verify correct resource type was passed to fetch
        call_args = mock_fetch.call_args
        assert call_args[0][4] == ResourceType.SKILL  # resource_type argument

    @patch("agr.cli.common.fetch_resource")
    def test_explicit_type_skill(self, mock_fetch):
        """Test that --type skill fetches a skill."""
        result = runner.invoke(app, ["add", "--type", "skill", "testuser/hello-world"])

        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args
        assert call_args[0][5] == ResourceType.SKILL  # resource_type is 6th positional arg

    @patch("agr.cli.common.fetch_resource")
    def test_explicit_type_command(self, mock_fetch):
        """Test that --type command fetches a command."""
        result = runner.invoke(app, ["add", "--type", "command", "testuser/hello"])

        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args
        assert call_args[0][5] == ResourceType.COMMAND

    @patch("agr.cli.common.fetch_resource")
    def test_explicit_type_agent(self, mock_fetch):
        """Test that --type agent fetches an agent."""
        result = runner.invoke(app, ["add", "--type", "agent", "testuser/hello-agent"])

        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args
        assert call_args[0][5] == ResourceType.AGENT

    @patch("agr.cli.common.fetch_bundle")
    def test_explicit_type_bundle(self, mock_fetch):
        """Test that --type bundle fetches a bundle."""
        from agr.fetcher import BundleInstallResult
        mock_fetch.return_value = BundleInstallResult(installed_skills=["test"])

        result = runner.invoke(app, ["add", "--type", "bundle", "testuser/my-bundle"])

        mock_fetch.assert_called_once()

    # Tests for --type AFTER resource reference (common user pattern)
    @patch("agr.cli.common.fetch_resource")
    def test_explicit_type_after_ref_skill(self, mock_fetch):
        """Test that 'agr add ref --type skill' works (type after resource)."""
        result = runner.invoke(app, ["add", "testuser/hello-world", "--type", "skill"])

        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args
        assert call_args[0][5] == ResourceType.SKILL

    @patch("agr.cli.common.fetch_resource")
    def test_explicit_type_after_ref_command(self, mock_fetch):
        """Test that 'agr add ref --type command' works (type after resource)."""
        result = runner.invoke(app, ["add", "testuser/hello", "--type", "command"])

        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args
        assert call_args[0][5] == ResourceType.COMMAND

    @patch("agr.cli.common.fetch_resource")
    def test_explicit_type_after_ref_agent(self, mock_fetch):
        """Test that 'agr add ref --type agent' works (type after resource)."""
        result = runner.invoke(app, ["add", "testuser/hello-agent", "--type", "agent"])

        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args
        assert call_args[0][5] == ResourceType.AGENT

    @patch("agr.cli.common.fetch_resource")
    def test_explicit_type_short_flag_after_ref(self, mock_fetch):
        """Test that 'agr add ref -t command' works (short flag after resource)."""
        result = runner.invoke(app, ["add", "testuser/hello", "-t", "command"])

        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args
        assert call_args[0][5] == ResourceType.COMMAND

    def test_invalid_type_shows_error(self):
        """Test that invalid --type shows an error."""
        result = runner.invoke(app, ["add", "--type", "invalid", "testuser/hello"])

        assert result.exit_code == 1
        assert "Unknown resource type" in result.output

    @patch("agr.cli.common.downloaded_repo")
    @patch("agr.cli.common.discover_resource_type_from_dir")
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

        result = runner.invoke(app, ["add", "testuser/hello"])

        assert result.exit_code == 1
        assert "multiple types" in result.output.lower()
        assert "--type" in result.output

    @patch("agr.cli.common.downloaded_repo")
    @patch("agr.cli.common.discover_resource_type_from_dir")
    def test_not_found_shows_error(self, mock_discover, mock_download, tmp_path):
        """Test that not found resources show a helpful error."""
        mock_download.return_value.__enter__ = MagicMock(return_value=tmp_path)
        mock_download.return_value.__exit__ = MagicMock(return_value=None)

        mock_discover.return_value = DiscoveryResult(resources=[])

        result = runner.invoke(app, ["add", "testuser/nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestDeprecatedAddCommands:
    """Tests for deprecated add subcommands."""

    @patch("agr.cli.common.handle_add_resource")
    def test_add_skill_shows_deprecation_warning(self, mock_handler):
        """Test that 'agr add skill' shows deprecation warning."""
        result = runner.invoke(app, ["add", "skill", "testuser/hello-world"])

        assert "deprecated" in result.output.lower()
        assert "agr add testuser/hello-world" in result.output

    @patch("agr.cli.common.handle_add_resource")
    def test_add_command_shows_deprecation_warning(self, mock_handler):
        """Test that 'agr add command' shows deprecation warning."""
        result = runner.invoke(app, ["add", "command", "testuser/hello"])

        assert "deprecated" in result.output.lower()
        assert "agr add testuser/hello" in result.output

    @patch("agr.cli.common.handle_add_resource")
    def test_add_agent_shows_deprecation_warning(self, mock_handler):
        """Test that 'agr add agent' shows deprecation warning."""
        result = runner.invoke(app, ["add", "agent", "testuser/hello-agent"])

        assert "deprecated" in result.output.lower()
        assert "agr add testuser/hello-agent" in result.output

    @patch("agr.cli.common.handle_add_bundle")
    def test_add_bundle_shows_deprecation_warning(self, mock_handler):
        """Test that 'agr add bundle' shows deprecation warning."""
        result = runner.invoke(app, ["add", "bundle", "testuser/my-bundle"])

        assert "deprecated" in result.output.lower()
        assert "agr add testuser/my-bundle" in result.output

    @patch("agr.cli.add.handle_add_resource")
    def test_deprecated_skill_still_works(self, mock_handler):
        """Test that deprecated skill command calls handler."""
        result = runner.invoke(app, ["add", "skill", "testuser/hello-world"])

        mock_handler.assert_called_once()
        call_args = mock_handler.call_args
        assert call_args[0][1] == ResourceType.SKILL

    @patch("agr.cli.add.handle_add_resource")
    def test_deprecated_commands_pass_overwrite(self, mock_handler):
        """Test that deprecated commands pass flags correctly."""
        result = runner.invoke(app, ["add", "--overwrite", "skill", "testuser/hello-world"])

        mock_handler.assert_called_once()
        call_args = mock_handler.call_args
        assert call_args[0][3] is True  # overwrite=True
