"""Generic resource discovery using ResourceSpec.

This module provides functions to find and discover resources in repositories
based on their specifications.
"""

from pathlib import Path

from agr.core.resource import Resource, ResourceSpec


def find_resource_in_repo(
    repo_dir: Path,
    name: str,
    spec: ResourceSpec,
) -> Resource | None:
    """Find a resource by name in a downloaded repository.

    Searches through the spec's search paths for a matching resource.

    Args:
        repo_dir: Path to extracted repository
        name: Name of the resource to find
        spec: Resource specification defining how to find it

    Returns:
        Resource if found, None otherwise
    """
    for search_path in spec.search_paths:
        if search_path == ".":
            # Root level: check repo_dir/name
            candidate = repo_dir / name
        else:
            candidate = repo_dir / search_path / name

        if spec.is_valid_resource(candidate):
            return Resource(
                spec=spec,
                name=name,
                path=candidate,
            )

    return None


def discover_resources_in_repo(
    repo_dir: Path,
    spec: ResourceSpec,
) -> list[Resource]:
    """Discover all resources of a type in a repository.

    Searches through the spec's search paths for all valid resources.

    Args:
        repo_dir: Path to extracted repository
        spec: Resource specification defining how to find resources

    Returns:
        List of discovered Resources
    """
    resources: list[Resource] = []
    seen_names: set[str] = set()

    for search_path in spec.search_paths:
        if search_path == ".":
            search_root = repo_dir
        else:
            search_root = repo_dir / search_path

        if not search_root.exists() or not search_root.is_dir():
            continue

        # Check immediate children for valid resources
        for child in search_root.iterdir():
            if spec.is_valid_resource(child):
                name = child.name
                # Avoid duplicates (same name found in multiple search paths)
                if name not in seen_names:
                    seen_names.add(name)
                    resources.append(
                        Resource(
                            spec=spec,
                            name=name,
                            path=child,
                        )
                    )

    return resources


def is_valid_resource_path(path: Path, spec: ResourceSpec) -> bool:
    """Check if a path is a valid resource according to the spec.

    Args:
        path: Path to check
        spec: Resource specification

    Returns:
        True if the path is a valid resource
    """
    return spec.is_valid_resource(path)
