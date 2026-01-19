"""Claude Code adapter implementation.

Provides the adapter for Claude Code, implementing the ToolAdapter protocol.
"""

import shutil
from pathlib import Path

from agr.adapters.base import ToolFormat, InstalledResource, discover_md_resources
from agr.adapters.registry import AdapterRegistry
from agr.handle import ParsedHandle


class ClaudeAdapter:
    """Adapter for Claude Code.

    Implements the ToolAdapter protocol for Claude Code,
    which uses:
    - .claude/ config directory
    - Colon-namespaced skill directories (e.g., username:skillname)
    - Nested command/agent/rule paths (e.g., username/name.md)
    - SKILL.md as skill marker
    """

    def __init__(self) -> None:
        """Initialize the Claude adapter."""
        self._format = ToolFormat(
            name="claude",
            display_name="Claude Code",
            config_dir=".claude",
            skill_dir="skills",
            command_dir="commands",
            agent_dir="agents",
            rule_dir="rules",
            skill_marker="SKILL.md",
            namespace_format="colon",
            cli_command="claude",
            global_config_dir=Path.home() / ".claude",
        )

    @property
    def format(self) -> ToolFormat:
        """Return the tool format configuration."""
        return self._format

    def get_skill_path(self, base: Path, handle: ParsedHandle) -> Path:
        """Build the path to a skill directory.

        Claude Code uses flattened colon-namespaced directories:
        - base/skills/username:skillname/
        - base/skills/skillname/ (for non-namespaced)

        Args:
            base: Base directory (e.g., Path(".claude"))
            handle: Parsed resource handle

        Returns:
            Path to the skill directory
        """
        return handle.to_skill_path(base)

    def get_command_path(self, base: Path, handle: ParsedHandle) -> Path:
        """Build the path to a command file.

        Claude Code uses nested paths:
        - base/commands/username/name.md
        - base/commands/name.md (for non-namespaced)

        Args:
            base: Base directory (e.g., Path(".claude"))
            handle: Parsed resource handle

        Returns:
            Path to the command file
        """
        return handle.to_command_path(base)

    def get_agent_path(self, base: Path, handle: ParsedHandle) -> Path:
        """Build the path to an agent file.

        Claude Code uses nested paths:
        - base/agents/username/name.md
        - base/agents/name.md (for non-namespaced)

        Args:
            base: Base directory (e.g., Path(".claude"))
            handle: Parsed resource handle

        Returns:
            Path to the agent file
        """
        return handle.to_agent_path(base)

    def get_rule_path(self, base: Path, handle: ParsedHandle) -> Path:
        """Build the path to a rule file.

        Claude Code uses nested paths:
        - base/rules/username/name.md
        - base/rules/name.md (for non-namespaced)

        Args:
            base: Base directory (e.g., Path(".claude"))
            handle: Parsed resource handle

        Returns:
            Path to the rule file
        """
        return handle.to_rule_path(base)

    def is_skill_directory(self, path: Path) -> bool:
        """Check if a path is a valid skill directory.

        Args:
            path: Path to check

        Returns:
            True if the path contains SKILL.md
        """
        return path.is_dir() and (path / self._format.skill_marker).exists()

    def discover_installed(self, base: Path) -> list[InstalledResource]:
        """Discover all installed resources in the base directory.

        Args:
            base: Base directory to search (e.g., Path(".claude"))

        Returns:
            List of discovered installed resources
        """
        resources = []

        # Discover skills (colon-namespaced directories)
        skills_dir = base / self._format.skill_dir
        if skills_dir.is_dir():
            from agr.handle import parse_handle
            for item in skills_dir.iterdir():
                if self.is_skill_directory(item):
                    parsed = parse_handle(item.name)
                    resources.append(
                        InstalledResource(
                            name=parsed.simple_name,
                            resource_type="skill",
                            path=item,
                            username=parsed.username,
                        )
                    )

        # Discover file-based resources (commands, agents, rules)
        for subdir, resource_type in [
            (self._format.command_dir, "command"),
            (self._format.agent_dir, "agent"),
            (self._format.rule_dir, "rule"),
        ]:
            resource_dir = base / subdir
            if resource_dir.is_dir():
                resources.extend(discover_md_resources(resource_dir, resource_type))

        return resources

    def is_cli_available(self) -> bool:
        """Check if the Claude CLI is available on the system.

        Returns:
            True if the claude command is available
        """
        return shutil.which(self._format.cli_command or "") is not None

    def transform_rule_content(self, content: str) -> str:
        """Transform rule content for Claude Code format.

        Claude Code uses rules as-is, no transformation needed.

        Args:
            content: Original rule content

        Returns:
            Unchanged rule content
        """
        return content


# Register the adapter
AdapterRegistry.register("claude", ClaudeAdapter)
