"""Utility functions for agr."""

import re
from pathlib import Path


# Type directories that trigger path namespacing
TYPE_DIRECTORIES = ("skills", "commands", "agents", "rules")


def compute_flattened_resource_name(
    username: str,
    path_segments: list[str],
    package_name: str | None = None,
) -> str:
    """Compute flattened resource name with colons.

    Naming formula: username : package : path : resource

    Args:
        username: The GitHub username or "local" for local resources
        path_segments: Path segments under the type directory
                       e.g., ["git", "status"] or ["commit"]
        package_name: Optional package name to prepend after username

    Returns:
        Flattened name with colons, e.g.:
        - ("user", ["git", "status"], None) -> "user:git:status"
        - ("user", ["git", "status"], "my-toolkit") -> "user:my-toolkit:git:status"
        - ("user", ["standalone"], "my-toolkit") -> "user:my-toolkit:standalone"

    Examples:
        >>> compute_flattened_resource_name("kasperjunge", ["commit"])
        'kasperjunge:commit'
        >>> compute_flattened_resource_name("kasperjunge", ["git", "status"], "my-toolkit")
        'kasperjunge:my-toolkit:git:status'
    """
    if not path_segments:
        raise ValueError("path_segments cannot be empty")

    parts = [username]
    if package_name:
        parts.append(package_name)
    parts.extend(path_segments)
    return ":".join(parts)


def compute_flattened_skill_name(username: str, path_segments: list[str]) -> str:
    """Compute the flattened skill name with colons.

    Deprecated: Use compute_flattened_resource_name() instead.

    Claude Code's .claude/skills/ directory only discovers top-level directories.
    To support nested skill organization, we flatten the path using colons.

    Args:
        username: The GitHub username or "local" for local resources
        path_segments: Path segments from skills/ root to the skill
                       e.g., ["commit"] or ["product-strategy", "growth-hacker"]

    Returns:
        Flattened name with colons, e.g.:
        - ("kasperjunge", ["commit"]) -> "kasperjunge:commit"
        - ("kasperjunge", ["product-strategy", "growth-hacker"]) -> "kasperjunge:product-strategy:growth-hacker"

    Examples:
        >>> compute_flattened_skill_name("kasperjunge", ["commit"])
        'kasperjunge:commit'
        >>> compute_flattened_skill_name("kasperjunge", ["product-strategy", "growth-hacker"])
        'kasperjunge:product-strategy:growth-hacker'
        >>> compute_flattened_skill_name("dsjacobsen", ["golang-pro"])
        'dsjacobsen:golang-pro'
    """
    return compute_flattened_resource_name(username, path_segments)


def compute_path_segments(
    resource_path: Path,
    resource_root: Path | None = None,
    type_dirs: tuple[str, ...] = TYPE_DIRECTORIES,
) -> list[str]:
    """Compute namespace path segments from a resource path.

    Extracts path segments UNDER type directories (skills/, commands/, etc.)
    When a type directory is found in the path, returns segments after it.
    If no type directory is found, returns just the resource name.

    Args:
        resource_path: Full path to the resource
        resource_root: Optional explicit resource root. If provided, computes
                       relative path from it instead of searching for type dirs.
        type_dirs: Tuple of type directory names to search for.
                   Defaults to TYPE_DIRECTORIES.

    Returns:
        List of path segments representing the namespace.

    Examples:
        >>> compute_path_segments(Path("skills/git/status"))
        ['git', 'status']
        >>> compute_path_segments(Path("commands/git/status.md"))
        ['git', 'status']
        >>> compute_path_segments(Path("standalone/SKILL.md"))
        ['standalone']
        >>> compute_path_segments(Path("./resources/skills/commit"))
        ['commit']
        >>> compute_path_segments(Path("./resources/skills/product-strategy/growth-hacker"))
        ['product-strategy', 'growth-hacker']
    """
    parts = resource_path.parts

    # If explicit resource_root provided, compute relative path
    if resource_root is not None:
        try:
            rel_path = resource_path.relative_to(resource_root)
            rel_parts = list(rel_path.parts)
            # Remove file extension from last part if it's a file
            if rel_parts and "." in rel_parts[-1]:
                rel_parts[-1] = rel_parts[-1].rsplit(".", 1)[0]
            return rel_parts if rel_parts else [resource_path.stem or resource_path.name]
        except ValueError:
            # resource_path is not relative to resource_root, fall back to name only
            name = resource_path.stem if resource_path.suffix else resource_path.name
            return [name]

    # Search for any type directory in path parts
    for type_dir in type_dirs:
        try:
            type_idx = parts.index(type_dir)
            segments = list(parts[type_idx + 1:])
            if segments:
                # Remove file extension from last segment if present
                if "." in segments[-1]:
                    segments[-1] = segments[-1].rsplit(".", 1)[0]
                return segments
        except ValueError:
            continue

    # No type dir found, use just the name (without extension)
    name = resource_path.stem if resource_path.suffix else resource_path.name
    return [name]


def compute_path_segments_from_skill_path(skill_path: Path, skills_root: Path | None = None) -> list[str]:
    """Compute namespace path segments from a skill source path.

    Deprecated: Use compute_path_segments() instead.

    Extracts the relative path from the skills/ root to the skill directory.

    Args:
        skill_path: Full path to the skill directory
        skills_root: Optional explicit skills root. If not provided, attempts
                     to find "skills" in the path.

    Returns:
        List of path segments from skills root to skill.

    Examples:
        >>> compute_path_segments_from_skill_path(Path("./resources/skills/commit"))
        ['commit']
        >>> compute_path_segments_from_skill_path(Path("./resources/skills/product-strategy/growth-hacker"))
        ['product-strategy', 'growth-hacker']
        >>> compute_path_segments_from_skill_path(Path("./skills/my-skill"))
        ['my-skill']
    """
    # Use the generalized function, but only look for "skills" to maintain backward compatibility
    return compute_path_segments(skill_path, skills_root, type_dirs=("skills",))


def update_skill_md_name(skill_dir: Path, new_name: str) -> None:
    """Update the name field in SKILL.md after installation.

    Parses the YAML frontmatter and updates the 'name' field to match
    the flattened directory name for discoverability.

    Args:
        skill_dir: Path to the skill directory containing SKILL.md
        new_name: The new name to set in the frontmatter

    Raises:
        FileNotFoundError: If SKILL.md doesn't exist in skill_dir
    """
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found in {skill_dir}")

    content = skill_md.read_text()

    # Check if file has YAML frontmatter (starts with ---)
    if not content.startswith("---"):
        # No frontmatter, add it with name
        new_content = f"---\nname: {new_name}\n---\n\n{content}"
        skill_md.write_text(new_content)
        return

    # Split by frontmatter delimiter
    parts = content.split("---", 2)
    if len(parts) < 3:
        # Malformed frontmatter, prepend new frontmatter
        new_content = f"---\nname: {new_name}\n---\n\n{content}"
        skill_md.write_text(new_content)
        return

    frontmatter = parts[1]
    body = parts[2]

    # Update or add name in frontmatter
    lines = frontmatter.strip().split("\n")
    new_lines = []
    name_found = False

    for line in lines:
        # Match name field (handles 'name: value' or 'name:value')
        if re.match(r"^\s*name\s*:", line):
            new_lines.append(f"name: {new_name}")
            name_found = True
        else:
            new_lines.append(line)

    if not name_found:
        # Insert name at the beginning of frontmatter
        new_lines.insert(0, f"name: {new_name}")

    new_frontmatter = "\n".join(new_lines)
    new_content = f"---\n{new_frontmatter}\n---{body}"
    skill_md.write_text(new_content)


def find_package_context(resource_path: Path) -> tuple[str | None, Path | None]:
    """Find if a resource is inside a package.

    Walks up parent directories looking for PACKAGE.md.

    Args:
        resource_path: Path to the resource (file or directory)

    Returns:
        Tuple of (package_name, package_root) if found, or (None, None) if not.
        The package_name is extracted from the PACKAGE.md frontmatter.
    """
    from agr.package import parse_package_md

    # Resolve the path to get absolute path
    try:
        resource_path = resource_path.resolve()
    except OSError:
        return (None, None)

    # Walk up parent directories looking for PACKAGE.md
    current = resource_path if resource_path.is_dir() else resource_path.parent

    while current != current.parent:  # Stop at filesystem root
        package_md = current / "PACKAGE.md"
        if package_md.exists():
            metadata = parse_package_md(package_md)
            if metadata.valid and metadata.name:
                return (metadata.name, current)
            # Found PACKAGE.md but it's invalid - still consider it a package boundary
            # but return None for name
            return (None, current)
        current = current.parent

    return (None, None)
