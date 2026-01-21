"""User journey tests for complete end-to-end workflows."""

from pathlib import Path

from typer.testing import CliRunner

from agr.cli.main import app
from agr.config import AgrConfig


runner = CliRunner()


class TestJourneyNewDeveloperSetup:
    """Tests for a new developer setting up a project with agr."""

    def test_complete_init_add_sync_workflow(self, project_with_git: Path):
        """Test complete workflow: init -> add resources -> sync."""
        # Step 1: Initialize project
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert (project_with_git / "agr.toml").exists()
        assert (project_with_git / "resources").exists()

        # Step 2: Create a local skill
        skill_dir = project_with_git / "resources" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            """---
name: my-skill
description: A test skill
---

# My Skill

This is my custom skill.
"""
        )

        # Step 3: Add the skill
        result = runner.invoke(app, ["add", "./resources/skills/my-skill"])
        assert result.exit_code == 0
        assert "added" in result.output.lower()

        # Step 4: Verify it's in agr.toml
        config = AgrConfig.load(project_with_git / "agr.toml")
        assert len(config.dependencies) >= 1

        # Step 5: Sync to install
        result = runner.invoke(app, ["sync"])
        assert result.exit_code == 0

        # Step 6: Verify installed
        installed = project_with_git / ".claude" / "skills" / "local:my-skill"
        assert installed.exists()

    def test_init_scaffold_add_workflow(self, project_with_git: Path):
        """Test workflow: init -> scaffold skill -> add scaffolded skill."""
        # Step 1: Initialize
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0

        # Step 2: Scaffold a skill
        result = runner.invoke(app, ["init", "skill", "my-new-skill"])
        assert result.exit_code == 0

        skill_md = project_with_git / "resources" / "skills" / "my-new-skill" / "SKILL.md"
        assert skill_md.exists()

        # Step 3: Add the scaffolded skill
        result = runner.invoke(app, ["add", "./resources/skills/my-new-skill"])
        assert result.exit_code == 0

        # Step 4: Verify in .claude
        installed = project_with_git / ".claude" / "skills" / "local:my-new-skill"
        assert installed.exists()


# ============================================================================
# Journey 2: Team Collaboration
# ============================================================================


class TestJourneyTeamCollaboration:
    """Tests for team collaboration scenarios."""

    def test_clone_and_sync_workflow(self, project_with_git: Path):
        """Test workflow: team member clones repo with agr.toml and syncs."""
        # Simulate existing agr.toml from repo
        (project_with_git / "agr.toml").write_text("""
[[dependencies]]
path = "./skills/team-skill"
type = "skill"
""")

        # Create the local skill source
        skill_dir = project_with_git / "skills" / "team-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Team Skill")

        # Sync to install
        result = runner.invoke(app, ["sync"])
        assert result.exit_code == 0

        # Verify installed
        installed = project_with_git / ".claude" / "skills" / "local:team-skill"
        assert installed.exists()

    def test_add_update_sync_workflow(self, project_with_git: Path):
        """Test workflow: add skill -> update source -> sync again."""
        # Initialize with agr.toml
        runner.invoke(app, ["init"])

        # Create initial skill
        skill_dir = project_with_git / "skills" / "evolving-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Version 1")

        # Add
        result = runner.invoke(app, ["add", "./skills/evolving-skill"])
        assert result.exit_code == 0

        # Sync
        runner.invoke(app, ["sync"])

        # Update source
        (skill_dir / "SKILL.md").write_text("# Version 2 - Updated")

        # Re-sync should update
        result = runner.invoke(app, ["sync"])
        assert result.exit_code == 0


# ============================================================================
# Journey 3: Package Development
# ============================================================================


class TestJourneyPackageDevelopment:
    """Tests for package development workflow."""

    def test_create_package_with_multiple_resources(self, project_with_git: Path):
        """Test creating a package with skills, commands, and agents."""
        runner.invoke(app, ["init"])

        # Scaffold a package
        result = runner.invoke(app, ["init", "package", "my-toolkit"])
        assert result.exit_code == 0

        pkg_dir = project_with_git / "resources" / "packages" / "my-toolkit"
        assert pkg_dir.exists()

        # Add skill to package
        skill_dir = pkg_dir / "skills" / "helper"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Helper Skill")

        # Add command to package
        cmd_dir = pkg_dir / "commands"
        cmd_dir.mkdir(exist_ok=True)
        (cmd_dir / "build.md").write_text("# Build Command")

        # Add agent to package
        agent_dir = pkg_dir / "agents"
        agent_dir.mkdir(exist_ok=True)
        (agent_dir / "tester.md").write_text("# Tester Agent")

        # Add package (explodes contents)
        result = runner.invoke(app, ["add", str(pkg_dir), "--type", "package"])
        assert result.exit_code == 0

        # Verify resources are installed with package namespace
        claude_dir = project_with_git / ".claude"
        assert (claude_dir / "skills" / "local:my-toolkit:helper").exists()
        assert (claude_dir / "commands" / "local" / "my-toolkit" / "build.md").exists()
        assert (claude_dir / "agents" / "local" / "my-toolkit" / "tester.md").exists()

    def test_nested_skills_in_package(self, project_with_git: Path):
        """Test creating package with nested skill structure."""
        runner.invoke(app, ["init"])

        pkg_dir = project_with_git / "my-pkg"
        pkg_dir.mkdir()

        # Create nested skills
        flat_skill = pkg_dir / "skills" / "basic"
        flat_skill.mkdir(parents=True)
        (flat_skill / "SKILL.md").write_text("# Basic")

        nested_skill = pkg_dir / "skills" / "category" / "advanced"
        nested_skill.mkdir(parents=True)
        (nested_skill / "SKILL.md").write_text("# Advanced")

        deep_skill = pkg_dir / "skills" / "a" / "b" / "deep"
        deep_skill.mkdir(parents=True)
        (deep_skill / "SKILL.md").write_text("# Deep")

        # Add package
        result = runner.invoke(app, ["add", "./my-pkg", "--type", "package"])
        assert result.exit_code == 0

        # Verify all are installed with correct namespacing
        skills_dir = project_with_git / ".claude" / "skills"
        installed = {d.name for d in skills_dir.iterdir()}
        assert "local:my-pkg:basic" in installed
        assert "local:my-pkg:category:advanced" in installed
        assert "local:my-pkg:a:b:deep" in installed


# ============================================================================
# Journey 4: Workspace Management
# ============================================================================


class TestJourneyWorkspaceManagement:
    """Tests for workspace management workflows."""

    def test_default_sync_installs_main_dependencies(self, project_with_git: Path):
        """Test syncing main dependencies."""
        runner.invoke(app, ["init"])

        # Create skill
        skill_dir = project_with_git / "skills" / "main-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Main Skill")

        # Configure main dependency
        (project_with_git / "agr.toml").write_text("""
[[dependencies]]
path = "./skills/main-skill"
type = "skill"
""")

        # Sync default workspace (just main deps)
        result = runner.invoke(app, ["sync"])
        assert result.exit_code == 0

        # Verify skill is installed
        assert (project_with_git / ".claude" / "skills" / "local:main-skill").exists()


# ============================================================================
# Journey 5: Resource Removal
# ============================================================================


class TestJourneyResourceRemoval:
    """Tests for resource removal workflows."""

    def test_add_then_remove_workflow(self, project_with_git: Path):
        """Test complete add -> use -> remove workflow."""
        runner.invoke(app, ["init"])

        # Create and add skill
        skill_dir = project_with_git / "skills" / "temporary"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Temporary Skill")

        result = runner.invoke(app, ["add", "./skills/temporary"])
        assert result.exit_code == 0

        # Verify installed
        installed = project_with_git / ".claude" / "skills" / "local:temporary"
        assert installed.exists()

        # Remove with confirmation
        result = runner.invoke(app, ["remove", "local:temporary", "-y"])
        assert result.exit_code == 0

        # Verify removed
        assert not installed.exists()

    def test_sync_after_config_change(self, project_with_git: Path):
        """Test syncing after config changes."""
        runner.invoke(app, ["init"])

        # Create skill and add to config
        skill_dir = project_with_git / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        # Add skill via CLI (adds to config and installs)
        result = runner.invoke(app, ["add", "./skills/my-skill"])
        assert result.exit_code == 0

        # Verify installed
        installed = project_with_git / ".claude" / "skills" / "local:my-skill"
        assert installed.exists()

        # Sync again should be idempotent
        result = runner.invoke(app, ["sync"])
        assert result.exit_code == 0
        assert installed.exists()


# ============================================================================
# Journey 6: Migration from Legacy Layout
# ============================================================================


class TestJourneyLegacyMigration:
    """Tests for migrating from legacy layouts."""

    def test_legacy_flat_skills_coexist(self, project_with_git: Path):
        """Test that legacy flat skills are preserved during sync."""
        runner.invoke(app, ["init"])

        # Create legacy flat skill (no colon in name)
        legacy_skill = project_with_git / ".claude" / "skills" / "legacy-skill"
        legacy_skill.mkdir(parents=True)
        (legacy_skill / "SKILL.md").write_text("# Legacy Skill")

        # Create new namespaced skill
        skill_dir = project_with_git / "skills" / "new-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# New Skill")
        runner.invoke(app, ["add", "./skills/new-skill"])

        # Sync should preserve legacy
        result = runner.invoke(app, ["sync"])
        assert result.exit_code == 0

        # Legacy skill should still exist
        assert legacy_skill.exists()

        # New skill should be installed
        assert (project_with_git / ".claude" / "skills" / "local:new-skill").exists()


# ============================================================================
# Journey 7: Directory Add with Multiple Resources
# ============================================================================


class TestJourneyBatchAdd:
    """Tests for adding multiple resources at once."""

    def test_add_directory_discovers_all_resources(self, project_with_git: Path):
        """Test adding a directory discovers all nested resources."""
        runner.invoke(app, ["init"])

        # Create skills directory with multiple skills
        skills_dir = project_with_git / "skills"
        skills_dir.mkdir()

        for name in ["alpha", "beta", "gamma"]:
            skill_dir = skills_dir / name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"# {name.title()} Skill")

        # Add directory
        result = runner.invoke(app, ["add", "./skills/"])
        assert result.exit_code == 0
        assert "Added 3 resource(s)" in result.output

        # Verify all installed
        for name in ["alpha", "beta", "gamma"]:
            assert (project_with_git / ".claude" / "skills" / f"local:{name}").exists()

    def test_add_directory_with_nested_skills(self, project_with_git: Path):
        """Test adding a directory with nested skill structure."""
        runner.invoke(app, ["init"])

        # Create nested structure
        skills_dir = project_with_git / "skills"

        direct_skill = skills_dir / "direct"
        direct_skill.mkdir(parents=True)
        (direct_skill / "SKILL.md").write_text("# Direct")

        nested_skill = skills_dir / "category" / "nested"
        nested_skill.mkdir(parents=True)
        (nested_skill / "SKILL.md").write_text("# Nested")

        # Add
        result = runner.invoke(app, ["add", "./skills/"])
        assert result.exit_code == 0
        assert "Added 2 resource(s)" in result.output

        # Verify
        assert (project_with_git / ".claude" / "skills" / "local:direct").exists()
        assert (project_with_git / ".claude" / "skills" / "local:category:nested").exists()
