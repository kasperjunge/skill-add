"""GitHub download and skill installation."""

import shutil
import tarfile
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import httpx

from agr.exceptions import AgrError, RepoNotFoundError, SkillNotFoundError
from agr.handle import ParsedHandle
from agr.skill import SKILL_MARKER, find_skill_in_repo, is_valid_skill_dir, update_skill_md_name
from agr.tool import DEFAULT_TOOL


@contextmanager
def downloaded_repo(username: str, repo_name: str) -> Generator[Path, None, None]:
    """Download a GitHub repo tarball and yield the extracted directory.

    Args:
        username: GitHub username
        repo_name: Repository name

    Yields:
        Path to extracted repository directory

    Raises:
        RepoNotFoundError: If the repository doesn't exist
        AgrError: If download or extraction fails
    """
    tarball_url = f"https://github.com/{username}/{repo_name}/archive/refs/heads/main.tar.gz"

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        tarball_path = tmp_path / "repo.tar.gz"

        # Download tarball
        try:
            with httpx.Client(follow_redirects=True, timeout=30.0) as client:
                response = client.get(tarball_url)
                if response.status_code == 404:
                    raise RepoNotFoundError(
                        f"Repository '{username}/{repo_name}' not found on GitHub"
                    )
                response.raise_for_status()
                tarball_path.write_bytes(response.content)
        except httpx.HTTPStatusError as e:
            raise AgrError(f"Failed to download repository: {e}")
        except httpx.RequestError as e:
            raise AgrError(f"Network error: {e}")

        # Extract tarball
        extract_path = tmp_path / "extracted"
        with tarfile.open(tarball_path, "r:gz") as tar:
            tar.extractall(extract_path, filter="data")

        # GitHub tarballs extract to {repo}-{branch}/
        repo_dir = extract_path / f"{repo_name}-main"
        if not repo_dir.exists():
            # Try finding the extracted directory
            dirs = list(extract_path.iterdir())
            if dirs:
                repo_dir = dirs[0]
            else:
                raise AgrError("Failed to extract repository")

        yield repo_dir


def install_skill_from_repo(
    repo_dir: Path,
    skill_name: str,
    handle: ParsedHandle,
    dest_dir: Path,
    overwrite: bool = False,
) -> Path:
    """Install a skill from a downloaded repository.

    Args:
        repo_dir: Path to extracted repository
        skill_name: Name of the skill to install
        handle: Parsed handle for naming
        dest_dir: Destination skills directory
        overwrite: Whether to overwrite existing

    Returns:
        Path to installed skill

    Raises:
        SkillNotFoundError: If skill not found in repo
        FileExistsError: If skill exists and not overwriting
    """
    # Find the skill in the repo
    skill_source = find_skill_in_repo(repo_dir, skill_name)
    if skill_source is None:
        raise SkillNotFoundError(
            f"Skill '{skill_name}' not found in repository.\n"
            f"Searched: resources/skills/{skill_name}/, skills/{skill_name}/, {skill_name}/"
        )

    # Determine installed name and destination
    installed_name = handle.to_installed_name()
    skill_dest = dest_dir / installed_name

    # Check if exists
    if skill_dest.exists() and not overwrite:
        raise FileExistsError(
            f"Skill already exists at {skill_dest}. Use --overwrite to replace."
        )

    # Remove existing if overwriting
    if skill_dest.exists():
        shutil.rmtree(skill_dest)

    # Ensure parent exists
    skill_dest.parent.mkdir(parents=True, exist_ok=True)

    # Copy skill
    shutil.copytree(skill_source, skill_dest)

    # Update SKILL.md name field
    update_skill_md_name(skill_dest, installed_name)

    return skill_dest


def install_local_skill(
    source_path: Path,
    dest_dir: Path,
    overwrite: bool = False,
) -> Path:
    """Install a local skill.

    Args:
        source_path: Path to local skill directory
        dest_dir: Destination skills directory
        overwrite: Whether to overwrite existing

    Returns:
        Path to installed skill

    Raises:
        SkillNotFoundError: If source is not a valid skill
        FileExistsError: If skill exists and not overwriting
    """
    # Validate source
    if not is_valid_skill_dir(source_path):
        raise SkillNotFoundError(
            f"'{source_path}' is not a valid skill (missing {SKILL_MARKER})"
        )

    # Determine installed name
    installed_name = f"local:{source_path.name}"
    skill_dest = dest_dir / installed_name

    # Check if exists
    if skill_dest.exists() and not overwrite:
        raise FileExistsError(
            f"Skill already exists at {skill_dest}. Use --overwrite to replace."
        )

    # Remove existing if overwriting
    if skill_dest.exists():
        shutil.rmtree(skill_dest)

    # Ensure parent exists
    skill_dest.parent.mkdir(parents=True, exist_ok=True)

    # Copy skill
    shutil.copytree(source_path, skill_dest)

    # Update SKILL.md name field
    update_skill_md_name(skill_dest, installed_name)

    return skill_dest


def fetch_and_install(
    handle: ParsedHandle,
    repo_root: Path,
    overwrite: bool = False,
) -> Path:
    """Fetch and install a skill.

    Args:
        handle: Parsed handle (remote or local)
        repo_root: Repository root path
        overwrite: Whether to overwrite existing

    Returns:
        Path to installed skill

    Raises:
        Various exceptions on failure
    """
    skills_dir = DEFAULT_TOOL.get_skills_dir(repo_root)

    if handle.is_local:
        # Local skill installation
        if handle.local_path is None:
            raise ValueError("Local handle missing path")

        source_path = handle.local_path
        if not source_path.is_absolute():
            source_path = (repo_root / source_path).resolve()

        return install_local_skill(source_path, skills_dir, overwrite)

    # Remote skill installation
    username, repo_name = handle.get_github_repo()

    with downloaded_repo(username, repo_name) as repo_dir:
        return install_skill_from_repo(
            repo_dir, handle.name, handle, skills_dir, overwrite
        )


def uninstall_skill(installed_name: str, repo_root: Path) -> bool:
    """Uninstall a skill by its installed name.

    Args:
        installed_name: Installed directory name (e.g., "kasperjunge:commit")
        repo_root: Repository root path

    Returns:
        True if removed, False if not found
    """
    skills_dir = DEFAULT_TOOL.get_skills_dir(repo_root)
    skill_path = skills_dir / installed_name

    if not skill_path.exists():
        return False

    shutil.rmtree(skill_path)
    return True


def get_installed_skills(repo_root: Path) -> list[str]:
    """Get list of installed skill names.

    Args:
        repo_root: Repository root path

    Returns:
        List of installed skill directory names
    """
    skills_dir = DEFAULT_TOOL.get_skills_dir(repo_root)

    if not skills_dir.exists():
        return []

    return [
        d.name for d in skills_dir.iterdir()
        if d.is_dir() and (d / SKILL_MARKER).exists()
    ]


def is_skill_installed(installed_name: str, repo_root: Path) -> bool:
    """Check if a skill is installed.

    Args:
        installed_name: Installed directory name
        repo_root: Repository root path

    Returns:
        True if installed
    """
    skills_dir = DEFAULT_TOOL.get_skills_dir(repo_root)
    skill_path = skills_dir / installed_name
    return skill_path.exists() and is_valid_skill_dir(skill_path)
