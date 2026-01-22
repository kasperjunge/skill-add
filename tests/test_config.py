"""Tests for agr.config module."""

import pytest

from agr.config import (
    AgrConfig,
    Dependency,
    find_config,
    find_repo_root,
    get_or_create_config,
)
from agr.exceptions import ConfigError


class TestDependency:
    """Tests for Dependency dataclass."""

    def test_remote_dependency(self):
        """Create a remote dependency."""
        dep = Dependency(type="skill", handle="kasperjunge/commit")
        assert dep.is_remote
        assert not dep.is_local
        assert dep.identifier == "kasperjunge/commit"

    def test_local_dependency(self):
        """Create a local dependency."""
        dep = Dependency(type="skill", path="./my-skill")
        assert dep.is_local
        assert not dep.is_remote
        assert dep.identifier == "./my-skill"

    def test_both_handle_and_path_raises(self):
        """Cannot have both handle and path."""
        with pytest.raises(ValueError, match="cannot have both"):
            Dependency(type="skill", handle="user/skill", path="./local")

    def test_neither_handle_nor_path_raises(self):
        """Must have either handle or path."""
        with pytest.raises(ValueError, match="must have either"):
            Dependency(type="skill")


class TestAgrConfig:
    """Tests for AgrConfig class."""

    def test_load_nonexistent(self, tmp_path):
        """Loading nonexistent file returns empty config."""
        config = AgrConfig.load(tmp_path / "agr.toml")
        assert config.dependencies == []

    def test_load_empty(self, tmp_path):
        """Loading empty file returns empty config."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text("dependencies = []")
        config = AgrConfig.load(config_path)
        assert config.dependencies == []

    def test_load_with_dependencies(self, tmp_path):
        """Load config with dependencies."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text("""
dependencies = [
    { handle = "kasperjunge/commit", type = "skill" },
    { path = "./my-skill", type = "skill" },
]
""")
        config = AgrConfig.load(config_path)
        assert len(config.dependencies) == 2
        assert config.dependencies[0].handle == "kasperjunge/commit"
        assert config.dependencies[1].path == "./my-skill"

    def test_load_invalid_toml_raises(self, tmp_path):
        """Loading invalid TOML raises ConfigError."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text("invalid toml [")
        with pytest.raises(ConfigError):
            AgrConfig.load(config_path)

    def test_save(self, tmp_path):
        """Save config to file."""
        config = AgrConfig()
        config.add_dependency(Dependency(type="skill", handle="kasperjunge/commit"))
        config_path = tmp_path / "agr.toml"
        config.save(config_path)

        # Reload and verify
        loaded = AgrConfig.load(config_path)
        assert len(loaded.dependencies) == 1
        assert loaded.dependencies[0].handle == "kasperjunge/commit"

    def test_add_dependency(self):
        """Add a dependency."""
        config = AgrConfig()
        config.add_dependency(Dependency(type="skill", handle="user/skill"))
        assert len(config.dependencies) == 1

    def test_add_dependency_replaces_existing(self):
        """Adding duplicate identifier replaces existing."""
        config = AgrConfig()
        config.add_dependency(Dependency(type="skill", handle="user/skill"))
        config.add_dependency(Dependency(type="skill", handle="user/skill"))
        assert len(config.dependencies) == 1

    def test_remove_dependency(self):
        """Remove a dependency."""
        config = AgrConfig()
        config.add_dependency(Dependency(type="skill", handle="user/skill"))
        removed = config.remove_dependency("user/skill")
        assert removed
        assert len(config.dependencies) == 0

    def test_remove_nonexistent(self):
        """Removing nonexistent returns False."""
        config = AgrConfig()
        removed = config.remove_dependency("user/skill")
        assert not removed

    def test_get_by_identifier(self):
        """Find dependency by identifier."""
        config = AgrConfig()
        config.add_dependency(Dependency(type="skill", handle="user/skill"))
        dep = config.get_by_identifier("user/skill")
        assert dep is not None
        assert dep.handle == "user/skill"

    def test_get_by_identifier_not_found(self):
        """Returns None for nonexistent identifier."""
        config = AgrConfig()
        dep = config.get_by_identifier("user/skill")
        assert dep is None


class TestFindConfig:
    """Tests for find_config function."""

    def test_find_in_current_dir(self, tmp_path, monkeypatch):
        """Find config in current directory."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()
        config_path = tmp_path / "agr.toml"
        config_path.write_text("dependencies = []")

        found = find_config()
        assert found == config_path

    def test_find_in_parent_dir(self, tmp_path, monkeypatch):
        """Find config in parent directory."""
        (tmp_path / ".git").mkdir()
        config_path = tmp_path / "agr.toml"
        config_path.write_text("dependencies = []")

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        monkeypatch.chdir(subdir)

        found = find_config()
        assert found == config_path

    def test_not_found_at_git_root(self, tmp_path, monkeypatch):
        """Returns None when not found at git root."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        found = find_config()
        assert found is None


class TestFindRepoRoot:
    """Tests for find_repo_root function."""

    def test_find_repo_root(self, tmp_path, monkeypatch):
        """Find git repository root."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        root = find_repo_root()
        assert root == tmp_path

    def test_find_from_subdir(self, tmp_path, monkeypatch):
        """Find repo root from subdirectory."""
        (tmp_path / ".git").mkdir()
        subdir = tmp_path / "a" / "b" / "c"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)

        root = find_repo_root()
        assert root == tmp_path

    def test_not_in_repo(self, tmp_path, monkeypatch):
        """Returns None when not in a git repo."""
        monkeypatch.chdir(tmp_path)

        root = find_repo_root()
        assert root is None


class TestGetOrCreateConfig:
    """Tests for get_or_create_config function."""

    def test_creates_new(self, tmp_path, monkeypatch):
        """Creates new config if none exists."""
        monkeypatch.chdir(tmp_path)

        path, config = get_or_create_config()
        assert path == tmp_path / "agr.toml"
        assert path.exists()
        assert config.dependencies == []

    def test_returns_existing(self, tmp_path, monkeypatch):
        """Returns existing config."""
        monkeypatch.chdir(tmp_path)
        config_path = tmp_path / "agr.toml"
        config_path.write_text("""
dependencies = [
    { handle = "user/skill", type = "skill" },
]
""")

        path, config = get_or_create_config()
        assert path == config_path
        assert len(config.dependencies) == 1
