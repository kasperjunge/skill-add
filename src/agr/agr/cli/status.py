"""Status command for agr - show sync status."""

from typing import Annotated

import typer
from rich.console import Console

from agr.cli.common import find_agr_toml, get_author_from_git, get_base_path
from agr.config import CONFIG_FILENAME, AgrConfig
from agr.exceptions import ConfigNotFoundError, ConfigParseError
from agr.status import get_status

console = Console()

app = typer.Typer(help="Show sync status.")


@app.callback(invoke_without_command=True)
def status(
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Check ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
) -> None:
    """Show status of resources relative to agr.toml.

    Displays which resources are:
    - Synced: Installed and up to date
    - Modified: Installed but changed locally
    - Missing: In config but not installed
    - Untracked: Installed but not in config

    Examples:
      agr status            # Show status of local .claude/
      agr status --global   # Show status of ~/.claude/
    """
    # Find config file
    config_path = find_agr_toml()
    if not config_path:
        console.print(f"[yellow]{CONFIG_FILENAME} not found[/yellow]")
        console.print("[dim]Run 'agr add <ref>' to create one[/dim]")

        # Still show untracked resources
        dest_base = get_base_path(global_install)
        if dest_base.exists():
            console.print(f"\n[cyan]Scanning {dest_base}...[/cyan]")
            _show_untracked_only(dest_base)
        return

    # Load config
    try:
        config = AgrConfig.load(config_path)
    except ConfigNotFoundError:
        console.print(f"[red]Error: {CONFIG_FILENAME} not found at {config_path}[/red]")
        raise typer.Exit(1)
    except ConfigParseError as e:
        console.print(f"[red]Error parsing {CONFIG_FILENAME}: {e}[/red]")
        raise typer.Exit(1)

    # Get destination and author
    dest_base = get_base_path(global_install)
    author = get_author_from_git(config_path.parent)

    console.print(f"[dim]Config: {config_path}[/dim]")
    console.print(f"[dim]Target: {dest_base}[/dim]")
    if author:
        console.print(f"[dim]Author: {author}[/dim]")

    # Get status
    report = get_status(config, dest_base, author)

    # Display results
    console.print()

    if report.synced:
        console.print(f"[green]Synced ({len(report.synced)})[/green]")
        for item in report.synced:
            ref_str = f" [dim]<- {item.source_ref}[/dim]" if item.source_ref else ""
            console.print(f"  [green]✓[/green] {item.path}{ref_str}")

    if report.modified:
        console.print(f"\n[yellow]Modified ({len(report.modified)})[/yellow]")
        for item in report.modified:
            console.print(f"  [yellow]~[/yellow] {item.path}")
        console.print("[dim]  Use 'agr sync --force' to overwrite[/dim]")

    if report.missing:
        console.print(f"\n[red]Missing ({len(report.missing)})[/red]")
        for item in report.missing:
            ref_str = f" [dim](from {item.source_ref})[/dim]" if item.source_ref else ""
            console.print(f"  [red]![/red] {item.path}{ref_str}")
        console.print("[dim]  Use 'agr sync' to install[/dim]")

    if report.untracked:
        console.print(f"\n[blue]Untracked ({len(report.untracked)})[/blue]")
        for item in report.untracked:
            console.print(f"  [blue]?[/blue] {item.path}")
        console.print("[dim]  Use 'agr sync --clean' to remove[/dim]")

    # Summary
    console.print()
    if report.is_clean:
        console.print("[green]Everything is synced and clean[/green]")
    else:
        total_deps = len(config.dependencies)
        total_pkgs = len(config.packages)
        console.print(f"[dim]Dependencies: {total_deps}, Packages: {total_pkgs}[/dim]")

        if report.missing:
            console.print("[yellow]Run 'agr sync' to install missing resources[/yellow]")


def _show_untracked_only(dest_base):
    """Show untracked resources when no config exists."""
    from pathlib import Path

    untracked: list[str] = []

    for subdir in ["skills", "commands", "agents"]:
        subdir_path = dest_base / subdir
        if not subdir_path.is_dir():
            continue

        for author_dir in subdir_path.iterdir():
            if not author_dir.is_dir():
                continue

            for resource in author_dir.iterdir():
                if resource.is_dir():
                    if (resource / "SKILL.md").exists():
                        untracked.append(f"{subdir}/{author_dir.name}/{resource.name}")
                    else:
                        for item in resource.iterdir():
                            untracked.append(f"{subdir}/{author_dir.name}/{resource.name}/{item.name}")
                elif resource.suffix == ".md":
                    untracked.append(f"{subdir}/{author_dir.name}/{resource.stem}")

    if untracked:
        console.print(f"\n[blue]Untracked ({len(untracked)})[/blue]")
        for item in sorted(untracked):
            console.print(f"  [blue]?[/blue] {item}")
    else:
        console.print("[dim]No resources found[/dim]")
