"""Integration tests for unified remove command."""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from agr.cli.main import app
from agr.config import AgrConfig
from agr.fetcher import DiscoveredResource, DiscoveryResult, ResourceType


runner = CliRunner()


class TestRemoveUnifiedCommand:
    """Tests for the unified remove command."""

    @patch("agr.cli.common.discover_local_resource_type")
    @patch("agr.cli.common.handle_remove_resource")
    def test_auto_detects_skill(self, mock_remove, mock_discover):
        """Test that auto-detection correctly identifies a local skill."""
        mock_discover.return_value = DiscoveryResult(
            resources=[
                DiscoveredResource(
                    name="hello-world",
                    resource_type=ResourceType.SKILL,
                    path_segments=["hello-world"]
                )
            ]
        )

        result = runner.invoke(app, ["remove", "hello-world"])

        mock_remove.assert_called_once()
        call_args = mock_remove.call_args
        assert call_args[0][1] == ResourceType.SKILL

    @patch("agr.cli.common.handle_remove_resource")
    def test_explicit_type_skill(self, mock_handler):
        """Test that --type skill delegates to skill handler."""
        result = runner.invoke(app, ["remove", "--type", "skill", "hello-world"])

        mock_handler.assert_called_once()
        call_args = mock_handler.call_args
        assert call_args[0][1] == ResourceType.SKILL

    @patch("agr.cli.common.handle_remove_resource")
    def test_explicit_type_command(self, mock_handler):
        """Test that --type command delegates to command handler."""
        result = runner.invoke(app, ["remove", "--type", "command", "hello"])

        mock_handler.assert_called_once()
        call_args = mock_handler.call_args
        assert call_args[0][1] == ResourceType.COMMAND

    @patch("agr.cli.common.handle_remove_resource")
    def test_explicit_type_agent(self, mock_handler):
        """Test that --type agent delegates to agent handler."""
        result = runner.invoke(app, ["remove", "--type", "agent", "hello-agent"])

        mock_handler.assert_called_once()
        call_args = mock_handler.call_args
        assert call_args[0][1] == ResourceType.AGENT

    @patch("agr.cli.common.handle_remove_bundle")
    def test_explicit_type_bundle(self, mock_handler):
        """Test that --type bundle delegates to bundle handler."""
        result = runner.invoke(app, ["remove", "--type", "bundle", "my-bundle"])

        mock_handler.assert_called_once()

    def test_invalid_type_shows_error(self):
        """Test that invalid --type shows an error."""
        result = runner.invoke(app, ["remove", "--type", "invalid", "hello"])

        assert result.exit_code == 1
        assert "Unknown resource type" in result.output

    @patch("agr.cli.common.discover_local_resource_type")
    def test_ambiguous_resource_shows_error(self, mock_discover):
        """Test that ambiguous local resources show an error with --type suggestion."""
        mock_discover.return_value = DiscoveryResult(
            resources=[
                DiscoveredResource(
                    name="hello",
                    resource_type=ResourceType.SKILL,
                    path_segments=["hello"]
                ),
                DiscoveredResource(
                    name="hello",
                    resource_type=ResourceType.COMMAND,
                    path_segments=["hello"]
                ),
            ]
        )

        result = runner.invoke(app, ["remove", "hello"])

        assert result.exit_code == 1
        assert "multiple types" in result.output.lower()
        assert "--type" in result.output

    @patch("agr.cli.common.discover_local_resource_type")
    def test_not_found_shows_error(self, mock_discover):
        """Test that not found resources show a helpful error."""
        mock_discover.return_value = DiscoveryResult(resources=[])

        result = runner.invoke(app, ["remove", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestDeprecatedRemoveCommands:
    """Tests for deprecated remove subcommands."""

    @patch("agr.cli.common.handle_remove_resource")
    def test_remove_skill_shows_deprecation_warning(self, mock_handler):
        """Test that 'agr remove skill' shows deprecation warning."""
        result = runner.invoke(app, ["remove", "skill", "hello-world"])

        assert "deprecated" in result.output.lower()
        assert "agr remove hello-world" in result.output

    @patch("agr.cli.common.handle_remove_resource")
    def test_remove_command_shows_deprecation_warning(self, mock_handler):
        """Test that 'agr remove command' shows deprecation warning."""
        result = runner.invoke(app, ["remove", "command", "hello"])

        assert "deprecated" in result.output.lower()
        assert "agr remove hello" in result.output

    @patch("agr.cli.common.handle_remove_resource")
    def test_remove_agent_shows_deprecation_warning(self, mock_handler):
        """Test that 'agr remove agent' shows deprecation warning."""
        result = runner.invoke(app, ["remove", "agent", "hello-agent"])

        assert "deprecated" in result.output.lower()
        assert "agr remove hello-agent" in result.output

    @patch("agr.cli.remove.handle_remove_bundle")
    def test_remove_bundle_shows_deprecation_warning(self, mock_handler):
        """Test that 'agr remove bundle' shows deprecation warning."""
        result = runner.invoke(app, ["remove", "bundle", "my-bundle"])

        assert "deprecated" in result.output.lower()
        # Check for key parts (output may wrap across lines)
        assert "agr remove my-bundle" in result.output
        assert "--type" in result.output
        assert "bundle" in result.output

    @patch("agr.cli.remove.handle_remove_resource")
    def test_deprecated_skill_still_works(self, mock_handler):
        """Test that deprecated skill command calls handler."""
        result = runner.invoke(app, ["remove", "skill", "hello-world"])

        mock_handler.assert_called_once()
        call_args = mock_handler.call_args
        assert call_args[0][1] == ResourceType.SKILL

    @patch("agr.cli.remove.handle_remove_resource")
    def test_deprecated_commands_pass_global(self, mock_handler):
        """Test that deprecated commands pass flags correctly."""
        result = runner.invoke(app, ["remove", "--global", "skill", "hello-world"])

        mock_handler.assert_called_once()
        call_args = mock_handler.call_args
        assert call_args[0][3] is True  # global_install=True


class TestRemoveNamespacedAndToml:
    """Tests for namespaced paths and agr.toml integration in remove."""

    def test_remove_from_namespaced_path(self, tmp_path: Path, monkeypatch):
        """Test that remove works with namespaced paths."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create namespaced skill
        skill_dir = tmp_path / ".claude" / "skills" / "kasperjunge" / "commit"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Commit Skill")

        result = runner.invoke(app, ["remove", "commit"])

        assert result.exit_code == 0
        assert not skill_dir.exists()

    def test_remove_updates_agr_toml(self, tmp_path: Path, monkeypatch):
        """Test that remove updates agr.toml."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create agr.toml with dependency
        config = AgrConfig()
        config.add_remote("kasperjunge/commit", "skill")
        config.add_remote("alice/review", "command")
        config.save(tmp_path / "agr.toml")

        # Create namespaced skill
        skill_dir = tmp_path / ".claude" / "skills" / "kasperjunge" / "commit"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Commit Skill")

        result = runner.invoke(app, ["remove", "commit"])

        # Verify agr.toml was updated
        updated_config = AgrConfig.load(tmp_path / "agr.toml")
        assert updated_config.get_by_handle("kasperjunge/commit") is None
        assert updated_config.get_by_handle("alice/review") is not None

    def test_remove_with_full_ref(self, tmp_path: Path, monkeypatch):
        """Test that remove works with full ref (username/name)."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create namespaced skill
        skill_dir = tmp_path / ".claude" / "skills" / "kasperjunge" / "commit"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Commit Skill")

        result = runner.invoke(app, ["remove", "kasperjunge/commit"])

        assert result.exit_code == 0
        assert not skill_dir.exists()

    def test_remove_falls_back_to_flat_path(self, tmp_path: Path, monkeypatch):
        """Test that remove works with flat (legacy) paths."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create flat skill (legacy)
        skill_dir = tmp_path / ".claude" / "skills" / "commit"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Commit Skill")

        result = runner.invoke(app, ["remove", "commit"])

        assert result.exit_code == 0
        assert not skill_dir.exists()

    def test_remove_with_explicit_type(self, tmp_path: Path, monkeypatch):
        """Test that remove with --type works with namespaced paths."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create namespaced command
        cmd_dir = tmp_path / ".claude" / "commands" / "alice"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "review.md").write_text("# Review Command")

        # Also create agr.toml
        config = AgrConfig()
        config.add_remote("alice/review", "command")
        config.save(tmp_path / "agr.toml")

        result = runner.invoke(app, ["remove", "--type", "command", "review"])

        assert result.exit_code == 0
        assert not (cmd_dir / "review.md").exists()

        # Verify agr.toml was updated
        updated_config = AgrConfig.load(tmp_path / "agr.toml")
        assert "alice/review" not in updated_config.dependencies
