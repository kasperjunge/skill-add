"""Tool detection utilities.

Provides functionality to detect which AI coding tools are available
in the current environment.
"""

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agr.config import AgrConfig


@dataclass
class DetectedTool:
    """Information about a detected AI coding tool.

    Attributes:
        name: Tool identifier (e.g., "claude", "cursor")
        config_dir: Path to local config directory (e.g., ./.claude), None if not present
        global_dir: Path to global config directory (e.g., ~/.claude), None if not present
        cli_available: Whether the tool's CLI is available
        cli_path: Path to the CLI executable, None if not available
    """

    name: str
    config_dir: Path | None
    global_dir: Path | None
    cli_available: bool
    cli_path: str | None


# Tool configurations for detection
TOOL_CONFIGS = {
    "claude": {
        "config_dir": ".claude",
        "global_dir_name": ".claude",
        "cli_commands": ["claude"],
    },
    "cursor": {
        "config_dir": ".cursor",
        "global_dir_name": ".cursor",
        "cli_commands": ["cursor-agent", "cursor"],
    },
}


class ToolDetector:
    """Detects available AI coding tools in the environment.

    Detects tools by checking:
    1. Local config directory presence (e.g., ./.claude)
    2. Global config directory presence (e.g., ~/.claude)
    3. CLI availability (e.g., claude command)
    """

    def __init__(self, base_path: Path | None = None):
        """Initialize the detector.

        Args:
            base_path: Base path to search for local config directories.
                      Defaults to current working directory.
        """
        self.base_path = base_path or Path.cwd()

    def detect_all(self) -> list[DetectedTool]:
        """Detect all available tools.

        Returns:
            List of detected tools with their availability information
        """
        detected = []

        for tool_name, config in TOOL_CONFIGS.items():
            # Check local config directory
            local_config = self.base_path / config["config_dir"]
            config_dir = local_config if local_config.is_dir() else None

            # Check global config directory
            global_config = Path.home() / config["global_dir_name"]
            global_dir = global_config if global_config.is_dir() else None

            # Check CLI availability
            cli_available = False
            cli_path = None
            for cmd in config["cli_commands"]:
                path = shutil.which(cmd)
                if path:
                    cli_available = True
                    cli_path = path
                    break

            detected.append(
                DetectedTool(
                    name=tool_name,
                    config_dir=config_dir,
                    global_dir=global_dir,
                    cli_available=cli_available,
                    cli_path=cli_path,
                )
            )

        return detected

    def detect_from_config(self, config: "AgrConfig") -> list[str]:
        """Detect target tools from agr configuration.

        Looks for tool-specific settings in the config.

        Args:
            config: The agr configuration

        Returns:
            List of tool names specified in config
        """
        # Future: Look for [tools] section in agr.toml
        # For now, return empty list (config doesn't specify tools yet)
        return []

    def get_target_tools(self, config: "AgrConfig | None" = None) -> list[str]:
        """Get the list of tools to target for operations.

        Priority:
        1. Tools specified in config (if any)
        2. Auto-detected tools with local config directories
        3. Default to ["claude"] if nothing detected

        Args:
            config: Optional agr configuration

        Returns:
            List of tool names to target
        """
        # Check config first
        if config:
            config_tools = self.detect_from_config(config)
            if config_tools:
                return config_tools

        # Auto-detect from environment
        detected = self.detect_all()
        tools_with_config = [t.name for t in detected if t.config_dir is not None]

        if tools_with_config:
            return tools_with_config

        # Default to claude
        return ["claude"]

    def is_tool_available(self, tool_name: str) -> bool:
        """Check if a specific tool is available.

        A tool is considered available if it has:
        - A local config directory, OR
        - A global config directory, OR
        - An available CLI

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if the tool is available
        """
        detected = self.detect_all()
        for tool in detected:
            if tool.name == tool_name:
                return (
                    tool.config_dir is not None
                    or tool.global_dir is not None
                    or tool.cli_available
                )
        return False
