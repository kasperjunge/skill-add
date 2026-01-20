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

        # Verify installed to .claude/ with flattened name
        installed = tmp_path / ".claude" / "skills" / "local:my-skill" / "SKILL.md"
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

    def test_add_local_md_file_requires_type_or_type_dir(self, tmp_path: Path, monkeypatch):
        """Test that .md files not under type dirs require --type."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        (tmp_path / "cmd.md").write_text("# Command")

        result = runner.invoke(app, ["add", "./cmd.md"])

        assert result.exit_code == 1
        assert "Cannot determine resource type" in result.output


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
    """Tests for is_local_path helper."""

    def test_recognizes_dot_slash(self):
        from agr.cli.common import is_local_path
        assert is_local_path("./path/to/file") is True

    def test_recognizes_absolute_path(self):
        from agr.cli.common import is_local_path
        assert is_local_path("/absolute/path") is True

    def test_recognizes_parent_path(self):
        from agr.cli.common import is_local_path
        assert is_local_path("../parent/path") is True

    def test_rejects_remote_ref(self):
        from agr.cli.common import is_local_path
        assert is_local_path("kasperjunge/commit") is False

    def test_rejects_remote_ref_with_repo(self):
        from agr.cli.common import is_local_path
        assert is_local_path("kasperjunge/repo/name") is False


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

        # Verify installed to .claude/skills/<flattened_name>/
        # Package skills use flattened names: local:toolkit:myskill
        installed = tmp_path / ".claude" / "skills" / "local:toolkit:myskill" / "SKILL.md"
        assert installed.exists()

        # Verify NOT installed to old .claude/packages/ path
        old_path = tmp_path / ".claude" / "packages"
        assert not old_path.exists()


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

        # Create local command under commands/ directory
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "cmd.md").write_text("# Command")

        result = runner.invoke(app, ["add", "./commands/cmd.md", "-w", "mypkg"])

        assert result.exit_code == 0

        content = (tmp_path / "agr.toml").read_text()
        assert "packages" in content
        assert "mypkg" in content


class TestNoAutoDetection:
    """Tests verifying structure-based auto-detection is removed."""

    def test_directory_with_skills_subdir_not_package(self, tmp_path: Path, monkeypatch):
        """Directory with skills/ subdir but no PACKAGE.md is NOT a package."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        dir_path = tmp_path / "my-dir"
        dir_path.mkdir()
        skills_dir = dir_path / "skills" / "test-skill"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("# Test")

        from agr.cli.add import _detect_local_type
        assert _detect_local_type(dir_path) is None  # NOT "package"

    def test_directory_with_nested_skills_not_namespace(self, tmp_path: Path):
        """Directory with nested SKILL.md files is NOT detected as namespace."""
        dir_path = tmp_path / "my-dir"
        nested = dir_path / "category" / "skill"
        nested.mkdir(parents=True)
        (nested / "SKILL.md").write_text("# Nested")

        from agr.cli.add import _detect_local_type
        assert _detect_local_type(dir_path) is None  # NOT "namespace"

    def test_packages_path_not_auto_package(self, tmp_path: Path):
        """Directory in packages/ without PACKAGE.md is NOT auto-detected as package."""
        pkg_dir = tmp_path / "packages" / "my-pkg"
        pkg_dir.mkdir(parents=True)
        skills_dir = pkg_dir / "skills" / "skill1"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("# Skill")

        from agr.cli.add import _detect_local_type
        assert _detect_local_type(pkg_dir) is None  # NOT "package"

    def test_directory_with_nested_skills_uses_discovery(self, tmp_path: Path, monkeypatch):
        """Directory with nested skills routes to discovery, not namespace handler."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create directory with skills (but no PACKAGE.md)
        dir_path = tmp_path / "my-skills"
        dir_path.mkdir()
        for name in ["skill-a", "skill-b"]:
            skill_dir = dir_path / name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"# {name}")

        result = runner.invoke(app, ["add", "./my-skills"])

        assert result.exit_code == 0
        # Skills installed WITHOUT parent directory prefix (discovery behavior)
        assert "local:skill-a" in result.output
        assert "local:skill-b" in result.output


class TestNestedCommandAgentPaths:
    """Tests for nested command/agent installation paths."""

    def test_command_in_nested_path_installed_to_nested_dir(self, tmp_path: Path, monkeypatch):
        """Test that commands in nested paths are installed to nested directories."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create nested command structure
        commands_dir = tmp_path / "commands" / "infra" / "deploy"
        commands_dir.mkdir(parents=True)
        cmd_file = commands_dir / "run.md"
        cmd_file.write_text("# Deploy run command")

        result = runner.invoke(app, ["add", "./commands/infra/deploy/run.md", "--type", "command"])

        assert result.exit_code == 0

        # Verify installed to nested path: .claude/commands/local/infra/deploy/run.md
        installed = tmp_path / ".claude" / "commands" / "local" / "infra" / "deploy" / "run.md"
        assert installed.exists()

    def test_agent_in_nested_path_installed_to_nested_dir(self, tmp_path: Path, monkeypatch):
        """Test that agents in nested paths are installed to nested directories."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create nested agent structure
        agents_dir = tmp_path / "agents" / "code" / "review"
        agents_dir.mkdir(parents=True)
        agent_file = agents_dir / "linter.md"
        agent_file.write_text("# Code review linter agent")

        result = runner.invoke(app, ["add", "./agents/code/review/linter.md", "--type", "agent"])

        assert result.exit_code == 0

        # Verify installed to nested path: .claude/agents/local/code/review/linter.md
        installed = tmp_path / ".claude" / "agents" / "local" / "code" / "review" / "linter.md"
        assert installed.exists()

    def test_package_with_nested_commands_explodes_to_nested_dirs(self, tmp_path: Path, monkeypatch):
        """Test that packages with nested commands preserve the nested structure."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create package with nested commands
        pkg_dir = tmp_path / "packages" / "toolkit"
        pkg_dir.mkdir(parents=True)

        # Add nested commands
        cmds_dir = pkg_dir / "commands" / "infra"
        cmds_dir.mkdir(parents=True)
        (cmds_dir / "deploy.md").write_text("# Deploy")

        # Add a skill so package is not empty
        skills_dir = pkg_dir / "skills" / "helper"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("# Helper")

        (pkg_dir / "agents").mkdir()

        result = runner.invoke(app, ["add", "./packages/toolkit", "--type", "package"])

        assert result.exit_code == 0

        # Verify command installed to nested path: .claude/commands/local/toolkit/infra/deploy.md
        installed_cmd = tmp_path / ".claude" / "commands" / "local" / "toolkit" / "infra" / "deploy.md"
        assert installed_cmd.exists()

    def test_flat_command_still_works(self, tmp_path: Path, monkeypatch):
        """Test that commands at root level still work as before."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create flat command
        (tmp_path / "commit.md").write_text("# Commit command")

        result = runner.invoke(app, ["add", "./commit.md", "--type", "command"])

        assert result.exit_code == 0

        # Verify installed to flat path: .claude/commands/local/commit.md
        installed = tmp_path / ".claude" / "commands" / "local" / "commit.md"
        assert installed.exists()


class TestDetectResourceTypeFromAncestors:
    """Tests for detect_resource_type_from_ancestors function."""

    def test_detect_type_from_commands_dir(self, tmp_path: Path):
        """File directly under commands/ detected as command."""
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        file_path = commands_dir / "deploy.md"
        file_path.write_text("# Deploy")

        from agr.cli.add import detect_resource_type_from_ancestors
        assert detect_resource_type_from_ancestors(file_path) == "command"

    def test_detect_type_from_nested_commands(self, tmp_path: Path):
        """File deep under commands/ still detected as command."""
        nested_dir = tmp_path / "commands" / "infra" / "aws"
        nested_dir.mkdir(parents=True)
        file_path = nested_dir / "deploy.md"
        file_path.write_text("# Deploy")

        from agr.cli.add import detect_resource_type_from_ancestors
        assert detect_resource_type_from_ancestors(file_path) == "command"

    def test_detect_type_from_agents_dir(self, tmp_path: Path):
        """File under agents/ detected as agent."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        file_path = agents_dir / "reviewer.md"
        file_path.write_text("# Reviewer")

        from agr.cli.add import detect_resource_type_from_ancestors
        assert detect_resource_type_from_ancestors(file_path) == "agent"

    def test_detect_type_from_rules_dir(self, tmp_path: Path):
        """File under rules/ detected as rule."""
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        file_path = rules_dir / "style.md"
        file_path.write_text("# Style Guide")

        from agr.cli.add import detect_resource_type_from_ancestors
        assert detect_resource_type_from_ancestors(file_path) == "rule"

    def test_detect_type_no_type_dir(self, tmp_path: Path):
        """File not under type directory returns None."""
        file_path = tmp_path / "random.md"
        file_path.write_text("# Random")

        from agr.cli.add import detect_resource_type_from_ancestors
        assert detect_resource_type_from_ancestors(file_path) is None

    def test_closest_type_dir_wins(self, tmp_path: Path):
        """When multiple type dirs in path, closest one wins."""
        # Create path like agents/commands/x.md
        nested_dir = tmp_path / "agents" / "commands"
        nested_dir.mkdir(parents=True)
        file_path = nested_dir / "test.md"
        file_path.write_text("# Test")

        from agr.cli.add import detect_resource_type_from_ancestors
        # "commands" is closer than "agents", so it should win
        assert detect_resource_type_from_ancestors(file_path) == "command"


class TestAncestorDetectionIntegration:
    """Integration tests for ancestor-based type detection."""

    def test_add_command_from_commands_dir(self, tmp_path: Path, monkeypatch):
        """Adding ./commands/deploy.md auto-detects as command."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "deploy.md").write_text("# Deploy")

        result = runner.invoke(app, ["add", "./commands/deploy.md"])

        assert result.exit_code == 0
        assert "Added local command 'deploy'" in result.output

        # Verify installed to .claude/commands/
        installed = tmp_path / ".claude" / "commands" / "local" / "deploy.md"
        assert installed.exists()

    def test_add_agent_from_agents_dir(self, tmp_path: Path, monkeypatch):
        """Adding ./agents/reviewer.md auto-detects as agent."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "reviewer.md").write_text("# Reviewer")

        result = runner.invoke(app, ["add", "./agents/reviewer.md"])

        assert result.exit_code == 0
        assert "Added local agent 'reviewer'" in result.output

        # Verify installed to .claude/agents/
        installed = tmp_path / ".claude" / "agents" / "local" / "reviewer.md"
        assert installed.exists()

    def test_add_rule_from_rules_dir(self, tmp_path: Path, monkeypatch):
        """Adding ./rules/style.md auto-detects as rule."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "style.md").write_text("# Style Guide")

        result = runner.invoke(app, ["add", "./rules/style.md"])

        assert result.exit_code == 0
        assert "Added local rule 'style'" in result.output

        # Verify installed to .claude/rules/
        installed = tmp_path / ".claude" / "rules" / "local" / "style.md"
        assert installed.exists()

    def test_add_nested_command_preserves_path(self, tmp_path: Path, monkeypatch):
        """Adding ./commands/infra/aws/deploy.md preserves nested structure."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        nested_dir = tmp_path / "commands" / "infra" / "aws"
        nested_dir.mkdir(parents=True)
        (nested_dir / "deploy.md").write_text("# Deploy")

        result = runner.invoke(app, ["add", "./commands/infra/aws/deploy.md"])

        assert result.exit_code == 0
        assert "Added local command 'deploy'" in result.output

        # Verify installed to nested path: .claude/commands/local/infra/aws/deploy.md
        installed = tmp_path / ".claude" / "commands" / "local" / "infra" / "aws" / "deploy.md"
        assert installed.exists()


class TestAmbiguousFileErrorHandling:
    """Tests for error handling when type cannot be determined."""

    def test_error_message_for_root_md_file(self, tmp_path: Path, monkeypatch):
        """Clear error when .md file is not under type directory."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        (tmp_path / "random.md").write_text("# Random")

        result = runner.invoke(app, ["add", "./random.md"])

        assert result.exit_code == 1
        assert "Cannot determine resource type" in result.output
        assert "not under a commands/, agents/, or rules/ directory" in result.output
        assert "--type" in result.output

    def test_type_flag_overrides_detection(self, tmp_path: Path, monkeypatch):
        """--type flag allows adding ambiguous files."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        (tmp_path / "random.md").write_text("# Random Command")

        result = runner.invoke(app, ["add", "./random.md", "--type", "command"])

        assert result.exit_code == 0
        assert "Added local command 'random'" in result.output

    def test_type_flag_overrides_auto_detection(self, tmp_path: Path, monkeypatch):
        """--type takes precedence over auto-detection."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create a file under commands/ but force it to be an agent
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "deploy.md").write_text("# Deploy Agent")

        result = runner.invoke(app, ["add", "./commands/deploy.md", "--type", "agent"])

        assert result.exit_code == 0
        assert "Added local agent 'deploy'" in result.output

        # Verify installed to .claude/agents/
        installed = tmp_path / ".claude" / "agents" / "local" / "deploy.md"
        assert installed.exists()
