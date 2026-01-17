"""Local resource sync functionality.

Syncs resources from convention paths (skills/, commands/, agents/, packages/)
to the .claude/ environment directory.
"""

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from agr.discovery import (
    DiscoveryContext,
    LocalResource,
)
from agr.fetcher import ResourceType


@dataclass
class SyncResult:
    """Result of a local sync operation.

    Attributes:
        installed: List of resource names that were newly installed
        updated: List of resource names that were updated
        removed: List of resource names that were removed (prune)
        errors: List of (name, error_message) tuples for failures
    """

    installed: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)

    @property
    def total_synced(self) -> int:
        """Total number of resources synced (installed + updated)."""
        return len(self.installed) + len(self.updated)

    @property
    def has_errors(self) -> bool:
        """Whether any errors occurred during sync."""
        return len(self.errors) > 0


def _get_dest_path(
    resource: LocalResource,
    username: str,
    base_path: Path,
) -> Path:
    """Get destination path for a resource.

    For a skill named "my-skill":
    - Without package: .claude/skills/username/my-skill/
    - With package "toolkit": .claude/skills/username/toolkit/my-skill/

    For a command named "quick-fix":
    - Without package: .claude/commands/username/quick-fix.md
    - With package "toolkit": .claude/commands/username/toolkit/quick-fix.md

    Args:
        resource: The local resource
        username: The user's namespace
        base_path: Base path (.claude directory)

    Returns:
        Path to the destination
    """
    type_subdir = {
        ResourceType.SKILL: "skills",
        ResourceType.COMMAND: "commands",
        ResourceType.AGENT: "agents",
    }[resource.resource_type]

    if resource.package_name:
        # Packaged resource: .claude/type/username/package/name
        if resource.resource_type == ResourceType.SKILL:
            return base_path / type_subdir / username / resource.package_name / resource.name
        else:
            # Commands and agents are files
            return base_path / type_subdir / username / resource.package_name / f"{resource.name}.md"
    else:
        # Top-level resource: .claude/type/username/name
        if resource.resource_type == ResourceType.SKILL:
            return base_path / type_subdir / username / resource.name
        else:
            return base_path / type_subdir / username / f"{resource.name}.md"


def _should_update(source_path: Path, dest_path: Path) -> bool:
    """Determine if a resource should be updated.

    Returns True if:
    - Destination doesn't exist
    - Source is newer than destination

    Args:
        source_path: Path to source file/directory
        dest_path: Path to destination file/directory

    Returns:
        True if the resource should be copied/updated
    """
    if not dest_path.exists():
        return True

    # For directories, check SKILL.md mtime
    if source_path.is_dir():
        source_marker = source_path / "SKILL.md"
        dest_marker = dest_path / "SKILL.md"
        if source_marker.exists() and dest_marker.exists():
            return source_marker.stat().st_mtime > dest_marker.stat().st_mtime
        return True

    # For files, compare mtime directly
    return source_path.stat().st_mtime > dest_path.stat().st_mtime


def _sync_resource(
    resource: LocalResource,
    username: str,
    base_path: Path,
    root_path: Path,
) -> tuple[str | None, str | None, str | None]:
    """Sync a single resource from source to destination.

    Args:
        resource: The resource to sync
        username: The user's namespace
        base_path: Base path (.claude directory)
        root_path: Repository root path

    Returns:
        Tuple of (installed_name, updated_name, error_tuple)
        Only one will be set based on the action taken.
    """
    source_path = root_path / resource.source_path
    dest_path = _get_dest_path(resource, username, base_path)

    try:
        if not _should_update(source_path, dest_path):
            return (None, None, None)  # No update needed

        # Determine if this is new or update
        is_update = dest_path.exists()

        # Remove existing if updating
        if is_update:
            if dest_path.is_dir():
                shutil.rmtree(dest_path)
            else:
                dest_path.unlink()

        # Ensure parent directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy resource
        if resource.resource_type == ResourceType.SKILL:
            shutil.copytree(source_path, dest_path)
        else:
            shutil.copy2(source_path, dest_path)

        if is_update:
            return (None, resource.name, None)
        else:
            return (resource.name, None, None)

    except Exception as e:
        return (None, None, (resource.name, str(e)))


def _collect_local_installed(
    base_path: Path,
    username: str,
) -> dict[str, Path]:
    """Collect all locally installed resources for the user.

    Args:
        base_path: Base .claude directory
        username: The user's namespace

    Returns:
        Dict mapping resource names to their paths
    """
    installed = {}

    # Check skills
    skills_dir = base_path / "skills" / username
    if skills_dir.is_dir():
        for item in skills_dir.iterdir():
            if item.is_dir():
                # Could be a skill or a package directory
                if (item / "SKILL.md").exists():
                    # Direct skill
                    installed[item.name] = item
                else:
                    # Package directory - check for skills inside
                    for sub in item.iterdir():
                        if sub.is_dir() and (sub / "SKILL.md").exists():
                            installed[f"{item.name}/{sub.name}"] = sub

    # Check commands
    commands_dir = base_path / "commands" / username
    if commands_dir.is_dir():
        for item in commands_dir.iterdir():
            if item.is_file() and item.suffix == ".md":
                installed[item.stem] = item
            elif item.is_dir():
                # Package directory
                for sub in item.glob("*.md"):
                    installed[f"{item.name}/{sub.stem}"] = sub

    # Check agents
    agents_dir = base_path / "agents" / username
    if agents_dir.is_dir():
        for item in agents_dir.iterdir():
            if item.is_file() and item.suffix == ".md":
                installed[item.stem] = item
            elif item.is_dir():
                # Package directory
                for sub in item.glob("*.md"):
                    installed[f"{item.name}/{sub.stem}"] = sub

    return installed


def _get_resource_key(resource: LocalResource) -> str:
    """Get a unique key for a resource.

    Args:
        resource: The resource

    Returns:
        A string key like "my-skill" or "my-toolkit/toolkit-skill"
    """
    if resource.package_name:
        return f"{resource.package_name}/{resource.name}"
    return resource.name


def sync_local_resources(
    context: DiscoveryContext,
    username: str,
    base_path: Path,
    root_path: Path,
    prune: bool = False,
) -> SyncResult:
    """Sync discovered local resources to .claude/ directory.

    Copies resources from convention paths (skills/, commands/, etc.)
    to the .claude/{type}/{username}/{name}/ structure.

    Args:
        context: Discovery context with found resources
        username: Username for namespacing (from git remote)
        base_path: Path to .claude directory
        root_path: Path to repository root
        prune: If True, remove resources not in context

    Returns:
        SyncResult with details of changes made
    """
    result = SyncResult()

    # Get all resources to sync
    all_resources = context.all_resources

    # Track which resources we're syncing (for prune)
    synced_keys = set()

    # Sync each resource
    for resource in all_resources:
        key = _get_resource_key(resource)
        synced_keys.add(key)

        installed, updated, error = _sync_resource(
            resource, username, base_path, root_path
        )
        if installed:
            result.installed.append(installed)
        if updated:
            result.updated.append(updated)
        if error:
            result.errors.append(error)

    # Prune if requested
    if prune:
        installed_resources = _collect_local_installed(base_path, username)
        for key, path in installed_resources.items():
            # Extract simple name for comparison
            simple_key = key.split("/")[-1] if "/" in key else key
            full_key = key

            if full_key not in synced_keys and simple_key not in synced_keys:
                try:
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    result.removed.append(simple_key)
                except Exception as e:
                    result.errors.append((simple_key, f"Failed to remove: {e}"))

    return result
