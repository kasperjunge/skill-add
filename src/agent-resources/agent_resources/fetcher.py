"""Generic resource fetcher for skills, commands, and agents."""

import shutil
import tarfile
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import httpx

from agent_resources.exceptions import (
    ClaudeAddError,
    RepoNotFoundError,
    ResourceExistsError,
    ResourceNotFoundError,
)


class ResourceType(Enum):
    """Type of resource to fetch."""

    SKILL = "skill"
    COMMAND = "command"
    AGENT = "agent"


@dataclass
class ResourceConfig:
    """Configuration for a resource type."""

    resource_type: ResourceType
    source_subdir: str  # e.g., ".claude/skills", ".claude/commands"
    dest_subdir: str  # e.g., "skills", "commands"
    is_directory: bool  # True for skills, False for commands/agents
    file_extension: str | None  # None for skills, ".md" for commands/agents


RESOURCE_CONFIGS: dict[ResourceType, ResourceConfig] = {
    ResourceType.SKILL: ResourceConfig(
        resource_type=ResourceType.SKILL,
        source_subdir=".claude/skills",
        dest_subdir="skills",
        is_directory=True,
        file_extension=None,
    ),
    ResourceType.COMMAND: ResourceConfig(
        resource_type=ResourceType.COMMAND,
        source_subdir=".claude/commands",
        dest_subdir="commands",
        is_directory=False,
        file_extension=".md",
    ),
    ResourceType.AGENT: ResourceConfig(
        resource_type=ResourceType.AGENT,
        source_subdir=".claude/agents",
        dest_subdir="agents",
        is_directory=False,
        file_extension=".md",
    ),
}


def _build_resource_path(base_dir: Path, config: ResourceConfig, path_segments: list[str]) -> Path:
    """Build a resource path from base directory and segments."""
    if config.is_directory:
        return base_dir / Path(*path_segments)
    *parent_segments, base_name = path_segments
    if parent_segments:
        return base_dir / Path(*parent_segments) / f"{base_name}{config.file_extension}"
    return base_dir / f"{base_name}{config.file_extension}"


def _download_and_extract_tarball(tarball_url: str, username: str, repo_name: str, tmp_path: Path) -> Path:
    """Download and extract a GitHub tarball, returning the repo directory path."""
    tarball_path = tmp_path / "repo.tar.gz"

    try:
        with httpx.Client(follow_redirects=True, timeout=30.0) as client:
            response = client.get(tarball_url)
            if response.status_code == 404:
                raise RepoNotFoundError(
                    f"Repository '{username}/{repo_name}' not found on GitHub."
                )
            response.raise_for_status()
            tarball_path.write_bytes(response.content)
    except httpx.HTTPStatusError as e:
        raise ClaudeAddError(f"Failed to download repository: {e}")
    except httpx.RequestError as e:
        raise ClaudeAddError(f"Network error: {e}")

    extract_path = tmp_path / "extracted"
    with tarfile.open(tarball_path, "r:gz") as tar:
        tar.extractall(extract_path)

    return extract_path / f"{repo_name}-main"


def fetch_resource(
    username: str,
    repo_name: str,
    name: str,
    path_segments: list[str],
    dest: Path,
    resource_type: ResourceType,
    overwrite: bool = False,
) -> Path:
    """
    Fetch a resource from a user's GitHub repo and copy it to dest.

    Args:
        username: GitHub username
        repo_name: GitHub repository name
        name: Display name of the resource (may contain colons for nested paths)
        path_segments: Path segments for the resource (e.g., ['dir', 'hello-world'])
        dest: Destination directory (e.g., .claude/skills/, .claude/commands/)
        resource_type: Type of resource (SKILL, COMMAND, or AGENT)
        overwrite: Whether to overwrite existing resource

    Returns:
        Path to the installed resource

    Raises:
        RepoNotFoundError: If the repository doesn't exist
        ResourceNotFoundError: If the resource doesn't exist in the repo
        ResourceExistsError: If resource exists locally and overwrite=False
    """
    config = RESOURCE_CONFIGS[resource_type]
    resource_dest = _build_resource_path(dest, config, path_segments)

    # Check if resource already exists locally
    if resource_dest.exists() and not overwrite:
        raise ResourceExistsError(
            f"{resource_type.value.capitalize()} '{name}' already exists at {resource_dest}\n"
            f"Use --overwrite to replace it."
        )

    # Download tarball
    tarball_url = (
        f"https://github.com/{username}/{repo_name}/archive/refs/heads/main.tar.gz"
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_dir = _download_and_extract_tarball(tarball_url, username, repo_name, Path(tmp_dir))
        source_base = repo_dir / config.source_subdir
        resource_source = _build_resource_path(source_base, config, path_segments)

        if not resource_source.exists():
            # Build display path for error message
            nested_path = "/".join(path_segments)
            if config.is_directory:
                expected_location = f"{config.source_subdir}/{nested_path}/"
            else:
                expected_location = f"{config.source_subdir}/{nested_path}{config.file_extension}"
            raise ResourceNotFoundError(
                f"{resource_type.value.capitalize()} '{name}' not found in {username}/{repo_name}.\n"
                f"Expected location: {expected_location}"
            )

        # Remove existing if overwriting
        if resource_dest.exists():
            if config.is_directory:
                shutil.rmtree(resource_dest)
            else:
                resource_dest.unlink()

        # Ensure destination parent exists (including nested directories)
        resource_dest.parent.mkdir(parents=True, exist_ok=True)

        # Copy resource to destination
        if config.is_directory:
            shutil.copytree(resource_source, resource_dest)
        else:
            shutil.copy2(resource_source, resource_dest)

    return resource_dest
