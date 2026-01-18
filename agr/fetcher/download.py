"""HTTP and tarball download operations for fetching resources."""

import tarfile
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import httpx

from agr.exceptions import AgrError, RepoNotFoundError
from agr.fetcher.types import ResourceConfig


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
