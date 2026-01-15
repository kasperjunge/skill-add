"""Generic resource fetcher for skills, commands, and agents."""

import shutil
import tarfile
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from agr.exceptions import (
    AgrError,
    BundleNotFoundError,
    RepoNotFoundError,
    ResourceExistsError,
    ResourceNotFoundError,
)
from agr.tools import ResourceType, ToolAdapter, ToolResourceConfig
from agr.tools.registry import get_tool_adapter


def _build_resource_path(base_dir: Path, config: ToolResourceConfig, path_segments: list[str]) -> Path:
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


def fetch_resource(
    username: str,
    repo_name: str,
    name: str,
    path_segments: list[str],
    dest: Path,
    resource_type: ResourceType,
    overwrite: bool = False,
    tool: ToolAdapter | None = None,
) -> Path:
    """Fetch a resource from a user's GitHub repo and copy it to dest."""
    if tool is None:
        tool = get_tool_adapter()

    config = tool.get_resource_config(resource_type)
    if config is None:
        raise AgrError(f"Tool '{tool.name}' does not support {resource_type.value}s")

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

        # Try to find resource in source repo (prefer destination tool format, fall back to canonical)
        source_subdir = f"{config.base_dir}/{config.subdir}"
        source_base = repo_dir / source_subdir
        resource_source = _build_resource_path(source_base, config, path_segments)

        if not resource_source.exists():
            # Build display path for error message
            nested_path = "/".join(path_segments)
            if config.is_directory:
                expected_location = f"{source_subdir}/{nested_path}/"
            else:
                expected_location = f"{source_subdir}/{nested_path}{config.file_extension}"
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
    """Discover all resources within a bundle directory."""
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
    """Fetch and install all resources from a bundle."""
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
    """Remove all local resources for a bundle."""
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
