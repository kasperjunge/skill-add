"""GitHub CLI integration for creating and pushing repositories."""

import re
import subprocess
from pathlib import Path


def get_username_from_git_remote(repo_path: Path | None = None) -> str | None:
    """Extract username from git remote origin URL.

    Parses both SSH and HTTPS style remotes:
    - git@github.com:username/repo.git -> username
    - https://github.com/username/repo.git -> username
    - https://github.com/username/repo -> username

    Args:
        repo_path: Path to the git repository (defaults to current directory)

    Returns:
        The username/org from the remote, or None if not found
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=30,
        )
        if result.returncode != 0:
            return None

        remote_url = result.stdout.strip()
        if not remote_url:
            return None

        # Try SSH format: git@github.com:username/repo.git
        ssh_match = re.match(r"git@[^:]+:([^/]+)/", remote_url)
        if ssh_match:
            return ssh_match.group(1)

        # Try HTTPS format: https://github.com/username/repo.git
        https_match = re.match(r"https?://[^/]+/([^/]+)/", remote_url)
        if https_match:
            return https_match.group(1)

        return None

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None


def check_gh_cli() -> bool:
    """Check if GitHub CLI is available and authenticated.

    Returns True if gh CLI is installed and authenticated, False otherwise.
    """
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_github_username() -> str | None:
    """Get the authenticated GitHub username.

    Returns the username if authenticated, None otherwise.
    """
    try:
        result = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None


def create_github_repo(path: Path, repo_name: str = "agent-resources") -> str | None:
    """Create a GitHub repository and push the local repo.

    Args:
        path: Path to the local git repository
        repo_name: Name for the GitHub repository (default: agent-resources)

    Returns:
        The GitHub repo URL if successful, None otherwise.
    """
    try:
        # Create repo on GitHub (public by default)
        subprocess.run(
            [
                "gh",
                "repo",
                "create",
                repo_name,
                "--public",
                "--source",
                str(path),
                "--push",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        )

        # Construct URL from username
        username = get_github_username()
        if username:
            return f"https://github.com/{username}/{repo_name}"

        return None
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None


def repo_exists(repo_name: str = "agent-resources") -> bool:
    """Check if a repository with the given name already exists.

    Returns True if the repo exists, False otherwise.
    """
    try:
        result = subprocess.run(
            ["gh", "repo", "view", repo_name],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
