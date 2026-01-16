"""Status reporting for agr resources."""

from dataclasses import dataclass, field
from pathlib import Path

from agr.config import AgrConfig
from agr.resolver import resolve_ref
from agr.sync import compute_file_hash


@dataclass
class ResourceStatus:
    """Status of a single resource."""

    path: str
    source_ref: str | None = None  # The ref it was installed from
    state: str = "unknown"  # synced, modified, missing, untracked


@dataclass
class StatusReport:
    """Overall status report."""

    synced: list[ResourceStatus] = field(default_factory=list)
    modified: list[ResourceStatus] = field(default_factory=list)
    missing: list[ResourceStatus] = field(default_factory=list)
    untracked: list[ResourceStatus] = field(default_factory=list)

    @property
    def total_tracked(self) -> int:
        return len(self.synced) + len(self.modified) + len(self.missing)

    @property
    def total_issues(self) -> int:
        return len(self.modified) + len(self.missing)

    @property
    def is_clean(self) -> bool:
        return self.total_issues == 0 and len(self.untracked) == 0


def get_status(
    config: AgrConfig,
    dest_base: Path,
    author: str | None = None,
) -> StatusReport:
    """Get status of all resources relative to config.

    Args:
        config: AgrConfig to check against
        dest_base: Base .claude directory
        author: Author username for authored packages

    Returns:
        StatusReport with categorized resources
    """
    report = StatusReport()

    # Track expected resources from dependencies
    expected_resources: dict[str, str] = {}  # path -> source ref

    # Build expected resources from dependencies
    for ref, dep in config.dependencies.items():
        try:
            resolved = resolve_ref(ref, dep.package)

            # Add expected paths for this dependency
            if dep.package:
                # For packages, we expect resources under the package directory
                for subdir in ["skills", "commands", "agents"]:
                    package_dir = dest_base / subdir / resolved.username / resolved.resource_name
                    if package_dir.exists():
                        for item in package_dir.iterdir():
                            rel_path = f"{subdir}/{resolved.username}/{resolved.resource_name}/{item.name}"
                            expected_resources[rel_path] = ref
            else:
                # For single resources, check all subdirs
                for subdir in ["skills", "commands", "agents"]:
                    # Skills are directories
                    if subdir == "skills":
                        resource_path = dest_base / subdir / resolved.username / resolved.resource_name
                        if resource_path.is_dir():
                            rel_path = f"{subdir}/{resolved.username}/{resolved.resource_name}"
                            expected_resources[rel_path] = ref
                    else:
                        # Commands/agents are files
                        resource_path = dest_base / subdir / resolved.username / f"{resolved.resource_name}.md"
                        if resource_path.is_file():
                            rel_path = f"{subdir}/{resolved.username}/{resolved.resource_name}"
                            expected_resources[rel_path] = ref
        except (ValueError, Exception):
            continue

    # Build expected resources from authored packages
    if author:
        for name, package in config.packages.items():
            for subdir in ["skills", "commands", "agents"]:
                package_dir = dest_base / subdir / author / name
                if package_dir.exists():
                    for item in package_dir.iterdir():
                        rel_path = f"{subdir}/{author}/{name}/{item.name}"
                        expected_resources[rel_path] = f"[package.{name}]"

    # Scan actual resources
    actual_resources: set[str] = set()

    for subdir in ["skills", "commands", "agents"]:
        subdir_path = dest_base / subdir
        if not subdir_path.is_dir():
            continue

        for author_dir in subdir_path.iterdir():
            if not author_dir.is_dir():
                continue

            for resource in author_dir.iterdir():
                # For skills (directories) and packages, recurse one level
                if resource.is_dir():
                    # Check if this is a skill (has SKILL.md) or a package directory
                    if (resource / "SKILL.md").exists():
                        rel_path = f"{subdir}/{author_dir.name}/{resource.name}"
                        actual_resources.add(rel_path)
                    else:
                        # Package directory - check items inside
                        for item in resource.iterdir():
                            rel_path = f"{subdir}/{author_dir.name}/{resource.name}/{item.name}"
                            actual_resources.add(rel_path)
                elif resource.suffix == ".md":
                    rel_path = f"{subdir}/{author_dir.name}/{resource.stem}"
                    actual_resources.add(rel_path)

    # Categorize resources
    for rel_path, source_ref in expected_resources.items():
        full_path = dest_base / rel_path

        # Adjust path for files that need extension
        if not full_path.exists():
            # Try with .md extension for commands/agents
            if full_path.suffix != ".md" and not full_path.is_dir():
                md_path = full_path.parent / f"{full_path.name}.md"
                if md_path.exists():
                    full_path = md_path

        if not full_path.exists() and not (dest_base / rel_path).exists():
            # Check if it's a directory path
            dir_path = dest_base / rel_path
            if not dir_path.exists():
                report.missing.append(ResourceStatus(
                    path=rel_path,
                    source_ref=source_ref,
                    state="missing",
                ))
        else:
            # Resource exists - mark as synced
            # (We could add hash comparison here for "modified" detection)
            report.synced.append(ResourceStatus(
                path=rel_path,
                source_ref=source_ref,
                state="synced",
            ))

    # Find untracked resources
    for rel_path in actual_resources:
        is_expected = any(
            rel_path == exp_path or rel_path.startswith(exp_path + "/")
            for exp_path in expected_resources
        )

        if not is_expected:
            report.untracked.append(ResourceStatus(
                path=rel_path,
                source_ref=None,
                state="untracked",
            ))

    return report


def format_status_report(report: StatusReport) -> str:
    """Format a status report for display.

    Args:
        report: StatusReport to format

    Returns:
        Formatted string for display
    """
    lines: list[str] = []

    if report.synced:
        lines.append(f"Synced ({len(report.synced)}):")
        for status in report.synced:
            ref_part = f" <- {status.source_ref}" if status.source_ref else ""
            lines.append(f"  ✓ {status.path}{ref_part}")

    if report.modified:
        lines.append(f"\nModified ({len(report.modified)}):")
        for status in report.modified:
            lines.append(f"  ~ {status.path}")

    if report.missing:
        lines.append(f"\nMissing ({len(report.missing)}):")
        for status in report.missing:
            ref_part = f" (from {status.source_ref})" if status.source_ref else ""
            lines.append(f"  ! {status.path}{ref_part}")

    if report.untracked:
        lines.append(f"\nUntracked ({len(report.untracked)}):")
        for status in report.untracked:
            lines.append(f"  ? {status.path}")

    if report.is_clean:
        lines.append("Everything is synced and clean.")

    return "\n".join(lines)
