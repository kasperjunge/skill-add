"""Type definitions for the fetcher module."""

from dataclasses import dataclass, field
from enum import Enum


class ResourceType(Enum):
    """Type of resource to fetch."""

    SKILL = "skill"
    COMMAND = "command"
    AGENT = "agent"


@dataclass
class ResourceConfig:
    """Configuration for a resource type."""

    resource_type: ResourceType
    source_subdir: str  # e.g., ".claude/skills", ".claude/commands"
    dest_subdir: str  # e.g., "skills", "commands"
    is_directory: bool  # True for skills, False for commands/agents
    file_extension: str | None  # None for skills, ".md" for commands/agents


RESOURCE_CONFIGS: dict[ResourceType, ResourceConfig] = {
    ResourceType.SKILL: ResourceConfig(
        resource_type=ResourceType.SKILL,
        source_subdir=".claude/skills",
        dest_subdir="skills",
        is_directory=True,
        file_extension=None,
    ),
    ResourceType.COMMAND: ResourceConfig(
        resource_type=ResourceType.COMMAND,
        source_subdir=".claude/commands",
        dest_subdir="commands",
        is_directory=False,
        file_extension=".md",
    ),
    ResourceType.AGENT: ResourceConfig(
        resource_type=ResourceType.AGENT,
        source_subdir=".claude/agents",
        dest_subdir="agents",
        is_directory=False,
        file_extension=".md",
    ),
}


@dataclass
class DiscoveredResource:
    """Holds information about a discovered resource."""

    name: str
    resource_type: ResourceType
    path_segments: list[str]
    username: str | None = None  # Username for namespaced resources


@dataclass
class DiscoveryResult:
    """Result of resource discovery operation."""

    resources: list[DiscoveredResource] = field(default_factory=list)
    is_bundle: bool = False

    @property
    def is_unique(self) -> bool:
        """Return True if exactly one resource type was found (including bundle)."""
        total = len(self.resources) + (1 if self.is_bundle else 0)
        return total == 1

    @property
    def is_ambiguous(self) -> bool:
        """Return True if multiple resource types were found."""
        total = len(self.resources) + (1 if self.is_bundle else 0)
        return total > 1

    @property
    def is_empty(self) -> bool:
        """Return True if no resources were found."""
        return len(self.resources) == 0 and not self.is_bundle

    @property
    def found_types(self) -> list[str]:
        """Return list of resource type names found."""
        types = [r.resource_type.value for r in self.resources]
        if self.is_bundle:
            types.append("bundle")
        return types
