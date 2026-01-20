"""Package identification via PACKAGE.md marker files."""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PackageMetadata:
    """Metadata parsed from a PACKAGE.md file."""

    name: str | None
    valid: bool
    error: str | None = None


# Regex for valid package name: alphanumeric, hyphens, underscores
# Must start with alphanumeric, no consecutive special chars
VALID_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9_-]*[a-zA-Z0-9])?$|^[a-zA-Z0-9]$")


class _NotFound:
    """Sentinel value to distinguish between 'not found' and 'found but empty'."""


_NOT_FOUND = _NotFound()


def _parse_simple_yaml_value(frontmatter: str, key: str) -> str | _NotFound:
    """Parse a simple key: value from YAML frontmatter.

    Handles basic cases like:
    - name: my-package
    - name: "my-package"
    - name: 'my-package'

    Args:
        frontmatter: The YAML frontmatter content (without --- delimiters)
        key: The key to extract

    Returns:
        The value if found (may be empty string), _NOT_FOUND if key not present
    """
    prefix = f"{key}:"
    for line in frontmatter.split("\n"):
        line = line.strip()
        if not line.startswith(prefix):
            continue
        value = line[len(prefix):].strip()
        # Remove surrounding quotes if present
        if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
            value = value[1:-1]
        return value
    return _NOT_FOUND


def parse_package_md(path: Path) -> PackageMetadata:
    """Parse a PACKAGE.md file and extract metadata.

    Args:
        path: Path to the PACKAGE.md file

    Returns:
        PackageMetadata with name if valid, or error details if invalid
    """
    if not path.exists():
        return PackageMetadata(name=None, valid=False, error="PACKAGE.md not found")

    try:
        content = path.read_text()
    except OSError as e:
        return PackageMetadata(name=None, valid=False, error=f"Failed to read PACKAGE.md: {e}")

    # Check for YAML frontmatter
    if not content.startswith("---"):
        return PackageMetadata(
            name=None, valid=False, error="PACKAGE.md must have YAML frontmatter (start with ---)"
        )

    # Split by frontmatter delimiter
    parts = content.split("---", 2)
    if len(parts) < 3:
        return PackageMetadata(
            name=None,
            valid=False,
            error="PACKAGE.md has malformed frontmatter (missing closing ---)",
        )

    frontmatter = parts[1]

    # Extract name field
    name = _parse_simple_yaml_value(frontmatter, "name")

    if isinstance(name, _NotFound):
        return PackageMetadata(
            name=None, valid=False, error="PACKAGE.md frontmatter must contain a 'name' field"
        )

    if not name:
        return PackageMetadata(name=None, valid=False, error="PACKAGE.md 'name' field cannot be empty")

    # Validate name format
    if not VALID_NAME_PATTERN.match(name):
        return PackageMetadata(
            name=None,
            valid=False,
            error=f"Invalid package name '{name}': must be alphanumeric with hyphens/underscores, "
            "start and end with alphanumeric",
        )

    return PackageMetadata(name=name, valid=True)


def validate_no_nested_packages(package_path: Path) -> list[Path]:
    """Validate that a package directory contains no nested PACKAGE.md files.

    Packages cannot contain other packages. This function checks for any
    PACKAGE.md files within subdirectories of the given package path.

    Args:
        package_path: Path to the package directory (containing the root PACKAGE.md)

    Returns:
        List of paths to any nested PACKAGE.md files found (empty if valid)
    """
    return [
        package_md
        for package_md in package_path.rglob("PACKAGE.md")
        if package_md.parent != package_path
    ]
