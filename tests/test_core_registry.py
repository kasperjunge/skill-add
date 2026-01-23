"""Tests for agr.core.registry module."""

import pytest

from agr.core.registry import (
    clear_registry,
    detect_tool,
    get_all_resource_specs,
    get_all_tool_specs,
    get_default_tool,
    get_registry_snapshot,
    get_resource_spec,
    get_tool_spec,
    register_resource_spec,
    register_tool_spec,
    restore_registry_snapshot,
)
from agr.core.resource import ResourceSpec, ResourceType
from agr.core.tool import ToolResourceConfig, ToolSpec


class TestResourceRegistry:
    """Tests for resource spec registry functions."""

    @pytest.fixture(autouse=True)
    def clean_registry(self):
        """Clean registry before and after each test."""
        # Store original state using public API
        snapshot = get_registry_snapshot()

        # Clear registry and suppress auto-registration for test isolation
        clear_registry(suppress_auto_registration=True)

        yield

        # Restore original state using public API
        restore_registry_snapshot(snapshot)

    @pytest.fixture
    def test_spec(self):
        """Create a test resource spec."""
        return ResourceSpec(
            type=ResourceType.SKILL,
            marker_file="TEST.md",
            is_directory=True,
            search_paths=("test",),
            required_frontmatter=(),
            optional_frontmatter=(),
            name_pattern=r"^[a-z]+$",
        )

    def test_register_and_get_resource_spec(self, test_spec):
        """Can register and retrieve a resource spec."""
        register_resource_spec(test_spec)
        retrieved = get_resource_spec(ResourceType.SKILL)
        assert retrieved is not None
        assert retrieved.marker_file == "TEST.md"

    def test_get_resource_spec_not_found(self):
        """Returns None for unregistered resource type."""
        # Clear the registry for this test using public API
        clear_registry()
        result = get_resource_spec(ResourceType.SKILL)
        assert result is None

    def test_get_all_resource_specs(self, test_spec):
        """Returns copy of all registered specs."""
        register_resource_spec(test_spec)
        all_specs = get_all_resource_specs()
        assert ResourceType.SKILL in all_specs
        # Verify it's a copy (modifications don't affect registry)
        all_specs.clear()
        assert get_resource_spec(ResourceType.SKILL) is not None


class TestToolRegistry:
    """Tests for tool spec registry functions."""

    @pytest.fixture(autouse=True)
    def clean_registry(self):
        """Clean registry before and after each test."""
        snapshot = get_registry_snapshot()
        clear_registry(suppress_auto_registration=True)

        yield

        restore_registry_snapshot(snapshot)

    @pytest.fixture
    def test_tool_spec(self):
        """Create a test tool spec."""
        return ToolSpec(
            name="test-tool",
            config_dir=".test",
            global_config_dir="~/.test",
            resource_configs={
                ResourceType.SKILL: ToolResourceConfig(subdir="skills"),
            },
            detection_markers=(".test",),
        )

    def test_register_and_get_tool_spec(self, test_tool_spec):
        """Can register and retrieve a tool spec."""
        register_tool_spec(test_tool_spec)
        retrieved = get_tool_spec("test-tool")
        assert retrieved is not None
        assert retrieved.config_dir == ".test"

    def test_get_tool_spec_not_found(self):
        """Returns None for unregistered tool."""
        result = get_tool_spec("nonexistent")
        assert result is None

    def test_get_all_tool_specs(self, test_tool_spec):
        """Returns copy of all registered tool specs."""
        register_tool_spec(test_tool_spec)
        all_specs = get_all_tool_specs()
        assert "test-tool" in all_specs
        # Verify it's a copy
        all_specs.clear()
        assert get_tool_spec("test-tool") is not None


class TestDetectTool:
    """Tests for detect_tool function."""

    @pytest.fixture(autouse=True)
    def clean_registry(self):
        """Clean registry before and after each test."""
        snapshot = get_registry_snapshot()
        clear_registry(suppress_auto_registration=True)

        yield

        restore_registry_snapshot(snapshot)

    def test_detect_tool_with_marker(self, tmp_path):
        """Detects tool when marker exists."""
        # Register a tool with a marker
        tool = ToolSpec(
            name="marker-tool",
            config_dir=".marker",
            global_config_dir="~/.marker",
            resource_configs={},
            detection_markers=(".marker", ".marker-alt"),
        )
        register_tool_spec(tool)

        # Create the marker
        (tmp_path / ".marker").mkdir()

        detected = detect_tool(tmp_path)
        assert detected is not None
        assert detected.name == "marker-tool"

    def test_detect_tool_no_marker(self, tmp_path):
        """Returns None when no markers found."""
        clear_registry()  # Ensure clean slate using public API
        tool = ToolSpec(
            name="marker-tool",
            config_dir=".marker",
            global_config_dir="~/.marker",
            resource_configs={},
            detection_markers=(".marker",),
        )
        register_tool_spec(tool)

        # No marker created
        detected = detect_tool(tmp_path)
        assert detected is None


class TestGetDefaultTool:
    """Tests for get_default_tool function."""

    @pytest.fixture(autouse=True)
    def clean_registry(self):
        """Clean registry before and after each test."""
        snapshot = get_registry_snapshot()
        clear_registry(suppress_auto_registration=True)

        yield

        restore_registry_snapshot(snapshot)

    def test_default_tool_prefers_claude(self):
        """Returns claude if registered."""
        claude = ToolSpec(
            name="claude",
            config_dir=".claude",
            global_config_dir="~/.claude",
            resource_configs={},
            detection_markers=(),
        )
        other = ToolSpec(
            name="other",
            config_dir=".other",
            global_config_dir="~/.other",
            resource_configs={},
            detection_markers=(),
        )
        register_tool_spec(other)
        register_tool_spec(claude)

        default = get_default_tool()
        assert default is not None
        assert default.name == "claude"

    def test_default_tool_fallback(self):
        """Returns first tool if claude not registered."""
        clear_registry()
        other = ToolSpec(
            name="other",
            config_dir=".other",
            global_config_dir="~/.other",
            resource_configs={},
            detection_markers=(),
        )
        register_tool_spec(other)

        default = get_default_tool()
        assert default is not None
        assert default.name == "other"

    def test_default_tool_none_when_empty(self):
        """Returns None when no tools registered."""
        clear_registry()
        assert get_default_tool() is None
