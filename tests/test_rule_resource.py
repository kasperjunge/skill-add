"""Tests for rule resource type support (Task #24)."""

from pathlib import Path

import pytest

from agr.constants import RULES_SUBDIR
from agr.config import VALID_TYPES
from agr.fetcher.types import ResourceType, RESOURCE_CONFIGS
from agr.handle import ParsedHandle, parse_handle
from agr.cli.paths import TYPE_TO_SUBDIR


class TestRuleResourceType:
    """Test rule resource type definitions."""

    def test_rule_type_exists(self):
        """Test that ResourceType.RULE exists."""
        assert hasattr(ResourceType, "RULE")
        assert ResourceType.RULE.value == "rule"

    def test_rule_config_exists(self):
        """Test that RESOURCE_CONFIGS includes RULE."""
        assert ResourceType.RULE in RESOURCE_CONFIGS

    def test_rule_config_is_file_based(self):
        """Test that rule config is file-based (not directory)."""
        config = RESOURCE_CONFIGS[ResourceType.RULE]
        assert config.is_directory is False
        assert config.file_extension == ".md"

    def test_rule_config_source_subdir(self):
        """Test rule config source subdirectory."""
        config = RESOURCE_CONFIGS[ResourceType.RULE]
        assert config.source_subdir == ".claude/rules"

    def test_rule_config_dest_subdir(self):
        """Test rule config destination subdirectory."""
        config = RESOURCE_CONFIGS[ResourceType.RULE]
        assert config.dest_subdir == "rules"


class TestRuleConstants:
    """Test rule-related constants."""

    def test_rules_subdir_constant(self):
        """Test RULES_SUBDIR constant exists."""
        assert RULES_SUBDIR == "rules"

    def test_rule_in_valid_types(self):
        """Test 'rule' is in VALID_TYPES."""
        assert "rule" in VALID_TYPES

    def test_rule_in_type_to_subdir(self):
        """Test 'rule' is in TYPE_TO_SUBDIR mapping."""
        assert "rule" in TYPE_TO_SUBDIR
        assert TYPE_TO_SUBDIR["rule"] == "rules"


class TestParsedHandleToRulePath:
    """Test rule path building with nested format."""

    def test_to_rule_path_with_username(self):
        """Test rule path with username uses nested format."""
        handle = ParsedHandle(
            username="kasperjunge",
            name="no-console",
            path_segments=["no-console"],
        )
        result = handle.to_rule_path(Path(".claude"))
        assert result == Path(".claude/rules/kasperjunge/no-console.md")

    def test_to_rule_path_without_username(self):
        """Test rule path without username uses flat format."""
        handle = ParsedHandle(name="no-console", path_segments=["no-console"])
        result = handle.to_rule_path(Path(".claude"))
        assert result == Path(".claude/rules/no-console.md")

    def test_to_rule_path_with_absolute_base(self):
        """Test rule path with absolute base path."""
        handle = ParsedHandle(
            username="user",
            name="rule",
            path_segments=["rule"],
        )
        result = handle.to_rule_path(Path("/home/user/.claude"))
        assert result == Path("/home/user/.claude/rules/user/rule.md")

    def test_to_rule_path_includes_nested_path(self):
        """Test rule path includes nested path segments."""
        handle = ParsedHandle(
            username="user",
            name="ignored",
            path_segments=["nested", "actual"],
        )
        result = handle.to_rule_path(Path(".claude"))
        # New behavior: includes full path structure
        assert result == Path(".claude/rules/user/nested/actual.md")


class TestToResourcePathRule:
    """Test to_resource_path with rule type."""

    def test_to_resource_path_rule_with_username(self):
        """Test resource path for rule type with username."""
        handle = ParsedHandle(
            username="user",
            name="rule",
            path_segments=["rule"],
        )
        result = handle.to_resource_path(Path(".claude"), "rule")
        assert result == Path(".claude/rules/user/rule.md")

    def test_to_resource_path_rule_without_username(self):
        """Test resource path for rule type without username."""
        handle = ParsedHandle(name="rule", path_segments=["rule"])
        result = handle.to_resource_path(Path(".claude"), "rule")
        assert result == Path(".claude/rules/rule.md")


class TestRuleDiscovery:
    """Test rule discovery in fetcher."""

    def test_discovers_rule_file(self, tmp_path):
        """Test discovering a rule file in repository."""
        from agr.fetcher.discovery import discover_resource_type_from_dir

        # Create rule file structure
        rule_dir = tmp_path / ".claude" / "rules"
        rule_dir.mkdir(parents=True)
        (rule_dir / "test-rule.md").write_text("# Test Rule\n")

        result = discover_resource_type_from_dir(
            tmp_path, "test-rule", ["test-rule"]
        )

        assert not result.is_empty
        rule_resources = [
            r for r in result.resources if r.resource_type == ResourceType.RULE
        ]
        assert len(rule_resources) == 1
        assert rule_resources[0].name == "test-rule"

    def test_rule_not_found(self, tmp_path):
        """Test rule not found when file doesn't exist."""
        from agr.fetcher.discovery import discover_resource_type_from_dir

        # Create empty rules directory
        rule_dir = tmp_path / ".claude" / "rules"
        rule_dir.mkdir(parents=True)

        result = discover_resource_type_from_dir(
            tmp_path, "nonexistent", ["nonexistent"]
        )

        rule_resources = [
            r for r in result.resources if r.resource_type == ResourceType.RULE
        ]
        assert len(rule_resources) == 0


class TestRuleLocalDiscovery:
    """Test rule discovery in CLI."""

    def test_discovers_local_rule_flat(self, tmp_path, monkeypatch):
        """Test discovering a flat rule file locally."""
        from agr.cli.discovery import discover_local_resource_type

        # Create rule file
        rule_dir = tmp_path / ".claude" / "rules"
        rule_dir.mkdir(parents=True)
        (rule_dir / "test-rule.md").write_text("# Test Rule\n")

        monkeypatch.chdir(tmp_path)

        result = discover_local_resource_type("test-rule", global_install=False)

        assert not result.is_empty
        rule_resources = [
            r for r in result.resources if r.resource_type == ResourceType.RULE
        ]
        assert len(rule_resources) == 1
        assert rule_resources[0].name == "test-rule"
        assert rule_resources[0].username is None

    def test_discovers_namespaced_rule(self, tmp_path, monkeypatch):
        """Test discovering a namespaced rule file locally."""
        from agr.cli.discovery import discover_local_resource_type

        # Create namespaced rule file
        rule_dir = tmp_path / ".claude" / "rules" / "kasperjunge"
        rule_dir.mkdir(parents=True)
        (rule_dir / "no-console.md").write_text("# No Console\n")

        monkeypatch.chdir(tmp_path)

        result = discover_local_resource_type("no-console", global_install=False)

        assert not result.is_empty
        rule_resources = [
            r for r in result.resources if r.resource_type == ResourceType.RULE
        ]
        assert len(rule_resources) == 1
        assert rule_resources[0].name == "no-console"
        assert rule_resources[0].username == "kasperjunge"

    def test_discovers_rule_with_full_ref(self, tmp_path, monkeypatch):
        """Test discovering a rule with full ref (username/name)."""
        from agr.cli.discovery import discover_local_resource_type

        # Create namespaced rule file
        rule_dir = tmp_path / ".claude" / "rules" / "kasperjunge"
        rule_dir.mkdir(parents=True)
        (rule_dir / "no-console.md").write_text("# No Console\n")

        monkeypatch.chdir(tmp_path)

        result = discover_local_resource_type(
            "kasperjunge/no-console", global_install=False
        )

        assert not result.is_empty
        rule_resources = [
            r for r in result.resources if r.resource_type == ResourceType.RULE
        ]
        assert len(rule_resources) == 1
        assert rule_resources[0].name == "no-console"
        assert rule_resources[0].username == "kasperjunge"
