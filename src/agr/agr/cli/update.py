"""Update subcommand for agr - re-fetch resources from GitHub."""

from typing import Annotated

import typer

from agr.cli.common import handle_update_bundle, handle_update_resource
from agr.tools import ResourceType
from agr.tools.registry import get_tool_adapter

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
    tool_name: Annotated[
        str | None,
        typer.Option(
            "--tool",
            "-t",
            help="Target tool (e.g., 'claude'). Defaults to auto-detect.",
        ),
    ] = None,
) -> None:
    """Update a skill by re-fetching from GitHub.

    REFERENCE format:
      - username/skill-name: re-fetches from github.com/username/agent-resources
      - username/repo/skill-name: re-fetches from github.com/username/repo

    Examples:
      agr update skill kasperjunge/hello-world
      agr update skill kasperjunge/my-repo/hello-world --global
      agr update skill kasperjunge/hello-world --tool claude
    """
    tool = get_tool_adapter(tool_name) if tool_name else None
    handle_update_resource(skill_ref, ResourceType.SKILL, global_install, tool)


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
    tool_name: Annotated[
        str | None,
        typer.Option(
            "--tool",
            "-t",
            help="Target tool (e.g., 'claude'). Defaults to auto-detect.",
        ),
    ] = None,
) -> None:
    """Update a slash command by re-fetching from GitHub.

    REFERENCE format:
      - username/command-name: re-fetches from github.com/username/agent-resources
      - username/repo/command-name: re-fetches from github.com/username/repo

    Examples:
      agr update command kasperjunge/hello
      agr update command kasperjunge/my-repo/hello-world --global
      agr update command kasperjunge/hello --tool claude
    """
    tool = get_tool_adapter(tool_name) if tool_name else None
    handle_update_resource(command_ref, ResourceType.COMMAND, global_install, tool)


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
    tool_name: Annotated[
        str | None,
        typer.Option(
            "--tool",
            "-t",
            help="Target tool (e.g., 'claude'). Defaults to auto-detect.",
        ),
    ] = None,
) -> None:
    """Update a sub-agent by re-fetching from GitHub.

    REFERENCE format:
      - username/agent-name: re-fetches from github.com/username/agent-resources
      - username/repo/agent-name: re-fetches from github.com/username/repo

    Examples:
      agr update agent kasperjunge/hello-agent
      agr update agent kasperjunge/my-repo/hello-agent --global
      agr update agent kasperjunge/hello-agent --tool claude
    """
    tool = get_tool_adapter(tool_name) if tool_name else None
    handle_update_resource(agent_ref, ResourceType.AGENT, global_install, tool)


@app.command("bundle")
def update_bundle(
    bundle_ref: Annotated[
        str,
        typer.Argument(
            help="Bundle reference: <username>/<bundle-name> or <username>/<repo>/<bundle-name>",
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
    """Update a bundle by re-fetching from GitHub.

    Re-downloads all resources from the bundle and overwrites local copies.
    Also adds any new resources that were added to the bundle upstream.

    REFERENCE format:
      - username/bundle-name: re-fetches from github.com/username/agent-resources
      - username/repo/bundle-name: re-fetches from github.com/username/repo

    Examples:
      agr update bundle kasperjunge/productivity
      agr update bundle kasperjunge/my-repo/productivity --global
    """
    handle_update_bundle(bundle_ref, global_install)
