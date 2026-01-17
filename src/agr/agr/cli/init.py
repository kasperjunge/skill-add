"""Init subcommand for agr - create new resources and repos."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console


console = Console()

app = typer.Typer(
    help="Create new agent resources or repositories.",
    invoke_without_command=True,
)

# Convention directory names for local authoring
AUTHORING_DIRS = ["skills", "commands", "agents", "packages"]


def _create_convention_structure(base_path: Path) -> list[Path]:
    """Create the convention directory structure for local authoring."""
    created = []
    for dirname in AUTHORING_DIRS:
        dir_path = base_path / dirname
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_path)
    return created


def _extract_name_and_path(name: str, path: Path | None) -> tuple[str, Path | None]:
    """Extract name and path when name contains path separators.

    If name contains '/' and path is None, split the name to extract
    the actual resource name and infer the path.

    Examples:
        'skills/my-skill' -> ('my-skill', Path('skills/my-skill'))
        './skills/my-skill' -> ('my-skill', Path('./skills/my-skill'))
        'my-skill' -> ('my-skill', None)

    Returns:
        Tuple of (extracted_name, inferred_path)
    """
    if "/" in name and path is None:
        given_path = Path(name)
        return given_path.name, given_path
    return name, path


def _get_resource_target_path(
    name: str,
    custom_path: Path | None,
    legacy: bool,
    resource_type: str,
    is_directory: bool = False,
) -> Path:
    """Get the target path for a resource scaffold.

    Args:
        name: Resource name
        custom_path: User-specified custom path, if any
        legacy: If True, use .claude/ path
        resource_type: The type directory (skills, commands, agents)
        is_directory: If True, resource is a directory (skills), else a file

    Returns:
        Target path for the resource
    """
    if custom_path:
        return custom_path
    if legacy:
        base = Path.cwd() / ".claude" / resource_type
    else:
        base = Path.cwd() / resource_type

    if is_directory:
        return base / name
    return base


@app.callback(invoke_without_command=True)
def init_callback(ctx: typer.Context) -> None:
    """Initialize agr for the current project.

    When called without a subcommand, creates agr.toml and convention directories.
    Use subcommands to create specific resource scaffolds.

    Subcommands:
      agr init skill <name>    Create a new skill scaffold
      agr init command <name>  Create a new command scaffold
      agr init agent <name>    Create a new agent scaffold
      agr init package <name>  Create a new package scaffold
    """
    if ctx.invoked_subcommand is None:
        from agr.config import AgrConfig

        config_path = Path.cwd() / "agr.toml"
        if config_path.exists():
            console.print("[yellow]agr.toml already exists[/yellow]")
        else:
            config = AgrConfig()
            config.save(config_path)
            console.print("[green]Created agr.toml[/green]")

        created = _create_convention_structure(Path.cwd())
        if created:
            for d in created:
                console.print(f"[green]Created {d.name}/[/green]")

        console.print("\nNext steps:")
        console.print("  agr init skill <name>    Create a skill")
        console.print("  agr init command <name>  Create a command")
        console.print("  agr add ./skills/myskill Add a resource")


@app.command("skill")
def init_skill(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the skill to create",
            metavar="NAME",
        ),
    ],
    path: Annotated[
        Path | None,
        typer.Option(
            "--path",
            "-p",
            help="Custom path (default: ./skills/<name>/)",
        ),
    ] = None,
    legacy: Annotated[
        bool,
        typer.Option(
            "--legacy",
            help="Create in .claude/skills/ instead of skills/ (old behavior)",
        ),
    ] = False,
) -> None:
    """Create a new skill scaffold in authoring path.

    By default, creates skills in ./skills/ for local authoring.
    Use --legacy to create in ./.claude/skills/ (old behavior).

    Examples:
      agr init skill my-skill              # Creates ./skills/my-skill/SKILL.md
      agr init skill skills/my-skill       # Creates ./skills/my-skill/SKILL.md
      agr init skill my-skill --legacy     # Creates ./.claude/skills/my-skill/SKILL.md
      agr init skill code-reviewer --path ./custom/path/
    """
    # Handle path in name argument
    name, path = _extract_name_and_path(name, path)
    target_path = _get_resource_target_path(name, path, legacy, "skills", is_directory=True)
    skill_file = target_path / "SKILL.md"

    if skill_file.exists():
        console.print(f"[red]Error: Skill already exists at {skill_file}[/red]")
        raise typer.Exit(1)

    target_path.mkdir(parents=True, exist_ok=True)

    skill_content = f"""\
---
name: {name}
description: Description of what this skill does
---

# {name.replace('-', ' ').title()} Skill

Describe what this skill does and when Claude should apply it.

## When to Use

Describe the situations when this skill should be applied.

## Instructions

Provide specific instructions for Claude to follow.
"""
    skill_file.write_text(skill_content)
    console.print(f"[green]Created skill at {skill_file}[/green]")

    if not legacy and not path:
        console.print("[dim]Run 'agr sync' to install to .claude/[/dim]")


@app.command("command")
def init_command(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the command to create (without leading slash)",
            metavar="NAME",
        ),
    ],
    path: Annotated[
        Path | None,
        typer.Option(
            "--path",
            "-p",
            help="Custom path (default: ./commands/<name>.md)",
        ),
    ] = None,
    legacy: Annotated[
        bool,
        typer.Option(
            "--legacy",
            help="Create in .claude/commands/ instead of commands/ (old behavior)",
        ),
    ] = False,
) -> None:
    """Create a new slash command scaffold in authoring path.

    By default, creates commands in ./commands/ for local authoring.
    Use --legacy to create in ./.claude/commands/ (old behavior).

    Examples:
      agr init command my-command           # Creates ./commands/my-command.md
      agr init command commands/my-command  # Creates ./commands/my-command.md
      agr init command my-command --legacy  # Creates ./.claude/commands/my-command.md
      agr init command deploy --path ./custom/path/
    """
    # Handle path in name argument
    name, path = _extract_name_and_path(name, path)
    # For commands, if path was extracted, use parent dir since command is a file
    if path is not None:
        path = path.parent
    target_path = _get_resource_target_path(name, path, legacy, "commands")
    command_file = target_path / f"{name}.md"

    if command_file.exists():
        console.print(f"[red]Error: Command already exists at {command_file}[/red]")
        raise typer.Exit(1)

    target_path.mkdir(parents=True, exist_ok=True)

    command_content = f"""\
---
description: Description of /{name} command
---

When the user runs /{name}, do the following:

1. First step
2. Second step
3. Third step

Provide clear, actionable instructions for what Claude should do.
"""
    command_file.write_text(command_content)
    console.print(f"[green]Created command at {command_file}[/green]")

    if not legacy and not path:
        console.print("[dim]Run 'agr sync' to install to .claude/[/dim]")


@app.command("agent")
def init_agent(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the agent to create",
            metavar="NAME",
        ),
    ],
    path: Annotated[
        Path | None,
        typer.Option(
            "--path",
            "-p",
            help="Custom path (default: ./agents/<name>.md)",
        ),
    ] = None,
    legacy: Annotated[
        bool,
        typer.Option(
            "--legacy",
            help="Create in .claude/agents/ instead of agents/ (old behavior)",
        ),
    ] = False,
) -> None:
    """Create a new sub-agent scaffold in authoring path.

    By default, creates agents in ./agents/ for local authoring.
    Use --legacy to create in ./.claude/agents/ (old behavior).

    Examples:
      agr init agent my-agent           # Creates ./agents/my-agent.md
      agr init agent agents/my-agent    # Creates ./agents/my-agent.md
      agr init agent my-agent --legacy  # Creates ./.claude/agents/my-agent.md
      agr init agent test-writer --path ./custom/path/
    """
    # Handle path in name argument
    name, path = _extract_name_and_path(name, path)
    # For agents, if path was extracted, use parent dir since agent is a file
    if path is not None:
        path = path.parent
    target_path = _get_resource_target_path(name, path, legacy, "agents")
    agent_file = target_path / f"{name}.md"

    if agent_file.exists():
        console.print(f"[red]Error: Agent already exists at {agent_file}[/red]")
        raise typer.Exit(1)

    target_path.mkdir(parents=True, exist_ok=True)

    agent_content = f"""\
---
description: Description of the {name} sub-agent
---

You are a specialized sub-agent for {name.replace('-', ' ')}.

## Purpose

Describe the specific purpose and capabilities of this agent.

## Instructions

When invoked, you should:

1. First action
2. Second action
3. Third action

## Constraints

- Constraint 1
- Constraint 2
"""
    agent_file.write_text(agent_content)
    console.print(f"[green]Created agent at {agent_file}[/green]")

    if not legacy and not path:
        console.print("[dim]Run 'agr sync' to install to .claude/[/dim]")


@app.command("package")
def init_package(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the package to create",
            metavar="NAME",
        ),
    ],
    path: Annotated[
        Path | None,
        typer.Option(
            "--path",
            "-p",
            help="Custom path (default: ./packages/<name>/)",
        ),
    ] = None,
) -> None:
    """Create a new package scaffold with skills/, commands/, agents/ subdirs.

    Packages group related resources together under a single namespace.

    Examples:
      agr init package my-toolkit           # Creates ./packages/my-toolkit/
      agr init package utils --path ./libs/
    """
    target_path = path or (Path.cwd() / "packages" / name)

    if target_path.exists():
        console.print(f"[red]Error: Package directory already exists at {target_path}[/red]")
        raise typer.Exit(1)

    # Create package structure
    target_path.mkdir(parents=True, exist_ok=True)
    (target_path / "skills").mkdir()
    (target_path / "commands").mkdir()
    (target_path / "agents").mkdir()

    console.print(f"[green]Created package at {target_path}/[/green]")
    console.print(f"  {target_path}/skills/")
    console.print(f"  {target_path}/commands/")
    console.print(f"  {target_path}/agents/")
    console.print("\nNext steps:")
    console.print(f"  agr init skill <name> --path {target_path}/skills/<name>")
    console.print(f"  agr init command <name> --path {target_path}/commands/")
    console.print(f"  agr init agent <name> --path {target_path}/agents/")
    console.print("\nAfter creating resources, run:")
    console.print("  agr sync                 # Sync to .claude/")
