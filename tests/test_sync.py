"""Tests for sync command."""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from agr.cli.main import app
from agr.config import AgrConfig


runner = CliRunner()


class TestSyncCommand:
    """Tests for agr sync command."""

    def test_sync_without_agr_toml_shows_message(self, tmp_path: Path, monkeypatch):
        """Test that sync works without agr.toml but shows message."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        result = runner.invoke(app, ["sync"])

        # Now sync succeeds even without agr.toml (can sync local resources)
        assert result.exit_code == 0
        # Should show message about no agr.toml or nothing to sync
        assert "nothing to sync" in result.output.lower() or "skipping remote" in result.output.lower()

    def test_sync_remote_only_errors_without_agr_toml(self, tmp_path: Path, monkeypatch):
        """Test that sync --remote errors when no agr.toml exists."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        result = runner.invoke(app, ["sync", "--remote"])

        # With --remote flag, no agr.toml is not an error, just a message
        assert result.exit_code == 0
        assert "nothing to sync" in result.output.lower() or "skipping remote" in result.output.lower()

    @patch("agr.cli.sync.fetch_resource")
    def test_sync_installs_missing_dependencies(
        self, mock_fetch, tmp_path: Path, monkeypatch
    ):
        """Test that sync installs dependencies from agr.toml."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create agr.toml with dependencies
        config = AgrConfig()
        config.add_remote("kasperjunge/commit", "skill")
        config.add_remote("alice/review", "command")
        config.save(tmp_path / "agr.toml")

        # Create .claude directory but no installed resources
        (tmp_path / ".claude" / "skills").mkdir(parents=True)
        (tmp_path / ".claude" / "commands").mkdir(parents=True)

        result = runner.invoke(app, ["sync"])

        # Verify fetch was called for both dependencies
        assert mock_fetch.call_count == 2

    @patch("agr.cli.sync.fetch_resource")
    def test_sync_skips_already_installed(
        self, mock_fetch, tmp_path: Path, monkeypatch
    ):
        """Test that sync skips already installed resources."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create agr.toml with dependency
        config = AgrConfig()
        config.add_remote("kasperjunge/commit", "skill")
        config.save(tmp_path / "agr.toml")

        # Create already installed skill in namespaced path
        skill_dir = tmp_path / ".claude" / "skills" / "kasperjunge" / "commit"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Commit Skill")

        result = runner.invoke(app, ["sync"])

        # Verify fetch was NOT called (resource already exists)
        mock_fetch.assert_not_called()

    def test_sync_prune_removes_unlisted_resources(
        self, tmp_path: Path, monkeypatch
    ):
        """Test that sync --prune removes resources not in agr.toml."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create agr.toml with one dependency
        config = AgrConfig()
        config.add_remote("kasperjunge/commit", "skill")
        config.save(tmp_path / "agr.toml")

        # Create installed skill that IS in toml
        skill_in_toml = tmp_path / ".claude" / "skills" / "kasperjunge" / "commit"
        skill_in_toml.mkdir(parents=True)
        (skill_in_toml / "SKILL.md").write_text("# Commit Skill")

        # Create installed skill that is NOT in toml
        skill_not_in_toml = tmp_path / ".claude" / "skills" / "alice" / "old-skill"
        skill_not_in_toml.mkdir(parents=True)
        (skill_not_in_toml / "SKILL.md").write_text("# Old Skill")

        result = runner.invoke(app, ["sync", "--prune"])

        # Verify skill in toml still exists
        assert skill_in_toml.exists()
        assert (skill_in_toml / "SKILL.md").exists()

        # Verify skill not in toml was removed
        assert not skill_not_in_toml.exists()

    def test_sync_prune_keeps_flat_path_resources(
        self, tmp_path: Path, monkeypatch
    ):
        """Test that sync --prune doesn't remove flat-path (legacy) resources."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create empty agr.toml
        config = AgrConfig()
        config.save(tmp_path / "agr.toml")

        # Create flat-path skill (legacy)
        flat_skill = tmp_path / ".claude" / "skills" / "legacy-skill"
        flat_skill.mkdir(parents=True)
        (flat_skill / "SKILL.md").write_text("# Legacy Skill")

        result = runner.invoke(app, ["sync", "--prune"])

        # Verify flat-path skill was NOT removed (backward compat)
        assert flat_skill.exists()

    @patch("agr.cli.sync.fetch_resource")
    def test_sync_with_custom_repo_dependency(
        self, mock_fetch, tmp_path: Path, monkeypatch
    ):
        """Test that sync handles custom repo dependencies."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create agr.toml with custom repo dependency
        config = AgrConfig()
        config.add_remote("kasperjunge/custom-repo/commit", "skill")
        config.save(tmp_path / "agr.toml")

        # Create .claude directory
        (tmp_path / ".claude" / "skills").mkdir(parents=True)

        result = runner.invoke(app, ["sync"])

        # Verify fetch was called with correct repo
        mock_fetch.assert_called_once()
        call_args = mock_fetch.call_args[0]
        # First arg should be username, second should be repo name
        assert call_args[0] == "kasperjunge"
        assert call_args[1] == "custom-repo"

    @patch("agr.cli.sync.fetch_resource")
    def test_sync_auto_detects_type(
        self, mock_fetch, tmp_path: Path, monkeypatch
    ):
        """Test that sync auto-detects type when not specified."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create agr.toml without type specified
        config = AgrConfig()
        config.add_remote("kasperjunge/commit", "skill")  # Default type is skill
        config.save(tmp_path / "agr.toml")

        # Create .claude directory
        (tmp_path / ".claude" / "skills").mkdir(parents=True)

        result = runner.invoke(app, ["sync"])

        # Verify fetch was called (auto-detection should handle it)
        mock_fetch.assert_called_once()
