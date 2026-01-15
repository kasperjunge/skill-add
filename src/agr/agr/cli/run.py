"""agrx - Run skills and commands without permanent installation."""

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
from agr.fetcher import fetch_resource
from agr.tools import ResourceType, ToolAdapter
from agr.tools.registry import get_tool_adapter

app = typer.Typer(name="agrx", help="Run skills and commands without permanent installation")
console = Console()

AGRX_PREFIX = "_agrx_"  # Prefix for temporary resources to avoid conflicts


def _check_tool_cli(tool: ToolAdapter) -> None:
    """Check if the tool's CLI is installed."""
    if not tool.is_installed():
        console.print(f"[red]Error: {tool.name} CLI not found.[/red]")
        if tool.cli_binary == "claude":
            console.print("Install it from: https://claude.ai/download")
        raise typer.Exit(1)


def _cleanup_resource(local_path: Path) -> None:
    """Clean up the temporary resource."""
    import shutil

    if local_path.exists():
        if local_path.is_dir():
            shutil.rmtree(local_path)
        else:
            local_path.unlink()


def _build_local_path(
    dest_dir: Path,
    name: str,
    resource_type: ResourceType,
    tool: ToolAdapter,
) -> Path:
    """Build the local path for a resource."""
    config = tool.get_resource_config(resource_type)
    if config is None:
        raise AgrError(f"Tool '{tool.name}' does not support {resource_type.value}s")
    if config.is_directory:
        return dest_dir / name
    return dest_dir / f"{name}{config.file_extension}"


def _run_resource(
    ref: str,
    resource_type: ResourceType,
    prompt_or_args: str | None,
    interactive: bool,
    global_install: bool,
    tool: ToolAdapter | None = None,
) -> None:
    """Download, run, and clean up a resource."""
    if tool is None:
        tool = get_tool_adapter()

    _check_tool_cli(tool)

    try:
        username, repo_name, name, path_segments = parse_resource_ref(ref)
    except typer.BadParameter as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    config = tool.get_resource_config(resource_type)
    if config is None:
        console.print(f"[red]Error: {tool.name} does not support {resource_type.value}s[/red]")
        raise typer.Exit(1)

    resource_name = path_segments[-1]
    prefixed_name = f"{AGRX_PREFIX}{resource_name}"

    dest_dir = get_destination(resource_type, global_install, tool)
    dest_dir.mkdir(parents=True, exist_ok=True)

    local_path = _build_local_path(dest_dir, prefixed_name, resource_type, tool)

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
                tool=tool,
            )

        # Rename to prefixed name to avoid conflicts
        original_path = _build_local_path(dest_dir, resource_name, resource_type, tool)

        if original_path.exists() and original_path != local_path:
            if local_path.exists():
                _cleanup_resource(local_path)
            original_path.rename(local_path)

        console.print(f"[dim]Running {resource_type.value} '{name}'...[/dim]")

        cli_binary = tool.cli_binary
        if cli_binary is None:
            console.print(f"[red]Error: {tool.name} does not have a CLI[/red]")
            raise typer.Exit(1)

        if interactive:
            # Start interactive session
            subprocess.run([cli_binary], check=False)
        else:
            # Build prompt: /<prefixed_name> [prompt_or_args]
            prompt = f"/{prefixed_name}"
            if prompt_or_args:
                prompt += f" {prompt_or_args}"
            subprocess.run([cli_binary, "-p", prompt], check=False)

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
        False, "--interactive", "-i", help="Start interactive session"
    ),
    global_install: bool = typer.Option(
        False, "--global", "-g", help="Install temporarily to ~/.<tool>/ instead of ./.<tool>/"
    ),
    tool_name: str | None = typer.Option(
        None, "--tool", "-t", help="Target tool (e.g., 'claude'). Defaults to auto-detect."
    ),
) -> None:
    """Run a skill temporarily without permanent installation."""
    tool = get_tool_adapter(tool_name) if tool_name else None
    _run_resource(skill_ref, ResourceType.SKILL, prompt, interactive, global_install, tool)


@app.command("command")
def run_command(
    command_ref: str = typer.Argument(..., help="Command reference (e.g., username/command-name)"),
    args: str = typer.Argument(None, help="Arguments to pass to the command"),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Start interactive session"
    ),
    global_install: bool = typer.Option(
        False, "--global", "-g", help="Install temporarily to ~/.<tool>/ instead of ./.<tool>/"
    ),
    tool_name: str | None = typer.Option(
        None, "--tool", "-t", help="Target tool (e.g., 'claude'). Defaults to auto-detect."
    ),
) -> None:
    """Run a command temporarily without permanent installation."""
    tool = get_tool_adapter(tool_name) if tool_name else None
    _run_resource(command_ref, ResourceType.COMMAND, args, interactive, global_install, tool)


if __name__ == "__main__":
    app()
