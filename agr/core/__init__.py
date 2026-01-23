"""Core abstractions for agr.

This module provides the core abstractions for resource and tool management:

- ResourceType: Enum of supported resource types
- ResourceSpec: Specification for a resource type
- Resource: An actual resource instance
- ToolSpec: Specification for an AI coding tool
- ToolResourceConfig: How a tool stores a resource type
- Orchestrator: Coordinates the install/uninstall pipeline

Built-in specs:
- SKILL_SPEC: Skill resource specification
- CLAUDE_SPEC: Claude Code tool specification
"""

from agr.core.discovery import (
    discover_resources_in_repo,
    find_resource_in_repo,
    is_valid_resource_path,
)
from agr.core.orchestrator import InstallResult, Orchestrator
from agr.core.registry import (
    detect_tool,
    get_all_resource_specs,
    get_all_tool_specs,
    get_default_tool,
    get_resource_spec,
    get_tool_spec,
    register_resource_spec,
    register_tool_spec,
)
from agr.core.resource import Resource, ResourceSpec, ResourceType
from agr.core.specs import CLAUDE_SPEC, SKILL_SPEC
from agr.core.tool import ToolResourceConfig, ToolSpec

__all__ = [
    # Resource types and specs
    "ResourceType",
    "ResourceSpec",
    "Resource",
    # Tool types and specs
    "ToolSpec",
    "ToolResourceConfig",
    # Built-in specs
    "SKILL_SPEC",
    "CLAUDE_SPEC",
    # Registry functions
    "register_resource_spec",
    "get_resource_spec",
    "get_all_resource_specs",
    "register_tool_spec",
    "get_tool_spec",
    "get_all_tool_specs",
    "detect_tool",
    "get_default_tool",
    # Discovery functions
    "find_resource_in_repo",
    "discover_resources_in_repo",
    "is_valid_resource_path",
    # Orchestrator
    "Orchestrator",
    "InstallResult",
]
