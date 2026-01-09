"""CLI for add-command command."""

from typing import Annotated

import typer

from agent_resources.cli.common import fetch_spinner, get_destination, parse_resource_ref, print_success_message
from agent_resources.exceptions import (
    ClaudeAddError,
    RepoNotFoundError,
    ResourceExistsError,
    ResourceNotFoundError,
)
from agent_resources.fetcher import ResourceType, fetch_resource

app = typer.Typer(
    add_completion=False,
    help="Add Claude Code slash commands from GitHub to your project.",
)


@app.command()
def add(
    command_ref: Annotated[
        str,
        typer.Argument(
            help="Command to add: <username>/<command-name> or <username>/<repo>/<command-name>",
            metavar="USERNAME/[REPO/]COMMAND-NAME",
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
    Add a slash command from a GitHub repository.

    The command will be copied to .claude/commands/<command-name>.md in the
    current directory (or ~/.claude/commands/ with --global).

    Example:
        add-command kasperjunge/commit
        add-command kasperjunge/my-repo/commit
        add-command kasperjunge/review-pr --global
    """
    try:
        username, repo_name, command_name = parse_resource_ref(command_ref)
    except typer.BadParameter as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    dest = get_destination("commands", global_install)

    try:
        with fetch_spinner():
            command_path = fetch_resource(
                username, repo_name, command_name, dest, ResourceType.COMMAND, overwrite
            )
        print_success_message("command", command_name, username, repo_name)
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
