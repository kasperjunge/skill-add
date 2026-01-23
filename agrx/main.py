"""CLI entry point for agrx - temporary skill runner."""

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
from agr.core import Orchestrator
from agr.exceptions import AgrError, InvalidHandleError
from agr.handle import parse_handle

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
    repo_root = find_repo_root()
    if not global_install and repo_root is None:
        console.print("[red]Error:[/red] Not in a git repository")
        console.print("[dim]Use --global to install to ~/.claude/skills/[/dim]")
        raise typer.Exit(1)

    # Use current directory as fallback for global installs
    if repo_root is None:
        repo_root = Path.cwd()

    try:
        # Parse handle
        parsed = parse_handle(handle)

        if parsed.is_local:
            console.print("[red]Error:[/red] agrx only works with remote handles")
            console.print("[dim]Use 'agr add' for local skills[/dim]")
            raise typer.Exit(1)

        # Check Claude CLI is available
        _check_claude_cli()

        console.print(f"[dim]Downloading {handle}...[/dim]")

        # Use Orchestrator for installation
        orchestrator = Orchestrator()
        result = orchestrator.install(
            parsed,
            repo_root,
            overwrite=True,
            temporary=True,
            temp_prefix=AGRX_PREFIX,
            global_install=global_install,
        )

        temp_skill_path = result.installed_path
        prefixed_name = result.resource_name

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
