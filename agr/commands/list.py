"""agr list command implementation."""

from rich.console import Console
from rich.table import Table

from agr.config import AgrConfig, find_config, find_repo_root
from agr.fetcher import is_skill_installed
from agr.handle import parse_handle

console = Console()


def run_list() -> None:
    """Run the list command.

    Lists all dependencies from agr.toml with their sync status.
    """
    # Find repo root
    repo_root = find_repo_root()
    if repo_root is None:
        console.print("[red]Error:[/red] Not in a git repository")
        raise SystemExit(1)

    # Find config
    config_path = find_config()
    if config_path is None:
        console.print("[yellow]No agr.toml found.[/yellow]")
        console.print("[dim]Run 'agr init' to create one.[/dim]")
        return

    config = AgrConfig.load(config_path)

    if not config.dependencies:
        console.print("[yellow]No dependencies in agr.toml.[/yellow]")
        console.print("[dim]Run 'agr add <handle>' to add skills.[/dim]")
        return

    # Build table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Skill", style="cyan")
    table.add_column("Type")
    table.add_column("Status")

    for dep in config.dependencies:
        identifier = dep.identifier

        # Determine display name and status
        if dep.is_local:
            display_name = dep.path or ""
            source = "local"
        else:
            display_name = dep.handle or ""
            source = "remote"

        # Check installation status
        try:
            handle = parse_handle(identifier)
            installed_name = handle.to_installed_name()
            is_installed = is_skill_installed(installed_name, repo_root)
            status = "[green]installed[/green]" if is_installed else "[yellow]not synced[/yellow]"
        except Exception:
            status = "[red]invalid[/red]"

        table.add_row(display_name, source, status)

    console.print(table)

    # Show config path
    console.print()
    console.print(f"[dim]Config: {config_path}[/dim]")
