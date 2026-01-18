"""Shared CLI utilities for agr commands."""

import random
import shutil
from contextlib import contextmanager
from pathlib import Path

import typer
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

from agr.config import AgrConfig, Dependency, get_or_create_config
from agr.exceptions import (
    AgrError,
    BundleNotFoundError,
    MultipleResourcesFoundError,
    RepoNotFoundError,
    ResourceExistsError,
    ResourceNotFoundError,
)
from agr.fetcher import (
    BundleInstallResult,
    BundleRemoveResult,
    DiscoveredResource,
    DiscoveryResult,
    RESOURCE_CONFIGS,
    ResourceType,
    discover_resource_type_from_dir,
    downloaded_repo,
    fetch_bundle,
    fetch_bundle_from_repo_dir,
    fetch_resource,
    fetch_resource_from_repo_dir,
    remove_bundle,
)

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


def print_success_message(resource_type: str, name: str, username: str, repo: str) -> None:
    """Print branded success message with rotating CTA."""
    console.print(f"[green]Added {resource_type} '{name}'[/green]")

    # Build share reference based on whether custom repo was used
    if repo == DEFAULT_REPO_NAME:
        share_ref = f"{username}/{name}"
    else:
        share_ref = f"{username}/{repo}/{name}"

    ctas = [
        f"Create your own {resource_type} library: agr init && agr add ./skills/your-skill",
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
    username: str | None = None,
) -> None:
    """
    Generic handler for adding any resource type.

    Args:
        resource_ref: Resource reference (e.g., "username/resource-name")
        resource_type: Type of resource (SKILL, COMMAND, or AGENT)
        resource_subdir: Destination subdirectory (e.g., "skills", "commands", "agents")
        overwrite: Whether to overwrite existing resource
        global_install: If True, install to ~/.claude/, else to ./.claude/
        username: GitHub username for namespaced installation
    """
    try:
        parsed_username, repo_name, name, path_segments = parse_resource_ref(resource_ref)
    except typer.BadParameter as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    # Use parsed username if not provided
    install_username = username or parsed_username

    dest = get_destination(resource_subdir, global_install)

    try:
        with fetch_spinner():
            fetch_resource(
                parsed_username, repo_name, name, path_segments, dest, resource_type, overwrite,
                username=install_username,
            )
        print_success_message(resource_type.value, name, parsed_username, repo_name)
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


def _get_namespaced_resource_path(
    name: str,
    username: str,
    resource_subdir: str,
    global_install: bool,
) -> Path:
    """Build the namespaced local path for a resource."""
    dest = get_destination(resource_subdir, global_install)
    if resource_subdir == "skills":
        return dest / username / name
    else:
        return dest / username / f"{name}.md"


def _remove_from_agr_toml(
    name: str,
    username: str | None = None,
    global_install: bool = False,
) -> None:
    """
    Remove a dependency from agr.toml after removing resource.

    Args:
        name: Resource name
        username: GitHub username (for building ref)
        global_install: If True, don't update agr.toml
    """
    if global_install:
        return

    try:
        from agr.config import find_config, AgrConfig

        config_path = find_config()
        if not config_path:
            return

        config = AgrConfig.load(config_path)

        # Try to find and remove matching dependency
        # Could be "username/name" or "username/repo/name"
        refs_to_check = []
        if username:
            refs_to_check.append(f"{username}/{name}")

        # Also check all handles ending with /name
        for dep in config.dependencies:
            if dep.handle and dep.handle.endswith(f"/{name}"):
                refs_to_check.append(dep.handle)

        removed = False
        for ref in refs_to_check:
            if config.remove_by_handle(ref):
                removed = True
                break

        if removed:
            config.save(config_path)
            console.print(f"[dim]Removed from agr.toml[/dim]")
    except Exception:
        # Don't fail the remove if agr.toml update fails
        pass


def _find_namespaced_resource(
    name: str,
    resource_subdir: str,
    global_install: bool,
) -> tuple[Path | None, str | None]:
    """
    Search all namespaced directories for a resource.

    Returns:
        Tuple of (path, username) if found, (None, None) otherwise
    """
    dest = get_destination(resource_subdir, global_install)
    if not dest.exists():
        return None, None

    for username_dir in dest.iterdir():
        if username_dir.is_dir():
            if resource_subdir == "skills":
                resource_path = username_dir / name
                if resource_path.is_dir() and (resource_path / "SKILL.md").exists():
                    return resource_path, username_dir.name
            else:
                resource_path = username_dir / f"{name}.md"
                if resource_path.is_file():
                    return resource_path, username_dir.name

    return None, None


def handle_remove_resource(
    name: str,
    resource_type: ResourceType,
    resource_subdir: str,
    global_install: bool = False,
    username: str | None = None,
) -> None:
    """
    Generic handler for removing any resource type.

    Removes the resource immediately without confirmation.
    Searches namespaced paths first, then falls back to flat paths.

    Args:
        name: Name of the resource to remove
        resource_type: Type of resource (SKILL, COMMAND, or AGENT)
        resource_subdir: Destination subdirectory (e.g., "skills", "commands", "agents")
        global_install: If True, remove from ~/.claude/, else from ./.claude/
        username: GitHub username for namespaced path lookup
    """
    local_path = None
    found_username = username

    # Try namespaced path first if username provided
    if username:
        namespaced_path = _get_namespaced_resource_path(name, username, resource_subdir, global_install)
        if namespaced_path.exists():
            local_path = namespaced_path

    # If not found and no username, search all namespaced directories
    if local_path is None and username is None:
        local_path, found_username = _find_namespaced_resource(name, resource_subdir, global_install)

    # If still not found, try flat path
    if local_path is None:
        flat_path = get_local_resource_path(name, resource_subdir, global_install)
        if flat_path.exists():
            local_path = flat_path
            found_username = None  # Flat path, no username

    if local_path is None:
        typer.echo(
            f"Error: {resource_type.value.capitalize()} '{name}' not found locally",
            err=True,
        )
        raise typer.Exit(1)

    try:
        if local_path.is_dir():
            shutil.rmtree(local_path)
        else:
            local_path.unlink()

        # Clean up empty username directory if this was a namespaced resource
        if found_username:
            username_dir = local_path.parent
            if username_dir.exists() and not any(username_dir.iterdir()):
                username_dir.rmdir()

        console.print(f"[green]Removed {resource_type.value} '{name}'[/green]")

        # Update agr.toml
        _remove_from_agr_toml(name, found_username, global_install)

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


# Unified handlers for auto-detection


def discover_local_resource_type(name: str, global_install: bool) -> DiscoveryResult:
    """
    Discover which resource types exist locally for a given name.

    Searches both namespaced paths (.claude/skills/username/name/) and
    flat paths (.claude/skills/name/) for backward compatibility.

    The name can be:
    - Simple name: "commit" - searches all usernames and flat path
    - Full ref: "kasperjunge/commit" - searches specific username only

    Args:
        name: Resource name or full ref (username/name) to search for
        global_install: If True, search in ~/.claude/, else in ./.claude/

    Returns:
        DiscoveryResult with list of found resource types
    """
    result = DiscoveryResult()
    base_path = get_base_path(global_install)

    # Check if name is a full ref (username/name)
    if "/" in name:
        parts = name.split("/")
        if len(parts) == 2:
            username, resource_name = parts
            # Search only in specific namespace
            _discover_in_namespace(
                base_path, resource_name, username, result
            )
            return result

    # Simple name - search both namespaced and flat paths
    # First check namespaced paths (.claude/skills/*/name/)
    _discover_in_all_namespaces(base_path, name, result)

    # Then check flat paths (.claude/skills/name/) for backward compat
    _discover_in_flat_path(base_path, name, result)

    return result


def _discover_in_namespace(
    base_path: Path,
    name: str,
    username: str,
    result: DiscoveryResult,
) -> None:
    """Discover resources in a specific username namespace."""
    # Check for skill
    skill_path = base_path / "skills" / username / name
    if skill_path.is_dir() and (skill_path / "SKILL.md").exists():
        result.resources.append(
            DiscoveredResource(
                name=name,
                resource_type=ResourceType.SKILL,
                path_segments=[name],
                username=username,
            )
        )

    # Check for command
    command_path = base_path / "commands" / username / f"{name}.md"
    if command_path.is_file():
        result.resources.append(
            DiscoveredResource(
                name=name,
                resource_type=ResourceType.COMMAND,
                path_segments=[name],
                username=username,
            )
        )

    # Check for agent
    agent_path = base_path / "agents" / username / f"{name}.md"
    if agent_path.is_file():
        result.resources.append(
            DiscoveredResource(
                name=name,
                resource_type=ResourceType.AGENT,
                path_segments=[name],
                username=username,
            )
        )


def _discover_in_all_namespaces(
    base_path: Path,
    name: str,
    result: DiscoveryResult,
) -> None:
    """Discover resources across all username namespaces."""
    # Check skills namespaces
    skills_dir = base_path / "skills"
    if skills_dir.is_dir():
        for username_dir in skills_dir.iterdir():
            if username_dir.is_dir():
                skill_path = username_dir / name
                if skill_path.is_dir() and (skill_path / "SKILL.md").exists():
                    result.resources.append(
                        DiscoveredResource(
                            name=name,
                            resource_type=ResourceType.SKILL,
                            path_segments=[name],
                            username=username_dir.name,
                        )
                    )

    # Check commands namespaces
    commands_dir = base_path / "commands"
    if commands_dir.is_dir():
        for username_dir in commands_dir.iterdir():
            if username_dir.is_dir():
                command_path = username_dir / f"{name}.md"
                if command_path.is_file():
                    result.resources.append(
                        DiscoveredResource(
                            name=name,
                            resource_type=ResourceType.COMMAND,
                            path_segments=[name],
                            username=username_dir.name,
                        )
                    )

    # Check agents namespaces
    agents_dir = base_path / "agents"
    if agents_dir.is_dir():
        for username_dir in agents_dir.iterdir():
            if username_dir.is_dir():
                agent_path = username_dir / f"{name}.md"
                if agent_path.is_file():
                    result.resources.append(
                        DiscoveredResource(
                            name=name,
                            resource_type=ResourceType.AGENT,
                            path_segments=[name],
                            username=username_dir.name,
                        )
                    )


def _discover_in_flat_path(
    base_path: Path,
    name: str,
    result: DiscoveryResult,
) -> None:
    """Discover resources in flat (non-namespaced) paths for backward compat."""
    # Check for skill (directory with SKILL.md)
    skill_path = base_path / "skills" / name
    if skill_path.is_dir() and (skill_path / "SKILL.md").exists():
        result.resources.append(
            DiscoveredResource(
                name=name,
                resource_type=ResourceType.SKILL,
                path_segments=[name],
                username=None,
            )
        )

    # Check for command (markdown file)
    command_path = base_path / "commands" / f"{name}.md"
    if command_path.is_file():
        result.resources.append(
            DiscoveredResource(
                name=name,
                resource_type=ResourceType.COMMAND,
                path_segments=[name],
                username=None,
            )
        )

    # Check for agent (markdown file)
    agent_path = base_path / "agents" / f"{name}.md"
    if agent_path.is_file():
        result.resources.append(
            DiscoveredResource(
                name=name,
                resource_type=ResourceType.AGENT,
                path_segments=[name],
                username=None,
            )
        )



def _build_dependency_ref(username: str, repo_name: str, name: str) -> str:
    """Build the dependency reference for agr.toml."""
    if repo_name == DEFAULT_REPO_NAME:
        return f"{username}/{name}"
    return f"{username}/{repo_name}/{name}"


def _add_to_agr_toml(
    resource_ref: str,
    resource_type: ResourceType | None = None,
    global_install: bool = False,
) -> None:
    """
    Add a dependency to agr.toml after successful install.

    Args:
        resource_ref: The dependency reference (e.g., "kasperjunge/commit")
        resource_type: Optional type hint for the dependency
        global_install: If True, don't update agr.toml (global resources aren't tracked)
    """
    # Don't track global installs in agr.toml
    if global_install:
        return

    try:
        config_path, config = get_or_create_config()
        type_str = resource_type.value if resource_type else "skill"
        config.add_remote(resource_ref, type_str)
        config.save(config_path)
        console.print(f"[dim]Added to agr.toml[/dim]")
    except Exception:
        # Don't fail the install if agr.toml update fails
        pass


def handle_add_unified(
    resource_ref: str,
    resource_type: str | None = None,
    overwrite: bool = False,
    global_install: bool = False,
) -> None:
    """
    Unified handler for adding any resource with auto-detection.

    Installs resources to namespaced paths (.claude/skills/username/name/)
    and tracks them in agr.toml.

    Args:
        resource_ref: Resource reference (e.g., "username/resource-name")
        resource_type: Optional explicit type ("skill", "command", "agent", "bundle")
        overwrite: Whether to overwrite existing resource
        global_install: If True, install to ~/.claude/, else to ./.claude/
    """
    try:
        username, repo_name, name, path_segments = parse_resource_ref(resource_ref)
    except typer.BadParameter as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    # Build dependency ref for agr.toml
    dep_ref = _build_dependency_ref(username, repo_name, name)

    # If explicit type provided, delegate to specific handler
    if resource_type:
        type_lower = resource_type.lower()
        type_map = {
            "skill": (ResourceType.SKILL, "skills"),
            "command": (ResourceType.COMMAND, "commands"),
            "agent": (ResourceType.AGENT, "agents"),
        }

        if type_lower == "bundle":
            handle_add_bundle(resource_ref, overwrite, global_install)
            return

        if type_lower not in type_map:
            typer.echo(f"Error: Unknown resource type '{resource_type}'. Use: skill, command, agent, or bundle.", err=True)
            raise typer.Exit(1)

        res_type, subdir = type_map[type_lower]
        handle_add_resource(resource_ref, res_type, subdir, overwrite, global_install, username=username)
        _add_to_agr_toml(dep_ref, res_type, global_install)
        return

    # Auto-detect type by downloading repo once
    try:
        with fetch_spinner():
            with downloaded_repo(username, repo_name) as repo_dir:
                discovery = discover_resource_type_from_dir(repo_dir, name, path_segments)

                if discovery.is_empty:
                    typer.echo(
                        f"Error: Resource '{name}' not found in {username}/{repo_name}.\n"
                        f"Searched in: skills, commands, agents, bundles.",
                        err=True,
                    )
                    raise typer.Exit(1)

                if discovery.is_ambiguous:
                    # Build helpful example commands for each type found
                    ref = f"{username}/{name}" if repo_name == DEFAULT_REPO_NAME else f"{username}/{repo_name}/{name}"
                    examples = "\n".join(
                        f"  agr add {ref} --type {t}" for t in discovery.found_types
                    )
                    raise MultipleResourcesFoundError(
                        f"Resource '{name}' found in multiple types: {', '.join(discovery.found_types)}.\n"
                        f"Use --type to specify which one to install:\n{examples}"
                    )

                # Install the unique resource
                dest_base = get_base_path(global_install)

                if discovery.is_bundle:
                    bundle_name = path_segments[-1] if path_segments else name
                    result = fetch_bundle_from_repo_dir(repo_dir, bundle_name, dest_base, overwrite)
                    print_bundle_success_message(bundle_name, result, username, repo_name)
                    # Bundles are deprecated, don't add to agr.toml
                else:
                    resource = discovery.resources[0]
                    res_config = RESOURCE_CONFIGS[resource.resource_type]
                    dest = dest_base / res_config.dest_subdir
                    # Use namespaced path with username
                    fetch_resource_from_repo_dir(
                        repo_dir, name, path_segments, dest, resource.resource_type, overwrite,
                        username=username,
                    )
                    print_success_message(resource.resource_type.value, name, username, repo_name)
                    # Add to agr.toml
                    _add_to_agr_toml(dep_ref, resource.resource_type, global_install)

    except (RepoNotFoundError, ResourceExistsError, BundleNotFoundError, MultipleResourcesFoundError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except AgrError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


def handle_remove_unified(
    name: str,
    resource_type: str | None = None,
    global_install: bool = False,
) -> None:
    """
    Unified handler for removing any resource with auto-detection.

    Supports both simple names ("commit") and full refs ("kasperjunge/commit").
    Searches namespaced paths first, then falls back to flat paths.

    Args:
        name: Resource name or full ref (username/name) to remove
        resource_type: Optional explicit type ("skill", "command", "agent", "bundle")
        global_install: If True, remove from ~/.claude/, else from ./.claude/
    """
    # Parse if name is a full ref
    parsed_username = None
    resource_name = name
    if "/" in name:
        parts = name.split("/")
        if len(parts) == 2:
            parsed_username, resource_name = parts

    # If explicit type provided, delegate to specific handler
    if resource_type:
        type_lower = resource_type.lower()
        type_map = {
            "skill": (ResourceType.SKILL, "skills"),
            "command": (ResourceType.COMMAND, "commands"),
            "agent": (ResourceType.AGENT, "agents"),
        }

        if type_lower == "bundle":
            handle_remove_bundle(resource_name, global_install)
            return

        if type_lower not in type_map:
            typer.echo(f"Error: Unknown resource type '{resource_type}'. Use: skill, command, agent, or bundle.", err=True)
            raise typer.Exit(1)

        res_type, subdir = type_map[type_lower]
        handle_remove_resource(resource_name, res_type, subdir, global_install, username=parsed_username)
        return

    # Auto-detect type from local files
    discovery = discover_local_resource_type(name, global_install)

    if discovery.is_empty:
        typer.echo(
            f"Error: Resource '{name}' not found locally.\n"
            f"Searched in: skills, commands, agents.",
            err=True,
        )
        raise typer.Exit(1)

    if discovery.is_ambiguous:
        # Build helpful example commands for each type found
        examples = "\n".join(
            f"  agr remove {name} --type {t}" for t in discovery.found_types
        )
        typer.echo(
            f"Error: Resource '{name}' found in multiple types: {', '.join(discovery.found_types)}.\n"
            f"Use --type to specify which one to remove:\n{examples}",
            err=True,
        )
        raise typer.Exit(1)

    # Remove the unique resource
    resource = discovery.resources[0]
    # Pass username from discovery (could be from namespaced path or parsed ref)
    username = resource.username or parsed_username
    handle_remove_resource(
        resource_name,
        resource.resource_type,
        RESOURCE_CONFIGS[resource.resource_type].dest_subdir,
        global_install,
        username=username,
    )


def discover_runnable_resource(
    repo_dir: Path,
    name: str,
    path_segments: list[str],
) -> DiscoveryResult:
    """
    Discover runnable resources (skills and commands only, not agents/bundles).

    Used by agrx to determine what type of resource to run.

    Args:
        repo_dir: Path to extracted repository
        name: Display name of the resource
        path_segments: Path segments for the resource

    Returns:
        DiscoveryResult with list of discovered runnable resources
    """
    result = DiscoveryResult()

    # Check for skill (directory with SKILL.md)
    skill_config = RESOURCE_CONFIGS[ResourceType.SKILL]
    skill_path = repo_dir / skill_config.source_subdir
    for segment in path_segments:
        skill_path = skill_path / segment
    if skill_path.is_dir() and (skill_path / "SKILL.md").exists():
        result.resources.append(
            DiscoveredResource(
                name=name,
                resource_type=ResourceType.SKILL,
                path_segments=path_segments,
            )
        )

    # Check for command (markdown file)
    command_config = RESOURCE_CONFIGS[ResourceType.COMMAND]
    command_path = repo_dir / command_config.source_subdir
    for segment in path_segments[:-1]:
        command_path = command_path / segment
    if path_segments:
        command_path = command_path / f"{path_segments[-1]}.md"
    if command_path.is_file():
        result.resources.append(
            DiscoveredResource(
                name=name,
                resource_type=ResourceType.COMMAND,
                path_segments=path_segments,
            )
        )

    return result
