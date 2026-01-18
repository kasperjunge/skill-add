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
    ConfigParseError,
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
from agr.resolver import resolve_remote_resource, ResourceSource

# Shared console instance for all CLI modules
console = Console()

# Default repository name when not specified
DEFAULT_REPO_NAME = "agent-resources"

# Shared mapping from resource type string to subdirectory
TYPE_TO_SUBDIR: dict[str, str] = {
    "skill": "skills",
    "command": "commands",
    "agent": "agents",
    "package": "packages",
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


def print_success_message(
    resource_type: str,
    name: str,
    username: str,
    repo: str,
    source: ResourceSource | None = None,
) -> None:
    """Print branded success message with rotating CTA.

    Args:
        resource_type: Type of resource (skill, command, agent)
        name: Resource name
        username: GitHub username
        repo: Repository name
        source: Where the resource was resolved from (for showing source indicator)
    """
    source_indicator = ""
    if source == ResourceSource.AGR_TOML:
        source_indicator = " [dim](via agr.toml)[/dim]"
    elif source == ResourceSource.CLAUDE_DIR:
        source_indicator = " [dim](via .claude/)[/dim]"

    console.print(f"[green]Added {resource_type} '{name}'[/green]{source_indicator}")

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
    path_segments: list[str] | None = None,
) -> Path:
    """Build the namespaced local path for a resource.

    Skills use flattened colon format (e.g., "skills/kasperjunge:seo").
    Commands and agents use nested format (e.g., "commands/username/name.md").

    Args:
        name: Simple resource name
        username: GitHub username
        resource_subdir: "skills", "commands", or "agents"
        global_install: Whether to use global ~/.claude/ path
        path_segments: Optional full path segments for nested skills
                       e.g., ["product-strategy", "growth-hacker"]
    """
    dest = get_destination(resource_subdir, global_install)
    if resource_subdir == "skills":
        # Skills use flattened colon format: skills/username:path:segments
        if path_segments and len(path_segments) > 1:
            # Nested skill - use full path segments
            flattened_name = f"{username}:{':'.join(path_segments)}"
        else:
            # Simple skill - just username:name
            flattened_name = f"{username}:{name}"
        return dest / flattened_name
    else:
        # Commands and agents use nested format
        return dest / username / f"{name}.md"


def _remove_from_agr_toml(
    name: str,
    username: str | None = None,
    global_install: bool = False,
) -> None:
    """
    Remove a dependency from agr.toml after removing resource.

    Uses centralized handle parsing for consistent matching between
    slash format (agr.toml) and colon format (filesystem).

    Args:
        name: Resource name (can be simple name, slash format, or colon format)
        username: GitHub username (for building ref if not in name)
        global_install: If True, don't update agr.toml
    """
    if global_install:
        return

    try:
        from agr.config import find_config, AgrConfig
        from agr.handle import parse_handle

        config_path = find_config()
        if not config_path:
            return

        config = AgrConfig.load(config_path)

        # Parse the input to normalize it
        parsed_input = parse_handle(name)
        effective_username = parsed_input.username or username

        # Find matching dependency using normalized comparison
        removed = False
        for dep in list(config.dependencies):
            if not dep.handle:
                continue

            # Use the matches_toml_handle method for consistent matching
            if parsed_input.matches_toml_handle(dep.handle):
                # Double-check username match if we have one
                if effective_username:
                    parsed_dep = parse_handle(dep.handle)
                    if parsed_dep.username and parsed_dep.username != effective_username:
                        continue

                config.remove_by_handle(dep.handle)
                removed = True
                break

        if removed:
            config.save(config_path)
            console.print("[dim]Removed from agr.toml[/dim]")
    except (ConfigParseError, ValueError, OSError) as e:
        console.print(f"[yellow]Warning: Could not update agr.toml: {e}[/yellow]")


def _find_namespaced_resource(
    name: str,
    resource_subdir: str,
    global_install: bool,
) -> tuple[Path | None, str | None]:
    """
    Search all namespaced directories for a resource.

    Skills use flattened colon format (e.g., "kasperjunge:seo").
    Commands and agents use nested format (e.g., "username/name.md").

    Returns:
        Tuple of (path, username) if found, (None, None) otherwise
    """
    from agr.handle import parse_handle

    dest = get_destination(resource_subdir, global_install)
    if not dest.exists():
        return None, None

    if resource_subdir == "skills":
        # Skills use flattened colon format at top level
        for item in dest.iterdir():
            if not item.is_dir():
                continue

            # Check flattened format: username:name or username:nested:name
            if ":" in item.name and (item / "SKILL.md").exists():
                parsed = parse_handle(item.name)
                if parsed.simple_name == name:
                    return item, parsed.username

            # Legacy nested format: username/name
            elif not ":" in item.name:
                resource_path = item / name
                if resource_path.is_dir() and (resource_path / "SKILL.md").exists():
                    return resource_path, item.name
    else:
        # Commands and agents use nested format: username/name.md
        for username_dir in dest.iterdir():
            if username_dir.is_dir():
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
    path_segments: list[str] | None = None,
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
        path_segments: Optional full path segments for nested skills
    """
    local_path = None
    found_username = username

    # Try namespaced path first if username provided
    if username:
        # Try new flattened format first (skills/username:name)
        namespaced_path = _get_namespaced_resource_path(
            name, username, resource_subdir, global_install, path_segments
        )
        if namespaced_path.exists():
            local_path = namespaced_path
        elif resource_subdir == "skills":
            # Fallback to legacy nested format (skills/username/name)
            dest = get_destination(resource_subdir, global_install)
            legacy_path = dest / username / name
            if legacy_path.is_dir() and (legacy_path / "SKILL.md").exists():
                local_path = legacy_path

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

    Searches namespaced paths (flattened colon format for skills, nested for commands/agents)
    and flat paths (.claude/skills/name/) for backward compatibility.

    The name can be:
    - Simple name: "commit" - searches all usernames and flat path
    - Full ref: "kasperjunge/commit" - searches specific username only
    - Colon format: "kasperjunge:commit" - parsed and searched

    Args:
        name: Resource name, full ref (username/name), or colon format to search for
        global_install: If True, search in ~/.claude/, else in ./.claude/

    Returns:
        DiscoveryResult with list of found resource types
    """
    from agr.handle import parse_handle

    result = DiscoveryResult()
    base_path = get_base_path(global_install)
    parsed = parse_handle(name)

    # Search namespaced paths (handles both flattened skills and nested commands/agents)
    # This function now properly parses the input to extract username and simple_name
    _discover_in_all_namespaces(base_path, name, result)

    # Then check flat paths (.claude/skills/name/) for backward compat
    _discover_in_flat_path(base_path, parsed.simple_name, result)

    return result


def _discover_in_namespace(
    base_path: Path,
    name: str,
    username: str,
    result: DiscoveryResult,
) -> None:
    """Discover resources in a specific username namespace.

    Skills use flattened colon format (e.g., "kasperjunge:seo").
    Commands and agents use nested format (e.g., "username/name.md").
    """
    from agr.handle import ParsedHandle

    # Check for skill (flattened colon format)
    flattened_skill_name = f"{username}:{name}"
    skill_path = base_path / "skills" / flattened_skill_name
    if skill_path.is_dir() and (skill_path / "SKILL.md").exists():
        result.resources.append(
            DiscoveredResource(
                name=name,
                resource_type=ResourceType.SKILL,
                path_segments=[name],
                username=username,
            )
        )
    else:
        # Fallback: check legacy nested format for backward compat
        legacy_skill_path = base_path / "skills" / username / name
        if legacy_skill_path.is_dir() and (legacy_skill_path / "SKILL.md").exists():
            result.resources.append(
                DiscoveredResource(
                    name=name,
                    resource_type=ResourceType.SKILL,
                    path_segments=[name],
                    username=username,
                )
            )

    # Check for command (nested format)
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

    # Check for agent (nested format)
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
    """Discover resources across all username namespaces.

    Skills are stored in flattened colon format (e.g., "kasperjunge:seo").
    Commands and agents use nested directory format (e.g., "username/name.md").
    """
    from agr.handle import parse_handle

    # Parse input to get components
    parsed_input = parse_handle(name)
    target_name = parsed_input.simple_name
    target_username = parsed_input.username

    # Check skills - stored with flattened colon names at top level
    skills_dir = base_path / "skills"
    if skills_dir.is_dir():
        for item in skills_dir.iterdir():
            if not item.is_dir():
                continue

            # Check for flattened colon format: "username:name" or "username:nested:name"
            if ":" in item.name and (item / "SKILL.md").exists():
                parsed_dir = parse_handle(item.name)
                # Match if names equal and username matches (if specified)
                if parsed_dir.simple_name == target_name:
                    if target_username is None or parsed_dir.username == target_username:
                        result.resources.append(
                            DiscoveredResource(
                                name=target_name,
                                resource_type=ResourceType.SKILL,
                                path_segments=parsed_dir.path_segments,
                                username=parsed_dir.username,
                            )
                        )
            # Also check legacy nested format: username/name (backward compat)
            elif not ":" in item.name:
                skill_path = item / target_name
                if skill_path.is_dir() and (skill_path / "SKILL.md").exists():
                    result.resources.append(
                        DiscoveredResource(
                            name=target_name,
                            resource_type=ResourceType.SKILL,
                            path_segments=[target_name],
                            username=item.name,
                        )
                    )

    # Check commands namespaces (nested format: username/name.md)
    commands_dir = base_path / "commands"
    if commands_dir.is_dir():
        for username_dir in commands_dir.iterdir():
            if username_dir.is_dir():
                # Skip if looking for specific username and this doesn't match
                if target_username and username_dir.name != target_username:
                    continue
                command_path = username_dir / f"{target_name}.md"
                if command_path.is_file():
                    result.resources.append(
                        DiscoveredResource(
                            name=target_name,
                            resource_type=ResourceType.COMMAND,
                            path_segments=[target_name],
                            username=username_dir.name,
                        )
                    )

    # Check agents namespaces (nested format: username/name.md)
    agents_dir = base_path / "agents"
    if agents_dir.is_dir():
        for username_dir in agents_dir.iterdir():
            if username_dir.is_dir():
                # Skip if looking for specific username and this doesn't match
                if target_username and username_dir.name != target_username:
                    continue
                agent_path = username_dir / f"{target_name}.md"
                if agent_path.is_file():
                    result.resources.append(
                        DiscoveredResource(
                            name=target_name,
                            resource_type=ResourceType.AGENT,
                            path_segments=[target_name],
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
    except (ConfigParseError, ValueError, OSError) as e:
        console.print(f"[yellow]Warning: Could not add to agr.toml: {e}[/yellow]")


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
                # First, check agr.toml for resource definition
                resolved = resolve_remote_resource(repo_dir, name)

                if resolved and resolved.source == ResourceSource.AGR_TOML:
                    # Resource found in agr.toml - use explicit path
                    dest_base = get_base_path(global_install)

                    if resolved.is_package:
                        # Package handling
                        bundle_name = path_segments[-1] if path_segments else name
                        result = fetch_bundle_from_repo_dir(repo_dir, bundle_name, dest_base, overwrite)
                        print_bundle_success_message(bundle_name, result, username, repo_name)
                    elif resolved.resource_type:
                        res_config = RESOURCE_CONFIGS[resolved.resource_type]
                        dest = dest_base / res_config.dest_subdir
                        fetch_resource_from_repo_dir(
                            repo_dir, name, path_segments, dest, resolved.resource_type, overwrite,
                            username=username,
                            source_path=resolved.path,
                        )
                        print_success_message(
                            resolved.resource_type.value, name, username, repo_name,
                            source=resolved.source,
                        )
                        _add_to_agr_toml(dep_ref, resolved.resource_type, global_install)
                    else:
                        typer.echo(
                            f"Error: Resource '{name}' found in agr.toml but has no type.",
                            err=True,
                        )
                        raise typer.Exit(1)
                    return

                # Fallback: check .claude/ directory (existing behavior)
                discovery = discover_resource_type_from_dir(repo_dir, name, path_segments)

                if discovery.is_empty:
                    typer.echo(
                        f"Error: Resource '{name}' not found in {username}/{repo_name}.\n"
                        f"Searched in: agr.toml, skills, commands, agents, bundles.",
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

                # Install the unique resource from .claude/
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
                    print_success_message(
                        resource.resource_type.value, name, username, repo_name,
                        source=ResourceSource.CLAUDE_DIR,
                    )
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

    Supports:
    - Simple names: "commit"
    - Full refs: "kasperjunge/commit" or "kasperjunge/repo/commit"
    - Colon format: "kasperjunge:commit" (from filesystem)

    Searches namespaced paths (flattened for skills, nested for commands/agents)
    first, then falls back to flat paths.

    Args:
        name: Resource name, full ref, or colon format to remove
        resource_type: Optional explicit type ("skill", "command", "agent", "bundle")
        global_install: If True, remove from ~/.claude/, else from ./.claude/
    """
    from agr.handle import parse_handle

    # Parse the name using centralized handle parsing
    parsed = parse_handle(name)
    parsed_username = parsed.username
    resource_name = parsed.simple_name

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
    # Pass the original name to preserve any username/format info for discovery
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
        path_segments=resource.path_segments,
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
