"""Bundle dataclasses and operations for multi-resource packages."""

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from agr.constants import TOOL_DIR_NAME, SKILLS_SUBDIR, COMMANDS_SUBDIR, AGENTS_SUBDIR
from agr.exceptions import BundleNotFoundError
from agr.fetcher.download import downloaded_repo


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
    skills_bundle_dir = repo_dir / TOOL_DIR_NAME / SKILLS_SUBDIR / bundle_name
    if skills_bundle_dir.is_dir():
        for skill_dir in skills_bundle_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                contents.skills.append(skill_dir.name)

    # Discover commands: look for .md files
    commands_bundle_dir = repo_dir / TOOL_DIR_NAME / COMMANDS_SUBDIR / bundle_name
    if commands_bundle_dir.is_dir():
        for cmd_file in commands_bundle_dir.glob("*.md"):
            contents.commands.append(cmd_file.stem)

    # Discover agents: look for .md files
    agents_bundle_dir = repo_dir / TOOL_DIR_NAME / AGENTS_SUBDIR / bundle_name
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


def fetch_bundle_from_repo_dir(
    repo_dir: Path,
    bundle_name: str,
    dest_base: Path,
    overwrite: bool = False,
) -> BundleInstallResult:
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
            f"  - {TOOL_DIR_NAME}/{SKILLS_SUBDIR}/{bundle_name}/*/SKILL.md\n"
            f"  - {TOOL_DIR_NAME}/{COMMANDS_SUBDIR}/{bundle_name}/*.md\n"
            f"  - {TOOL_DIR_NAME}/{AGENTS_SUBDIR}/{bundle_name}/*.md"
        )

    result = BundleInstallResult()

    # Install skills (directories)
    result.installed_skills, result.skipped_skills = _install_bundle_directory(
        contents.skills,
        repo_dir / TOOL_DIR_NAME / SKILLS_SUBDIR / bundle_name,
        dest_base / SKILLS_SUBDIR,
        bundle_name,
        overwrite,
    )

    # Install commands (files)
    result.installed_commands, result.skipped_commands = _install_bundle_files(
        contents.commands,
        repo_dir / TOOL_DIR_NAME / COMMANDS_SUBDIR / bundle_name,
        dest_base / COMMANDS_SUBDIR,
        bundle_name,
        overwrite,
    )

    # Install agents (files)
    result.installed_agents, result.skipped_agents = _install_bundle_files(
        contents.agents,
        repo_dir / TOOL_DIR_NAME / AGENTS_SUBDIR / bundle_name,
        dest_base / AGENTS_SUBDIR,
        bundle_name,
        overwrite,
    )

    return result


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
    with downloaded_repo(username, repo_name) as repo_dir:
        return fetch_bundle_from_repo_dir(repo_dir, bundle_name, dest_base, overwrite)


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
    skills_bundle_dir = dest_base / SKILLS_SUBDIR / bundle_name
    if skills_bundle_dir.is_dir():
        for skill_dir in skills_bundle_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                result.removed_skills.append(skill_dir.name)
        shutil.rmtree(skills_bundle_dir)

    # Check and remove commands bundle directory
    commands_bundle_dir = dest_base / COMMANDS_SUBDIR / bundle_name
    if commands_bundle_dir.is_dir():
        for cmd_file in commands_bundle_dir.glob("*.md"):
            result.removed_commands.append(cmd_file.stem)
        shutil.rmtree(commands_bundle_dir)

    # Check and remove agents bundle directory
    agents_bundle_dir = dest_base / AGENTS_SUBDIR / bundle_name
    if agents_bundle_dir.is_dir():
        for agent_file in agents_bundle_dir.glob("*.md"):
            result.removed_agents.append(agent_file.stem)
        shutil.rmtree(agents_bundle_dir)

    if result.is_empty:
        raise BundleNotFoundError(
            f"Bundle '{bundle_name}' not found locally.\n"
            f"Expected one of:\n"
            f"  - {dest_base}/{SKILLS_SUBDIR}/{bundle_name}/\n"
            f"  - {dest_base}/{COMMANDS_SUBDIR}/{bundle_name}/\n"
            f"  - {dest_base}/{AGENTS_SUBDIR}/{bundle_name}/"
        )

    return result
