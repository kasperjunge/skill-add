"""Handle parsing for agr.

Handle formats:
- Remote: "username/skill" or "username/repo/skill"
- Local: "./path/to/skill" or "path/to/skill"

Installed naming:
- Remote: "username:skill" or "username:repo:skill"
- Local: "local:skillname"
"""

from dataclasses import dataclass
from pathlib import Path

from agr.exceptions import InvalidHandleError


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

        Examples:
            Remote: "kasperjunge:commit" or "maragudk:skills:collaboration"
            Local: "local:my-skill"
        """
        if self.is_local:
            return f"local:{self.name}"

        if not self.username:
            return self.name

        if self.repo:
            return f"{self.username}:{self.repo}:{self.name}"
        return f"{self.username}:{self.name}"

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
        return ParsedHandle(
            username=parts[0],
            name=parts[1],
        )

    if len(parts) == 3:
        # user/repo/name format
        return ParsedHandle(
            username=parts[0],
            repo=parts[1],
            name=parts[2],
        )

    raise InvalidHandleError(
        f"Invalid handle '{ref}': too many path segments (expected user/name or user/repo/name)"
    )


def installed_name_to_toml_handle(installed_name: str) -> str:
    """Convert installed directory name back to agr.toml handle.

    Args:
        installed_name: Directory name like "kasperjunge:commit" or "local:my-skill"

    Returns:
        Handle like "kasperjunge/commit" or the local path
    """
    if ":" not in installed_name:
        return installed_name

    parts = installed_name.split(":")

    if parts[0] == "local":
        # Local skill - return just the name (path is lost)
        return parts[1] if len(parts) > 1 else installed_name

    # Remote: convert colons to slashes
    return "/".join(parts)
