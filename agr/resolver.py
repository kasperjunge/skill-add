"""Remote resource resolution for agr add operations.

This module handles the resolution order for remote resources:
1. Check agr.toml dependencies array for entries with "path" key
2. Fallback to .claude/{type}/{name}
3. Auto-discover recognizable resources anywhere in repo (skills, commands, agents)
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import tomlkit
from tomlkit.exceptions import TOMLKitError

from agr.constants import TOOL_DIR_NAME, SKILLS_SUBDIR, COMMANDS_SUBDIR, AGENTS_SUBDIR
from agr.fetcher import ResourceType
from agr.package import parse_package_md


def _find_package_context_in_repo(repo_dir: Path, resource_path: Path) -> str | None:
    """Walk up from resource_path looking for PACKAGE.md within repo_dir.

    Args:
        repo_dir: Path to extracted repository (boundary)
        resource_path: Path to the resource (relative to repo_dir)

    Returns:
        Package name from PACKAGE.md if found, None otherwise
    """
    repo_dir = repo_dir.resolve()
    full_resource_path = (repo_dir / resource_path).resolve()
    current = full_resource_path if full_resource_path.is_dir() else full_resource_path.parent

    while current != current.parent:
        if current == repo_dir or not str(current).startswith(str(repo_dir)):
            break

        package_md = current / "PACKAGE.md"
        if package_md.exists():
            metadata = parse_package_md(package_md)
            if metadata.valid and metadata.name:
                return metadata.name
            return None

        current = current.parent

    return None


class ResourceSource(Enum):
    """Where a resource was resolved from."""

    AGR_TOML = "agr_toml"  # Explicitly defined in agr.toml
    CLAUDE_DIR = "claude_dir"  # Found in .claude/ directory
    REPO_ROOT = "repo_root"  # Auto-discovered anywhere in repo


@dataclass
class ResolvedResource:
    """A resolved resource with its location and source.

    Attributes:
        name: The resource name
        resource_type: Type of resource (SKILL, COMMAND, AGENT)
        path: Path to the resource (relative to repo root)
        source: Where the resource was resolved from
        is_package: Whether this is a package/bundle
        package_name: Package context from PACKAGE.md if found
    """

    name: str
    resource_type: ResourceType | None
    path: Path
    source: ResourceSource
    is_package: bool = False
    package_name: str | None = None


def _extract_resource_name(path_str: str) -> str:
    """Extract resource name from a path.

    Examples:
        "resources/commands/hello-world.md" -> "hello-world"
        "resources/skills/commit" -> "commit"
        "resources/packages/python-dev" -> "python-dev"
        "resources/skills/product-strategy/growth-hacker" -> "product-strategy:growth-hacker"

    For nested paths (more than one segment after the type dir),
    joins with colons to create colon-delimited names.

    Args:
        path_str: Path string from agr.toml dependencies

    Returns:
        Resource name (with colons for nested paths)
    """
    p = Path(path_str)

    # Remove .md extension if present
    if p.suffix == ".md":
        p = p.with_suffix("")

    # Get path parts after "resources/{type}/"
    parts = p.parts

    # Find the index after "resources" and the type directory
    # e.g., ("resources", "skills", "product-strategy", "growth-hacker")
    #        -> ["product-strategy", "growth-hacker"]
    if len(parts) >= 3 and parts[0] == "resources":
        # Skip "resources" and the type directory (skills/commands/agents/packages)
        name_parts = parts[2:]
    elif len(parts) >= 2:
        # Fallback: just use last segments
        name_parts = parts[1:]
    else:
        # Single segment, just use the name
        name_parts = (p.name,)

    # Join with colons for nested paths
    return ":".join(name_parts)


def parse_remote_agr_toml(repo_dir: Path) -> dict[str, dict]:
    """Parse agr.toml dependencies for resources available for remote install.

    Reads the dependencies array and extracts entries with "path" key,
    which represent local resources that can be installed remotely.
    Entries with "handle" key are remote dependencies and are skipped.

    Args:
        repo_dir: Path to extracted repository

    Returns:
        Dict mapping resource names to their config:
        {
            "hello-world": {"path": "resources/commands/hello-world.md", "type": "command"},
            "commit": {"path": "resources/skills/commit", "type": "skill"},
            "product-strategy:growth-hacker": {"path": "resources/skills/product-strategy/growth-hacker", "type": "skill"},
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

    dependencies = doc.get("dependencies", [])
    if not isinstance(dependencies, list):
        return {}

    result = {}

    for dep in dependencies:
        if not isinstance(dep, dict):
            continue

        # Only entries with "path" are local resources (available for install)
        # Entries with "handle" are remote dependencies (skip)
        if "path" not in dep or "handle" in dep:
            continue

        path_str = dep["path"]
        resource_type = dep.get("type")
        is_package = resource_type == "package"

        # Extract name from path
        name = _extract_resource_name(path_str)

        result[name] = {
            "path": path_str,
            "type": resource_type,
            "package": is_package,
        }

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

    # Check for package context
    package_name = _find_package_context_in_repo(repo_dir, path)

    return ResolvedResource(
        name=name,
        resource_type=resource_type,
        path=path,
        source=ResourceSource.AGR_TOML,
        is_package=is_package,
        package_name=package_name,
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
    claude_dir = repo_dir / TOOL_DIR_NAME

    # Check for skill
    skill_path = claude_dir / SKILLS_SUBDIR / name
    if skill_path.is_dir() and (skill_path / "SKILL.md").exists():
        rel_path = Path(TOOL_DIR_NAME) / SKILLS_SUBDIR / name
        package_name = _find_package_context_in_repo(repo_dir, rel_path)
        return ResolvedResource(
            name=name,
            resource_type=ResourceType.SKILL,
            path=rel_path,
            source=ResourceSource.CLAUDE_DIR,
            package_name=package_name,
        )

    # Check for command
    command_path = claude_dir / COMMANDS_SUBDIR / f"{name}.md"
    if command_path.is_file():
        rel_path = Path(TOOL_DIR_NAME) / COMMANDS_SUBDIR / f"{name}.md"
        package_name = _find_package_context_in_repo(repo_dir, rel_path)
        return ResolvedResource(
            name=name,
            resource_type=ResourceType.COMMAND,
            path=rel_path,
            source=ResourceSource.CLAUDE_DIR,
            package_name=package_name,
        )

    # Check for agent
    agent_path = claude_dir / AGENTS_SUBDIR / f"{name}.md"
    if agent_path.is_file():
        rel_path = Path(TOOL_DIR_NAME) / AGENTS_SUBDIR / f"{name}.md"
        package_name = _find_package_context_in_repo(repo_dir, rel_path)
        return ResolvedResource(
            name=name,
            resource_type=ResourceType.AGENT,
            path=rel_path,
            source=ResourceSource.CLAUDE_DIR,
            package_name=package_name,
        )

    # Check for bundles (directories with nested resources)
    # Bundles don't inherit package context - they are the grouping themselves
    bundle_checks = [
        (SKILLS_SUBDIR, lambda p: any(s.is_dir() and (s / "SKILL.md").exists() for s in p.iterdir())),
        (COMMANDS_SUBDIR, lambda p: any(p.glob("*.md"))),
        (AGENTS_SUBDIR, lambda p: any(p.glob("*.md"))),
    ]
    for subdir, has_resources in bundle_checks:
        bundle_path = claude_dir / subdir / name
        if bundle_path.is_dir() and has_resources(bundle_path):
            return ResolvedResource(
                name=name,
                resource_type=None,
                path=Path(TOOL_DIR_NAME) / subdir / name,
                source=ResourceSource.CLAUDE_DIR,
                is_package=True,
                package_name=None,
            )

    return None


def _resolve_from_repo_root(repo_dir: Path, name: str) -> ResolvedResource | None:
    """Auto-discover resource anywhere in repo (third fallback).

    The `name` may contain colons for nested paths (e.g., "tools:git").
    These get converted to directory paths for searching.

    Uses directory-based detection:
    - Skills: {path_segments}/SKILL.md (directory with SKILL.md)
    - Commands: **/commands/{path_segments}.md
    - Agents: **/agents/{path_segments}.md

    Note: Packages are NOT auto-discovered; they must be declared in agr.toml.

    Args:
        repo_dir: Path to repository root
        name: Resource name (may contain colons for nested paths)

    Returns:
        ResolvedResource if found, None otherwise
    """
    # Convert colon-separated name to path segments
    # e.g., "tools:git" -> ["tools", "git"]
    path_segments = name.split(":") if ":" in name else [name]
    simple_name = path_segments[-1]  # Last segment is the actual resource name

    # Build the relative path from segments
    # For skills: tools/git/SKILL.md
    # For commands/agents: commands/tools/git.md or agents/tools/git.md
    nested_path = Path(*path_segments)

    # 1. Check for skill at exact path: {nested_path}/SKILL.md
    skill_path = repo_dir / nested_path
    if skill_path.is_dir() and (skill_path / "SKILL.md").exists():
        package_name = _find_package_context_in_repo(repo_dir, nested_path)
        return ResolvedResource(
            name=name,
            resource_type=ResourceType.SKILL,
            path=nested_path,
            source=ResourceSource.REPO_ROOT,
            package_name=package_name,
        )

    # 2. Search for skill anywhere in repo: **/{nested_path}/SKILL.md
    # Use rglob to find the pattern anywhere
    search_pattern = str(nested_path / "SKILL.md")
    for skill_md in repo_dir.rglob(search_pattern):
        # Skip .claude/ directory (already handled in fallback 2)
        rel_path = skill_md.parent.relative_to(repo_dir)
        if str(rel_path).startswith(TOOL_DIR_NAME):
            continue
        package_name = _find_package_context_in_repo(repo_dir, rel_path)
        return ResolvedResource(
            name=name,
            resource_type=ResourceType.SKILL,
            path=rel_path,
            source=ResourceSource.REPO_ROOT,
            package_name=package_name,
        )

    # 3. Check for command in commands/ directory
    # Build path: commands/{path_segments[:-1]}/{simple_name}.md
    if len(path_segments) > 1:
        cmd_rel_path = Path(COMMANDS_SUBDIR, *path_segments[:-1], f"{simple_name}.md")
    else:
        cmd_rel_path = Path(COMMANDS_SUBDIR, f"{simple_name}.md")

    for cmd_path in repo_dir.rglob(str(cmd_rel_path)):
        rel_path = cmd_path.relative_to(repo_dir)
        # Skip .claude/ directory
        if str(rel_path).startswith(TOOL_DIR_NAME):
            continue
        package_name = _find_package_context_in_repo(repo_dir, rel_path)
        return ResolvedResource(
            name=name,
            resource_type=ResourceType.COMMAND,
            path=rel_path,
            source=ResourceSource.REPO_ROOT,
            package_name=package_name,
        )

    # 4. Check for agent in agents/ directory
    if len(path_segments) > 1:
        agent_rel_path = Path(AGENTS_SUBDIR, *path_segments[:-1], f"{simple_name}.md")
    else:
        agent_rel_path = Path(AGENTS_SUBDIR, f"{simple_name}.md")

    for agent_path in repo_dir.rglob(str(agent_rel_path)):
        rel_path = agent_path.relative_to(repo_dir)
        # Skip .claude/ directory
        if str(rel_path).startswith(TOOL_DIR_NAME):
            continue
        package_name = _find_package_context_in_repo(repo_dir, rel_path)
        return ResolvedResource(
            name=name,
            resource_type=ResourceType.AGENT,
            path=rel_path,
            source=ResourceSource.REPO_ROOT,
            package_name=package_name,
        )

    return None


def resolve_remote_resource(repo_dir: Path, name: str) -> ResolvedResource | None:
    """Resolve a resource reference in a remote repository.

    Resolution order:
    1. Check agr.toml for [resource.{name}] or [package.{name}]
    2. Fallback to .claude/{type}/{name}
    3. Auto-discover anywhere in repo (skills, commands, agents)

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

    # Second, fallback to .claude/ directory
    resolved = _resolve_from_claude_dir(repo_dir, name)
    if resolved:
        return resolved

    # Third, auto-discover anywhere in repo
    return _resolve_from_repo_root(repo_dir, name)
