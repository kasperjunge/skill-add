"""Shared CLI utilities for agr commands."""

import random
import re
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

import typer
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

from agr.config import CONFIG_FILENAME, AgrConfig, find_config, load_or_create_config
from agr.exceptions import (
    AgrError,
    BundleNotFoundError,
    ConfigNotFoundError,
    RepoNotFoundError,
    ResourceExistsError,
    ResourceNotFoundError,
)
from agr.fetcher import (
    BundleInstallResult,
    BundleRemoveResult,
    ResourceType,
    fetch_bundle,
    fetch_resource,
    remove_bundle,
)

console = Console()

# Default repository name when not specified
DEFAULT_REPO_NAME = "agent-resources"


def find_agr_toml(start_path: Path | None = None) -> Path | None:
    """Find agr.toml by walking up the directory tree.

    Args:
        start_path: Starting directory (defaults to cwd)

    Returns:
        Path to agr.toml if found, None otherwise
    """
    return find_config(start_path)


def get_or_create_config(start_path: Path | None = None) -> AgrConfig:
    """Get existing config or create a new one.

    Args:
        start_path: Starting directory (defaults to cwd)

    Returns:
        AgrConfig instance
    """
    return load_or_create_config(start_path)


def get_author_from_git(repo_path: Path | None = None) -> str | None:
    """Extract author username from git remote origin URL.

    Parses the origin remote URL to extract the GitHub username.
    Supports both HTTPS and SSH URL formats.

    Args:
        repo_path: Path to git repository (defaults to cwd)

    Returns:
        GitHub username if found, None otherwise

    Examples:
        "https://github.com/kasperjunge/agent-resources.git" -> "kasperjunge"
        "git@github.com:kasperjunge/agent-resources.git" -> "kasperjunge"
    """
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
        return parse_github_username_from_url(url)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def parse_github_username_from_url(url: str) -> str | None:
    """Parse GitHub username from a remote URL.

    Args:
        url: Git remote URL (HTTPS or SSH format)

    Returns:
        GitHub username if parseable, None otherwise
    """
    # HTTPS format: https://github.com/username/repo.git
    https_match = re.match(r"https://github\.com/([^/]+)/", url)
    if https_match:
        return https_match.group(1)

    # SSH format: git@github.com:username/repo.git
    ssh_match = re.match(r"git@github\.com:([^/]+)/", url)
    if ssh_match:
        return ssh_match.group(1)

    return None


def build_namespaced_path(
    base_path: Path,
    resource_type: str,
    username: str,
    package_name: str | None = None,
    resource_name: str | None = None,
) -> Path:
    """Build a namespaced install path for a resource.

    Args:
        base_path: Base .claude directory path
        resource_type: "skills", "commands", or "agents"
        username: Author username (namespace)
        package_name: Package name if part of a package
        resource_name: Name of the resource

    Returns:
        Full Path for the resource
    """
    path = base_path / resource_type / username
    if package_name:
        path = path / package_name
    if resource_name:
        path = path / resource_name
    return path


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
        return Path.home() / ".claude"
    return Path.cwd() / ".claude"


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


# Bundle handlers


def print_installed_resources(result: BundleInstallResult) -> None:
    """Print the list of installed resources from a bundle result."""
    if result.installed_skills:
        skills_str = ", ".join(result.installed_skills)
        console.print(f"  [cyan]Skills ({len(result.installed_skills)}):[/cyan] {skills_str}")
    if result.installed_commands:
        commands_str = ", ".join(result.installed_commands)
        console.print(f"  [cyan]Commands ({len(result.installed_commands)}):[/cyan] {commands_str}")
    if result.installed_agents:
        agents_str = ", ".join(result.installed_agents)
        console.print(f"  [cyan]Agents ({len(result.installed_agents)}):[/cyan] {agents_str}")


def print_bundle_success_message(
    bundle_name: str,
    result: BundleInstallResult,
    username: str,
    repo: str,
) -> None:
    """Print detailed success message for bundle installation."""
    console.print(f"[green]Installed bundle '{bundle_name}'[/green]")
    print_installed_resources(result)

    if result.total_skipped > 0:
        console.print(
            f"[yellow]Skipped {result.total_skipped} existing resource(s). "
            "Use --overwrite to replace.[/yellow]"
        )
        if result.skipped_skills:
            console.print(f"  [dim]Skipped skills: {', '.join(result.skipped_skills)}[/dim]")
        if result.skipped_commands:
            console.print(f"  [dim]Skipped commands: {', '.join(result.skipped_commands)}[/dim]")
        if result.skipped_agents:
            console.print(f"  [dim]Skipped agents: {', '.join(result.skipped_agents)}[/dim]")

    # Build share reference
    if repo == DEFAULT_REPO_NAME:
        share_ref = f"{username}/{bundle_name}"
    else:
        share_ref = f"{username}/{repo}/{bundle_name}"

    ctas = [
        f"Create your own bundle: organize resources under .claude/*/bundle-name/",
        "Star: https://github.com/kasperjunge/agent-resources",
        f"Share: agr add bundle {share_ref}",
    ]
    console.print(f"[dim]{random.choice(ctas)}[/dim]")


def print_bundle_remove_message(bundle_name: str, result: BundleRemoveResult) -> None:
    """Print detailed message for bundle removal."""
    console.print(f"[green]Removed bundle '{bundle_name}'[/green]")

    if result.removed_skills:
        skills_str = ", ".join(result.removed_skills)
        console.print(f"  [dim]Skills ({len(result.removed_skills)}): {skills_str}[/dim]")
    if result.removed_commands:
        commands_str = ", ".join(result.removed_commands)
        console.print(f"  [dim]Commands ({len(result.removed_commands)}): {commands_str}[/dim]")
    if result.removed_agents:
        agents_str = ", ".join(result.removed_agents)
        console.print(f"  [dim]Agents ({len(result.removed_agents)}): {agents_str}[/dim]")


def handle_add_bundle(
    bundle_ref: str,
    overwrite: bool = False,
    global_install: bool = False,
) -> None:
    """
    Handler for adding a bundle of resources.

    Args:
        bundle_ref: Bundle reference (e.g., "username/bundle-name")
        overwrite: Whether to overwrite existing resources
        global_install: If True, install to ~/.claude/, else to ./.claude/
    """
    try:
        username, repo_name, bundle_name, _path_segments = parse_resource_ref(bundle_ref)
    except typer.BadParameter as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    dest_base = get_base_path(global_install)

    try:
        with fetch_spinner():
            result = fetch_bundle(username, repo_name, bundle_name, dest_base, overwrite)

        if result.total_installed == 0 and result.total_skipped > 0:
            console.print(f"[yellow]No new resources installed from bundle '{bundle_name}'.[/yellow]")
            console.print("[yellow]All resources already exist. Use --overwrite to replace.[/yellow]")
        else:
            print_bundle_success_message(bundle_name, result, username, repo_name)

    except (RepoNotFoundError, BundleNotFoundError, AgrError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


def handle_update_bundle(
    bundle_ref: str,
    global_install: bool = False,
) -> None:
    """
    Handler for updating a bundle by re-fetching from GitHub.

    Args:
        bundle_ref: Bundle reference (e.g., "username/bundle-name")
        global_install: If True, update in ~/.claude/, else in ./.claude/
    """
    try:
        username, repo_name, bundle_name, _path_segments = parse_resource_ref(bundle_ref)
    except typer.BadParameter as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    dest_base = get_base_path(global_install)

    try:
        with fetch_spinner():
            result = fetch_bundle(username, repo_name, bundle_name, dest_base, overwrite=True)

        console.print(f"[green]Updated bundle '{bundle_name}'[/green]")
        print_installed_resources(result)

    except (RepoNotFoundError, BundleNotFoundError, AgrError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


def handle_remove_bundle(
    bundle_name: str,
    global_install: bool = False,
) -> None:
    """
    Handler for removing a bundle.

    Args:
        bundle_name: Name of the bundle to remove
        global_install: If True, remove from ~/.claude/, else from ./.claude/
    """
    dest_base = get_base_path(global_install)

    try:
        result = remove_bundle(bundle_name, dest_base)
        print_bundle_remove_message(bundle_name, result)
    except BundleNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except OSError as e:
        typer.echo(f"Error: Failed to remove bundle: {e}", err=True)
        raise typer.Exit(1)
