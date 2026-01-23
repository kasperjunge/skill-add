"""Registry for resource and tool specifications.

This module provides O(1) registration and lookup for specs,
enabling easy extensibility for new resource types and tools.
"""

from pathlib import Path

from agr.core.resource import ResourceSpec, ResourceType
from agr.core.tool import ToolSpec


# Module-level registries
_resource_specs: dict[ResourceType, ResourceSpec] = {}
_tool_specs: dict[str, ToolSpec] = {}


def register_resource_spec(spec: ResourceSpec) -> None:
    """Register a resource specification.

    Args:
        spec: The resource spec to register
    """
    _resource_specs[spec.type] = spec


def get_resource_spec(resource_type: ResourceType) -> ResourceSpec | None:
    """Get a resource specification by type.

    Args:
        resource_type: The resource type to look up

    Returns:
        The ResourceSpec or None if not registered
    """
    return _resource_specs.get(resource_type)


def get_all_resource_specs() -> dict[ResourceType, ResourceSpec]:
    """Get all registered resource specifications.

    Returns:
        Dictionary mapping resource types to their specs
    """
    return _resource_specs.copy()


def register_tool_spec(spec: ToolSpec) -> None:
    """Register a tool specification.

    Args:
        spec: The tool spec to register
    """
    _tool_specs[spec.name] = spec


def get_tool_spec(name: str) -> ToolSpec | None:
    """Get a tool specification by name.

    Args:
        name: The tool name to look up

    Returns:
        The ToolSpec or None if not registered
    """
    return _tool_specs.get(name)


def get_all_tool_specs() -> dict[str, ToolSpec]:
    """Get all registered tool specifications.

    Returns:
        Dictionary mapping tool names to their specs
    """
    return _tool_specs.copy()


def detect_tool(repo_root: Path) -> ToolSpec | None:
    """Detect which tool is in use in a repository.

    Checks for detection markers of each registered tool.

    Args:
        repo_root: Repository root path

    Returns:
        The detected ToolSpec or None if no tool is detected
    """
    for spec in _tool_specs.values():
        for marker in spec.detection_markers:
            if (repo_root / marker).exists():
                return spec
    return None


def get_default_tool() -> ToolSpec | None:
    """Get the default tool specification.

    Returns:
        The 'claude' ToolSpec if registered, otherwise the first registered tool,
        or None if no tools are registered.
    """
    # Prefer claude as default
    if "claude" in _tool_specs:
        return _tool_specs["claude"]

    # Fall back to first registered tool
    if _tool_specs:
        return next(iter(_tool_specs.values()))

    return None
