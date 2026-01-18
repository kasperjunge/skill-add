"""Resource discovery functions for auto-detecting resource types."""

from pathlib import Path

from agr.fetcher.bundle import discover_bundle_contents
from agr.fetcher.download import _build_resource_path
from agr.fetcher.types import (
    DiscoveredResource,
    DiscoveryResult,
    RESOURCE_CONFIGS,
    ResourceType,
)


def discover_resource_type_from_dir(
    repo_dir: Path,
    name: str,
    path_segments: list[str],
) -> DiscoveryResult:
    """
    Search all resource directories to find matching resources.

    Priority order for detection:
    1. Skill (.claude/skills/{name}/SKILL.md or .claude/skills/{path}/SKILL.md)
    2. Command (.claude/commands/{name}.md or .claude/commands/{path}.md)
    3. Agent (.claude/agents/{name}.md or .claude/agents/{path}.md)
    4. Bundle (.claude/*/name/ directories with resources)

    Args:
        repo_dir: Path to extracted repository
        name: Display name of the resource
        path_segments: Path segments for the resource

    Returns:
        DiscoveryResult with list of discovered resources
    """
    result = DiscoveryResult()

    # Check for skill (directory with SKILL.md)
    skill_config = RESOURCE_CONFIGS[ResourceType.SKILL]
    skill_path = _build_resource_path(
        repo_dir / skill_config.source_subdir, skill_config, path_segments
    )
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
    command_path = _build_resource_path(
        repo_dir / command_config.source_subdir, command_config, path_segments
    )
    if command_path.is_file():
        result.resources.append(
            DiscoveredResource(
                name=name,
                resource_type=ResourceType.COMMAND,
                path_segments=path_segments,
            )
        )

    # Check for agent (markdown file)
    agent_config = RESOURCE_CONFIGS[ResourceType.AGENT]
    agent_path = _build_resource_path(
        repo_dir / agent_config.source_subdir, agent_config, path_segments
    )
    if agent_path.is_file():
        result.resources.append(
            DiscoveredResource(
                name=name,
                resource_type=ResourceType.AGENT,
                path_segments=path_segments,
            )
        )

    # Check for bundle (directory with resources in any of the three locations)
    bundle_name = path_segments[-1] if path_segments else name
    bundle_contents = discover_bundle_contents(repo_dir, bundle_name)
    if not bundle_contents.is_empty:
        result.is_bundle = True

    return result


def _is_bundle(repo_dir: Path, path_segments: list[str]) -> bool:
    """Check if a name refers to a bundle in the repo."""
    bundle_name = path_segments[-1] if path_segments else ""
    if not bundle_name:
        return False
    bundle_contents = discover_bundle_contents(repo_dir, bundle_name)
    return not bundle_contents.is_empty
