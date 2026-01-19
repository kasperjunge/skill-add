"""Base classes and protocols for tool adapters.

This module defines the core abstractions for tool-specific adapters,
enabling agr to work with different AI coding tools like Claude Code and Cursor.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ToolFormat:
    """Tool-specific format configuration.

    Defines the directory structure and conventions used by a specific
    AI coding tool (e.g., Claude Code, Cursor).

    Attributes:
        name: Short identifier for the tool (e.g., "claude", "cursor")
        display_name: Human-readable tool name (e.g., "Claude Code", "Cursor")
        config_dir: Name of the config directory (e.g., ".claude", ".cursor")
        skill_dir: Subdirectory for skills (e.g., "skills")
        command_dir: Subdirectory for commands (e.g., "commands")
        agent_dir: Subdirectory for agents (e.g., "agents")
        rule_dir: Subdirectory for rules (e.g., "rules")
        skill_marker: File that identifies a skill directory (e.g., "SKILL.md")
        namespace_format: How namespaces are handled ("colon", "nested", "flat")
        cli_command: CLI command to invoke the tool (e.g., "claude"), None if not applicable
        global_config_dir: Path to global config directory (e.g., ~/.claude)
    """

    name: str
    display_name: str
    config_dir: str
    skill_dir: str
    command_dir: str
    agent_dir: str
    rule_dir: str
    skill_marker: str
    namespace_format: str  # "colon" | "nested" | "flat"
    cli_command: str | None
    global_config_dir: Path


@runtime_checkable
class ToolAdapter(Protocol):
    """Protocol for tool-specific adapters.

    Defines the interface that all tool adapters must implement.
    Uses structural typing (Protocol) for flexibility.
    """

    @property
    def format(self) -> ToolFormat:
        """Return the tool format configuration."""
        ...

    def get_skill_path(self, base: Path, handle: "ParsedHandle") -> Path:
        """Build the path to a skill directory.

        Args:
            base: Base directory (e.g., Path(".claude"))
            handle: Parsed resource handle

        Returns:
            Path to the skill directory
        """
        ...

    def get_command_path(self, base: Path, handle: "ParsedHandle") -> Path:
        """Build the path to a command file.

        Args:
            base: Base directory (e.g., Path(".claude"))
            handle: Parsed resource handle

        Returns:
            Path to the command file
        """
        ...

    def get_agent_path(self, base: Path, handle: "ParsedHandle") -> Path:
        """Build the path to an agent file.

        Args:
            base: Base directory (e.g., Path(".claude"))
            handle: Parsed resource handle

        Returns:
            Path to the agent file
        """
        ...

    def get_rule_path(self, base: Path, handle: "ParsedHandle") -> Path:
        """Build the path to a rule file.

        Args:
            base: Base directory (e.g., Path(".claude"))
            handle: Parsed resource handle

        Returns:
            Path to the rule file
        """
        ...

    def is_skill_directory(self, path: Path) -> bool:
        """Check if a path is a valid skill directory.

        Args:
            path: Path to check

        Returns:
            True if the path is a valid skill directory
        """
        ...

    def discover_installed(self, base: Path) -> list["InstalledResource"]:
        """Discover all installed resources in the base directory.

        Args:
            base: Base directory to search (e.g., Path(".claude"))

        Returns:
            List of discovered installed resources
        """
        ...

    def is_cli_available(self) -> bool:
        """Check if the tool's CLI is available on the system.

        Returns:
            True if the CLI is available
        """
        ...

    def transform_rule_content(self, content: str) -> str:
        """Transform rule content for this tool's format.

        Different tools may have different rule format requirements.
        For example, Cursor may need paths: frontmatter converted to globs.

        Args:
            content: Original rule content

        Returns:
            Transformed rule content for this tool
        """
        ...


@dataclass
class InstalledResource:
    """Represents an installed resource discovered by an adapter.

    Attributes:
        name: Resource name
        resource_type: Type of resource ("skill", "command", "agent", "rule")
        path: Path to the installed resource
        username: Username namespace (if namespaced)
    """

    name: str
    resource_type: str
    path: Path
    username: str | None = None


def discover_md_resources(
    resource_dir: Path, resource_type: str
) -> list[InstalledResource]:
    """Discover .md resources in a directory.

    Handles both flat and nested (username/name.md) structures.
    Shared helper for adapters.

    Args:
        resource_dir: Directory to search
        resource_type: Type of resource ("command", "agent", "rule")

    Returns:
        List of discovered resources
    """
    resources = []

    for item in resource_dir.iterdir():
        if item.is_file() and item.suffix == ".md":
            resources.append(
                InstalledResource(
                    name=item.stem,
                    resource_type=resource_type,
                    path=item,
                    username=None,
                )
            )
        elif item.is_dir():
            for sub_item in item.iterdir():
                if sub_item.is_file() and sub_item.suffix == ".md":
                    resources.append(
                        InstalledResource(
                            name=sub_item.stem,
                            resource_type=resource_type,
                            path=sub_item,
                            username=item.name,
                        )
                    )

    return resources


# Type alias for forward reference
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agr.handle import ParsedHandle
