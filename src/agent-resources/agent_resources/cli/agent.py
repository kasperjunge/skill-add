"""CLI for add-agent command."""

from typing import Annotated

import typer

from agent_resources.cli.common import handle_add_resource
from agent_resources.fetcher import ResourceType

app = typer.Typer(
    add_completion=False,
    help="Add Claude Code sub-agents from GitHub to your project.",
)


@app.command()
def add(
    agent_ref: Annotated[
        str,
        typer.Argument(
            help="Agent to add: <username>/<agent-name> or <username>/<repo>/<agent-name>",
            metavar="USERNAME/[REPO/]AGENT-NAME",
        ),
    ],
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite existing agent if it exists.",
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
    Add a sub-agent from a GitHub repository.

    The agent will be copied to .claude/agents/<agent-name>.md in the
    current directory (or ~/.claude/agents/ with --global).

    Example:
        add-agent kasperjunge/code-reviewer
        add-agent kasperjunge/my-repo/code-reviewer
        add-agent kasperjunge/test-writer --global
    """
    handle_add_resource(agent_ref, ResourceType.AGENT, "agents", overwrite, global_install)


if __name__ == "__main__":
    app()
