"""Local resource sync functionality.

DEPRECATED: This module is kept for backward compatibility but is no longer
used by 'agr sync'. The new sync behavior only syncs resources explicitly
listed in the agr.toml dependencies array. Resources should be added via
'agr add ./path' which both adds to agr.toml and installs to .claude/.

Syncs resources from convention paths (skills/, commands/, agents/, packages/)
to the .claude/ environment directory.
"""

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from agr.discovery import DiscoveryContext, LocalResource
from agr.fetcher import ResourceType


# Mapping from resource type to subdirectory name
TYPE_TO_SUBDIR = {
    ResourceType.SKILL: "skills",
    ResourceType.COMMAND: "commands",
    ResourceType.AGENT: "agents",
}


@dataclass
class SyncResult:
    """Result of a local sync operation."""

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
        return bool(self.errors)


def _get_dest_path(
    resource: LocalResource,
    username: str,
    base_path: Path,
) -> Path:
    """Get destination path for a resource.

    Skills are directories, commands/agents are .md files.
    Package resources include the package name in the path.
    """
    subdir = TYPE_TO_SUBDIR[resource.resource_type]
    is_skill = resource.resource_type == ResourceType.SKILL

    # Build base path: .claude/{type}/{username}
    dest = base_path / subdir / username

    # Add package directory if present
    if resource.package_name:
        dest = dest / resource.package_name

    # Add resource name (directory for skills, .md file for others)
    if is_skill:
        return dest / resource.name
    return dest / f"{resource.name}.md"


def _should_update(source_path: Path, dest_path: Path) -> bool:
    """Determine if a resource should be updated.

    Returns True if destination doesn't exist or source is newer.
    """
    if not dest_path.exists():
        return True

    # For skill directories, compare SKILL.md timestamps
    if source_path.is_dir():
        source_marker = source_path / "SKILL.md"
        dest_marker = dest_path / "SKILL.md"
        if source_marker.exists() and dest_marker.exists():
            return source_marker.stat().st_mtime > dest_marker.stat().st_mtime
        return True

    # For files, compare timestamps directly
    return source_path.stat().st_mtime > dest_path.stat().st_mtime


def _remove_path(path: Path) -> None:
    """Remove a file or directory."""
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def _sync_resource(
    resource: LocalResource,
    username: str,
    base_path: Path,
    root_path: Path,
) -> tuple[str | None, str | None, tuple[str, str] | None]:
    """Sync a single resource from source to destination.

    Returns:
        Tuple of (installed_name, updated_name, error_tuple).
        Only one will be non-None based on the action taken.
    """
    source_path = root_path / resource.source_path
    dest_path = _get_dest_path(resource, username, base_path)

    try:
        if not _should_update(source_path, dest_path):
            return (None, None, None)

        is_update = dest_path.exists()

        if is_update:
            _remove_path(dest_path)

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        if resource.resource_type == ResourceType.SKILL:
            shutil.copytree(source_path, dest_path)
        else:
            shutil.copy2(source_path, dest_path)

        if is_update:
            return (None, resource.name, None)
        return (resource.name, None, None)

    except Exception as e:
        return (None, None, (resource.name, str(e)))


def _collect_skills_installed(user_dir: Path) -> dict[str, Path]:
    """Collect installed skills from a user's directory."""
    installed = {}
    if not user_dir.is_dir():
        return installed

    for item in user_dir.iterdir():
        if not item.is_dir():
            continue
        if (item / "SKILL.md").exists():
            # Direct skill
            installed[item.name] = item
        else:
            # Package directory - check for skills inside
            for sub in item.iterdir():
                if sub.is_dir() and (sub / "SKILL.md").exists():
                    installed[f"{item.name}/{sub.name}"] = sub
    return installed


def _collect_md_files_installed(user_dir: Path) -> dict[str, Path]:
    """Collect installed .md file resources from a user's directory."""
    installed = {}
    if not user_dir.is_dir():
        return installed

    for item in user_dir.iterdir():
        if item.is_file() and item.suffix == ".md":
            installed[item.stem] = item
        elif item.is_dir():
            # Package directory
            for sub in item.glob("*.md"):
                installed[f"{item.name}/{sub.stem}"] = sub
    return installed


def _collect_local_installed(base_path: Path, username: str) -> dict[str, Path]:
    """Collect all locally installed resources for the user."""
    installed = {}
    installed.update(_collect_skills_installed(base_path / "skills" / username))
    installed.update(_collect_md_files_installed(base_path / "commands" / username))
    installed.update(_collect_md_files_installed(base_path / "agents" / username))
    return installed


def _get_resource_key(resource: LocalResource) -> str:
    """Get a unique key for a resource (e.g., 'my-skill' or 'pkg/skill')."""
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
    """
    result = SyncResult()
    synced_keys = set()

    for resource in context.all_resources:
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

    if prune:
        _prune_unlisted_resources(base_path, username, synced_keys, result)

    return result


def _prune_unlisted_resources(
    base_path: Path,
    username: str,
    synced_keys: set[str],
    result: SyncResult,
) -> None:
    """Remove installed resources that are not in the synced set."""
    installed_resources = _collect_local_installed(base_path, username)

    for key, path in installed_resources.items():
        simple_key = key.split("/")[-1] if "/" in key else key

        if key not in synced_keys and simple_key not in synced_keys:
            try:
                _remove_path(path)
                result.removed.append(simple_key)
            except Exception as e:
                result.errors.append((simple_key, f"Failed to remove: {e}"))
