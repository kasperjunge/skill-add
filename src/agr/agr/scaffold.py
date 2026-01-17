"""Scaffolding functions for creating agent-resources repository structure."""

import subprocess
from pathlib import Path


def init_git(path: Path) -> bool:
    """Initialize git repository and create initial commit.

    Returns True if successful, False otherwise.
    """
    try:
        subprocess.run(
            ["git", "init"],
            cwd=path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "add", "."],
            cwd=path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit: agent-resources repo scaffold"],
            cwd=path,
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
