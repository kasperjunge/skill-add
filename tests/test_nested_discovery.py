"""Tests for recursive nested resource discovery in agr add."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agr.cli.main import app
from agr.config import AgrConfig


runner = CliRunner()


class TestNestedResourceDiscovery:
    """Tests for recursive discovery of nested resources."""

    def test_add_directory_finds_nested_skills(self, tmp_path: Path, monkeypatch):
        """Test that skills in subdirectories are discovered recursively."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create nested skill structure:
        # skills/
        #   commit/SKILL.md           <- direct child
        #   anthropic/
        #     code-review/SKILL.md    <- nested
        #   product-strategy/
        #     flywheel/SKILL.md       <- nested
        #     jobs-theory/SKILL.md    <- nested
        skills_dir = tmp_path / "skills"
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
        config = AgrConfig.load(tmp_path / "agr.toml")
        local_deps = config.get_local_dependencies()
        assert len(local_deps) == 4
        assert all(d.type == "skill" for d in local_deps)

    def test_add_directory_finds_nested_agents(self, tmp_path: Path, monkeypatch):
        """Test that agents in subdirectories are discovered recursively."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create nested agent structure:
        # agents/
        #   hello-world.md            <- direct child
        #   anthropic/
        #     code-simplifier.md      <- nested
        agents_dir = tmp_path / "agents"
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
        config = AgrConfig.load(tmp_path / "agr.toml")
        local_deps = config.get_local_dependencies()
        assert len(local_deps) == 2

    def test_add_directory_excludes_skill_reference_files(self, tmp_path: Path, monkeypatch):
        """Test that .md files inside skill directories are not added as commands."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create skill with reference files inside:
        # skills/
        #   my-skill/
        #     SKILL.md                <- skill entry point
        #     references/
        #       guide.md              <- should NOT be added as command
        #       patterns.md           <- should NOT be added as command
        skills_dir = tmp_path / "skills"
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
        config = AgrConfig.load(tmp_path / "agr.toml")
        local_deps = config.get_local_dependencies()
        assert len(local_deps) == 1
        assert local_deps[0].type == "skill"

    def test_add_directory_mixed_types_nested(self, tmp_path: Path, monkeypatch):
        """Test discovery with mixed resource types at different nesting levels."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create mixed structure:
        # resources/
        #   commands/
        #     build.md                <- command
        #     dev/
        #       watch.md              <- nested command
        #   skills/
        #     deploy/SKILL.md         <- skill
        #     cloud/
        #       aws/SKILL.md          <- nested skill
        resources_dir = tmp_path / "resources"
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

    def test_add_deeply_nested_skills(self, tmp_path: Path, monkeypatch):
        """Test discovery of deeply nested skills (3+ levels deep)."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create deeply nested structure:
        # skills/
        #   org/
        #     team/
        #       project/
        #         feature/SKILL.md
        skills_dir = tmp_path / "skills"
        deep_path = skills_dir / "org" / "team" / "project" / "feature"
        deep_path.mkdir(parents=True)
        (deep_path / "SKILL.md").write_text("# Deep Feature Skill")

        result = runner.invoke(app, ["add", "./skills/"])

        assert result.exit_code == 0
        assert "feature" in result.output
        assert "Added 1 resource(s)" in result.output

        # Verify installation preserves namespace structure
        # Installed to .claude/skills/<user>/<namespace>/<relative-path>/
        installed = tmp_path / ".claude" / "skills" / "local" / "skills" / "org" / "team" / "project" / "feature" / "SKILL.md"
        assert installed.exists()

    def test_add_directory_handles_empty_subdirs(self, tmp_path: Path, monkeypatch):
        """Test that empty subdirectories don't cause issues."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create structure with empty subdirs
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "empty-dir").mkdir()
        (skills_dir / "real-skill").mkdir()
        (skills_dir / "real-skill" / "SKILL.md").write_text("# Real Skill")

        result = runner.invoke(app, ["add", "./skills/"])

        assert result.exit_code == 0
        assert "real-skill" in result.output
        assert "Added 1 resource(s)" in result.output
