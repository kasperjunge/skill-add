"""Resource fetching operations for skills, commands, and agents."""

import shutil
from pathlib import Path

from agr.exceptions import ResourceExistsError, ResourceNotFoundError
from agr.fetcher.download import _build_resource_path, downloaded_repo
from agr.fetcher.types import RESOURCE_CONFIGS, ResourceType
from agr.utils import compute_flattened_resource_name, update_skill_md_name


def fetch_resource_from_repo_dir(
    repo_dir: Path,
    name: str,
    path_segments: list[str],
    dest: Path,
    resource_type: ResourceType,
    overwrite: bool = False,
    username: str | None = None,
    source_path: Path | None = None,
    package_name: str | None = None,
) -> Path:
    """
    Fetch a resource from an already-downloaded repo directory.

    This avoids double downloads when used with downloaded_repo context manager.

    Args:
        repo_dir: Path to extracted repository
        name: Display name of the resource
        path_segments: Path segments for the resource
        dest: Destination directory (e.g., .claude/skills/)
        resource_type: Type of resource
        overwrite: Whether to overwrite existing resource
        username: GitHub username for namespaced installation (e.g., "kasperjunge")
                  When provided, installs to dest/<flattened_name>/ for skills,
                  or dest/username/name/ for commands/agents.
        source_path: Explicit source path (relative to repo root) from resolver.
                     If provided, uses this instead of building from path_segments.
                     This is used when the resource location is specified in agr.toml.
        package_name: Package name from PACKAGE.md for additional namespacing.
                      When provided, adds package context to the installed path:
                      - Skills: dest/username:package:name/
                      - Commands/agents: dest/username/package/name.md

    Returns:
        Path to the installed resource

    Raises:
        ResourceNotFoundError: If the resource doesn't exist in the repo
        ResourceExistsError: If resource exists locally and overwrite=False
    """
    config = RESOURCE_CONFIGS[resource_type]

    # Build destination path - skills use flattened colon-namespaced names
    if username and config.is_directory:
        # Skills: .claude/skills/<flattened_name>/
        # e.g., .claude/skills/kasperjunge:commit/ or .claude/skills/kasperjunge:package:skill/
        flattened_name = compute_flattened_resource_name(username, path_segments, package_name)
        resource_dest = dest / flattened_name
    elif username:
        # Commands/agents: .claude/commands/username/[package/][path/]name.md
        # Include package_name and full path_segments for nested directory structure
        namespaced_dest = dest / username
        if package_name:
            namespaced_dest = namespaced_dest / package_name
        nested_dirs = path_segments[:-1] if path_segments else []
        if nested_dirs:
            resource_dest = _build_resource_path(namespaced_dest / Path(*nested_dirs), config, [path_segments[-1]])
        else:
            resource_dest = _build_resource_path(namespaced_dest, config, path_segments)
    else:
        # Flat path (backward compat): .claude/skills/name/
        resource_dest = _build_resource_path(dest, config, path_segments)

    # Check if resource already exists locally
    if resource_dest.exists() and not overwrite:
        raise ResourceExistsError(
            f"{resource_type.value.capitalize()} '{name}' already exists at {resource_dest}\n"
            f"Use --overwrite to replace it."
        )

    # Determine source path: use explicit source_path if provided, else build from path_segments
    if source_path:
        resource_source = repo_dir / source_path
    else:
        source_base = repo_dir / config.source_subdir
        resource_source = _build_resource_path(source_base, config, path_segments)

    if not resource_source.exists():
        if source_path:
            expected_location = str(source_path)
        else:
            nested_path = "/".join(path_segments)
            if config.is_directory:
                expected_location = f"{config.source_subdir}/{nested_path}/"
            else:
                expected_location = f"{config.source_subdir}/{nested_path}{config.file_extension}"
        raise ResourceNotFoundError(
            f"{resource_type.value.capitalize()} '{name}' not found.\n"
            f"Expected location: {expected_location}"
        )

    # Remove existing if overwriting
    if resource_dest.exists():
        if config.is_directory:
            shutil.rmtree(resource_dest)
        else:
            resource_dest.unlink()

    # Ensure destination parent exists
    resource_dest.parent.mkdir(parents=True, exist_ok=True)

    # Copy resource to destination
    if config.is_directory:
        shutil.copytree(resource_source, resource_dest)
        # Update SKILL.md name field for skills (flattened_name already computed above)
        if username:
            update_skill_md_name(resource_dest, flattened_name)
    else:
        shutil.copy2(resource_source, resource_dest)

    return resource_dest


def fetch_resource(
    repo_username: str,
    repo_name: str,
    name: str,
    path_segments: list[str],
    dest: Path,
    resource_type: ResourceType,
    overwrite: bool = False,
    username: str | None = None,
) -> Path:
    """
    Fetch a resource from a user's GitHub repo and copy it to dest.

    Args:
        repo_username: GitHub username (repo owner)
        repo_name: GitHub repository name
        name: Display name of the resource (may contain colons for nested paths)
        path_segments: Path segments for the resource (e.g., ['dir', 'hello-world'])
        dest: Destination directory (e.g., .claude/skills/, .claude/commands/)
        resource_type: Type of resource (SKILL, COMMAND, or AGENT)
        overwrite: Whether to overwrite existing resource
        username: GitHub username for namespaced installation. When provided,
                  installs to dest/<flattened_name>/ for skills,
                  or dest/username/name/ for commands/agents.

    Returns:
        Path to the installed resource

    Raises:
        RepoNotFoundError: If the repository doesn't exist
        ResourceNotFoundError: If the resource doesn't exist in the repo
        ResourceExistsError: If resource exists locally and overwrite=False
    """
    with downloaded_repo(repo_username, repo_name) as repo_dir:
        return fetch_resource_from_repo_dir(
            repo_dir, name, path_segments, dest, resource_type, overwrite, username
        )
