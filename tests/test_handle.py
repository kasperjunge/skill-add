"""Tests for centralized handle parsing and conversion module."""

from pathlib import Path

import pytest

from agr.handle import (
    ParsedHandle,
    parse_handle,
    skill_dirname_to_toml_handle,
    toml_handle_to_skill_dirname,
)


class TestParseHandle:
    """Test handle parsing for all formats."""

    def test_empty_string(self):
        """Test parsing empty string."""
        result = parse_handle("")
        assert result.username is None
        assert result.name == ""
        assert result.path_segments == []

    def test_simple_name(self):
        """Test parsing simple resource name."""
        result = parse_handle("seo")
        assert result.username is None
        assert result.name == "seo"
        assert result.simple_name == "seo"
        assert result.path_segments == ["seo"]

    def test_two_part_slash(self):
        """Test parsing user/name format."""
        result = parse_handle("kasperjunge/seo")
        assert result.username == "kasperjunge"
        assert result.name == "seo"
        assert result.repo is None
        assert result.path_segments == ["seo"]

    def test_three_part_slash(self):
        """Test parsing user/repo/name format (second part is repo)."""
        result = parse_handle("user/repo/command")
        assert result.username == "user"
        assert result.repo == "repo"
        assert result.name == "command"
        assert result.path_segments == ["command"]

    def test_four_part_slash(self):
        """Test parsing user/repo/path/name format."""
        result = parse_handle("user/nested/more/name")
        assert result.username == "user"
        assert result.repo == "nested"
        assert result.name == "name"
        assert result.path_segments == ["more", "name"]

    def test_colon_format_simple(self):
        """Test parsing user:name colon format."""
        result = parse_handle("kasperjunge:seo")
        assert result.username == "kasperjunge"
        assert result.name == "seo"
        assert result.path_segments == ["seo"]

    def test_colon_format_nested(self):
        """Test parsing user:nested:name colon format."""
        result = parse_handle("kasperjunge:product-strategy:growth-hacker")
        assert result.username == "kasperjunge"
        assert result.name == "growth-hacker"
        assert result.path_segments == ["product-strategy", "growth-hacker"]


class TestParsedHandleSimpleName:
    """Test the simple_name property."""

    def test_simple_name_from_simple_input(self):
        """simple_name returns the name when there are no segments."""
        parsed = ParsedHandle(name="test")
        assert parsed.simple_name == "test"

    def test_simple_name_from_segments(self):
        """simple_name returns last segment."""
        parsed = ParsedHandle(name="ignored", path_segments=["nested", "actual"])
        assert parsed.simple_name == "actual"


class TestParsedHandleToTomlHandle:
    """Test conversion to toml handle format."""

    def test_to_toml_handle_simple(self):
        """Test conversion with username and simple name."""
        parsed = ParsedHandle(username="kasperjunge", name="seo", path_segments=["seo"])
        assert parsed.to_toml_handle() == "kasperjunge/seo"

    def test_to_toml_handle_with_repo(self):
        """Test conversion with explicit repo."""
        parsed = ParsedHandle(
            username="user", repo="repo", name="cmd", path_segments=["cmd"]
        )
        assert parsed.to_toml_handle() == "user/repo/cmd"

    def test_to_toml_handle_nested(self):
        """Test conversion with nested path segments."""
        parsed = ParsedHandle(
            username="kasperjunge",
            name="growth-hacker",
            path_segments=["product-strategy", "growth-hacker"],
        )
        assert parsed.to_toml_handle() == "kasperjunge/product-strategy/growth-hacker"

    def test_to_toml_handle_no_username(self):
        """Test conversion without username returns just name."""
        parsed = ParsedHandle(name="seo", path_segments=["seo"])
        assert parsed.to_toml_handle() == "seo"


class TestParsedHandleToSkillDirname:
    """Test conversion to skill directory name format."""

    def test_to_skill_dirname_simple(self):
        """Test conversion with username and simple name."""
        parsed = ParsedHandle(username="kasperjunge", name="seo", path_segments=["seo"])
        assert parsed.to_skill_dirname() == "kasperjunge:seo"

    def test_to_skill_dirname_nested(self):
        """Test conversion with nested path segments."""
        parsed = ParsedHandle(
            username="kasperjunge",
            name="growth-hacker",
            path_segments=["product-strategy", "growth-hacker"],
        )
        assert parsed.to_skill_dirname() == "kasperjunge:product-strategy:growth-hacker"

    def test_to_skill_dirname_no_username(self):
        """Test conversion without username returns just name."""
        parsed = ParsedHandle(name="seo", path_segments=["seo"])
        assert parsed.to_skill_dirname() == "seo"


class TestMatchesTomlHandle:
    """Test handle matching logic."""

    def test_exact_match(self):
        """Test exact match between parsed and toml handle."""
        parsed = parse_handle("kasperjunge/seo")
        assert parsed.matches_toml_handle("kasperjunge/seo")

    def test_simple_name_matches_full(self):
        """Test simple name matches full handle."""
        parsed = parse_handle("seo")
        assert parsed.matches_toml_handle("kasperjunge/seo")

    def test_different_username_no_match(self):
        """Test different usernames don't match."""
        parsed = parse_handle("other/seo")
        assert not parsed.matches_toml_handle("kasperjunge/seo")

    def test_colon_format_matches_slash(self):
        """Test colon format matches slash format."""
        parsed = parse_handle("kasperjunge:seo")
        assert parsed.matches_toml_handle("kasperjunge/seo")


class TestSkillDirnameToTomlHandle:
    """Test reverse conversion from dirname to toml handle."""

    def test_simple(self):
        """Test simple conversion."""
        assert skill_dirname_to_toml_handle("kasperjunge:seo") == "kasperjunge/seo"

    def test_nested(self):
        """Test nested conversion."""
        result = skill_dirname_to_toml_handle("kasperjunge:product-strategy:growth-hacker")
        assert result == "kasperjunge/product-strategy/growth-hacker"


class TestTomlHandleToSkillDirname:
    """Test conversion from toml handle to dirname."""

    def test_simple(self):
        """Test simple conversion."""
        assert toml_handle_to_skill_dirname("kasperjunge/seo") == "kasperjunge:seo"

    def test_nested(self):
        """Test nested conversion with 4-part handle (path_segments after repo)."""
        result = toml_handle_to_skill_dirname("kasperjunge/repo/product-strategy/growth-hacker")
        assert result == "kasperjunge:product-strategy:growth-hacker"

    def test_with_nested_path(self):
        """Test 3-part handle conversion (repo not in dirname)."""
        result = toml_handle_to_skill_dirname("user/nested/skill")
        assert result == "user:skill"

    def test_maragudk_skills_collaboration(self):
        """Test maragudk/skills/collaboration: repo not in dirname."""
        result = toml_handle_to_skill_dirname("maragudk/skills/collaboration")
        assert result == "maragudk:collaboration"


class TestRoundTrip:
    """Test round-trip conversions."""

    def test_toml_to_dirname_to_toml(self):
        """Test toml -> dirname -> toml round trip."""
        original = "kasperjunge/seo"
        dirname = toml_handle_to_skill_dirname(original)
        back = skill_dirname_to_toml_handle(dirname)
        assert back == original

    def test_dirname_to_toml_to_dirname(self):
        """Test dirname -> toml -> dirname round trip."""
        original = "kasperjunge:seo"
        toml = skill_dirname_to_toml_handle(original)
        back = toml_handle_to_skill_dirname(toml)
        assert back == original


class TestParsedHandleToSkillPath:
    """Test skill path building with flattened colon format."""

    def test_with_username(self):
        """Test skill path with username uses flattened colon format."""
        handle = ParsedHandle(username="kasperjunge", name="seo", path_segments=["seo"])
        result = handle.to_skill_path(Path(".claude"))
        assert result == Path(".claude/skills/kasperjunge:seo")

    def test_nested_path_segments(self):
        """Test skill path with nested path segments."""
        handle = ParsedHandle(
            username="kasperjunge",
            name="growth-hacker",
            path_segments=["product-strategy", "growth-hacker"],
        )
        result = handle.to_skill_path(Path(".claude"))
        assert result == Path(".claude/skills/kasperjunge:product-strategy:growth-hacker")


class TestParsedHandleToCommandPath:
    """Test command path building with nested format."""

    def test_with_username(self):
        """Test command path with username uses nested format."""
        handle = ParsedHandle(username="kasperjunge", name="commit", path_segments=["commit"])
        result = handle.to_command_path(Path(".claude"))
        assert result == Path(".claude/commands/kasperjunge/commit.md")

    def test_with_nested_path_segments(self):
        """Test command path with nested segments includes full path."""
        handle = ParsedHandle(
            username="user",
            name="deploy",
            path_segments=["pkg", "infra", "deploy"],
        )
        result = handle.to_command_path(Path(".claude"))
        assert result == Path(".claude/commands/user/pkg/infra/deploy.md")


class TestParsedHandleToResourcePath:
    """Test resource path dispatch by type."""

    def test_skill_type(self):
        """Test resource path for skill type."""
        handle = ParsedHandle(username="user", name="skill", path_segments=["skill"])
        result = handle.to_resource_path(Path(".claude"), "skill")
        assert result == Path(".claude/skills/user:skill")

    def test_command_type(self):
        """Test resource path for command type."""
        handle = ParsedHandle(username="user", name="cmd", path_segments=["cmd"])
        result = handle.to_resource_path(Path(".claude"), "command")
        assert result == Path(".claude/commands/user/cmd.md")


class TestParsedHandleFromComponents:
    """Test factory method for creating ParsedHandle."""

    def test_basic_components(self):
        """Test creating handle from basic components."""
        handle = ParsedHandle.from_components("kasperjunge", "seo")
        assert handle.username == "kasperjunge"
        assert handle.name == "seo"
        assert handle.path_segments == ["seo"]
        assert handle.repo is None

    def test_path_building_round_trip(self):
        """Test that from_components produces correct paths."""
        handle = ParsedHandle.from_components("kasperjunge", "commit")
        assert handle.to_skill_path(Path(".claude")) == Path(".claude/skills/kasperjunge:commit")
        assert handle.to_command_path(Path(".claude")) == Path(".claude/commands/kasperjunge/commit.md")
