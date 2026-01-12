"""Shared CLI utilities for agr commands."""

import random
import shutil
from contextlib import contextmanager
from pathlib import Path

import typer
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

from agr.exceptions import (
    AgrError,
    RepoNotFoundError,
    ResourceExistsError,
    ResourceNotFoundError,
)
from agr.fetcher import ResourceType, fetch_resource

console = Console()

# Default repository name when not specified
DEFAULT_REPO_NAME = "agent-resources"


def parse_nested_name(name: str) -> tuple[str, list[str]]:
    """
    Parse a resource name that may contain colon-delimited path segments.

    Args:
        name: Resource name, possibly with colons (e.g., "dir:hello-world")

    Returns:
        Tuple of (base_name, path_segments) where:
        - base_name is the final segment (e.g., "hello-world")
        - path_segments is the full list of segments (e.g., ["dir", "hello-world"])

    Raises:
        typer.BadParameter: If the name has invalid colon usage
    """
    if not name:
        raise typer.BadParameter("Resource name cannot be empty")

    if name.startswith(":") or name.endswith(":"):
        raise typer.BadParameter(
            f"Invalid resource name '{name}': cannot start or end with ':'"
        )

    segments = name.split(":")

    # Check for empty segments (consecutive colons)
    if any(not seg for seg in segments):
        raise typer.BadParameter(
            f"Invalid resource name '{name}': contains empty path segments"
        )

    base_name = segments[-1]
    return base_name, segments


def parse_resource_ref(ref: str) -> tuple[str, str, str, list[str]]:
    """
    Parse resource reference into components.

    Supports two formats:
    - '<username>/<name>' -> uses default 'agent-resources' repo
    - '<username>/<repo>/<name>' -> uses custom repo

    The name component can contain colons for nested paths:
    - 'dir:hello-world' -> path segments ['dir', 'hello-world']

    Args:
        ref: Resource reference

    Returns:
        Tuple of (username, repo_name, resource_name, path_segments)
        - resource_name: the full name with colons (for display)
        - path_segments: list of path components (for file operations)

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

    # Parse nested path from name
    _base_name, path_segments = parse_nested_name(name)

    return username, repo, name, path_segments


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
    console.print(f"[green]Added {resource_type} '{name}'[/green]")

    # Build share reference based on whether custom repo was used
    if repo == DEFAULT_REPO_NAME:
        share_ref = f"{username}/{name}"
    else:
        share_ref = f"{username}/{repo}/{name}"

    ctas = [
        f"Create your own {resource_type} library: agr init repo agent-resources",
        "Star: https://github.com/kasperjunge/agent-resources",
        f"Share: agr add {resource_type} {share_ref}",
    ]
    console.print(f"[dim]{random.choice(ctas)}[/dim]")


def handle_add_resource(
    resource_ref: str,
    resource_type: ResourceType,
    resource_subdir: str,
    overwrite: bool = False,
    global_install: bool = False,
) -> None:
    """
    Generic handler for adding any resource type.

    Args:
        resource_ref: Resource reference (e.g., "username/resource-name")
        resource_type: Type of resource (SKILL, COMMAND, or AGENT)
        resource_subdir: Destination subdirectory (e.g., "skills", "commands", "agents")
        overwrite: Whether to overwrite existing resource
        global_install: If True, install to ~/.claude/, else to ./.claude/
    """
    try:
        username, repo_name, name, path_segments = parse_resource_ref(resource_ref)
    except typer.BadParameter as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    dest = get_destination(resource_subdir, global_install)

    try:
        with fetch_spinner():
            fetch_resource(
                username, repo_name, name, path_segments, dest, resource_type, overwrite
            )
        print_success_message(resource_type.value, name, username, repo_name)
    except (RepoNotFoundError, ResourceNotFoundError, ResourceExistsError, AgrError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


def get_local_resource_path(
    name: str,
    resource_subdir: str,
    global_install: bool,
) -> Path:
    """
    Build the local path for a resource based on its name and type.

    Args:
        name: Resource name (e.g., "hello-world")
        resource_subdir: Subdirectory type ("skills", "commands", or "agents")
        global_install: If True, look in ~/.claude/, else ./.claude/

    Returns:
        Path to the local resource (directory for skills, file for commands/agents)
    """
    dest = get_destination(resource_subdir, global_install)

    if resource_subdir == "skills":
        return dest / name
    else:
        # commands and agents are .md files
        return dest / f"{name}.md"


def handle_update_resource(
    resource_ref: str,
    resource_type: ResourceType,
    resource_subdir: str,
    global_install: bool = False,
) -> None:
    """
    Generic handler for updating any resource type.

    Re-fetches the resource from GitHub and overwrites the local copy.

    Args:
        resource_ref: Resource reference (e.g., "username/resource-name")
        resource_type: Type of resource (SKILL, COMMAND, or AGENT)
        resource_subdir: Destination subdirectory (e.g., "skills", "commands", "agents")
        global_install: If True, update in ~/.claude/, else in ./.claude/
    """
    try:
        username, repo_name, name, path_segments = parse_resource_ref(resource_ref)
    except typer.BadParameter as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    # Get local resource path to verify it exists
    local_path = get_local_resource_path(name, resource_subdir, global_install)

    if not local_path.exists():
        typer.echo(
            f"Error: {resource_type.value.capitalize()} '{name}' not found locally at {local_path}",
            err=True,
        )
        raise typer.Exit(1)

    dest = get_destination(resource_subdir, global_install)

    try:
        with fetch_spinner():
            fetch_resource(
                username, repo_name, name, path_segments, dest, resource_type, overwrite=True
            )
        console.print(f"[green]Updated {resource_type.value} '{name}'[/green]")
    except (RepoNotFoundError, ResourceNotFoundError, AgrError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


def handle_remove_resource(
    name: str,
    resource_type: ResourceType,
    resource_subdir: str,
    global_install: bool = False,
) -> None:
    """
    Generic handler for removing any resource type.

    Removes the resource immediately without confirmation.

    Args:
        name: Name of the resource to remove
        resource_type: Type of resource (SKILL, COMMAND, or AGENT)
        resource_subdir: Destination subdirectory (e.g., "skills", "commands", "agents")
        global_install: If True, remove from ~/.claude/, else from ./.claude/
    """
    local_path = get_local_resource_path(name, resource_subdir, global_install)

    if not local_path.exists():
        typer.echo(
            f"Error: {resource_type.value.capitalize()} '{name}' not found at {local_path}",
            err=True,
        )
        raise typer.Exit(1)

    try:
        if local_path.is_dir():
            shutil.rmtree(local_path)
        else:
            local_path.unlink()
        console.print(f"[green]Removed {resource_type.value} '{name}'[/green]")
    except OSError as e:
        typer.echo(f"Error: Failed to remove resource: {e}", err=True)
        raise typer.Exit(1)
