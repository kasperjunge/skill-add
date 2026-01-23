"""Tests for agr.core.orchestrator module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from agr.core import CLAUDE_SPEC
from agr.core.orchestrator import InstallResult, Orchestrator
from agr.core.resource import ResourceType
from agr.handle import ParsedHandle


class TestInstallResult:
    """Tests for InstallResult dataclass."""

    def test_create_result(self, tmp_path):
        """Can create an InstallResult."""
        result = InstallResult(
            resource_name="test:skill",
            installed_path=tmp_path / "test:skill",
            was_overwritten=False,
        )
        assert result.resource_name == "test:skill"
        assert result.installed_path == tmp_path / "test:skill"
        assert result.was_overwritten is False


class TestOrchestrator:
    """Tests for Orchestrator class."""

    @pytest.fixture
    def orchestrator(self):
        """Create an orchestrator with Claude spec."""
        return Orchestrator(tool=CLAUDE_SPEC)

    @pytest.fixture
    def git_repo(self, tmp_path):
        """Create a minimal git repo."""
        (tmp_path / ".git").mkdir()
        return tmp_path

    @pytest.fixture
    def local_skill(self, tmp_path):
        """Create a local skill for testing."""
        skill_dir = tmp_path / "local-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: local-skill
---

# Local Skill
""")
        return skill_dir

    def test_init_default_tool(self):
        """Uses default tool when none specified."""
        orchestrator = Orchestrator()
        assert orchestrator.tool is not None

    def test_init_custom_tool(self):
        """Uses specified tool."""
        orchestrator = Orchestrator(tool=CLAUDE_SPEC)
        assert orchestrator.tool.name == "claude"

    def test_tool_property(self, orchestrator):
        """tool property returns the tool spec."""
        assert orchestrator.tool == CLAUDE_SPEC

    def test_install_local_skill(self, orchestrator, git_repo, local_skill):
        """Installs a local skill."""
        handle = ParsedHandle(
            is_local=True,
            name=local_skill.name,
            local_path=local_skill,
        )

        result = orchestrator.install(handle, git_repo)

        assert result.resource_name == f"local:{local_skill.name}"
        assert result.installed_path.exists()
        assert (result.installed_path / "SKILL.md").exists()

    def test_install_local_skill_with_overwrite(self, orchestrator, git_repo, local_skill):
        """Overwrites existing skill when overwrite=True."""
        handle = ParsedHandle(
            is_local=True,
            name=local_skill.name,
            local_path=local_skill,
        )

        # Install twice
        orchestrator.install(handle, git_repo)
        result = orchestrator.install(handle, git_repo, overwrite=True)

        assert result.was_overwritten
        assert result.installed_path.exists()

    def test_install_temporary(self, orchestrator, git_repo, local_skill):
        """Installs with temporary prefix."""
        handle = ParsedHandle(
            is_local=True,
            name=local_skill.name,
            local_path=local_skill,
        )

        result = orchestrator.install(
            handle,
            git_repo,
            temporary=True,
            temp_prefix="_agrx_",
        )

        assert result.resource_name.startswith("_agrx_")
        assert result.installed_path.exists()

    def test_install_from_string_handle(self, orchestrator, git_repo, local_skill):
        """Accepts string handle."""
        # Use local path syntax
        result = orchestrator.install(
            str(local_skill),
            git_repo,
        )

        assert result.installed_path.exists()

    def test_uninstall_existing(self, orchestrator, git_repo, local_skill):
        """Uninstalls an existing skill."""
        handle = ParsedHandle(
            is_local=True,
            name=local_skill.name,
            local_path=local_skill,
        )

        result = orchestrator.install(handle, git_repo)
        removed = orchestrator.uninstall(result.resource_name, git_repo)

        assert removed is True
        assert not result.installed_path.exists()

    def test_uninstall_nonexistent(self, orchestrator, git_repo):
        """Returns False for nonexistent skill."""
        removed = orchestrator.uninstall("nonexistent:skill", git_repo)
        assert removed is False

    def test_list_installed_empty(self, orchestrator, git_repo):
        """Returns empty list when no skills installed."""
        installed = orchestrator.list_installed(git_repo)
        assert installed == []

    def test_list_installed_with_skills(self, orchestrator, git_repo, local_skill):
        """Lists installed skills."""
        handle = ParsedHandle(
            is_local=True,
            name=local_skill.name,
            local_path=local_skill,
        )

        orchestrator.install(handle, git_repo)
        installed = orchestrator.list_installed(git_repo)

        assert len(installed) == 1
        assert f"local:{local_skill.name}" in installed

    def test_is_installed_true(self, orchestrator, git_repo, local_skill):
        """Returns True for installed skill."""
        handle = ParsedHandle(
            is_local=True,
            name=local_skill.name,
            local_path=local_skill,
        )

        result = orchestrator.install(handle, git_repo)
        assert orchestrator.is_installed(result.resource_name, git_repo)

    def test_is_installed_false(self, orchestrator, git_repo):
        """Returns False for non-installed skill."""
        assert not orchestrator.is_installed("nonexistent:skill", git_repo)


class TestOrchestratorRemote:
    """Tests for Orchestrator with remote handles (mocked)."""

    @pytest.fixture
    def orchestrator(self):
        """Create an orchestrator with Claude spec."""
        return Orchestrator(tool=CLAUDE_SPEC)

    @pytest.fixture
    def git_repo(self, tmp_path):
        """Create a minimal git repo."""
        (tmp_path / ".git").mkdir()
        return tmp_path

    @pytest.fixture
    def mock_repo(self, tmp_path):
        """Create a mock downloaded repo structure."""
        repo_dir = tmp_path / "mock-repo"
        repo_dir.mkdir()
        skill_dir = repo_dir / "resources" / "skills" / "commit"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("""---
name: commit
---

# Commit Skill
""")
        return repo_dir

    def test_install_remote_skill(self, orchestrator, git_repo, mock_repo):
        """Installs a remote skill (mocked download)."""
        handle = ParsedHandle(
            username="testuser",
            name="commit",
        )

        # Mock the downloaded_repo context manager at the fetcher module level
        from contextlib import contextmanager

        @contextmanager
        def mock_downloaded_repo(username, repo_name):
            yield mock_repo

        with patch("agr.fetcher.downloaded_repo", mock_downloaded_repo):
            result = orchestrator.install(handle, git_repo)

        assert result.resource_name == "testuser:commit"
        assert result.installed_path.exists()
        assert (result.installed_path / "SKILL.md").exists()

    def test_install_remote_temporary(self, orchestrator, git_repo, mock_repo):
        """Installs a remote skill temporarily (mocked)."""
        handle = ParsedHandle(
            username="testuser",
            name="commit",
        )

        from contextlib import contextmanager

        @contextmanager
        def mock_downloaded_repo(username, repo_name):
            yield mock_repo

        with patch("agr.fetcher.downloaded_repo", mock_downloaded_repo):
            result = orchestrator.install(
                handle,
                git_repo,
                temporary=True,
                temp_prefix="_test_",
            )

        assert result.resource_name == "_test_commit"
        assert result.installed_path.exists()


class TestOrchestratorGlobal:
    """Tests for Orchestrator with global install/uninstall."""

    @pytest.fixture
    def mock_home(self, tmp_path):
        """Create a mock home directory."""
        home = tmp_path / "home"
        home.mkdir()
        return home

    @pytest.fixture
    def test_tool_spec(self, mock_home):
        """Create a tool spec with test global dir."""
        from agr.core.resource import ResourceType
        from agr.core.tool import ToolResourceConfig, ToolSpec
        return ToolSpec(
            name="test-claude",
            config_dir=".claude",
            global_config_dir=str(mock_home / ".claude"),
            resource_configs={
                ResourceType.SKILL: ToolResourceConfig(subdir="skills"),
            },
            detection_markers=(".claude",),
        )

    @pytest.fixture
    def orchestrator(self, test_tool_spec):
        """Create an orchestrator with test tool spec."""
        return Orchestrator(tool=test_tool_spec)

    @pytest.fixture
    def local_skill(self, tmp_path):
        """Create a local skill for testing."""
        skill_dir = tmp_path / "global-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: global-skill
---

# Global Skill
""")
        return skill_dir

    def test_install_global(self, orchestrator, tmp_path, local_skill, mock_home):
        """Installs to global directory."""
        handle = ParsedHandle(
            is_local=True,
            name=local_skill.name,
            local_path=local_skill,
        )

        result = orchestrator.install(handle, tmp_path, global_install=True)

        expected_dir = mock_home / ".claude" / "skills"
        assert result.installed_path.parent == expected_dir

    def test_list_installed_global(self, orchestrator, tmp_path, local_skill, mock_home):
        """Lists globally installed skills."""
        handle = ParsedHandle(
            is_local=True,
            name=local_skill.name,
            local_path=local_skill,
        )

        orchestrator.install(handle, tmp_path, global_install=True)
        installed = orchestrator.list_installed(tmp_path, global_list=True)

        assert len(installed) == 1

    def test_uninstall_global(self, orchestrator, tmp_path, local_skill, mock_home):
        """Uninstalls from global directory."""
        handle = ParsedHandle(
            is_local=True,
            name=local_skill.name,
            local_path=local_skill,
        )

        result = orchestrator.install(handle, tmp_path, global_install=True)
        removed = orchestrator.uninstall(result.resource_name, tmp_path, global_uninstall=True)

        assert removed is True
        assert not result.installed_path.exists()
