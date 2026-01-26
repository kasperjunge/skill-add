"""Handle parsing for agr.

Handle formats:
- Remote: "username/skill" or "username/repo/skill"
- Local: "./path/to/skill" or "path/to/skill"

Installed naming (Windows-compatible using -- separator):
- Remote: "username--skill" or "username--repo--skill"
- Local: "local--skillname"
"""

from dataclasses import dataclass
from pathlib import Path

from agr.exceptions import InvalidHandleError

# Separator used in installed directory names (Windows-compatible)
INSTALLED_NAME_SEPARATOR = "--"
# Prefix for local skills in installed name
LOCAL_PREFIX = "local"
# Legacy separator (colon) for backward compatibility during migration
LEGACY_SEPARATOR = ":"


@dataclass
class ParsedHandle:
    """Parsed resource handle."""

    username: str | None = None  # GitHub username, None for local
    repo: str | None = None  # Repository name, None = default (agent-resources)
    name: str = ""  # Skill name (final segment)
    is_local: bool = False  # True for local path references
    local_path: Path | None = None  # Original local path if is_local

    @property
    def is_remote(self) -> bool:
        """True if this is a remote GitHub reference."""
        return not self.is_local and self.username is not None

    def to_toml_handle(self) -> str:
        """Convert to agr.toml format.

        Examples:
            Remote: "kasperjunge/commit" or "maragudk/skills/collaboration"
            Local: "./my-skill"
        """
        if self.is_local and self.local_path:
            return str(self.local_path)

        if not self.username:
            return self.name

        if self.repo:
            return f"{self.username}/{self.repo}/{self.name}"
        return f"{self.username}/{self.name}"

    def to_installed_name(self) -> str:
        """Convert to installed directory name.

        Uses INSTALLED_NAME_SEPARATOR (--) for Windows compatibility.

        Examples:
            Remote: "kasperjunge--commit" or "maragudk--skills--collaboration"
            Local: "local--my-skill"
        """
        sep = INSTALLED_NAME_SEPARATOR
        if self.is_local:
            return f"{LOCAL_PREFIX}{sep}{self.name}"

        if not self.username:
            return self.name

        if self.repo:
            return f"{self.username}{sep}{self.repo}{sep}{self.name}"
        return f"{self.username}{sep}{self.name}"

    def get_github_repo(self) -> tuple[str, str]:
        """Get (username, repo_name) for GitHub download.

        Returns:
            Tuple of (username, repo_name). repo_name defaults to "agent-resources".

        Raises:
            InvalidHandleError: If this is a local handle.
        """
        if self.is_local:
            raise InvalidHandleError("Cannot get GitHub repo for local handle")
        if not self.username:
            raise InvalidHandleError("No username in handle")
        return (self.username, self.repo or "agent-resources")


def parse_handle(ref: str) -> ParsedHandle:
    """Parse a handle string into components.

    Args:
        ref: Handle string. Examples:
            - "kasperjunge/commit" -> remote, user=kasperjunge, name=commit
            - "maragudk/skills/collaboration" -> remote, user=maragudk, repo=skills, name=collaboration
            - "./my-skill" -> local, name=my-skill
            - "../other/skill" -> local, name=skill

    Returns:
        ParsedHandle with parsed components.

    Raises:
        InvalidHandleError: If the handle format is invalid.
    """
    if not ref or not ref.strip():
        raise InvalidHandleError("Empty handle")

    ref = ref.strip()

    # Local path detection: starts with . or /
    if ref.startswith(("./", "../", "/")):
        path = Path(ref)
        _validate_no_separator_in_name(ref, path.name)
        return ParsedHandle(
            is_local=True,
            name=path.name,
            local_path=path,
        )

    # Also treat as local if it's a relative path that exists
    if "/" not in ref or (Path(ref).exists() and not ref.count("/") == 1):
        # Check if it's a path (has multiple segments or exists)
        test_path = Path(ref)
        if test_path.exists():
            _validate_no_separator_in_name(ref, test_path.name)
            return ParsedHandle(
                is_local=True,
                name=test_path.name,
                local_path=test_path,
            )

    # Remote handle: split by /
    parts = ref.split("/")

    if len(parts) == 1:
        # Simple name like "commit" - treat as local since no username
        raise InvalidHandleError(
            f"Invalid handle '{ref}': remote handles require username/name format"
        )

    if len(parts) == 2:
        # user/name format
        username, skill_name = parts[0], parts[1]
        _validate_no_separator_in_components(ref, username=username, skill_name=skill_name)
        return ParsedHandle(
            username=username,
            name=skill_name,
        )

    if len(parts) == 3:
        # user/repo/name format
        username, repo, skill_name = parts[0], parts[1], parts[2]
        _validate_no_separator_in_components(ref, username=username, repo=repo, skill_name=skill_name)
        return ParsedHandle(
            username=username,
            repo=repo,
            name=skill_name,
        )

    raise InvalidHandleError(
        f"Invalid handle '{ref}': too many path segments (expected user/name or user/repo/name)"
    )


def _validate_no_separator_in_name(ref: str, name: str) -> None:
    """Validate that a name doesn't contain the reserved separator sequence.

    Args:
        ref: Original handle string for error messages.
        name: The name to validate.

    Raises:
        InvalidHandleError: If the name contains the separator.
    """
    if INSTALLED_NAME_SEPARATOR in name:
        raise InvalidHandleError(
            f"Invalid handle '{ref}': name '{name}' contains reserved sequence '{INSTALLED_NAME_SEPARATOR}'"
        )


def _validate_no_separator_in_components(
    ref: str,
    *,
    username: str | None = None,
    repo: str | None = None,
    skill_name: str | None = None,
) -> None:
    """Validate that no component contains the reserved separator sequence.

    Args:
        ref: Original handle string for error messages.
        username: GitHub username to validate.
        repo: Repository name to validate.
        skill_name: Skill name to validate.

    Raises:
        InvalidHandleError: If any component contains the separator.
    """
    sep = INSTALLED_NAME_SEPARATOR
    for component, name in [("username", username), ("repo", repo), ("skill name", skill_name)]:
        if name and sep in name:
            raise InvalidHandleError(
                f"Invalid handle '{ref}': {component} '{name}' contains reserved sequence '{sep}'"
            )


def installed_name_to_toml_handle(installed_name: str) -> str:
    """Convert installed directory name back to agr.toml handle.

    Supports both new separator format and legacy colon format for backward compatibility.

    Args:
        installed_name: Directory name like "kasperjunge--commit" or "local--my-skill"
                       (also accepts legacy "kasperjunge:commit" or "local:my-skill")

    Returns:
        Handle like "kasperjunge/commit" or the local path
    """
    # Support legacy colon format during migration
    if LEGACY_SEPARATOR in installed_name:
        parts = installed_name.split(LEGACY_SEPARATOR)
        if parts[0] == LOCAL_PREFIX:
            return parts[1] if len(parts) > 1 else installed_name
        return "/".join(parts)

    # New separator format
    if INSTALLED_NAME_SEPARATOR not in installed_name:
        return installed_name

    parts = installed_name.split(INSTALLED_NAME_SEPARATOR)
    if parts[0] == LOCAL_PREFIX:
        # Local skill - return just the name (path is lost)
        return parts[1] if len(parts) > 1 else installed_name

    # Remote: convert separators to slashes
    return "/".join(parts)
