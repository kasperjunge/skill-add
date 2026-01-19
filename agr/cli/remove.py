"""Remove subcommand for agr - delete local resources."""

import shutil
from pathlib import Path
from typing import Annotated, List, Optional

import typer

from agr.cli.common import (
    TYPE_TO_SUBDIR,
    console,
    error_exit,
    extract_type_from_args,
    find_repo_root,
    get_base_path,
    handle_remove_bundle,
    handle_remove_resource,
    handle_remove_unified,
    is_local_path,
)
from agr.config import find_config, AgrConfig
from agr.fetcher import ResourceType
from agr.github import get_username_from_git_remote

# Deprecated subcommand names
DEPRECATED_SUBCOMMANDS = {"skill", "command", "agent", "bundle"}




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
        error_exit("No agr.toml found")

    config = AgrConfig.load(config_path)

    # Check if path is in config
    dep = config.get_by_path(local_path)
    if not dep:
        error_exit(f"Path '{local_path}' not found in agr.toml")

    # Get username for finding installed resource
    repo_root = find_repo_root()
    username = get_username_from_git_remote(repo_root)
    if not username:
        username = "local"

    # Determine installed path
    source_path = Path(local_path)
    name = source_path.stem if source_path.is_file() else source_path.name

    subdir = TYPE_TO_SUBDIR.get(dep.type, "skills")

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
    if is_local_path(first_arg):
        handle_remove_local(first_arg, global_install)
        return

    # Handle deprecated subcommand syntax: agr remove skill <name>
    if first_arg in DEPRECATED_SUBCOMMANDS:
        if len(cleaned_args) < 2:
            error_exit(f"Missing resource name after '{first_arg}'.")

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
