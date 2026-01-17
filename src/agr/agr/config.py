"""Configuration management for agr.toml."""

from dataclasses import dataclass, field
from pathlib import Path

import tomlkit
from tomlkit import TOMLDocument
from tomlkit.exceptions import TOMLKitError

from agr.exceptions import ConfigParseError


# Valid resource types
VALID_TYPES = {"skill", "command", "agent", "package"}


@dataclass
class Dependency:
    """Unified dependency specification for agr.toml.

    A dependency can be either remote (GitHub handle) or local (file path).

    Examples:
        Remote: { handle = "kasperjunge/commit", type = "skill" }
        Local:  { path = "./commands/docs.md", type = "command" }
    """

    type: str  # "skill", "command", "agent", "package" - always explicit
    handle: str | None = None  # Remote GitHub reference (e.g., "kasperjunge/commit")
    path: str | None = None  # Local file/directory path (e.g., "./commands/docs.md")

    def __post_init__(self) -> None:
        """Validate dependency has exactly one source."""
        if self.handle and self.path:
            raise ValueError("Dependency cannot have both handle and path")
        if not self.handle and not self.path:
            raise ValueError("Dependency must have either handle or path")

    @property
    def is_local(self) -> bool:
        """Return True if this is a local path dependency."""
        return self.path is not None

    @property
    def is_remote(self) -> bool:
        """Return True if this is a remote GitHub dependency."""
        return self.handle is not None

    @property
    def identifier(self) -> str:
        """Return unique identifier (path or handle)."""
        return self.path or self.handle or ""


@dataclass
class PackageConfig:
    """Workspace package configuration.

    Represents a named workspace that groups related dependencies.

    Example in agr.toml:
        [packages.myworkspace]
        path = "./packages/myworkspace"
        dependencies = [
            { path = "./skills/tool-use", type = "skill" },
        ]
    """
    path: str
    dependencies: list["Dependency"] = field(default_factory=list)


# Legacy dataclasses for migration support
@dataclass
class DependencySpec:
    """Legacy: Specification for a dependency in old agr.toml format."""

    type: str | None = None


@dataclass
class LocalResourceSpec:
    """Legacy: Specification for a local resource in old agr.toml format."""

    path: str
    type: str | None = None
    package: str | None = None


@dataclass
class AgrConfig:
    """
    Configuration loaded from agr.toml.

    New unified format (list):
    dependencies = [
        { handle = "kasperjunge/commit", type = "skill" },
        { path = "./commands/docs.md", type = "command" },
    ]

    Old format (tables) is auto-migrated on load:
    [dependencies]
    "kasperjunge/commit" = {}

    [local]
    "custom-skill" = { path = "./my-resources/custom-skill", type = "skill" }
    """

    dependencies: list[Dependency] = field(default_factory=list)
    packages: dict[str, PackageConfig] = field(default_factory=dict)
    _document: TOMLDocument | None = field(default=None, repr=False)
    _path: Path | None = field(default=None, repr=False)
    _migrated: bool = field(default=False, repr=False)  # Track if migration occurred

    @classmethod
    def _is_new_format(cls, doc: TOMLDocument) -> bool:
        """Detect if document uses new list-based format."""
        deps = doc.get("dependencies")
        # New format: dependencies is a list
        return isinstance(deps, list)

    @classmethod
    def _migrate_old_format(
        cls, doc: TOMLDocument
    ) -> tuple[list[Dependency], bool]:
        """Migrate old table-based format to new list format.

        Returns:
            Tuple of (dependencies_list, was_migrated)
        """
        dependencies: list[Dependency] = []

        # Parse old [dependencies] table section
        deps_section = doc.get("dependencies", {})
        if isinstance(deps_section, dict):
            for ref, spec in deps_section.items():
                dep_type = "skill"  # Default type for old format
                if isinstance(spec, dict) and spec.get("type"):
                    dep_type = spec["type"]
                dependencies.append(Dependency(handle=ref, type=dep_type))

        # Parse old [local] section
        local_section = doc.get("local", {})
        if isinstance(local_section, dict):
            for _name, spec in local_section.items():
                if isinstance(spec, dict) and "path" in spec:
                    dep_type = spec.get("type", "skill")
                    dependencies.append(Dependency(path=spec["path"], type=dep_type))

        was_migrated = bool(deps_section) or bool(local_section)
        return dependencies, was_migrated

    @classmethod
    def _parse_new_format(cls, doc: TOMLDocument) -> list[Dependency]:
        """Parse new list-based format."""
        dependencies: list[Dependency] = []
        deps_list = doc.get("dependencies", [])

        for item in deps_list:
            if not isinstance(item, dict):
                continue

            dep_type = item.get("type", "skill")
            handle = item.get("handle")
            path = item.get("path")

            if handle:
                dependencies.append(Dependency(handle=handle, type=dep_type))
            elif path:
                dependencies.append(Dependency(path=path, type=dep_type))

        return dependencies

    @classmethod
    def _parse_packages_section(cls, doc: TOMLDocument) -> dict[str, "PackageConfig"]:
        """Parse [packages] section from document."""
        packages: dict[str, PackageConfig] = {}
        packages_section = doc.get("packages", {})

        if not isinstance(packages_section, dict):
            return packages

        for name, pkg_data in packages_section.items():
            if not isinstance(pkg_data, dict):
                continue

            pkg_path = pkg_data.get("path", f"./packages/{name}")
            pkg_deps: list[Dependency] = []

            deps_list = pkg_data.get("dependencies", [])
            for item in deps_list:
                if not isinstance(item, dict):
                    continue
                dep_type = item.get("type", "skill")
                handle = item.get("handle")
                path = item.get("path")
                if handle:
                    pkg_deps.append(Dependency(handle=handle, type=dep_type))
                elif path:
                    pkg_deps.append(Dependency(path=path, type=dep_type))

            packages[name] = PackageConfig(path=pkg_path, dependencies=pkg_deps)

        return packages

    @classmethod
    def load(cls, path: Path) -> "AgrConfig":
        """
        Load configuration from an agr.toml file.

        Supports both new list format and old table format.
        Old format is auto-migrated in memory and will be saved in new format.

        Args:
            path: Path to the agr.toml file

        Returns:
            AgrConfig instance with loaded dependencies

        Raises:
            ConfigParseError: If the file contains invalid TOML
        """
        if not path.exists():
            config = cls()
            config._path = path
            return config

        try:
            content = path.read_text()
            doc = tomlkit.parse(content)
        except TOMLKitError as e:
            raise ConfigParseError(f"Invalid TOML in {path}: {e}")

        config = cls()
        config._document = doc
        config._path = path

        if cls._is_new_format(doc):
            config.dependencies = cls._parse_new_format(doc)
            config._migrated = False
        else:
            config.dependencies, config._migrated = cls._migrate_old_format(doc)

        # Parse packages section
        config.packages = cls._parse_packages_section(doc)

        return config

    def save(self, path: Path | None = None) -> None:
        """
        Save configuration to an agr.toml file in new list format.

        Args:
            path: Path to save to (uses original path if not specified)
        """
        save_path = path or self._path
        if save_path is None:
            raise ValueError("No path specified for saving config")

        # Always create fresh document for new format
        doc = tomlkit.document()

        # Build dependencies array
        deps_array = tomlkit.array()
        deps_array.multiline(True)

        for dep in self.dependencies:
            item = tomlkit.inline_table()
            if dep.handle:
                item["handle"] = dep.handle
            if dep.path:
                item["path"] = dep.path
            item["type"] = dep.type
            deps_array.append(item)

        doc["dependencies"] = deps_array

        # Build packages section if any exist
        if self.packages:
            packages_table = tomlkit.table()
            for name, pkg in self.packages.items():
                pkg_table = tomlkit.table()
                pkg_table["path"] = pkg.path
                pkg_deps_array = tomlkit.array()
                pkg_deps_array.multiline(True)
                for dep in pkg.dependencies:
                    item = tomlkit.inline_table()
                    if dep.handle:
                        item["handle"] = dep.handle
                    if dep.path:
                        item["path"] = dep.path
                    item["type"] = dep.type
                    pkg_deps_array.append(item)
                pkg_table["dependencies"] = pkg_deps_array
                packages_table[name] = pkg_table
            doc["packages"] = packages_table

        save_path.write_text(tomlkit.dumps(doc))
        self._document = doc
        self._path = save_path
        self._migrated = False

    def add_dependency(self, dep: Dependency) -> None:
        """
        Add or update a dependency.

        If a dependency with the same identifier exists, it's replaced.

        Args:
            dep: Dependency to add
        """
        # Remove existing with same identifier
        self.dependencies = [
            d for d in self.dependencies if d.identifier != dep.identifier
        ]
        self.dependencies.append(dep)

    def add_remote(self, handle: str, resource_type: str) -> None:
        """
        Add a remote GitHub dependency.

        Args:
            handle: GitHub reference (e.g., "kasperjunge/commit")
            resource_type: Type of resource ("skill", "command", "agent")
        """
        self.add_dependency(Dependency(handle=handle, type=resource_type))

    def add_local(self, path: str, resource_type: str) -> None:
        """
        Add a local path dependency.

        Args:
            path: Local file/directory path
            resource_type: Type of resource ("skill", "command", "agent", "package")
        """
        self.add_dependency(Dependency(path=path, type=resource_type))

    def add_to_workspace(self, workspace: str, dep: Dependency) -> None:
        """
        Add a dependency to a workspace package.

        Creates the workspace if it doesn't exist.

        Args:
            workspace: Name of the workspace package
            dep: Dependency to add to the workspace
        """
        if workspace not in self.packages:
            self.packages[workspace] = PackageConfig(path=f"./packages/{workspace}")
        pkg = self.packages[workspace]
        # Remove existing with same identifier
        pkg.dependencies = [d for d in pkg.dependencies if d.identifier != dep.identifier]
        pkg.dependencies.append(dep)

    def remove_dependency(self, identifier: str) -> bool:
        """
        Remove a dependency by its identifier (handle or path).

        Args:
            identifier: Handle or path to remove

        Returns:
            True if removed, False if not found
        """
        original_len = len(self.dependencies)
        self.dependencies = [
            d for d in self.dependencies if d.identifier != identifier
        ]
        return len(self.dependencies) < original_len

    def remove_by_handle(self, handle: str) -> bool:
        """Remove a remote dependency by handle."""
        return self.remove_dependency(handle)

    def remove_by_path(self, path: str) -> bool:
        """Remove a local dependency by path."""
        return self.remove_dependency(path)

    def get_by_handle(self, handle: str) -> Dependency | None:
        """Find a dependency by its handle."""
        for dep in self.dependencies:
            if dep.handle == handle:
                return dep
        return None

    def get_by_path(self, path: str) -> Dependency | None:
        """Find a dependency by its path."""
        for dep in self.dependencies:
            if dep.path == path:
                return dep
        return None

    def get_local_dependencies(self) -> list[Dependency]:
        """Return all local path dependencies."""
        return [d for d in self.dependencies if d.is_local]

    def get_remote_dependencies(self) -> list[Dependency]:
        """Return all remote GitHub dependencies."""
        return [d for d in self.dependencies if d.is_remote]


def find_config(start_path: Path | None = None) -> Path | None:
    """
    Find agr.toml by walking up from the start path to the git root.

    Args:
        start_path: Directory to start searching from (defaults to cwd)

    Returns:
        Path to agr.toml if found, None otherwise
    """
    current = start_path or Path.cwd()

    while True:
        config_path = current / "agr.toml"
        if config_path.exists():
            return config_path

        # Check if we've reached git root
        if (current / ".git").exists():
            return None

        # Move to parent
        parent = current.parent
        if parent == current:
            # Reached filesystem root
            return None
        current = parent


def get_or_create_config(start_path: Path | None = None) -> tuple[Path, AgrConfig]:
    """
    Get existing config or create a new one in cwd.

    Args:
        start_path: Directory to start searching from (defaults to cwd)

    Returns:
        Tuple of (path to config, AgrConfig instance)
    """
    existing = find_config(start_path)
    if existing:
        return existing, AgrConfig.load(existing)

    # Create new config in cwd
    cwd = start_path or Path.cwd()
    config_path = cwd / "agr.toml"

    config = AgrConfig()
    config.save(config_path)

    return config_path, config
