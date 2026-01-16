"""Sync command for agr - install dependencies from agr.toml."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from agr.cli.common import find_agr_toml, get_author_from_git, get_base_path
from agr.config import CONFIG_FILENAME, AgrConfig
from agr.exceptions import ConfigNotFoundError, ConfigParseError
from agr.sync import clean_untracked, sync_authored_packages, sync_dependencies

console = Console()

app = typer.Typer(help="Sync dependencies from agr.toml.")


@app.callback(invoke_without_command=True)
def sync(
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Force overwrite even if resources have been modified locally.",
        ),
    ] = False,
    clean: Annotated[
        bool,
        typer.Option(
            "--clean",
            help="Remove resources not tracked in agr.toml.",
        ),
    ] = False,
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Sync to ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
) -> None:
    """Sync all dependencies and packages from agr.toml.

    Reads agr.toml and installs all dependencies to .claude/ directory.
    Also builds locally-authored packages.

    Examples:
      agr sync              # Install/update all dependencies
      agr sync --force      # Overwrite modified resources
      agr sync --clean      # Remove untracked resources
    """
    # Find config file
    config_path = find_agr_toml()
    if not config_path:
        console.print(f"[red]Error: {CONFIG_FILENAME} not found[/red]")
        console.print("[dim]Run 'agr add <ref>' to create one[/dim]")
        raise typer.Exit(1)

    # Load config
    try:
        config = AgrConfig.load(config_path)
    except ConfigNotFoundError:
        console.print(f"[red]Error: {CONFIG_FILENAME} not found at {config_path}[/red]")
        raise typer.Exit(1)
    except ConfigParseError as e:
        console.print(f"[red]Error parsing {CONFIG_FILENAME}: {e}[/red]")
        raise typer.Exit(1)

    # Determine destination
    dest_base = get_base_path(global_install)

    # Get author for authored packages
    author = get_author_from_git(config_path.parent)

    console.print(f"[dim]Syncing from {config_path}[/dim]")

    has_work = False

    # Sync dependencies
    if config.dependencies:
        console.print(f"\n[cyan]Syncing {len(config.dependencies)} dependencies...[/cyan]")
        dep_result = sync_dependencies(config, dest_base, force)

        if dep_result.installed:
            has_work = True
            for item in dep_result.installed:
                console.print(f"  [green]+ {item}[/green]")

        if dep_result.updated:
            has_work = True
            for item in dep_result.updated:
                console.print(f"  [blue]↑ {item}[/blue]")

        if dep_result.skipped:
            for item in dep_result.skipped:
                console.print(f"  [dim]= {item}[/dim]")

        if dep_result.failed:
            has_work = True
            for ref, error in dep_result.failed:
                console.print(f"  [red]✗ {ref}: {error}[/red]")

    # Sync authored packages
    if config.packages and author:
        console.print(f"\n[cyan]Building {len(config.packages)} packages...[/cyan]")
        pkg_result = sync_authored_packages(config, dest_base, author, force)

        if pkg_result.installed:
            has_work = True
            for item in pkg_result.installed:
                console.print(f"  [green]+ {item}[/green]")

        if pkg_result.updated:
            has_work = True
            for item in pkg_result.updated:
                console.print(f"  [blue]↑ {item}[/blue]")

        if pkg_result.skipped:
            for item in pkg_result.skipped:
                console.print(f"  [dim]= {item}[/dim]")

        if pkg_result.failed:
            has_work = True
            for ref, error in pkg_result.failed:
                console.print(f"  [red]✗ {ref}: {error}[/red]")
    elif config.packages and not author:
        console.print(
            "[yellow]Warning: Cannot determine author from git remote. "
            "Packages will not be synced.[/yellow]"
        )

    # Clean untracked resources
    if clean:
        console.print("\n[cyan]Cleaning untracked resources...[/cyan]")
        removed = clean_untracked(config, dest_base, author)
        if removed:
            has_work = True
            for item in removed:
                console.print(f"  [red]- {item}[/red]")
        else:
            console.print("  [dim]No untracked resources found[/dim]")

    # Summary
    if not has_work and not config.dependencies and not config.packages:
        console.print("\n[yellow]No dependencies or packages in agr.toml[/yellow]")
        console.print("[dim]Run 'agr add <ref>' to add dependencies[/dim]")
    elif not has_work:
        console.print("\n[green]Everything up to date[/green]")
    else:
        console.print("\n[green]Sync complete[/green]")
