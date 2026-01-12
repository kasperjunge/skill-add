"""Update subcommand for agr - re-fetch resources from GitHub."""

from typing import Annotated

import typer

from agr.cli.common import handle_update_resource
from agr.fetcher import ResourceType

app = typer.Typer(
    help="Update skills, commands, or agents from GitHub.",
    no_args_is_help=True,
)


@app.command("skill")
def update_skill(
    skill_ref: Annotated[
        str,
        typer.Argument(
            help="Skill reference: <username>/<skill-name> or <username>/<repo>/<skill-name>",
            metavar="REFERENCE",
        ),
    ],
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Update in ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
) -> None:
    """Update a skill by re-fetching from GitHub.

    REFERENCE format:
      - username/skill-name: re-fetches from github.com/username/agent-resources
      - username/repo/skill-name: re-fetches from github.com/username/repo

    Examples:
      agr update skill kasperjunge/hello-world
      agr update skill kasperjunge/my-repo/hello-world --global
    """
    handle_update_resource(skill_ref, ResourceType.SKILL, "skills", global_install)


@app.command("command")
def update_command(
    command_ref: Annotated[
        str,
        typer.Argument(
            help="Command reference: <username>/<command-name> or <username>/<repo>/<command-name>",
            metavar="REFERENCE",
        ),
    ],
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Update in ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
) -> None:
    """Update a slash command by re-fetching from GitHub.

    REFERENCE format:
      - username/command-name: re-fetches from github.com/username/agent-resources
      - username/repo/command-name: re-fetches from github.com/username/repo

    Examples:
      agr update command kasperjunge/hello
      agr update command kasperjunge/my-repo/hello-world --global
    """
    handle_update_resource(command_ref, ResourceType.COMMAND, "commands", global_install)


@app.command("agent")
def update_agent(
    agent_ref: Annotated[
        str,
        typer.Argument(
            help="Agent reference: <username>/<agent-name> or <username>/<repo>/<agent-name>",
            metavar="REFERENCE",
        ),
    ],
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Update in ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
) -> None:
    """Update a sub-agent by re-fetching from GitHub.

    REFERENCE format:
      - username/agent-name: re-fetches from github.com/username/agent-resources
      - username/repo/agent-name: re-fetches from github.com/username/repo

    Examples:
      agr update agent kasperjunge/hello-agent
      agr update agent kasperjunge/my-repo/hello-agent --global
    """
    handle_update_resource(agent_ref, ResourceType.AGENT, "agents", global_install)
