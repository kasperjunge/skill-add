"""GitHub CLI integration for creating and pushing repositories."""

import subprocess
from pathlib import Path


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


def get_author_from_remote(repo_path: Path | None = None) -> str | None:
    """Get the author (username) from the git remote origin URL.

    Parses the origin remote URL to extract the GitHub username.
    Supports both HTTPS and SSH URL formats.

    Args:
        repo_path: Path to the git repository (defaults to current directory)

    Returns:
        GitHub username if found, None otherwise

    Examples:
        For "https://github.com/kasperjunge/agent-resources.git" returns "kasperjunge"
        For "git@github.com:kasperjunge/agent-resources.git" returns "kasperjunge"
    """
    import re

    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=5,
        )
        if result.returncode != 0:
            return None

        url = result.stdout.strip()

        # HTTPS format: https://github.com/username/repo.git
        https_match = re.match(r"https://github\.com/([^/]+)/", url)
        if https_match:
            return https_match.group(1)

        # SSH format: git@github.com:username/repo.git
        ssh_match = re.match(r"git@github\.com:([^/]+)/", url)
        if ssh_match:
            return ssh_match.group(1)

        return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
