"""Centralized handle parsing and conversion for agr.

This module provides a single source of truth for parsing and converting
resource handles between different formats used in the codebase:

| System          | Format    | Example                                | Used In                  |
|-----------------|-----------|----------------------------------------|--------------------------|
| External/Config | Slash `/` | `kasperjunge/seo`                      | agr.toml, CLI input      |
| Internal/Storage| Colon `:` | `kasperjunge:seo`                      | Skill directories on disk|

All code paths that need to parse or convert handles should use this module.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParsedHandle:
    """Parsed resource handle with all components.

    Attributes:
        username: GitHub username (e.g., "kasperjunge"), None for simple names
        repo: Repository name (e.g., "agent-resources"), None if using default
        name: Resource name (the final/leaf segment)
        path_segments: Full list of path segments after username
                       e.g., ["seo"] or ["product-strategy", "growth-hacker"]
    """

    username: str | None = None
    repo: str | None = None
    name: str = ""
    path_segments: list[str] = field(default_factory=list)

    @property
    def simple_name(self) -> str:
        """Just the resource name (last segment)."""
        return self.path_segments[-1] if self.path_segments else self.name

    def to_toml_handle(self) -> str:
        """Convert to agr.toml format: user/name or user/repo/name.

        Examples:
            >>> ParsedHandle(username="kasperjunge", name="seo", path_segments=["seo"]).to_toml_handle()
            'kasperjunge/seo'
            >>> ParsedHandle(username="user", repo="repo", name="cmd", path_segments=["cmd"]).to_toml_handle()
            'user/repo/cmd'
            >>> ParsedHandle(username="k", name="g", path_segments=["product-strategy", "growth-hacker"]).to_toml_handle()
            'k/product-strategy/growth-hacker'
        """
        if not self.username:
            return self.name

        if self.repo:
            # With explicit repo: user/repo/path_segments
            parts = [self.username, self.repo] + self.path_segments
            return "/".join(parts)

        # Without repo: user/path_segments
        return f"{self.username}/{'/'.join(self.path_segments)}"

    def to_skill_dirname(self) -> str:
        """Convert to skill directory name: user:name or user:nested:name.

        Skills use a flattened colon-separated format for directory names
        because Claude Code only discovers top-level directories in .claude/skills/.

        Examples:
            >>> ParsedHandle(username="kasperjunge", name="seo", path_segments=["seo"]).to_skill_dirname()
            'kasperjunge:seo'
            >>> ParsedHandle(username="k", name="g", path_segments=["product-strategy", "growth-hacker"]).to_skill_dirname()
            'k:product-strategy:growth-hacker'
        """
        if not self.username:
            return self.name

        parts = [self.username] + self.path_segments
        return ":".join(parts)

    def matches_toml_handle(self, toml_handle: str) -> bool:
        """Check if this parsed handle matches a handle from agr.toml.

        Matching is done by comparing:
        1. Simple names must be equal
        2. If both have usernames, they must match
        3. If one has no username, match by simple name only

        Examples:
            >>> parse_handle("kasperjunge/seo").matches_toml_handle("kasperjunge/seo")
            True
            >>> parse_handle("seo").matches_toml_handle("kasperjunge/seo")
            True
            >>> parse_handle("other/seo").matches_toml_handle("kasperjunge/seo")
            False
        """
        other = parse_handle(toml_handle)

        # Match if simple names are equal and usernames match (if both present)
        if self.simple_name != other.simple_name:
            return False

        if self.username and other.username:
            return self.username == other.username

        return True

    def to_skill_path(self, base_path: Path) -> Path:
        """Build skill path: base_path/skills/{username}:{segments} or base_path/skills/{name}.

        Examples:
            >>> ParsedHandle(username="kasperjunge", name="seo", path_segments=["seo"]).to_skill_path(Path(".claude"))
            PosixPath('.claude/skills/kasperjunge:seo')
            >>> ParsedHandle(name="seo", path_segments=["seo"]).to_skill_path(Path(".claude"))
            PosixPath('.claude/skills/seo')
        """
        if not self.username:
            return base_path / "skills" / self.name
        return base_path / "skills" / self.to_skill_dirname()

    def _to_nested_md_path(self, base_path: Path, type_dir: str) -> Path:
        """Build nested path for .md file resources (commands, agents, rules).

        Args:
            base_path: Base directory (e.g., Path(".claude"))
            type_dir: Type subdirectory name (e.g., "commands", "agents", "rules")

        Returns:
            Path in format: base_path/{type_dir}/{username}/{nested_dirs}/{name}.md
        """
        filename = f"{self.simple_name}.md"
        if not self.username:
            return base_path / type_dir / filename
        nested_dirs = self.path_segments[:-1] if self.path_segments else []
        if nested_dirs:
            return base_path / type_dir / self.username / Path(*nested_dirs) / filename
        return base_path / type_dir / self.username / filename

    def to_command_path(self, base_path: Path) -> Path:
        """Build command path: base_path/commands/{username}/{path}/{name}.md or base_path/commands/{name}.md.

        Includes full path_segments for nested directory structure.

        Examples:
            >>> ParsedHandle(username="kasperjunge", name="commit", path_segments=["commit"]).to_command_path(Path(".claude"))
            PosixPath('.claude/commands/kasperjunge/commit.md')
            >>> ParsedHandle(name="commit", path_segments=["commit"]).to_command_path(Path(".claude"))
            PosixPath('.claude/commands/commit.md')
            >>> ParsedHandle(username="user", name="deploy", path_segments=["pkg", "infra", "deploy"]).to_command_path(Path(".claude"))
            PosixPath('.claude/commands/user/pkg/infra/deploy.md')
        """
        return self._to_nested_md_path(base_path, "commands")

    def to_agent_path(self, base_path: Path) -> Path:
        """Build agent path: base_path/agents/{username}/{path}/{name}.md or base_path/agents/{name}.md.

        Includes full path_segments for nested directory structure.

        Examples:
            >>> ParsedHandle(username="kasperjunge", name="reviewer", path_segments=["reviewer"]).to_agent_path(Path(".claude"))
            PosixPath('.claude/agents/kasperjunge/reviewer.md')
            >>> ParsedHandle(name="reviewer", path_segments=["reviewer"]).to_agent_path(Path(".claude"))
            PosixPath('.claude/agents/reviewer.md')
            >>> ParsedHandle(username="user", name="deploy", path_segments=["pkg", "infra", "deploy"]).to_agent_path(Path(".claude"))
            PosixPath('.claude/agents/user/pkg/infra/deploy.md')
        """
        return self._to_nested_md_path(base_path, "agents")

    def to_rule_path(self, base_path: Path) -> Path:
        """Build rule path: base_path/rules/{username}/{path}/{name}.md or base_path/rules/{name}.md.

        Includes full path_segments for nested directory structure.

        Examples:
            >>> ParsedHandle(username="kasperjunge", name="no-console", path_segments=["no-console"]).to_rule_path(Path(".claude"))
            PosixPath('.claude/rules/kasperjunge/no-console.md')
            >>> ParsedHandle(name="no-console", path_segments=["no-console"]).to_rule_path(Path(".claude"))
            PosixPath('.claude/rules/no-console.md')
            >>> ParsedHandle(username="user", name="lint", path_segments=["pkg", "code", "lint"]).to_rule_path(Path(".claude"))
            PosixPath('.claude/rules/user/pkg/code/lint.md')
        """
        return self._to_nested_md_path(base_path, "rules")

    def to_resource_path(self, base_path: Path, resource_type: str) -> Path:
        """Build resource path based on type (skill, command, agent, rule).

        Args:
            base_path: Base directory (e.g., Path(".claude"))
            resource_type: One of "skill", "command", "agent", "rule"

        Returns:
            Path to the resource

        Raises:
            ValueError: If resource_type is not one of skill, command, agent, rule
        """
        builders = {
            "skill": self.to_skill_path,
            "command": self.to_command_path,
            "agent": self.to_agent_path,
            "rule": self.to_rule_path,
        }
        if resource_type not in builders:
            raise ValueError(f"Unknown resource type: {resource_type}")
        return builders[resource_type](base_path)

    @classmethod
    def from_components(
        cls,
        username: str,
        name: str,
        path_segments: list[str] | None = None,
        repo: str | None = None,
    ) -> "ParsedHandle":
        """Factory method for creating ParsedHandle from components.

        Args:
            username: GitHub username
            name: Resource name
            path_segments: Optional path segments (defaults to [name])
            repo: Optional repository name

        Returns:
            ParsedHandle instance

        Examples:
            >>> ParsedHandle.from_components("kasperjunge", "seo")
            ParsedHandle(username='kasperjunge', repo=None, name='seo', path_segments=['seo'])
        """
        segments = path_segments if path_segments is not None else [name]
        return cls(username=username, repo=repo, name=name, path_segments=segments)


def parse_handle(handle: str) -> ParsedHandle:
    """Parse any handle format into normalized components.

    Supports:
    - "name" -> simple name
    - "user/name" -> 2-part slash format (config/CLI)
    - "user/repo/name" -> 3-part slash format
    - "user/nested/name" -> multi-part slash format
    - "user:name" -> colon format (from filesystem)
    - "user:nested:name" -> nested colon format

    Args:
        handle: The handle string to parse

    Returns:
        ParsedHandle with all components extracted

    Examples:
        >>> parse_handle("seo").name
        'seo'
        >>> h = parse_handle("kasperjunge/seo")
        >>> (h.username, h.name)
        ('kasperjunge', 'seo')
        >>> h = parse_handle("kasperjunge:seo")
        >>> (h.username, h.name, h.to_toml_handle())
        ('kasperjunge', 'seo', 'kasperjunge/seo')
    """
    if not handle:
        return ParsedHandle(name="")

    # Colon format (filesystem): user:name or user:nested:name
    if ":" in handle and "/" not in handle:
        parts = handle.split(":")
        return ParsedHandle(
            username=parts[0],
            name=parts[-1],
            path_segments=parts[1:],
        )

    # Slash format (config/CLI): user/name or user/repo/name or user/nested/name
    if "/" in handle:
        parts = handle.split("/")

        if len(parts) == 2:
            # user/name
            return ParsedHandle(
                username=parts[0],
                name=parts[1],
                path_segments=[parts[1]],
            )

        # For 3+ parts, we store all segments after username in path_segments
        # This allows proper round-trip conversion for skill dirnames.
        # The repo field is only set when explicitly needed for GitHub URLs,
        # but for skill dirname purposes, path_segments is what matters.
        if len(parts) >= 3:
            return ParsedHandle(
                username=parts[0],
                name=parts[-1],
                path_segments=parts[1:],
            )

    # Simple name
    return ParsedHandle(name=handle, path_segments=[handle])


def skill_dirname_to_toml_handle(dirname: str) -> str:
    """Convert skill directory name back to agr.toml handle format.

    Args:
        dirname: The skill directory name (e.g., "kasperjunge:seo")

    Returns:
        The toml handle format (e.g., "kasperjunge/seo")

    Examples:
        >>> skill_dirname_to_toml_handle("kasperjunge:seo")
        'kasperjunge/seo'
        >>> skill_dirname_to_toml_handle("k:product-strategy:growth-hacker")
        'k/product-strategy/growth-hacker'
    """
    parsed = parse_handle(dirname)
    return parsed.to_toml_handle()


def toml_handle_to_skill_dirname(toml_handle: str) -> str:
    """Convert agr.toml handle to skill directory name format.

    Args:
        toml_handle: The toml handle (e.g., "kasperjunge/seo")

    Returns:
        The skill directory name (e.g., "kasperjunge:seo")

    Examples:
        >>> toml_handle_to_skill_dirname("kasperjunge/seo")
        'kasperjunge:seo'
        >>> toml_handle_to_skill_dirname("k/product-strategy/growth-hacker")
        'k:product-strategy:growth-hacker'
    """
    parsed = parse_handle(toml_handle)
    return parsed.to_skill_dirname()
