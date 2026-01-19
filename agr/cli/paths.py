"""Path utilities for agr CLI commands."""

import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import NoReturn

import typer
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

from agr.constants import (
    TOOL_DIR_NAME,
    SKILLS_SUBDIR,
    COMMANDS_SUBDIR,
    AGENTS_SUBDIR,
    RULES_SUBDIR,
    PACKAGES_SUBDIR,
)


# Shared console instance for all CLI modules
console = Console()

# Default repository name when not specified
DEFAULT_REPO_NAME = "agent-resources"

# Shared mapping from resource type string to subdirectory
TYPE_TO_SUBDIR: dict[str, str] = {
    "skill": SKILLS_SUBDIR,
    "command": COMMANDS_SUBDIR,
    "agent": AGENTS_SUBDIR,
    "rule": RULES_SUBDIR,
    "package": PACKAGES_SUBDIR,
}


def find_repo_root() -> Path:
    """Find the repository root by looking for .git directory.

    Returns:
        Path to the repository root, or current working directory if not in a repo.
    """
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def is_local_path(ref: str) -> bool:
    """Check if a reference is a local path.

    Args:
        ref: A resource reference string

    Returns:
        True if the reference starts with './', '/', or '../'
    """
    return ref.startswith(("./", "/", "../"))


def extract_type_from_args(
    args: list[str] | None, explicit_type: str | None
) -> tuple[list[str], str | None]:
    """Extract --type/-t option from args list if present.

    When --type or -t appears after the resource reference, Typer captures it
    as part of the variadic args list. This function extracts it.

    Args:
        args: The argument list (may contain --type/-t)
        explicit_type: The resource_type value from Typer (may be None if type was in args)

    Returns:
        Tuple of (cleaned_args, resource_type)
    """
    if not args or explicit_type is not None:
        return args or [], explicit_type

    cleaned_args = []
    resource_type = None
    i = 0
    while i < len(args):
        if args[i] in ("--type", "-t") and i + 1 < len(args):
            resource_type = args[i + 1]
            i += 2  # Skip both --type and its value
        else:
            cleaned_args.append(args[i])
            i += 1

    return cleaned_args, resource_type


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


def get_base_path(global_install: bool) -> Path:
    """Get the base .claude directory path."""
    if global_install:
        return Path.home() / TOOL_DIR_NAME
    return Path.cwd() / TOOL_DIR_NAME


def get_destination(resource_subdir: str, global_install: bool) -> Path:
    """
    Get the destination directory for a resource.

    Args:
        resource_subdir: The subdirectory name (e.g., "skills", "commands", "agents")
        global_install: If True, install to ~/.claude/, else to ./.claude/

    Returns:
        Path to the destination directory
    """
    return get_base_path(global_install) / resource_subdir


def get_namespaced_destination(
    username: str,
    resource_name: str,
    resource_subdir: str,
    global_install: bool,
) -> Path:
    """
    Get the namespaced destination path for a resource.

    Namespaced paths include the username:
    .claude/{subdir}/{username}/{name}/

    Args:
        username: GitHub username (e.g., "kasperjunge")
        resource_name: Name of the resource (e.g., "commit")
        resource_subdir: The subdirectory name (e.g., "skills", "commands", "agents")
        global_install: If True, use ~/.claude/, else ./.claude/

    Returns:
        Path to the namespaced destination (e.g., .claude/skills/kasperjunge/commit/)
    """
    base = get_base_path(global_install)
    return base / resource_subdir / username / resource_name


@contextmanager
def fetch_spinner():
    """Show spinner during fetch operation."""
    with Live(Spinner("dots", text="Fetching..."), console=console, transient=True):
        yield


def cleanup_empty_parent(path: Path) -> None:
    """Remove the parent directory if it's empty."""
    parent = path.parent
    if parent.exists() and not any(parent.iterdir()):
        parent.rmdir()


def remove_path(path: Path) -> None:
    """Remove a file or directory and clean up empty parent."""
    if path.is_dir():
        shutil.rmtree(path)
    elif path.is_file():
        path.unlink()
    else:
        return
    cleanup_empty_parent(path)


def error_exit(message: str, code: int = 1) -> NoReturn:
    """Print error message and exit with error code.

    Args:
        message: The error message to display
        code: Exit code (default: 1)

    Raises:
        typer.Exit: Always raises with the specified exit code
    """
    console.print(f"[red]Error: {message}[/red]")
    raise typer.Exit(code)


def warn(message: str) -> None:
    """Print warning message.

    Args:
        message: The warning message to display
    """
    console.print(f"[yellow]Warning: {message}[/yellow]")
