"""Remove subcommand for agr - delete local resources."""

from typing import Annotated, List, Optional

import typer
from rich.console import Console

from agr.cli.common import handle_remove_bundle, handle_remove_resource, handle_remove_unified
from agr.fetcher import ResourceType

console = Console()

# Deprecated subcommand names
DEPRECATED_SUBCOMMANDS = {"skill", "command", "agent", "bundle"}

app = typer.Typer(
    help="Remove skills, commands, or agents.",
)


@app.callback(invoke_without_command=True)
def remove_unified(
    ctx: typer.Context,
    args: Annotated[
        Optional[List[str]],
        typer.Argument(help="Name of the resource to remove"),
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

    Examples:
      agr remove hello-world
      agr remove hello-world --type skill
      agr remove hello-world --global
    """
    if not args:
        console.print(ctx.get_help())
        raise typer.Exit(0)

    first_arg = args[0]

    # Handle deprecated subcommand syntax: agr remove skill <name>
    if first_arg in DEPRECATED_SUBCOMMANDS:
        if len(args) < 2:
            console.print(f"[red]Error: Missing resource name after '{first_arg}'.[/red]")
            raise typer.Exit(1)

        name = args[1]
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
