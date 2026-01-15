"""Tool abstraction layer for supporting multiple AI coding tools."""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class Tool(Enum):
    """Supported AI coding tools."""

    CLAUDE_CODE = "claude"
    # Future tools (placeholders for architecture design):
    # CURSOR = "cursor"
    # COPILOT = "copilot"
    # CODEX = "codex"


class ResourceType(Enum):
    """Type of resource to fetch."""

    SKILL = "skill"
    COMMAND = "command"
    AGENT = "agent"


@dataclass(frozen=True)
class ToolResourceConfig:
    """How a tool handles a specific resource type.

    Attributes:
        base_dir: Base directory for the tool (e.g., ".claude")
        subdir: Subdirectory for this resource type (e.g., "skills", "commands")
        is_directory: True for directory-based resources (skills), False for files
        file_extension: Extension for file-based resources (e.g., ".md"), None for directories
        entry_file: Entry file for directory-based resources (e.g., "SKILL.md")
    """

    base_dir: str
    subdir: str
    is_directory: bool
    file_extension: str | None
    entry_file: str | None = None


class ToolAdapter(Protocol):
    """Protocol defining the interface for tool adapters.

    Each AI coding tool (Claude Code, Cursor, Copilot, etc.) implements
    this protocol to define how it handles resources.
    """

    @property
    def name(self) -> str:
        """Human-readable name of the tool (e.g., 'Claude Code')."""
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
        """CLI binary name (e.g., 'claude'), or None if no CLI."""
        ...

    def get_resource_config(self, resource_type: ResourceType) -> ToolResourceConfig | None:
        """Get configuration for a specific resource type.

        Args:
            resource_type: The type of resource

        Returns:
            ToolResourceConfig for this resource type, or None if not supported
        """
        ...

    def supports_resource_type(self, resource_type: ResourceType) -> bool:
        """Check if this tool supports a given resource type.

        Args:
            resource_type: The type of resource

        Returns:
            True if the tool supports this resource type
        """
        ...

    def is_installed(self) -> bool:
        """Check if the tool's CLI is installed on the system.

        Returns:
            True if the CLI binary is found in PATH
        """
        ...

    def is_project_configured(self, project_path: "Path") -> bool:
        """Check if a project has this tool configured.

        Args:
            project_path: Path to the project directory

        Returns:
            True if the tool's base directory exists in the project
        """
        ...

    def transform_resource(
        self,
        content: str,
        source_tool: Tool,
        resource_type: ResourceType,
    ) -> str:
        """Transform resource content from another tool's format.

        Args:
            content: The resource content to transform
            source_tool: The tool the content was authored for
            resource_type: The type of resource

        Returns:
            Transformed content suitable for this tool
        """
        ...


# Re-export Path for type hints in protocol
from pathlib import Path

__all__ = [
    "Tool",
    "ResourceType",
    "ToolResourceConfig",
    "ToolAdapter",
]
