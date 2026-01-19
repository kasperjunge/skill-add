"""Local resource discovery for agr CLI commands."""

from pathlib import Path

from agr.fetcher import (
    DiscoveredResource,
    DiscoveryResult,
    RESOURCE_CONFIGS,
    ResourceType,
)
from agr.handle import parse_handle, ParsedHandle

from agr.cli.paths import get_base_path


def discover_local_resource_type(name: str, global_install: bool) -> DiscoveryResult:
    """
    Discover which resource types exist locally for a given name.

    Searches namespaced paths (flattened colon format for skills, nested for commands/agents)
    and flat paths (.claude/skills/name/) for backward compatibility.

    The name can be:
    - Simple name: "commit" - searches all usernames and flat path
    - Full ref: "kasperjunge/commit" - searches specific username only
    - Colon format: "kasperjunge:commit" - parsed and searched

    Args:
        name: Resource name, full ref (username/name), or colon format to search for
        global_install: If True, search in ~/.claude/, else in ./.claude/

    Returns:
        DiscoveryResult with list of found resource types
    """
    result = DiscoveryResult()
    base_path = get_base_path(global_install)
    parsed = parse_handle(name)

    # Search namespaced paths (handles both flattened skills and nested commands/agents)
    # This function now properly parses the input to extract username and simple_name
    _discover_in_all_namespaces(base_path, name, result)

    # Then check flat paths (.claude/skills/name/) for backward compat
    _discover_in_flat_path(base_path, parsed.simple_name, result)

    return result


def _discover_in_namespace(
    base_path: Path,
    name: str,
    username: str,
    result: DiscoveryResult,
) -> None:
    """Discover resources in a specific username namespace.

    Skills use flattened colon format (e.g., "kasperjunge:seo").
    Commands, agents, and rules use nested format (e.g., "username/name.md").
    """
    handle = ParsedHandle.from_components(username, name)

    # Check for skill (flattened colon format or legacy nested)
    skill_path = handle.to_skill_path(base_path)
    legacy_skill_path = base_path / "skills" / username / name
    if (skill_path.is_dir() and (skill_path / "SKILL.md").exists()) or \
       (legacy_skill_path.is_dir() and (legacy_skill_path / "SKILL.md").exists()):
        result.resources.append(
            DiscoveredResource(
                name=name,
                resource_type=ResourceType.SKILL,
                path_segments=[name],
                username=username,
            )
        )

    # Check file-based resources (command, agent, rule)
    file_checks = [
        (handle.to_command_path(base_path), ResourceType.COMMAND),
        (handle.to_agent_path(base_path), ResourceType.AGENT),
        (handle.to_rule_path(base_path), ResourceType.RULE),
    ]
    for path, resource_type in file_checks:
        if path.is_file():
            result.resources.append(
                DiscoveredResource(
                    name=name,
                    resource_type=resource_type,
                    path_segments=[name],
                    username=username,
                )
            )


def _discover_in_all_namespaces(
    base_path: Path,
    name: str,
    result: DiscoveryResult,
) -> None:
    """Discover resources across all username namespaces.

    Skills are stored in flattened colon format (e.g., "kasperjunge:seo").
    Commands and agents use nested directory format (e.g., "username/name.md").
    """
    # Parse input to get components
    parsed_input = parse_handle(name)
    target_name = parsed_input.simple_name
    target_username = parsed_input.username

    # Check skills - stored with flattened colon names at top level
    skills_dir = base_path / "skills"
    if skills_dir.is_dir():
        for item in skills_dir.iterdir():
            if not item.is_dir():
                continue

            # Check for flattened colon format: "username:name" or "username:nested:name"
            if ":" in item.name and (item / "SKILL.md").exists():
                parsed_dir = parse_handle(item.name)
                # Match if names equal and username matches (if specified)
                if parsed_dir.simple_name == target_name:
                    if target_username is None or parsed_dir.username == target_username:
                        result.resources.append(
                            DiscoveredResource(
                                name=target_name,
                                resource_type=ResourceType.SKILL,
                                path_segments=parsed_dir.path_segments,
                                username=parsed_dir.username,
                            )
                        )
            # Also check legacy nested format: username/name (backward compat)
            elif ":" not in item.name:
                skill_path = item / target_name
                if skill_path.is_dir() and (skill_path / "SKILL.md").exists():
                    result.resources.append(
                        DiscoveredResource(
                            name=target_name,
                            resource_type=ResourceType.SKILL,
                            path_segments=[target_name],
                            username=item.name,
                        )
                    )

    # Check file-based resources (commands, agents, rules) using nested format
    file_based_types = [
        ("commands", ResourceType.COMMAND),
        ("agents", ResourceType.AGENT),
        ("rules", ResourceType.RULE),
    ]
    for subdir, resource_type in file_based_types:
        resource_dir = base_path / subdir
        if not resource_dir.is_dir():
            continue
        for username_dir in resource_dir.iterdir():
            if not username_dir.is_dir():
                continue
            if target_username and username_dir.name != target_username:
                continue
            resource_path = username_dir / f"{target_name}.md"
            if resource_path.is_file():
                result.resources.append(
                    DiscoveredResource(
                        name=target_name,
                        resource_type=resource_type,
                        path_segments=[target_name],
                        username=username_dir.name,
                    )
                )


def _discover_in_flat_path(
    base_path: Path,
    name: str,
    result: DiscoveryResult,
) -> None:
    """Discover resources in flat (non-namespaced) paths for backward compat."""
    handle = ParsedHandle(name=name, path_segments=[name])

    # Check for skill (directory with SKILL.md)
    skill_path = handle.to_skill_path(base_path)
    if skill_path.is_dir() and (skill_path / "SKILL.md").exists():
        result.resources.append(
            DiscoveredResource(
                name=name,
                resource_type=ResourceType.SKILL,
                path_segments=[name],
                username=None,
            )
        )

    # Check file-based resources (command, agent, rule)
    file_checks = [
        (handle.to_command_path(base_path), ResourceType.COMMAND),
        (handle.to_agent_path(base_path), ResourceType.AGENT),
        (handle.to_rule_path(base_path), ResourceType.RULE),
    ]
    for path, resource_type in file_checks:
        if path.is_file():
            result.resources.append(
                DiscoveredResource(
                    name=name,
                    resource_type=resource_type,
                    path_segments=[name],
                    username=None,
                )
            )


def discover_runnable_resource(
    repo_dir: Path,
    name: str,
    path_segments: list[str],
) -> DiscoveryResult:
    """
    Discover runnable resources (skills and commands only, not agents/bundles).

    Used by agrx to determine what type of resource to run.

    Args:
        repo_dir: Path to extracted repository
        name: Display name of the resource
        path_segments: Path segments for the resource

    Returns:
        DiscoveryResult with list of discovered runnable resources
    """
    result = DiscoveryResult()

    # Check for skill (directory with SKILL.md)
    skill_config = RESOURCE_CONFIGS[ResourceType.SKILL]
    skill_path = repo_dir / skill_config.source_subdir
    for segment in path_segments:
        skill_path = skill_path / segment
    if skill_path.is_dir() and (skill_path / "SKILL.md").exists():
        result.resources.append(
            DiscoveredResource(
                name=name,
                resource_type=ResourceType.SKILL,
                path_segments=path_segments,
            )
        )

    # Check for command (markdown file)
    command_config = RESOURCE_CONFIGS[ResourceType.COMMAND]
    command_path = repo_dir / command_config.source_subdir
    for segment in path_segments[:-1]:
        command_path = command_path / segment
    if path_segments:
        command_path = command_path / f"{path_segments[-1]}.md"
    if command_path.is_file():
        result.resources.append(
            DiscoveredResource(
                name=name,
                resource_type=ResourceType.COMMAND,
                path_segments=path_segments,
            )
        )

    return result
