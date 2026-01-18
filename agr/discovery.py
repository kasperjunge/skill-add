"""Local resource discovery for authoring paths.

NOTE: As of the unified dependencies refactor, auto-discovery is deprecated.
Resources should be explicitly added via 'agr add ./path' instead of being
auto-discovered. The discover_local_resources function is kept for backward
compatibility but is no longer called by 'agr sync'.

This module provides functionality to discover resources in convention paths:
- skills/*/SKILL.md
- commands/*.md
- agents/*.md
- packages/*/skills/*/SKILL.md
- packages/*/commands/*.md
- packages/*/agents/*.md
"""

from dataclasses import dataclass, field
from pathlib import Path

from agr.fetcher import ResourceType


@dataclass
class LocalResource:
    """A locally discovered resource in a convention path.

    Attributes:
        name: The resource name (e.g., "my-skill")
        resource_type: Type of resource (SKILL, COMMAND, AGENT)
        source_path: Path to the resource relative to repo root
        package_name: Name of containing package (if within a package)
    """

    name: str
    resource_type: ResourceType
    source_path: Path
    package_name: str | None = None


@dataclass
class LocalPackage:
    """A locally discovered package containing multiple resources.

    Attributes:
        name: The package name (e.g., "my-toolkit")
        path: Path to the package directory relative to repo root
        resources: List of resources within the package
    """

    name: str
    path: Path
    resources: list[LocalResource] = field(default_factory=list)


@dataclass
class DiscoveryContext:
    """Result of local resource discovery.

    Contains all discovered resources organized by type.
    """

    skills: list[LocalResource] = field(default_factory=list)
    commands: list[LocalResource] = field(default_factory=list)
    agents: list[LocalResource] = field(default_factory=list)
    packages: list[LocalPackage] = field(default_factory=list)

    @property
    def all_resources(self) -> list[LocalResource]:
        """Return all resources including those in packages."""
        resources = self.skills + self.commands + self.agents
        for pkg in self.packages:
            resources.extend(pkg.resources)
        return resources

    @property
    def is_empty(self) -> bool:
        """Return True if no resources were discovered."""
        return not (self.skills or self.commands or self.agents or self.packages)


def _discover_skills_in_dir(
    root_path: Path,
    skills_dir: Path,
    package_name: str | None = None,
) -> list[LocalResource]:
    """Discover skills in a directory containing skill subdirectories.

    Skills are directories containing a SKILL.md file.
    """
    if not skills_dir.is_dir():
        return []

    resources = []
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            resources.append(
                LocalResource(
                    name=skill_dir.name,
                    resource_type=ResourceType.SKILL,
                    source_path=skill_dir.relative_to(root_path),
                    package_name=package_name,
                )
            )
    return resources


def _discover_md_files_in_dir(
    root_path: Path,
    target_dir: Path,
    resource_type: ResourceType,
    package_name: str | None = None,
) -> list[LocalResource]:
    """Discover markdown file resources in a directory.

    Used for commands and agents which are single .md files.
    """
    if not target_dir.is_dir():
        return []

    return [
        LocalResource(
            name=md_file.stem,
            resource_type=resource_type,
            source_path=md_file.relative_to(root_path),
            package_name=package_name,
        )
        for md_file in target_dir.glob("*.md")
        if md_file.is_file()
    ]


def _discover_package_resources(
    root_path: Path,
    package_path: Path,
    package_name: str,
) -> list[LocalResource]:
    """Discover all resources within a package directory."""
    resources = []
    resources.extend(
        _discover_skills_in_dir(root_path, package_path / "skills", package_name)
    )
    resources.extend(
        _discover_md_files_in_dir(
            root_path, package_path / "commands", ResourceType.COMMAND, package_name
        )
    )
    resources.extend(
        _discover_md_files_in_dir(
            root_path, package_path / "agents", ResourceType.AGENT, package_name
        )
    )
    return resources


def _discover_packages(root_path: Path) -> list[LocalPackage]:
    """Discover packages in packages/ directory."""
    packages_dir = root_path / "packages"
    if not packages_dir.is_dir():
        return []

    packages = []
    for pkg_dir in packages_dir.iterdir():
        if not pkg_dir.is_dir():
            continue

        resources = _discover_package_resources(root_path, pkg_dir, pkg_dir.name)
        if resources:
            packages.append(
                LocalPackage(
                    name=pkg_dir.name,
                    path=pkg_dir.relative_to(root_path),
                    resources=resources,
                )
            )
    return packages


def discover_local_resources(root_path: Path) -> DiscoveryContext:
    """Discover all local resources in convention paths.

    DEPRECATED: This function is kept for backward compatibility but is no longer
    used by 'agr sync'. Resources should be explicitly added via 'agr add ./path'.

    Scans the following paths for resources:
    - skills/*/SKILL.md (skill directories)
    - commands/*.md (command files)
    - agents/*.md (agent files)
    - packages/*/skills/*/SKILL.md (packaged skills)
    - packages/*/commands/*.md (packaged commands)
    - packages/*/agents/*.md (packaged agents)
    """
    return DiscoveryContext(
        skills=_discover_skills_in_dir(root_path, root_path / "skills"),
        commands=_discover_md_files_in_dir(
            root_path, root_path / "commands", ResourceType.COMMAND
        ),
        agents=_discover_md_files_in_dir(
            root_path, root_path / "agents", ResourceType.AGENT
        ),
        packages=_discover_packages(root_path),
    )
