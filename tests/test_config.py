"""Tests for agr.toml configuration management."""

from pathlib import Path

import pytest

from agr.config import AgrConfig, Dependency, find_config, get_or_create_config
from agr.exceptions import ConfigParseError


class TestDependency:
    """Tests for Dependency dataclass."""

    def test_create_remote_dependency(self):
        """Test creating a remote dependency with handle."""
        dep = Dependency(handle="kasperjunge/commit", type="skill")
        assert dep.handle == "kasperjunge/commit"
        assert dep.path is None
        assert dep.type == "skill"
        assert dep.is_remote
        assert not dep.is_local
        assert dep.identifier == "kasperjunge/commit"

    def test_create_local_dependency(self):
        """Test creating a local dependency with path."""
        dep = Dependency(path="./commands/docs.md", type="command")
        assert dep.path == "./commands/docs.md"
        assert dep.handle is None
        assert dep.type == "command"
        assert dep.is_local
        assert not dep.is_remote
        assert dep.identifier == "./commands/docs.md"

    def test_dependency_requires_handle_or_path(self):
        """Test that dependency must have either handle or path."""
        with pytest.raises(ValueError, match="must have either handle or path"):
            Dependency(type="skill")

    def test_dependency_cannot_have_both(self):
        """Test that dependency cannot have both handle and path."""
        with pytest.raises(ValueError, match="cannot have both handle and path"):
            Dependency(handle="kasperjunge/commit", path="./skills/test", type="skill")


class TestAgrConfig:
    """Tests for AgrConfig class."""

    def test_load_valid_new_format(self, tmp_path: Path):
        """Test loading a valid agr.toml file in new list format."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text('''dependencies = [
    { handle = "kasperjunge/commit", type = "skill" },
    { path = "./commands/docs.md", type = "command" },
]
''')

        config = AgrConfig.load(config_path)

        assert len(config.dependencies) == 2
        assert config.dependencies[0].handle == "kasperjunge/commit"
        assert config.dependencies[0].type == "skill"
        assert config.dependencies[1].path == "./commands/docs.md"
        assert config.dependencies[1].type == "command"

    def test_load_valid_old_format_migrates(self, tmp_path: Path):
        """Test loading old table format auto-migrates."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text('''[dependencies]
"kasperjunge/commit" = {}
"alice/code-review" = { type = "skill" }
''')

        config = AgrConfig.load(config_path)

        assert len(config.dependencies) == 2
        assert config._migrated is True
        # Find by handle
        commit_dep = config.get_by_handle("kasperjunge/commit")
        review_dep = config.get_by_handle("alice/code-review")
        assert commit_dep is not None
        assert commit_dep.type == "skill"  # Default type
        assert review_dep is not None
        assert review_dep.type == "skill"

    def test_load_old_format_with_local_section(self, tmp_path: Path):
        """Test loading old format with [local] section migrates."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text('''[dependencies]
"kasperjunge/commit" = {}

[local]
"my-skill" = { path = "./skills/my-skill", type = "skill" }
''')

        config = AgrConfig.load(config_path)

        assert len(config.dependencies) == 2
        assert config._migrated is True
        local_dep = config.get_by_path("./skills/my-skill")
        assert local_dep is not None
        assert local_dep.type == "skill"

    def test_load_empty_config(self, tmp_path: Path):
        """Test loading an empty agr.toml file."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text("")

        config = AgrConfig.load(config_path)

        assert config.dependencies == []

    def test_load_config_without_dependencies(self, tmp_path: Path):
        """Test loading a config file without dependencies section."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text("[metadata]\nname = 'test'\n")

        config = AgrConfig.load(config_path)

        assert config.dependencies == []

    def test_load_invalid_toml_raises_error(self, tmp_path: Path):
        """Test that invalid TOML raises ConfigParseError."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text("invalid toml [[[")

        with pytest.raises(ConfigParseError):
            AgrConfig.load(config_path)

    def test_load_nonexistent_file(self, tmp_path: Path):
        """Test loading a nonexistent file returns empty config."""
        config_path = tmp_path / "nonexistent.toml"

        config = AgrConfig.load(config_path)

        assert config.dependencies == []

    def test_save_roundtrip(self, tmp_path: Path):
        """Test that saving and loading preserves data."""
        config_path = tmp_path / "agr.toml"

        # Create and save config
        config = AgrConfig()
        config.add_remote("kasperjunge/commit", "skill")
        config.add_local("./commands/docs.md", "command")
        config.save(config_path)

        # Load and verify
        loaded = AgrConfig.load(config_path)
        assert len(loaded.dependencies) == 2
        assert loaded.get_by_handle("kasperjunge/commit") is not None
        assert loaded.get_by_path("./commands/docs.md") is not None

    def test_save_writes_new_format(self, tmp_path: Path):
        """Test that saving always writes new list format."""
        config_path = tmp_path / "agr.toml"

        config = AgrConfig()
        config.add_remote("kasperjunge/commit", "skill")
        config.save(config_path)

        content = config_path.read_text()
        assert "dependencies = [" in content
        assert "handle = " in content


class TestDependencyManagement:
    """Tests for add/remove dependency operations."""

    def test_add_remote_basic(self):
        """Test adding a basic remote dependency."""
        config = AgrConfig()

        config.add_remote("kasperjunge/commit", "skill")

        assert len(config.dependencies) == 1
        dep = config.get_by_handle("kasperjunge/commit")
        assert dep is not None
        assert dep.type == "skill"

    def test_add_local_basic(self):
        """Test adding a basic local dependency."""
        config = AgrConfig()

        config.add_local("./commands/docs.md", "command")

        assert len(config.dependencies) == 1
        dep = config.get_by_path("./commands/docs.md")
        assert dep is not None
        assert dep.type == "command"

    def test_add_dependency_overwrites_existing(self):
        """Test that adding an existing dependency overwrites it."""
        config = AgrConfig()
        config.add_remote("kasperjunge/commit", "skill")

        config.add_remote("kasperjunge/commit", "command")

        assert len(config.dependencies) == 1
        dep = config.get_by_handle("kasperjunge/commit")
        assert dep.type == "command"

    def test_remove_dependency(self):
        """Test removing a dependency by identifier."""
        config = AgrConfig()
        config.add_remote("kasperjunge/commit", "skill")
        config.add_remote("alice/review", "skill")

        removed = config.remove_dependency("kasperjunge/commit")

        assert removed is True
        assert len(config.dependencies) == 1
        assert config.get_by_handle("kasperjunge/commit") is None
        assert config.get_by_handle("alice/review") is not None

    def test_remove_by_handle(self):
        """Test removing a remote dependency by handle."""
        config = AgrConfig()
        config.add_remote("kasperjunge/commit", "skill")

        removed = config.remove_by_handle("kasperjunge/commit")

        assert removed is True
        assert len(config.dependencies) == 0

    def test_remove_by_path(self):
        """Test removing a local dependency by path."""
        config = AgrConfig()
        config.add_local("./commands/docs.md", "command")

        removed = config.remove_by_path("./commands/docs.md")

        assert removed is True
        assert len(config.dependencies) == 0

    def test_remove_nonexistent_dependency(self):
        """Test that removing a nonexistent dependency returns False."""
        config = AgrConfig()

        removed = config.remove_dependency("nonexistent/dep")

        assert removed is False
        assert config.dependencies == []

    def test_get_local_dependencies(self):
        """Test filtering to local dependencies only."""
        config = AgrConfig()
        config.add_remote("kasperjunge/commit", "skill")
        config.add_local("./commands/docs.md", "command")
        config.add_local("./skills/test", "skill")

        local = config.get_local_dependencies()

        assert len(local) == 2
        assert all(d.is_local for d in local)

    def test_get_remote_dependencies(self):
        """Test filtering to remote dependencies only."""
        config = AgrConfig()
        config.add_remote("kasperjunge/commit", "skill")
        config.add_remote("alice/review", "skill")
        config.add_local("./commands/docs.md", "command")

        remote = config.get_remote_dependencies()

        assert len(remote) == 2
        assert all(d.is_remote for d in remote)


class TestFindConfig:
    """Tests for find_config function."""

    def test_find_config_in_current_dir(self, tmp_path: Path, monkeypatch):
        """Test finding config in current directory."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text("dependencies = []\n")
        monkeypatch.chdir(tmp_path)

        # Also create a git directory to mark as git root
        (tmp_path / ".git").mkdir()

        result = find_config()

        assert result == config_path

    def test_find_config_in_parent_dir(self, tmp_path: Path, monkeypatch):
        """Test finding config in parent directory."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text("dependencies = []\n")
        (tmp_path / ".git").mkdir()

        subdir = tmp_path / "src" / "app"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)

        result = find_config()

        assert result == config_path

    def test_find_config_stops_at_git_root(self, tmp_path: Path, monkeypatch):
        """Test that search stops at git root."""
        # Create config outside git root
        outer_config = tmp_path / "agr.toml"
        outer_config.write_text("dependencies = []\n")

        # Create git root without config
        git_root = tmp_path / "project"
        git_root.mkdir()
        (git_root / ".git").mkdir()

        subdir = git_root / "src"
        subdir.mkdir()
        monkeypatch.chdir(subdir)

        result = find_config()

        assert result is None

    def test_find_config_not_found(self, tmp_path: Path, monkeypatch):
        """Test when no config file exists."""
        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)

        result = find_config()

        assert result is None


class TestGetOrCreateConfig:
    """Tests for get_or_create_config function."""

    def test_get_existing_config(self, tmp_path: Path, monkeypatch):
        """Test getting an existing config file."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text('''dependencies = [
    { handle = "kasperjunge/commit", type = "skill" },
]
''')
        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)

        path, config = get_or_create_config()

        assert path == config_path
        assert config.get_by_handle("kasperjunge/commit") is not None

    def test_create_config_when_missing(self, tmp_path: Path, monkeypatch):
        """Test creating a config file when none exists."""
        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)

        path, config = get_or_create_config()

        assert path == tmp_path / "agr.toml"
        assert path.exists()
        assert config.dependencies == []

    def test_get_config_from_parent_dir(self, tmp_path: Path, monkeypatch):
        """Test getting config from parent directory."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text("dependencies = []\n")
        (tmp_path / ".git").mkdir()

        subdir = tmp_path / "src"
        subdir.mkdir()
        monkeypatch.chdir(subdir)

        path, config = get_or_create_config()

        assert path == config_path
