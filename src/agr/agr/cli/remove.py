"""Remove subcommand for agr - delete local resources."""

from typing import Annotated

import typer

from agr.cli.common import handle_remove_bundle, handle_remove_resource
from agr.tools import ResourceType
from agr.tools.registry import get_tool_adapter

app = typer.Typer(
    help="Remove skills, commands, or agents.",
    no_args_is_help=True,
)


@app.command("skill")
def remove_skill(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the skill to remove",
            metavar="NAME",
        ),
    ],
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Remove from ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
    tool_name: Annotated[
        str | None,
        typer.Option(
            "--tool",
            "-t",
            help="Target tool (e.g., 'claude'). Defaults to auto-detect.",
        ),
    ] = None,
) -> None:
    """Remove a skill from the local installation.

    Removes the skill directory immediately without confirmation.

    Examples:
      agr remove skill hello-world
      agr remove skill hello-world --global
      agr remove skill hello-world --tool claude
    """
    tool = get_tool_adapter(tool_name) if tool_name else None
    handle_remove_resource(name, ResourceType.SKILL, global_install, tool)


@app.command("command")
def remove_command(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the command to remove",
            metavar="NAME",
        ),
    ],
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Remove from ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
    tool_name: Annotated[
        str | None,
        typer.Option(
            "--tool",
            "-t",
            help="Target tool (e.g., 'claude'). Defaults to auto-detect.",
        ),
    ] = None,
) -> None:
    """Remove a slash command from the local installation.

    Removes the command file immediately without confirmation.

    Examples:
      agr remove command hello
      agr remove command hello --global
      agr remove command hello --tool claude
    """
    tool = get_tool_adapter(tool_name) if tool_name else None
    handle_remove_resource(name, ResourceType.COMMAND, global_install, tool)


@app.command("agent")
def remove_agent(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the agent to remove",
            metavar="NAME",
        ),
    ],
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Remove from ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
    tool_name: Annotated[
        str | None,
        typer.Option(
            "--tool",
            "-t",
            help="Target tool (e.g., 'claude'). Defaults to auto-detect.",
        ),
    ] = None,
) -> None:
    """Remove a sub-agent from the local installation.

    Removes the agent file immediately without confirmation.

    Examples:
      agr remove agent hello-agent
      agr remove agent hello-agent --global
      agr remove agent hello-agent --tool claude
    """
    tool = get_tool_adapter(tool_name) if tool_name else None
    handle_remove_resource(name, ResourceType.AGENT, global_install, tool)


@app.command("bundle")
def remove_bundle(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the bundle to remove",
            metavar="NAME",
        ),
    ],
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Remove from ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
) -> None:
    """Remove all resources from a bundle.

    Removes the bundle directory for skills, commands, and agents.

    Examples:
      agr remove bundle productivity
      agr remove bundle productivity --global
    """
    handle_remove_bundle(name, global_install)
