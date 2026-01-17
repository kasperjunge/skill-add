"""Remote resource resolution for agr add operations.

This module handles the resolution order for remote resources:
1. Check agr.toml for [resource.*] or [package.*] sections
2. Fallback to .claude/{type}/{name}
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import tomlkit
from tomlkit.exceptions import TOMLKitError

from agr.fetcher import ResourceType


class ResourceSource(Enum):
    """Where a resource was resolved from."""

    AGR_TOML = "agr_toml"  # Explicitly defined in agr.toml
    CLAUDE_DIR = "claude_dir"  # Found in .claude/ directory


@dataclass
class ResolvedResource:
    """A resolved resource with its location and source.

    Attributes:
        name: The resource name
        resource_type: Type of resource (SKILL, COMMAND, AGENT)
        path: Path to the resource (relative to repo root)
        source: Where the resource was resolved from
        is_package: Whether this is a package/bundle
    """

    name: str
    resource_type: ResourceType | None
    path: Path
    source: ResourceSource
    is_package: bool = False


def parse_remote_agr_toml(repo_dir: Path) -> dict[str, dict]:
    """Parse agr.toml from a remote repository for resource/package definitions.

    Looks for [resource.*] and [package.*] sections that define
    where resources are located for publishing.

    Args:
        repo_dir: Path to extracted repository

    Returns:
        Dict mapping resource names to their config:
        {
            "my-skill": {"path": "skills/my-skill", "type": "skill"},
            "my-toolkit": {"path": "packages/my-toolkit", "package": True}
        }
    """
    agr_toml_path = repo_dir / "agr.toml"

    if not agr_toml_path.exists():
        return {}

    try:
        content = agr_toml_path.read_text()
        doc = tomlkit.parse(content)
    except TOMLKitError:
        return {}

    result = {}

    # Parse [resource.*] sections - tomlkit parses dotted keys as nested dicts
    # [resource.my-skill] becomes {"resource": {"my-skill": {...}}}
    resource_section = doc.get("resource", {})
    if isinstance(resource_section, dict):
        for resource_name, value in resource_section.items():
            if isinstance(value, dict):
                result[resource_name] = dict(value)

    # Parse [package.*] sections
    package_section = doc.get("package", {})
    if isinstance(package_section, dict):
        for package_name, value in package_section.items():
            if isinstance(value, dict):
                config = dict(value)
                config["package"] = True
                result[package_name] = config

    return result


def _detect_type_from_path(repo_dir: Path, path: Path) -> ResourceType | None:
    """Detect resource type from a path.

    Args:
        repo_dir: Path to repository root
        path: Path to the resource (relative to repo root)

    Returns:
        ResourceType if detected, None otherwise
    """
    full_path = repo_dir / path

    # Check if it's a skill (directory with SKILL.md)
    if full_path.is_dir() and (full_path / "SKILL.md").exists():
        return ResourceType.SKILL

    # Check if it's a command or agent (.md file)
    if full_path.is_file() and full_path.suffix == ".md":
        # Could be command or agent - would need context to determine
        # Default to command for now
        return ResourceType.COMMAND

    return None


def _resolve_from_agr_toml(
    repo_dir: Path, name: str, resources: dict[str, dict]
) -> ResolvedResource | None:
    """Try to resolve a resource from agr.toml definitions.

    Args:
        repo_dir: Path to repository root
        name: Resource name to look for
        resources: Parsed resource definitions from agr.toml

    Returns:
        ResolvedResource if found in agr.toml, None otherwise
    """
    if name not in resources:
        return None

    config = resources[name]
    path_str = config.get("path")
    if not path_str:
        return None

    path = Path(path_str)
    is_package = config.get("package", False)

    # Determine resource type
    type_str = config.get("type")
    if type_str:
        type_map = {
            "skill": ResourceType.SKILL,
            "command": ResourceType.COMMAND,
            "agent": ResourceType.AGENT,
        }
        resource_type = type_map.get(type_str)
    else:
        resource_type = _detect_type_from_path(repo_dir, path)

    return ResolvedResource(
        name=name,
        resource_type=resource_type,
        path=path,
        source=ResourceSource.AGR_TOML,
        is_package=is_package,
    )


def _resolve_from_claude_dir(repo_dir: Path, name: str) -> ResolvedResource | None:
    """Try to resolve a resource from .claude/ directory.

    Checks in order:
    1. .claude/skills/{name}/SKILL.md
    2. .claude/commands/{name}.md
    3. .claude/agents/{name}.md
    4. Bundle: .claude/skills/{name}/*/SKILL.md (nested directories)

    Args:
        repo_dir: Path to repository root
        name: Resource name to look for

    Returns:
        ResolvedResource if found in .claude/, None otherwise
    """
    claude_dir = repo_dir / ".claude"

    # Check for skill
    skill_path = claude_dir / "skills" / name
    if skill_path.is_dir() and (skill_path / "SKILL.md").exists():
        return ResolvedResource(
            name=name,
            resource_type=ResourceType.SKILL,
            path=Path(".claude/skills") / name,
            source=ResourceSource.CLAUDE_DIR,
        )

    # Check for command
    command_path = claude_dir / "commands" / f"{name}.md"
    if command_path.is_file():
        return ResolvedResource(
            name=name,
            resource_type=ResourceType.COMMAND,
            path=Path(".claude/commands") / f"{name}.md",
            source=ResourceSource.CLAUDE_DIR,
        )

    # Check for agent
    agent_path = claude_dir / "agents" / f"{name}.md"
    if agent_path.is_file():
        return ResolvedResource(
            name=name,
            resource_type=ResourceType.AGENT,
            path=Path(".claude/agents") / f"{name}.md",
            source=ResourceSource.CLAUDE_DIR,
        )

    # Check for bundle (directory with nested resources)
    # A bundle exists if there are subdirectories with resources in skills/
    bundle_skills_path = claude_dir / "skills" / name
    if bundle_skills_path.is_dir():
        # Check if any subdirectory has SKILL.md (making it a bundle)
        for subdir in bundle_skills_path.iterdir():
            if subdir.is_dir() and (subdir / "SKILL.md").exists():
                return ResolvedResource(
                    name=name,
                    resource_type=None,  # Bundles don't have a single type
                    path=Path(".claude/skills") / name,
                    source=ResourceSource.CLAUDE_DIR,
                    is_package=True,
                )

    # Check for bundle in commands/
    bundle_commands_path = claude_dir / "commands" / name
    if bundle_commands_path.is_dir():
        # Check if directory contains .md files
        md_files = list(bundle_commands_path.glob("*.md"))
        if md_files:
            return ResolvedResource(
                name=name,
                resource_type=None,
                path=Path(".claude/commands") / name,
                source=ResourceSource.CLAUDE_DIR,
                is_package=True,
            )

    # Check for bundle in agents/
    bundle_agents_path = claude_dir / "agents" / name
    if bundle_agents_path.is_dir():
        md_files = list(bundle_agents_path.glob("*.md"))
        if md_files:
            return ResolvedResource(
                name=name,
                resource_type=None,
                path=Path(".claude/agents") / name,
                source=ResourceSource.CLAUDE_DIR,
                is_package=True,
            )

    return None


def resolve_remote_resource(repo_dir: Path, name: str) -> ResolvedResource | None:
    """Resolve a resource reference in a remote repository.

    Resolution order:
    1. Check agr.toml for [resource.{name}] or [package.{name}]
    2. Fallback to .claude/{type}/{name}

    Args:
        repo_dir: Path to extracted repository
        name: Resource name to resolve

    Returns:
        ResolvedResource with path, type, and source, or None if not found
    """
    # First, check agr.toml
    agr_resources = parse_remote_agr_toml(repo_dir)
    resolved = _resolve_from_agr_toml(repo_dir, name, agr_resources)
    if resolved:
        return resolved

    # Fallback to .claude/ directory
    return _resolve_from_claude_dir(repo_dir, name)
