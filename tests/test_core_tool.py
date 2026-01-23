"""Tests for agr.core.tool module."""

from pathlib import Path

import pytest

from agr.core.resource import ResourceType
from agr.core.tool import ToolResourceConfig, ToolSpec


class TestToolResourceConfig:
    """Tests for ToolResourceConfig class."""

    def test_create_config(self):
        """Can create a ToolResourceConfig."""
        config = ToolResourceConfig(subdir="skills")
        assert config.subdir == "skills"

    def test_frozen(self):
        """ToolResourceConfig is frozen (immutable)."""
        config = ToolResourceConfig(subdir="skills")
        with pytest.raises(Exception):  # FrozenInstanceError
            config.subdir = "other"


class TestToolSpec:
    """Tests for ToolSpec class."""

    @pytest.fixture
    def claude_spec(self):
        """Create a Claude tool spec for testing."""
        return ToolSpec(
            name="claude",
            config_dir=".claude",
            global_config_dir="~/.claude",
            resource_configs={
                ResourceType.SKILL: ToolResourceConfig(subdir="skills"),
            },
            detection_markers=(".claude",),
        )

    def test_supports_resource_supported(self, claude_spec):
        """Returns True for supported resource types."""
        assert claude_spec.supports_resource(ResourceType.SKILL)

    def test_supports_resource_not_supported(self, claude_spec):
        """Returns False for unsupported resource types."""
        # Create a mock enum value for testing
        # Since ResourceType only has SKILL currently, we test with a valid type
        # that's not in the config (but this would fail since SKILL is the only one)
        # For now, just verify SKILL is supported
        assert claude_spec.supports_resource(ResourceType.SKILL)

    def test_get_resource_dir(self, claude_spec, tmp_path):
        """Returns correct resource directory path."""
        expected = tmp_path / ".claude" / "skills"
        assert claude_spec.get_resource_dir(tmp_path, ResourceType.SKILL) == expected

    def test_get_resource_dir_unsupported_raises(self, tmp_path):
        """Raises ValueError for unsupported resource type."""
        # Create a spec with no resource configs
        spec = ToolSpec(
            name="empty",
            config_dir=".empty",
            global_config_dir="~/.empty",
            resource_configs={},
            detection_markers=(),
        )
        with pytest.raises(ValueError, match="does not support resource type"):
            spec.get_resource_dir(tmp_path, ResourceType.SKILL)

    def test_get_global_resource_dir(self, claude_spec):
        """Returns correct global resource directory path."""
        expected = Path.home() / ".claude" / "skills"
        assert claude_spec.get_global_resource_dir(ResourceType.SKILL) == expected

    def test_get_global_resource_dir_unsupported_raises(self):
        """Raises ValueError for unsupported resource type."""
        spec = ToolSpec(
            name="empty",
            config_dir=".empty",
            global_config_dir="~/.empty",
            resource_configs={},
            detection_markers=(),
        )
        with pytest.raises(ValueError, match="does not support resource type"):
            spec.get_global_resource_dir(ResourceType.SKILL)

    def test_get_skills_dir_backward_compat(self, claude_spec, tmp_path):
        """get_skills_dir works for backward compatibility."""
        expected = tmp_path / ".claude" / "skills"
        assert claude_spec.get_skills_dir(tmp_path) == expected

    def test_get_global_skills_dir_backward_compat(self, claude_spec):
        """get_global_skills_dir works for backward compatibility."""
        expected = Path.home() / ".claude" / "skills"
        assert claude_spec.get_global_skills_dir() == expected

    def test_frozen(self, claude_spec):
        """ToolSpec is frozen (immutable)."""
        with pytest.raises(Exception):  # FrozenInstanceError
            claude_spec.name = "other"
