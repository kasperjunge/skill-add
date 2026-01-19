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

    # Check file-based resources (command, agent, rule)
    for resource_type in [ResourceType.COMMAND, ResourceType.AGENT, ResourceType.RULE]:
        config = RESOURCE_CONFIGS[resource_type]
        resource_path = _build_resource_path(
            repo_dir / config.source_subdir, config, path_segments
        )
        if resource_path.is_file():
            result.resources.append(
                DiscoveredResource(
                    name=name,
                    resource_type=resource_type,
                    path_segments=path_segments,
                )
            )

    # Check for bundle
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
