"""Unit tests for remote resource resolution."""

import pytest
from pathlib import Path

from agr.resolver import (
    ResolvedResource,
    ResourceSource,
    resolve_remote_resource,
    parse_remote_agr_toml,
)
from agr.fetcher import ResourceType


class TestResolvedResource:
    """Tests for ResolvedResource dataclass."""

    def test_creates_resolved_resource(self):
        """Test creating a ResolvedResource."""
        resource = ResolvedResource(
            name="my-skill",
            resource_type=ResourceType.SKILL,
            path=Path(".claude/skills/my-skill"),
            source=ResourceSource.CLAUDE_DIR,
        )
        assert resource.name == "my-skill"
        assert resource.resource_type == ResourceType.SKILL
        assert resource.source == ResourceSource.CLAUDE_DIR

    def test_resolved_from_agr_toml(self):
        """Test creating a resource resolved from agr.toml."""
        resource = ResolvedResource(
            name="custom-skill",
            resource_type=ResourceType.SKILL,
            path=Path("skills/custom-skill"),
            source=ResourceSource.AGR_TOML,
        )
        assert resource.source == ResourceSource.AGR_TOML


class TestParseRemoteAgrToml:
    """Tests for parse_remote_agr_toml function."""

    def test_parses_resource_section(self, tmp_path):
        """Test parsing [resource.*] sections from agr.toml."""
        agr_toml = tmp_path / "agr.toml"
        agr_toml.write_text("""
[dependencies]

[resource.my-skill]
path = "skills/my-skill"
type = "skill"

[resource.my-cmd]
path = "commands/my-cmd.md"
type = "command"
""")
        result = parse_remote_agr_toml(tmp_path)

        assert "my-skill" in result
        assert result["my-skill"]["path"] == "skills/my-skill"
        assert result["my-skill"]["type"] == "skill"
        assert "my-cmd" in result
        assert result["my-cmd"]["type"] == "command"

    def test_parses_package_section(self, tmp_path):
        """Test parsing [package.*] sections from agr.toml."""
        agr_toml = tmp_path / "agr.toml"
        agr_toml.write_text("""
[package.my-toolkit]
path = "packages/my-toolkit"
""")
        result = parse_remote_agr_toml(tmp_path)

        assert "my-toolkit" in result
        assert result["my-toolkit"]["path"] == "packages/my-toolkit"
        assert result["my-toolkit"].get("package") is True

    def test_returns_empty_when_no_agr_toml(self, tmp_path):
        """Test returning empty dict when no agr.toml exists."""
        result = parse_remote_agr_toml(tmp_path)
        assert result == {}

    def test_returns_empty_when_no_resource_sections(self, tmp_path):
        """Test returning empty dict when only dependencies section exists."""
        agr_toml = tmp_path / "agr.toml"
        agr_toml.write_text("""
[dependencies]
"kasperjunge/commit" = {}
""")
        result = parse_remote_agr_toml(tmp_path)
        assert result == {}


class TestResolveRemoteResource:
    """Tests for resolve_remote_resource function."""

    def test_resolves_from_agr_toml_first(self, tmp_path):
        """Test that agr.toml definitions take priority over .claude/."""
        # Create agr.toml with resource definition
        agr_toml = tmp_path / "agr.toml"
        agr_toml.write_text("""
[resource.my-skill]
path = "custom/path/my-skill"
type = "skill"
""")

        # Also create in .claude/ (should be ignored)
        claude_skill = tmp_path / ".claude" / "skills" / "my-skill"
        claude_skill.mkdir(parents=True)
        (claude_skill / "SKILL.md").write_text("# Skill from .claude")

        # Also create in custom path
        custom_skill = tmp_path / "custom" / "path" / "my-skill"
        custom_skill.mkdir(parents=True)
        (custom_skill / "SKILL.md").write_text("# Skill from custom path")

        result = resolve_remote_resource(tmp_path, "my-skill")

        assert result is not None
        assert result.source == ResourceSource.AGR_TOML
        assert result.path == Path("custom/path/my-skill")

    def test_falls_back_to_claude_dir(self, tmp_path):
        """Test fallback to .claude/ when not in agr.toml."""
        # Only create in .claude/
        claude_skill = tmp_path / ".claude" / "skills" / "my-skill"
        claude_skill.mkdir(parents=True)
        (claude_skill / "SKILL.md").write_text("# Skill from .claude")

        result = resolve_remote_resource(tmp_path, "my-skill")

        assert result is not None
        assert result.source == ResourceSource.CLAUDE_DIR
        assert result.resource_type == ResourceType.SKILL

    def test_returns_none_when_not_found(self, tmp_path):
        """Test returning None when resource doesn't exist."""
        result = resolve_remote_resource(tmp_path, "nonexistent")
        assert result is None

    def test_resolves_command_from_claude_dir(self, tmp_path):
        """Test resolving a command from .claude/ directory."""
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "my-cmd.md").write_text("# My Command")

        result = resolve_remote_resource(tmp_path, "my-cmd")

        assert result is not None
        assert result.resource_type == ResourceType.COMMAND
        assert result.source == ResourceSource.CLAUDE_DIR

    def test_resolves_agent_from_claude_dir(self, tmp_path):
        """Test resolving an agent from .claude/ directory."""
        agents_dir = tmp_path / ".claude" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "my-agent.md").write_text("# My Agent")

        result = resolve_remote_resource(tmp_path, "my-agent")

        assert result is not None
        assert result.resource_type == ResourceType.AGENT
        assert result.source == ResourceSource.CLAUDE_DIR

    def test_resolves_package_from_agr_toml(self, tmp_path):
        """Test resolving a package from agr.toml."""
        agr_toml = tmp_path / "agr.toml"
        agr_toml.write_text("""
[package.my-toolkit]
path = "packages/my-toolkit"
""")

        # Create package structure
        pkg_dir = tmp_path / "packages" / "my-toolkit" / "skills" / "toolkit-skill"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "SKILL.md").write_text("# Toolkit Skill")

        result = resolve_remote_resource(tmp_path, "my-toolkit")

        assert result is not None
        assert result.source == ResourceSource.AGR_TOML
        assert result.is_package is True

    def test_resolves_package_from_claude_bundle(self, tmp_path):
        """Test resolving a package/bundle from .claude/ directory."""
        # Create bundle structure in .claude/
        bundle_skill = tmp_path / ".claude" / "skills" / "my-bundle" / "bundle-skill"
        bundle_skill.mkdir(parents=True)
        (bundle_skill / "SKILL.md").write_text("# Bundle Skill")

        result = resolve_remote_resource(tmp_path, "my-bundle")

        assert result is not None
        assert result.source == ResourceSource.CLAUDE_DIR
        assert result.is_package is True

    def test_type_override_from_agr_toml(self, tmp_path):
        """Test that type specified in agr.toml is used."""
        agr_toml = tmp_path / "agr.toml"
        agr_toml.write_text("""
[resource.helper]
path = "lib/helper"
type = "skill"
""")

        # Create the skill at custom path
        skill_dir = tmp_path / "lib" / "helper"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Helper")

        result = resolve_remote_resource(tmp_path, "helper")

        assert result is not None
        assert result.resource_type == ResourceType.SKILL
        assert result.source == ResourceSource.AGR_TOML
