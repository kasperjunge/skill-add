"""Tests for workspace package functionality."""

from pathlib import Path

import pytest

from agr.config import AgrConfig, Dependency, PackageConfig


class TestPackageConfig:
    """Tests for PackageConfig dataclass."""

    def test_create_package_config(self):
        """Test creating a PackageConfig."""
        pkg = PackageConfig(path="./packages/myworkspace")
        assert pkg.path == "./packages/myworkspace"
        assert pkg.dependencies == []

    def test_package_config_with_dependencies(self):
        """Test creating a PackageConfig with dependencies."""
        deps = [
            Dependency(path="./skills/tool-use", type="skill"),
            Dependency(handle="kasperjunge/commit", type="skill"),
        ]
        pkg = PackageConfig(path="./packages/toolkit", dependencies=deps)
        assert len(pkg.dependencies) == 2


class TestWorkspaceFlag:
    """Tests for -w/--workspace flag functionality."""

    def test_add_to_workspace_creates_package_section(self):
        """Test that add_to_workspace creates the packages section."""
        config = AgrConfig()
        dep = Dependency(path="./skills/tool-use", type="skill")

        config.add_to_workspace("myworkspace", dep)

        assert "myworkspace" in config.packages
        assert config.packages["myworkspace"].path == "./packages/myworkspace"
        assert len(config.packages["myworkspace"].dependencies) == 1

    def test_add_to_workspace_multiple_deps(self):
        """Test adding multiple dependencies to same workspace."""
        config = AgrConfig()
        dep1 = Dependency(path="./skills/tool-use", type="skill")
        dep2 = Dependency(path="./commands/docs.md", type="command")

        config.add_to_workspace("myworkspace", dep1)
        config.add_to_workspace("myworkspace", dep2)

        assert len(config.packages["myworkspace"].dependencies) == 2

    def test_add_to_workspace_overwrites_duplicate(self):
        """Test that adding same dependency to workspace overwrites."""
        config = AgrConfig()
        dep1 = Dependency(path="./skills/tool-use", type="skill")
        dep2 = Dependency(path="./skills/tool-use", type="command")  # Same path, different type

        config.add_to_workspace("myworkspace", dep1)
        config.add_to_workspace("myworkspace", dep2)

        assert len(config.packages["myworkspace"].dependencies) == 1
        assert config.packages["myworkspace"].dependencies[0].type == "command"

    def test_add_to_multiple_workspaces(self):
        """Test adding to different workspaces."""
        config = AgrConfig()
        dep1 = Dependency(path="./skills/tool-use", type="skill")
        dep2 = Dependency(path="./commands/docs.md", type="command")

        config.add_to_workspace("workspace1", dep1)
        config.add_to_workspace("workspace2", dep2)

        assert "workspace1" in config.packages
        assert "workspace2" in config.packages
        assert len(config.packages["workspace1"].dependencies) == 1
        assert len(config.packages["workspace2"].dependencies) == 1


class TestWorkspaceSaveLoad:
    """Tests for saving and loading workspaces."""

    def test_save_load_with_packages(self, tmp_path: Path):
        """Test that saving and loading preserves packages."""
        config_path = tmp_path / "agr.toml"

        # Create and save config with workspace
        config = AgrConfig()
        config.add_remote("kasperjunge/commit", "skill")
        config.add_to_workspace(
            "toolkit",
            Dependency(path="./skills/tool-use", type="skill"),
        )
        config.save(config_path)

        # Load and verify
        loaded = AgrConfig.load(config_path)
        assert len(loaded.dependencies) == 1
        assert "toolkit" in loaded.packages
        assert len(loaded.packages["toolkit"].dependencies) == 1
        assert loaded.packages["toolkit"].dependencies[0].path == "./skills/tool-use"

    def test_workspace_dependencies_roundtrip(self, tmp_path: Path):
        """Test that workspace dependencies survive save/load roundtrip."""
        config_path = tmp_path / "agr.toml"

        config = AgrConfig()
        config.add_to_workspace(
            "myworkspace",
            Dependency(path="./skills/skill1", type="skill"),
        )
        config.add_to_workspace(
            "myworkspace",
            Dependency(handle="kasperjunge/commit", type="skill"),
        )
        config.save(config_path)

        loaded = AgrConfig.load(config_path)

        assert len(loaded.packages["myworkspace"].dependencies) == 2
        # Check that both local and remote deps are preserved
        paths = [d.path for d in loaded.packages["myworkspace"].dependencies]
        handles = [d.handle for d in loaded.packages["myworkspace"].dependencies]
        assert "./skills/skill1" in paths
        assert "kasperjunge/commit" in handles

    def test_save_creates_packages_table(self, tmp_path: Path):
        """Test that saving writes [packages] table correctly."""
        config_path = tmp_path / "agr.toml"

        config = AgrConfig()
        config.add_to_workspace(
            "myworkspace",
            Dependency(path="./skills/test", type="skill"),
        )
        config.save(config_path)

        content = config_path.read_text()
        assert "[packages]" in content or "[packages.myworkspace]" in content
        assert "myworkspace" in content
        assert "path = " in content

    def test_load_empty_packages_section(self, tmp_path: Path):
        """Test loading config with empty packages section."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text('''dependencies = []

[packages]
''')

        config = AgrConfig.load(config_path)

        assert config.packages == {}

    def test_load_packages_with_dependencies(self, tmp_path: Path):
        """Test loading config with packages containing dependencies."""
        config_path = tmp_path / "agr.toml"
        config_path.write_text('''dependencies = []

[packages.toolkit]
path = "./packages/toolkit"
dependencies = [
    { path = "./skills/skill1", type = "skill" },
    { handle = "user/skill2", type = "skill" },
]
''')

        config = AgrConfig.load(config_path)

        assert "toolkit" in config.packages
        assert config.packages["toolkit"].path == "./packages/toolkit"
        assert len(config.packages["toolkit"].dependencies) == 2
