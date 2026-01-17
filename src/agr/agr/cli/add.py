"""Add subcommand for agr - install resources from GitHub."""

from typing import Annotated, List, Optional

import typer
from rich.console import Console

from agr.cli.common import handle_add_bundle, handle_add_resource, handle_add_unified
from agr.fetcher import ResourceType

console = Console()

# Deprecated subcommand names
DEPRECATED_SUBCOMMANDS = {"skill", "command", "agent", "bundle"}

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
            help="Explicit resource type: skill, command, agent, or bundle",
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
) -> None:
    """Add a resource from a GitHub repository with auto-detection.

    REFERENCE format:
      - username/name: installs from github.com/username/agent-resources
      - username/repo/name: installs from github.com/username/repo

    Auto-detects the resource type (skill, command, agent, or bundle).
    Use --type to explicitly specify when a name exists in multiple types.

    Examples:
      agr add kasperjunge/hello-world
      agr add kasperjunge/my-repo/hello-world --type skill
      agr add kasperjunge/productivity --global
    """
    if not args:
        console.print(ctx.get_help())
        raise typer.Exit(0)

    first_arg = args[0]

    # Handle deprecated subcommand syntax: agr add skill <ref>
    if first_arg in DEPRECATED_SUBCOMMANDS:
        if len(args) < 2:
            console.print(f"[red]Error: Missing resource reference after '{first_arg}'.[/red]")
            raise typer.Exit(1)

        resource_ref = args[1]
        console.print(
            f"[yellow]Warning: 'agr add {first_arg}' is deprecated. "
            f"Use 'agr add {resource_ref}' instead.[/yellow]"
        )

        if first_arg == "skill":
            handle_add_resource(resource_ref, ResourceType.SKILL, "skills", overwrite, global_install)
        elif first_arg == "command":
            handle_add_resource(resource_ref, ResourceType.COMMAND, "commands", overwrite, global_install)
        elif first_arg == "agent":
            handle_add_resource(resource_ref, ResourceType.AGENT, "agents", overwrite, global_install)
        elif first_arg == "bundle":
            handle_add_bundle(resource_ref, overwrite, global_install)
        return

    # Normal unified add: agr add <ref>
    resource_ref = first_arg
    handle_add_unified(resource_ref, resource_type, overwrite, global_install)
