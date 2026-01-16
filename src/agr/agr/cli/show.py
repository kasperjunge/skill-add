"""Show command for agr - display package and resource information."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from agr.cli.common import find_agr_toml, get_author_from_git, get_base_path
from agr.config import CONFIG_FILENAME, AgrConfig
from agr.detector import ResourceType, discover_package_resources
from agr.exceptions import ConfigNotFoundError, ConfigParseError

console = Console()

app = typer.Typer(
    help="Show package and resource information.",
    no_args_is_help=True,
)


@app.command("package")
def show_package(
    name: Annotated[
        str,
        typer.Argument(
            help="Package name to show",
            metavar="NAME",
        ),
    ],
) -> None:
    """Show contents of a package.

    Displays all skills, commands, and agents in the package.

    Examples:
      agr show package my-toolkit
    """
    # Find config
    config_path = find_agr_toml()
    if not config_path:
        console.print(f"[red]Error: {CONFIG_FILENAME} not found[/red]")
        raise typer.Exit(1)

    try:
        config = AgrConfig.load(config_path)
    except (ConfigNotFoundError, ConfigParseError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    if name not in config.packages:
        console.print(f"[red]Package '{name}' not found in {CONFIG_FILENAME}[/red]")
        console.print()
        if config.packages:
            console.print("[dim]Available packages:[/dim]")
            for pkg_name in config.packages:
                console.print(f"  - {pkg_name}")
        raise typer.Exit(1)

    package = config.packages[name]
    config_dir = config.path.parent

    # Display package info
    console.print(f"[bold cyan]Package: {name}[/bold cyan]")
    if package.description:
        console.print(f"[dim]{package.description}[/dim]")
    console.print()

    # Show patterns
    console.print("[bold]Patterns:[/bold]")
    if package.skills:
        console.print(f"  Skills: {', '.join(package.skills)}")
    if package.commands:
        console.print(f"  Commands: {', '.join(package.commands)}")
    if package.agents:
        console.print(f"  Agents: {', '.join(package.agents)}")

    if not package.skills and not package.commands and not package.agents:
        console.print("  [dim]No patterns defined[/dim]")
        return

    # Discover actual resources
    console.print()
    console.print("[bold]Discovered resources:[/bold]")

    resources = discover_package_resources(
        config_dir,
        skill_patterns=package.skills if package.skills else None,
        command_patterns=package.commands if package.commands else None,
        agent_patterns=package.agents if package.agents else None,
    )

    total = 0

    if resources[ResourceType.SKILL]:
        console.print(f"\n  [cyan]Skills ({len(resources[ResourceType.SKILL])}):[/cyan]")
        for skill in resources[ResourceType.SKILL]:
            console.print(f"    - {skill.name}")
            total += 1

    if resources[ResourceType.COMMAND]:
        console.print(f"\n  [cyan]Commands ({len(resources[ResourceType.COMMAND])}):[/cyan]")
        for cmd in resources[ResourceType.COMMAND]:
            console.print(f"    - {cmd.stem}")
            total += 1

    if resources[ResourceType.AGENT]:
        console.print(f"\n  [cyan]Agents ({len(resources[ResourceType.AGENT])}):[/cyan]")
        for agent in resources[ResourceType.AGENT]:
            console.print(f"    - {agent.stem}")
            total += 1

    if total == 0:
        console.print("  [yellow]No resources found matching patterns[/yellow]")
    else:
        console.print(f"\n[dim]Total: {total} resources[/dim]")


@app.command("packages")
def show_packages() -> None:
    """List all packages in agr.toml.

    Examples:
      agr show packages
    """
    config_path = find_agr_toml()
    if not config_path:
        console.print(f"[red]Error: {CONFIG_FILENAME} not found[/red]")
        raise typer.Exit(1)

    try:
        config = AgrConfig.load(config_path)
    except (ConfigNotFoundError, ConfigParseError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    if not config.packages:
        console.print("[yellow]No packages defined in agr.toml[/yellow]")
        console.print("[dim]Create one with: agr new package <name>[/dim]")
        return

    table = Table(title="Packages")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Skills", justify="right")
    table.add_column("Commands", justify="right")
    table.add_column("Agents", justify="right")

    for name, package in config.packages.items():
        table.add_row(
            name,
            package.description or "-",
            str(len(package.skills)),
            str(len(package.commands)),
            str(len(package.agents)),
        )

    console.print(table)


@app.command("deps")
def show_dependencies() -> None:
    """List all dependencies in agr.toml.

    Examples:
      agr show deps
    """
    config_path = find_agr_toml()
    if not config_path:
        console.print(f"[red]Error: {CONFIG_FILENAME} not found[/red]")
        raise typer.Exit(1)

    try:
        config = AgrConfig.load(config_path)
    except (ConfigNotFoundError, ConfigParseError) as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    if not config.dependencies:
        console.print("[yellow]No dependencies in agr.toml[/yellow]")
        console.print("[dim]Add one with: agr add <ref>[/dim]")
        return

    table = Table(title="Dependencies")
    table.add_column("Reference", style="cyan")
    table.add_column("Type")

    for ref, dep in config.dependencies.items():
        dep_type = "package" if dep.package else "resource"
        table.add_row(ref, dep_type)

    console.print(table)


@app.command("installed")
def show_installed(
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Show ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
) -> None:
    """List all installed resources.

    Examples:
      agr show installed
      agr show installed --global
    """
    dest_base = get_base_path(global_install)

    if not dest_base.exists():
        console.print(f"[yellow]No .claude directory found at {dest_base}[/yellow]")
        return

    console.print(f"[bold]Installed resources in {dest_base}[/bold]")

    total = 0

    for subdir in ["skills", "commands", "agents"]:
        subdir_path = dest_base / subdir
        if not subdir_path.is_dir():
            continue

        resources: list[str] = []

        for author_dir in sorted(subdir_path.iterdir()):
            if not author_dir.is_dir():
                continue

            for resource in sorted(author_dir.iterdir()):
                if resource.is_dir():
                    if (resource / "SKILL.md").exists():
                        resources.append(f"{author_dir.name}/{resource.name}")
                    else:
                        # Package directory
                        for item in sorted(resource.iterdir()):
                            if item.is_dir() and (item / "SKILL.md").exists():
                                resources.append(f"{author_dir.name}/{resource.name}/{item.name}")
                            elif item.suffix == ".md":
                                resources.append(f"{author_dir.name}/{resource.name}/{item.stem}")
                elif resource.suffix == ".md":
                    resources.append(f"{author_dir.name}/{resource.stem}")

        if resources:
            console.print(f"\n[cyan]{subdir.capitalize()} ({len(resources)}):[/cyan]")
            for res in resources:
                console.print(f"  {res}")
            total += len(resources)

    if total == 0:
        console.print("[dim]No resources installed[/dim]")
    else:
        console.print(f"\n[dim]Total: {total} resources[/dim]")
