"""Claude Code adapter implementation."""

import shutil
from pathlib import Path

from agr.tools import ResourceType, Tool, ToolResourceConfig


class ClaudeCodeAdapter:
    """Adapter for Claude Code tool."""

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
        return "Claude Code"

    @property
    def tool_id(self) -> Tool:
        return Tool.CLAUDE_CODE

    @property
    def base_directory(self) -> str:
        return ".claude"

    @property
    def cli_binary(self) -> str | None:
        return "claude"

    def get_resource_config(self, resource_type: ResourceType) -> ToolResourceConfig | None:
        return self._RESOURCE_CONFIGS.get(resource_type)

    def is_installed(self) -> bool:
        return shutil.which(self.cli_binary) is not None

    def is_project_configured(self, project_path: Path) -> bool:
        return (project_path / self.base_directory).is_dir()
