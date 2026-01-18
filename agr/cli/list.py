"""List command for agr - show installed dependencies."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from agr.config import AgrConfig, Dependency, find_config
from agr.cli.common import get_base_path
from agr.github import get_username_from_git_remote

console = Console()

app = typer.Typer(
    help="List installed dependencies from agr.toml.",
)


def _find_repo_root() -> Path:
    """Find the repository root by looking for .git directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def _is_installed(dep: Dependency, base_path: Path, username: str) -> bool:
    """Check if a dependency is installed in .claude/."""
    type_to_subdir = {
        "skill": "skills",
        "command": "commands",
        "agent": "agents",
        "package": "packages",
    }
    subdir = type_to_subdir.get(dep.type, "skills")

    if dep.is_local and dep.path:
        # Local dependency - check if installed
        source_path = Path(dep.path)
        name = source_path.stem if source_path.is_file() else source_path.name

        if dep.type in ("skill", "package"):
            installed_path = base_path / subdir / username / name
            return installed_path.is_dir()
        else:
            installed_path = base_path / subdir / username / f"{name}.md"
            return installed_path.is_file()

    elif dep.is_remote and dep.handle:
        # Remote dependency - parse handle and check
        parts = dep.handle.split("/")
        if len(parts) >= 2:
            remote_username = parts[0]
            name = parts[-1]

            if dep.type == "skill":
                installed_path = base_path / subdir / remote_username / name
                return installed_path.is_dir() and (installed_path / "SKILL.md").exists()
            else:
                installed_path = base_path / subdir / remote_username / f"{name}.md"
                return installed_path.is_file()

    return False


def _format_table(
    deps: list[Dependency],
    base_path: Path,
    username: str,
) -> Table:
    """Format dependencies as a rich table."""
    table = Table(show_header=True, header_style="bold")
    table.add_column("Source", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Handle/Path", style="white")
    table.add_column("Status", style="green")

    for dep in deps:
        source = "local" if dep.is_local else "remote"
        identifier = dep.path if dep.is_local else dep.handle
        installed = _is_installed(dep, base_path, username)
        status = "[green]installed[/green]" if installed else "[red]not installed[/red]"

        table.add_row(source, dep.type, identifier or "", status)

    return table


def _format_simple(
    deps: list[Dependency],
    base_path: Path,
    username: str,
) -> str:
    """Format dependencies as simple text."""
    lines = []
    for dep in deps:
        identifier = dep.path if dep.is_local else dep.handle
        installed = _is_installed(dep, base_path, username)
        status = "installed" if installed else "not installed"
        lines.append(f"{identifier} ({dep.type}) - {status}")
    return "\n".join(lines)


def _format_json(
    deps: list[Dependency],
    base_path: Path,
    username: str,
) -> str:
    """Format dependencies as JSON."""
    data = []
    for dep in deps:
        installed = _is_installed(dep, base_path, username)
        entry = {
            "type": dep.type,
            "source": "local" if dep.is_local else "remote",
            "installed": installed,
        }
        if dep.path:
            entry["path"] = dep.path
        if dep.handle:
            entry["handle"] = dep.handle
        data.append(entry)
    return json.dumps(data, indent=2)


@app.callback(invoke_without_command=True)
def list_dependencies(
    ctx: typer.Context,
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: table, simple, or json",
        ),
    ] = "table",
    local_only: Annotated[
        bool,
        typer.Option(
            "--local",
            help="Only show local dependencies",
        ),
    ] = False,
    remote_only: Annotated[
        bool,
        typer.Option(
            "--remote",
            help="Only show remote dependencies",
        ),
    ] = False,
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Check installation in ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
) -> None:
    """List all dependencies from agr.toml with their install status.

    Shows both local path dependencies and remote GitHub dependencies.

    Examples:
      agr list                  # Show all dependencies as table
      agr list --format json    # Output as JSON
      agr list --local          # Show only local dependencies
      agr list --remote         # Show only remote dependencies
    """
    config_path = find_config()
    if not config_path:
        console.print("[dim]No agr.toml found. Nothing to list.[/dim]")
        console.print("[dim]Use 'agr add' to add dependencies first.[/dim]")
        return

    config = AgrConfig.load(config_path)

    if not config.dependencies:
        console.print("[dim]No dependencies in agr.toml.[/dim]")
        console.print("[dim]Use 'agr add' to add dependencies.[/dim]")
        return

    # Filter dependencies
    deps = config.dependencies
    if local_only:
        deps = config.get_local_dependencies()
    elif remote_only:
        deps = config.get_remote_dependencies()

    if not deps:
        console.print("[dim]No matching dependencies found.[/dim]")
        return

    # Get base path and username for install status check
    base_path = get_base_path(global_install)
    repo_root = _find_repo_root()
    username = get_username_from_git_remote(repo_root) or "local"

    # Format output
    if format == "json":
        console.print(_format_json(deps, base_path, username))
    elif format == "simple":
        console.print(_format_simple(deps, base_path, username))
    else:
        table = _format_table(deps, base_path, username)
        console.print(table)

    # Summary
    total = len(deps)
    installed = sum(1 for d in deps if _is_installed(d, base_path, username))
    console.print(f"\n[dim]{installed}/{total} installed[/dim]")
