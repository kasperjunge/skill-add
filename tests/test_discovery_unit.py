"""Unit tests for resource discovery functions."""

from pathlib import Path

import pytest

from agr.cli.add import detect_resource_type_from_ancestors, _detect_local_type
from agr.cli.common import discover_local_resource_type
from agr.fetcher import (
    BundleContents,
    BundleInstallResult,
    BundleRemoveResult,
    DiscoveredResource,
    DiscoveryResult,
    RESOURCE_CONFIGS,
    ResourceConfig,
    ResourceType,
    discover_bundle_contents,
    discover_resource_type_from_dir,
    downloaded_repo,
    fetch_bundle,
    fetch_bundle_from_repo_dir,
    fetch_resource,
    fetch_resource_from_repo_dir,
    remove_bundle,
)
from agr.fetcher.discovery import _is_bundle
from agr.resolver import _resolve_from_repo_root, ResourceSource


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


# ============================================================================
# discover_resource_type_from_dir Tests
# ============================================================================


class TestDiscoverResourceTypeFromDir:
    """Tests for discover_resource_type_from_dir function."""

    def test_discovers_skill(self, tmp_path):
        """Test discovering a skill resource."""
        skill_dir = tmp_path / ".claude" / "skills" / "hello-world"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Hello World Skill")

        result = discover_resource_type_from_dir(tmp_path, "hello-world", ["hello-world"])

        assert result.is_unique is True
        assert len(result.resources) == 1
        assert result.resources[0].resource_type == ResourceType.SKILL

    def test_discovers_command(self, tmp_path):
        """Test discovering a command resource."""
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "hello.md").write_text("# Hello Command")

        result = discover_resource_type_from_dir(tmp_path, "hello", ["hello"])

        assert result.is_unique is True
        assert len(result.resources) == 1
        assert result.resources[0].resource_type == ResourceType.COMMAND

    def test_discovers_agent(self, tmp_path):
        """Test discovering an agent resource."""
        agents_dir = tmp_path / ".claude" / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "hello-agent.md").write_text("# Hello Agent")

        result = discover_resource_type_from_dir(tmp_path, "hello-agent", ["hello-agent"])

        assert result.is_unique is True
        assert len(result.resources) == 1
        assert result.resources[0].resource_type == ResourceType.AGENT

    def test_discovers_bundle(self, tmp_path):
        """Test discovering a bundle resource."""
        bundle_skill_dir = tmp_path / ".claude" / "skills" / "my-bundle" / "test-skill"
        bundle_skill_dir.mkdir(parents=True)
        (bundle_skill_dir / "SKILL.md").write_text("# Test Skill")

        result = discover_resource_type_from_dir(tmp_path, "my-bundle", ["my-bundle"])

        assert result.is_bundle is True

    def test_discovers_multiple_types(self, tmp_path):
        """Test discovering when name exists in multiple types."""
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
        (tmp_path / ".claude").mkdir(parents=True)

        result = discover_resource_type_from_dir(tmp_path, "nonexistent", ["nonexistent"])

        assert result.is_empty is True


# ============================================================================
# _resolve_from_repo_root Tests (Auto-Discovery)
# ============================================================================


class TestResolveFromRepoRoot:
    """Tests for _resolve_from_repo_root function (auto-discovery)."""

    def test_discovers_skill_at_repo_root(self, tmp_path):
        """Test discovering a skill directory at repo root."""
        skill_dir = tmp_path / "go"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Go Skill")

        result = _resolve_from_repo_root(tmp_path, "go")

        assert result is not None
        assert result.name == "go"
        assert result.resource_type == ResourceType.SKILL
        assert result.path == Path("go")
        assert result.source == ResourceSource.REPO_ROOT

    def test_discovers_nested_skill_with_colon_name(self, tmp_path):
        """Test discovering nested skill using colon-separated name."""
        skill_dir = tmp_path / "tools" / "git"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Git Tools Skill")

        result = _resolve_from_repo_root(tmp_path, "tools:git")

        assert result is not None
        assert result.name == "tools:git"
        assert result.resource_type == ResourceType.SKILL
        assert result.path == Path("tools/git")

    def test_discovers_command_in_commands_directory(self, tmp_path):
        """Test discovering command in commands/ directory."""
        cmd_dir = tmp_path / "commands"
        cmd_dir.mkdir()
        (cmd_dir / "deploy.md").write_text("# Deploy Command")

        result = _resolve_from_repo_root(tmp_path, "deploy")

        assert result is not None
        assert result.name == "deploy"
        assert result.resource_type == ResourceType.COMMAND
        assert result.path == Path("commands/deploy.md")

    def test_discovers_agent_in_agents_directory(self, tmp_path):
        """Test discovering agent in agents/ directory."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "reviewer.md").write_text("# Reviewer Agent")

        result = _resolve_from_repo_root(tmp_path, "reviewer")

        assert result is not None
        assert result.name == "reviewer"
        assert result.resource_type == ResourceType.AGENT
        assert result.path == Path("agents/reviewer.md")

    def test_returns_none_when_not_found(self, tmp_path):
        """Test returning None when no matching resource exists."""
        result = _resolve_from_repo_root(tmp_path, "nonexistent")
        assert result is None

    def test_skill_priority_over_command(self, tmp_path):
        """Test that skills are discovered before commands."""
        skill_dir = tmp_path / "myresource"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Skill")

        cmd_dir = tmp_path / "commands"
        cmd_dir.mkdir()
        (cmd_dir / "myresource.md").write_text("# Command")

        result = _resolve_from_repo_root(tmp_path, "myresource")

        assert result is not None
        assert result.resource_type == ResourceType.SKILL

    def test_skips_claude_directory(self, tmp_path):
        """Test that .claude/ directory is skipped during auto-discovery."""
        claude_skill = tmp_path / ".claude" / "skills" / "myskill"
        claude_skill.mkdir(parents=True)
        (claude_skill / "SKILL.md").write_text("# Skill in .claude")

        result = _resolve_from_repo_root(tmp_path, "myskill")

        assert result is None


# ============================================================================
# discover_local_resource_type Tests
# ============================================================================


class TestDiscoverLocalResourceType:
    """Tests for discover_local_resource_type function."""

    def test_discovers_local_skill(self, tmp_path, monkeypatch):
        """Test discovering a locally installed skill."""
        skill_dir = tmp_path / ".claude" / "skills" / "hello-world"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Hello World Skill")

        monkeypatch.chdir(tmp_path)

        result = discover_local_resource_type("hello-world", global_install=False)

        assert result.is_unique is True
        assert result.resources[0].resource_type == ResourceType.SKILL

    def test_discovers_local_command(self, tmp_path, monkeypatch):
        """Test discovering a locally installed command."""
        commands_dir = tmp_path / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "hello.md").write_text("# Hello Command")

        monkeypatch.chdir(tmp_path)

        result = discover_local_resource_type("hello", global_install=False)

        assert result.is_unique is True
        assert result.resources[0].resource_type == ResourceType.COMMAND

    def test_discovers_nothing_locally(self, tmp_path, monkeypatch):
        """Test when resource doesn't exist locally."""
        (tmp_path / ".claude").mkdir(parents=True)
        monkeypatch.chdir(tmp_path)

        result = discover_local_resource_type("nonexistent", global_install=False)

        assert result.is_empty is True


# ============================================================================
# Ancestor-based Type Detection Tests
# ============================================================================


class TestAncestorBasedTypeDetection:
    """Tests for detecting resource type from parent directories."""

    def test_file_in_commands_dir_detected_as_command(self, tmp_path):
        """File under commands/ is detected as command."""
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        file_path = commands_dir / "deploy.md"
        file_path.write_text("# Deploy")

        result = detect_resource_type_from_ancestors(file_path)
        assert result == "command"

    def test_file_in_nested_commands_dir_detected_as_command(self, tmp_path):
        """File deep under commands/ is still detected as command."""
        nested_dir = tmp_path / "commands" / "infra" / "aws"
        nested_dir.mkdir(parents=True)
        file_path = nested_dir / "deploy.md"
        file_path.write_text("# Deploy")

        result = detect_resource_type_from_ancestors(file_path)
        assert result == "command"

    def test_file_in_agents_dir_detected_as_agent(self, tmp_path):
        """File under agents/ is detected as agent."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        file_path = agents_dir / "reviewer.md"
        file_path.write_text("# Reviewer")

        result = detect_resource_type_from_ancestors(file_path)
        assert result == "agent"

    def test_file_in_rules_dir_detected_as_rule(self, tmp_path):
        """File under rules/ is detected as rule."""
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        file_path = rules_dir / "style.md"
        file_path.write_text("# Style")

        result = detect_resource_type_from_ancestors(file_path)
        assert result == "rule"

    def test_file_not_in_type_dir_returns_none(self, tmp_path):
        """File not under type directory returns None."""
        file_path = tmp_path / "random.md"
        file_path.write_text("# Random")

        result = detect_resource_type_from_ancestors(file_path)
        assert result is None


# ============================================================================
# _detect_local_type Tests
# ============================================================================


class TestDetectLocalType:
    """Unit tests for _detect_local_type function."""

    def test_directory_with_skill_md_detected_as_skill(self, tmp_path):
        """Directory containing SKILL.md is detected as skill."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Skill")

        result = _detect_local_type(skill_dir)
        assert result == "skill"

    def test_directory_with_package_md_detected_as_package(self, tmp_path):
        """Directory containing PACKAGE.md is detected as package."""
        pkg_dir = tmp_path / "my-pkg"
        pkg_dir.mkdir()
        (pkg_dir / "PACKAGE.md").write_text("---\nname: my-pkg\n---\n")

        result = _detect_local_type(pkg_dir)
        assert result == "package"

    def test_empty_directory_returns_none(self, tmp_path):
        """Empty directory returns None."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = _detect_local_type(empty_dir)
        assert result is None

    def test_file_without_md_extension_returns_none(self, tmp_path):
        """Non-.md file returns None."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("text content")

        result = _detect_local_type(txt_file)
        assert result is None


# ============================================================================
# Fetcher Module Exports Tests
# ============================================================================


class TestFetcherModuleExports:
    """Test that fetcher module exports expected symbols."""

    def test_types_module_exports(self):
        """Test types.py exports all type definitions."""
        # Verify ResourceType enum values
        assert ResourceType.SKILL.value == "skill"
        assert ResourceType.COMMAND.value == "command"
        assert ResourceType.AGENT.value == "agent"

        # Verify RESOURCE_CONFIGS has all types
        assert ResourceType.SKILL in RESOURCE_CONFIGS
        assert ResourceType.COMMAND in RESOURCE_CONFIGS
        assert ResourceType.AGENT in RESOURCE_CONFIGS

    def test_resource_config_structure(self):
        """Test ResourceConfig has correct structure for each type."""
        skill_config = RESOURCE_CONFIGS[ResourceType.SKILL]
        assert skill_config.is_directory is True
        assert skill_config.source_subdir == ".claude/skills"
        assert skill_config.dest_subdir == "skills"

        command_config = RESOURCE_CONFIGS[ResourceType.COMMAND]
        assert command_config.is_directory is False
        assert command_config.file_extension == ".md"
        assert command_config.source_subdir == ".claude/commands"

        agent_config = RESOURCE_CONFIGS[ResourceType.AGENT]
        assert agent_config.is_directory is False
        assert agent_config.file_extension == ".md"
        assert agent_config.source_subdir == ".claude/agents"

    def test_bundle_dataclasses(self):
        """Test bundle dataclass structure."""
        contents = BundleContents(bundle_name="test")
        assert contents.is_empty is True
        assert contents.total_count == 0

        result = BundleInstallResult()
        assert result.total_installed == 0
        assert result.total_skipped == 0

        remove_result = BundleRemoveResult()
        assert remove_result.is_empty is True
        assert remove_result.total_removed == 0

    def test_all_functions_are_callable(self):
        """Test all exported functions are callable."""
        assert callable(downloaded_repo)
        assert callable(discover_resource_type_from_dir)
        assert callable(_is_bundle)
        assert callable(fetch_resource_from_repo_dir)
        assert callable(fetch_resource)
        assert callable(discover_bundle_contents)
        assert callable(fetch_bundle_from_repo_dir)
        assert callable(fetch_bundle)
        assert callable(remove_bundle)


class TestBackwardCompatibilityImports:
    """Test backward compatibility via agr.fetcher package imports."""

    def test_all_public_symbols_importable_from_package(self):
        """Test all public symbols can be imported from agr.fetcher."""
        import agr.fetcher as fetcher_module

        # All symbols should be importable without error
        assert fetcher_module.ResourceType is not None
        assert fetcher_module.ResourceConfig is not None
        assert fetcher_module.RESOURCE_CONFIGS is not None
        assert fetcher_module.DiscoveredResource is not None
        assert fetcher_module.DiscoveryResult is not None
        assert fetcher_module.downloaded_repo is not None
        assert fetcher_module.discover_resource_type_from_dir is not None
        assert fetcher_module.fetch_resource_from_repo_dir is not None
        assert fetcher_module.fetch_resource is not None
        assert fetcher_module.BundleContents is not None
        assert fetcher_module.BundleInstallResult is not None
        assert fetcher_module.BundleRemoveResult is not None
        assert fetcher_module.discover_bundle_contents is not None
        assert fetcher_module.fetch_bundle_from_repo_dir is not None
        assert fetcher_module.fetch_bundle is not None
        assert fetcher_module.remove_bundle is not None

    def test_all_exports_match_dunder_all(self):
        """Test that __all__ matches actual exports."""
        import agr.fetcher as fetcher_module

        for name in fetcher_module.__all__:
            assert hasattr(fetcher_module, name), f"Missing export: {name}"
