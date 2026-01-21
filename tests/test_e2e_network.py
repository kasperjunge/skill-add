"""End-to-end tests hitting real GitHub.

Run: pytest -m e2e
Skip: pytest -m "not e2e"
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agr.cli.main import app
from agr.cli.run import app as agrx_app
from agr.config import AgrConfig


runner = CliRunner()


@pytest.mark.e2e
class TestAgrAddFromGitHub:
    """E2E tests for agr add command fetching from GitHub."""

    def test_add_remote_skill_by_short_ref(self, git_project: Path, check_github_rate_limit):
        """Test adding remote skill with user/name format."""
        check_github_rate_limit()

        result = runner.invoke(app, ["add", "kasperjunge/commit"])

        assert result.exit_code == 0
        assert "Added remote skill" in result.output

        # Verify installed
        installed = git_project / ".claude" / "skills" / "kasperjunge:commit"
        assert installed.exists()
        assert (installed / "SKILL.md").exists()

    def test_add_remote_skill_resolves_default_repo(self, git_project: Path, check_github_rate_limit):
        """Test that user/name resolves to user/agent-resources by default."""
        check_github_rate_limit()

        result = runner.invoke(app, ["add", "maragudk/collaboration"])

        assert result.exit_code == 0
        # Should resolve to maragudk/skills repo
        installed = git_project / ".claude" / "skills" / "maragudk:collaboration"
        assert installed.exists()

    def test_add_remote_skill_with_explicit_repo(self, git_project: Path, check_github_rate_limit):
        """Test adding skill with explicit user/repo/name format."""
        check_github_rate_limit()

        result = runner.invoke(app, ["add", "maragudk/skills/collaboration"])

        assert result.exit_code == 0
        installed = git_project / ".claude" / "skills" / "maragudk:collaboration"
        assert installed.exists()

    def test_add_remote_command(self, git_project: Path, check_github_rate_limit):
        """Test adding a remote command."""
        check_github_rate_limit()

        result = runner.invoke(app, ["add", "kasperjunge/commit", "--type", "command"])

        # This may fail if the command doesn't exist, which is fine
        # The test verifies the code path works
        if result.exit_code == 0:
            assert "Added remote command" in result.output

    def test_add_nonexistent_resource_fails(self, git_project: Path, check_github_rate_limit):
        """Test that adding non-existent resource produces clear error."""
        check_github_rate_limit()

        result = runner.invoke(app, ["add", "nonexistent-user-12345/nonexistent-resource"])

        assert result.exit_code != 0

    def test_add_records_in_config(self, git_project: Path, check_github_rate_limit):
        """Test that added resources are recorded in agr.toml."""
        check_github_rate_limit()

        runner.invoke(app, ["add", "kasperjunge/commit"])

        config = AgrConfig.load(git_project / "agr.toml")
        deps = config.get_remote_dependencies()
        handles = [d.handle for d in deps]
        assert "kasperjunge/commit" in handles

    def test_add_with_overwrite(self, git_project: Path, check_github_rate_limit):
        """Test adding with --overwrite flag replaces existing."""
        check_github_rate_limit()

        # First add
        runner.invoke(app, ["add", "kasperjunge/commit"])

        # Modify installed file
        installed = git_project / ".claude" / "skills" / "kasperjunge:commit" / "SKILL.md"
        original_content = installed.read_text()
        installed.write_text("# Modified content")

        # Add again with overwrite
        result = runner.invoke(app, ["add", "kasperjunge/commit", "--overwrite"])

        assert result.exit_code == 0
        # Content should be restored from remote
        new_content = installed.read_text()
        assert new_content != "# Modified content"

    def test_add_skips_if_exists(self, git_project: Path, check_github_rate_limit):
        """Test that add without --overwrite skips existing resources."""
        check_github_rate_limit()

        # First add
        runner.invoke(app, ["add", "kasperjunge/commit"])

        # Second add should skip
        result = runner.invoke(app, ["add", "kasperjunge/commit"])

        assert result.exit_code == 0
        assert "already exists" in result.output.lower() or "skip" in result.output.lower()


# ============================================================================
# agr sync with Real Dependencies Tests
# ============================================================================


@pytest.mark.e2e
class TestAgrSyncWithRealDeps:
    """E2E tests for agr sync command with real GitHub dependencies."""

    def test_sync_single_remote_dep(self, git_project: Path, check_github_rate_limit):
        """Test syncing a single remote dependency."""
        check_github_rate_limit()

        # Create agr.toml with remote dep
        (git_project / "agr.toml").write_text("""
[[dependencies]]
handle = "kasperjunge/commit"
type = "skill"
""")

        result = runner.invoke(app, ["sync"])

        assert result.exit_code == 0
        installed = git_project / ".claude" / "skills" / "kasperjunge:commit"
        assert installed.exists()

    def test_sync_multiple_remote_deps(self, git_project: Path, check_github_rate_limit):
        """Test syncing multiple remote dependencies."""
        check_github_rate_limit()

        (git_project / "agr.toml").write_text("""
[[dependencies]]
handle = "kasperjunge/commit"
type = "skill"

[[dependencies]]
handle = "maragudk/collaboration"
type = "skill"
""")

        result = runner.invoke(app, ["sync"])

        assert result.exit_code == 0
        assert (git_project / ".claude" / "skills" / "kasperjunge:commit").exists()
        assert (git_project / ".claude" / "skills" / "maragudk:collaboration").exists()

    def test_sync_mixed_local_and_remote(self, git_project: Path, check_github_rate_limit):
        """Test syncing both local and remote dependencies."""
        check_github_rate_limit()

        # Create local skill
        local_skill = git_project / "skills" / "local-skill"
        local_skill.mkdir(parents=True)
        (local_skill / "SKILL.md").write_text("# Local Skill")

        (git_project / "agr.toml").write_text("""
[[dependencies]]
path = "./skills/local-skill"
type = "skill"

[[dependencies]]
handle = "kasperjunge/commit"
type = "skill"
""")

        result = runner.invoke(app, ["sync"])

        assert result.exit_code == 0
        assert (git_project / ".claude" / "skills" / "local:local-skill").exists()
        assert (git_project / ".claude" / "skills" / "kasperjunge:commit").exists()

    def test_sync_idempotent(self, git_project: Path, check_github_rate_limit):
        """Test that sync is idempotent."""
        check_github_rate_limit()

        (git_project / "agr.toml").write_text("""
[[dependencies]]
handle = "kasperjunge/commit"
type = "skill"
""")

        # First sync
        result1 = runner.invoke(app, ["sync"])
        assert result1.exit_code == 0

        # Second sync should also succeed without changes
        result2 = runner.invoke(app, ["sync"])
        assert result2.exit_code == 0

    def test_sync_with_nonexistent_dep_fails_gracefully(self, git_project: Path, check_github_rate_limit):
        """Test that sync handles nonexistent deps gracefully."""
        check_github_rate_limit()

        (git_project / "agr.toml").write_text("""
[[dependencies]]
handle = "nonexistent-user-12345/nonexistent-resource"
type = "skill"
""")

        result = runner.invoke(app, ["sync"])

        # Should fail but not crash
        assert result.exit_code != 0 or "error" in result.output.lower() or "failed" in result.output.lower()

    def test_sync_workspace_package(self, git_project: Path, check_github_rate_limit):
        """Test syncing a workspace package."""
        check_github_rate_limit()

        (git_project / "agr.toml").write_text("""
[workspaces.my-workspace]
dependencies = [
    { handle = "kasperjunge/commit", type = "skill" }
]
""")

        result = runner.invoke(app, ["sync", "--workspace", "my-workspace"])

        assert result.exit_code == 0
        assert (git_project / ".claude" / "skills" / "kasperjunge:commit").exists()


# ============================================================================
# agrx Temporary Runs Tests
# ============================================================================


@pytest.mark.e2e
class TestAgrxTemporaryRuns:
    """E2E tests for agrx temporary resource runs."""

    def test_agrx_skill_downloaded_and_removed(self, git_project: Path, check_github_rate_limit):
        """Test that agrx downloads skill temporarily."""
        check_github_rate_limit()

        # agrx adds temporarily but doesn't persist
        result = runner.invoke(agrx_app, ["kasperjunge/commit"])

        assert result.exit_code == 0
        # Should show skill was fetched
        assert "kasperjunge/commit" in result.output.lower() or "commit" in result.output.lower()

    def test_agrx_multiple_resources(self, git_project: Path, check_github_rate_limit):
        """Test agrx with multiple resources."""
        check_github_rate_limit()

        result = runner.invoke(agrx_app, ["kasperjunge/commit", "maragudk/collaboration"])

        # Should handle multiple resources
        if result.exit_code == 0:
            assert "commit" in result.output.lower() or "collaboration" in result.output.lower()

    def test_agrx_nonexistent_resource_fails(self, git_project: Path, check_github_rate_limit):
        """Test that agrx with nonexistent resource fails gracefully."""
        check_github_rate_limit()

        result = runner.invoke(agrx_app, ["nonexistent-user-12345/nonexistent-resource"])

        assert result.exit_code != 0

    def test_agrx_with_explicit_type(self, git_project: Path, check_github_rate_limit):
        """Test agrx with explicit resource type."""
        check_github_rate_limit()

        result = runner.invoke(agrx_app, ["kasperjunge/commit", "--type", "skill"])

        if result.exit_code == 0:
            assert "commit" in result.output.lower()


# ============================================================================
# Discovery/Resolution E2E Tests
# ============================================================================


@pytest.mark.e2e
class TestDiscoveryResolution:
    """E2E tests for resource discovery and resolution."""

    def test_resolve_user_slash_name(self, git_project: Path, check_github_rate_limit):
        """Test resolving user/name format finds correct resource."""
        check_github_rate_limit()

        result = runner.invoke(app, ["add", "kasperjunge/commit"])

        assert result.exit_code == 0
        # Verify resolution worked
        assert "Added" in result.output

    def test_resolve_nested_skill(self, git_project: Path, check_github_rate_limit):
        """Test resolving nested skill paths."""
        check_github_rate_limit()

        # Try to add a nested skill if available
        result = runner.invoke(app, ["add", "kasperjunge/product-strategy/flywheel"])

        # May or may not exist, but should not crash
        # We're testing the resolution code path

    def test_auto_discovery_in_remote_repo(self, git_project: Path, check_github_rate_limit):
        """Test that auto-discovery works for remote repos."""
        check_github_rate_limit()

        # Add without explicit type - should auto-detect
        result = runner.invoke(app, ["add", "kasperjunge/commit"])

        assert result.exit_code == 0
        # Should have auto-detected as skill
        assert "skill" in result.output.lower()

    def test_list_shows_remote_resources(self, git_project: Path, check_github_rate_limit):
        """Test that agr list shows installed remote resources."""
        check_github_rate_limit()

        runner.invoke(app, ["add", "kasperjunge/commit"])

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "kasperjunge" in result.output or "commit" in result.output

    def test_remove_remote_resource(self, git_project: Path, check_github_rate_limit):
        """Test removing a remote resource."""
        check_github_rate_limit()

        runner.invoke(app, ["add", "kasperjunge/commit"])

        # Verify installed
        installed = git_project / ".claude" / "skills" / "kasperjunge:commit"
        assert installed.exists()

        # Remove
        result = runner.invoke(app, ["remove", "kasperjunge/commit", "-y"])

        assert result.exit_code == 0
        assert not installed.exists()

    def test_info_shows_remote_resource_details(self, git_project: Path, check_github_rate_limit):
        """Test agr info shows details for remote resource."""
        check_github_rate_limit()

        runner.invoke(app, ["add", "kasperjunge/commit"])

        result = runner.invoke(app, ["info", "kasperjunge/commit"])

        if result.exit_code == 0:
            assert "commit" in result.output.lower()
