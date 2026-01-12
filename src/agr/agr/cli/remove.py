"""Remove subcommand for agr - delete local resources."""

from typing import Annotated

import typer

from agr.cli.common import handle_remove_resource
from agr.fetcher import ResourceType

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
) -> None:
    """Remove a skill from the local installation.

    Removes the skill directory immediately without confirmation.

    Examples:
      agr remove skill hello-world
      agr remove skill hello-world --global
    """
    handle_remove_resource(name, ResourceType.SKILL, "skills", global_install)


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
) -> None:
    """Remove a slash command from the local installation.

    Removes the command file immediately without confirmation.

    Examples:
      agr remove command hello
      agr remove command hello --global
    """
    handle_remove_resource(name, ResourceType.COMMAND, "commands", global_install)


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
) -> None:
    """Remove a sub-agent from the local installation.

    Removes the agent file immediately without confirmation.

    Examples:
      agr remove agent hello-agent
      agr remove agent hello-agent --global
    """
    handle_remove_resource(name, ResourceType.AGENT, "agents", global_install)
