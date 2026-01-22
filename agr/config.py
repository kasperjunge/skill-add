"""Configuration management for agr.toml."""

from dataclasses import dataclass, field
from pathlib import Path

import tomlkit
from tomlkit import TOMLDocument
from tomlkit.exceptions import TOMLKitError

from agr.exceptions import ConfigError


@dataclass
class Dependency:
    """A dependency in agr.toml.

    Examples:
        Remote: { handle = "kasperjunge/commit", type = "skill" }
        Local:  { path = "./my-skill", type = "skill" }
    """

    type: str  # Always "skill" for now
    handle: str | None = None  # Remote GitHub reference
    path: str | None = None  # Local path

    def __post_init__(self) -> None:
        """Validate dependency has exactly one source."""
        if self.handle and self.path:
            raise ValueError("Dependency cannot have both handle and path")
        if not self.handle and not self.path:
            raise ValueError("Dependency must have either handle or path")

    @property
    def is_local(self) -> bool:
        """True if this is a local path dependency."""
        return self.path is not None

    @property
    def is_remote(self) -> bool:
        """True if this is a remote GitHub dependency."""
        return self.handle is not None

    @property
    def identifier(self) -> str:
        """Unique identifier (path or handle)."""
        return self.path or self.handle or ""


@dataclass
class AgrConfig:
    """Configuration loaded from agr.toml.

    Format:
        dependencies = [
            { handle = "kasperjunge/commit", type = "skill" },
            { path = "./my-skill", type = "skill" },
        ]
    """

    dependencies: list[Dependency] = field(default_factory=list)
    _path: Path | None = field(default=None, repr=False)

    @classmethod
    def load(cls, path: Path) -> "AgrConfig":
        """Load configuration from agr.toml.

        Args:
            path: Path to agr.toml

        Returns:
            AgrConfig instance

        Raises:
            ConfigError: If the file contains invalid TOML
        """
        if not path.exists():
            config = cls()
            config._path = path
            return config

        try:
            content = path.read_text()
            doc = tomlkit.parse(content)
        except TOMLKitError as e:
            raise ConfigError(f"Invalid TOML in {path}: {e}")

        config = cls()
        config._path = path

        # Parse dependencies list
        deps_list = doc.get("dependencies", [])
        for item in deps_list:
            if not isinstance(item, dict):
                continue
            dep_type = item.get("type", "skill")
            handle = item.get("handle")
            path_val = item.get("path")

            if handle:
                config.dependencies.append(Dependency(handle=handle, type=dep_type))
            elif path_val:
                config.dependencies.append(Dependency(path=path_val, type=dep_type))

        return config

    def save(self, path: Path | None = None) -> None:
        """Save configuration to agr.toml.

        Args:
            path: Path to save to (uses original path if not specified)

        Raises:
            ValueError: If no path specified and no original path
        """
        save_path = path or self._path
        if save_path is None:
            raise ValueError("No path specified for saving config")

        doc: TOMLDocument = tomlkit.document()

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
        save_path.write_text(tomlkit.dumps(doc))
        self._path = save_path

    def add_dependency(self, dep: Dependency) -> None:
        """Add or update a dependency.

        If a dependency with the same identifier exists, it's replaced.
        """
        self.dependencies = [
            d for d in self.dependencies if d.identifier != dep.identifier
        ]
        self.dependencies.append(dep)

    def remove_dependency(self, identifier: str) -> bool:
        """Remove a dependency by identifier (handle or path).

        Returns:
            True if removed, False if not found
        """
        original_len = len(self.dependencies)
        self.dependencies = [
            d for d in self.dependencies if d.identifier != identifier
        ]
        return len(self.dependencies) < original_len

    def get_by_identifier(self, identifier: str) -> Dependency | None:
        """Find a dependency by handle or path."""
        for dep in self.dependencies:
            if dep.identifier == identifier:
                return dep
        return None


def find_config(start_path: Path | None = None) -> Path | None:
    """Find agr.toml by walking up from start path.

    Stops at git root or filesystem root.

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

        # Stop at git root
        if (current / ".git").exists():
            return None

        parent = current.parent
        if parent == current:
            return None
        current = parent


def find_repo_root(start_path: Path | None = None) -> Path | None:
    """Find the git repository root.

    Args:
        start_path: Directory to start searching from (defaults to cwd)

    Returns:
        Path to repo root if found, None otherwise
    """
    current = start_path or Path.cwd()

    while True:
        if (current / ".git").exists():
            return current

        parent = current.parent
        if parent == current:
            return None
        current = parent


def get_or_create_config(start_path: Path | None = None) -> tuple[Path, AgrConfig]:
    """Get existing config or create new one.

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
