"""Reference resolution for agr dependencies.

Implements three-tier resolution:
1. "commit" -> official index
2. "kasper/commit" -> kasper/agent-resources
3. "kasper/repo/commit" -> kasper/repo
"""

from dataclasses import dataclass
from enum import Enum

import httpx

from agr.exceptions import ResourceNotFoundError

# Default repository name
DEFAULT_REPO = "agent-resources"

# Official index URL (GitHub raw content)
OFFICIAL_INDEX_URL = "https://raw.githubusercontent.com/kasperjunge/agent-resources/main/index.json"

# Cache for the official index
_index_cache: dict[str, dict] | None = None


class RefType(Enum):
    """Type of reference."""

    OFFICIAL = "official"  # From official index (e.g., "commit")
    USER_DEFAULT = "user_default"  # User's agent-resources (e.g., "kasper/commit")
    USER_CUSTOM = "user_custom"  # User's custom repo (e.g., "kasper/my-repo/commit")


@dataclass
class ResolvedRef:
    """A resolved resource reference."""

    ref: str  # Original reference string
    ref_type: RefType
    username: str
    repo: str
    resource_name: str
    path_segments: list[str]  # For nested paths (e.g., ["dir", "hello-world"])
    is_package: bool = False

    @property
    def github_url(self) -> str:
        """Get the GitHub repository URL."""
        return f"https://github.com/{self.username}/{self.repo}"

    @property
    def tarball_url(self) -> str:
        """Get the tarball download URL."""
        return f"https://github.com/{self.username}/{self.repo}/archive/refs/heads/main.tar.gz"

    @property
    def display_ref(self) -> str:
        """Get a display-friendly reference string."""
        if self.ref_type == RefType.OFFICIAL:
            return self.resource_name
        if self.ref_type == RefType.USER_DEFAULT:
            return f"{self.username}/{self.resource_name}"
        return f"{self.username}/{self.repo}/{self.resource_name}"


def _parse_nested_name(name: str) -> tuple[str, list[str]]:
    """Parse a name that may contain colon-delimited path segments.

    Args:
        name: Resource name, possibly with colons (e.g., "dir:hello-world")

    Returns:
        Tuple of (base_name, path_segments)
    """
    if not name:
        raise ValueError("Resource name cannot be empty")

    if name.startswith(":") or name.endswith(":"):
        raise ValueError(f"Invalid resource name '{name}': cannot start or end with ':'")

    segments = name.split(":")

    if any(not seg for seg in segments):
        raise ValueError(f"Invalid resource name '{name}': contains empty path segments")

    base_name = segments[-1]
    return base_name, segments


def _fetch_official_index() -> dict[str, dict]:
    """Fetch the official index from GitHub.

    Returns:
        Dictionary mapping resource names to their metadata

    Note:
        Results are cached in memory for the session.
    """
    global _index_cache

    if _index_cache is not None:
        return _index_cache

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(OFFICIAL_INDEX_URL)
            if response.status_code == 200:
                _index_cache = response.json()
                return _index_cache
    except (httpx.RequestError, ValueError):
        pass

    # Return empty dict if fetch fails
    _index_cache = {}
    return _index_cache


def _lookup_in_official_index(name: str) -> dict | None:
    """Look up a resource in the official index.

    Args:
        name: Resource name

    Returns:
        Resource metadata if found, None otherwise
    """
    index = _fetch_official_index()
    return index.get(name)


def resolve_ref(ref: str, is_package: bool = False) -> ResolvedRef:
    """Resolve a reference string to a ResolvedRef.

    Three-tier resolution:
    1. "commit" -> look up in official index
    2. "kasper/commit" -> kasper/agent-resources/commit
    3. "kasper/repo/commit" -> kasper/repo/commit

    Args:
        ref: Reference string
        is_package: Whether this reference is marked as a package

    Returns:
        ResolvedRef with all resolution details

    Raises:
        ResourceNotFoundError: If reference cannot be resolved
        ValueError: If reference format is invalid
    """
    parts = ref.split("/")

    if len(parts) == 1:
        # Single name -> official index
        name = parts[0]
        _, path_segments = _parse_nested_name(name)
        base_name = path_segments[-1]

        # Look up in official index
        entry = _lookup_in_official_index(base_name)
        if entry:
            return ResolvedRef(
                ref=ref,
                ref_type=RefType.OFFICIAL,
                username=entry.get("username", "kasperjunge"),
                repo=entry.get("repo", DEFAULT_REPO),
                resource_name=name,
                path_segments=path_segments,
                is_package=is_package or entry.get("package", False),
            )

        # Not in index - could be a typo or future addition
        raise ResourceNotFoundError(
            f"Resource '{ref}' not found in official index.\n"
            f"Use 'username/{ref}' to install from a user's repository."
        )

    elif len(parts) == 2:
        # username/name -> username/agent-resources
        username, name = parts
        if not username or not name:
            raise ValueError(f"Invalid reference format: '{ref}'")

        _, path_segments = _parse_nested_name(name)

        return ResolvedRef(
            ref=ref,
            ref_type=RefType.USER_DEFAULT,
            username=username,
            repo=DEFAULT_REPO,
            resource_name=name,
            path_segments=path_segments,
            is_package=is_package,
        )

    elif len(parts) == 3:
        # username/repo/name -> username/repo
        username, repo, name = parts
        if not username or not repo or not name:
            raise ValueError(f"Invalid reference format: '{ref}'")

        _, path_segments = _parse_nested_name(name)

        return ResolvedRef(
            ref=ref,
            ref_type=RefType.USER_CUSTOM,
            username=username,
            repo=repo,
            resource_name=name,
            path_segments=path_segments,
            is_package=is_package,
        )

    else:
        raise ValueError(
            f"Invalid reference format: '{ref}'. "
            "Expected: <name>, <username>/<name>, or <username>/<repo>/<name>"
        )


def clear_index_cache() -> None:
    """Clear the cached official index.

    Useful for testing or forcing a refresh.
    """
    global _index_cache
    _index_cache = None


def build_namespaced_path(
    base_path: str,
    resource_type: str,
    username: str,
    package_name: str | None,
    resource_name: str,
) -> str:
    """Build a namespaced install path for a resource.

    Args:
        base_path: Base .claude directory path
        resource_type: "skills", "commands", or "agents"
        username: Author username (namespace)
        package_name: Package name if resource is part of a package, None otherwise
        resource_name: Name of the resource

    Returns:
        Full path for the resource

    Examples:
        >>> build_namespaced_path(".claude", "skills", "kasper", None, "commit")
        ".claude/skills/kasper/commit"
        >>> build_namespaced_path(".claude", "skills", "kasper", "my-toolkit", "analyzer")
        ".claude/skills/kasper/my-toolkit/analyzer"
    """
    if package_name:
        return f"{base_path}/{resource_type}/{username}/{package_name}/{resource_name}"
    return f"{base_path}/{resource_type}/{username}/{resource_name}"
