"""Tests for agr.fetcher module."""

import pytest

from agr.exceptions import SkillNotFoundError
from agr.fetcher import (
    get_installed_skills,
    install_local_skill,
    is_skill_installed,
    uninstall_skill,
)
from agr.skill import SKILL_MARKER


class TestInstallLocalSkill:
    """Tests for install_local_skill function."""

    def test_install_valid_skill(self, tmp_path, skill_fixture):
        """Install a valid local skill."""
        dest_dir = tmp_path / ".claude" / "skills"
        dest_dir.mkdir(parents=True)

        installed_path = install_local_skill(skill_fixture, dest_dir)

        assert installed_path.exists()
        assert (installed_path / SKILL_MARKER).exists()
        assert installed_path.name == f"local:{skill_fixture.name}"

    def test_install_invalid_skill_raises(self, tmp_path):
        """Installing directory without SKILL.md raises."""
        source_dir = tmp_path / "not-a-skill"
        source_dir.mkdir()
        dest_dir = tmp_path / ".claude" / "skills"
        dest_dir.mkdir(parents=True)

        with pytest.raises(SkillNotFoundError, match="not a valid skill"):
            install_local_skill(source_dir, dest_dir)

    def test_install_existing_raises(self, tmp_path, skill_fixture):
        """Installing to existing location raises without overwrite."""
        dest_dir = tmp_path / ".claude" / "skills"
        dest_dir.mkdir(parents=True)

        # Install once
        install_local_skill(skill_fixture, dest_dir)

        # Install again should raise
        with pytest.raises(FileExistsError):
            install_local_skill(skill_fixture, dest_dir)

    def test_install_with_overwrite(self, tmp_path, skill_fixture):
        """Overwrite flag allows reinstalling."""
        dest_dir = tmp_path / ".claude" / "skills"
        dest_dir.mkdir(parents=True)

        # Install twice with overwrite
        install_local_skill(skill_fixture, dest_dir)
        installed_path = install_local_skill(skill_fixture, dest_dir, overwrite=True)

        assert installed_path.exists()


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
        installed_path = install_local_skill(skill_fixture, skills_dir)
        installed_name = installed_path.name

        # Uninstall
        removed = uninstall_skill(installed_name, repo_root)

        assert removed
        assert not installed_path.exists()

    def test_uninstall_nonexistent(self, tmp_path):
        """Uninstalling nonexistent returns False."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()

        removed = uninstall_skill("nonexistent:skill", repo_root)
        assert not removed


class TestGetInstalledSkills:
    """Tests for get_installed_skills function."""

    def test_no_skills_dir(self, tmp_path):
        """Returns empty list when skills dir doesn't exist."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()

        skills = get_installed_skills(repo_root)
        assert skills == []

    def test_with_skills(self, tmp_path, skill_fixture):
        """Returns list of installed skill names."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        skills_dir = repo_root / ".claude" / "skills"
        skills_dir.mkdir(parents=True)

        install_local_skill(skill_fixture, skills_dir)

        skills = get_installed_skills(repo_root)
        assert len(skills) == 1
        assert skills[0] == f"local:{skill_fixture.name}"


class TestIsSkillInstalled:
    """Tests for is_skill_installed function."""

    def test_installed(self, tmp_path, skill_fixture):
        """Returns True for installed skill."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()
        skills_dir = repo_root / ".claude" / "skills"
        skills_dir.mkdir(parents=True)

        installed_path = install_local_skill(skill_fixture, skills_dir)
        installed_name = installed_path.name

        assert is_skill_installed(installed_name, repo_root)

    def test_not_installed(self, tmp_path):
        """Returns False for non-installed skill."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        (repo_root / ".git").mkdir()

        assert not is_skill_installed("nonexistent:skill", repo_root)


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
            assert (repo_dir / "pyproject.toml").exists() or (repo_dir / "agr.toml").exists()

    @pytest.mark.e2e
    def test_download_nonexistent_raises(self):
        """Downloading nonexistent repo raises."""
        from agr.exceptions import RepoNotFoundError
        from agr.fetcher import downloaded_repo

        with pytest.raises(RepoNotFoundError):
            with downloaded_repo("nonexistent-user-12345", "nonexistent-repo-67890"):
                pass
