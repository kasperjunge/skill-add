"""CLI for add-skill command."""

from typing import Annotated

import typer

from agent_resources.cli.common import handle_add_resource
from agent_resources.fetcher import ResourceType

app = typer.Typer(
    add_completion=False,
    help="Add Claude Code skills from GitHub to your project.",
)


@app.command()
def add(
    skill_ref: Annotated[
        str,
        typer.Argument(
            help="Skill to add: <username>/<skill-name> or <username>/<repo>/<skill-name>",
            metavar="USERNAME/[REPO/]SKILL-NAME",
        ),
    ],
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite existing skill if it exists.",
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
    Add a skill from a GitHub repository.

    The skill will be copied to .claude/skills/<skill-name>/ in the current
    directory (or ~/.claude/skills/ with --global).

    Example:
        add-skill kasperjunge/analyze-paper
        add-skill kasperjunge/my-repo/analyze-paper
        add-skill kasperjunge/analyze-paper --global
    """
    handle_add_resource(skill_ref, ResourceType.SKILL, "skills", overwrite, global_install)


if __name__ == "__main__":
    app()
