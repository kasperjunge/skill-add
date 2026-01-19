"""Tests for agr/constants.py."""

from agr.constants import (
    TOOL_DIR_NAME,
    SKILLS_SUBDIR,
    COMMANDS_SUBDIR,
    AGENTS_SUBDIR,
    PACKAGES_SUBDIR,
)


class TestToolDirName:
    """Tests for TOOL_DIR_NAME constant."""

    def test_tool_dir_name_value(self):
        """Test that TOOL_DIR_NAME is .claude."""
        assert TOOL_DIR_NAME == ".claude"

    def test_tool_dir_name_is_string(self):
        """Test that TOOL_DIR_NAME is a string."""
        assert isinstance(TOOL_DIR_NAME, str)


class TestSubdirConstants:
    """Tests for subdirectory name constants."""

    def test_skills_subdir(self):
        """Test that SKILLS_SUBDIR is skills."""
        assert SKILLS_SUBDIR == "skills"

    def test_commands_subdir(self):
        """Test that COMMANDS_SUBDIR is commands."""
        assert COMMANDS_SUBDIR == "commands"

    def test_agents_subdir(self):
        """Test that AGENTS_SUBDIR is agents."""
        assert AGENTS_SUBDIR == "agents"

    def test_packages_subdir(self):
        """Test that PACKAGES_SUBDIR is packages."""
        assert PACKAGES_SUBDIR == "packages"

    def test_all_subdirs_are_strings(self):
        """Test that all subdir constants are strings."""
        assert isinstance(SKILLS_SUBDIR, str)
        assert isinstance(COMMANDS_SUBDIR, str)
        assert isinstance(AGENTS_SUBDIR, str)
        assert isinstance(PACKAGES_SUBDIR, str)
