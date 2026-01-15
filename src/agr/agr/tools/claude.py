"""Claude Code adapter implementation."""

import shutil
from pathlib import Path

from agr.tools import ResourceType, Tool, ToolResourceConfig


class ClaudeCodeAdapter:
    """Adapter for Claude Code tool.

    Claude Code is the canonical format for agent-resources.
    All other tools transform from/to this format.
    """

    # Resource configurations for Claude Code
    _RESOURCE_CONFIGS: dict[ResourceType, ToolResourceConfig] = {
        ResourceType.SKILL: ToolResourceConfig(
            base_dir=".claude",
            subdir="skills",
            is_directory=True,
            file_extension=None,
            entry_file="SKILL.md",
        ),
        ResourceType.COMMAND: ToolResourceConfig(
            base_dir=".claude",
            subdir="commands",
            is_directory=False,
            file_extension=".md",
            entry_file=None,
        ),
        ResourceType.AGENT: ToolResourceConfig(
            base_dir=".claude",
            subdir="agents",
            is_directory=False,
            file_extension=".md",
            entry_file=None,
        ),
    }

    @property
    def name(self) -> str:
        """Human-readable name of the tool."""
        return "Claude Code"

    @property
    def tool_id(self) -> Tool:
        """Tool identifier enum value."""
        return Tool.CLAUDE_CODE

    @property
    def base_directory(self) -> str:
        """Base directory for tool configuration."""
        return ".claude"

    @property
    def cli_binary(self) -> str | None:
        """CLI binary name."""
        return "claude"

    def get_resource_config(self, resource_type: ResourceType) -> ToolResourceConfig | None:
        """Get configuration for a specific resource type."""
        return self._RESOURCE_CONFIGS.get(resource_type)

    def supports_resource_type(self, resource_type: ResourceType) -> bool:
        """Check if this tool supports a given resource type."""
        return resource_type in self._RESOURCE_CONFIGS

    def is_installed(self) -> bool:
        """Check if the Claude CLI is installed on the system."""
        return shutil.which(self.cli_binary) is not None

    def is_project_configured(self, project_path: Path) -> bool:
        """Check if a project has Claude Code configured."""
        return (project_path / self.base_directory).is_dir()

    def transform_resource(
        self,
        content: str,
        source_tool: Tool,
        resource_type: ResourceType,
    ) -> str:
        """Transform resource content from another tool's format.

        Since Claude Code is the canonical format, transformations from
        Claude Code to Claude Code are identity operations. Transformations
        from other tools would be implemented here in the future.
        """
        # Claude Code is the canonical format - no transformation needed
        # when source is also Claude Code
        if source_tool == Tool.CLAUDE_CODE:
            return content

        # Future: implement transformations from other tools
        # For now, return content as-is (best effort)
        return content

    def get_source_subdir(self, resource_type: ResourceType) -> str:
        """Get the full source subdirectory path for a resource type.

        Args:
            resource_type: The type of resource

        Returns:
            Full path like ".claude/skills" or ".claude/commands"
        """
        config = self.get_resource_config(resource_type)
        if config is None:
            raise ValueError(f"Unsupported resource type: {resource_type}")
        return f"{config.base_dir}/{config.subdir}"

    def get_dest_subdir(self, resource_type: ResourceType) -> str:
        """Get the destination subdirectory for a resource type.

        Args:
            resource_type: The type of resource

        Returns:
            Subdirectory name like "skills" or "commands"
        """
        config = self.get_resource_config(resource_type)
        if config is None:
            raise ValueError(f"Unsupported resource type: {resource_type}")
        return config.subdir
