"""Sync engine for installing dependencies and building packages."""

import hashlib
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from agr.config import AgrConfig, Package
from agr.detector import ResourceType, discover_package_resources
from agr.exceptions import AgrError, RepoNotFoundError
from agr.resolver import ResolvedRef, resolve_ref


@dataclass
class SyncResult:
    """Result of a sync operation."""

    installed: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)  # (ref, error message)
    removed: list[str] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        return len(self.installed) + len(self.updated) + len(self.skipped)

    @property
    def has_errors(self) -> bool:
        return len(self.failed) > 0

    def merge(self, other: "SyncResult") -> None:
        """Merge another SyncResult into this one."""
        self.installed.extend(other.installed)
        self.updated.extend(other.updated)
        self.skipped.extend(other.skipped)
        self.failed.extend(other.failed)
        self.removed.extend(other.removed)


def compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of a file or directory.

    For directories, hashes all files recursively.
    """
    hasher = hashlib.sha256()

    if path.is_file():
        hasher.update(path.read_bytes())
    elif path.is_dir():
        for file_path in sorted(path.rglob("*")):
            if file_path.is_file():
                # Include relative path in hash for directory structure
                rel_path = file_path.relative_to(path)
                hasher.update(str(rel_path).encode())
                hasher.update(file_path.read_bytes())

    return hasher.hexdigest()


def _download_and_extract_tarball(tarball_url: str, username: str, repo_name: str, tmp_path: Path) -> Path:
    """Download and extract a GitHub tarball."""
    tarball_path = tmp_path / "repo.tar.gz"

    try:
        with httpx.Client(follow_redirects=True, timeout=30.0) as client:
            response = client.get(tarball_url)
            if response.status_code == 404:
                raise RepoNotFoundError(
                    f"Repository '{username}/{repo_name}' not found on GitHub."
                )
            response.raise_for_status()
            tarball_path.write_bytes(response.content)
    except httpx.HTTPStatusError as e:
        raise AgrError(f"Failed to download repository: {e}")
    except httpx.RequestError as e:
        raise AgrError(f"Network error: {e}")

    import tarfile

    extract_path = tmp_path / "extracted"
    with tarfile.open(tarball_path, "r:gz") as tar:
        tar.extractall(extract_path)

    return extract_path / f"{repo_name}-main"


def _install_skill(source: Path, dest: Path, force: bool = False) -> bool:
    """Install a skill directory.

    Returns True if installed/updated, False if skipped.
    """
    if dest.exists():
        if not force:
            # Check if modified
            source_hash = compute_file_hash(source)
            dest_hash = compute_file_hash(dest)
            if source_hash == dest_hash:
                return False  # Skip, already up to date
        shutil.rmtree(dest)

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, dest)
    return True


def _install_file(source: Path, dest: Path, force: bool = False) -> bool:
    """Install a file (command or agent).

    Returns True if installed/updated, False if skipped.
    """
    if dest.exists():
        if not force:
            source_hash = compute_file_hash(source)
            dest_hash = compute_file_hash(dest)
            if source_hash == dest_hash:
                return False
        dest.unlink()

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return True


def _find_resource_types_in_repo(
    repo_dir: Path,
    path_segments: list[str],
) -> dict[ResourceType, Path]:
    """Find all resource types that match the given name in a repo.

    Args:
        repo_dir: Path to the extracted repository
        path_segments: Path segments to the resource (e.g., ["hello-world"])

    Returns:
        Dict mapping ResourceType to the source path for each found type
    """
    found: dict[ResourceType, Path] = {}

    for resource_type, subdir in [
        (ResourceType.SKILL, "skills"),
        (ResourceType.COMMAND, "commands"),
        (ResourceType.AGENT, "agents"),
    ]:
        source_base = repo_dir / ".claude" / subdir
        source_path = source_base / "/".join(path_segments)

        if resource_type == ResourceType.SKILL:
            # Skills are directories with SKILL.md
            if source_path.is_dir() and (source_path / "SKILL.md").exists():
                found[resource_type] = source_path
        else:
            # Commands and agents are .md files
            md_path = source_path.with_suffix(".md") if not source_path.suffix else source_path
            if md_path.is_file():
                found[resource_type] = md_path

    return found


def sync_dependency(
    resolved: ResolvedRef,
    dest_base: Path,
    force: bool = False,
    specified_type: str | None = None,
) -> SyncResult:
    """Sync a single dependency.

    Args:
        resolved: Resolved reference
        dest_base: Base .claude directory
        force: Force overwrite even if modified
        specified_type: Optional type constraint ("skill", "command", or "agent")

    Returns:
        SyncResult for this dependency
    """
    result = SyncResult()

    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            repo_dir = _download_and_extract_tarball(
                resolved.tarball_url,
                resolved.username,
                resolved.repo,
                Path(tmp_dir),
            )
        except (RepoNotFoundError, AgrError) as e:
            result.failed.append((resolved.ref, str(e)))
            return result

        if resolved.is_package:
            # Install all resources from package
            _sync_package_from_repo(
                repo_dir,
                resolved,
                dest_base,
                force,
                result,
            )
        else:
            # Install single resource
            _sync_single_resource(
                repo_dir,
                resolved,
                dest_base,
                force,
                result,
                specified_type,
            )

    return result


def _sync_single_resource(
    repo_dir: Path,
    resolved: ResolvedRef,
    dest_base: Path,
    force: bool,
    result: SyncResult,
    specified_type: str | None = None,
) -> None:
    """Sync a single resource from a repo.

    Args:
        repo_dir: Path to the extracted repository
        resolved: Resolved reference info
        dest_base: Base .claude directory
        force: Force overwrite even if modified
        result: SyncResult to update
        specified_type: Optional type constraint ("skill", "command", or "agent")
    """
    resource_name = resolved.path_segments[-1] if resolved.path_segments else resolved.resource_name

    # Find all matching resource types
    found_types = _find_resource_types_in_repo(repo_dir, resolved.path_segments)

    if not found_types:
        result.failed.append((resolved.ref, f"Resource '{resolved.resource_name}' not found in repository"))
        return

    # If user specified a type, use only that
    if specified_type:
        target_type = ResourceType(specified_type)
        if target_type not in found_types:
            available_types = ", ".join(t.value for t in found_types.keys())
            result.failed.append((
                resolved.ref,
                f"Resource '{resource_name}' not found as {specified_type}. "
                f"Available types: {available_types}"
            ))
            return

        # Install the specified type
        source_path = found_types[target_type]
        _install_single_type(
            target_type, source_path, dest_base, resolved, resource_name, force, result
        )
        return

    # Check for ambiguity
    if len(found_types) > 1:
        types_list = ", ".join(t.value for t in found_types.keys())
        result.failed.append((
            resolved.ref,
            f"Multiple resources named '{resource_name}' found: {types_list}. "
            f"Please specify the type with: agr add {resolved.ref} --type <skill|command|agent>"
        ))
        return

    # Single type found - install it
    resource_type, source_path = list(found_types.items())[0]
    _install_single_type(
        resource_type, source_path, dest_base, resolved, resource_name, force, result
    )


def _install_single_type(
    resource_type: ResourceType,
    source_path: Path,
    dest_base: Path,
    resolved: ResolvedRef,
    resource_name: str,
    force: bool,
    result: SyncResult,
) -> None:
    """Install a single resource type."""
    subdir = resource_type.value + "s"  # skill -> skills, command -> commands, agent -> agents

    if resource_type == ResourceType.SKILL:
        dest_path = dest_base / subdir / resolved.username / resource_name
        existed = dest_path.exists()
        if _install_skill(source_path, dest_path, force):
            if existed:
                result.updated.append(f"{subdir}/{resolved.username}/{resource_name}")
            else:
                result.installed.append(f"{subdir}/{resolved.username}/{resource_name}")
        else:
            result.skipped.append(f"{subdir}/{resolved.username}/{resource_name}")
    else:
        dest_path = dest_base / subdir / resolved.username / f"{resource_name}.md"
        existed = dest_path.exists()
        if _install_file(source_path, dest_path, force):
            if existed:
                result.updated.append(f"{subdir}/{resolved.username}/{resource_name}")
            else:
                result.installed.append(f"{subdir}/{resolved.username}/{resource_name}")
        else:
            result.skipped.append(f"{subdir}/{resolved.username}/{resource_name}")


def _sync_package_from_repo(
    repo_dir: Path,
    resolved: ResolvedRef,
    dest_base: Path,
    force: bool,
    result: SyncResult,
) -> None:
    """Sync all resources from a package in a repo."""
    package_name = resolved.resource_name

    # Look for resources in package directories
    for resource_type, subdir in [
        (ResourceType.SKILL, "skills"),
        (ResourceType.COMMAND, "commands"),
        (ResourceType.AGENT, "agents"),
    ]:
        source_dir = repo_dir / ".claude" / subdir / package_name

        if not source_dir.is_dir():
            continue

        if resource_type == ResourceType.SKILL:
            # Install skill directories
            for skill_dir in source_dir.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    dest_path = dest_base / subdir / resolved.username / package_name / skill_dir.name
                    ref_name = f"{subdir}/{resolved.username}/{package_name}/{skill_dir.name}"
                    if _install_skill(skill_dir, dest_path, force):
                        result.installed.append(ref_name)
                    else:
                        result.skipped.append(ref_name)
        else:
            # Install .md files
            for md_file in source_dir.glob("*.md"):
                dest_path = dest_base / subdir / resolved.username / package_name / md_file.name
                ref_name = f"{subdir}/{resolved.username}/{package_name}/{md_file.stem}"
                if _install_file(md_file, dest_path, force):
                    result.installed.append(ref_name)
                else:
                    result.skipped.append(ref_name)


def sync_dependencies(
    config: AgrConfig,
    dest_base: Path,
    force: bool = False,
) -> SyncResult:
    """Sync all dependencies from config.

    Args:
        config: AgrConfig with dependencies
        dest_base: Base .claude directory
        force: Force overwrite even if modified

    Returns:
        Combined SyncResult for all dependencies
    """
    result = SyncResult()

    for ref, dep in config.dependencies.items():
        try:
            resolved = resolve_ref(ref, dep.package)
        except (ValueError, Exception) as e:
            result.failed.append((ref, str(e)))
            continue

        dep_result = sync_dependency(resolved, dest_base, force, specified_type=dep.type)
        result.merge(dep_result)

    return result


def sync_authored_package(
    package: Package,
    package_path: Path,
    dest_base: Path,
    author: str,
    force: bool = False,
) -> SyncResult:
    """Sync a locally-authored package to .claude/.

    Args:
        package: Package configuration
        package_path: Base path for resolving package patterns
        dest_base: Base .claude directory
        author: Author username for namespacing
        force: Force overwrite even if modified

    Returns:
        SyncResult for this package
    """
    result = SyncResult()

    # Discover resources using patterns or defaults
    resources = discover_package_resources(
        package_path,
        skill_patterns=package.skills or None,
        command_patterns=package.commands or None,
        agent_patterns=package.agents or None,
    )

    # Install skills
    for skill_path in resources[ResourceType.SKILL]:
        dest_path = dest_base / "skills" / author / package.name / skill_path.name
        ref_name = f"skills/{author}/{package.name}/{skill_path.name}"
        try:
            if _install_skill(skill_path, dest_path, force):
                result.installed.append(ref_name)
            else:
                result.skipped.append(ref_name)
        except Exception as e:
            result.failed.append((ref_name, str(e)))

    # Install commands
    for cmd_path in resources[ResourceType.COMMAND]:
        dest_path = dest_base / "commands" / author / package.name / cmd_path.name
        ref_name = f"commands/{author}/{package.name}/{cmd_path.stem}"
        try:
            if _install_file(cmd_path, dest_path, force):
                result.installed.append(ref_name)
            else:
                result.skipped.append(ref_name)
        except Exception as e:
            result.failed.append((ref_name, str(e)))

    # Install agents
    for agent_path in resources[ResourceType.AGENT]:
        dest_path = dest_base / "agents" / author / package.name / agent_path.name
        ref_name = f"agents/{author}/{package.name}/{agent_path.stem}"
        try:
            if _install_file(agent_path, dest_path, force):
                result.installed.append(ref_name)
            else:
                result.skipped.append(ref_name)
        except Exception as e:
            result.failed.append((ref_name, str(e)))

    return result


def sync_authored_packages(
    config: AgrConfig,
    dest_base: Path,
    author: str,
    force: bool = False,
) -> SyncResult:
    """Sync all locally-authored packages.

    Args:
        config: AgrConfig with packages
        dest_base: Base .claude directory
        author: Author username for namespacing
        force: Force overwrite even if modified

    Returns:
        Combined SyncResult for all packages
    """
    result = SyncResult()
    config_dir = config.path.parent

    for name, package in config.packages.items():
        pkg_result = sync_authored_package(
            package,
            config_dir,
            dest_base,
            author,
            force,
        )
        result.merge(pkg_result)

    return result


def clean_untracked(
    config: AgrConfig,
    dest_base: Path,
    author: str | None = None,
) -> list[str]:
    """Remove resources not tracked in config.

    Args:
        config: AgrConfig to check against
        dest_base: Base .claude directory
        author: Author username (for filtering authored packages)

    Returns:
        List of removed paths
    """
    removed: list[str] = []

    # Build set of expected paths from config
    expected_paths: set[str] = set()

    # Add paths from dependencies
    for ref, dep in config.dependencies.items():
        try:
            resolved = resolve_ref(ref, dep.package)
            # This is a simplification - in practice we'd need to check what was actually installed
            for subdir in ["skills", "commands", "agents"]:
                if dep.package:
                    expected_paths.add(f"{subdir}/{resolved.username}/{resolved.resource_name}")
                else:
                    expected_paths.add(f"{subdir}/{resolved.username}/{resolved.resource_name}")
        except (ValueError, Exception):
            continue

    # Add paths from authored packages
    if author:
        for name, package in config.packages.items():
            for subdir in ["skills", "commands", "agents"]:
                expected_paths.add(f"{subdir}/{author}/{name}")

    # Scan installed resources
    for subdir in ["skills", "commands", "agents"]:
        subdir_path = dest_base / subdir
        if not subdir_path.is_dir():
            continue

        for author_dir in subdir_path.iterdir():
            if not author_dir.is_dir():
                continue

            for resource_dir in author_dir.iterdir():
                rel_path = f"{subdir}/{author_dir.name}/{resource_dir.name}"

                # Check if this path is expected
                is_expected = any(rel_path.startswith(exp) or exp.startswith(rel_path)
                                 for exp in expected_paths)

                if not is_expected:
                    # Remove untracked resource
                    if resource_dir.is_dir():
                        shutil.rmtree(resource_dir)
                    else:
                        resource_dir.unlink()
                    removed.append(rel_path)

    return removed
