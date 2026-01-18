"""Unit tests for resource discovery functions."""

import tempfile
from pathlib import Path

import pytest

from agr.fetcher import (
    DiscoveredResource,
    DiscoveryResult,
    ResourceType,
    discover_resource_type_from_dir,
)
from agr.cli.common import discover_local_resource_type


class TestDiscoveryResult:
    """Tests for DiscoveryResult dataclass properties."""

    def test_is_unique_single_resource(self):
        """Test is_unique returns True for single resource."""
        result = DiscoveryResult(resources=[
            DiscoveredResource(name="test", resource_type=ResourceType.SKILL, path_segments=["test"])
        ])
        assert result.is_unique is True
        assert result.is_ambiguous is False
        assert result.is_empty is False

    def test_is_unique_bundle_only(self):
        """Test is_unique returns True for bundle only."""
        result = DiscoveryResult(resources=[], is_bundle=True)
        assert result.is_unique is True
        assert result.is_ambiguous is False
        assert result.is_empty is False

    def test_is_ambiguous_multiple_resources(self):
        """Test is_ambiguous returns True for multiple resources."""
        result = DiscoveryResult(resources=[
            DiscoveredResource(name="test", resource_type=ResourceType.SKILL, path_segments=["test"]),
            DiscoveredResource(name="test", resource_type=ResourceType.COMMAND, path_segments=["test"]),
        ])
        assert result.is_unique is False
        assert result.is_ambiguous is True

    def test_is_ambiguous_resource_and_bundle(self):
        """Test is_ambiguous returns True for resource + bundle."""
        result = DiscoveryResult(
            resources=[
                DiscoveredResource(name="test", resource_type=ResourceType.SKILL, path_segments=["test"])
            ],
            is_bundle=True
        )
        assert result.is_unique is False
        assert result.is_ambiguous is True

    def test_is_empty_no_resources(self):
        """Test is_empty returns True when no resources found."""
        result = DiscoveryResult(resources=[])
        assert result.is_empty is True
        assert result.is_unique is False

    def test_found_types_list(self):
        """Test found_types returns correct type names."""
        result = DiscoveryResult(
            resources=[
                DiscoveredResource(name="test", resource_type=ResourceType.SKILL, path_segments=["test"]),
                DiscoveredResource(name="test", resource_type=ResourceType.COMMAND, path_segments=["test"]),
            ],
            is_bundle=True
        )
        assert sorted(result.found_types) == ["bundle", "command", "skill"]


class TestDiscoverResourceTypeFromDir:
    """Tests for discover_resource_type_from_dir function."""

    def test_discovers_skill(self, tmp_path):
        """Test discovering a skill resource."""
        # Create skill directory structure
        skill_dir = tmp_path / ".claude" / "skills" / "hello-world"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Hello World Skill")

        result = discover_resource_type_from_dir(tmp_path, "hello-world", ["hello-world"])

        assert result.is_unique is True
        assert len(result.resources) == 1
        assert result.resources[0].resource_type == ResourceType.SKILL

    def test_discovers_command(self, tmp_path):
        """Test discovering a command resource."""
        # Create command file
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "hello.md").write_text("# Hello Command")

        result = discover_resource_type_from_dir(tmp_path, "hello", ["hello"])

        assert result.is_unique is True
        assert len(result.resources) == 1
        assert result.resources[0].resource_type == ResourceType.COMMAND

    def test_discovers_agent(self, tmp_path):
        """Test discovering an agent resource."""
        # Create agent file
        agents_dir = tmp_path / ".claude" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "hello-agent.md").write_text("# Hello Agent")

        result = discover_resource_type_from_dir(tmp_path, "hello-agent", ["hello-agent"])

        assert result.is_unique is True
        assert len(result.resources) == 1
        assert result.resources[0].resource_type == ResourceType.AGENT

    def test_discovers_bundle(self, tmp_path):
        """Test discovering a bundle resource."""
        # Create bundle structure with a skill inside
        bundle_skill_dir = tmp_path / ".claude" / "skills" / "my-bundle" / "test-skill"
        bundle_skill_dir.mkdir(parents=True)
        (bundle_skill_dir / "SKILL.md").write_text("# Test Skill")

        result = discover_resource_type_from_dir(tmp_path, "my-bundle", ["my-bundle"])

        assert result.is_bundle is True

    def test_discovers_multiple_types(self, tmp_path):
        """Test discovering when name exists in multiple types."""
        # Create both skill and command with same name
        skill_dir = tmp_path / ".claude" / "skills" / "hello"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Hello Skill")

        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "hello.md").write_text("# Hello Command")

        result = discover_resource_type_from_dir(tmp_path, "hello", ["hello"])

        assert result.is_ambiguous is True
        assert len(result.resources) == 2
        types = [r.resource_type for r in result.resources]
        assert ResourceType.SKILL in types
        assert ResourceType.COMMAND in types

    def test_discovers_nothing(self, tmp_path):
        """Test when resource doesn't exist."""
        # Create empty .claude directory
        (tmp_path / ".claude").mkdir(parents=True)

        result = discover_resource_type_from_dir(tmp_path, "nonexistent", ["nonexistent"])

        assert result.is_empty is True


class TestDiscoverLocalResourceType:
    """Tests for discover_local_resource_type function."""

    def test_discovers_local_skill(self, tmp_path, monkeypatch):
        """Test discovering a locally installed skill."""
        # Create skill directory
        skill_dir = tmp_path / ".claude" / "skills" / "hello-world"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Hello World Skill")

        # Patch Path.cwd() to return our tmp_path
        monkeypatch.chdir(tmp_path)

        result = discover_local_resource_type("hello-world", global_install=False)

        assert result.is_unique is True
        assert result.resources[0].resource_type == ResourceType.SKILL

    def test_discovers_local_command(self, tmp_path, monkeypatch):
        """Test discovering a locally installed command."""
        # Create command file
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "hello.md").write_text("# Hello Command")

        monkeypatch.chdir(tmp_path)

        result = discover_local_resource_type("hello", global_install=False)

        assert result.is_unique is True
        assert result.resources[0].resource_type == ResourceType.COMMAND

    def test_discovers_local_agent(self, tmp_path, monkeypatch):
        """Test discovering a locally installed agent."""
        # Create agent file
        agents_dir = tmp_path / ".claude" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "hello-agent.md").write_text("# Hello Agent")

        monkeypatch.chdir(tmp_path)

        result = discover_local_resource_type("hello-agent", global_install=False)

        assert result.is_unique is True
        assert result.resources[0].resource_type == ResourceType.AGENT

    def test_discovers_local_multiple_types(self, tmp_path, monkeypatch):
        """Test discovering when name exists in multiple local types."""
        # Create both skill and command with same name
        skill_dir = tmp_path / ".claude" / "skills" / "hello"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Hello Skill")

        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "hello.md").write_text("# Hello Command")

        monkeypatch.chdir(tmp_path)

        result = discover_local_resource_type("hello", global_install=False)

        assert result.is_ambiguous is True
        assert len(result.resources) == 2

    def test_discovers_nothing_locally(self, tmp_path, monkeypatch):
        """Test when resource doesn't exist locally."""
        (tmp_path / ".claude").mkdir(parents=True)
        monkeypatch.chdir(tmp_path)

        result = discover_local_resource_type("nonexistent", global_install=False)

        assert result.is_empty is True
