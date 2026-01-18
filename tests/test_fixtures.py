"""Tests using committed test fixtures in resources/.

These tests use the committed test resources to verify:
- Skill discovery (flat, nested, with frontmatter)
- Command discovery
- Agent discovery
- Package detection and explosion
- Name flattening
- Frontmatter parsing and name updates
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agr.cli.main import app
from agr.utils import (
    compute_flattened_skill_name,
    compute_path_segments_from_skill_path,
    update_skill_md_name,
)


runner = CliRunner()

# Path to committed test resources
RESOURCES_PATH = Path(__file__).parent.parent / "resources"


class TestSkillDiscoveryFixtures:
    """Test skill discovery using committed fixtures.

    Note: discover_local_resources only discovers direct children of skills/.
    Skills nested under _test/ are discovered via CLI add command with recursive discovery.
    These tests verify file existence and CLI functionality.
    """

    def test_flat_skill_exists(self):
        """Test that flat-skill SKILL.md exists."""
        skill_md = RESOURCES_PATH / "skills" / "_test" / "flat-skill" / "SKILL.md"
        assert skill_md.exists()

        content = skill_md.read_text()
        assert "# Flat Skill" in content

    def test_skill_with_frontmatter_exists(self):
        """Test skill with YAML frontmatter exists and has correct structure."""
        skill_md = (
            RESOURCES_PATH / "skills" / "_test" / "skill-with-frontmatter" / "SKILL.md"
        )
        assert skill_md.exists()

        content = skill_md.read_text()
        assert content.startswith("---")
        assert "name: skill-with-frontmatter" in content
        assert "triggers:" in content

    def test_nested_skills_exist(self):
        """Test nested skills exist in correct directory structure."""
        # Verify nested-category itself is not treated as a skill (no SKILL.md)
        nested_category_skill_md = (
            RESOURCES_PATH / "skills" / "_test" / "nested-category" / "SKILL.md"
        )
        assert not nested_category_skill_md.exists()

        # Verify nested skills exist
        nested_skill_a = (
            RESOURCES_PATH
            / "skills"
            / "_test"
            / "nested-category"
            / "nested-skill-a"
            / "SKILL.md"
        )
        assert nested_skill_a.exists()

        deeply_nested = (
            RESOURCES_PATH
            / "skills"
            / "_test"
            / "nested-category"
            / "deep"
            / "deeply-nested-skill"
            / "SKILL.md"
        )
        assert deeply_nested.exists()

    def test_test_namespace_directory_exists(self):
        """Test that the _test namespace directory structure exists."""
        test_skills_dir = RESOURCES_PATH / "skills" / "_test"
        assert test_skills_dir.is_dir()

        # Verify expected subdirectories
        assert (test_skills_dir / "flat-skill").is_dir()
        assert (test_skills_dir / "skill-with-frontmatter").is_dir()
        assert (test_skills_dir / "nested-category").is_dir()
        assert (test_skills_dir / "nested-category" / "nested-skill-a").is_dir()
        assert (
            test_skills_dir / "nested-category" / "deep" / "deeply-nested-skill"
        ).is_dir()

    def test_nested_skill_md_files_exist(self):
        """Test that nested SKILL.md files exist."""
        base = RESOURCES_PATH / "skills" / "_test"

        nested_skill_md = base / "nested-category" / "nested-skill-a" / "SKILL.md"
        assert nested_skill_md.exists()

        deep_skill_md = (
            base / "nested-category" / "deep" / "deeply-nested-skill" / "SKILL.md"
        )
        assert deep_skill_md.exists()


class TestCommandDiscoveryFixtures:
    """Test command discovery using committed fixtures.

    Note: Commands are in commands/_test/ subdirectory, so discover_local_resources
    won't find them directly. Tests verify file existence.
    """

    def test_basic_command_exists(self):
        """Test basic-command.md exists."""
        cmd_file = RESOURCES_PATH / "commands" / "_test" / "basic-command.md"
        assert cmd_file.exists()

        content = cmd_file.read_text()
        assert "# Basic Command" in content
        assert "## Instructions" in content

    def test_command_with_args_exists(self):
        """Test command-with-args.md exists with argument definitions."""
        cmd_file = RESOURCES_PATH / "commands" / "_test" / "command-with-args.md"
        assert cmd_file.exists()

        content = cmd_file.read_text()
        assert "# Command With Args" in content
        assert "## Arguments" in content
        assert "target" in content
        assert "--verbose" in content
        assert "--format" in content


class TestAgentDiscoveryFixtures:
    """Test agent discovery using committed fixtures.

    Note: Agents are in agents/_test/ subdirectory, so discover_local_resources
    won't find them directly. Tests verify file existence.
    """

    def test_basic_agent_exists(self):
        """Test basic-agent.md exists."""
        agent_file = RESOURCES_PATH / "agents" / "_test" / "basic-agent.md"
        assert agent_file.exists()

        content = agent_file.read_text()
        assert "# Basic Agent" in content
        assert "## Tools" in content
        assert "Bash" in content

    def test_multi_tool_agent_exists(self):
        """Test multi-tool-agent.md exists with multiple tools."""
        agent_file = RESOURCES_PATH / "agents" / "_test" / "multi-tool-agent.md"
        assert agent_file.exists()

        content = agent_file.read_text()
        assert "# Multi-Tool Agent" in content
        assert "## Tools" in content
        assert "Bash" in content
        assert "Read" in content
        assert "Write" in content
        assert "Glob" in content
        assert "Grep" in content


class TestPackageDiscoveryFixtures:
    """Test package detection using committed fixtures."""

    def test_nested_skills_package_exists(self):
        """Test _test-nested-skills package exists with nested skill structure."""
        pkg_path = RESOURCES_PATH / "packages" / "_test-nested-skills"
        assert pkg_path.is_dir()

        # Verify the nested structure exists
        skill_one = pkg_path / "skills" / "category" / "cat-skill-one" / "SKILL.md"
        skill_two = pkg_path / "skills" / "category" / "cat-skill-two" / "SKILL.md"
        assert skill_one.exists()
        assert skill_two.exists()


class TestPackageExplosionFixtures:
    """Test package explosion using committed fixtures."""

    def test_explodes_simple_package(self, tmp_path, monkeypatch):
        """Test _test-simple package explodes to correct structure."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        pkg_path = RESOURCES_PATH / "packages" / "_test-simple"

        result = runner.invoke(app, ["add", str(pkg_path), "--type", "package"])

        assert result.exit_code == 0

        # Verify skill was installed with flattened name
        installed = (
            tmp_path / ".claude" / "skills" / "local:_test-simple:simple-skill" / "SKILL.md"
        )
        assert installed.exists()

        # Verify name was updated in SKILL.md
        content = installed.read_text()
        assert "name: local:_test-simple:simple-skill" in content

    def test_explodes_complete_package(self, tmp_path, monkeypatch):
        """Test _test-complete package explodes all resource types."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        pkg_path = RESOURCES_PATH / "packages" / "_test-complete"

        result = runner.invoke(app, ["add", str(pkg_path), "--type", "package"])

        assert result.exit_code == 0

        # Verify skills installed with flattened names
        assert (
            tmp_path / ".claude" / "skills" / "local:_test-complete:alpha" / "SKILL.md"
        ).exists()
        assert (
            tmp_path / ".claude" / "skills" / "local:_test-complete:beta" / "SKILL.md"
        ).exists()

        # Verify command installed (in package subdirectory)
        assert (
            tmp_path / ".claude" / "commands" / "local" / "_test-complete" / "pkg-cmd.md"
        ).exists()

        # Verify agent installed (in package subdirectory)
        assert (
            tmp_path / ".claude" / "agents" / "local" / "_test-complete" / "pkg-agent.md"
        ).exists()

    def test_explodes_nested_skills_package(self, tmp_path, monkeypatch):
        """Test _test-nested-skills creates flattened skill names."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        pkg_path = RESOURCES_PATH / "packages" / "_test-nested-skills"

        result = runner.invoke(app, ["add", str(pkg_path), "--type", "package"])

        assert result.exit_code == 0

        # Verify nested skills installed with flattened names
        assert (
            tmp_path
            / ".claude"
            / "skills"
            / "local:_test-nested-skills:category:cat-skill-one"
            / "SKILL.md"
        ).exists()
        assert (
            tmp_path
            / ".claude"
            / "skills"
            / "local:_test-nested-skills:category:cat-skill-two"
            / "SKILL.md"
        ).exists()


class TestNameFlatteningFixtures:
    """Test name flattening with committed fixtures."""

    def test_flattens_flat_skill_name(self):
        """Test flat-skill flattens to user:_test:flat-skill."""
        skill_path = RESOURCES_PATH / "skills" / "_test" / "flat-skill"
        segments = compute_path_segments_from_skill_path(skill_path)

        # segments should be ["_test", "flat-skill"]
        assert segments == ["_test", "flat-skill"]

        flattened = compute_flattened_skill_name("local", segments)
        assert flattened == "local:_test:flat-skill"

    def test_flattens_nested_skill_name(self):
        """Test nested-skill-a flattens to user:_test:nested-category:nested-skill-a."""
        skill_path = (
            RESOURCES_PATH / "skills" / "_test" / "nested-category" / "nested-skill-a"
        )
        segments = compute_path_segments_from_skill_path(skill_path)

        assert segments == ["_test", "nested-category", "nested-skill-a"]

        flattened = compute_flattened_skill_name("local", segments)
        assert flattened == "local:_test:nested-category:nested-skill-a"

    def test_flattens_deeply_nested_skill_name(self):
        """Test deeply-nested-skill flattens correctly."""
        skill_path = (
            RESOURCES_PATH
            / "skills"
            / "_test"
            / "nested-category"
            / "deep"
            / "deeply-nested-skill"
        )
        segments = compute_path_segments_from_skill_path(skill_path)

        assert segments == ["_test", "nested-category", "deep", "deeply-nested-skill"]

        flattened = compute_flattened_skill_name("local", segments)
        assert flattened == "local:_test:nested-category:deep:deeply-nested-skill"

    def test_add_flat_skill_uses_flattened_name(self, tmp_path, monkeypatch):
        """Test adding flat-skill installs to flattened directory."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        skill_path = RESOURCES_PATH / "skills" / "_test" / "flat-skill"

        result = runner.invoke(app, ["add", str(skill_path)])

        assert result.exit_code == 0

        # Verify installed with flattened name
        installed = tmp_path / ".claude" / "skills" / "local:_test:flat-skill" / "SKILL.md"
        assert installed.exists()


class TestFrontmatterFixtures:
    """Test frontmatter handling with committed fixtures."""

    def test_parses_frontmatter_from_skill(self):
        """Test YAML frontmatter is parsed from skill-with-frontmatter."""
        skill_md = (
            RESOURCES_PATH
            / "skills"
            / "_test"
            / "skill-with-frontmatter"
            / "SKILL.md"
        )
        content = skill_md.read_text()

        # Verify frontmatter structure
        assert content.startswith("---")
        assert "name: skill-with-frontmatter" in content
        assert "description:" in content
        assert "triggers:" in content
        assert "- test-frontmatter" in content
        assert "- frontmatter-example" in content

    def test_updates_name_field_on_install(self, tmp_path, monkeypatch):
        """Test name field in frontmatter is updated to flattened name on install."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        skill_path = RESOURCES_PATH / "skills" / "_test" / "skill-with-frontmatter"

        result = runner.invoke(app, ["add", str(skill_path)])

        assert result.exit_code == 0

        # Verify installed SKILL.md has updated name
        installed = (
            tmp_path
            / ".claude"
            / "skills"
            / "local:_test:skill-with-frontmatter"
            / "SKILL.md"
        )
        assert installed.exists()

        content = installed.read_text()
        # Name should be updated to flattened version
        assert "name: local:_test:skill-with-frontmatter" in content
        # Other frontmatter should be preserved
        assert "description:" in content
        assert "triggers:" in content

    def test_update_skill_md_name_with_test_skill(self, tmp_path):
        """Test update_skill_md_name works with a copy of test fixture."""
        # Copy skill-with-frontmatter to tmp_path
        src_skill = (
            RESOURCES_PATH
            / "skills"
            / "_test"
            / "skill-with-frontmatter"
            / "SKILL.md"
        )
        dest_dir = tmp_path / "test-skill"
        dest_dir.mkdir()
        dest_skill = dest_dir / "SKILL.md"
        dest_skill.write_text(src_skill.read_text())

        # Update the name
        update_skill_md_name(dest_dir, "new:flattened:name")

        # Verify name was updated
        content = dest_skill.read_text()
        assert "name: new:flattened:name" in content
        # Verify other frontmatter preserved
        assert "description:" in content
        assert "triggers:" in content


class TestAddNestedSkillFixtures:
    """Test adding nested skills from fixtures."""

    def test_add_nested_skill_a(self, tmp_path, monkeypatch):
        """Test adding nested-skill-a from fixtures."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        skill_path = (
            RESOURCES_PATH / "skills" / "_test" / "nested-category" / "nested-skill-a"
        )

        result = runner.invoke(app, ["add", str(skill_path)])

        assert result.exit_code == 0

        # Verify installed with flattened name
        installed = (
            tmp_path
            / ".claude"
            / "skills"
            / "local:_test:nested-category:nested-skill-a"
            / "SKILL.md"
        )
        assert installed.exists()

    def test_add_deeply_nested_skill(self, tmp_path, monkeypatch):
        """Test adding deeply-nested-skill from fixtures."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        skill_path = (
            RESOURCES_PATH
            / "skills"
            / "_test"
            / "nested-category"
            / "deep"
            / "deeply-nested-skill"
        )

        result = runner.invoke(app, ["add", str(skill_path)])

        assert result.exit_code == 0

        # Verify installed with flattened name
        installed = (
            tmp_path
            / ".claude"
            / "skills"
            / "local:_test:nested-category:deep:deeply-nested-skill"
            / "SKILL.md"
        )
        assert installed.exists()

        # Verify name in SKILL.md
        content = installed.read_text()
        assert "name: local:_test:nested-category:deep:deeply-nested-skill" in content

    def test_add_namespace_directory(self, tmp_path, monkeypatch):
        """Test adding the nested-category namespace directory.

        When adding a namespace directory directly, the flattened name starts
        from that directory (not including parent directories like _test).
        """
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        namespace_path = RESOURCES_PATH / "skills" / "_test" / "nested-category"

        result = runner.invoke(app, ["add", str(namespace_path)])

        assert result.exit_code == 0

        # Verify all nested skills were installed
        # Note: _test is NOT in the name because we added nested-category directly
        assert (
            tmp_path
            / ".claude"
            / "skills"
            / "local:nested-category:nested-skill-a"
            / "SKILL.md"
        ).exists()

        assert (
            tmp_path
            / ".claude"
            / "skills"
            / "local:nested-category:deep:deeply-nested-skill"
            / "SKILL.md"
        ).exists()


class TestResourceFilesIntegrity:
    """Test that all committed test resource files are valid."""

    def test_all_skill_md_files_are_readable(self):
        """Test that all SKILL.md files in fixtures are readable."""
        skill_files = list(RESOURCES_PATH.glob("**/SKILL.md"))

        # We expect at least the test skills we created
        # 4 in skills/_test/ + 1 in _test-simple + 2 in _test-complete +
        # 2 in _test-nested-skills + existing resources
        assert len(skill_files) >= 9

        for skill_file in skill_files:
            content = skill_file.read_text()
            assert len(content) > 0
            assert "#" in content  # Should have a heading

    def test_all_command_md_files_are_readable(self):
        """Test that all command .md files in fixtures are readable."""
        cmd_files = list(RESOURCES_PATH.glob("**/commands/*.md"))

        # We expect: 2 in commands/_test/ + 1 in _test-complete +
        # 2 in _test-commands-only + existing commands
        assert len(cmd_files) >= 5

        for cmd_file in cmd_files:
            content = cmd_file.read_text()
            assert len(content) > 0
            # Commands should have either a heading or frontmatter
            assert "#" in content or content.startswith("---")

    def test_all_agent_md_files_are_readable(self):
        """Test that all agent .md files in fixtures are readable."""
        agent_files = list(RESOURCES_PATH.glob("**/agents/*.md"))

        # Note: This glob only matches direct children of agents/ directories
        # Files in subdirs like agents/_test/ require a different pattern
        assert len(agent_files) >= 2

        for agent_file in agent_files:
            content = agent_file.read_text()
            assert len(content) > 0
            assert "#" in content
