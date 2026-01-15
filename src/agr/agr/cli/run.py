"""agrx - Run skills and commands without permanent installation."""

import shutil
import signal
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console

from agr.cli.common import (
    fetch_spinner,
    get_destination,
    parse_resource_ref,
)
from agr.exceptions import AgrError
from agr.fetcher import RESOURCE_CONFIGS, ResourceType, fetch_resource

app = typer.Typer(name="agrx", help="Run skills and commands without permanent installation")
console = Console()

AGRX_PREFIX = "_agrx_"  # Prefix for temporary resources to avoid conflicts


def _check_claude_cli() -> None:
    """Check if Claude CLI is installed."""
    if shutil.which("claude") is None:
        console.print("[red]Error: Claude CLI not found.[/red]")
        console.print("Install it from: https://claude.ai/download")
        raise typer.Exit(1)


def _cleanup_resource(local_path: Path) -> None:
    """Clean up the temporary resource."""
    if local_path.exists():
        if local_path.is_dir():
            shutil.rmtree(local_path)
        else:
            local_path.unlink()


def _build_local_path(dest_dir: Path, prefixed_name: str, resource_type: ResourceType) -> Path:
    """Build the local path for a resource based on its type."""
    config = RESOURCE_CONFIGS[resource_type]
    if config.is_directory:
        return dest_dir / prefixed_name
    return dest_dir / f"{prefixed_name}{config.file_extension}"


def _run_resource(
    ref: str,
    resource_type: ResourceType,
    prompt_or_args: str | None,
    interactive: bool,
    global_install: bool,
) -> None:
    """
    Download, run, and clean up a resource.

    Args:
        ref: Resource reference (e.g., "username/skill-name")
        resource_type: Type of resource (SKILL or COMMAND)
        prompt_or_args: Optional prompt or arguments to pass
        interactive: If True, start interactive Claude session
        global_install: If True, install to ~/.claude/ instead of ./.claude/
    """
    _check_claude_cli()

    try:
        username, repo_name, name, path_segments = parse_resource_ref(ref)
    except typer.BadParameter as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    config = RESOURCE_CONFIGS[resource_type]
    resource_name = path_segments[-1]
    prefixed_name = f"{AGRX_PREFIX}{resource_name}"

    dest_dir = get_destination(config.dest_subdir, global_install)
    dest_dir.mkdir(parents=True, exist_ok=True)

    local_path = _build_local_path(dest_dir, prefixed_name, resource_type)

    # Set up signal handlers for cleanup on interrupt
    cleanup_done = False

    def cleanup_handler(signum, frame):
        nonlocal cleanup_done
        if not cleanup_done:
            cleanup_done = True
            _cleanup_resource(local_path)
        sys.exit(1)

    original_sigint = signal.signal(signal.SIGINT, cleanup_handler)
    original_sigterm = signal.signal(signal.SIGTERM, cleanup_handler)

    try:
        # Fetch the resource to original name first
        with fetch_spinner():
            fetch_resource(
                username,
                repo_name,
                name,
                path_segments,
                dest_dir,
                resource_type,
                overwrite=True,
            )

        # Rename to prefixed name to avoid conflicts
        original_path = _build_local_path(dest_dir, resource_name, resource_type)

        if original_path.exists() and original_path != local_path:
            if local_path.exists():
                _cleanup_resource(local_path)
            original_path.rename(local_path)

        console.print(f"[dim]Running {resource_type.value} '{name}'...[/dim]")

        if interactive:
            # Start interactive Claude session
            subprocess.run(["claude"], check=False)
        else:
            # Build prompt: /<prefixed_name> [prompt_or_args]
            claude_prompt = f"/{prefixed_name}"
            if prompt_or_args:
                claude_prompt += f" {prompt_or_args}"
            subprocess.run(["claude", "-p", claude_prompt], check=False)

    except AgrError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        # Restore original signal handlers
        signal.signal(signal.SIGINT, original_sigint)
        signal.signal(signal.SIGTERM, original_sigterm)

        # Cleanup the resource
        if not cleanup_done:
            _cleanup_resource(local_path)


@app.command("skill")
def run_skill(
    skill_ref: str = typer.Argument(..., help="Skill reference (e.g., username/skill-name)"),
    prompt: str = typer.Argument(None, help="Prompt to send with the skill"),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Start interactive Claude session"
    ),
    global_install: bool = typer.Option(
        False, "--global", "-g", help="Install temporarily to ~/.claude/ instead of ./.claude/"
    ),
) -> None:
    """Run a skill temporarily without permanent installation."""
    _run_resource(skill_ref, ResourceType.SKILL, prompt, interactive, global_install)


@app.command("command")
def run_command(
    command_ref: str = typer.Argument(..., help="Command reference (e.g., username/command-name)"),
    args: str = typer.Argument(None, help="Arguments to pass to the command"),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Start interactive Claude session"
    ),
    global_install: bool = typer.Option(
        False, "--global", "-g", help="Install temporarily to ~/.claude/ instead of ./.claude/"
    ),
) -> None:
    """Run a command temporarily without permanent installation."""
    _run_resource(command_ref, ResourceType.COMMAND, args, interactive, global_install)


if __name__ == "__main__":
    app()
