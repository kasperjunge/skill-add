"""CLI for add-command command."""

from typing import Annotated

import typer

from agent_resources.cli.common import handle_add_resource
from agent_resources.fetcher import ResourceType

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
    handle_add_resource(command_ref, ResourceType.COMMAND, "commands", overwrite, global_install)


if __name__ == "__main__":
    app()
