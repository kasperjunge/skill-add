"""Built-in resource and tool specifications.

This module defines the built-in specs for Phase 1:
- SKILL_SPEC: Skill resource specification
- CLAUDE_SPEC: Claude Code tool specification

Import this module to register the built-in specs.
"""

from agr.core.registry import register_resource_spec, register_tool_spec
from agr.core.resource import ResourceSpec, ResourceType
from agr.core.tool import ToolResourceConfig, ToolSpec


# Skill resource specification
SKILL_SPEC = ResourceSpec(
    type=ResourceType.SKILL,
    marker_file="SKILL.md",
    is_directory=True,
    search_paths=("resources/skills", "skills", "."),
    required_frontmatter=(),  # No required fields for now
    optional_frontmatter=("name", "description", "version"),
    name_pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$",
)


# Claude Code tool specification
CLAUDE_SPEC = ToolSpec(
    name="claude",
    config_dir=".claude",
    global_config_dir="~/.claude",
    resource_configs={
        ResourceType.SKILL: ToolResourceConfig(subdir="skills"),
        # Future: ResourceType.RULE: ToolResourceConfig(subdir="rules"),
    },
    detection_markers=(".claude",),
)


def register_builtin_specs() -> None:
    """Register all built-in resource and tool specifications."""
    register_resource_spec(SKILL_SPEC)
    register_tool_spec(CLAUDE_SPEC)


# Auto-register when module is imported
register_builtin_specs()
