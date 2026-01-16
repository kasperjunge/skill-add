"""Configuration management for agr.toml."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tomli
import tomli_w

from agr.exceptions import ConfigNotFoundError, ConfigParseError, ConfigValidationError

CONFIG_FILENAME = "agr.toml"


@dataclass
class Dependency:
    """A dependency on an external resource or package.

    Examples:
        "kasper/commit" = {}
        "alice/data-toolkit" = { package = true }
        "commit" = {}  # From official index
        "bob/ambiguous" = { type = "skill" }  # Disambiguate when multiple types exist
    """

    ref: str
    package: bool = False
    type: str | None = None  # "skill", "command", or "agent"

    @classmethod
    def from_dict(cls, ref: str, data: dict[str, Any]) -> "Dependency":
        """Create a Dependency from a TOML dict entry."""
        return cls(
            ref=ref,
            package=data.get("package", False),
            type=data.get("type"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a TOML-serializable dict."""
        result: dict[str, Any] = {}
        if self.package:
            result["package"] = True
        if self.type:
            result["type"] = self.type
        return result


@dataclass
class LocalResource:
    """A locally-authored resource.

    Example:
        [resource.my-helper]
        type = "skill"
        path = "./skills/my-helper/"
    """

    name: str
    type: str  # "skill", "command", or "agent"
    path: str

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "LocalResource":
        """Create a LocalResource from a TOML dict entry."""
        if "type" not in data:
            raise ConfigValidationError(f"Resource '{name}' missing required 'type' field")
        if "path" not in data:
            raise ConfigValidationError(f"Resource '{name}' missing required 'path' field")

        resource_type = data["type"]
        if resource_type not in ("skill", "command", "agent"):
            raise ConfigValidationError(
                f"Resource '{name}' has invalid type '{resource_type}'. "
                "Must be 'skill', 'command', or 'agent'"
            )

        return cls(
            name=name,
            type=resource_type,
            path=data["path"],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a TOML-serializable dict."""
        return {
            "type": self.type,
            "path": self.path,
        }


@dataclass
class Package:
    """A locally-authored package containing multiple resources.

    Example:
        [package.my-toolkit]
        description = "My toolkit"
        skills = ["./my-toolkit/skills/*/"]
        commands = ["./my-toolkit/commands/*.md"]
        agents = ["./my-toolkit/agents/*.md"]
    """

    name: str
    description: str = ""
    skills: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    agents: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "Package":
        """Create a Package from a TOML dict entry."""
        return cls(
            name=name,
            description=data.get("description", ""),
            skills=data.get("skills", []),
            commands=data.get("commands", []),
            agents=data.get("agents", []),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a TOML-serializable dict."""
        result: dict[str, Any] = {}
        if self.description:
            result["description"] = self.description
        if self.skills:
            result["skills"] = self.skills
        if self.commands:
            result["commands"] = self.commands
        if self.agents:
            result["agents"] = self.agents
        return result


@dataclass
class AgrConfig:
    """Configuration from agr.toml."""

    path: Path
    dependencies: dict[str, Dependency] = field(default_factory=dict)
    resources: dict[str, LocalResource] = field(default_factory=dict)
    packages: dict[str, Package] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "AgrConfig":
        """Load configuration from agr.toml.

        Args:
            path: Path to the agr.toml file

        Returns:
            Parsed AgrConfig

        Raises:
            ConfigNotFoundError: If the file doesn't exist
            ConfigParseError: If the file cannot be parsed
            ConfigValidationError: If the configuration is invalid
        """
        if not path.exists():
            raise ConfigNotFoundError(f"Config file not found: {path}")

        try:
            with open(path, "rb") as f:
                data = tomli.load(f)
        except tomli.TOMLDecodeError as e:
            raise ConfigParseError(f"Failed to parse {path}: {e}")

        return cls._from_dict(path, data)

    @classmethod
    def _from_dict(cls, path: Path, data: dict[str, Any]) -> "AgrConfig":
        """Create an AgrConfig from a parsed TOML dict."""
        config = cls(path=path)

        # Parse dependencies
        deps_data = data.get("dependencies", {})
        for ref, dep_config in deps_data.items():
            if not isinstance(dep_config, dict):
                raise ConfigValidationError(
                    f"Dependency '{ref}' must be a table, got {type(dep_config).__name__}"
                )
            config.dependencies[ref] = Dependency.from_dict(ref, dep_config)

        # Parse local resources
        resources_data = data.get("resource", {})
        for name, res_config in resources_data.items():
            if not isinstance(res_config, dict):
                raise ConfigValidationError(
                    f"Resource '{name}' must be a table, got {type(res_config).__name__}"
                )
            config.resources[name] = LocalResource.from_dict(name, res_config)

        # Parse packages
        packages_data = data.get("package", {})
        for name, pkg_config in packages_data.items():
            if not isinstance(pkg_config, dict):
                raise ConfigValidationError(
                    f"Package '{name}' must be a table, got {type(pkg_config).__name__}"
                )
            config.packages[name] = Package.from_dict(name, pkg_config)

        return config

    def save(self) -> None:
        """Save configuration to agr.toml."""
        data = self._to_dict()
        with open(self.path, "wb") as f:
            tomli_w.dump(data, f)

    def _to_dict(self) -> dict[str, Any]:
        """Convert to a TOML-serializable dict."""
        data: dict[str, Any] = {}

        # Serialize dependencies
        if self.dependencies:
            data["dependencies"] = {
                ref: dep.to_dict() for ref, dep in self.dependencies.items()
            }

        # Serialize resources
        if self.resources:
            data["resource"] = {
                name: res.to_dict() for name, res in self.resources.items()
            }

        # Serialize packages
        if self.packages:
            data["package"] = {
                name: pkg.to_dict() for name, pkg in self.packages.items()
            }

        return data

    def add_dependency(
        self, ref: str, package: bool = False, resource_type: str | None = None
    ) -> None:
        """Add a dependency to the config.

        Args:
            ref: Reference string (e.g., "kasper/commit", "commit")
            package: Whether this is a package dependency
            resource_type: Optional type hint ("skill", "command", or "agent")
        """
        self.dependencies[ref] = Dependency(ref=ref, package=package, type=resource_type)

    def remove_dependency(self, ref: str) -> bool:
        """Remove a dependency from the config.

        Args:
            ref: Reference string to remove

        Returns:
            True if the dependency was removed, False if it didn't exist
        """
        if ref in self.dependencies:
            del self.dependencies[ref]
            return True
        return False

    def add_resource(self, name: str, resource_type: str, path: str) -> None:
        """Add a local resource to the config.

        Args:
            name: Resource name
            resource_type: Type of resource ("skill", "command", "agent")
            path: Path to the resource
        """
        self.resources[name] = LocalResource(name=name, type=resource_type, path=path)

    def add_package(self, name: str, description: str = "") -> Package:
        """Add a package to the config.

        Args:
            name: Package name
            description: Optional package description

        Returns:
            The created Package object
        """
        pkg = Package(name=name, description=description)
        self.packages[name] = pkg
        return pkg


def find_config(start_path: Path | None = None) -> Path | None:
    """Find agr.toml by walking up the directory tree.

    Args:
        start_path: Starting directory (defaults to current working directory)

    Returns:
        Path to agr.toml if found, None otherwise
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    while True:
        config_path = current / CONFIG_FILENAME
        if config_path.exists():
            return config_path

        parent = current.parent
        if parent == current:
            # Reached filesystem root
            return None
        current = parent


def load_or_create_config(start_path: Path | None = None) -> AgrConfig:
    """Load existing config or create a new one.

    If agr.toml exists in the directory tree, load it.
    Otherwise, create a new config file in the current directory.

    Args:
        start_path: Starting directory (defaults to current working directory)

    Returns:
        Loaded or newly created AgrConfig
    """
    existing = find_config(start_path)
    if existing:
        return AgrConfig.load(existing)

    # Create new config in current directory
    config_path = (start_path or Path.cwd()) / CONFIG_FILENAME
    config = AgrConfig(path=config_path)
    config.save()
    return config
