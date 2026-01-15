"""Tool abstraction layer for supporting multiple AI coding tools."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol


class Tool(Enum):
    """Supported AI coding tools."""

    CLAUDE_CODE = "claude"


class ResourceType(Enum):
    """Type of resource to fetch."""

    SKILL = "skill"
    COMMAND = "command"
    AGENT = "agent"


@dataclass(frozen=True)
class ToolResourceConfig:
    """Configuration for how a tool handles a specific resource type."""

    base_dir: str
    subdir: str
    is_directory: bool
    file_extension: str | None
    entry_file: str | None = None


class ToolAdapter(Protocol):
    """Protocol defining the interface for tool adapters."""

    @property
    def name(self) -> str:
        """Human-readable name of the tool."""
        ...

    @property
    def tool_id(self) -> Tool:
        """Tool identifier enum value."""
        ...

    @property
    def base_directory(self) -> str:
        """Base directory for tool configuration (e.g., '.claude')."""
        ...

    @property
    def cli_binary(self) -> str | None:
        """CLI binary name, or None if no CLI."""
        ...

    def get_resource_config(self, resource_type: ResourceType) -> ToolResourceConfig | None:
        """Get configuration for a specific resource type."""
        ...

    def is_installed(self) -> bool:
        """Check if the tool's CLI is installed on the system."""
        ...

    def is_project_configured(self, project_path: Path) -> bool:
        """Check if a project has this tool configured."""
        ...


__all__ = [
    "Tool",
    "ResourceType",
    "ToolResourceConfig",
    "ToolAdapter",
]
