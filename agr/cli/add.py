"""Add subcommand for agr - install resources from GitHub."""

import glob
import shutil
from pathlib import Path
from typing import Annotated, List, Optional

import typer

from agr.cli.common import (
    TYPE_TO_SUBDIR,
    console,
    error_exit,
    find_repo_root,
    get_base_path,
    handle_add_bundle,
    handle_add_resource,
    handle_add_unified,
    is_local_path,
)
from agr.config import Dependency, get_or_create_config
from agr.fetcher import ResourceType
from agr.github import get_username_from_git_remote
from agr.package import parse_package_md, validate_no_nested_packages
from agr.utils import (
    compute_flattened_resource_name,
    compute_path_segments,
    find_package_context,
    update_skill_md_name,
)

# Deprecated subcommand names
DEPRECATED_SUBCOMMANDS = {"skill", "command", "agent", "bundle"}

# Mapping for deprecated subcommands to their handlers
DEPRECATED_TYPE_HANDLERS = {
    "skill": (ResourceType.SKILL, "skills"),
    "command": (ResourceType.COMMAND, "commands"),
    "agent": (ResourceType.AGENT, "agents"),
}


def extract_options_from_args(
    args: list[str] | None,
    explicit_type: str | None,
    explicit_to: str | None,
    explicit_workspace: str | None = None,
) -> tuple[list[str], str | None, str | None, str | None]:
    """Extract --type/-t, --to, and --workspace/-w options from args list if present.

    When options appear after the resource reference, Typer captures them
    as part of the variadic args list. This function extracts them.
    """
    if not args:
        return [], explicit_type, explicit_to, explicit_workspace

    cleaned_args = []
    resource_type = explicit_type
    to_package = explicit_to
    workspace = explicit_workspace

    i = 0
    while i < len(args):
        arg = args[i]
        has_next = i + 1 < len(args)

        if arg in ("--type", "-t") and has_next and resource_type is None:
            resource_type = args[i + 1]
            i += 2
        elif arg == "--to" and has_next and to_package is None:
            to_package = args[i + 1]
            i += 2
        elif arg in ("--workspace", "-w") and has_next and workspace is None:
            workspace = args[i + 1]
            i += 2
        else:
            cleaned_args.append(arg)
            i += 1

    return cleaned_args, resource_type, to_package, workspace



def _is_glob_pattern(ref: str) -> bool:
    """Check if a reference contains glob patterns."""
    return "*" in ref or "?" in ref or "[" in ref


TYPE_DIRECTORY_TO_TYPE: dict[str, str] = {
    "commands": "command",
    "agents": "agent",
    "rules": "rule",
}


def detect_resource_type_from_ancestors(file_path: Path) -> str | None:
    """Detect resource type by finding type directory in file's ancestors.

    Walks up the directory tree looking for type directories (commands/, agents/,
    rules/). The first type directory found determines the resource type.

    Note: Skills are detected by SKILL.md marker, not parent directories.
    """
    for parent in file_path.resolve().parents:
        if parent.name in TYPE_DIRECTORY_TO_TYPE:
            return TYPE_DIRECTORY_TO_TYPE[parent.name]
    return None


def _detect_local_type(path: Path) -> str | None:
    """Detect resource type from a local path using explicit markers.

    Returns "skill", "command", "agent", "rule", "package", or None if unknown.

    Detection rules:
    - Directory with PACKAGE.md -> package (highest priority)
    - Directory with SKILL.md -> skill
    - File with .md extension -> detect from ancestor directories (commands/, agents/, rules/)

    Directories without explicit markers return None and route to
    handle_add_directory() for individual resource discovery.
    """
    if path.is_file():
        if path.suffix != ".md":
            return None
        # Use ancestor-based detection instead of defaulting to command
        return detect_resource_type_from_ancestors(path)

    if not path.is_dir():
        return None

    if (path / "PACKAGE.md").exists():
        return "package"

    if (path / "SKILL.md").exists():
        return "skill"

    return None


def _explode_package(
    package_path: Path,
    username: str,
    package_name: str,
    base_path: Path,
) -> dict[str, int]:
    """Install package contents to .claude/<type>/<flattened_name>.

    "Explodes" a package by installing its contents to the appropriate
    type directories with flattened colon-namespaced directory names
    for Claude Code discoverability.

    Args:
        package_path: Path to the package directory
        username: Username for namespacing
        package_name: Name of the package (may be overridden by PACKAGE.md)
        base_path: Base .claude/ path

    Returns:
        Dict with counts of installed resources by type
    """
    # Check for PACKAGE.md and use its name if present
    package_md = package_path / "PACKAGE.md"
    if package_md.exists():
        metadata = parse_package_md(package_md)
        if metadata.valid and metadata.name:
            package_name = metadata.name

    counts = {"skills": 0, "commands": 0, "agents": 0}

    # Skills - use flattened names with recursive discovery for nested skills
    skills_dir = package_path / "skills"
    if skills_dir.is_dir():
        for skill_md in skills_dir.rglob("SKILL.md"):
            skill_dir = skill_md.parent
            # Compute path segments relative to package skills dir
            rel_parts = list(skill_dir.relative_to(skills_dir).parts)
            flattened_name = compute_flattened_resource_name(username, rel_parts, package_name)
            dest = base_path / "skills" / flattened_name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(skill_dir, dest)
            update_skill_md_name(dest, flattened_name)
            counts["skills"] += 1

    # Commands and agents - use rglob and preserve nested paths
    for type_name, type_dir in [("commands", "commands"), ("agents", "agents")]:
        source_dir = package_path / type_dir
        if not source_dir.is_dir():
            continue
        for md_file in source_dir.rglob("*.md"):
            rel_parts = list(md_file.parent.relative_to(source_dir).parts)
            if rel_parts and rel_parts != ["."]:
                dest = base_path / type_dir / username / package_name / Path(*rel_parts) / md_file.name
            else:
                dest = base_path / type_dir / username / package_name / md_file.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(md_file, dest)
            counts[type_name] += 1

    return counts


def _install_local_resource(
    source_path: Path,
    resource_type: str,
    username: str,
    base_path: Path,
    package_context: tuple[str | None, Path | None] = (None, None),
) -> str:
    """Install a local resource to .claude/ directory.

    Args:
        source_path: Path to the source resource
        resource_type: Type of resource (skill, command, agent, package)
        username: Username for namespacing
        base_path: Base .claude/ path
        package_context: Optional tuple of (package_name, package_root) for
                         resources inside a package

    Returns:
        The installed resource name (flattened for skills)
    """
    # Handle package explosion
    if resource_type == "package":
        counts = _explode_package(source_path, username, source_path.name, base_path)
        return source_path.name  # Package is exploded to type directories

    subdir = TYPE_TO_SUBDIR.get(resource_type, "skills")
    package_name, package_root = package_context

    if resource_type == "skill":
        # Skills use flattened colon-namespaced directory names
        path_segments = compute_path_segments(source_path)
        flattened_name = compute_flattened_resource_name(username, path_segments, package_name)
        dest_path = base_path / subdir / flattened_name
        name = flattened_name
    else:
        # Commands and agents are files - include nested path structure
        path_segments = compute_path_segments(source_path)
        name = source_path.stem
        if package_name:
            all_segments = [package_name] + path_segments
        else:
            all_segments = path_segments
        nested_dirs = all_segments[:-1]
        if nested_dirs:
            dest_path = base_path / subdir / username / Path(*nested_dirs) / f"{name}.md"
        else:
            dest_path = base_path / subdir / username / f"{name}.md"

    # Remove existing if present
    if dest_path.exists():
        if dest_path.is_dir():
            shutil.rmtree(dest_path)
        else:
            dest_path.unlink()

    # Create parent directories
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Copy resource
    if source_path.is_dir():
        shutil.copytree(source_path, dest_path)
        # Update SKILL.md name field for skills
        if resource_type == "skill":
            update_skill_md_name(dest_path, flattened_name)
    else:
        shutil.copy2(source_path, dest_path)

    return name


def _validate_package(pkg_path: Path) -> None:
    """Validate a package directory before installation.

    Checks:
    - PACKAGE.md is valid if present
    - No nested PACKAGE.md files exist
    - Package contains at least one resource

    Args:
        pkg_path: Path to the package directory

    Raises:
        SystemExit: If validation fails
    """
    package_md = pkg_path / "PACKAGE.md"
    if package_md.exists():
        metadata = parse_package_md(package_md)
        if not metadata.valid:
            error_exit(f"Invalid PACKAGE.md: {metadata.error}")

        nested = validate_no_nested_packages(pkg_path)
        if nested:
            nested_paths = ", ".join(str(p.relative_to(pkg_path)) for p in nested)
            error_exit(
                f"Found nested PACKAGE.md files in package '{pkg_path.name}':\n"
                f"  {nested_paths}\n"
                "Packages cannot contain other packages."
            )

    # Check package has at least one resource
    has_skills = (pkg_path / "skills").is_dir() and any((pkg_path / "skills").rglob("SKILL.md"))
    has_commands = (pkg_path / "commands").is_dir() and any((pkg_path / "commands").glob("*.md"))
    has_agents = (pkg_path / "agents").is_dir() and any((pkg_path / "agents").glob("*.md"))

    if not (has_skills or has_commands or has_agents):
        error_exit(
            f"Package '{pkg_path.name}' contains no resources.\n"
            "Add skills, commands, or agents to the package first."
        )


def handle_add_local(
    local_path: str,
    resource_type: str | None,
    global_install: bool = False,
    workspace: str | None = None,
) -> None:
    """Handle adding a local resource to agr.toml and installing to .claude/."""
    path = Path(local_path)

    if not path.exists():
        error_exit(f"Path does not exist: {path}")

    # Detect type if not explicitly provided
    if not resource_type:
        resource_type = _detect_local_type(path)

    # Directory without markers containing discoverable resources routes to discovery
    if resource_type is None and path.is_dir():
        has_resources = any(path.rglob("SKILL.md")) or any(path.glob("*.md"))
        if has_resources:
            handle_add_directory(path, None, global_install, workspace)
            return

    if not resource_type:
        if path.is_file() and path.suffix == ".md":
            error_exit(
                f"Cannot determine resource type for {path.name}\n"
                "The file is not under a commands/, agents/, or rules/ directory.\n"
                f"Use --type to specify: agr add {local_path} --type <command|agent|rule>"
            )
        error_exit(
            f"Could not detect resource type for '{path}'.\n"
            "Use --type to specify: skill, command, agent, rule, or package"
        )

    # Validate packages
    if resource_type == "package":
        _validate_package(path)

    name = path.stem if path.is_file() else path.name

    # Get username for namespacing
    repo_root = find_repo_root()
    username = get_username_from_git_remote(repo_root)
    if not username:
        username = "local"

    # Add to agr.toml (to workspace if specified, else to main dependencies)
    config_path, config = get_or_create_config()
    dep = Dependency(path=local_path, type=resource_type)
    if workspace:
        config.add_to_workspace(workspace, dep)
    else:
        config.add_local(local_path, resource_type)
    config.save(config_path)

    # Install to .claude/
    base_path = get_base_path(global_install)
    installed_name = _install_local_resource(path, resource_type, username, base_path)

    console.print(f"[green]Added local {resource_type} '{name}'[/green]")
    console.print(f"  path: {local_path}")
    if workspace:
        console.print(f"  workspace: {workspace}")
    # Skills use flattened names, commands/agents use nested paths
    if resource_type == "skill":
        console.print(f"  installed to: .claude/{resource_type}s/{installed_name}")
    else:
        console.print(f"  installed to: .claude/{resource_type}s/{username}/{name}")


def handle_add_directory(
    dir_path: Path,
    resource_type: str | None,
    global_install: bool = False,
    workspace: str | None = None,
) -> None:
    """Add all resources in a directory recursively.

    Discovers:
    - Skills: All directories containing SKILL.md at any depth
    - Commands/Agents: All .md files at any depth (excluding those inside skill dirs)

    Args:
        dir_path: Path to the directory containing resources
        resource_type: Optional explicit resource type
        global_install: If True, install to ~/.claude/
        workspace: Optional workspace package name
    """
    config_path, config = get_or_create_config()
    base_path = get_base_path(global_install)
    username = get_username_from_git_remote(find_repo_root()) or "local"

    # Check if directory is inside a package
    package_context = find_package_context(dir_path)

    added_count = 0

    # Find all skill directories (containing SKILL.md) recursively
    for skill_md in dir_path.rglob("SKILL.md"):
        skill_dir = skill_md.parent
        try:
            rel_path = f"./{skill_dir.relative_to(Path.cwd())}"
        except ValueError:
            rel_path = str(skill_dir)
        dep = Dependency(path=rel_path, type="skill")
        if workspace:
            config.add_to_workspace(workspace, dep)
        else:
            config.add_local(rel_path, "skill")
        installed_name = _install_local_resource(skill_dir, "skill", username, base_path, package_context)
        console.print(f"[green]Added skill '{installed_name}'[/green]")
        added_count += 1

    # Collect all skill directories to exclude their .md files
    skill_dirs = {skill_md.parent for skill_md in dir_path.rglob("SKILL.md")}

    # Find all .md files recursively, excluding those inside skill directories
    for md_file in dir_path.rglob("*.md"):
        # Skip SKILL.md files (already handled above)
        if md_file.name == "SKILL.md":
            continue
        # Skip if inside a skill directory (these are reference files, not resources)
        if any(skill_dir in md_file.parents or skill_dir == md_file.parent for skill_dir in skill_dirs):
            continue

        detected_type = resource_type or _detect_local_type(md_file)
        if detected_type:
            try:
                rel_path = f"./{md_file.relative_to(Path.cwd())}"
            except ValueError:
                rel_path = str(md_file)
            dep = Dependency(path=rel_path, type=detected_type)
            if workspace:
                config.add_to_workspace(workspace, dep)
            else:
                config.add_local(rel_path, detected_type)
            _install_local_resource(md_file, detected_type, username, base_path, package_context)
            console.print(f"[green]Added {detected_type} '{md_file.stem}'[/green]")
            added_count += 1

    config.save(config_path)
    console.print(f"\n[dim]Added {added_count} resource(s)[/dim]")


def handle_add_glob(
    pattern: str,
    resource_type: str | None,
    global_install: bool = False,
) -> None:
    """Handle adding multiple local resources via glob pattern.

    Args:
        pattern: Glob pattern like "./commands/*.md"
        resource_type: Optional explicit resource type
        global_install: If True, install to ~/.claude/
    """
    # Expand glob pattern
    matches = list(glob.glob(pattern, recursive=True))

    if not matches:
        error_exit(f"No files match pattern: {pattern}")

    # Filter to only existing files/dirs
    paths = [Path(m) for m in matches if Path(m).exists()]

    if not paths:
        error_exit(f"No valid paths match pattern: {pattern}")

    console.print(f"Found {len(paths)} matching path(s)")

    # Get username for namespacing
    repo_root = find_repo_root()
    username = get_username_from_git_remote(repo_root)
    if not username:
        username = "local"

    config_path, config = get_or_create_config()
    base_path = get_base_path(global_install)

    added_count = 0
    for path in paths:
        # Detect or use explicit type
        detected_type = resource_type or _detect_local_type(path)
        if not detected_type:
            console.print(f"[yellow]Skipping '{path}': Could not detect type[/yellow]")
            continue

        # Make path relative for storage
        try:
            rel_path = path.relative_to(Path.cwd())
            path_str = f"./{rel_path}"
        except ValueError:
            path_str = str(path)

        # Add to config
        config.add_local(path_str, detected_type)

        # Install to .claude/
        installed_name = _install_local_resource(path, detected_type, username, base_path)

        # Use flattened name for skills, original name for others
        display_name = installed_name if detected_type == "skill" else (path.stem if path.is_file() else path.name)
        console.print(f"[green]Added {detected_type} '{display_name}'[/green]")
        added_count += 1

    # Save config
    config.save(config_path)

    console.print(f"\n[dim]Added {added_count} resource(s) to agr.toml[/dim]")


app = typer.Typer(
    help="Add skills, commands, or agents from GitHub.",
)


@app.callback(invoke_without_command=True)
def add_unified(
    ctx: typer.Context,
    args: Annotated[
        Optional[List[str]],
        typer.Argument(help="Resource reference and optional arguments"),
    ] = None,
    resource_type: Annotated[
        Optional[str],
        typer.Option(
            "--type",
            "-t",
            help="Explicit resource type: skill, command, agent, package, or bundle",
        ),
    ] = None,
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite existing resource if it exists.",
        ),
    ] = False,
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Install to ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
    workspace: Annotated[
        Optional[str],
        typer.Option(
            "--workspace",
            "-w",
            help="Add to workspace package (groups dependencies together)",
        ),
    ] = None,
    to_package: Annotated[
        Optional[str],
        typer.Option(
            "--to",
            help="(Deprecated) Add local resource to a package namespace",
        ),
    ] = None,
) -> None:
    """Add a resource from a GitHub repository or local path.

    REFERENCE format:
      - username/name: installs from github.com/username/agent-resources
      - username/repo/name: installs from github.com/username/repo
      - ./path/to/resource: adds local path and installs to .claude/
      - ./path/*.md: glob pattern to add multiple resources

    Auto-detects the resource type (skill, command, agent, package, or bundle).
    Use --type to explicitly specify when needed.

    Examples:
      agr add kasperjunge/hello-world
      agr add kasperjunge/my-repo/hello-world --type skill
      agr add kasperjunge/productivity --global
      agr add ./skills/my-skill
      agr add ./commands/deploy.md
      agr add ./commands/*.md
      agr add ./packages/my-toolkit --type package
    """
    # Extract --type/-t, --to, and --workspace/-w from args if captured there (happens when options come after ref)
    cleaned_args, resource_type, to_package, workspace = extract_options_from_args(args, resource_type, to_package, workspace)

    if not cleaned_args:
        console.print(ctx.get_help())
        raise typer.Exit(0)

    # Check for multiple local paths (shell-expanded glob)
    local_paths = [arg for arg in cleaned_args if is_local_path(arg)]
    if len(local_paths) > 1:
        # Shell expanded a glob pattern, process all local paths
        for local_path in local_paths:
            handle_add_local(local_path, resource_type, global_install, workspace)
        return

    first_arg = cleaned_args[0]

    # Handle glob patterns
    if is_local_path(first_arg) and _is_glob_pattern(first_arg):
        handle_add_glob(first_arg, resource_type, global_install)
        return

    # Handle local paths
    if is_local_path(first_arg):
        handle_add_local(first_arg, resource_type, global_install, workspace)
        return

    # Handle deprecated subcommand syntax: agr add skill <ref>
    if first_arg in DEPRECATED_SUBCOMMANDS:
        _handle_deprecated_add(first_arg, cleaned_args, overwrite, global_install)
        return

    # Normal unified add: agr add <ref>
    handle_add_unified(first_arg, resource_type, overwrite, global_install)


def _handle_deprecated_add(
    subcommand: str,
    args: list[str],
    overwrite: bool,
    global_install: bool,
) -> None:
    """Handle deprecated agr add <type> <ref> syntax."""
    if len(args) < 2:
        error_exit(f"Missing resource reference after '{subcommand}'.")

    resource_ref = args[1]
    console.print(
        f"[yellow]Warning: 'agr add {subcommand}' is deprecated. "
        f"Use 'agr add {resource_ref}' instead.[/yellow]"
    )

    if subcommand == "bundle":
        handle_add_bundle(resource_ref, overwrite, global_install)
        return

    res_type, subdir = DEPRECATED_TYPE_HANDLERS[subcommand]
    handle_add_resource(resource_ref, res_type, subdir, overwrite, global_install)
