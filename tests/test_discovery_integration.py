"""Integration tests for resource discovery via CLI."""

from pathlib import Path

from typer.testing import CliRunner

from agr.cli.main import app
from agr.config import AgrConfig


runner = CliRunner()


class TestRecursiveSkillDiscovery:
    """Tests for recursive skill discovery in directories."""

    def test_discovers_skills_at_multiple_depths(self, git_project: Path):
        """Discovers skills at various nesting levels."""
        skills_dir = git_project / "skills"
        skills_dir.mkdir()

        (skills_dir / "skill-a").mkdir()
        (skills_dir / "skill-a" / "SKILL.md").write_text("# Skill A")

        (skills_dir / "category" / "skill-b").mkdir(parents=True)
        (skills_dir / "category" / "skill-b" / "SKILL.md").write_text("# Skill B")

        (skills_dir / "cat" / "subcat" / "skill-c").mkdir(parents=True)
        (skills_dir / "cat" / "subcat" / "skill-c" / "SKILL.md").write_text("# Skill C")

        result = runner.invoke(app, ["add", "./skills/"])

        assert result.exit_code == 0
        assert "skill-a" in result.output
        assert "skill-b" in result.output
        assert "skill-c" in result.output
        assert "Added 3 resource(s)" in result.output

    def test_skill_reference_files_not_discovered(self, git_project: Path):
        """Reference .md files inside skill directories are not discovered."""
        skills_dir = git_project / "skills"
        skills_dir.mkdir()

        skill_dir = skills_dir / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# My Skill")
        (skill_dir / "reference.md").write_text("# Reference")
        (skill_dir / "references" / "guide.md").parent.mkdir()
        (skill_dir / "references" / "guide.md").write_text("# Guide")

        result = runner.invoke(app, ["add", "./skills/"])

        assert result.exit_code == 0
        assert "my-skill" in result.output
        assert "Added 1 resource(s)" in result.output

    def test_empty_directories_ignored(self, git_project: Path):
        """Empty directories don't cause issues."""
        skills_dir = git_project / "skills"
        skills_dir.mkdir()
        (skills_dir / "empty-dir").mkdir()
        (skills_dir / "real-skill").mkdir()
        (skills_dir / "real-skill" / "SKILL.md").write_text("# Real")

        result = runner.invoke(app, ["add", "./skills/"])

        assert result.exit_code == 0
        assert "real-skill" in result.output
        assert "Added 1 resource(s)" in result.output

    def test_deeply_nested_skills_full_path_in_name(self, git_project: Path):
        """Deeply nested skills get full path in flattened name."""
        deep_path = git_project / "skills" / "a" / "b" / "c" / "d" / "deep-skill"
        deep_path.mkdir(parents=True)
        (deep_path / "SKILL.md").write_text("# Deep Skill")

        result = runner.invoke(app, ["add", "./skills/"])

        assert result.exit_code == 0
        installed = git_project / ".claude" / "skills" / "local:a:b:c:d:deep-skill" / "SKILL.md"
        assert installed.exists()


# ============================================================================
# Recursive Command Discovery Tests
# ============================================================================


class TestRecursiveCommandDiscovery:
    """Tests for recursive command discovery in directories."""

    def test_discovers_commands_at_multiple_depths(self, git_project: Path):
        """Discovers commands at various nesting levels."""
        commands_dir = git_project / "commands"
        commands_dir.mkdir()

        (commands_dir / "cmd-a.md").write_text("# Command A")

        (commands_dir / "infra").mkdir()
        (commands_dir / "infra" / "cmd-b.md").write_text("# Command B")

        (commands_dir / "aws" / "ec2").mkdir(parents=True)
        (commands_dir / "aws" / "ec2" / "cmd-c.md").write_text("# Command C")

        result = runner.invoke(app, ["add", "./commands/"])

        assert result.exit_code == 0
        assert "cmd-a" in result.output
        assert "cmd-b" in result.output
        assert "cmd-c" in result.output
        assert "Added 3 resource(s)" in result.output

    def test_nested_commands_preserve_path_structure(self, git_project: Path):
        """Nested commands are installed with preserved path structure."""
        commands_dir = git_project / "commands" / "infra" / "aws"
        commands_dir.mkdir(parents=True)
        (commands_dir / "deploy.md").write_text("# Deploy")

        result = runner.invoke(app, ["add", "./commands/infra/aws/deploy.md"])

        assert result.exit_code == 0
        installed = git_project / ".claude" / "commands" / "local" / "infra" / "aws" / "deploy.md"
        assert installed.exists()


# ============================================================================
# Mixed Resource Discovery Tests
# ============================================================================


class TestMixedResourceDiscovery:
    """Tests for discovering mixed resource types in directories."""

    def test_discovers_skills_and_commands_separately(self, git_project: Path):
        """Adding skills/ and commands/ directories works independently."""
        skills_dir = git_project / "skills"
        skills_dir.mkdir()
        (skills_dir / "my-skill").mkdir()
        (skills_dir / "my-skill" / "SKILL.md").write_text("# Skill")

        commands_dir = git_project / "commands"
        commands_dir.mkdir()
        (commands_dir / "my-cmd.md").write_text("# Command")

        result = runner.invoke(app, ["add", "./skills/"])
        assert result.exit_code == 0
        assert "my-skill" in result.output

        result = runner.invoke(app, ["add", "./commands/"])
        assert result.exit_code == 0
        assert "my-cmd" in result.output

        assert (git_project / ".claude" / "skills" / "local:my-skill" / "SKILL.md").exists()
        assert (git_project / ".claude" / "commands" / "local" / "my-cmd.md").exists()

    def test_add_directory_mixed_types_nested(self, git_project: Path):
        """Test discovery with mixed resource types at different nesting levels."""
        resources_dir = git_project / "resources"
        resources_dir.mkdir()

        # Commands
        cmd_dir = resources_dir / "commands"
        cmd_dir.mkdir()
        (cmd_dir / "build.md").write_text("# Build")
        dev_dir = cmd_dir / "dev"
        dev_dir.mkdir()
        (dev_dir / "watch.md").write_text("# Watch")

        # Skills
        skills_dir = resources_dir / "skills"
        skills_dir.mkdir()
        (skills_dir / "deploy").mkdir()
        (skills_dir / "deploy" / "SKILL.md").write_text("# Deploy")
        cloud_dir = skills_dir / "cloud"
        cloud_dir.mkdir()
        (cloud_dir / "aws").mkdir()
        (cloud_dir / "aws" / "SKILL.md").write_text("# AWS")

        # Add commands directory
        result = runner.invoke(app, ["add", "./resources/commands/"])
        assert result.exit_code == 0
        assert "build" in result.output
        assert "watch" in result.output
        assert "Added 2 resource(s)" in result.output

        # Add skills directory
        result = runner.invoke(app, ["add", "./resources/skills/"])
        assert result.exit_code == 0
        assert "deploy" in result.output
        assert "aws" in result.output
        assert "Added 2 resource(s)" in result.output


# ============================================================================
# Ambiguous File Handling Tests
# ============================================================================


class TestAmbiguousFileHandling:
    """Tests for error handling when file type cannot be determined."""

    def test_root_md_file_produces_clear_error(self, git_project: Path):
        """Adding .md file not under type directory produces clear error."""
        (git_project / "random.md").write_text("# Random")

        result = runner.invoke(app, ["add", "./random.md"])

        assert result.exit_code == 1
        assert "Cannot determine resource type" in result.output
        assert "--type" in result.output

    def test_error_message_suggests_type_flag(self, git_project: Path):
        """Error message suggests using --type flag."""
        (git_project / "ambiguous.md").write_text("# Ambiguous")

        result = runner.invoke(app, ["add", "./ambiguous.md"])

        assert result.exit_code == 1
        assert "--type" in result.output

    def test_type_flag_overrides_detection(self, git_project: Path):
        """--type flag allows adding ambiguous files."""
        (git_project / "random.md").write_text("# Random Command")

        result = runner.invoke(app, ["add", "./random.md", "--type", "command"])

        assert result.exit_code == 0
        assert "Added local command 'random'" in result.output

    def test_type_flag_overrides_auto_detection(self, git_project: Path):
        """--type takes precedence over auto-detection."""
        commands_dir = git_project / "commands"
        commands_dir.mkdir()
        (commands_dir / "deploy.md").write_text("# Deploy Agent")

        result = runner.invoke(app, ["add", "./commands/deploy.md", "--type", "agent"])

        assert result.exit_code == 0
        assert "Added local agent 'deploy'" in result.output
        installed = git_project / ".claude" / "agents" / "local" / "deploy.md"
        assert installed.exists()


# ============================================================================
# Package Discovery and Explosion Tests
# ============================================================================


RESOURCES_PATH = Path(__file__).parent.parent / "resources"
PACKAGES_PATH = RESOURCES_PATH / "packages"


class TestPackageExplosion:
    """Tests for package detection and explosion."""

    def test_explodes_simple_package(self, git_project: Path):
        """Test _test-simple package explodes to correct structure."""
        pkg_path = PACKAGES_PATH / "_test-simple"
        if not pkg_path.exists():
            # Create the package if it doesn't exist
            pkg_path.mkdir(parents=True)
            skill_dir = pkg_path / "skills" / "simple-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("# Simple Skill")

        result = runner.invoke(app, ["add", str(pkg_path), "--type", "package"])

        assert result.exit_code == 0

        installed = git_project / ".claude" / "skills" / "local:test-simple:simple-skill" / "SKILL.md"
        assert installed.exists()

        content = installed.read_text()
        assert "name: local:test-simple:simple-skill" in content

    def test_package_with_nested_skills(self, git_project: Path):
        """Test package with nested skills creates flattened names."""
        # Create package with nested skill structure
        pkg_dir = git_project / "test-pkg"
        pkg_dir.mkdir()
        skills_dir = pkg_dir / "skills" / "category" / "nested-skill"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("# Nested Skill")

        result = runner.invoke(app, ["add", str(pkg_dir), "--type", "package"])

        assert result.exit_code == 0

        installed = git_project / ".claude" / "skills" / "local:test-pkg:category:nested-skill" / "SKILL.md"
        assert installed.exists()

        content = installed.read_text()
        assert "name: local:test-pkg:category:nested-skill" in content


# ============================================================================
# Nested Skill Discovery Tests (agr add with directory)
# ============================================================================


class TestNestedResourceDiscovery:
    """Tests for recursive discovery of nested resources."""

    def test_add_directory_finds_nested_skills(self, git_project: Path):
        """Test that skills in subdirectories are discovered recursively."""
        skills_dir = git_project / "skills"
        skills_dir.mkdir()

        # Direct child skill
        (skills_dir / "commit").mkdir()
        (skills_dir / "commit" / "SKILL.md").write_text("# Commit Skill")

        # Nested skills under anthropic/
        anthropic_dir = skills_dir / "anthropic"
        anthropic_dir.mkdir()
        (anthropic_dir / "code-review").mkdir()
        (anthropic_dir / "code-review" / "SKILL.md").write_text("# Code Review Skill")

        # Nested skills under product-strategy/
        ps_dir = skills_dir / "product-strategy"
        ps_dir.mkdir()
        for name in ["flywheel", "jobs-theory"]:
            (ps_dir / name).mkdir()
            (ps_dir / name / "SKILL.md").write_text(f"# {name.title()} Skill")

        result = runner.invoke(app, ["add", "./skills/"])

        assert result.exit_code == 0
        # All 4 skills should be found
        assert "commit" in result.output
        assert "code-review" in result.output
        assert "flywheel" in result.output
        assert "jobs-theory" in result.output
        assert "Added 4 resource(s)" in result.output

        # Verify config has all skills
        config = AgrConfig.load(git_project / "agr.toml")
        local_deps = config.get_local_dependencies()
        assert len(local_deps) == 4
        assert all(d.type == "skill" for d in local_deps)

    def test_add_directory_finds_nested_agents(self, git_project: Path):
        """Test that agents in subdirectories are discovered recursively."""
        agents_dir = git_project / "agents"
        agents_dir.mkdir()

        # Direct child agent
        (agents_dir / "hello-world.md").write_text("# Hello World Agent")

        # Nested agent under anthropic/
        anthropic_dir = agents_dir / "anthropic"
        anthropic_dir.mkdir()
        (anthropic_dir / "code-simplifier.md").write_text("# Code Simplifier Agent")

        result = runner.invoke(app, ["add", "./agents/"])

        assert result.exit_code == 0
        # Both agents should be found
        assert "hello-world" in result.output
        assert "code-simplifier" in result.output
        assert "Added 2 resource(s)" in result.output

        # Verify config has both agents
        config = AgrConfig.load(git_project / "agr.toml")
        local_deps = config.get_local_dependencies()
        assert len(local_deps) == 2

    def test_add_directory_excludes_skill_reference_files(self, git_project: Path):
        """Test that .md files inside skill directories are not added as commands."""
        skills_dir = git_project / "skills"
        skills_dir.mkdir()

        skill_dir = skills_dir / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# My Skill")

        refs_dir = skill_dir / "references"
        refs_dir.mkdir()
        (refs_dir / "guide.md").write_text("# Guide Reference")
        (refs_dir / "patterns.md").write_text("# Patterns Reference")

        result = runner.invoke(app, ["add", "./skills/"])

        assert result.exit_code == 0
        # Only the skill should be added
        assert "my-skill" in result.output
        assert "Added 1 resource(s)" in result.output
        # Reference files should NOT be added
        assert "guide" not in result.output
        assert "patterns" not in result.output

        # Verify config only has the skill
        config = AgrConfig.load(git_project / "agr.toml")
        local_deps = config.get_local_dependencies()
        assert len(local_deps) == 1
        assert local_deps[0].type == "skill"


# ============================================================================
# Flattened Name Installation Tests
# ============================================================================


class TestFlattenedNameInstallation:
    """Tests for installing skills with flattened colon-namespaced names."""

    def test_add_flat_skill_installs_with_flattened_name(self, git_project: Path):
        """Test adding a flat skill installs to user:skill/ directory."""
        skill_dir = git_project / "skills" / "commit"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Commit")

        result = runner.invoke(app, ["add", "./skills/commit"])

        assert result.exit_code == 0

        # Verify installed to flattened path
        installed = git_project / ".claude" / "skills" / "local:commit" / "SKILL.md"
        assert installed.exists()

    def test_add_nested_skill_installs_with_flattened_name(self, git_project: Path):
        """Test adding a nested skill installs to user:namespace:skill/ directory."""
        skill_dir = git_project / "skills" / "product-strategy" / "growth-hacker"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Growth Hacker")

        result = runner.invoke(app, ["add", "./skills/product-strategy/growth-hacker"])

        assert result.exit_code == 0

        # Verify installed to flattened path
        installed = (
            git_project
            / ".claude"
            / "skills"
            / "local:product-strategy:growth-hacker"
            / "SKILL.md"
        )
        assert installed.exists()

    def test_skill_md_name_updated_on_add(self, git_project: Path):
        """Test that SKILL.md name is updated when skill is added."""
        skill_dir = git_project / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            """---
name: my-skill
description: Test skill
---

# My Skill
"""
        )

        runner.invoke(app, ["add", "./skills/my-skill"])

        # Verify name was updated
        installed = git_project / ".claude" / "skills" / "local:my-skill" / "SKILL.md"
        content = installed.read_text()
        assert "name: local:my-skill" in content
        assert "description: Test skill" in content
