"""CLI entry point for agrx - temporary skill runner."""

import atexit
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from agr import __version__
from agr.config import find_repo_root
from agr.exceptions import AgrError, InvalidHandleError
from agr.fetcher import downloaded_repo, install_skill_from_repo
from agr.handle import parse_handle
from agr.tool import DEFAULT_TOOL

app = typer.Typer(
    name="agrx",
    help="Run a skill temporarily without adding to agr.toml.",
    no_args_is_help=True,
    add_completion=False,
)

console = Console()

AGRX_PREFIX = "_agrx_"  # Prefix for temporary resources


def _check_claude_cli() -> None:
    """Check if Claude CLI is installed."""
    if shutil.which("claude") is None:
        console.print("[red]Error:[/red] Claude CLI not found.")
        console.print("[dim]Install it from: https://claude.ai/download[/dim]")
        raise typer.Exit(1)


def _cleanup_skill(skill_path: Path) -> None:
    """Clean up a temporary skill."""
    if skill_path.exists():
        try:
            shutil.rmtree(skill_path)
        except Exception:
            pass  # Best effort cleanup


@app.command()
def main(
    handle: Annotated[
        str,
        typer.Argument(
            help="Skill handle to run (e.g., kasperjunge/commit).",
        ),
    ],
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive", "-i",
            help="Start interactive Claude session after running the skill.",
        ),
    ] = False,
    prompt: Annotated[
        Optional[str],
        typer.Option(
            "--prompt", "-p",
            help="Prompt to pass to the skill.",
        ),
    ] = None,
    global_install: Annotated[
        bool,
        typer.Option(
            "--global", "-g",
            help="Install to ~/.claude/skills/ instead of ./.claude/skills/.",
        ),
    ] = False,
) -> None:
    """Run a skill temporarily without adding to agr.toml.

    Downloads and installs the skill to a temporary location, runs it with Claude,
    and cleans up afterwards.

    Examples:
        agrx kasperjunge/commit
        agrx maragudk/skills/collaboration -i
        agrx kasperjunge/commit -p "Review my changes"
    """
    # Find repo root (or use current dir for global)
    if global_install:
        skills_dir = DEFAULT_TOOL.get_global_skills_dir()
    else:
        repo_root = find_repo_root()
        if repo_root is None:
            console.print("[red]Error:[/red] Not in a git repository")
            console.print("[dim]Use --global to install to ~/.claude/skills/[/dim]")
            raise typer.Exit(1)
        skills_dir = DEFAULT_TOOL.get_skills_dir(repo_root)

    try:
        # Parse handle
        parsed = parse_handle(handle)

        if parsed.is_local:
            console.print("[red]Error:[/red] agrx only works with remote handles")
            console.print("[dim]Use 'agr add' for local skills[/dim]")
            raise typer.Exit(1)

        # Check Claude CLI is available
        _check_claude_cli()

        # Get GitHub coordinates
        username, repo_name = parsed.get_github_repo()

        console.print(f"[dim]Downloading {handle}...[/dim]")

        # Create prefixed name for temporary skill
        prefixed_name = f"{AGRX_PREFIX}{parsed.name}"
        temp_skill_path = skills_dir / prefixed_name

        # Download and install
        with downloaded_repo(username, repo_name) as repo_dir:
            # Create a modified handle for the prefixed installation
            from agr.handle import ParsedHandle
            temp_handle = ParsedHandle(
                username=AGRX_PREFIX.rstrip("_"),
                name=parsed.name,
            )

            install_skill_from_repo(
                repo_dir,
                parsed.name,
                temp_handle,
                skills_dir,
                overwrite=True,
            )

        # The skill is installed as _agrx_:skillname, rename to just _agrx_skillname
        installed_path = skills_dir / f"{AGRX_PREFIX.rstrip('_')}:{parsed.name}"
        if installed_path.exists() and installed_path != temp_skill_path:
            if temp_skill_path.exists():
                shutil.rmtree(temp_skill_path)
            installed_path.rename(temp_skill_path)

        # Set up cleanup handlers
        cleanup_done = False

        def cleanup_handler(signum, frame):
            nonlocal cleanup_done
            if not cleanup_done:
                cleanup_done = True
                _cleanup_skill(temp_skill_path)
            sys.exit(1)

        original_sigint = signal.signal(signal.SIGINT, cleanup_handler)
        original_sigterm = signal.signal(signal.SIGTERM, cleanup_handler)

        try:
            console.print(f"[dim]Running skill '{parsed.name}'...[/dim]")

            # Build the claude command
            skill_prompt = f"/{prefixed_name}"
            if prompt:
                skill_prompt += f" {prompt}"

            if interactive:
                # Run the skill first, then continue in interactive mode
                subprocess.run(
                    ["claude", "-p", skill_prompt, "--dangerously-skip-permissions"],
                    check=False,
                )
                console.print("[dim]Continuing in interactive mode...[/dim]")
                subprocess.run(["claude", "--continue"], check=False)
            else:
                # Just run the skill
                subprocess.run(
                    ["claude", "-p", skill_prompt],
                    check=False,
                )

        finally:
            # Restore signal handlers
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)

            # Clean up
            if not cleanup_done:
                cleanup_done = True
                _cleanup_skill(temp_skill_path)

    except InvalidHandleError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except AgrError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
