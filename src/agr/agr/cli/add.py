"""Add subcommand for agr - add dependencies to agr.toml."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from agr.cli.common import get_or_create_config, handle_add_bundle, handle_add_resource
from agr.config import CONFIG_FILENAME
from agr.fetcher import ResourceType
from agr.resolver import resolve_ref

console = Console()

app = typer.Typer(
    help="Add dependencies to agr.toml or install resources directly.",
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def add_dependency(
    ctx: typer.Context,
    ref: Annotated[
        Optional[str],
        typer.Argument(
            help="Reference to add: <name>, <username>/<name>, or <username>/<repo>/<name>",
            metavar="REFERENCE",
        ),
    ] = None,
    package: Annotated[
        bool,
        typer.Option(
            "--package",
            "-p",
            help="Mark this dependency as a package (installs all resources).",
        ),
    ] = False,
    resource_type: Annotated[
        Optional[str],
        typer.Option(
            "--type",
            "-t",
            help="Resource type: skill, command, or agent (for disambiguation).",
        ),
    ] = None,
    to_package: Annotated[
        Optional[str],
        typer.Option(
            "--to",
            help="Add a local path to a package definition.",
        ),
    ] = None,
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite existing resource if it exists (for direct install).",
        ),
    ] = False,
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Install to ~/.claude/ instead of ./.claude/ (for direct install).",
        ),
    ] = False,
    direct: Annotated[
        bool,
        typer.Option(
            "--direct",
            "-d",
            help="Install directly without adding to agr.toml (legacy mode).",
        ),
    ] = False,
) -> None:
    """Add a dependency to agr.toml.

    By default, adds the reference to agr.toml [dependencies] section.
    Use `agr sync` to install all dependencies.

    REFERENCE formats:
      - name: installs from official index
      - username/name: installs from github.com/username/agent-resources
      - username/repo/name: installs from github.com/username/repo

    Examples:
      agr add commit                    # Add from official index
      agr add kasperjunge/hello-world   # Add from user's agent-resources
      agr add kasperjunge/commit --package  # Add as a package
      agr add kasperjunge/hello-world --type skill  # Disambiguate resource type
      agr add ./my-skill --to my-toolkit    # Add local path to package
      agr add kasperjunge/hello-world --direct  # Install directly (legacy)
    """
    # If a subcommand was invoked, skip the callback logic
    if ctx.invoked_subcommand is not None:
        return

    if ref is None:
        # Show help if no arguments
        console.print("[yellow]Usage: agr add <reference>[/yellow]")
        console.print()
        console.print("Reference formats:")
        console.print("  name                    - From official index")
        console.print("  username/name           - From user's agent-resources repo")
        console.print("  username/repo/name      - From user's custom repo")
        console.print()
        console.print("Options:")
        console.print("  --package, -p           - Mark as package (multiple resources)")
        console.print("  --type, -t <type>       - Resource type: skill, command, or agent")
        console.print("  --to <package>          - Add local path to a package definition")
        console.print("  --direct, -d            - Install directly without agr.toml")
        raise typer.Exit(0)

    # Handle --to for adding local paths to packages
    if to_package:
        _add_to_package(ref, to_package)
        return

    # Handle --direct for legacy direct installation
    if direct:
        _direct_install(ref, package, overwrite, global_install)
        return

    # Default: add to agr.toml
    _add_to_config(ref, package, resource_type)


VALID_TYPES = ("skill", "command", "agent")


def _add_to_config(ref: str, is_package: bool, resource_type: str | None = None) -> None:
    """Add a dependency to agr.toml."""
    try:
        # Validate resource type if provided
        if resource_type and resource_type not in VALID_TYPES:
            console.print(f"[red]Invalid type: {resource_type}[/red]")
            console.print(f"Valid types: {', '.join(VALID_TYPES)}")
            raise typer.Exit(1)

        # Type is not compatible with package
        if resource_type and is_package:
            console.print("[red]Cannot use --type with --package[/red]")
            console.print("[dim]Packages install all resource types from a directory[/dim]")
            raise typer.Exit(1)

        # Validate the reference format
        resolved = resolve_ref(ref, is_package)

        # Get or create config
        config = get_or_create_config()

        # Check if already exists
        if ref in config.dependencies:
            console.print(f"[yellow]Dependency '{ref}' already in {CONFIG_FILENAME}[/yellow]")
            return

        # Add to config
        config.add_dependency(ref, package=is_package, resource_type=resource_type)
        config.save()

        pkg_str = " (package)" if is_package else ""
        type_str = f" (type={resource_type})" if resource_type else ""
        console.print(f"[green]Added '{ref}'{pkg_str}{type_str} to {CONFIG_FILENAME}[/green]")
        console.print(f"[dim]Run 'agr sync' to install dependencies[/dim]")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


def _add_to_package(local_path: str, package_name: str) -> None:
    """Add a local path to a package definition."""
    path = Path(local_path)

    # Get or create config
    config = get_or_create_config()

    # Get or create the package
    if package_name not in config.packages:
        pkg = config.add_package(package_name)
        console.print(f"[dim]Created package '{package_name}'[/dim]")
    else:
        pkg = config.packages[package_name]

    # Determine resource type from path
    path_str = str(path)
    if "/skills/" in path_str or path_str.startswith("skills/") or path_str.endswith("/"):
        # Treat as skill pattern
        if local_path not in pkg.skills:
            pkg.skills.append(local_path)
            config.save()
            console.print(f"[green]Added '{local_path}' to package '{package_name}' skills[/green]")
        else:
            console.print(f"[yellow]'{local_path}' already in package '{package_name}'[/yellow]")
    elif "/commands/" in path_str or path_str.startswith("commands/"):
        if local_path not in pkg.commands:
            pkg.commands.append(local_path)
            config.save()
            console.print(f"[green]Added '{local_path}' to package '{package_name}' commands[/green]")
        else:
            console.print(f"[yellow]'{local_path}' already in package '{package_name}'[/yellow]")
    elif "/agents/" in path_str or path_str.startswith("agents/"):
        if local_path not in pkg.agents:
            pkg.agents.append(local_path)
            config.save()
            console.print(f"[green]Added '{local_path}' to package '{package_name}' agents[/green]")
        else:
            console.print(f"[yellow]'{local_path}' already in package '{package_name}'[/yellow]")
    else:
        # Default to skills for directories, could be enhanced with detection
        if local_path not in pkg.skills:
            pkg.skills.append(local_path)
            config.save()
            console.print(f"[green]Added '{local_path}' to package '{package_name}' (as skill pattern)[/green]")
        else:
            console.print(f"[yellow]'{local_path}' already in package '{package_name}'[/yellow]")


def _direct_install(ref: str, is_package: bool, overwrite: bool, global_install: bool) -> None:
    """Install a resource directly without agr.toml (legacy mode)."""
    if is_package:
        handle_add_bundle(ref, overwrite, global_install)
    else:
        # Try to detect type from reference or default to skill
        # For direct install, we need to use the legacy subcommands
        console.print("[yellow]For direct install, use: agr add skill/command/agent <ref>[/yellow]")
        console.print("[dim]Or remove --direct to add to agr.toml[/dim]")
        raise typer.Exit(1)


# Legacy subcommands for backward compatibility
@app.command("skill")
def add_skill(
    skill_ref: Annotated[
        str,
        typer.Argument(
            help="Skill reference: <username>/<skill-name> or <username>/<repo>/<skill-name>",
            metavar="REFERENCE",
        ),
    ],
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite existing skill if it exists.",
        ),
    ] = False,
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Install to ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
) -> None:
    """Add a skill from a GitHub repository (legacy direct install).

    REFERENCE format:
      - username/skill-name: installs from github.com/username/agent-resources
      - username/repo/skill-name: installs from github.com/username/repo

    Examples:
      agr add skill kasperjunge/hello-world
      agr add skill kasperjunge/my-repo/hello-world --global
    """
    handle_add_resource(skill_ref, ResourceType.SKILL, "skills", overwrite, global_install)


@app.command("command")
def add_command(
    command_ref: Annotated[
        str,
        typer.Argument(
            help="Command reference: <username>/<command-name> or <username>/<repo>/<command-name>",
            metavar="REFERENCE",
        ),
    ],
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite existing command if it exists.",
        ),
    ] = False,
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Install to ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
) -> None:
    """Add a slash command from a GitHub repository (legacy direct install).

    REFERENCE format:
      - username/command-name: installs from github.com/username/agent-resources
      - username/repo/command-name: installs from github.com/username/repo

    Examples:
      agr add command kasperjunge/hello
      agr add command kasperjunge/my-repo/hello --global
    """
    handle_add_resource(command_ref, ResourceType.COMMAND, "commands", overwrite, global_install)


@app.command("agent")
def add_agent(
    agent_ref: Annotated[
        str,
        typer.Argument(
            help="Agent reference: <username>/<agent-name> or <username>/<repo>/<agent-name>",
            metavar="REFERENCE",
        ),
    ],
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite existing agent if it exists.",
        ),
    ] = False,
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Install to ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
) -> None:
    """Add a sub-agent from a GitHub repository (legacy direct install).

    REFERENCE format:
      - username/agent-name: installs from github.com/username/agent-resources
      - username/repo/agent-name: installs from github.com/username/repo

    Examples:
      agr add agent kasperjunge/hello-agent
      agr add agent kasperjunge/my-repo/hello-agent --global
    """
    handle_add_resource(agent_ref, ResourceType.AGENT, "agents", overwrite, global_install)


@app.command("bundle")
def add_bundle(
    bundle_ref: Annotated[
        str,
        typer.Argument(
            help="Bundle reference: <username>/<bundle-name> or <username>/<repo>/<bundle-name>",
            metavar="REFERENCE",
        ),
    ],
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite existing resources if they exist.",
        ),
    ] = False,
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Install to ~/.claude/ instead of ./.claude/",
        ),
    ] = False,
) -> None:
    """Add a bundle of resources from a GitHub repository (legacy direct install).

    A bundle installs all skills, commands, and agents from a named directory.

    REFERENCE format:
      - username/bundle-name: installs from github.com/username/agent-resources
      - username/repo/bundle-name: installs from github.com/username/repo

    Bundle structure in source repo:
      .claude/skills/{bundle-name}/*/SKILL.md     -> skills
      .claude/commands/{bundle-name}/*.md         -> commands
      .claude/agents/{bundle-name}/*.md           -> agents

    Resources are installed with the bundle name as a prefix:
      .claude/skills/{bundle-name}/{skill-name}/
      .claude/commands/{bundle-name}/{command-name}.md
      .claude/agents/{bundle-name}/{agent-name}.md

    Examples:
      agr add bundle kasperjunge/productivity
      agr add bundle kasperjunge/my-repo/productivity --global
    """
    handle_add_bundle(bundle_ref, overwrite, global_install)
