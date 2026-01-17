"""Tests for [local] section in config.py."""

from pathlib import Path

import pytest

from agr.config import AgrConfig, LocalResourceSpec


class TestLocalResourceSpec:
    """Tests for LocalResourceSpec dataclass."""

    def test_creates_local_resource_spec(self):
        """Test creating a LocalResourceSpec."""
        spec = LocalResourceSpec(
            path="./my-resources/custom-skill",
            type="skill",
        )
        assert spec.path == "./my-resources/custom-skill"
        assert spec.type == "skill"
        assert spec.package is None

    def test_creates_with_package(self):
        """Test creating a LocalResourceSpec with package."""
        spec = LocalResourceSpec(
            path="./scripts/deploy.md",
            type="command",
            package="my-toolkit",
        )
        assert spec.package == "my-toolkit"


class TestAgrConfigLocal:
    """Tests for AgrConfig [local] section support."""

    def test_load_with_local_section(self, tmp_path: Path):
        """Test loading config with [local] section."""
        config_content = """\
[dependencies]

[local]
"custom-skill" = { path = "./my-resources/custom-skill", type = "skill" }
"deploy-cmd" = { path = "./scripts/deploy.md", type = "command" }
"""
        config_path = tmp_path / "agr.toml"
        config_path.write_text(config_content)

        config = AgrConfig.load(config_path)

        assert len(config.local) == 2
        assert "custom-skill" in config.local
        assert config.local["custom-skill"].path == "./my-resources/custom-skill"
        assert config.local["custom-skill"].type == "skill"
        assert config.local["deploy-cmd"].type == "command"

    def test_load_with_package_in_local(self, tmp_path: Path):
        """Test loading local resource with package assignment."""
        config_content = """\
[local]
"helper" = { path = "./lib/helper", type = "skill", package = "utils" }
"""
        config_path = tmp_path / "agr.toml"
        config_path.write_text(config_content)

        config = AgrConfig.load(config_path)

        assert config.local["helper"].package == "utils"

    def test_load_without_local_section(self, tmp_path: Path):
        """Test that config without [local] section has empty local dict."""
        config_content = """\
[dependencies]
"kasperjunge/commit" = {}
"""
        config_path = tmp_path / "agr.toml"
        config_path.write_text(config_content)

        config = AgrConfig.load(config_path)

        assert len(config.local) == 0

    def test_save_local_section(self, tmp_path: Path):
        """Test saving config with local resources."""
        config_path = tmp_path / "agr.toml"

        config = AgrConfig()
        config.add_local("my-skill", LocalResourceSpec(
            path="./skills/my-skill",
            type="skill",
        ))
        config.save(config_path)

        # Reload and verify
        loaded = AgrConfig.load(config_path)
        assert "my-skill" in loaded.local
        assert loaded.local["my-skill"].path == "./skills/my-skill"

    def test_save_roundtrip_local(self, tmp_path: Path):
        """Test save/load roundtrip preserves local section."""
        config_path = tmp_path / "agr.toml"

        config = AgrConfig()
        config.add_local("skill-a", LocalResourceSpec(path="./a", type="skill"))
        config.add_local("cmd-b", LocalResourceSpec(path="./b.md", type="command", package="pkg"))
        config.save(config_path)

        loaded = AgrConfig.load(config_path)
        assert len(loaded.local) == 2
        assert loaded.local["skill-a"].type == "skill"
        assert loaded.local["cmd-b"].package == "pkg"

    def test_add_local_resource(self):
        """Test adding a local resource."""
        config = AgrConfig()
        config.add_local("my-skill", LocalResourceSpec(
            path="./custom/skill",
            type="skill",
        ))

        assert "my-skill" in config.local
        assert config.local["my-skill"].path == "./custom/skill"

    def test_remove_local_resource(self):
        """Test removing a local resource."""
        config = AgrConfig()
        config.add_local("my-skill", LocalResourceSpec(path="./a"))
        config.add_local("my-cmd", LocalResourceSpec(path="./b"))

        config.remove_local("my-skill")

        assert "my-skill" not in config.local
        assert "my-cmd" in config.local

    def test_remove_nonexistent_local(self):
        """Test removing nonexistent local resource doesn't error."""
        config = AgrConfig()
        config.remove_local("nonexistent")  # Should not raise

    def test_mixed_dependencies_and_local(self, tmp_path: Path):
        """Test config with both dependencies and local sections."""
        config_content = """\
[dependencies]
"kasperjunge/commit" = { type = "skill" }

[local]
"my-helper" = { path = "./helpers/my-helper" }
"""
        config_path = tmp_path / "agr.toml"
        config_path.write_text(config_content)

        config = AgrConfig.load(config_path)

        assert len(config.dependencies) == 1
        assert len(config.local) == 1
        assert "kasperjunge/commit" in config.dependencies
        assert "my-helper" in config.local
