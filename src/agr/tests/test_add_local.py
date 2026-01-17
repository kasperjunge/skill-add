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
        dep = config.get_by_path("./custom/my-skill")
        assert dep is not None
        assert dep.type == "skill"

        # Verify installed to .claude/
        installed = tmp_path / ".claude" / "skills" / "local" / "my-skill" / "SKILL.md"
        assert installed.exists()

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
        dep = config.get_by_path("./scripts/deploy.md")
        assert dep is not None
        assert dep.type == "command"

        # Verify installed to .claude/
        installed = tmp_path / ".claude" / "commands" / "local" / "deploy.md"
        assert installed.exists()

    def test_add_local_with_package_type(self, tmp_path: Path, monkeypatch):
        """Test adding a local package."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create local package with subdirs and a skill (non-empty package)
        pkg_dir = tmp_path / "packages" / "utils"
        pkg_dir.mkdir(parents=True)
        skills_dir = pkg_dir / "skills" / "helper"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("# Helper Skill")
        (pkg_dir / "commands").mkdir()
        (pkg_dir / "agents").mkdir()

        result = runner.invoke(app, ["add", "./packages/utils", "--type", "package"])

        assert result.exit_code == 0
        assert "Added local package" in result.output or "Added" in result.output

        config = AgrConfig.load(tmp_path / "agr.toml")
        dep = config.get_by_path("./packages/utils")
        assert dep is not None
        assert dep.type == "package"

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
        dep = config.get_by_path("./scripts/task.md")
        assert dep is not None
        assert dep.type == "agent"

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


class TestAddGlob:
    """Tests for adding multiple local resources via glob patterns."""

    def test_add_glob_pattern(self, tmp_path: Path, monkeypatch):
        """Test adding multiple files with glob pattern."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create multiple command files
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "deploy.md").write_text("# Deploy")
        (commands_dir / "build.md").write_text("# Build")
        (commands_dir / "test.md").write_text("# Test")

        result = runner.invoke(app, ["add", "./commands/*.md"])

        assert result.exit_code == 0
        assert "Added" in result.output

        # Verify all were added
        config = AgrConfig.load(tmp_path / "agr.toml")
        local_deps = config.get_local_dependencies()
        assert len(local_deps) == 3

    def test_add_glob_no_matches(self, tmp_path: Path, monkeypatch):
        """Test error when glob pattern matches nothing."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        result = runner.invoke(app, ["add", "./nonexistent/*.md"])

        assert result.exit_code == 1
        assert "No files match" in result.output


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


class TestIsGlobPattern:
    """Tests for _is_glob_pattern helper."""

    def test_recognizes_asterisk(self):
        from agr.cli.add import _is_glob_pattern
        assert _is_glob_pattern("./commands/*.md") is True

    def test_recognizes_question_mark(self):
        from agr.cli.add import _is_glob_pattern
        assert _is_glob_pattern("./commands/?.md") is True

    def test_recognizes_brackets(self):
        from agr.cli.add import _is_glob_pattern
        assert _is_glob_pattern("./commands/[abc].md") is True

    def test_rejects_plain_path(self):
        from agr.cli.add import _is_glob_pattern
        assert _is_glob_pattern("./commands/deploy.md") is False


class TestAddDirectory:
    """Tests for adding directory of resources."""

    def test_add_directory_adds_all_resources(self, tmp_path: Path, monkeypatch):
        """Test that adding a directory adds all contained resources."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create a directory with multiple commands
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "cmd1.md").write_text("# Cmd1")
        (commands_dir / "cmd2.md").write_text("# Cmd2")

        result = runner.invoke(app, ["add", "./commands/"])

        assert result.exit_code == 0
        assert "cmd1" in result.output
        assert "cmd2" in result.output

        config = AgrConfig.load(tmp_path / "agr.toml")
        local_deps = config.get_local_dependencies()
        assert len(local_deps) == 2

    def test_add_directory_with_skill_subdirs(self, tmp_path: Path, monkeypatch):
        """Test that directory with skill subdirectories adds all skills."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create skills directory with skill subdirs
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        for name in ["skill1", "skill2"]:
            skill_dir = skills_dir / name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"# {name}")

        result = runner.invoke(app, ["add", "./skills/"])

        assert result.exit_code == 0
        assert "skill1" in result.output
        assert "skill2" in result.output


class TestAddEmptyPackage:
    """Tests for empty package error."""

    def test_add_empty_package_errors(self, tmp_path: Path, monkeypatch):
        """Test that adding an empty package results in an error."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create empty package
        pkg_dir = tmp_path / "packages" / "empty"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "skills").mkdir()
        (pkg_dir / "commands").mkdir()
        (pkg_dir / "agents").mkdir()

        result = runner.invoke(app, ["add", "./packages/empty", "--type", "package"])

        assert result.exit_code == 1
        assert "contains no resources" in result.output


class TestPackageExplosion:
    """Tests for package explosion into type directories."""

    def test_package_explodes_to_type_directories(self, tmp_path: Path, monkeypatch):
        """Test that package contents are installed to their type directories."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create package with skill
        pkg_dir = tmp_path / "packages" / "toolkit"
        skills_dir = pkg_dir / "skills" / "myskill"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("# My Skill")
        # Also create commands dir
        (pkg_dir / "commands").mkdir(parents=True)
        (pkg_dir / "agents").mkdir(parents=True)

        result = runner.invoke(app, ["add", "./packages/toolkit", "--type", "package"])

        assert result.exit_code == 0

        # Verify installed to .claude/skills/<user>/toolkit/myskill/
        installed = tmp_path / ".claude" / "skills" / "local" / "toolkit" / "myskill" / "SKILL.md"
        assert installed.exists()

        # Verify NOT installed to old .claude/packages/ path
        old_path = tmp_path / ".claude" / "packages"
        assert not old_path.exists()


class TestAddNamespace:
    """Tests for namespace directory support."""

    def test_add_namespace_directory(self, tmp_path: Path, monkeypatch):
        """Test adding a namespace directory (directory of skill directories)."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create namespace with multiple skills
        namespace_dir = tmp_path / "my-namespace"
        namespace_dir.mkdir()
        for name in ["skill-a", "skill-b"]:
            skill_dir = namespace_dir / name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"# {name}")

        result = runner.invoke(app, ["add", "./my-namespace"])

        assert result.exit_code == 0
        assert "skill-a" in result.output
        assert "skill-b" in result.output

        # Verify installed to .claude/skills/<user>/<namespace>/<skill>/
        for name in ["skill-a", "skill-b"]:
            installed = tmp_path / ".claude" / "skills" / "local" / "my-namespace" / name / "SKILL.md"
            assert installed.exists()


class TestWorkspaceAdd:
    """Tests for -w/--workspace flag."""

    def test_add_to_workspace_local(self, tmp_path: Path, monkeypatch):
        """Test adding a local resource to a workspace."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create local skill
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        result = runner.invoke(app, ["add", "./skills/my-skill", "-w", "myworkspace"])

        assert result.exit_code == 0
        assert "workspace: myworkspace" in result.output

        # Verify agr.toml has packages section
        config = AgrConfig.load(tmp_path / "agr.toml")
        assert "myworkspace" in config.packages
        assert len(config.packages["myworkspace"].dependencies) == 1

    def test_workspace_creates_package_section(self, tmp_path: Path, monkeypatch):
        """Test that workspace creates the [packages] section in agr.toml."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create local command
        (tmp_path / "cmd.md").write_text("# Command")

        result = runner.invoke(app, ["add", "./cmd.md", "-w", "mypkg"])

        assert result.exit_code == 0

        content = (tmp_path / "agr.toml").read_text()
        assert "packages" in content
        assert "mypkg" in content
