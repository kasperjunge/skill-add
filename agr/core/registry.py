"""Registry for resource and tool specifications.

This module provides O(1) registration and lookup for specs,
enabling easy extensibility for new resource types and tools.

Thread-safe: All registry operations are protected by a lock.
"""

import threading
from pathlib import Path

from agr.core.resource import ResourceSpec, ResourceType
from agr.core.tool import ToolSpec


# Module-level registries with lock for thread safety
_registry_lock = threading.Lock()
_resource_specs: dict[ResourceType, ResourceSpec] = {}
_tool_specs: dict[str, ToolSpec] = {}
_builtin_specs_registered = False
_suppress_auto_registration = False  # For testing: prevents lazy registration


def ensure_builtin_specs_registered() -> None:
    """Ensure built-in specs are registered.

    This is idempotent - calling it multiple times has no effect.
    Called lazily by get_default_tool() and get_resource_spec().
    """
    global _builtin_specs_registered
    with _registry_lock:
        if _builtin_specs_registered or _suppress_auto_registration:
            return
        _builtin_specs_registered = True

    # Import here to avoid circular imports and perform registration
    from agr.core.specs import register_builtin_specs
    register_builtin_specs()


def register_resource_spec(spec: ResourceSpec) -> None:
    """Register a resource specification.

    Args:
        spec: The resource spec to register
    """
    with _registry_lock:
        _resource_specs[spec.type] = spec


def get_resource_spec(resource_type: ResourceType) -> ResourceSpec | None:
    """Get a resource specification by type.

    Args:
        resource_type: The resource type to look up

    Returns:
        The ResourceSpec or None if not registered
    """
    ensure_builtin_specs_registered()
    with _registry_lock:
        return _resource_specs.get(resource_type)


def get_all_resource_specs() -> dict[ResourceType, ResourceSpec]:
    """Get all registered resource specifications.

    Returns:
        Dictionary mapping resource types to their specs
    """
    ensure_builtin_specs_registered()
    with _registry_lock:
        return _resource_specs.copy()


def register_tool_spec(spec: ToolSpec) -> None:
    """Register a tool specification.

    Args:
        spec: The tool spec to register
    """
    with _registry_lock:
        _tool_specs[spec.name] = spec


def get_tool_spec(name: str) -> ToolSpec | None:
    """Get a tool specification by name.

    Args:
        name: The tool name to look up

    Returns:
        The ToolSpec or None if not registered
    """
    ensure_builtin_specs_registered()
    with _registry_lock:
        return _tool_specs.get(name)


def get_all_tool_specs() -> dict[str, ToolSpec]:
    """Get all registered tool specifications.

    Returns:
        Dictionary mapping tool names to their specs
    """
    ensure_builtin_specs_registered()
    with _registry_lock:
        return _tool_specs.copy()


def detect_tool(repo_root: Path) -> ToolSpec | None:
    """Detect which tool is in use in a repository.

    Checks for detection markers of each registered tool.

    Args:
        repo_root: Repository root path

    Returns:
        The detected ToolSpec or None if no tool is detected
    """
    ensure_builtin_specs_registered()
    with _registry_lock:
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
    ensure_builtin_specs_registered()
    with _registry_lock:
        # Prefer claude as default
        if "claude" in _tool_specs:
            return _tool_specs["claude"]

        # Fall back to first registered tool
        if _tool_specs:
            return next(iter(_tool_specs.values()))

        return None


# --- Test utilities for registry isolation ---


def clear_registry(*, suppress_auto_registration: bool = True) -> None:
    """Clear all registered specs.

    This is primarily for testing purposes to ensure test isolation.

    Args:
        suppress_auto_registration: If True (default), prevents lazy registration
            from automatically re-registering built-in specs after clearing.
            Set to False to allow normal lazy registration behavior.
    """
    global _builtin_specs_registered, _suppress_auto_registration
    with _registry_lock:
        _resource_specs.clear()
        _tool_specs.clear()
        _builtin_specs_registered = False
        _suppress_auto_registration = suppress_auto_registration


def get_registry_snapshot() -> tuple[dict[ResourceType, ResourceSpec], dict[str, ToolSpec], bool, bool]:
    """Get a snapshot of the current registry state.

    Returns:
        Tuple of (resource_specs copy, tool_specs copy, builtin_registered flag, suppress_flag)
    """
    with _registry_lock:
        return (
            _resource_specs.copy(),
            _tool_specs.copy(),
            _builtin_specs_registered,
            _suppress_auto_registration,
        )


def restore_registry_snapshot(
    snapshot: tuple[dict[ResourceType, ResourceSpec], dict[str, ToolSpec], bool, bool] | tuple[dict[ResourceType, ResourceSpec], dict[str, ToolSpec], bool]
) -> None:
    """Restore registry state from a snapshot.

    Args:
        snapshot: Tuple returned by get_registry_snapshot()
    """
    global _builtin_specs_registered, _suppress_auto_registration
    # Handle both old 3-tuple and new 4-tuple snapshots for compatibility
    if len(snapshot) == 4:
        resource_specs, tool_specs, builtin_registered, suppress_flag = snapshot
    else:
        resource_specs, tool_specs, builtin_registered = snapshot
        suppress_flag = False

    with _registry_lock:
        _resource_specs.clear()
        _resource_specs.update(resource_specs)
        _tool_specs.clear()
        _tool_specs.update(tool_specs)
        _builtin_specs_registered = builtin_registered
        _suppress_auto_registration = suppress_flag
