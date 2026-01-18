"""Tests for local dependencies in unified config format.

Tests the migration from old [local] section to new unified dependencies array,
and verifies local dependency functionality.
"""

from pathlib import Path

import pytest

from agr.config import AgrConfig, Dependency, LocalResourceSpec


class TestLocalResourceSpec:
    """Tests for legacy LocalResourceSpec dataclass."""

    def test_creates_local_resource_spec(self):
        """Test creating a LocalResourceSpec (legacy dataclass)."""
        spec = LocalResourceSpec(
            path="./my-resources/custom-skill",
            type="skill",
        )
        assert spec.path == "./my-resources/custom-skill"
        assert spec.type == "skill"
        assert spec.package is None

    def test_creates_with_package(self):
        """Test creating a LocalResourceSpec with package (legacy)."""
        spec = LocalResourceSpec(
            path="./scripts/deploy.md",
            type="command",
            package="my-toolkit",
        )
        assert spec.package == "my-toolkit"


class TestLocalDependencies:
    """Tests for local dependency handling in new unified format."""

    def test_load_new_format_with_local_dependencies(self, tmp_path: Path):
        """Test loading new format with local path dependencies."""
        config_content = """\
dependencies = [
    { path = "./skills/custom-skill", type = "skill" },
    { path = "./commands/deploy.md", type = "command" },
]
"""
        config_path = tmp_path / "agr.toml"
        config_path.write_text(config_content)

        config = AgrConfig.load(config_path)

        local_deps = config.get_local_dependencies()
        assert len(local_deps) == 2
        assert local_deps[0].path == "./skills/custom-skill"
        assert local_deps[0].type == "skill"
        assert local_deps[1].path == "./commands/deploy.md"
        assert local_deps[1].type == "command"

    def test_migrate_old_local_section(self, tmp_path: Path):
        """Test migrating old [local] section to new format."""
        config_content = """\
[dependencies]

[local]
"custom-skill" = { path = "./my-resources/custom-skill", type = "skill" }
"deploy-cmd" = { path = "./scripts/deploy.md", type = "command" }
"""
        config_path = tmp_path / "agr.toml"
        config_path.write_text(config_content)

        config = AgrConfig.load(config_path)

        # Should be migrated to unified dependencies
        assert config._migrated is True
        local_deps = config.get_local_dependencies()
        assert len(local_deps) == 2

        # Find by path
        skill_dep = config.get_by_path("./my-resources/custom-skill")
        cmd_dep = config.get_by_path("./scripts/deploy.md")
        assert skill_dep is not None
        assert skill_dep.type == "skill"
        assert cmd_dep is not None
        assert cmd_dep.type == "command"

    def test_load_without_local_dependencies(self, tmp_path: Path):
        """Test that config without local deps has empty local list."""
        config_content = """\
dependencies = [
    { handle = "kasperjunge/commit", type = "skill" },
]
"""
        config_path = tmp_path / "agr.toml"
        config_path.write_text(config_content)

        config = AgrConfig.load(config_path)

        assert len(config.get_local_dependencies()) == 0

    def test_save_local_dependencies(self, tmp_path: Path):
        """Test saving config with local dependencies."""
        config_path = tmp_path / "agr.toml"

        config = AgrConfig()
        config.add_local("./skills/my-skill", "skill")
        config.save(config_path)

        # Reload and verify
        loaded = AgrConfig.load(config_path)
        local_deps = loaded.get_local_dependencies()
        assert len(local_deps) == 1
        assert local_deps[0].path == "./skills/my-skill"

    def test_save_roundtrip_local(self, tmp_path: Path):
        """Test save/load roundtrip preserves local dependencies."""
        config_path = tmp_path / "agr.toml"

        config = AgrConfig()
        config.add_local("./skills/a", "skill")
        config.add_local("./commands/b.md", "command")
        config.save(config_path)

        loaded = AgrConfig.load(config_path)
        local_deps = loaded.get_local_dependencies()
        assert len(local_deps) == 2

        skill_dep = loaded.get_by_path("./skills/a")
        cmd_dep = loaded.get_by_path("./commands/b.md")
        assert skill_dep is not None
        assert skill_dep.type == "skill"
        assert cmd_dep is not None
        assert cmd_dep.type == "command"

    def test_add_local_dependency(self):
        """Test adding a local dependency."""
        config = AgrConfig()
        config.add_local("./custom/skill", "skill")

        dep = config.get_by_path("./custom/skill")
        assert dep is not None
        assert dep.path == "./custom/skill"
        assert dep.type == "skill"

    def test_remove_local_dependency(self):
        """Test removing a local dependency by path."""
        config = AgrConfig()
        config.add_local("./skills/a", "skill")
        config.add_local("./commands/b.md", "command")

        removed = config.remove_by_path("./skills/a")

        assert removed is True
        assert config.get_by_path("./skills/a") is None
        assert config.get_by_path("./commands/b.md") is not None

    def test_remove_nonexistent_local(self):
        """Test removing nonexistent local dependency returns False."""
        config = AgrConfig()
        removed = config.remove_by_path("./nonexistent")
        assert removed is False

    def test_mixed_dependencies_migration(self, tmp_path: Path):
        """Test migrating config with both dependencies and local sections."""
        config_content = """\
[dependencies]
"kasperjunge/commit" = { type = "skill" }

[local]
"my-helper" = { path = "./helpers/my-helper", type = "skill" }
"""
        config_path = tmp_path / "agr.toml"
        config_path.write_text(config_content)

        config = AgrConfig.load(config_path)

        # Both should be migrated to unified list
        assert config._migrated is True
        assert len(config.dependencies) == 2

        remote_deps = config.get_remote_dependencies()
        local_deps = config.get_local_dependencies()
        assert len(remote_deps) == 1
        assert len(local_deps) == 1

        assert config.get_by_handle("kasperjunge/commit") is not None
        assert config.get_by_path("./helpers/my-helper") is not None

    def test_migration_saves_new_format(self, tmp_path: Path):
        """Test that migrated config saves in new format."""
        # Start with old format
        config_content = """\
[dependencies]
"kasperjunge/commit" = {}

[local]
"my-skill" = { path = "./skills/my-skill", type = "skill" }
"""
        config_path = tmp_path / "agr.toml"
        config_path.write_text(config_content)

        # Load and save
        config = AgrConfig.load(config_path)
        config.save(config_path)

        # Verify new format
        content = config_path.read_text()
        assert "dependencies = [" in content
        assert "[local]" not in content
        assert "[dependencies]" not in content  # Old table format
