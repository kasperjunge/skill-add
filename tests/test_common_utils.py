"""Tests for shared utilities in agr/cli/common.py."""

import os
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agr.cli.common import (
    TYPE_TO_SUBDIR,
    console,
    extract_type_from_args,
    find_repo_root,
    is_local_path,
)
# Import private functions directly from handlers module for testing
from agr.cli.handlers import _add_to_agr_toml, _remove_from_agr_toml
from agr.exceptions import ConfigParseError
from agr.fetcher import ResourceType


class TestFindRepoRoot:
    """Tests for find_repo_root utility."""

    def test_finds_repo_root_in_git_repo(self, tmp_path):
        """Test that find_repo_root finds the .git directory."""
        # Create a git repo structure
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)

        # Change to nested directory and test
        original_cwd = os.getcwd()
        try:
            os.chdir(subdir)
            root = find_repo_root()
            assert root == tmp_path
        finally:
            os.chdir(original_cwd)

    def test_returns_cwd_when_not_in_repo(self, tmp_path):
        """Test that find_repo_root returns cwd when not in a git repo."""
        subdir = tmp_path / "not_a_repo" / "subdir"
        subdir.mkdir(parents=True)

        original_cwd = os.getcwd()
        try:
            os.chdir(subdir)
            root = find_repo_root()
            assert root == subdir
        finally:
            os.chdir(original_cwd)


class TestIsLocalPath:
    """Tests for is_local_path utility."""

    def test_recognizes_dot_slash(self):
        """Test that ./path is recognized as local."""
        assert is_local_path("./path/to/file") is True

    def test_recognizes_absolute_path(self):
        """Test that /absolute/path is recognized as local."""
        assert is_local_path("/absolute/path") is True

    def test_recognizes_parent_path(self):
        """Test that ../parent/path is recognized as local."""
        assert is_local_path("../parent/path") is True

    def test_rejects_remote_ref(self):
        """Test that username/name is not recognized as local."""
        assert is_local_path("kasperjunge/commit") is False

    def test_rejects_remote_ref_with_repo(self):
        """Test that username/repo/name is not recognized as local."""
        assert is_local_path("kasperjunge/repo/name") is False

    def test_rejects_simple_name(self):
        """Test that simple name is not recognized as local."""
        assert is_local_path("my-skill") is False


class TestExtractTypeFromArgs:
    """Tests for extract_type_from_args utility."""

    def test_returns_explicit_type_when_provided(self):
        """Test that explicit type takes precedence."""
        args = ["my-skill", "--type", "command"]
        cleaned, resource_type = extract_type_from_args(args, "skill")
        assert resource_type == "skill"
        assert cleaned == args  # Args unchanged when explicit_type provided

    def test_extracts_type_from_args(self):
        """Test extraction of --type from args."""
        args = ["my-skill", "--type", "command"]
        cleaned, resource_type = extract_type_from_args(args, None)
        assert resource_type == "command"
        assert cleaned == ["my-skill"]

    def test_extracts_type_short_flag(self):
        """Test extraction of -t from args."""
        args = ["my-skill", "-t", "agent"]
        cleaned, resource_type = extract_type_from_args(args, None)
        assert resource_type == "agent"
        assert cleaned == ["my-skill"]

    def test_returns_none_when_no_type_in_args(self):
        """Test that None is returned when no type in args."""
        args = ["my-skill"]
        cleaned, resource_type = extract_type_from_args(args, None)
        assert resource_type is None
        assert cleaned == ["my-skill"]

    def test_handles_empty_args(self):
        """Test handling of empty args."""
        cleaned, resource_type = extract_type_from_args([], None)
        assert resource_type is None
        assert cleaned == []

    def test_handles_none_args(self):
        """Test handling of None args."""
        cleaned, resource_type = extract_type_from_args(None, None)
        assert resource_type is None
        assert cleaned == []

    def test_type_at_beginning(self):
        """Test extraction when --type is at the beginning."""
        args = ["--type", "skill", "my-skill"]
        cleaned, resource_type = extract_type_from_args(args, None)
        assert resource_type == "skill"
        assert cleaned == ["my-skill"]

    def test_preserves_other_args(self):
        """Test that other arguments are preserved."""
        args = ["my-skill", "--type", "skill", "--other", "value"]
        cleaned, resource_type = extract_type_from_args(args, None)
        assert resource_type == "skill"
        assert cleaned == ["my-skill", "--other", "value"]


class TestTypeToSubdir:
    """Tests for TYPE_TO_SUBDIR constant."""

    def test_contains_skill(self):
        """Test that skill maps to skills."""
        assert TYPE_TO_SUBDIR["skill"] == "skills"

    def test_contains_command(self):
        """Test that command maps to commands."""
        assert TYPE_TO_SUBDIR["command"] == "commands"

    def test_contains_agent(self):
        """Test that agent maps to agents."""
        assert TYPE_TO_SUBDIR["agent"] == "agents"

    def test_contains_package(self):
        """Test that package maps to packages."""
        assert TYPE_TO_SUBDIR["package"] == "packages"


class TestConsole:
    """Tests for shared console instance."""

    def test_console_is_initialized(self):
        """Test that console is a Console instance."""
        from rich.console import Console
        assert isinstance(console, Console)


class TestAddToAgrTomlWarnings:
    """Tests for _add_to_agr_toml exception handling."""

    @patch("agr.cli.handlers.get_or_create_config")
    @patch("agr.cli.handlers.console")
    def test_warns_on_config_parse_error(self, mock_console, mock_get_config):
        """Test that ConfigParseError triggers a warning message."""
        mock_get_config.side_effect = ConfigParseError("Invalid TOML syntax")

        # Should not raise, but should print a warning
        _add_to_agr_toml("testuser/skill", ResourceType.SKILL, global_install=False)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "Warning" in call_args
        assert "Could not add to agr.toml" in call_args

    @patch("agr.cli.handlers.get_or_create_config")
    @patch("agr.cli.handlers.console")
    def test_warns_on_value_error(self, mock_console, mock_get_config):
        """Test that ValueError triggers a warning message."""
        mock_get_config.side_effect = ValueError("Invalid value")

        _add_to_agr_toml("testuser/skill", ResourceType.SKILL, global_install=False)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "Warning" in call_args

    @patch("agr.cli.handlers.get_or_create_config")
    @patch("agr.cli.handlers.console")
    def test_warns_on_os_error(self, mock_console, mock_get_config):
        """Test that OSError triggers a warning message."""
        mock_get_config.side_effect = OSError("Permission denied")

        _add_to_agr_toml("testuser/skill", ResourceType.SKILL, global_install=False)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "Warning" in call_args

    @patch("agr.cli.handlers.console")
    def test_skips_for_global_install(self, mock_console):
        """Test that global installs skip agr.toml update entirely."""
        _add_to_agr_toml("testuser/skill", ResourceType.SKILL, global_install=True)

        # Should not print anything - global installs skip agr.toml
        mock_console.print.assert_not_called()


class TestRemoveFromAgrTomlWarnings:
    """Tests for _remove_from_agr_toml exception handling."""

    @patch("agr.config.find_config")
    @patch("agr.config.AgrConfig.load")
    @patch("agr.cli.handlers.console")
    def test_warns_on_config_parse_error(self, mock_console, mock_load, mock_find_config):
        """Test that ConfigParseError triggers a warning message."""
        mock_find_config.return_value = Path("/fake/agr.toml")
        mock_load.side_effect = ConfigParseError("Invalid TOML syntax")

        # Should not raise, but should print a warning
        _remove_from_agr_toml("test-skill", username=None, global_install=False)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "Warning" in call_args
        assert "Could not update agr.toml" in call_args

    @patch("agr.config.find_config")
    @patch("agr.config.AgrConfig.load")
    @patch("agr.cli.handlers.console")
    def test_warns_on_value_error(self, mock_console, mock_load, mock_find_config):
        """Test that ValueError triggers a warning message."""
        mock_find_config.return_value = Path("/fake/agr.toml")
        mock_load.side_effect = ValueError("Invalid value")

        _remove_from_agr_toml("test-skill", username=None, global_install=False)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "Warning" in call_args

    @patch("agr.config.find_config")
    @patch("agr.config.AgrConfig.load")
    @patch("agr.cli.handlers.console")
    def test_warns_on_os_error(self, mock_console, mock_load, mock_find_config):
        """Test that OSError triggers a warning message."""
        mock_find_config.return_value = Path("/fake/agr.toml")
        mock_load.side_effect = OSError("Permission denied")

        _remove_from_agr_toml("test-skill", username=None, global_install=False)

        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args[0][0]
        assert "Warning" in call_args

    @patch("agr.cli.handlers.console")
    def test_skips_for_global_install(self, mock_console):
        """Test that global installs skip agr.toml update entirely."""
        _remove_from_agr_toml("test-skill", username=None, global_install=True)

        # Should not print anything - global installs skip agr.toml
        mock_console.print.assert_not_called()
