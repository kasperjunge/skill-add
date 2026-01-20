"""Test Job 7: Resource Discovery & Resolution.

Tests for resource type auto-detection and resolution.

Reference: .documents/jobs.md section "7. Resource Discovery & Resolution"

NOTE: Comprehensive tests for this job are in:
- tests/test_discovery.py - resource discovery functionality
- tests/test_nested_discovery.py - nested resource discovery

Existing Coverage:
- tests/test_discovery.py - type detection, resource finding
- tests/test_nested_discovery.py - nested path handling
- tests/test_handle.py - handle parsing and conversion
- tests/test_namespace_flattening.py - namespace/flattening logic
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agr.cli.main import app
from agr.cli.run import app as agrx_app
from agr.fetcher import ResourceType, DiscoveredResource, DiscoveryResult
from agr.handle import ParsedHandle, parse_handle


runner = CliRunner()


class TestAutoDetection:
    """Tests for auto-detection of resource types.

    See test_discovery.py for comprehensive tests.
    """

    def test_skill_detected_from_skill_md(self, project_with_agr_toml: Path):
        """Verify skill is detected from SKILL.md presence."""
        skill_dir = project_with_agr_toml / "resources" / "skills" / "auto-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Auto Skill")

        result = runner.invoke(app, ["add", "./resources/skills/auto-skill"])

        assert result.exit_code == 0
        # Should detect as skill without --type flag

    def test_command_detected_from_md_extension(self, project_with_agr_toml: Path):
        """Verify command is detected from .md file in commands dir."""
        cmd_dir = project_with_agr_toml / "resources" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "auto-cmd.md").write_text("# Auto Command")

        result = runner.invoke(app, ["add", "./resources/commands/auto-cmd.md"])

        assert result.exit_code == 0
        # Should detect as command

    def test_agent_detected_from_agents_directory(self, project_with_agr_toml: Path):
        """Verify agent is detected from .md file in agents dir."""
        agent_dir = project_with_agr_toml / "resources" / "agents"
        agent_dir.mkdir(parents=True)
        (agent_dir / "auto-agent.md").write_text("# Auto Agent")

        result = runner.invoke(app, ["add", "./resources/agents/auto-agent.md"])

        assert result.exit_code == 0


class TestNestedSkillNaming:
    """Tests for nested skill naming with colon notation.

    See test_namespace_flattening.py for comprehensive tests.
    """

    def test_nested_skill_flattens_to_colon_notation(
        self, project_with_agr_toml: Path
    ):
        """Verify nested skills use flattened colon-namespaced names."""
        # Create nested skill structure
        skill_dir = project_with_agr_toml / "resources" / "skills" / "category" / "nested-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Nested Skill")

        result = runner.invoke(app, ["add", "./resources/skills/category/nested-skill"])

        assert result.exit_code == 0

        # Should be installed with flattened name
        claude_skills = project_with_agr_toml / ".claude" / "skills"
        if claude_skills.exists():
            skill_dirs = list(claude_skills.iterdir())
            # Should have colon in name (e.g., user:category:nested-skill)
            flattened_names = [d.name for d in skill_dirs if ":" in d.name]
            assert len(flattened_names) > 0


class TestUsernameNamespacing:
    """Tests for username namespacing to avoid conflicts.

    See test_handle.py for comprehensive tests.
    """

    def test_parse_handle_extracts_username(self):
        """Verify handle parsing extracts username correctly."""
        handle = parse_handle("alice/helper")

        assert handle.username == "alice"
        assert handle.simple_name == "helper"

    def test_parse_handle_with_repo(self):
        """Verify handle parsing with explicit repo."""
        handle = parse_handle("alice/custom-repo/helper")

        assert handle.username == "alice"
        assert handle.simple_name == "helper"

    def test_parsed_handle_to_skill_dirname(self):
        """Verify ParsedHandle converts to skill dirname correctly."""
        handle = ParsedHandle.from_components("kasperjunge", "commit")

        assert handle.to_skill_dirname() == "kasperjunge:commit"

    def test_parsed_handle_to_toml_handle(self):
        """Verify ParsedHandle converts to toml handle correctly."""
        handle = ParsedHandle.from_components("kasperjunge", "commit")

        assert handle.to_toml_handle() == "kasperjunge/commit"


class TestShortFormReferences:
    """Tests for short-form GitHub references.

    See test_handle.py for comprehensive tests.
    """

    def test_two_part_reference_uses_default_repo(self):
        """Verify two-part reference uses default agent-resources repo."""
        handle = parse_handle("username/resource-name")

        assert handle.username == "username"
        assert handle.simple_name == "resource-name"
        # No explicit repo means default repo

    def test_three_part_reference_specifies_repo(self):
        """Verify three-part reference specifies custom repo."""
        handle = parse_handle("username/custom-repo/resource-name")

        assert handle.username == "username"
        assert handle.simple_name == "resource-name"
        # path_segments should include repo for proper path building


class TestColonNotationConversion:
    """Tests for colon notation conversion.

    See test_handle.py for comprehensive tests.
    """

    def test_toml_handle_to_skill_dirname(self):
        """Verify slash-separated handle converts to colon-separated dirname."""
        from agr.handle import toml_handle_to_skill_dirname

        dirname = toml_handle_to_skill_dirname("kasperjunge/commit")
        assert dirname == "kasperjunge:commit"

    def test_skill_dirname_to_toml_handle(self):
        """Verify colon-separated dirname converts to slash-separated handle."""
        from agr.handle import skill_dirname_to_toml_handle

        handle = skill_dirname_to_toml_handle("kasperjunge:commit")
        assert handle == "kasperjunge/commit"

    def test_nested_handle_conversion_roundtrip(self):
        """Verify nested handles roundtrip - note repo info is lost.

        For handles with 3+ parts (user/repo/path/name), the repo part
        is not included in the dirname since it's used for GitHub fetching
        only. The round-trip loses this information by design.
        """
        from agr.handle import toml_handle_to_skill_dirname, skill_dirname_to_toml_handle

        # 4-part handle: repo="category" is lost in dirname
        original = "user/category/subcategory/skill"
        dirname = toml_handle_to_skill_dirname(original)
        # dirname only includes path_segments after repo
        assert dirname == "user:subcategory:skill"
        roundtrip = skill_dirname_to_toml_handle(dirname)
        # round-trip loses the repo part
        assert roundtrip == "user/subcategory/skill"
