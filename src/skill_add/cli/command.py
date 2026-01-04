"""CLI for command-add command."""

from typing import Annotated

import typer

from skill_add.cli.common import get_destination, parse_resource_ref
from skill_add.exceptions import (
    ClaudeAddError,
    RepoNotFoundError,
    ResourceExistsError,
    ResourceNotFoundError,
)
from skill_add.fetcher import ResourceType, fetch_resource

app = typer.Typer(
    add_completion=False,
    help="Add Claude Code slash commands from GitHub to your project.",
)


@app.command()
def add(
    command_ref: Annotated[
        str,
        typer.Argument(
            help="Command to add in format: <username>/<command-name>",
            metavar="USERNAME/COMMAND-NAME",
        ),
    ],
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite existing command if it exists.",
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
    """
    Add a slash command from a GitHub user's agent-skills repository.

    The command will be copied to .claude/commands/<command-name>.md in the
    current directory (or ~/.claude/commands/ with --global).

    Example:
        command-add kasperjunge/commit
        command-add kasperjunge/review-pr --global
    """
    try:
        username, command_name = parse_resource_ref(command_ref)
    except typer.BadParameter as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    dest = get_destination("commands", global_install)
    scope = "user" if global_install else "project"

    typer.echo(f"Fetching command '{command_name}' from {username}/agent-skills...")

    try:
        command_path = fetch_resource(
            username, command_name, dest, ResourceType.COMMAND, overwrite
        )
        typer.echo(f"Added command '{command_name}' to {command_path} ({scope} scope)")
    except RepoNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except ResourceNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except ResourceExistsError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except ClaudeAddError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
