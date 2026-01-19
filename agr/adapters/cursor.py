"""Cursor adapter implementation.

Provides the adapter for Cursor, implementing the ToolAdapter protocol.
"""

import re
import shutil
from pathlib import Path

from agr.adapters.base import ToolFormat, InstalledResource, discover_md_resources
from agr.adapters.registry import AdapterRegistry
from agr.handle import ParsedHandle


class CursorAdapter:
    """Adapter for Cursor.

    Implements the ToolAdapter protocol for Cursor,
    which uses:
    - .cursor/ config directory
    - Reads skills from .claude/skills/ for Claude compatibility
    - Uses .cursorrules for rules (or .cursor/rules/)
    - May have different path conventions in the future
    """

    def __init__(self) -> None:
        """Initialize the Cursor adapter."""
        self._format = ToolFormat(
            name="cursor",
            display_name="Cursor",
            config_dir=".cursor",
            skill_dir="skills",  # Note: Cursor may read from .claude/skills
            command_dir="commands",
            agent_dir="agents",
            rule_dir="rules",
            skill_marker="SKILL.md",  # Same as Claude for compatibility
            namespace_format="nested",  # Cursor uses nested paths
            cli_command="cursor",  # Or cursor-agent
            global_config_dir=Path.home() / ".cursor",
        )

    @property
    def format(self) -> ToolFormat:
        """Return the tool format configuration."""
        return self._format

    def get_skill_path(self, base: Path, handle: ParsedHandle) -> Path:
        """Build the path to a skill directory.

        Cursor uses nested directory structure:
        - base/skills/username/skillname/
        - base/skills/skillname/ (for non-namespaced)

        Args:
            base: Base directory (e.g., Path(".cursor"))
            handle: Parsed resource handle

        Returns:
            Path to the skill directory
        """
        # Cursor uses nested format instead of colon format
        if not handle.username:
            return base / self._format.skill_dir / handle.simple_name
        return base / self._format.skill_dir / handle.username / handle.simple_name

    def get_command_path(self, base: Path, handle: ParsedHandle) -> Path:
        """Build the path to a command file.

        Cursor uses nested paths:
        - base/commands/username/name.md
        - base/commands/name.md (for non-namespaced)

        Args:
            base: Base directory (e.g., Path(".cursor"))
            handle: Parsed resource handle

        Returns:
            Path to the command file
        """
        if not handle.username:
            return base / self._format.command_dir / f"{handle.simple_name}.md"
        return base / self._format.command_dir / handle.username / f"{handle.simple_name}.md"

    def get_agent_path(self, base: Path, handle: ParsedHandle) -> Path:
        """Build the path to an agent file.

        Cursor uses nested paths:
        - base/agents/username/name.md
        - base/agents/name.md (for non-namespaced)

        Args:
            base: Base directory (e.g., Path(".cursor"))
            handle: Parsed resource handle

        Returns:
            Path to the agent file
        """
        if not handle.username:
            return base / self._format.agent_dir / f"{handle.simple_name}.md"
        return base / self._format.agent_dir / handle.username / f"{handle.simple_name}.md"

    def get_rule_path(self, base: Path, handle: ParsedHandle) -> Path:
        """Build the path to a rule file.

        Cursor uses nested paths:
        - base/rules/username/name.md
        - base/rules/name.md (for non-namespaced)

        Args:
            base: Base directory (e.g., Path(".cursor"))
            handle: Parsed resource handle

        Returns:
            Path to the rule file
        """
        if not handle.username:
            return base / self._format.rule_dir / f"{handle.simple_name}.md"
        return base / self._format.rule_dir / handle.username / f"{handle.simple_name}.md"

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
            base: Base directory to search (e.g., Path(".cursor"))

        Returns:
            List of discovered installed resources
        """
        resources = []

        # Discover skills (nested directories)
        skills_dir = base / self._format.skill_dir
        if skills_dir.is_dir():
            for item in skills_dir.iterdir():
                if not item.is_dir():
                    continue
                if self.is_skill_directory(item):
                    resources.append(
                        InstalledResource(
                            name=item.name,
                            resource_type="skill",
                            path=item,
                            username=None,
                        )
                    )
                else:
                    # Username directory containing skills
                    for sub_item in item.iterdir():
                        if self.is_skill_directory(sub_item):
                            resources.append(
                                InstalledResource(
                                    name=sub_item.name,
                                    resource_type="skill",
                                    path=sub_item,
                                    username=item.name,
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
        """Check if the Cursor CLI is available on the system.

        Returns:
            True if the cursor or cursor-agent command is available
        """
        return (
            shutil.which("cursor-agent") is not None
            or shutil.which("cursor") is not None
        )

    def transform_rule_content(self, content: str) -> str:
        """Transform rule content for Cursor format.

        Cursor may need different rule format. For example:
        - Convert paths: frontmatter to globs format
        - Handle Cursor-specific syntax

        Args:
            content: Original rule content

        Returns:
            Transformed rule content for Cursor
        """
        # Transform paths: frontmatter to globs if present
        # Example: paths: ["src/**/*.ts"] -> globs: ["src/**/*.ts"]
        # This is a simple transformation; more complex ones may be needed

        # Check for YAML frontmatter with paths:
        frontmatter_pattern = r"^---\s*\n(.*?)\n---"
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if match:
            frontmatter = match.group(1)
            # Convert paths: to globs: if present
            if "paths:" in frontmatter:
                transformed_frontmatter = frontmatter.replace("paths:", "globs:")
                content = content.replace(frontmatter, transformed_frontmatter)

        return content


# Register the adapter
AdapterRegistry.register("cursor", CursorAdapter)
