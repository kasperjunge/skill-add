"""Unit tests for local resource discovery (authoring paths)."""

import pytest
from pathlib import Path

from agr.discovery import (
    LocalResource,
    LocalPackage,
    DiscoveryContext,
    discover_local_resources,
)
from agr.fetcher import ResourceType


class TestLocalResource:
    """Tests for LocalResource dataclass."""

    def test_creates_local_resource(self):
        """Test creating a LocalResource."""
        resource = LocalResource(
            name="my-skill",
            resource_type=ResourceType.SKILL,
            source_path=Path("skills/my-skill"),
        )
        assert resource.name == "my-skill"
        assert resource.resource_type == ResourceType.SKILL
        assert resource.source_path == Path("skills/my-skill")
        assert resource.package_name is None

    def test_creates_local_resource_with_package(self):
        """Test creating a LocalResource within a package."""
        resource = LocalResource(
            name="toolkit-skill",
            resource_type=ResourceType.SKILL,
            source_path=Path("packages/my-toolkit/skills/toolkit-skill"),
            package_name="my-toolkit",
        )
        assert resource.name == "toolkit-skill"
        assert resource.package_name == "my-toolkit"


class TestLocalPackage:
    """Tests for LocalPackage dataclass."""

    def test_creates_local_package(self):
        """Test creating a LocalPackage."""
        package = LocalPackage(
            name="my-toolkit",
            path=Path("packages/my-toolkit"),
            resources=[],
        )
        assert package.name == "my-toolkit"
        assert package.path == Path("packages/my-toolkit")
        assert package.resources == []

    def test_package_with_resources(self):
        """Test creating a LocalPackage with resources."""
        skill = LocalResource(
            name="toolkit-skill",
            resource_type=ResourceType.SKILL,
            source_path=Path("packages/my-toolkit/skills/toolkit-skill"),
            package_name="my-toolkit",
        )
        package = LocalPackage(
            name="my-toolkit",
            path=Path("packages/my-toolkit"),
            resources=[skill],
        )
        assert len(package.resources) == 1
        assert package.resources[0].name == "toolkit-skill"


class TestDiscoveryContext:
    """Tests for DiscoveryContext dataclass."""

    def test_creates_empty_context(self):
        """Test creating an empty DiscoveryContext."""
        context = DiscoveryContext(
            skills=[],
            commands=[],
            agents=[],
            packages=[],
        )
        assert len(context.skills) == 0
        assert len(context.commands) == 0
        assert len(context.agents) == 0
        assert len(context.packages) == 0

    def test_creates_populated_context(self):
        """Test creating a populated DiscoveryContext."""
        skill = LocalResource(
            name="my-skill",
            resource_type=ResourceType.SKILL,
            source_path=Path("skills/my-skill"),
        )
        command = LocalResource(
            name="my-cmd",
            resource_type=ResourceType.COMMAND,
            source_path=Path("commands/my-cmd.md"),
        )
        context = DiscoveryContext(
            skills=[skill],
            commands=[command],
            agents=[],
            packages=[],
        )
        assert len(context.skills) == 1
        assert len(context.commands) == 1


class TestDiscoverLocalResources:
    """Tests for discover_local_resources function."""

    def test_discovers_skills_in_convention_path(self, tmp_path):
        """Test discovering skills in skills/ directory."""
        # Create skill in convention path
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        context = discover_local_resources(tmp_path)

        assert len(context.skills) == 1
        assert context.skills[0].name == "my-skill"
        assert context.skills[0].resource_type == ResourceType.SKILL
        assert context.skills[0].package_name is None

    def test_discovers_commands_in_convention_path(self, tmp_path):
        """Test discovering commands in commands/ directory."""
        # Create command in convention path
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "quick-fix.md").write_text("# Quick Fix Command")

        context = discover_local_resources(tmp_path)

        assert len(context.commands) == 1
        assert context.commands[0].name == "quick-fix"
        assert context.commands[0].resource_type == ResourceType.COMMAND

    def test_discovers_agents_in_convention_path(self, tmp_path):
        """Test discovering agents in agents/ directory."""
        # Create agent in convention path
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "reviewer.md").write_text("# Reviewer Agent")

        context = discover_local_resources(tmp_path)

        assert len(context.agents) == 1
        assert context.agents[0].name == "reviewer"
        assert context.agents[0].resource_type == ResourceType.AGENT

    def test_discovers_packages(self, tmp_path):
        """Test discovering packages in packages/ directory."""
        # Create package structure
        pkg_skill_dir = tmp_path / "packages" / "my-toolkit" / "skills" / "toolkit-skill"
        pkg_skill_dir.mkdir(parents=True)
        (pkg_skill_dir / "SKILL.md").write_text("# Toolkit Skill")

        pkg_cmd_dir = tmp_path / "packages" / "my-toolkit" / "commands"
        pkg_cmd_dir.mkdir(parents=True)
        (pkg_cmd_dir / "toolkit-cmd.md").write_text("# Toolkit Command")

        context = discover_local_resources(tmp_path)

        assert len(context.packages) == 1
        assert context.packages[0].name == "my-toolkit"
        assert len(context.packages[0].resources) == 2

    def test_discovers_all_resource_types(self, tmp_path):
        """Test discovering all resource types together."""
        # Create skill
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        # Create command
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "my-cmd.md").write_text("# My Command")

        # Create agent
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "my-agent.md").write_text("# My Agent")

        context = discover_local_resources(tmp_path)

        assert len(context.skills) == 1
        assert len(context.commands) == 1
        assert len(context.agents) == 1

    def test_ignores_invalid_skill_directory(self, tmp_path):
        """Test that directories without SKILL.md are ignored."""
        # Create directory without SKILL.md
        skill_dir = tmp_path / "skills" / "not-a-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "README.md").write_text("# Not a skill")

        context = discover_local_resources(tmp_path)

        assert len(context.skills) == 0

    def test_ignores_non_markdown_commands(self, tmp_path):
        """Test that non-.md files in commands/ are ignored."""
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "script.py").write_text("# Not a command")

        context = discover_local_resources(tmp_path)

        assert len(context.commands) == 0

    def test_returns_empty_context_when_no_resources(self, tmp_path):
        """Test that empty context is returned when no resources exist."""
        context = discover_local_resources(tmp_path)

        assert len(context.skills) == 0
        assert len(context.commands) == 0
        assert len(context.agents) == 0
        assert len(context.packages) == 0

    def test_discovers_multiple_skills(self, tmp_path):
        """Test discovering multiple skills."""
        for name in ["skill-a", "skill-b", "skill-c"]:
            skill_dir = tmp_path / "skills" / name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(f"# {name}")

        context = discover_local_resources(tmp_path)

        assert len(context.skills) == 3
        names = [s.name for s in context.skills]
        assert "skill-a" in names
        assert "skill-b" in names
        assert "skill-c" in names

    def test_package_resources_include_package_name(self, tmp_path):
        """Test that package resources have package_name set."""
        pkg_skill_dir = tmp_path / "packages" / "my-toolkit" / "skills" / "toolkit-skill"
        pkg_skill_dir.mkdir(parents=True)
        (pkg_skill_dir / "SKILL.md").write_text("# Toolkit Skill")

        context = discover_local_resources(tmp_path)

        assert len(context.packages) == 1
        pkg = context.packages[0]
        assert len(pkg.resources) == 1
        assert pkg.resources[0].package_name == "my-toolkit"
