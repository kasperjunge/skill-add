"""Tests for agr sync owner/repo functionality."""

from pathlib import Path
from unittest.mock import patch, MagicMock
from contextlib import contextmanager

import pytest
from typer.testing import CliRunner

from agr.cli.main import app
from agr.config import AgrConfig
from agr.resolver import (
    discover_all_repo_resources,
    ResolvedResource,
    ResourceSource,
)
from agr.fetcher import ResourceType


runner = CliRunner()


@contextmanager
def mock_downloaded_repo(repo_dir: Path):
    """Context manager mock for downloaded_repo."""
    yield repo_dir


class TestDiscoverAllRepoResources:
    """Tests for discover_all_repo_resources function."""

    def test_discovers_resources_from_agr_toml(self, tmp_path: Path):
        """Test discovering resources declared in agr.toml."""
        # Create agr.toml with declared resources
        agr_toml = tmp_path / "agr.toml"
        agr_toml.write_text("""
dependencies = [
    {path = "resources/skills/commit", type = "skill"},
    {path = "resources/commands/docs.md", type = "command"},
]
""")

        # Create the resources
        skill_dir = tmp_path / "resources" / "skills" / "commit"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Commit Skill")

        cmd_file = tmp_path / "resources" / "commands" / "docs.md"
        cmd_file.parent.mkdir(parents=True)
        cmd_file.write_text("# Docs Command")

        resources = discover_all_repo_resources(tmp_path)

        assert len(resources) == 2
        names = {r.name for r in resources}
        assert "commit" in names
        assert "docs" in names

    def test_discovers_resources_from_claude_dir(self, tmp_path: Path):
        """Test discovering resources from .claude/ directory."""
        # Create skills in .claude/
        skill_dir = tmp_path / ".claude" / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        # Create command in .claude/
        cmd_dir = tmp_path / ".claude" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "my-command.md").write_text("# My Command")

        # Create agent in .claude/
        agent_dir = tmp_path / ".claude" / "agents"
        agent_dir.mkdir(parents=True)
        (agent_dir / "my-agent.md").write_text("# My Agent")

        resources = discover_all_repo_resources(tmp_path)

        assert len(resources) == 3
        names = {r.name for r in resources}
        assert "my-skill" in names
        assert "my-command" in names
        assert "my-agent" in names

    def test_discovers_root_skills(self, tmp_path: Path):
        """Test discovering skills at repo root (like maragudk/skills)."""
        # Create skills at root level (like maragudk/skills repo)
        for skill_name in ["bluesky", "brainstorm", "collaboration"]:
            skill_dir = tmp_path / skill_name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"# {skill_name} Skill")

        resources = discover_all_repo_resources(tmp_path)

        assert len(resources) == 3
        names = {r.name for r in resources}
        assert names == {"bluesky", "brainstorm", "collaboration"}

        # All should be from REPO_ROOT source
        for r in resources:
            assert r.source == ResourceSource.REPO_ROOT

    def test_deduplication_agr_toml_takes_priority(self, tmp_path: Path):
        """Test that resources from agr.toml take priority over .claude/."""
        # Create agr.toml with resource - use resources/ prefix for proper name extraction
        agr_toml = tmp_path / "agr.toml"
        agr_toml.write_text("""
dependencies = [
    {path = "resources/skills/my-skill", type = "skill"},
]
""")

        # Create skill at agr.toml path
        agr_skill = tmp_path / "resources" / "skills" / "my-skill"
        agr_skill.mkdir(parents=True)
        (agr_skill / "SKILL.md").write_text("# From agr.toml")

        # Also create in .claude/ (should be ignored due to same name)
        claude_skill = tmp_path / ".claude" / "skills" / "my-skill"
        claude_skill.mkdir(parents=True)
        (claude_skill / "SKILL.md").write_text("# From .claude")

        resources = discover_all_repo_resources(tmp_path)

        # Should only find one (agr.toml takes priority)
        assert len(resources) == 1
        assert resources[0].source == ResourceSource.AGR_TOML
        assert resources[0].path == Path("resources/skills/my-skill")

    def test_deduplication_claude_dir_takes_priority_over_root(self, tmp_path: Path):
        """Test that .claude/ takes priority over repo root."""
        # Create in .claude/
        claude_skill = tmp_path / ".claude" / "skills" / "my-skill"
        claude_skill.mkdir(parents=True)
        (claude_skill / "SKILL.md").write_text("# From .claude")

        # Also create at root (should be ignored)
        root_skill = tmp_path / "my-skill"
        root_skill.mkdir()
        (root_skill / "SKILL.md").write_text("# From root")

        resources = discover_all_repo_resources(tmp_path)

        # Should only find one
        assert len(resources) == 1
        assert resources[0].source == ResourceSource.CLAUDE_DIR

    def test_empty_repo_returns_empty_list(self, tmp_path: Path):
        """Test that empty repo returns empty list."""
        resources = discover_all_repo_resources(tmp_path)
        assert resources == []

    def test_skips_hidden_directories(self, tmp_path: Path):
        """Test that hidden directories are skipped in root discovery."""
        # Create skill in hidden directory
        hidden_skill = tmp_path / ".hidden" / "my-skill"
        hidden_skill.mkdir(parents=True)
        (hidden_skill / "SKILL.md").write_text("# Hidden Skill")

        # Create normal skill
        normal_skill = tmp_path / "normal-skill"
        normal_skill.mkdir()
        (normal_skill / "SKILL.md").write_text("# Normal Skill")

        resources = discover_all_repo_resources(tmp_path)

        assert len(resources) == 1
        assert resources[0].name == "normal-skill"


class TestSyncRepoCommand:
    """Tests for agr sync owner/repo command."""

    @patch("agr.cli.sync.downloaded_repo")
    def test_sync_repo_discovers_and_installs(
        self, mock_download, tmp_path: Path, monkeypatch
    ):
        """Test that sync owner/repo discovers and installs resources."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create a mock repo directory with skills
        repo_dir = tmp_path / "mock_repo"
        for skill_name in ["skill-a", "skill-b"]:
            skill_dir = repo_dir / skill_name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(f"# {skill_name}")

        mock_download.return_value.__enter__ = lambda self: repo_dir
        mock_download.return_value.__exit__ = lambda self, *args: None

        result = runner.invoke(app, ["sync", "testowner/testrepo", "--yes"])

        assert result.exit_code == 0
        assert "skill-a" in result.output
        assert "skill-b" in result.output

    @patch("agr.cli.sync.downloaded_repo")
    def test_sync_repo_shows_discovered_resources(
        self, mock_download, tmp_path: Path, monkeypatch
    ):
        """Test that sync shows discovered resources before confirming."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create mock repo with resources
        repo_dir = tmp_path / "mock_repo"
        skill_dir = repo_dir / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        mock_download.return_value.__enter__ = lambda self: repo_dir
        mock_download.return_value.__exit__ = lambda self, *args: None

        # Decline the confirmation
        result = runner.invoke(app, ["sync", "testowner/testrepo"], input="n\n")

        assert "Discovered" in result.output
        assert "my-skill" in result.output
        assert "Cancelled" in result.output

    @patch("agr.cli.sync.downloaded_repo")
    def test_sync_repo_with_yes_skips_confirmation(
        self, mock_download, tmp_path: Path, monkeypatch
    ):
        """Test that --yes flag skips confirmation."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        repo_dir = tmp_path / "mock_repo"
        skill_dir = repo_dir / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Test Skill")

        mock_download.return_value.__enter__ = lambda self: repo_dir
        mock_download.return_value.__exit__ = lambda self, *args: None

        result = runner.invoke(app, ["sync", "testowner/testrepo", "--yes"])

        # Should not ask for confirmation
        assert "Install" not in result.output or "resources?" not in result.output
        assert result.exit_code == 0

    @patch("agr.cli.sync.downloaded_repo")
    def test_sync_repo_empty_shows_message(
        self, mock_download, tmp_path: Path, monkeypatch
    ):
        """Test that empty repo shows appropriate message."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Empty repo directory
        repo_dir = tmp_path / "mock_repo"
        repo_dir.mkdir()

        mock_download.return_value.__enter__ = lambda self: repo_dir
        mock_download.return_value.__exit__ = lambda self, *args: None

        result = runner.invoke(app, ["sync", "testowner/testrepo", "--yes"])

        assert "No resources found" in result.output

    @patch("agr.cli.sync.downloaded_repo")
    def test_sync_repo_adds_to_agr_toml(
        self, mock_download, tmp_path: Path, monkeypatch
    ):
        """Test that installed resources are added to agr.toml."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        repo_dir = tmp_path / "mock_repo"
        skill_dir = repo_dir / "installed-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Installed Skill")

        mock_download.return_value.__enter__ = lambda self: repo_dir
        mock_download.return_value.__exit__ = lambda self, *args: None

        result = runner.invoke(app, ["sync", "testowner/testrepo", "--yes"])

        assert result.exit_code == 0

        # Check agr.toml was created with dependency
        config = AgrConfig.load(tmp_path / "agr.toml")
        handles = [d.handle for d in config.dependencies if d.handle]
        assert any("installed-skill" in h for h in handles)

    @patch("agr.cli.sync.downloaded_repo")
    def test_sync_repo_skips_existing_without_overwrite(
        self, mock_download, tmp_path: Path, monkeypatch
    ):
        """Test that existing resources are skipped without --overwrite."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        repo_dir = tmp_path / "mock_repo"
        skill_dir = repo_dir / "existing-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# New Version")

        mock_download.return_value.__enter__ = lambda self: repo_dir
        mock_download.return_value.__exit__ = lambda self, *args: None

        # Pre-install the skill
        existing_dir = tmp_path / ".claude" / "skills" / "testowner:existing-skill"
        existing_dir.mkdir(parents=True)
        (existing_dir / "SKILL.md").write_text("# Old Version")

        result = runner.invoke(app, ["sync", "testowner/testrepo", "--yes"])

        assert "exists" in result.output.lower() or "skipped" in result.output.lower()
        # Old version should still be there
        assert "Old Version" in (existing_dir / "SKILL.md").read_text()

    @patch("agr.cli.sync.downloaded_repo")
    def test_sync_repo_overwrites_with_flag(
        self, mock_download, tmp_path: Path, monkeypatch
    ):
        """Test that --overwrite replaces existing resources."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        repo_dir = tmp_path / "mock_repo"
        skill_dir = repo_dir / "existing-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# New Version")

        mock_download.return_value.__enter__ = lambda self: repo_dir
        mock_download.return_value.__exit__ = lambda self, *args: None

        # Pre-install the skill
        existing_dir = tmp_path / ".claude" / "skills" / "testowner:existing-skill"
        existing_dir.mkdir(parents=True)
        (existing_dir / "SKILL.md").write_text("# Old Version")

        result = runner.invoke(
            app, ["sync", "testowner/testrepo", "--yes", "--overwrite"]
        )

        assert result.exit_code == 0
        # Should be updated (name field is updated to include namespace)
        content = (existing_dir / "SKILL.md").read_text()
        assert "name: testowner:existing-skill" in content

    def test_sync_repo_invalid_format_error(self, tmp_path: Path, monkeypatch):
        """Test that invalid repo format shows error."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        result = runner.invoke(app, ["sync", "invalid-format", "--yes"])

        assert result.exit_code == 1
        assert "Invalid repository reference" in result.output

    def test_sync_repo_with_three_parts_error(self, tmp_path: Path, monkeypatch):
        """Test that three-part format (owner/repo/resource) shows error."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        result = runner.invoke(app, ["sync", "owner/repo/resource", "--yes"])

        assert result.exit_code == 1
        assert "Invalid repository reference" in result.output


class TestAddSyncHint:
    """Tests for the sync hint in agr add command."""

    @patch("agr.cli.handlers.downloaded_repo")
    def test_add_shows_sync_hint_when_resource_not_found(
        self, mock_download, tmp_path: Path, monkeypatch
    ):
        """Test that agr add owner/repo shows sync hint when resource not found."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create empty repo (no resources)
        repo_dir = tmp_path / "mock_repo"
        repo_dir.mkdir()

        mock_download.return_value.__enter__ = lambda self: repo_dir
        mock_download.return_value.__exit__ = lambda self, *args: None

        result = runner.invoke(app, ["add", "testowner/testrepo"])

        assert result.exit_code == 1
        # Should show the hint
        assert "agr sync testowner/testrepo" in result.output
        assert "Hint" in result.output

    @patch("agr.cli.handlers.downloaded_repo")
    def test_add_no_hint_for_three_part_refs(
        self, mock_download, tmp_path: Path, monkeypatch
    ):
        """Test that agr add owner/repo/resource doesn't show sync hint."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create empty repo
        repo_dir = tmp_path / "mock_repo"
        repo_dir.mkdir()

        mock_download.return_value.__enter__ = lambda self: repo_dir
        mock_download.return_value.__exit__ = lambda self, *args: None

        result = runner.invoke(app, ["add", "testowner/testrepo/nonexistent"])

        assert result.exit_code == 1
        # Should NOT show the sync hint for three-part refs
        assert "agr sync" not in result.output


class TestRepoSyncResult:
    """Tests for RepoSyncResult dataclass."""

    def test_total_installed_counts_all_types(self):
        """Test that total_installed counts all resource types."""
        from agr.cli.sync import RepoSyncResult

        result = RepoSyncResult(
            installed_skills=["a", "b"],
            installed_commands=["c"],
            installed_agents=["d"],
            installed_rules=["e", "f"],
        )

        assert result.total_installed == 6

    def test_total_skipped_counts_skipped(self):
        """Test that total_skipped counts skipped resources."""
        from agr.cli.sync import RepoSyncResult

        result = RepoSyncResult(
            skipped=["x", "y", "z"],
        )

        assert result.total_skipped == 3

    def test_total_errors_counts_errors(self):
        """Test that total_errors counts errors."""
        from agr.cli.sync import RepoSyncResult

        result = RepoSyncResult(
            errors=[("a", "error1"), ("b", "error2")],
        )

        assert result.total_errors == 2
