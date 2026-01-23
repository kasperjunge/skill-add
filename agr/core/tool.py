"""Tool specification definitions.

This module defines the abstractions for AI coding tools (Claude, Cursor, etc.)
and how they store resources.
"""

from dataclasses import dataclass
from pathlib import Path

from agr.core.resource import ResourceType


@dataclass(frozen=True)
class ToolResourceConfig:
    """Configuration for how a tool stores a specific resource type."""

    subdir: str  # e.g., "skills", "rules", "agents"


@dataclass(frozen=True)
class ToolSpec:
    """Specification for an AI coding tool.

    Defines how a tool stores resources and how to detect it.
    """

    name: str  # e.g., "claude"
    config_dir: str  # e.g., ".claude"
    global_config_dir: str  # e.g., "~/.claude"
    resource_configs: dict[ResourceType, ToolResourceConfig]
    detection_markers: tuple[str, ...]  # Files/dirs that indicate this tool is in use

    def supports_resource(self, resource_type: ResourceType) -> bool:
        """Check if this tool supports a resource type.

        Args:
            resource_type: The resource type to check

        Returns:
            True if the tool supports this resource type
        """
        return resource_type in self.resource_configs

    def get_resource_dir(self, repo_root: Path, resource_type: ResourceType) -> Path:
        """Get the resource directory for this tool in a repo.

        Args:
            repo_root: Repository root path
            resource_type: The resource type

        Returns:
            Path to the resource directory

        Raises:
            ValueError: If the tool doesn't support this resource type
        """
        if resource_type not in self.resource_configs:
            raise ValueError(
                f"Tool '{self.name}' does not support resource type '{resource_type.value}'"
            )
        config = self.resource_configs[resource_type]
        return repo_root / self.config_dir / config.subdir

    def get_global_resource_dir(self, resource_type: ResourceType) -> Path:
        """Get the global resource directory for this tool.

        Args:
            resource_type: The resource type

        Returns:
            Path to the global resource directory

        Raises:
            ValueError: If the tool doesn't support this resource type
        """
        if resource_type not in self.resource_configs:
            raise ValueError(
                f"Tool '{self.name}' does not support resource type '{resource_type.value}'"
            )
        config = self.resource_configs[resource_type]
        global_dir = Path(self.global_config_dir).expanduser()
        return global_dir / config.subdir

    # Backward compatibility methods for skills
    def get_skills_dir(self, repo_root: Path) -> Path:
        """Get the skills directory for this tool in a repo.

        Args:
            repo_root: Repository root path

        Returns:
            Path to the skills directory
        """
        return self.get_resource_dir(repo_root, ResourceType.SKILL)

    def get_global_skills_dir(self) -> Path:
        """Get the global skills directory (in user home).

        Returns:
            Path to the global skills directory
        """
        return self.get_global_resource_dir(ResourceType.SKILL)
