"""Resource type detection based on path patterns."""

import glob as glob_module
from enum import Enum
from pathlib import Path


class ResourceType(Enum):
    """Type of resource."""

    SKILL = "skill"
    COMMAND = "command"
    AGENT = "agent"


def _path_contains_segment(path_str: str, segment: str) -> bool:
    """Check if a path contains a specific directory segment."""
    return f"/{segment}/" in path_str or path_str.startswith(f"{segment}/")


def detect_resource_type(path: Path) -> ResourceType | None:
    """Detect resource type from path based on parent directory naming.

    The type is determined by the presence of /skills/, /commands/, or /agents/
    in the path. For skills, the directory must contain SKILL.md.
    For commands and agents, the path must be a .md file.

    Args:
        path: Path to the resource

    Returns:
        Detected ResourceType, or None if type cannot be determined

    Examples:
        >>> detect_resource_type(Path("./skills/my-skill/"))
        ResourceType.SKILL
        >>> detect_resource_type(Path("./commands/my-cmd.md"))
        ResourceType.COMMAND
    """
    path_str = str(path)
    is_planning_path = not path.exists() and not path.suffix

    if _path_contains_segment(path_str, "skills"):
        if path.is_dir() and (path / "SKILL.md").exists():
            return ResourceType.SKILL
        if is_planning_path:
            return ResourceType.SKILL

    elif _path_contains_segment(path_str, "commands"):
        if path.suffix == ".md" or is_planning_path:
            return ResourceType.COMMAND

    elif _path_contains_segment(path_str, "agents"):
        if path.suffix == ".md" or is_planning_path:
            return ResourceType.AGENT

    return None


def detect_package_root(path: Path) -> Path | None:
    """Detect the root of a package by looking for resource subdirectories.

    A package root is a directory that contains one or more of:
    - skills/ subdirectory
    - commands/ subdirectory
    - agents/ subdirectory

    Args:
        path: Path to check

    Returns:
        Path to the package root if found, None otherwise
    """
    if not path.is_dir():
        return None

    # Check if this directory has resource subdirectories
    has_skills = (path / "skills").is_dir()
    has_commands = (path / "commands").is_dir()
    has_agents = (path / "agents").is_dir()

    if has_skills or has_commands or has_agents:
        return path

    return None


def is_package(path: Path) -> bool:
    """Check if a path is a package (has resource subdirectories).

    Args:
        path: Path to check

    Returns:
        True if the path is a package directory
    """
    return detect_package_root(path) is not None


def expand_glob_patterns(base: Path, patterns: list[str]) -> list[Path]:
    """Expand glob patterns relative to a base directory.

    Args:
        base: Base directory for relative patterns
        patterns: List of glob patterns

    Returns:
        List of matched paths, sorted alphabetically

    Examples:
        >>> expand_glob_patterns(Path("./my-toolkit"), ["skills/*/"])
        [Path("./my-toolkit/skills/analyzer/"), Path("./my-toolkit/skills/helper/")]
    """
    results: list[Path] = []

    for pattern in patterns:
        # Handle both relative and absolute patterns
        if Path(pattern).is_absolute():
            full_pattern = pattern
        else:
            full_pattern = str(base / pattern)

        # Expand the glob
        for match in glob_module.glob(full_pattern, recursive=True):
            match_path = Path(match)
            if match_path not in results:
                results.append(match_path)

    return sorted(results)


def discover_resources_in_directory(
    path: Path,
) -> dict[ResourceType, list[Path]]:
    """Discover all resources in a directory.

    Scans a directory for skills, commands, and agents based on
    the standard .claude directory structure.

    Args:
        path: Directory to scan

    Returns:
        Dictionary mapping ResourceType to list of resource paths
    """
    results: dict[ResourceType, list[Path]] = {
        ResourceType.SKILL: [],
        ResourceType.COMMAND: [],
        ResourceType.AGENT: [],
    }

    if not path.is_dir():
        return results

    # Check for skills
    skills_dir = path / "skills"
    if skills_dir.is_dir():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                results[ResourceType.SKILL].append(skill_dir)

    # Check for commands
    commands_dir = path / "commands"
    if commands_dir.is_dir():
        for cmd_file in commands_dir.glob("*.md"):
            results[ResourceType.COMMAND].append(cmd_file)

    # Check for agents
    agents_dir = path / "agents"
    if agents_dir.is_dir():
        for agent_file in agents_dir.glob("*.md"):
            results[ResourceType.AGENT].append(agent_file)

    return results


def discover_package_resources(
    package_path: Path,
    skill_patterns: list[str] | None = None,
    command_patterns: list[str] | None = None,
    agent_patterns: list[str] | None = None,
) -> dict[ResourceType, list[Path]]:
    """Discover resources in a package using optional glob patterns.

    If patterns are provided, use them. Otherwise, use default discovery.

    Args:
        package_path: Path to the package root
        skill_patterns: Optional glob patterns for skills
        command_patterns: Optional glob patterns for commands
        agent_patterns: Optional glob patterns for agents

    Returns:
        Dictionary mapping ResourceType to list of resource paths
    """
    results: dict[ResourceType, list[Path]] = {
        ResourceType.SKILL: [],
        ResourceType.COMMAND: [],
        ResourceType.AGENT: [],
    }

    if skill_patterns:
        for path in expand_glob_patterns(package_path, skill_patterns):
            if path.is_dir() and (path / "SKILL.md").exists():
                results[ResourceType.SKILL].append(path)
    else:
        skills_dir = package_path / "skills"
        if skills_dir.is_dir():
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    results[ResourceType.SKILL].append(skill_dir)

    if command_patterns:
        for path in expand_glob_patterns(package_path, command_patterns):
            if path.is_file() and path.suffix == ".md":
                results[ResourceType.COMMAND].append(path)
    else:
        commands_dir = package_path / "commands"
        if commands_dir.is_dir():
            results[ResourceType.COMMAND].extend(commands_dir.glob("*.md"))

    if agent_patterns:
        for path in expand_glob_patterns(package_path, agent_patterns):
            if path.is_file() and path.suffix == ".md":
                results[ResourceType.AGENT].append(path)
    else:
        agents_dir = package_path / "agents"
        if agents_dir.is_dir():
            results[ResourceType.AGENT].extend(agents_dir.glob("*.md"))

    # Sort all results
    for resource_type in results:
        results[resource_type] = sorted(results[resource_type])

    return results
