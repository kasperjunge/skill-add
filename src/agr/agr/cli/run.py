"""agrx - Run skills and commands without permanent installation."""

import shutil
import signal
import subprocess
import sys
from pathlib import Path
from typing import Annotated, List, Optional

import typer
from rich.console import Console

from agr.cli.common import (
    discover_runnable_resource,
    fetch_spinner,
    get_destination,
    parse_resource_ref,
)
from agr.exceptions import AgrError, MultipleResourcesFoundError
from agr.fetcher import RESOURCE_CONFIGS, ResourceType, downloaded_repo, fetch_resource, fetch_resource_from_repo_dir

# Deprecated subcommand names
DEPRECATED_SUBCOMMANDS = {"skill", "command"}

app = typer.Typer(
    name="agrx",
    help="Run skills and commands without permanent installation",
)
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


def _run_resource_unified(
    ref: str,
    prompt_or_args: str | None,
    interactive: bool,
    global_install: bool,
    resource_type: str | None = None,
) -> None:
    """
    Download, run, and clean up a resource with auto-detection.

    Args:
        ref: Resource reference (e.g., "username/skill-name")
        prompt_or_args: Optional prompt or arguments to pass
        interactive: If True, start interactive Claude session
        global_install: If True, install to ~/.claude/ instead of ./.claude/
        resource_type: Optional explicit type ("skill" or "command")
    """
    _check_claude_cli()

    try:
        username, repo_name, name, path_segments = parse_resource_ref(ref)
    except typer.BadParameter as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    # If explicit type provided, use existing handler
    if resource_type:
        type_lower = resource_type.lower()
        if type_lower == "skill":
            _run_resource(ref, ResourceType.SKILL, prompt_or_args, interactive, global_install)
            return
        elif type_lower == "command":
            _run_resource(ref, ResourceType.COMMAND, prompt_or_args, interactive, global_install)
            return
        else:
            console.print(f"[red]Error: Unknown resource type '{resource_type}'. Use: skill or command.[/red]")
            raise typer.Exit(1)

    # Auto-detect type by downloading repo
    try:
        with fetch_spinner():
            with downloaded_repo(username, repo_name) as repo_dir:
                discovery = discover_runnable_resource(repo_dir, name, path_segments)

                if discovery.is_empty:
                    console.print(
                        f"[red]Error: Resource '{name}' not found in {username}/{repo_name}.[/red]\n"
                        f"Searched in: skills, commands.",
                    )
                    raise typer.Exit(1)

                if discovery.is_ambiguous:
                    console.print(
                        f"[red]Error: Resource '{name}' found in multiple types: {', '.join(discovery.found_types)}.[/red]\n"
                        f"Use --type to specify which one to run.",
                    )
                    raise typer.Exit(1)

                # Use the discovered resource type
                detected_type = discovery.resources[0].resource_type
                config = RESOURCE_CONFIGS[detected_type]
                resource_name = path_segments[-1]
                prefixed_name = f"{AGRX_PREFIX}{resource_name}"

                dest_dir = get_destination(config.dest_subdir, global_install)
                dest_dir.mkdir(parents=True, exist_ok=True)

                local_path = _build_local_path(dest_dir, prefixed_name, detected_type)

                # Fetch the resource from the already-downloaded repo
                fetch_resource_from_repo_dir(
                    repo_dir, name, path_segments, dest_dir, detected_type, overwrite=True
                )

                # Rename to prefixed name to avoid conflicts
                original_path = _build_local_path(dest_dir, resource_name, detected_type)
                if original_path.exists() and original_path != local_path:
                    if local_path.exists():
                        _cleanup_resource(local_path)
                    original_path.rename(local_path)

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
            console.print(f"[dim]Running {detected_type.value} '{name}'...[/dim]")

            if interactive:
                subprocess.run(["claude"], check=False)
            else:
                claude_prompt = f"/{prefixed_name}"
                if prompt_or_args:
                    claude_prompt += f" {prompt_or_args}"
                subprocess.run(["claude", "-p", claude_prompt], check=False)
        finally:
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)
            if not cleanup_done:
                _cleanup_resource(local_path)

    except AgrError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def run_unified(
    ctx: typer.Context,
    args: Annotated[
        Optional[List[str]],
        typer.Argument(help="Resource reference and optional prompt"),
    ] = None,
    resource_type: Annotated[
        Optional[str],
        typer.Option(
            "--type",
            "-t",
            help="Explicit resource type: skill or command",
        ),
    ] = None,
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive",
            "-i",
            help="Start interactive Claude session",
        ),
    ] = False,
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Install temporarily to ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
) -> None:
    """Run a skill or command temporarily without permanent installation.

    Auto-detects the resource type (skill or command).
    Use --type to explicitly specify when a name exists in multiple types.

    Examples:
      agrx kasperjunge/hello-world
      agrx kasperjunge/hello-world "my prompt"
      agrx kasperjunge/my-repo/hello-world --type skill
      agrx kasperjunge/hello-world --interactive
    """
    if not args:
        console.print(ctx.get_help())
        raise typer.Exit(0)

    first_arg = args[0]

    # Handle deprecated subcommand syntax: agrx skill <ref>
    if first_arg in DEPRECATED_SUBCOMMANDS:
        if len(args) < 2:
            console.print(f"[red]Error: Missing resource reference after '{first_arg}'.[/red]")
            raise typer.Exit(1)

        resource_ref = args[1]
        prompt_or_args = args[2] if len(args) > 2 else None
        console.print(
            f"[yellow]Warning: 'agrx {first_arg}' is deprecated. "
            f"Use 'agrx {resource_ref}' instead.[/yellow]"
        )

        if first_arg == "skill":
            _run_resource(resource_ref, ResourceType.SKILL, prompt_or_args, interactive, global_install)
        elif first_arg == "command":
            _run_resource(resource_ref, ResourceType.COMMAND, prompt_or_args, interactive, global_install)
        return

    # Normal unified run: agrx <ref> [prompt]
    resource_ref = first_arg
    prompt_or_args = args[1] if len(args) > 1 else None
    _run_resource_unified(resource_ref, prompt_or_args, interactive, global_install, resource_type)


if __name__ == "__main__":
    app()
