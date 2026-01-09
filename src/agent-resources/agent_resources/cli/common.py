"""Shared CLI utilities for add-skill, add-command, and add-agent."""

import random
from contextlib import contextmanager
from pathlib import Path

import typer
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

console = Console()

# Default repository name when not specified
DEFAULT_REPO_NAME = "agent-resources"


def parse_resource_ref(ref: str) -> tuple[str, str, str]:
    """
    Parse resource reference into components.

    Supports two formats:
    - '<username>/<name>' -> uses default 'agent-resources' repo
    - '<username>/<repo>/<name>' -> uses custom repo

    Args:
        ref: Resource reference

    Returns:
        Tuple of (username, repo_name, resource_name)

    Raises:
        typer.BadParameter: If the format is invalid
    """
    parts = ref.split("/")

    if len(parts) == 2:
        username, name = parts
        repo = DEFAULT_REPO_NAME
    elif len(parts) == 3:
        username, repo, name = parts
    else:
        raise typer.BadParameter(
            f"Invalid format: '{ref}'. Expected: <username>/<name> or <username>/<repo>/<name>"
        )

    if not username or not name or (len(parts) == 3 and not repo):
        raise typer.BadParameter(
            f"Invalid format: '{ref}'. Expected: <username>/<name> or <username>/<repo>/<name>"
        )

    return username, repo, name


def get_destination(resource_subdir: str, global_install: bool) -> Path:
    """
    Get the destination directory for a resource.

    Args:
        resource_subdir: The subdirectory name (e.g., "skills", "commands", "agents")
        global_install: If True, install to ~/.claude/, else to ./.claude/

    Returns:
        Path to the destination directory
    """
    if global_install:
        base = Path.home() / ".claude"
    else:
        base = Path.cwd() / ".claude"

    return base / resource_subdir


@contextmanager
def fetch_spinner():
    """Show spinner during fetch operation."""
    with Live(Spinner("dots", text="Fetching..."), console=console, transient=True):
        yield


def print_success_message(resource_type: str, name: str, username: str, repo: str) -> None:
    """Print branded success message with rotating CTA."""
    console.print(f"✅ Added {resource_type} '{name}' via 🧩 agent-resources", style="dim")

    # Build share reference based on whether custom repo was used
    if repo == DEFAULT_REPO_NAME:
        share_ref = f"{username}/{name}"
    else:
        share_ref = f"{username}/{repo}/{name}"

    ctas = [
        f"💡 Create your own {resource_type} library on GitHub: uvx create-agent-resources-repo --github",
        "⭐ Star: github.com/kasperjunge/agent-resources-project",
        f"📢 Share: uvx add-{resource_type} {share_ref}",
    ]
    console.print(random.choice(ctas), style="dim")
