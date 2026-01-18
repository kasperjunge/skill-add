"""Generic resource fetcher for skills, commands, and agents."""

import shutil
import tarfile
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Generator

import httpx

from agr.exceptions import (
    AgrError,
    BundleNotFoundError,
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


# Discovery dataclasses for auto-detection


@dataclass
class DiscoveredResource:
    """Holds information about a discovered resource."""

    name: str
    resource_type: ResourceType
    path_segments: list[str]
    username: str | None = None  # Username for namespaced resources


@dataclass
class DiscoveryResult:
    """Result of resource discovery operation."""

    resources: list[DiscoveredResource] = field(default_factory=list)
    is_bundle: bool = False

    @property
    def is_unique(self) -> bool:
        """Return True if exactly one resource type was found (including bundle)."""
        total = len(self.resources) + (1 if self.is_bundle else 0)
        return total == 1

    @property
    def is_ambiguous(self) -> bool:
        """Return True if multiple resource types were found."""
        total = len(self.resources) + (1 if self.is_bundle else 0)
        return total > 1

    @property
    def is_empty(self) -> bool:
        """Return True if no resources were found."""
        return len(self.resources) == 0 and not self.is_bundle

    @property
    def found_types(self) -> list[str]:
        """Return list of resource type names found."""
        types = [r.resource_type.value for r in self.resources]
        if self.is_bundle:
            types.append("bundle")
        return types


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
        raise AgrError(f"Failed to download repository: {e}")
    except httpx.RequestError as e:
        raise AgrError(f"Network error: {e}")

    extract_path = tmp_path / "extracted"
    with tarfile.open(tarball_path, "r:gz") as tar:
        tar.extractall(extract_path)

    return extract_path / f"{repo_name}-main"


@contextmanager
def downloaded_repo(
    username: str, repo_name: str
) -> Generator[Path, None, None]:
    """
    Context manager that downloads a repo tarball once and yields the repo directory.

    This allows both discovery and fetching to happen within the same temporary directory,
    avoiding double downloads.

    Args:
        username: GitHub username
        repo_name: GitHub repository name

    Yields:
        Path to the extracted repository directory

    Raises:
        RepoNotFoundError: If the repository doesn't exist
    """
    tarball_url = (
        f"https://github.com/{username}/{repo_name}/archive/refs/heads/main.tar.gz"
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_dir = _download_and_extract_tarball(
            tarball_url, username, repo_name, Path(tmp_dir)
        )
        yield repo_dir


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


def fetch_resource_from_repo_dir(
    repo_dir: Path,
    name: str,
    path_segments: list[str],
    dest: Path,
    resource_type: ResourceType,
    overwrite: bool = False,
    username: str | None = None,
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
                  When provided, installs to dest/username/name/ instead of dest/name/

    Returns:
        Path to the installed resource

    Raises:
        ResourceNotFoundError: If the resource doesn't exist in the repo
        ResourceExistsError: If resource exists locally and overwrite=False
    """
    config = RESOURCE_CONFIGS[resource_type]

    # Build destination path - namespaced if username provided
    if username:
        # Namespaced path: .claude/skills/username/name/
        namespaced_dest = dest / username
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

    source_base = repo_dir / config.source_subdir
    resource_source = _build_resource_path(source_base, config, path_segments)

    if not resource_source.exists():
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
    else:
        shutil.copy2(resource_source, resource_dest)

    return resource_dest


def fetch_bundle_from_repo_dir(
    repo_dir: Path,
    bundle_name: str,
    dest_base: Path,
    overwrite: bool = False,
) -> "BundleInstallResult":
    """
    Fetch and install a bundle from an already-downloaded repo directory.

    Args:
        repo_dir: Path to extracted repository
        bundle_name: Name of the bundle directory
        dest_base: Base destination directory (e.g., .claude/)
        overwrite: Whether to overwrite existing resources

    Returns:
        BundleInstallResult with installed and skipped resources

    Raises:
        BundleNotFoundError: If bundle directory doesn't exist
    """
    contents = discover_bundle_contents(repo_dir, bundle_name)

    if contents.is_empty:
        raise BundleNotFoundError(
            f"Bundle '{bundle_name}' not found.\n"
            f"Expected one of:\n"
            f"  - .claude/skills/{bundle_name}/*/SKILL.md\n"
            f"  - .claude/commands/{bundle_name}/*.md\n"
            f"  - .claude/agents/{bundle_name}/*.md"
        )

    result = BundleInstallResult()

    # Install skills (directories)
    result.installed_skills, result.skipped_skills = _install_bundle_directory(
        contents.skills,
        repo_dir / ".claude" / "skills" / bundle_name,
        dest_base / "skills",
        bundle_name,
        overwrite,
    )

    # Install commands (files)
    result.installed_commands, result.skipped_commands = _install_bundle_files(
        contents.commands,
        repo_dir / ".claude" / "commands" / bundle_name,
        dest_base / "commands",
        bundle_name,
        overwrite,
    )

    # Install agents (files)
    result.installed_agents, result.skipped_agents = _install_bundle_files(
        contents.agents,
        repo_dir / ".claude" / "agents" / bundle_name,
        dest_base / "agents",
        bundle_name,
        overwrite,
    )

    return result


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
        username: GitHub username for namespaced installation (when provided,
                  installs to dest/username/name/ instead of dest/name/)

    Returns:
        Path to the installed resource

    Raises:
        RepoNotFoundError: If the repository doesn't exist
        ResourceNotFoundError: If the resource doesn't exist in the repo
        ResourceExistsError: If resource exists locally and overwrite=False
    """
    config = RESOURCE_CONFIGS[resource_type]

    # Build destination path - namespaced if username provided
    if username:
        namespaced_dest = dest / username
        resource_dest = _build_resource_path(namespaced_dest, config, path_segments)
    else:
        resource_dest = _build_resource_path(dest, config, path_segments)

    # Check if resource already exists locally
    if resource_dest.exists() and not overwrite:
        raise ResourceExistsError(
            f"{resource_type.value.capitalize()} '{name}' already exists at {resource_dest}\n"
            f"Use --overwrite to replace it."
        )

    # Download tarball
    tarball_url = (
        f"https://github.com/{repo_username}/{repo_name}/archive/refs/heads/main.tar.gz"
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_dir = _download_and_extract_tarball(tarball_url, repo_username, repo_name, Path(tmp_dir))
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
                f"{resource_type.value.capitalize()} '{name}' not found in {repo_username}/{repo_name}.\n"
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


# Bundle-related dataclasses and functions


@dataclass
class BundleContents:
    """Discovered resources in a bundle."""

    bundle_name: str
    skills: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    agents: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.skills or self.commands or self.agents)

    @property
    def total_count(self) -> int:
        return len(self.skills) + len(self.commands) + len(self.agents)


@dataclass
class BundleInstallResult:
    """Result of bundle installation."""

    installed_skills: list[str] = field(default_factory=list)
    installed_commands: list[str] = field(default_factory=list)
    installed_agents: list[str] = field(default_factory=list)
    skipped_skills: list[str] = field(default_factory=list)
    skipped_commands: list[str] = field(default_factory=list)
    skipped_agents: list[str] = field(default_factory=list)

    @property
    def total_installed(self) -> int:
        return (
            len(self.installed_skills)
            + len(self.installed_commands)
            + len(self.installed_agents)
        )

    @property
    def total_skipped(self) -> int:
        return (
            len(self.skipped_skills)
            + len(self.skipped_commands)
            + len(self.skipped_agents)
        )


@dataclass
class BundleRemoveResult:
    """Result of bundle removal."""

    removed_skills: list[str] = field(default_factory=list)
    removed_commands: list[str] = field(default_factory=list)
    removed_agents: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.removed_skills or self.removed_commands or self.removed_agents)

    @property
    def total_removed(self) -> int:
        return (
            len(self.removed_skills)
            + len(self.removed_commands)
            + len(self.removed_agents)
        )


def discover_bundle_contents(repo_dir: Path, bundle_name: str) -> BundleContents:
    """
    Discover all resources within a bundle directory.

    Looks for:
    - .claude/skills/{bundle_name}/*/SKILL.md -> skill directories
    - .claude/commands/{bundle_name}/*.md -> command files
    - .claude/agents/{bundle_name}/*.md -> agent files

    Args:
        repo_dir: Path to extracted repository
        bundle_name: Name of the bundle directory

    Returns:
        BundleContents with lists of discovered resources
    """
    contents = BundleContents(bundle_name=bundle_name)

    # Discover skills: look for subdirectories with SKILL.md
    skills_bundle_dir = repo_dir / ".claude" / "skills" / bundle_name
    if skills_bundle_dir.is_dir():
        for skill_dir in skills_bundle_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                contents.skills.append(skill_dir.name)

    # Discover commands: look for .md files
    commands_bundle_dir = repo_dir / ".claude" / "commands" / bundle_name
    if commands_bundle_dir.is_dir():
        for cmd_file in commands_bundle_dir.glob("*.md"):
            contents.commands.append(cmd_file.stem)

    # Discover agents: look for .md files
    agents_bundle_dir = repo_dir / ".claude" / "agents" / bundle_name
    if agents_bundle_dir.is_dir():
        for agent_file in agents_bundle_dir.glob("*.md"):
            contents.agents.append(agent_file.stem)

    return contents


def _install_bundle_directory(
    names: list[str],
    src_base: Path,
    dest_base: Path,
    bundle_name: str,
    overwrite: bool,
) -> tuple[list[str], list[str]]:
    """Install directory-based resources (skills) from a bundle."""
    installed = []
    skipped = []
    for name in names:
        dest_path = dest_base / bundle_name / name
        src_path = src_base / name

        if dest_path.exists() and not overwrite:
            skipped.append(name)
            continue

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        if dest_path.exists():
            shutil.rmtree(dest_path)
        shutil.copytree(src_path, dest_path)
        installed.append(name)
    return installed, skipped


def _install_bundle_files(
    names: list[str],
    src_base: Path,
    dest_base: Path,
    bundle_name: str,
    overwrite: bool,
) -> tuple[list[str], list[str]]:
    """Install file-based resources (commands, agents) from a bundle."""
    installed = []
    skipped = []
    for name in names:
        dest_path = dest_base / bundle_name / f"{name}.md"
        src_path = src_base / f"{name}.md"

        if dest_path.exists() and not overwrite:
            skipped.append(name)
            continue

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        if dest_path.exists():
            dest_path.unlink()
        shutil.copy2(src_path, dest_path)
        installed.append(name)
    return installed, skipped


def fetch_bundle(
    username: str,
    repo_name: str,
    bundle_name: str,
    dest_base: Path,
    overwrite: bool = False,
) -> BundleInstallResult:
    """
    Fetch and install all resources from a bundle.

    Args:
        username: GitHub username
        repo_name: GitHub repository name
        bundle_name: Name of the bundle directory
        dest_base: Base destination directory (e.g., .claude/)
        overwrite: Whether to overwrite existing resources

    Returns:
        BundleInstallResult with installed and skipped resources

    Raises:
        RepoNotFoundError: If the repository doesn't exist
        BundleNotFoundError: If bundle directory doesn't exist in any location
    """
    tarball_url = (
        f"https://github.com/{username}/{repo_name}/archive/refs/heads/main.tar.gz"
    )
    result = BundleInstallResult()

    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_dir = _download_and_extract_tarball(
            tarball_url, username, repo_name, Path(tmp_dir)
        )

        contents = discover_bundle_contents(repo_dir, bundle_name)

        if contents.is_empty:
            raise BundleNotFoundError(
                f"Bundle '{bundle_name}' not found in {username}/{repo_name}.\n"
                f"Expected one of:\n"
                f"  - .claude/skills/{bundle_name}/*/SKILL.md\n"
                f"  - .claude/commands/{bundle_name}/*.md\n"
                f"  - .claude/agents/{bundle_name}/*.md"
            )

        # Install skills (directories)
        result.installed_skills, result.skipped_skills = _install_bundle_directory(
            contents.skills,
            repo_dir / ".claude" / "skills" / bundle_name,
            dest_base / "skills",
            bundle_name,
            overwrite,
        )

        # Install commands (files)
        result.installed_commands, result.skipped_commands = _install_bundle_files(
            contents.commands,
            repo_dir / ".claude" / "commands" / bundle_name,
            dest_base / "commands",
            bundle_name,
            overwrite,
        )

        # Install agents (files)
        result.installed_agents, result.skipped_agents = _install_bundle_files(
            contents.agents,
            repo_dir / ".claude" / "agents" / bundle_name,
            dest_base / "agents",
            bundle_name,
            overwrite,
        )

    return result


def remove_bundle(bundle_name: str, dest_base: Path) -> BundleRemoveResult:
    """
    Remove all local resources for a bundle.

    Args:
        bundle_name: Name of the bundle to remove
        dest_base: Base directory (e.g., .claude/)

    Returns:
        BundleRemoveResult with lists of removed resources

    Raises:
        BundleNotFoundError: If bundle doesn't exist locally
    """
    result = BundleRemoveResult()

    # Check and remove skills bundle directory
    skills_bundle_dir = dest_base / "skills" / bundle_name
    if skills_bundle_dir.is_dir():
        for skill_dir in skills_bundle_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                result.removed_skills.append(skill_dir.name)
        shutil.rmtree(skills_bundle_dir)

    # Check and remove commands bundle directory
    commands_bundle_dir = dest_base / "commands" / bundle_name
    if commands_bundle_dir.is_dir():
        for cmd_file in commands_bundle_dir.glob("*.md"):
            result.removed_commands.append(cmd_file.stem)
        shutil.rmtree(commands_bundle_dir)

    # Check and remove agents bundle directory
    agents_bundle_dir = dest_base / "agents" / bundle_name
    if agents_bundle_dir.is_dir():
        for agent_file in agents_bundle_dir.glob("*.md"):
            result.removed_agents.append(agent_file.stem)
        shutil.rmtree(agents_bundle_dir)

    if result.is_empty:
        raise BundleNotFoundError(
            f"Bundle '{bundle_name}' not found locally.\n"
            f"Expected one of:\n"
            f"  - {dest_base}/skills/{bundle_name}/\n"
            f"  - {dest_base}/commands/{bundle_name}/\n"
            f"  - {dest_base}/agents/{bundle_name}/"
        )

    return result
