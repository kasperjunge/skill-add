"""Resource handlers for agr CLI commands."""

import random
import shutil
from pathlib import Path

import typer

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
from agr.handle import parse_handle
from agr.resolver import resolve_remote_resource, ResourceSource

from agr.cli.paths import (
    console,
    DEFAULT_REPO_NAME,
    TYPE_TO_SUBDIR,
    error_exit,
    fetch_spinner,
    get_base_path,
    get_destination,
    get_namespaced_destination,
    parse_resource_ref,
)
from agr.cli.discovery import discover_local_resource_type

# Mapping from type string to (ResourceType, subdir) tuple
# Used by unified handlers for explicit type resolution
RESOURCE_TYPE_MAP: dict[str, tuple[ResourceType, str]] = {
    "skill": (ResourceType.SKILL, "skills"),
    "command": (ResourceType.COMMAND, "commands"),
    "agent": (ResourceType.AGENT, "agents"),
    "rule": (ResourceType.RULE, "rules"),
}


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
    elif source == ResourceSource.REPO_ROOT:
        source_indicator = " [dim](auto-discovered)[/dim]"

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
        error_exit(str(e))

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
        error_exit(str(e))


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
    from agr.handle import ParsedHandle

    base_path = get_base_path(global_install)
    handle = ParsedHandle.from_components(username, name, path_segments)

    # Map resource_subdir to resource type
    subdir_to_type = {"skills": "skill", "commands": "command", "agents": "agent", "rules": "rule"}
    resource_type = subdir_to_type.get(resource_subdir, "skill")

    return handle.to_resource_path(base_path, resource_type)


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
            elif ":" not in item.name:
                resource_path = item / name
                if resource_path.is_dir() and (resource_path / "SKILL.md").exists():
                    return resource_path, item.name
    else:
        # Commands, agents, and rules use nested format: username/name.md
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
        error_exit(f"{resource_type.value.capitalize()} '{name}' not found locally")

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
        error_exit(f"Failed to remove resource: {e}")


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
        "Create your own bundle: organize resources under .claude/*/bundle-name/",
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
        error_exit(str(e))

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
        error_exit(str(e))


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
        error_exit(str(e))
    except OSError as e:
        error_exit(f"Failed to remove bundle: {e}")


# Unified handlers for auto-detection


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
        console.print("[dim]Added to agr.toml[/dim]")
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
        error_exit(str(e))

    # Build dependency ref for agr.toml
    dep_ref = _build_dependency_ref(username, repo_name, name)

    # If explicit type provided, delegate to specific handler
    if resource_type:
        type_lower = resource_type.lower()

        if type_lower == "bundle":
            handle_add_bundle(resource_ref, overwrite, global_install)
            return

        if type_lower not in RESOURCE_TYPE_MAP:
            error_exit(f"Unknown resource type '{resource_type}'. Use: skill, command, agent, or bundle.")

        res_type, subdir = RESOURCE_TYPE_MAP[type_lower]
        handle_add_resource(resource_ref, res_type, subdir, overwrite, global_install, username=username)
        _add_to_agr_toml(dep_ref, res_type, global_install)
        return

    # Auto-detect type by downloading repo once
    try:
        with fetch_spinner():
            with downloaded_repo(username, repo_name) as repo_dir:
                # First, check agr.toml for resource definition
                resolved = resolve_remote_resource(repo_dir, name)

                if resolved and resolved.source in (ResourceSource.AGR_TOML, ResourceSource.REPO_ROOT):
                    # Resource found in agr.toml or auto-discovered in repo - use explicit path
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
                            package_name=resolved.package_name,
                        )
                        print_success_message(
                            resolved.resource_type.value, name, username, repo_name,
                            source=resolved.source,
                        )
                        _add_to_agr_toml(dep_ref, resolved.resource_type, global_install)
                    else:
                        error_exit(f"Resource '{name}' found in agr.toml but has no type.")
                    return

                # Fallback: check .claude/ directory (existing behavior)
                discovery = discover_resource_type_from_dir(repo_dir, name, path_segments)

                if discovery.is_empty:
                    error_exit(
                        f"Resource '{name}' not found in {username}/{repo_name}.\n"
                        f"Searched in: agr.toml, skills, commands, agents, bundles."
                    )

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
        error_exit(str(e))
    except AgrError as e:
        error_exit(str(e))


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
    # Parse the name using centralized handle parsing
    parsed = parse_handle(name)
    parsed_username = parsed.username
    resource_name = parsed.simple_name

    # If explicit type provided, delegate to specific handler
    if resource_type:
        type_lower = resource_type.lower()

        if type_lower == "bundle":
            handle_remove_bundle(resource_name, global_install)
            return

        if type_lower not in RESOURCE_TYPE_MAP:
            error_exit(f"Unknown resource type '{resource_type}'. Use: skill, command, agent, or bundle.")

        res_type, subdir = RESOURCE_TYPE_MAP[type_lower]
        handle_remove_resource(resource_name, res_type, subdir, global_install, username=parsed_username)
        return

    # Auto-detect type from local files
    # Pass the original name to preserve any username/format info for discovery
    discovery = discover_local_resource_type(name, global_install)

    if discovery.is_empty:
        error_exit(
            f"Resource '{name}' not found locally.\n"
            f"Searched in: skills, commands, agents."
        )

    if discovery.is_ambiguous:
        # Build helpful example commands for each type found
        examples = "\n".join(
            f"  agr remove {name} --type {t}" for t in discovery.found_types
        )
        error_exit(
            f"Resource '{name}' found in multiple types: {', '.join(discovery.found_types)}.\n"
            f"Use --type to specify which one to remove:\n{examples}"
        )

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
