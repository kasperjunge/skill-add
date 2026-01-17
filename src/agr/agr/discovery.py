"""Local resource discovery for authoring paths.

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

    Attributes:
        skills: List of discovered skill resources
        commands: List of discovered command resources
        agents: List of discovered agent resources
        packages: List of discovered packages with their resources
    """

    skills: list[LocalResource] = field(default_factory=list)
    commands: list[LocalResource] = field(default_factory=list)
    agents: list[LocalResource] = field(default_factory=list)
    packages: list[LocalPackage] = field(default_factory=list)

    @property
    def all_resources(self) -> list[LocalResource]:
        """Return all resources including those in packages."""
        all_res = list(self.skills) + list(self.commands) + list(self.agents)
        for pkg in self.packages:
            all_res.extend(pkg.resources)
        return all_res

    @property
    def is_empty(self) -> bool:
        """Return True if no resources were discovered."""
        return (
            len(self.skills) == 0
            and len(self.commands) == 0
            and len(self.agents) == 0
            and len(self.packages) == 0
        )


def _discover_skills(root_path: Path) -> list[LocalResource]:
    """Discover skills in skills/ directory.

    Looks for directories containing SKILL.md files.

    Args:
        root_path: Path to repository root

    Returns:
        List of discovered skill resources
    """
    skills = []
    skills_dir = root_path / "skills"

    if not skills_dir.is_dir():
        return skills

    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            skills.append(
                LocalResource(
                    name=skill_dir.name,
                    resource_type=ResourceType.SKILL,
                    source_path=skill_dir.relative_to(root_path),
                )
            )

    return skills


def _discover_commands(root_path: Path) -> list[LocalResource]:
    """Discover commands in commands/ directory.

    Looks for .md files directly in the commands directory.

    Args:
        root_path: Path to repository root

    Returns:
        List of discovered command resources
    """
    commands = []
    commands_dir = root_path / "commands"

    if not commands_dir.is_dir():
        return commands

    for cmd_file in commands_dir.glob("*.md"):
        if cmd_file.is_file():
            commands.append(
                LocalResource(
                    name=cmd_file.stem,
                    resource_type=ResourceType.COMMAND,
                    source_path=cmd_file.relative_to(root_path),
                )
            )

    return commands


def _discover_agents(root_path: Path) -> list[LocalResource]:
    """Discover agents in agents/ directory.

    Looks for .md files directly in the agents directory.

    Args:
        root_path: Path to repository root

    Returns:
        List of discovered agent resources
    """
    agents = []
    agents_dir = root_path / "agents"

    if not agents_dir.is_dir():
        return agents

    for agent_file in agents_dir.glob("*.md"):
        if agent_file.is_file():
            agents.append(
                LocalResource(
                    name=agent_file.stem,
                    resource_type=ResourceType.AGENT,
                    source_path=agent_file.relative_to(root_path),
                )
            )

    return agents


def _discover_package_resources(
    root_path: Path, package_path: Path, package_name: str
) -> list[LocalResource]:
    """Discover resources within a package.

    Args:
        root_path: Path to repository root
        package_path: Path to the package directory
        package_name: Name of the package

    Returns:
        List of resources within the package
    """
    resources = []

    # Discover package skills
    pkg_skills_dir = package_path / "skills"
    if pkg_skills_dir.is_dir():
        for skill_dir in pkg_skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                resources.append(
                    LocalResource(
                        name=skill_dir.name,
                        resource_type=ResourceType.SKILL,
                        source_path=skill_dir.relative_to(root_path),
                        package_name=package_name,
                    )
                )

    # Discover package commands
    pkg_commands_dir = package_path / "commands"
    if pkg_commands_dir.is_dir():
        for cmd_file in pkg_commands_dir.glob("*.md"):
            if cmd_file.is_file():
                resources.append(
                    LocalResource(
                        name=cmd_file.stem,
                        resource_type=ResourceType.COMMAND,
                        source_path=cmd_file.relative_to(root_path),
                        package_name=package_name,
                    )
                )

    # Discover package agents
    pkg_agents_dir = package_path / "agents"
    if pkg_agents_dir.is_dir():
        for agent_file in pkg_agents_dir.glob("*.md"):
            if agent_file.is_file():
                resources.append(
                    LocalResource(
                        name=agent_file.stem,
                        resource_type=ResourceType.AGENT,
                        source_path=agent_file.relative_to(root_path),
                        package_name=package_name,
                    )
                )

    return resources


def _discover_packages(root_path: Path) -> list[LocalPackage]:
    """Discover packages in packages/ directory.

    Looks for directories containing skills/, commands/, or agents/ subdirectories.

    Args:
        root_path: Path to repository root

    Returns:
        List of discovered packages
    """
    packages = []
    packages_dir = root_path / "packages"

    if not packages_dir.is_dir():
        return packages

    for pkg_dir in packages_dir.iterdir():
        if not pkg_dir.is_dir():
            continue

        # Discover resources within this package
        resources = _discover_package_resources(root_path, pkg_dir, pkg_dir.name)

        # Only add package if it has resources
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

    Scans the following paths for resources:
    - skills/*/SKILL.md (skill directories)
    - commands/*.md (command files)
    - agents/*.md (agent files)
    - packages/*/skills/*/SKILL.md (packaged skills)
    - packages/*/commands/*.md (packaged commands)
    - packages/*/agents/*.md (packaged agents)

    Args:
        root_path: Path to repository root

    Returns:
        DiscoveryContext containing all discovered resources
    """
    return DiscoveryContext(
        skills=_discover_skills(root_path),
        commands=_discover_commands(root_path),
        agents=_discover_agents(root_path),
        packages=_discover_packages(root_path),
    )
