"""Tests for agr.fetcher module."""

import pytest
import respx
from httpx import Response

from agr.exceptions import (
    AgrError,
    AuthenticationError,
    RepoNotFoundError,
    SkillNotFoundError,
)
from agr.fetcher import (
    _cleanup_empty_parents,
    _get_github_token,
    downloaded_repo,
    fetch_and_install_to_tools,
    get_installed_skills,
    install_local_skill,
    is_skill_installed,
    uninstall_skill,
)
from agr.handle import ParsedHandle
from agr.skill import SKILL_MARKER
from agr.tool import CLAUDE, CURSOR


class TestGitHubAuthentication:
    """Tests for GitHub token authentication."""

    def test_get_github_token_returns_value(self, monkeypatch):
        """Token is returned when GITHUB_TOKEN is set."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test123")
        monkeypatch.delenv("GH_TOKEN", raising=False)
        assert _get_github_token() == "ghp_test123"

    def test_get_github_token_returns_none_when_unset(self, monkeypatch):
        """None returned when no token env vars are set."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)
        assert _get_github_token() is None

    def test_get_github_token_empty_string_is_none(self, monkeypatch):
        """Empty string treated as unset."""
        monkeypatch.setenv("GITHUB_TOKEN", "")
        monkeypatch.delenv("GH_TOKEN", raising=False)
        assert _get_github_token() is None

    def test_get_github_token_whitespace_is_none(self, monkeypatch):
        """Whitespace-only treated as unset."""
        monkeypatch.setenv("GITHUB_TOKEN", "   ")
        monkeypatch.delenv("GH_TOKEN", raising=False)
        assert _get_github_token() is None

    def test_get_github_token_prefers_github_token(self, monkeypatch):
        """GITHUB_TOKEN takes precedence over GH_TOKEN."""
        monkeypatch.setenv("GITHUB_TOKEN", "primary")
        monkeypatch.setenv("GH_TOKEN", "fallback")
        assert _get_github_token() == "primary"

    def test_get_github_token_falls_back_to_gh_token(self, monkeypatch):
        """GH_TOKEN used when GITHUB_TOKEN is not set."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setenv("GH_TOKEN", "fallback")
        assert _get_github_token() == "fallback"

    @respx.mock
    def test_token_sent_in_authorization_header(self, monkeypatch):
        """Token is included in Authorization header when set."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        monkeypatch.delenv("GH_TOKEN", raising=False)

        route = respx.get(
            "https://github.com/user/repo/archive/refs/heads/main.tar.gz"
        ).mock(return_value=Response(404))

        with pytest.raises(RepoNotFoundError):
            with downloaded_repo("user", "repo"):
                pass

        assert route.called
        assert route.calls[0].request.headers["Authorization"] == "token test_token"

    @respx.mock
    def test_no_auth_header_when_token_unset(self, monkeypatch):
        """No Authorization header when token is not set."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)

        route = respx.get(
            "https://github.com/user/repo/archive/refs/heads/main.tar.gz"
        ).mock(return_value=Response(404))

        with pytest.raises(RepoNotFoundError):
            with downloaded_repo("user", "repo"):
                pass

        assert route.called
        assert "Authorization" not in route.calls[0].request.headers

    @respx.mock
    def test_401_without_token_suggests_setting_token(self, monkeypatch):
        """401 without token suggests setting GITHUB_TOKEN."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)

        respx.get("https://github.com/user/repo/archive/refs/heads/main.tar.gz").mock(
            return_value=Response(401)
        )

        with pytest.raises(AuthenticationError, match="Set GITHUB_TOKEN"):
            with downloaded_repo("user", "repo"):
                pass

    @respx.mock
    def test_401_with_token_suggests_checking_token(self, monkeypatch):
        """401 with token suggests checking validity."""
        monkeypatch.setenv("GITHUB_TOKEN", "bad_token")
        monkeypatch.delenv("GH_TOKEN", raising=False)

        respx.get("https://github.com/user/repo/archive/refs/heads/main.tar.gz").mock(
            return_value=Response(401)
        )

        with pytest.raises(AuthenticationError, match="is valid"):
            with downloaded_repo("user", "repo"):
                pass

    @respx.mock
    def test_403_with_token_raises_scope_error(self, monkeypatch):
        """403 with token suggests checking scope."""
        monkeypatch.setenv("GITHUB_TOKEN", "token_without_scope")
        monkeypatch.delenv("GH_TOKEN", raising=False)

        respx.get("https://github.com/user/repo/archive/refs/heads/main.tar.gz").mock(
            return_value=Response(403)
        )

        with pytest.raises(AuthenticationError, match="repo.*scope"):
            with downloaded_repo("user", "repo"):
                pass

    @respx.mock
    def test_403_without_token_suggests_setting_token(self, monkeypatch):
        """403 without token suggests setting GITHUB_TOKEN."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)

        respx.get("https://github.com/user/repo/archive/refs/heads/main.tar.gz").mock(
            return_value=Response(403)
        )

        with pytest.raises(AuthenticationError, match="Set GITHUB_TOKEN"):
            with downloaded_repo("user", "repo"):
                pass

    @respx.mock
    def test_429_raises_rate_limit_error(self, monkeypatch):
        """429 response raises AgrError with rate limit message."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)

        respx.get("https://github.com/user/repo/archive/refs/heads/main.tar.gz").mock(
            return_value=Response(429)
        )

        with pytest.raises(AgrError, match="rate limit"):
            with downloaded_repo("user", "repo"):
                pass

    @respx.mock
    def test_error_message_does_not_contain_token(self, monkeypatch):
        """Error messages must not contain the token value."""
        secret_token = "ghp_SUPERSECRET123456"
        monkeypatch.setenv("GITHUB_TOKEN", secret_token)
        monkeypatch.delenv("GH_TOKEN", raising=False)

        respx.get("https://github.com/user/repo/archive/refs/heads/main.tar.gz").mock(
            return_value=Response(500)
        )

        with pytest.raises(AgrError) as exc_info:
            with downloaded_repo("user", "repo"):
                pass

        assert secret_token not in str(exc_info.value)
        # Verify exception chaining is suppressed (security)
        assert exc_info.value.__cause__ is None

    def test_get_github_token_strips_whitespace(self, monkeypatch):
        """Token with surrounding whitespace is stripped."""
        monkeypatch.setenv("GITHUB_TOKEN", "  ghp_test123  ")
        monkeypatch.delenv("GH_TOKEN", raising=False)
        assert _get_github_token() == "ghp_test123"

    def test_get_github_token_github_whitespace_falls_back_to_gh(self, monkeypatch):
        """Whitespace GITHUB_TOKEN falls back to valid GH_TOKEN."""
        monkeypatch.setenv("GITHUB_TOKEN", "   ")
        monkeypatch.setenv("GH_TOKEN", "fallback_token")
        assert _get_github_token() == "fallback_token"

    def test_get_github_token_both_whitespace_returns_none(self, monkeypatch):
        """Both tokens whitespace-only returns None."""
        monkeypatch.setenv("GITHUB_TOKEN", "   ")
        monkeypatch.setenv("GH_TOKEN", "   ")
        assert _get_github_token() is None

    @respx.mock
    def test_connect_error_raises_agr_error(self, monkeypatch):
        """Connection errors wrapped in AgrError."""
        import httpx

        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)

        respx.get("https://github.com/user/repo/archive/refs/heads/main.tar.gz").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with pytest.raises(AgrError, match="Network error: ConnectError"):
            with downloaded_repo("user", "repo"):
                pass

    @respx.mock
    def test_timeout_error_raises_agr_error(self, monkeypatch):
        """Timeout errors wrapped in AgrError."""
        import httpx

        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)

        respx.get("https://github.com/user/repo/archive/refs/heads/main.tar.gz").mock(
            side_effect=httpx.ReadTimeout("Read timed out")
        )

        with pytest.raises(AgrError, match="Network error: ReadTimeout"):
            with downloaded_repo("user", "repo"):
                pass

    @respx.mock
    def test_500_raises_agr_error_with_status_code(self, monkeypatch):
        """500 response raises AgrError with status code in message."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)

        respx.get("https://github.com/user/repo/archive/refs/heads/main.tar.gz").mock(
            return_value=Response(500)
        )

        with pytest.raises(AgrError, match="HTTP 500"):
            with downloaded_repo("user", "repo"):
                pass

    @respx.mock
    def test_502_raises_agr_error_with_status_code(self, monkeypatch):
        """502 response raises AgrError with status code in message."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GH_TOKEN", raising=False)

        respx.get("https://github.com/user/repo/archive/refs/heads/main.tar.gz").mock(
            return_value=Response(502)
        )

        with pytest.raises(AgrError, match="HTTP 502"):
            with downloaded_repo("user", "repo"):
                pass


class TestInstallLocalSkill:
    """Tests for install_local_skill function."""

    def test_install_valid_skill(self, tmp_path, skill_fixture):
        """Install a valid local skill."""
        dest_dir = tmp_path / ".claude" / "skills"
        dest_dir.mkdir(parents=True)

        installed_path = install_local_skill(skill_fixture, dest_dir, CLAUDE)

        assert installed_path.exists()
        assert (installed_path / SKILL_MARKER).exists()
        assert installed_path.name == f"local--{skill_fixture.name}"

    def test_install_invalid_skill_raises(self, tmp_path):
        """Installing directory without SKILL.md raises."""
        source_dir = tmp_path / "not-a-skill"
        source_dir.mkdir()
        dest_dir = tmp_path / ".claude" / "skills"
        dest_dir.mkdir(parents=True)

        with pytest.raises(SkillNotFoundError, match="not a valid skill"):
            install_local_skill(source_dir, dest_dir, CLAUDE)

    def test_install_existing_raises(self, tmp_path, skill_fixture):
        """Installing to existing location raises without overwrite."""
        dest_dir = tmp_path / ".claude" / "skills"
        dest_dir.mkdir(parents=True)

        # Install once
        install_local_skill(skill_fixture, dest_dir, CLAUDE)

        # Install again should raise
        with pytest.raises(FileExistsError):
            install_local_skill(skill_fixture, dest_dir, CLAUDE)

    def test_install_with_overwrite(self, tmp_path, skill_fixture):
        """Overwrite flag allows reinstalling."""
        dest_dir = tmp_path / ".claude" / "skills"
        dest_dir.mkdir(parents=True)

        # Install twice with overwrite
        install_local_skill(skill_fixture, dest_dir, CLAUDE)
        installed_path = install_local_skill(
            skill_fixture, dest_dir, CLAUDE, overwrite=True
        )

        assert installed_path.exists()

    def test_install_rejects_separator_in_name(self, tmp_path):
        """Installing skill with reserved separator in name raises."""
        from agr.skill import SKILL_MARKER

        # Create a skill with -- in its name
        bad_skill = tmp_path / "my--bad--skill"
        bad_skill.mkdir()
        (bad_skill / SKILL_MARKER).write_text("# Bad Skill")

        dest_dir = tmp_path / ".claude" / "skills"
        dest_dir.mkdir(parents=True)

        with pytest.raises(AgrError, match="contains reserved sequence"):
            install_local_skill(bad_skill, dest_dir, CLAUDE)


class TestUninstallSkill:
    """Tests for uninstall_skill function."""

    def test_uninstall_existing(self, tmp_path, skill_fixture):
        """Uninstall an existing skill."""
        # Set up repo structure
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        skills_dir = repo_root / ".claude" / "skills"
        skills_dir.mkdir(parents=True)

        # Install skill
        installed_path = install_local_skill(skill_fixture, skills_dir, CLAUDE)

        # Create handle for uninstall
        handle = ParsedHandle(
            is_local=True, name=skill_fixture.name, local_path=skill_fixture
        )

        # Uninstall
        removed = uninstall_skill(handle, repo_root, CLAUDE)

        assert removed
        assert not installed_path.exists()

    def test_uninstall_nonexistent(self, tmp_path):
        """Uninstalling nonexistent returns False."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()

        handle = ParsedHandle(is_local=True, name="nonexistent-skill")
        removed = uninstall_skill(handle, repo_root, CLAUDE)
        assert not removed


class TestGetInstalledSkills:
    """Tests for get_installed_skills function."""

    def test_no_skills_dir(self, tmp_path):
        """Returns empty list when skills dir doesn't exist."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()

        skills = get_installed_skills(repo_root, CLAUDE)
        assert skills == []

    def test_with_skills(self, tmp_path, skill_fixture):
        """Returns list of installed skill names."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        skills_dir = repo_root / ".claude" / "skills"
        skills_dir.mkdir(parents=True)

        install_local_skill(skill_fixture, skills_dir, CLAUDE)

        skills = get_installed_skills(repo_root, CLAUDE)
        assert len(skills) == 1
        assert skills[0] == f"local--{skill_fixture.name}"


class TestIsSkillInstalled:
    """Tests for is_skill_installed function."""

    def test_installed(self, tmp_path, skill_fixture):
        """Returns True for installed skill."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        skills_dir = repo_root / ".claude" / "skills"
        skills_dir.mkdir(parents=True)

        install_local_skill(skill_fixture, skills_dir, CLAUDE)

        # Create handle for checking
        handle = ParsedHandle(
            is_local=True, name=skill_fixture.name, local_path=skill_fixture
        )
        assert is_skill_installed(handle, repo_root, CLAUDE)

    def test_not_installed(self, tmp_path):
        """Returns False for non-installed skill."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()

        handle = ParsedHandle(is_local=True, name="nonexistent-skill")
        assert not is_skill_installed(handle, repo_root, CLAUDE)


class TestDownloadedRepo:
    """Tests for downloaded_repo context manager.

    These are E2E tests that require network access.
    """

    @pytest.mark.e2e
    def test_download_existing_repo(self):
        """Download a real repository."""
        from agr.fetcher import downloaded_repo

        with downloaded_repo("kasperjunge", "agent-resources") as repo_dir:
            assert repo_dir.exists()
            # Should have agr.toml or pyproject.toml
            assert (repo_dir / "pyproject.toml").exists() or (
                repo_dir / "agr.toml"
            ).exists()

    @pytest.mark.e2e
    def test_download_nonexistent_raises(self):
        """Downloading nonexistent repo raises."""
        from agr.exceptions import RepoNotFoundError
        from agr.fetcher import downloaded_repo

        with pytest.raises(RepoNotFoundError):
            with downloaded_repo("nonexistent-user-12345", "nonexistent-repo-67890"):
                pass


class TestCleanupEmptyParents:
    """Tests for _cleanup_empty_parents function."""

    def test_stops_at_boundary(self, tmp_path):
        """Doesn't delete beyond stop_at."""
        stop_at = tmp_path / "skills"
        stop_at.mkdir()
        nested = stop_at / "a" / "b" / "c"
        nested.mkdir(parents=True)

        # Clean up nested empty dirs
        _cleanup_empty_parents(nested, stop_at)

        # All empty dirs within stop_at should be removed
        assert not (stop_at / "a").exists()
        # But stop_at itself should remain
        assert stop_at.exists()

    def test_handles_non_empty_dir(self, tmp_path):
        """Stops at non-empty directories."""
        stop_at = tmp_path / "skills"
        stop_at.mkdir()
        nested = stop_at / "a" / "b"
        nested.mkdir(parents=True)
        # Put a file in "a"
        (stop_at / "a" / "file.txt").write_text("content")

        _cleanup_empty_parents(nested, stop_at)

        # "b" should be removed but "a" should remain (has file)
        assert not (stop_at / "a" / "b").exists()
        assert (stop_at / "a").exists()
        assert (stop_at / "a" / "file.txt").exists()

    def test_handles_symlinks(self, tmp_path):
        """Resolves symlinks before comparison."""
        stop_at = tmp_path / "skills"
        stop_at.mkdir()
        nested = stop_at / "a" / "b"
        nested.mkdir(parents=True)

        # Create a symlink to the skills dir
        symlink = tmp_path / "skills_link"
        symlink.symlink_to(stop_at)

        # Use symlink path
        nested_via_link = symlink / "a" / "b"

        _cleanup_empty_parents(nested_via_link, symlink)

        # Should still clean up properly
        assert not (stop_at / "a").exists()
        assert stop_at.exists()


class TestFetchAndInstallToTools:
    """Tests for fetch_and_install_to_tools function."""

    def test_local_skill_to_multiple_tools(self, tmp_path, skill_fixture):
        """Local skill installs to multiple tools."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()

        handle = ParsedHandle(
            is_local=True, name=skill_fixture.name, local_path=skill_fixture
        )

        results = fetch_and_install_to_tools(
            handle, repo_root, [CLAUDE, CURSOR], overwrite=False
        )

        assert "claude" in results
        assert "cursor" in results
        assert results["claude"].exists()
        assert results["cursor"].exists()
        # Claude uses flat naming
        assert "--" in results["claude"].name
        # Cursor uses nested directories
        assert results["cursor"].parent.name == "local"

    def test_rollback_on_partial_failure(self, tmp_path, skill_fixture):
        """If second tool fails, first tool installation is rolled back."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()

        # Pre-install to cursor so it will fail without overwrite
        cursor_skills = repo_root / ".cursor" / "skills" / "local"
        cursor_skills.mkdir(parents=True)
        (cursor_skills / skill_fixture.name).mkdir()
        (cursor_skills / skill_fixture.name / "SKILL.md").write_text("# existing")

        handle = ParsedHandle(
            is_local=True, name=skill_fixture.name, local_path=skill_fixture
        )

        # This should fail on cursor (file exists) and rollback claude
        with pytest.raises(FileExistsError):
            fetch_and_install_to_tools(
                handle, repo_root, [CLAUDE, CURSOR], overwrite=False
            )

        # Claude installation should be rolled back
        claude_path = repo_root / ".claude" / "skills" / f"local--{skill_fixture.name}"
        assert not claude_path.exists()

    def test_empty_tools_list_raises(self, tmp_path, skill_fixture):
        """Empty tools list raises ValueError."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()

        handle = ParsedHandle(
            is_local=True, name=skill_fixture.name, local_path=skill_fixture
        )

        with pytest.raises(ValueError, match="No tools provided"):
            fetch_and_install_to_tools(handle, repo_root, [], overwrite=False)
