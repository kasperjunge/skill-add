"""Sync command for agr."""

import shutil
from pathlib import Path

import typer

from agr.config import AgrConfig, Dependency, find_config
from agr.exceptions import AgrError, RepoNotFoundError, ResourceNotFoundError
from agr.fetcher import RESOURCE_CONFIGS, ResourceType, fetch_resource
from agr.github import get_username_from_git_remote
from agr.cli.common import (
    DEFAULT_REPO_NAME,
    TYPE_TO_SUBDIR,
    console,
    fetch_spinner,
    find_repo_root,
    get_base_path,
)
from agr.cli.paths import remove_path
from agr.utils import (
    compute_flattened_resource_name,
    compute_path_segments,
    find_package_context,
    update_skill_md_name,
)

app = typer.Typer()

# Mapping from type string to ResourceType enum
TYPE_STRING_TO_ENUM = {
    "skill": ResourceType.SKILL,
    "command": ResourceType.COMMAND,
    "agent": ResourceType.AGENT,
}


def _parse_dependency_ref(ref: str) -> tuple[str, str, str]:
    """Parse a dependency reference from agr.toml.

    Supports:
    - "username/name" -> username, DEFAULT_REPO_NAME, name
    - "username/repo/name" -> username, repo, name
    """
    parts = ref.split("/")
    if len(parts) == 2:
        return parts[0], DEFAULT_REPO_NAME, parts[1]
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    raise ValueError(f"Invalid dependency reference: {ref}")


def _is_resource_installed(
    username: str,
    name: str,
    resource_type: ResourceType,
    base_path: Path,
) -> bool:
    """Check if a resource is installed at the namespaced path."""
    from agr.handle import ParsedHandle

    config = RESOURCE_CONFIGS[resource_type]
    handle = ParsedHandle.from_components(username, name)

    if config.is_directory:
        # Skills: .claude/skills/<flattened_name>/SKILL.md
        resource_path = handle.to_skill_path(base_path)
        return resource_path.is_dir() and (resource_path / "SKILL.md").exists()
    else:
        # Commands/Agents: .claude/commands/username/name.md
        resource_path = handle.to_resource_path(base_path, resource_type.value)
        return resource_path.is_file()


def _type_string_to_enum(type_str: str) -> ResourceType | None:
    """Convert type string to ResourceType enum, or None if unknown."""
    return TYPE_STRING_TO_ENUM.get(type_str.lower())


def _discover_installed_namespaced_resources(
    base_path: Path,
) -> set[str]:
    """
    Discover all installed namespaced resources.

    Returns set of dependency refs in agr.toml format (slash-separated).
    For skills with flattened names like "kasperjunge:commit",
    returns "kasperjunge/commit".

    Uses centralized handle module for consistent conversion.
    """
    from agr.handle import skill_dirname_to_toml_handle

    installed = set()

    # Check skills - stored with flattened colon names like "kasperjunge:commit"
    skills_dir = base_path / "skills"
    if skills_dir.is_dir():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                if ":" in skill_dir.name:
                    # Use centralized conversion
                    toml_handle = skill_dirname_to_toml_handle(skill_dir.name)
                    installed.add(toml_handle)

    # Check commands and agents (nested format: username/[path/]name.md)
    for type_dir in ["commands", "agents"]:
        type_path = base_path / type_dir
        if not type_path.is_dir():
            continue
        for username_dir in type_path.iterdir():
            if not username_dir.is_dir():
                continue
            for md_file in username_dir.rglob("*.md"):
                # Build relative path from username dir
                # e.g., pkg/infra/deploy.md -> pkg/infra/deploy
                rel_path = md_file.relative_to(username_dir)
                parts = list(rel_path.parts)
                parts[-1] = rel_path.stem  # Remove .md extension
                handle_path = "/".join(parts)
                installed.add(f"{username_dir.name}/{handle_path}")

    return installed


def _remove_namespaced_resource(username: str, name: str, base_path: Path) -> None:
    """Remove a namespaced resource from disk.

    Uses ParsedHandle for consistent path building across resource types.
    For example, username="kasperjunge", name="commit"
    will remove ".claude/skills/kasperjunge:commit/".

    Args:
        username: GitHub username
        name: Resource name (may contain "/" for nested paths)
        base_path: Base .claude directory path
    """
    from agr.handle import ParsedHandle

    handle = ParsedHandle.from_components(username, name)
    paths_to_try = [
        handle.to_skill_path(base_path),
        handle.to_command_path(base_path),
        handle.to_agent_path(base_path),
    ]

    for path in paths_to_try:
        if path.exists():
            remove_path(path)
            return




def _sync_local_dependency(
    dep: Dependency,
    username: str,
    base_path: Path,
    repo_root: Path,
) -> tuple[str | None, str | None, tuple[str, str] | None]:
    """Sync a single local dependency to .claude directory.

    Returns:
        Tuple of (installed_name, updated_name, error_tuple).
        Only one will be non-None based on the action taken.
    """
    if not dep.path:
        return (None, None, None)

    source_path = repo_root / dep.path
    if not source_path.exists():
        return (None, None, (dep.path, f"Source path does not exist: {source_path}"))

    # Determine destination path based on type
    subdir = TYPE_TO_SUBDIR.get(dep.type, "skills")

    # Handle package explosion
    if dep.type == "package":
        name = source_path.name
        try:
            from agr.cli.add import _explode_package
            # Check if any exploded skills exist (using flattened names)
            skills_dir = base_path / "skills"
            pkg_prefix = f"{username}:{name}:"
            has_existing_skills = skills_dir.is_dir() and any(
                d.name.startswith(pkg_prefix) for d in skills_dir.iterdir() if d.is_dir()
            )
            is_update = has_existing_skills or any([
                (base_path / "commands" / username / name).exists(),
                (base_path / "agents" / username / name).exists(),
            ])
            _explode_package(source_path, username, name, base_path)
            if is_update:
                return (None, name, None)
            return (name, None, None)
        except Exception as e:
            return (None, None, (name, str(e)))

    # Check if source is inside a package
    package_name, _ = find_package_context(source_path)

    # Build destination path
    if dep.type == "skill":
        # Skills use flattened colon-namespaced directory names
        path_segments = compute_path_segments(source_path)
        flattened_name = compute_flattened_resource_name(username, path_segments, package_name)
        dest_path = base_path / subdir / flattened_name
        name = flattened_name
    else:
        # Commands/agents are files - include nested path structure
        path_segments = compute_path_segments(source_path)
        name = source_path.stem
        if package_name:
            all_segments = [package_name] + path_segments
        else:
            all_segments = path_segments
        nested_dirs = all_segments[:-1]
        if nested_dirs:
            dest_path = base_path / subdir / username / Path(*nested_dirs) / f"{name}.md"
        else:
            dest_path = base_path / subdir / username / f"{name}.md"

    try:
        is_update = dest_path.exists()

        # Check if source is newer than destination
        if is_update:
            if source_path.is_dir():
                source_marker = source_path / "SKILL.md"
                dest_marker = dest_path / "SKILL.md"
                if source_marker.exists() and dest_marker.exists():
                    if source_marker.stat().st_mtime <= dest_marker.stat().st_mtime:
                        return (None, None, None)  # Up to date
            elif source_path.stat().st_mtime <= dest_path.stat().st_mtime:
                return (None, None, None)  # Up to date

            # Remove existing before updating
            if dest_path.is_dir():
                shutil.rmtree(dest_path)
            else:
                dest_path.unlink()

        # Create parent directories
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy source to destination
        if source_path.is_dir():
            shutil.copytree(source_path, dest_path)
            # Update SKILL.md name field for skills
            if dep.type == "skill":
                update_skill_md_name(dest_path, flattened_name)
        else:
            shutil.copy2(source_path, dest_path)

        if is_update:
            return (None, name, None)
        return (name, None, None)

    except Exception as e:
        return (None, None, (name, str(e)))


def _sync_local_dependencies(
    config: AgrConfig,
    base_path: Path,
    prune: bool,
) -> tuple[int, int, int, int]:
    """Sync local dependencies from agr.toml to .claude directory.

    Only syncs dependencies explicitly listed in the config.

    Returns:
        Tuple of (installed, updated, pruned, failed) counts
    """
    repo_root = find_repo_root() or Path.cwd()

    username = get_username_from_git_remote(repo_root)
    if not username:
        console.print("[yellow]Warning: Could not determine username from git remote.[/yellow]")
        console.print("[yellow]Using 'local' as namespace. Configure git remote for proper namespacing.[/yellow]")
        username = "local"

    local_deps = config.get_local_dependencies()
    if not local_deps:
        return (0, 0, 0, 0)

    installed_count, updated_count, failed_count = 0, 0, 0
    synced_names: set[str] = set()

    for dep in local_deps:
        installed, updated, error = _sync_local_dependency(
            dep, username, base_path, repo_root
        )
        if installed:
            console.print(f"[green]Installed local resource '{installed}'[/green]")
            synced_names.add(installed)
            installed_count += 1
        if updated:
            console.print(f"[blue]Updated local resource '{updated}'[/blue]")
            synced_names.add(updated)
            updated_count += 1
        if error:
            name, msg = error
            console.print(f"[red]Failed to sync '{name}': {msg}[/red]")
            failed_count += 1

    # Pruning for local resources (if requested)
    pruned_count = 0
    if prune:
        pruned_count = _prune_unlisted_local_resources(
            config, base_path, username, synced_names
        )

    return (installed_count, updated_count, pruned_count, failed_count)


def _prune_unlisted_local_resources(
    config: AgrConfig,
    base_path: Path,
    username: str,
    synced_names: set[str],
) -> int:
    """Remove local resources that are not in the config.

    For skills, checks for flattened names like "kasperjunge:commit"
    that start with the username prefix.
    """
    # Build set of expected local resources
    expected_paths = {dep.path for dep in config.get_local_dependencies()}

    pruned_count = 0

    # Check skills - now stored with flattened names at top level
    skills_dir = base_path / "skills"
    if skills_dir.is_dir():
        prefix = f"{username}:"
        for item in skills_dir.iterdir():
            if item.is_dir() and item.name.startswith(prefix):
                # This is a local skill (starts with our username)
                if item.name in synced_names:
                    continue
                # This resource is not in our expected set - it may be from old auto-discovery
                # Only prune if it looks like a local resource (not a remote one)
                # We can't easily tell, so we'll skip pruning here for safety
                # The user should manually remove unwanted resources

    # Check commands, agents, packages - still use nested structure
    for subdir in ["commands", "agents", "packages"]:
        user_dir = base_path / subdir / username
        if not user_dir.is_dir():
            continue

        for item in user_dir.iterdir():
            # Skip if this was just synced
            name = item.stem if item.is_file() else item.name
            if name in synced_names:
                continue

            # This resource is not in our expected set - it may be from old auto-discovery
            # Only prune if it looks like a local resource (not a remote one)
            # We can't easily tell, so we'll skip pruning here for safety
            # The user should manually remove unwanted resources

    return pruned_count


@app.command()
def sync(
    global_install: bool = typer.Option(
        False, "--global", "-g",
        help="Sync to global ~/.claude/ directory",
    ),
    prune: bool = typer.Option(
        False, "--prune",
        help="Remove resources not listed in agr.toml",
    ),
    local_only: bool = typer.Option(
        False, "--local",
        help="Only sync local dependencies from agr.toml",
    ),
    remote_only: bool = typer.Option(
        False, "--remote",
        help="Only sync remote dependencies from agr.toml",
    ),
) -> None:
    """Synchronize installed resources with agr.toml dependencies.

    Only syncs resources explicitly listed in the agr.toml dependencies array.
    Local paths and remote handles are both tracked in the same dependencies list.

    Use --local to only sync local path dependencies.
    Use --remote to only sync remote GitHub dependencies.
    """
    base_path = get_base_path(global_install)
    total_installed, total_updated, total_pruned, total_failed = 0, 0, 0, 0

    config_path = find_config()
    if not config_path:
        console.print("[dim]No agr.toml found. Nothing to sync.[/dim]")
        console.print("[dim]Use 'agr add' to add dependencies first.[/dim]")
        return

    config = AgrConfig.load(config_path)

    # Save config if it was migrated from old format
    if config._migrated:
        config.save(config_path)
        console.print("[blue]Migrated agr.toml to new format[/blue]")

    # Sync local dependencies
    if not remote_only:
        installed, updated, pruned, failed = _sync_local_dependencies(config, base_path, prune)
        total_installed += installed
        total_updated += updated
        total_pruned += pruned
        total_failed += failed

    # Sync remote dependencies
    if not local_only:
        installed, _skipped, failed, pruned = _sync_remote_dependencies(config, base_path, prune)
        total_installed += installed
        total_pruned += pruned
        total_failed += failed

    # Print summary
    _print_sync_summary(total_installed, total_updated, total_pruned, total_failed)

    if total_failed > 0:
        raise typer.Exit(1)


def _print_sync_summary(installed: int, updated: int, pruned: int, failed: int) -> None:
    """Print a summary of sync results."""
    if not (installed or updated or pruned or failed):
        console.print("[dim]Nothing to sync.[/dim]")
        return

    parts = []
    if installed:
        parts.append(f"{installed} installed")
    if updated:
        parts.append(f"{updated} updated")
    if pruned:
        parts.append(f"{pruned} pruned")
    if failed:
        parts.append(f"[red]{failed} failed[/red]")
    console.print(f"[dim]Sync complete: {', '.join(parts)}[/dim]")


def _sync_remote_dependencies(
    config: AgrConfig,
    base_path: Path,
    prune: bool,
) -> tuple[int, int, int, int]:
    """Sync remote dependencies from agr.toml.

    Returns:
        Tuple of (installed, skipped, failed, pruned) counts
    """
    installed_count, skipped_count, failed_count, pruned_count = 0, 0, 0, 0

    for dep in config.get_remote_dependencies():
        if not dep.handle:
            continue

        try:
            username, repo_name, name = _parse_dependency_ref(dep.handle)
        except ValueError as e:
            console.print(f"[yellow]Skipping invalid dependency '{dep.handle}': {e}[/yellow]")
            continue

        resource_type = _type_string_to_enum(dep.type) if dep.type else ResourceType.SKILL

        if _is_resource_installed(username, name, resource_type, base_path):
            skipped_count += 1
            continue

        try:
            res_config = RESOURCE_CONFIGS[resource_type]
            dest = base_path / res_config.dest_subdir

            with fetch_spinner():
                fetch_resource(
                    username, repo_name, name, [name], dest, resource_type,
                    overwrite=False, username=username,
                )
            console.print(f"[green]Installed {resource_type.value} '{name}'[/green]")
            installed_count += 1
        except (RepoNotFoundError, ResourceNotFoundError, AgrError) as e:
            console.print(f"[red]Failed to install '{dep.handle}': {e}[/red]")
            failed_count += 1

    if prune:
        pruned_count = _prune_unlisted_remote_resources(config, base_path)

    return (installed_count, skipped_count, failed_count, pruned_count)


def _prune_unlisted_remote_resources(config: AgrConfig, base_path: Path) -> int:
    """Remove installed resources that are not in the config."""
    expected_refs = set()
    for dep in config.get_remote_dependencies():
        if not dep.handle:
            continue
        try:
            username, _, name = _parse_dependency_ref(dep.handle)
            expected_refs.add(f"{username}/{name}")
        except ValueError:
            continue

    installed_refs = _discover_installed_namespaced_resources(base_path)
    pruned_count = 0

    for ref in installed_refs:
        if ref not in expected_refs:
            parts = ref.split("/")
            if len(parts) == 2:
                username, name = parts
                _remove_namespaced_resource(username, name, base_path)
                console.print(f"[yellow]Pruned '{ref}'[/yellow]")
                pruned_count += 1

    return pruned_count
