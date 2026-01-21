"""Integration tests for namespace flattening via CLI."""

from pathlib import Path

from typer.testing import CliRunner

from agr.cli.main import app


runner = CliRunner()


class TestInstallFlatSkill:
    """Tests for installing flat skills with flattened names."""

    def test_add_flat_skill_installs_with_flattened_name(self, git_project: Path):
        """Flat skill installs to local:skill/ directory."""
        skill_dir = git_project / "skills" / "commit"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            """---
name: commit
description: Generate commit messages
---

# Commit
"""
        )

        result = runner.invoke(app, ["add", "./skills/commit"])

        assert result.exit_code == 0
        installed = git_project / ".claude" / "skills" / "local:commit" / "SKILL.md"
        assert installed.exists()
        assert "name: local:commit" in installed.read_text()


class TestInstallNestedSkill:
    """Tests for installing nested skills with flattened names."""

    def test_add_nested_skill_installs_with_flattened_name(self, git_project: Path):
        """Nested skill installs to local:namespace:skill/ directory."""
        skill_dir = git_project / "skills" / "product-strategy" / "growth-hacker"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            """---
name: growth-hacker
description: Growth hacking strategies
---

# Growth Hacker
"""
        )

        result = runner.invoke(app, ["add", "./skills/product-strategy/growth-hacker"])

        assert result.exit_code == 0
        installed = (
            git_project
            / ".claude"
            / "skills"
            / "local:product-strategy:growth-hacker"
            / "SKILL.md"
        )
        assert installed.exists()
        assert "name: local:product-strategy:growth-hacker" in installed.read_text()


class TestPackageExplodeFlattening:
    """Tests for _explode_package() flattening."""

    def test_package_explode_flattens_skills(self, git_project: Path):
        """Package explosion uses flattened names for skills."""
        pkg_dir = git_project / "packages" / "my-toolkit"
        skills_dir = pkg_dir / "skills" / "helper"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("# Helper Skill")
        (pkg_dir / "commands").mkdir()
        (pkg_dir / "agents").mkdir()

        result = runner.invoke(app, ["add", "./packages/my-toolkit", "--type", "package"])

        assert result.exit_code == 0
        installed = (
            git_project / ".claude" / "skills" / "local:my-toolkit:helper" / "SKILL.md"
        )
        assert installed.exists()
        assert "name: local:my-toolkit:helper" in installed.read_text()

    def test_package_explode_nested_skills(self, git_project: Path):
        """Nested skills in packages are discovered and flattened correctly."""
        pkg_dir = git_project / "packages" / "my-toolkit"
        nested_skill = pkg_dir / "skills" / "category" / "helper"
        nested_skill.mkdir(parents=True)
        (nested_skill / "SKILL.md").write_text("# Nested Helper Skill")
        (pkg_dir / "commands").mkdir()
        (pkg_dir / "agents").mkdir()

        result = runner.invoke(app, ["add", "./packages/my-toolkit", "--type", "package"])

        assert result.exit_code == 0
        installed = (
            git_project / ".claude" / "skills" / "local:my-toolkit:category:helper" / "SKILL.md"
        )
        assert installed.exists()
        assert "name: local:my-toolkit:category:helper" in installed.read_text()

    def test_package_mixed_skill_depths(self, git_project: Path):
        """Both flat and nested skills in same package are handled."""
        pkg_dir = git_project / "packages" / "mixed-toolkit"

        flat_skill = pkg_dir / "skills" / "flat-skill"
        flat_skill.mkdir(parents=True)
        (flat_skill / "SKILL.md").write_text("# Flat Skill")

        nested_skill = pkg_dir / "skills" / "category" / "nested-skill"
        nested_skill.mkdir(parents=True)
        (nested_skill / "SKILL.md").write_text("# Nested Skill")

        (pkg_dir / "commands").mkdir()
        (pkg_dir / "agents").mkdir()

        result = runner.invoke(app, ["add", "./packages/mixed-toolkit", "--type", "package"])

        assert result.exit_code == 0
        assert (git_project / ".claude" / "skills" / "local:mixed-toolkit:flat-skill" / "SKILL.md").exists()
        assert (git_project / ".claude" / "skills" / "local:mixed-toolkit:category:nested-skill" / "SKILL.md").exists()


class TestSyncLocalDependencyFlattening:
    """Tests for sync applying flattening to local skills."""

    def test_sync_flattens_local_skill(self, git_project: Path):
        """Sync uses flattened names for local skills."""
        skill_dir = git_project / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        (git_project / "agr.toml").write_text("""
[[dependencies]]
path = "./skills/my-skill"
type = "skill"
""")

        result = runner.invoke(app, ["sync"])

        assert result.exit_code == 0
        assert (git_project / ".claude" / "skills" / "local:my-skill" / "SKILL.md").exists()

    def test_sync_flattens_nested_local_skill(self, git_project: Path):
        """Sync uses flattened names for nested local skills."""
        skill_dir = git_project / "skills" / "product" / "flywheel"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Flywheel")

        (git_project / "agr.toml").write_text("""
[[dependencies]]
path = "./skills/product/flywheel"
type = "skill"
""")

        result = runner.invoke(app, ["sync"])

        assert result.exit_code == 0
        assert (git_project / ".claude" / "skills" / "local:product:flywheel" / "SKILL.md").exists()


class TestSkillPathNamespacing:
    """Tests for skill path namespace generation."""

    def test_standalone_skill_namespace(self, git_project: Path):
        """Standalone skill uses local:skill format."""
        skill_dir = git_project / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        result = runner.invoke(app, ["add", "./skills/my-skill"])

        assert result.exit_code == 0
        installed = git_project / ".claude" / "skills" / "local:my-skill" / "SKILL.md"
        assert installed.exists()

    def test_nested_skill_namespace(self, git_project: Path):
        """Nested skill uses local:parent:child format."""
        skill_dir = git_project / "skills" / "category" / "nested-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Nested Skill")

        result = runner.invoke(app, ["add", "./skills/category/nested-skill"])

        assert result.exit_code == 0
        installed = git_project / ".claude" / "skills" / "local:category:nested-skill" / "SKILL.md"
        assert installed.exists()

    def test_packaged_skill_namespace(self, git_project: Path):
        """Skill in package uses local:pkg:skill format."""
        pkg_dir = git_project / "my-pkg"
        pkg_dir.mkdir()
        (pkg_dir / "PACKAGE.md").write_text("---\nname: my-pkg\n---\n")
        skill_dir = pkg_dir / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        result = runner.invoke(app, ["add", "./my-pkg"])

        assert result.exit_code == 0
        installed = git_project / ".claude" / "skills" / "local:my-pkg:my-skill" / "SKILL.md"
        assert installed.exists()


class TestCommandPathNamespacing:
    """Tests for command path namespace generation."""

    def test_command_in_commands_dir(self, git_project: Path):
        """Command in commands/ installs to .claude/commands/local/cmd.md."""
        commands_dir = git_project / "commands"
        commands_dir.mkdir()
        (commands_dir / "deploy.md").write_text("# Deploy")

        result = runner.invoke(app, ["add", "./commands/deploy.md"])

        assert result.exit_code == 0
        installed = git_project / ".claude" / "commands" / "local" / "deploy.md"
        assert installed.exists()

    def test_nested_command_preserves_path(self, git_project: Path):
        """Nested command preserves directory structure."""
        nested_dir = git_project / "commands" / "infra" / "aws"
        nested_dir.mkdir(parents=True)
        (nested_dir / "deploy.md").write_text("# Deploy")

        result = runner.invoke(app, ["add", "./commands/infra/aws/deploy.md"])

        assert result.exit_code == 0
        installed = git_project / ".claude" / "commands" / "local" / "infra" / "aws" / "deploy.md"
        assert installed.exists()


class TestAgentPathNamespacing:
    """Tests for agent path namespace generation."""

    def test_agent_in_agents_dir(self, git_project: Path):
        """Agent in agents/ installs to .claude/agents/local/agent.md."""
        agents_dir = git_project / "agents"
        agents_dir.mkdir()
        (agents_dir / "reviewer.md").write_text("# Reviewer")

        result = runner.invoke(app, ["add", "./agents/reviewer.md"])

        assert result.exit_code == 0
        installed = git_project / ".claude" / "agents" / "local" / "reviewer.md"
        assert installed.exists()


class TestRulePathNamespacing:
    """Tests for rule path namespace generation."""

    def test_rule_in_rules_dir(self, git_project: Path):
        """Rule in rules/ installs to .claude/rules/local/rule.md."""
        rules_dir = git_project / "rules"
        rules_dir.mkdir()
        (rules_dir / "style.md").write_text("# Style Guide")

        result = runner.invoke(app, ["add", "./rules/style.md"])

        assert result.exit_code == 0
        installed = git_project / ".claude" / "rules" / "local" / "style.md"
        assert installed.exists()
