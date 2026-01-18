"""Add subcommand for agr - install resources from GitHub."""

import glob
import shutil
from pathlib import Path
from typing import Annotated, List, Optional

import typer
from rich.console import Console

from agr.cli.common import handle_add_bundle, handle_add_resource, handle_add_unified, get_base_path
from agr.config import Dependency, get_or_create_config
from agr.fetcher import ResourceType
from agr.github import get_username_from_git_remote

console = Console()

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

def _is_local_path(ref: str) -> bool:
    """Check if a reference is a local path."""
    return ref.startswith(("./", "/", "../"))


def _is_glob_pattern(ref: str) -> bool:
    """Check if a reference contains glob patterns."""
    return "*" in ref or "?" in ref or "[" in ref


def _detect_local_type(path: Path) -> str | None:
    """Detect resource type from a local path.

    Returns "skill", "command", "agent", "package", "namespace", or None if unknown.
    Auto-detects based on:
    - Directory with SKILL.md -> skill
    - File with .md extension -> command (or agent if in agents/ dir)
    - Directory in packages/ -> package
    - Directory with skills/, commands/, or agents/ subdirs -> package
    - Directory containing only skill subdirectories -> namespace
    """
    path_str = str(path)

    # Check if in packages/ directory
    if "packages/" in path_str or path_str.startswith("packages"):
        if path.is_dir():
            # Check if it's a package directory (has subdirs for resources)
            has_subdirs = any(
                (path / d).is_dir() for d in ["skills", "commands", "agents"]
            )
            if has_subdirs:
                return "package"
            # Might be a skill inside a package
            if (path / "SKILL.md").exists():
                return "skill"
        return "package"

    # Check for skill directory
    if path.is_dir() and (path / "SKILL.md").exists():
        return "skill"

    # Check for command/agent file
    if path.is_file() and path.suffix == ".md":
        # Detect agent vs command from parent directory name
        if path.parent.name == "agents" or "agents/" in path_str:
            return "agent"
        return "command"

    # Check for package directory
    if path.is_dir():
        has_subdirs = any(
            (path / d).is_dir() for d in ["skills", "commands", "agents"]
        )
        if has_subdirs:
            return "package"

        # Check for namespace containing skills (recursively, not just direct children)
        # A namespace is a directory that contains skill directories at any depth
        has_nested_skills = any(path.rglob("SKILL.md"))
        if has_nested_skills:
            return "namespace"

    return None


def handle_add_namespace(
    namespace_path: Path,
    global_install: bool,
    workspace: str | None = None,
) -> None:
    """Add all skills from a namespace directory recursively.

    A namespace is a directory containing multiple skill subdirectories.
    Skills are discovered recursively and installed to .claude/skills/<user>/<namespace>/<relative-path>/

    Args:
        namespace_path: Path to the namespace directory
        global_install: If True, install to ~/.claude/
        workspace: Optional workspace package name
    """
    config_path, config = get_or_create_config()
    base_path = get_base_path(global_install)
    username = get_username_from_git_remote(_find_repo_root()) or "local"
    namespace_name = namespace_path.name

    added_count = 0

    # Find all skill directories recursively (containing SKILL.md)
    for skill_md in namespace_path.rglob("SKILL.md"):
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

        # Compute relative path from namespace root
        # e.g., if namespace_path is "./skills" and skill_dir is "./skills/product/flywheel"
        # then rel_to_namespace is "product/flywheel"
        rel_to_namespace = skill_dir.relative_to(namespace_path)

        # Install to .claude/skills/<user>/<namespace>/<relative-path>/
        dest_path = base_path / "skills" / username / namespace_name / rel_to_namespace
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        if dest_path.exists():
            shutil.rmtree(dest_path)
        shutil.copytree(skill_dir, dest_path)

        console.print(f"[green]Added skill '{namespace_name}/{rel_to_namespace}'[/green]")
        added_count += 1

    config.save(config_path)
    console.print(f"\n[dim]Added {added_count} resource(s)[/dim]")


def _find_repo_root() -> Path:
    """Find the repository root by looking for .git directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def _explode_package(
    package_path: Path,
    username: str,
    package_name: str,
    base_path: Path,
) -> dict[str, int]:
    """Install package contents to .claude/<type>/<user>/<pkg>/<resource>.

    "Explodes" a package by installing its contents to the appropriate
    type directories instead of keeping them bundled.

    Args:
        package_path: Path to the package directory
        username: Username for namespacing
        package_name: Name of the package
        base_path: Base .claude/ path

    Returns:
        Dict with counts of installed resources by type
    """
    counts = {"skills": 0, "commands": 0, "agents": 0}

    # Skills
    skills_dir = package_path / "skills"
    if skills_dir.is_dir():
        for skill in skills_dir.iterdir():
            if skill.is_dir() and (skill / "SKILL.md").exists():
                dest = base_path / "skills" / username / package_name / skill.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(skill, dest)
                counts["skills"] += 1

    # Commands
    cmds_dir = package_path / "commands"
    if cmds_dir.is_dir():
        for cmd in cmds_dir.glob("*.md"):
            dest = base_path / "commands" / username / package_name / cmd.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cmd, dest)
            counts["commands"] += 1

    # Agents
    agents_dir = package_path / "agents"
    if agents_dir.is_dir():
        for agent in agents_dir.glob("*.md"):
            dest = base_path / "agents" / username / package_name / agent.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(agent, dest)
            counts["agents"] += 1

    return counts


def _install_local_resource(
    source_path: Path,
    resource_type: str,
    username: str,
    base_path: Path,
) -> None:
    """Install a local resource to .claude/ directory.

    Args:
        source_path: Path to the source resource
        resource_type: Type of resource (skill, command, agent, package)
        username: Username for namespacing
        base_path: Base .claude/ path
    """
    # Handle package explosion
    if resource_type == "package":
        counts = _explode_package(source_path, username, source_path.name, base_path)
        return  # Package is exploded to type directories

    type_to_subdir = {
        "skill": "skills",
        "command": "commands",
        "agent": "agents",
    }
    subdir = type_to_subdir.get(resource_type, "skills")

    if resource_type == "skill":
        # Skills are directories
        name = source_path.name
        dest_path = base_path / subdir / username / name
    else:
        # Commands and agents are files
        name = source_path.stem
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
    else:
        shutil.copy2(source_path, dest_path)


def handle_add_local(
    local_path: str,
    resource_type: str | None,
    global_install: bool = False,
    workspace: str | None = None,
) -> None:
    """Handle adding a local resource to agr.toml and installing to .claude/."""
    path = Path(local_path)

    if not path.exists():
        console.print(f"[red]Error: Path does not exist: {path}[/red]")
        raise typer.Exit(1)

    # Detect type first to handle namespaces properly
    if not resource_type:
        resource_type = _detect_local_type(path)

    # Handle namespace (directory of skill directories) before generic directory check
    if resource_type == "namespace":
        handle_add_namespace(path, global_install, workspace)
        return

    # Check if it's a directory of resources (not a skill itself, not a namespace)
    if path.is_dir() and not (path / "SKILL.md").exists() and resource_type not in ("package", "namespace"):
        has_skills = any((d / "SKILL.md").exists() for d in path.iterdir() if d.is_dir())
        has_md = any(path.glob("*.md"))
        if has_skills or has_md:
            handle_add_directory(path, resource_type, global_install, workspace)
            return

    if not resource_type:
        console.print(
            f"[red]Error: Could not detect resource type for '{path}'.[/red]\n"
            "Use --type to specify: skill, command, agent, or package"
        )
        raise typer.Exit(1)

    # Validate that packages are not empty
    if resource_type == "package":
        pkg_path = path
        has_resources = any([
            any((pkg_path / "skills").glob("*/SKILL.md")) if (pkg_path / "skills").is_dir() else False,
            any((pkg_path / "commands").glob("*.md")) if (pkg_path / "commands").is_dir() else False,
            any((pkg_path / "agents").glob("*.md")) if (pkg_path / "agents").is_dir() else False,
        ])
        if not has_resources:
            console.print(f"[red]Error: Package '{pkg_path.name}' contains no resources.[/red]")
            console.print("[dim]Add skills, commands, or agents to the package first.[/dim]")
            raise typer.Exit(1)

    name = path.stem if path.is_file() else path.name

    # Get username for namespacing
    repo_root = _find_repo_root()
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
    _install_local_resource(path, resource_type, username, base_path)

    console.print(f"[green]Added local {resource_type} '{name}'[/green]")
    console.print(f"  path: {local_path}")
    if workspace:
        console.print(f"  workspace: {workspace}")
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
    username = get_username_from_git_remote(_find_repo_root()) or "local"

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
        _install_local_resource(skill_dir, "skill", username, base_path)
        console.print(f"[green]Added skill '{skill_dir.name}'[/green]")
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
            _install_local_resource(md_file, detected_type, username, base_path)
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
        console.print(f"[red]Error: No files match pattern: {pattern}[/red]")
        raise typer.Exit(1)

    # Filter to only existing files/dirs
    paths = [Path(m) for m in matches if Path(m).exists()]

    if not paths:
        console.print(f"[red]Error: No valid paths match pattern: {pattern}[/red]")
        raise typer.Exit(1)

    console.print(f"Found {len(paths)} matching path(s)")

    # Get username for namespacing
    repo_root = _find_repo_root()
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
        _install_local_resource(path, detected_type, username, base_path)

        name = path.stem if path.is_file() else path.name
        console.print(f"[green]Added {detected_type} '{name}'[/green]")
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
    local_paths = [arg for arg in cleaned_args if _is_local_path(arg)]
    if len(local_paths) > 1:
        # Shell expanded a glob pattern, process all local paths
        for local_path in local_paths:
            handle_add_local(local_path, resource_type, global_install, workspace)
        return

    first_arg = cleaned_args[0]

    # Handle glob patterns
    if _is_local_path(first_arg) and _is_glob_pattern(first_arg):
        handle_add_glob(first_arg, resource_type, global_install)
        return

    # Handle local paths
    if _is_local_path(first_arg):
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
        console.print(f"[red]Error: Missing resource reference after '{subcommand}'.[/red]")
        raise typer.Exit(1)

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
