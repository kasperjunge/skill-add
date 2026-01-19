"""Integration tests for unified agrx command."""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path

from agr.cli.run import app
from agr.fetcher import ResourceType, DiscoveredResource, DiscoveryResult
from agr.resolver import ResolvedResource, ResourceSource


runner = CliRunner()


class TestAgrxUnifiedCommand:
    """Tests for the unified agrx command."""

    @patch("agr.cli.run._run_resource")
    def test_explicit_type_skill(self, mock_run):
        """Test that --type skill delegates to skill runner."""
        result = runner.invoke(app, ["--type", "skill", "testuser/hello-world"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][1] == ResourceType.SKILL

    @patch("agr.cli.run._run_resource")
    def test_explicit_type_command(self, mock_run):
        """Test that --type command delegates to command runner."""
        result = runner.invoke(app, ["--type", "command", "testuser/hello"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][1] == ResourceType.COMMAND

    def test_invalid_type_shows_error(self):
        """Test that invalid --type shows an error."""
        result = runner.invoke(app, ["--type", "invalid", "testuser/hello"])

        assert result.exit_code == 1
        assert "Unknown resource type" in result.output

    @patch("agr.cli.run.downloaded_repo")
    @patch("agr.cli.run.discover_runnable_resource")
    def test_not_found_shows_error(self, mock_discover, mock_download, tmp_path):
        """Test that not found resources show a helpful error."""
        mock_download.return_value.__enter__ = MagicMock(return_value=tmp_path)
        mock_download.return_value.__exit__ = MagicMock(return_value=None)

        mock_discover.return_value = DiscoveryResult(resources=[])

        result = runner.invoke(app, ["testuser/nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    @patch("agr.cli.run.downloaded_repo")
    @patch("agr.cli.run.discover_runnable_resource")
    def test_ambiguous_resource_shows_error(self, mock_discover, mock_download, tmp_path):
        """Test that ambiguous resources show an error with --type suggestion."""
        mock_download.return_value.__enter__ = MagicMock(return_value=tmp_path)
        mock_download.return_value.__exit__ = MagicMock(return_value=None)

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

        result = runner.invoke(app, ["testuser/hello"])

        assert result.exit_code == 1
        assert "multiple types" in result.output.lower()
        assert "--type" in result.output


class TestDeprecatedAgrxCommands:
    """Tests for deprecated agrx subcommands."""

    @patch("agr.cli.run._run_resource")
    def test_agrx_skill_shows_deprecation_warning(self, mock_run):
        """Test that 'agrx skill' shows deprecation warning."""
        result = runner.invoke(app, ["skill", "testuser/hello-world"])

        assert "deprecated" in result.output.lower()
        assert "agrx testuser/hello-world" in result.output

    @patch("agr.cli.run._run_resource")
    def test_agrx_command_shows_deprecation_warning(self, mock_run):
        """Test that 'agrx command' shows deprecation warning."""
        result = runner.invoke(app, ["command", "testuser/hello"])

        assert "deprecated" in result.output.lower()
        assert "agrx testuser/hello" in result.output

    @patch("agr.cli.run._run_resource")
    def test_deprecated_skill_still_works(self, mock_run):
        """Test that deprecated commands call runner."""
        result = runner.invoke(app, ["skill", "testuser/hello-world"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][1] == ResourceType.SKILL

    @patch("agr.cli.run._run_resource")
    def test_deprecated_commands_pass_interactive(self, mock_run):
        """Test deprecated commands pass interactive flag."""
        result = runner.invoke(app, ["--interactive", "skill", "testuser/hello-world"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][3] is True  # interactive=True

    @patch("agr.cli.run._run_resource")
    def test_deprecated_commands_with_prompt(self, mock_run):
        """Test deprecated commands pass prompt argument."""
        result = runner.invoke(app, ["skill", "testuser/hello-world", "my prompt"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][2] == "my prompt"  # prompt_or_args


class TestInteractiveMode:
    """Tests for interactive mode (-i flag) behavior."""

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.fetch_resource")
    @patch("agr.cli.run._build_local_path")
    @patch("agr.cli.run._cleanup_resource")
    def test_interactive_mode_passes_dangerously_skip_permissions(
        self, mock_cleanup, mock_build_path, mock_fetch, mock_subprocess, mock_which, tmp_path
    ):
        """Test that -i flag passes --dangerously-skip-permissions to Claude CLI and then continues."""
        # Setup mocks
        mock_build_path.return_value = tmp_path / "_agrx_hello-world.md"

        result = runner.invoke(app, ["--type", "skill", "-i", "testuser/hello-world"])

        # Interactive mode calls subprocess twice: first to run skill, then to continue
        assert mock_subprocess.call_count == 2
        first_call_args = mock_subprocess.call_args_list[0][0][0]
        second_call_args = mock_subprocess.call_args_list[1][0][0]

        # First call runs the skill with --dangerously-skip-permissions
        assert "claude" in first_call_args
        assert "-p" in first_call_args
        assert "/_agrx_hello-world" in first_call_args
        assert "--dangerously-skip-permissions" in first_call_args

        # Second call continues the conversation interactively
        assert second_call_args == ["claude", "--continue"]

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.fetch_resource")
    @patch("agr.cli.run._build_local_path")
    @patch("agr.cli.run._cleanup_resource")
    def test_interactive_mode_includes_prompt_args(
        self, mock_cleanup, mock_build_path, mock_fetch, mock_subprocess, mock_which, tmp_path
    ):
        """Test that -i flag includes prompt_or_args in the skill invocation."""
        mock_build_path.return_value = tmp_path / "_agrx_hello-world.md"

        result = runner.invoke(app, ["--type", "skill", "-i", "testuser/hello-world", "my custom args"])

        # Interactive mode calls subprocess twice
        assert mock_subprocess.call_count == 2
        first_call_args = mock_subprocess.call_args_list[0][0][0]

        # The prompt should include both the skill and the args
        prompt_idx = first_call_args.index("-p") + 1
        prompt_value = first_call_args[prompt_idx]
        assert "/_agrx_hello-world" in prompt_value
        assert "my custom args" in prompt_value

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.fetch_resource")
    @patch("agr.cli.run._build_local_path")
    @patch("agr.cli.run._cleanup_resource")
    def test_non_interactive_mode_does_not_pass_continue(
        self, mock_cleanup, mock_build_path, mock_fetch, mock_subprocess, mock_which, tmp_path
    ):
        """Test that non-interactive mode does not pass --continue or --dangerously-skip-permissions."""
        mock_build_path.return_value = tmp_path / "_agrx_hello-world.md"

        result = runner.invoke(app, ["--type", "skill", "testuser/hello-world"])

        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]

        assert "--continue" not in call_args
        assert "--dangerously-skip-permissions" not in call_args

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.downloaded_repo")
    @patch("agr.cli.run.discover_runnable_resource")
    @patch("agr.cli.run.fetch_resource_from_repo_dir")
    @patch("agr.cli.run._build_local_path")
    @patch("agr.cli.run._cleanup_resource")
    def test_interactive_mode_unified_passes_correct_args(
        self, mock_cleanup, mock_build_path, mock_fetch_from_repo,
        mock_discover, mock_download, mock_subprocess, mock_which, tmp_path
    ):
        """Test that -i flag works correctly with auto-detected resource type."""
        # Setup mocks for unified mode (auto-detection)
        mock_download.return_value.__enter__ = MagicMock(return_value=tmp_path)
        mock_download.return_value.__exit__ = MagicMock(return_value=None)
        mock_build_path.return_value = tmp_path / "_agrx_hello.md"

        mock_discover.return_value = DiscoveryResult(
            resources=[
                DiscoveredResource(
                    name="hello",
                    resource_type=ResourceType.SKILL,
                    path_segments=["hello"]
                ),
            ]
        )

        result = runner.invoke(app, ["-i", "testuser/hello"])

        # Interactive mode calls subprocess twice: first to run skill, then to continue
        assert mock_subprocess.call_count == 2
        first_call_args = mock_subprocess.call_args_list[0][0][0]
        second_call_args = mock_subprocess.call_args_list[1][0][0]

        # First call runs the skill
        assert "claude" in first_call_args
        assert "-p" in first_call_args
        assert "--dangerously-skip-permissions" in first_call_args

        # Second call continues the conversation interactively
        assert second_call_args == ["claude", "--continue"]


class TestAutoDiscoveryFallback:
    """Tests for auto-discovery fallback using resolve_remote_resource."""

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.downloaded_repo")
    @patch("agr.cli.run.resolve_remote_resource")
    @patch("agr.cli.run.fetch_resource_from_repo_dir")
    @patch("agr.cli.run._build_local_path")
    @patch("agr.cli.run._cleanup_resource")
    def test_uses_resolver_before_discover_runnable(
        self, mock_cleanup, mock_build_path, mock_fetch_from_repo,
        mock_resolve, mock_download, mock_subprocess, mock_which, tmp_path
    ):
        """Test that resolve_remote_resource is called before discover_runnable_resource."""
        mock_download.return_value.__enter__ = MagicMock(return_value=tmp_path)
        mock_download.return_value.__exit__ = MagicMock(return_value=None)
        mock_build_path.return_value = tmp_path / "_agrx_bluesky"

        # Resolver finds the skill at repo root
        mock_resolve.return_value = ResolvedResource(
            name="bluesky",
            resource_type=ResourceType.SKILL,
            path=Path("bluesky"),
            source=ResourceSource.REPO_ROOT,
        )

        result = runner.invoke(app, ["testuser/skills/bluesky"])

        # Should call resolver first
        mock_resolve.assert_called_once()
        # Should use the resolved path
        mock_fetch_from_repo.assert_called_once()
        call_kwargs = mock_fetch_from_repo.call_args.kwargs
        assert call_kwargs.get("source_path") == Path("bluesky")

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.downloaded_repo")
    @patch("agr.cli.run.resolve_remote_resource")
    @patch("agr.cli.run.discover_runnable_resource")
    @patch("agr.cli.run.fetch_resource_from_repo_dir")
    @patch("agr.cli.run._build_local_path")
    @patch("agr.cli.run._cleanup_resource")
    def test_falls_back_to_discover_when_resolver_returns_none(
        self, mock_cleanup, mock_build_path, mock_fetch_from_repo,
        mock_discover, mock_resolve, mock_download, mock_subprocess, mock_which, tmp_path
    ):
        """Test that discover_runnable_resource is used when resolver returns None."""
        mock_download.return_value.__enter__ = MagicMock(return_value=tmp_path)
        mock_download.return_value.__exit__ = MagicMock(return_value=None)
        mock_build_path.return_value = tmp_path / "_agrx_hello"

        # Resolver doesn't find the resource
        mock_resolve.return_value = None

        # But discover_runnable_resource finds it
        mock_discover.return_value = DiscoveryResult(
            resources=[
                DiscoveredResource(
                    name="hello",
                    resource_type=ResourceType.SKILL,
                    path_segments=["hello"]
                ),
            ]
        )

        result = runner.invoke(app, ["testuser/hello"])

        # Should call both resolver and discover
        mock_resolve.assert_called_once()
        mock_discover.assert_called_once()
        # Should use the discovered resource (no source_path)
        call_kwargs = mock_fetch_from_repo.call_args.kwargs
        assert call_kwargs.get("source_path") is None

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.downloaded_repo")
    @patch("agr.cli.run.resolve_remote_resource")
    @patch("agr.cli.run.fetch_resource_from_repo_dir")
    @patch("agr.cli.run._build_local_path")
    @patch("agr.cli.run._cleanup_resource")
    def test_agr_toml_source_provides_source_path(
        self, mock_cleanup, mock_build_path, mock_fetch_from_repo,
        mock_resolve, mock_download, mock_subprocess, mock_which, tmp_path
    ):
        """Test that AGR_TOML source provides source_path to fetch."""
        mock_download.return_value.__enter__ = MagicMock(return_value=tmp_path)
        mock_download.return_value.__exit__ = MagicMock(return_value=None)
        mock_build_path.return_value = tmp_path / "_agrx_myskill"

        # Resolver finds via agr.toml
        mock_resolve.return_value = ResolvedResource(
            name="myskill",
            resource_type=ResourceType.SKILL,
            path=Path("resources/skills/myskill"),
            source=ResourceSource.AGR_TOML,
        )

        result = runner.invoke(app, ["testuser/myrepo/myskill"])

        mock_fetch_from_repo.assert_called_once()
        call_kwargs = mock_fetch_from_repo.call_args.kwargs
        assert call_kwargs.get("source_path") == Path("resources/skills/myskill")

    @patch("agr.cli.run.shutil.which", return_value="/usr/bin/claude")
    @patch("agr.cli.run.subprocess.run")
    @patch("agr.cli.run.downloaded_repo")
    @patch("agr.cli.run.resolve_remote_resource")
    @patch("agr.cli.run.fetch_resource_from_repo_dir")
    @patch("agr.cli.run._build_local_path")
    @patch("agr.cli.run._cleanup_resource")
    def test_claude_dir_source_does_not_provide_source_path(
        self, mock_cleanup, mock_build_path, mock_fetch_from_repo,
        mock_resolve, mock_download, mock_subprocess, mock_which, tmp_path
    ):
        """Test that CLAUDE_DIR source does not provide source_path (uses default paths)."""
        mock_download.return_value.__enter__ = MagicMock(return_value=tmp_path)
        mock_download.return_value.__exit__ = MagicMock(return_value=None)
        mock_build_path.return_value = tmp_path / "_agrx_commit"

        # Resolver finds in .claude/ directory
        mock_resolve.return_value = ResolvedResource(
            name="commit",
            resource_type=ResourceType.SKILL,
            path=Path(".claude/skills/commit"),
            source=ResourceSource.CLAUDE_DIR,
        )

        result = runner.invoke(app, ["testuser/commit"])

        mock_fetch_from_repo.assert_called_once()
        call_kwargs = mock_fetch_from_repo.call_args.kwargs
        # CLAUDE_DIR uses standard paths, so no source_path needed
        assert call_kwargs.get("source_path") is None

    @patch("agr.cli.run.downloaded_repo")
    @patch("agr.cli.run.resolve_remote_resource")
    @patch("agr.cli.run.discover_runnable_resource")
    def test_error_message_mentions_repo_root_search(
        self, mock_discover, mock_resolve, mock_download, tmp_path
    ):
        """Test that error message mentions repo root was searched."""
        mock_download.return_value.__enter__ = MagicMock(return_value=tmp_path)
        mock_download.return_value.__exit__ = MagicMock(return_value=None)

        # Neither finds the resource
        mock_resolve.return_value = None
        mock_discover.return_value = DiscoveryResult(resources=[])

        result = runner.invoke(app, ["testuser/nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()
        assert "repo root" in result.output.lower()
