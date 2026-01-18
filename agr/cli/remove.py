"""Remove subcommand for agr - delete local resources."""

import shutil
from pathlib import Path
from typing import Annotated, List, Optional

import typer
from rich.console import Console

from agr.cli.common import handle_remove_bundle, handle_remove_resource, handle_remove_unified, get_base_path
from agr.config import find_config, AgrConfig
from agr.fetcher import ResourceType
from agr.github import get_username_from_git_remote

console = Console()

# Deprecated subcommand names
DEPRECATED_SUBCOMMANDS = {"skill", "command", "agent", "bundle"}


def _is_local_path(ref: str) -> bool:
    """Check if a reference is a local path."""
    return ref.startswith(("./", "/", "../"))


def _find_repo_root() -> Path:
    """Find the repository root by looking for .git directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def handle_remove_local(
    local_path: str,
    global_install: bool = False,
) -> None:
    """Handle removing a local resource by path.

    Removes from both agr.toml and .claude/ directory.

    Args:
        local_path: The local path to remove (e.g., "./commands/docs.md")
        global_install: If True, remove from ~/.claude/
    """
    # Find and load config
    config_path = find_config()
    if not config_path:
        console.print("[red]Error: No agr.toml found[/red]")
        raise typer.Exit(1)

    config = AgrConfig.load(config_path)

    # Check if path is in config
    dep = config.get_by_path(local_path)
    if not dep:
        console.print(f"[red]Error: Path '{local_path}' not found in agr.toml[/red]")
        raise typer.Exit(1)

    # Get username for finding installed resource
    repo_root = _find_repo_root()
    username = get_username_from_git_remote(repo_root)
    if not username:
        username = "local"

    # Determine installed path
    source_path = Path(local_path)
    name = source_path.stem if source_path.is_file() else source_path.name

    type_to_subdir = {
        "skill": "skills",
        "command": "commands",
        "agent": "agents",
        "package": "packages",
    }
    subdir = type_to_subdir.get(dep.type, "skills")

    base_path = get_base_path(global_install)

    if dep.type in ("skill", "package"):
        installed_path = base_path / subdir / username / name
    else:
        installed_path = base_path / subdir / username / f"{name}.md"

    # Remove from .claude/
    if installed_path.exists():
        if installed_path.is_dir():
            shutil.rmtree(installed_path)
        else:
            installed_path.unlink()
        console.print(f"[green]Removed from .claude/: {installed_path.relative_to(base_path)}[/green]")

        # Clean up empty parent directories
        parent = installed_path.parent
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()

    # Remove from config
    config.remove_by_path(local_path)
    config.save(config_path)

    console.print(f"[green]Removed '{local_path}' from agr.toml[/green]")


def extract_type_from_args(
    args: list[str] | None, explicit_type: str | None
) -> tuple[list[str], str | None]:
    """
    Extract --type/-t option from args list if present.

    When --type or -t appears after the resource name, Typer captures it
    as part of the variadic args list. This function extracts it.

    Args:
        args: The argument list (may contain --type/-t)
        explicit_type: The resource_type value from Typer (may be None if type was in args)

    Returns:
        Tuple of (cleaned_args, resource_type)
    """
    if not args or explicit_type is not None:
        return args or [], explicit_type

    cleaned_args = []
    resource_type = None
    i = 0
    while i < len(args):
        if args[i] in ("--type", "-t") and i + 1 < len(args):
            resource_type = args[i + 1]
            i += 2  # Skip both --type and its value
        else:
            cleaned_args.append(args[i])
            i += 1

    return cleaned_args, resource_type

app = typer.Typer(
    help="Remove skills, commands, or agents.",
)


@app.callback(invoke_without_command=True)
def remove_unified(
    ctx: typer.Context,
    args: Annotated[
        Optional[List[str]],
        typer.Argument(help="Name or path of the resource to remove"),
    ] = None,
    resource_type: Annotated[
        Optional[str],
        typer.Option(
            "--type",
            "-t",
            help="Explicit resource type: skill, command, agent, or bundle",
        ),
    ] = None,
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Remove from ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
) -> None:
    """Remove a resource from the local installation with auto-detection.

    Auto-detects the resource type (skill, command, agent) from local files.
    Use --type to explicitly specify when a name exists in multiple types.

    Supports both resource names and local paths:
      agr remove hello-world          # Remove by name
      agr remove ./commands/docs.md   # Remove by path

    Examples:
      agr remove hello-world
      agr remove hello-world --type skill
      agr remove hello-world --global
      agr remove ./commands/docs.md
    """
    # Extract --type/-t from args if it was captured there (happens when type comes after name)
    cleaned_args, resource_type = extract_type_from_args(args, resource_type)

    if not cleaned_args:
        console.print(ctx.get_help())
        raise typer.Exit(0)

    first_arg = cleaned_args[0]

    # Handle local paths
    if _is_local_path(first_arg):
        handle_remove_local(first_arg, global_install)
        return

    # Handle deprecated subcommand syntax: agr remove skill <name>
    if first_arg in DEPRECATED_SUBCOMMANDS:
        if len(cleaned_args) < 2:
            console.print(f"[red]Error: Missing resource name after '{first_arg}'.[/red]")
            raise typer.Exit(1)

        name = cleaned_args[1]
        if first_arg == "bundle":
            console.print(
                f"[yellow]Warning: 'agr remove bundle' is deprecated. "
                f"Use 'agr remove {name} --type bundle' instead.[/yellow]"
            )
            handle_remove_bundle(name, global_install)
        else:
            console.print(
                f"[yellow]Warning: 'agr remove {first_arg}' is deprecated. "
                f"Use 'agr remove {name}' instead.[/yellow]"
            )
            if first_arg == "skill":
                handle_remove_resource(name, ResourceType.SKILL, "skills", global_install)
            elif first_arg == "command":
                handle_remove_resource(name, ResourceType.COMMAND, "commands", global_install)
            elif first_arg == "agent":
                handle_remove_resource(name, ResourceType.AGENT, "agents", global_install)
        return

    # Normal unified remove: agr remove <name>
    name = first_arg
    handle_remove_unified(name, resource_type, global_install)
