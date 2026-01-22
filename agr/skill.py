"""Skill validation and SKILL.md handling."""

import re
from enum import Enum
from pathlib import Path


class ResourceType(Enum):
    """Resource types supported by agr."""

    SKILL = "skill"
    # Future: INSTRUCTION = "instruction"


# Marker file for skills
SKILL_MARKER = "SKILL.md"


def is_valid_skill_dir(path: Path) -> bool:
    """Check if a directory is a valid skill (contains SKILL.md).

    Args:
        path: Path to check

    Returns:
        True if the path is a directory containing SKILL.md
    """
    if not path.is_dir():
        return False
    return (path / SKILL_MARKER).exists()


def find_skill_in_repo(repo_dir: Path, skill_name: str) -> Path | None:
    """Find a skill directory in a downloaded repo.

    Searches for:
    1. resources/skills/{skill_name}/SKILL.md
    2. skills/{skill_name}/SKILL.md
    3. {skill_name}/SKILL.md (root level)

    Args:
        repo_dir: Path to extracted repository
        skill_name: Name of the skill to find

    Returns:
        Path to skill directory if found, None otherwise
    """
    search_paths = [
        repo_dir / "resources" / "skills" / skill_name,
        repo_dir / "skills" / skill_name,
        repo_dir / skill_name,
    ]

    for path in search_paths:
        if is_valid_skill_dir(path):
            return path

    return None


def discover_skills_in_repo(repo_dir: Path) -> list[tuple[str, Path]]:
    """Discover all skills in a repository.

    Args:
        repo_dir: Path to extracted repository

    Returns:
        List of (skill_name, skill_path) tuples
    """
    skills: list[tuple[str, Path]] = []

    # Search locations
    search_roots = [
        repo_dir / "resources" / "skills",
        repo_dir / "skills",
        repo_dir,  # Root level skills
    ]

    for root in search_roots:
        if not root.exists() or not root.is_dir():
            continue

        # Check immediate children for SKILL.md
        for child in root.iterdir():
            if child.is_dir() and is_valid_skill_dir(child):
                skills.append((child.name, child))

    return skills


def update_skill_md_name(skill_dir: Path, new_name: str) -> None:
    """Update the name field in SKILL.md.

    Args:
        skill_dir: Path to skill directory containing SKILL.md
        new_name: New name to set in frontmatter
    """
    skill_md = skill_dir / SKILL_MARKER
    if not skill_md.exists():
        return

    content = skill_md.read_text()

    # Check if file has YAML frontmatter
    if not content.startswith("---"):
        # No frontmatter, add it
        new_content = f"---\nname: {new_name}\n---\n\n{content}"
        skill_md.write_text(new_content)
        return

    # Split by frontmatter delimiter
    parts = content.split("---", 2)
    if len(parts) < 3:
        # Malformed frontmatter
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
        if re.match(r"^\s*name\s*:", line):
            new_lines.append(f"name: {new_name}")
            name_found = True
        else:
            new_lines.append(line)

    if not name_found:
        new_lines.insert(0, f"name: {new_name}")

    new_frontmatter = "\n".join(new_lines)
    new_content = f"---\n{new_frontmatter}\n---{body}"
    skill_md.write_text(new_content)


def validate_skill_name(name: str) -> bool:
    """Validate a skill name.

    Valid names: alphanumeric, hyphens, underscores.

    Args:
        name: Skill name to validate

    Returns:
        True if valid
    """
    if not name:
        return False
    return bool(re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$", name))


def create_skill_scaffold(name: str, base_dir: Path | None = None) -> Path:
    """Create a skill scaffold with SKILL.md.

    Args:
        name: Skill name
        base_dir: Directory to create skill in (defaults to cwd)

    Returns:
        Path to created skill directory

    Raises:
        ValueError: If name is invalid
        FileExistsError: If skill directory already exists
    """
    if not validate_skill_name(name):
        raise ValueError(
            f"Invalid skill name '{name}': must be alphanumeric with hyphens/underscores"
        )

    base = base_dir or Path.cwd()
    skill_dir = base / name

    if skill_dir.exists():
        raise FileExistsError(f"Directory '{name}' already exists")

    skill_dir.mkdir(parents=True)

    # Create SKILL.md with scaffold content
    skill_md = skill_dir / SKILL_MARKER
    skill_md.write_text(f"""---
name: {name}
---

# {name}

Description of what this skill does.

## When to use

Describe when Claude should use this skill.

## Instructions

Provide detailed instructions for Claude here.
""")

    return skill_dir
