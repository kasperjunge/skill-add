"""agr sync command implementation."""

from pathlib import Path

from rich.console import Console

from agr.config import AgrConfig, find_config, find_repo_root
from agr.exceptions import AgrError
from agr.fetcher import fetch_and_install, is_skill_installed
from agr.handle import parse_handle

console = Console()


def run_sync() -> None:
    """Run the sync command.

    Installs all dependencies from agr.toml that aren't already installed.
    """
    # Find repo root
    repo_root = find_repo_root()
    if repo_root is None:
        console.print("[red]Error:[/red] Not in a git repository")
        raise SystemExit(1)

    # Find config
    config_path = find_config()
    if config_path is None:
        console.print("[yellow]No agr.toml found.[/yellow] Nothing to sync.")
        return

    config = AgrConfig.load(config_path)

    if not config.dependencies:
        console.print("[yellow]No dependencies in agr.toml.[/yellow] Nothing to sync.")
        return

    # Track results
    results: list[tuple[str, str, str | None]] = []  # (identifier, status, error)

    for dep in config.dependencies:
        identifier = dep.identifier

        try:
            # Parse handle
            if dep.is_local:
                ref = dep.path or ""
            else:
                ref = dep.handle or ""

            handle = parse_handle(ref)
            installed_name = handle.to_installed_name()

            # Check if already installed
            if is_skill_installed(installed_name, repo_root):
                results.append((identifier, "up-to-date", None))
                continue

            # Install
            fetch_and_install(handle, repo_root, overwrite=False)
            results.append((identifier, "installed", None))

        except AgrError as e:
            results.append((identifier, "error", str(e)))
        except Exception as e:
            results.append((identifier, "error", f"Unexpected: {e}"))

    # Print results
    installed = 0
    up_to_date = 0
    errors = 0

    for identifier, status, error in results:
        if status == "installed":
            console.print(f"[green]Installed:[/green] {identifier}")
            installed += 1
        elif status == "up-to-date":
            console.print(f"[dim]Up to date:[/dim] {identifier}")
            up_to_date += 1
        else:
            console.print(f"[red]Error:[/red] {identifier}")
            if error:
                console.print(f"  [dim]{error}[/dim]")
            errors += 1

    # Summary
    console.print()
    parts = []
    if installed:
        parts.append(f"{installed} installed")
    if up_to_date:
        parts.append(f"{up_to_date} up to date")
    if errors:
        parts.append(f"{errors} failed")

    console.print(f"[bold]Summary:[/bold] {', '.join(parts)}")

    if errors:
        raise SystemExit(1)
