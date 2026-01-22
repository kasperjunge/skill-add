"""CLI entry point for agr."""

from typing import Annotated, Optional

import typer

from agr import __version__
from agr.commands.add import run_add
from agr.commands.init import run_init
from agr.commands.list import run_list
from agr.commands.remove import run_remove
from agr.commands.sync import run_sync

app = typer.Typer(
    name="agr",
    help="Agent Resources - Install and manage Claude Code skills.",
    no_args_is_help=True,
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        print(f"agr {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version", "-v",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """Agent Resources - Install and manage Claude Code skills."""
    pass


@app.command()
def init(
    skill_name: Annotated[
        Optional[str],
        typer.Argument(
            help="Name for a new skill scaffold. If omitted, creates agr.toml.",
        ),
    ] = None,
) -> None:
    """Initialize agr.toml or create a skill scaffold.

    Without arguments: Creates agr.toml in current directory.
    With skill name: Creates a skill scaffold directory.

    Examples:
        agr init           # Create agr.toml
        agr init my-skill  # Create my-skill/SKILL.md scaffold
    """
    run_init(skill_name)


@app.command()
def add(
    refs: Annotated[
        list[str],
        typer.Argument(
            help="Skill handles (user/skill) or local paths (./path) to add.",
        ),
    ],
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite", "-o",
            help="Overwrite existing skills.",
        ),
    ] = False,
) -> None:
    """Add skills from GitHub or local paths.

    Examples:
        agr add kasperjunge/commit
        agr add maragudk/skills/collaboration
        agr add ./my-skill
        agr add kasperjunge/commit kasperjunge/pr  # Multiple
    """
    run_add(refs, overwrite)


@app.command()
def remove(
    refs: Annotated[
        list[str],
        typer.Argument(
            help="Skill handles or paths to remove.",
        ),
    ],
) -> None:
    """Remove skills from the project.

    Examples:
        agr remove kasperjunge/commit
        agr remove ./my-skill
    """
    run_remove(refs)


@app.command()
def sync() -> None:
    """Install all skills from agr.toml.

    Installs any dependencies that aren't already installed.
    """
    run_sync()


@app.command(name="list")
def list_cmd() -> None:
    """List all skills and their status.

    Shows all dependencies from agr.toml and whether they're installed.
    """
    run_list()


if __name__ == "__main__":
    app()
