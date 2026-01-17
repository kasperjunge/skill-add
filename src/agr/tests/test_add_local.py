"""Tests for agr add with local paths."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agr.cli.main import app
from agr.config import AgrConfig


runner = CliRunner()


class TestAddLocal:
    """Tests for adding local resources."""

    def test_add_local_skill_directory(self, tmp_path: Path, monkeypatch):
        """Test adding a local skill directory."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create local skill
        skill_dir = tmp_path / "custom" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        result = runner.invoke(app, ["add", "./custom/my-skill"])

        assert result.exit_code == 0
        assert "Added local skill 'my-skill'" in result.output

        # Verify agr.toml was created/updated
        config = AgrConfig.load(tmp_path / "agr.toml")
        assert "my-skill" in config.local
        assert config.local["my-skill"].path == "./custom/my-skill"
        assert config.local["my-skill"].type == "skill"

    def test_add_local_command_file(self, tmp_path: Path, monkeypatch):
        """Test adding a local command file."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create local command
        commands_dir = tmp_path / "scripts"
        commands_dir.mkdir()
        (commands_dir / "deploy.md").write_text("# Deploy")

        result = runner.invoke(app, ["add", "./scripts/deploy.md", "--type", "command"])

        assert result.exit_code == 0
        assert "Added local command 'deploy'" in result.output

        config = AgrConfig.load(tmp_path / "agr.toml")
        assert "deploy" in config.local
        assert config.local["deploy"].type == "command"

    def test_add_local_with_package(self, tmp_path: Path, monkeypatch):
        """Test adding a local resource to a package."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create local skill
        skill_dir = tmp_path / "lib" / "helper"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Helper")

        result = runner.invoke(app, ["add", "./lib/helper", "--to", "utils"])

        assert result.exit_code == 0
        assert "package: utils" in result.output

        config = AgrConfig.load(tmp_path / "agr.toml")
        assert config.local["helper"].package == "utils"

    def test_add_local_errors_nonexistent_path(self, tmp_path: Path, monkeypatch):
        """Test that adding nonexistent path errors."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        result = runner.invoke(app, ["add", "./nonexistent"])

        assert result.exit_code == 1
        assert "does not exist" in result.output

    def test_add_local_requires_type_for_ambiguous(self, tmp_path: Path, monkeypatch):
        """Test that ambiguous paths require --type."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create a directory without SKILL.md
        (tmp_path / "ambiguous").mkdir()

        result = runner.invoke(app, ["add", "./ambiguous"])

        assert result.exit_code == 1
        assert "Could not detect resource type" in result.output

    def test_add_local_with_explicit_type(self, tmp_path: Path, monkeypatch):
        """Test adding with explicit type."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create a command file
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "task.md").write_text("# Task")

        result = runner.invoke(app, ["add", "./scripts/task.md", "--type", "agent"])

        assert result.exit_code == 0
        assert "Added local agent" in result.output

        config = AgrConfig.load(tmp_path / "agr.toml")
        assert config.local["task"].type == "agent"

    def test_add_local_auto_detects_skill(self, tmp_path: Path, monkeypatch):
        """Test that skill is auto-detected from SKILL.md."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Skill")

        result = runner.invoke(app, ["add", "./my-skill"])

        assert result.exit_code == 0
        assert "skill" in result.output

    def test_add_local_auto_detects_command_from_md_file(self, tmp_path: Path, monkeypatch):
        """Test that .md files default to command type."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        (tmp_path / "cmd.md").write_text("# Command")

        result = runner.invoke(app, ["add", "./cmd.md"])

        assert result.exit_code == 0
        # .md files default to command
        assert "command" in result.output


class TestIsLocalPath:
    """Tests for _is_local_path helper."""

    def test_recognizes_dot_slash(self):
        from agr.cli.add import _is_local_path
        assert _is_local_path("./path/to/file") is True

    def test_recognizes_absolute_path(self):
        from agr.cli.add import _is_local_path
        assert _is_local_path("/absolute/path") is True

    def test_recognizes_parent_path(self):
        from agr.cli.add import _is_local_path
        assert _is_local_path("../parent/path") is True

    def test_rejects_remote_ref(self):
        from agr.cli.add import _is_local_path
        assert _is_local_path("kasperjunge/commit") is False

    def test_rejects_remote_ref_with_repo(self):
        from agr.cli.add import _is_local_path
        assert _is_local_path("kasperjunge/repo/name") is False
