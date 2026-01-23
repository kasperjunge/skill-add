"""Resource type definitions and specifications.

This module defines the core abstractions for resources (skills, rules, etc.)
that can be installed by agr.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ResourceType(Enum):
    """Resource types supported by agr."""

    SKILL = "skill"
    # Future: RULE = "rule"
    # Future: COMMAND = "command"
    # Future: SUBAGENT = "subagent"
    # Future: INSTRUCTION = "instruction"


@dataclass(frozen=True)
class ResourceSpec:
    """Specification for a resource type.

    Defines how to discover and validate a particular type of resource.
    """

    type: ResourceType
    marker_file: str  # e.g., "SKILL.md"
    is_directory: bool  # True for skills (directories), False for single files
    search_paths: tuple[str, ...]  # e.g., ("resources/skills", "skills", ".")
    required_frontmatter: tuple[str, ...]  # Required frontmatter fields
    optional_frontmatter: tuple[str, ...]  # Optional frontmatter fields
    name_pattern: str  # Regex pattern for valid names

    def validate_name(self, name: str) -> bool:
        """Validate a resource name against the spec's pattern.

        Args:
            name: Name to validate

        Returns:
            True if the name is valid
        """
        if not name:
            return False
        return bool(re.match(self.name_pattern, name))

    def is_valid_resource(self, path: Path) -> bool:
        """Check if a path is a valid resource of this type.

        Args:
            path: Path to check

        Returns:
            True if the path is a valid resource
        """
        if self.is_directory:
            if not path.is_dir():
                return False
            return (path / self.marker_file).exists()
        else:
            # Single file resource
            return path.is_file() and path.name == self.marker_file


@dataclass
class Resource:
    """A discovered or installed resource.

    Represents an actual instance of a resource type.
    """

    spec: ResourceSpec
    name: str
    path: Path
    metadata: dict = field(default_factory=dict)

    @property
    def type(self) -> ResourceType:
        """Get the resource type."""
        return self.spec.type

    @property
    def marker_path(self) -> Path:
        """Get the path to the marker file."""
        if self.spec.is_directory:
            return self.path / self.spec.marker_file
        return self.path

    def is_valid(self) -> bool:
        """Check if this resource is still valid (exists and has marker)."""
        return self.spec.is_valid_resource(self.path)
