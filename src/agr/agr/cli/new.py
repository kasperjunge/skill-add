"""New command for agr - create new resources and packages."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from agr.cli.common import get_or_create_config
from agr.config import CONFIG_FILENAME

console = Console()

app = typer.Typer(
    help="Create new resources and packages.",
    no_args_is_help=True,
)


@app.command("package")
def new_package(
    name: Annotated[
        str,
        typer.Argument(
            help="Name for the new package",
            metavar="NAME",
        ),
    ],
    description: Annotated[
        str,
        typer.Option(
            "--description",
            "-d",
            help="Description for the package",
        ),
    ] = "",
    scaffold: Annotated[
        bool,
        typer.Option(
            "--scaffold",
            "-s",
            help="Create directory structure for the package",
        ),
    ] = False,
) -> None:
    """Create a new package definition.

    Creates a [package.NAME] entry in agr.toml and optionally
    scaffolds the directory structure.

    Examples:
      agr new package my-toolkit
      agr new package my-toolkit --description "My useful tools"
      agr new package my-toolkit --scaffold
    """
    # Get or create config
    config = get_or_create_config()

    # Check if package already exists
    if name in config.packages:
        console.print(f"[yellow]Package '{name}' already exists in {CONFIG_FILENAME}[/yellow]")
        raise typer.Exit(1)

    # Create package in config
    pkg = config.add_package(name, description)
    config.save()

    console.print(f"[green]Created package '{name}' in {CONFIG_FILENAME}[/green]")

    # Scaffold directories if requested
    if scaffold:
        base_dir = config.path.parent / name
        _scaffold_package(base_dir, name)

        # Update package patterns
        pkg.skills = [f"./{name}/skills/*/"]
        pkg.commands = [f"./{name}/commands/*.md"]
        pkg.agents = [f"./{name}/agents/*.md"]
        config.save()

        console.print(f"[green]Created directory structure at {base_dir}[/green]")

    console.print()
    console.print("[dim]Next steps:[/dim]")
    if scaffold:
        console.print(f"  1. Add skills to ./{name}/skills/")
        console.print(f"  2. Add commands to ./{name}/commands/")
        console.print(f"  3. Add agents to ./{name}/agents/")
    else:
        console.print("  1. Add resources with: agr add ./path --to " + name)
    console.print("  4. Run 'agr sync' to build the package")


def _scaffold_package(base_dir: Path, name: str) -> None:
    """Create directory structure for a package."""
    # Create subdirectories
    skills_dir = base_dir / "skills"
    commands_dir = base_dir / "commands"
    agents_dir = base_dir / "agents"

    skills_dir.mkdir(parents=True, exist_ok=True)
    commands_dir.mkdir(parents=True, exist_ok=True)
    agents_dir.mkdir(parents=True, exist_ok=True)

    # Create example skill
    example_skill_dir = skills_dir / "example-skill"
    example_skill_dir.mkdir(exist_ok=True)

    skill_md = example_skill_dir / "SKILL.md"
    if not skill_md.exists():
        skill_md.write_text(f"""# Example Skill

This is an example skill in the {name} package.

## Usage

Describe how to use this skill.

## Configuration

Any configuration options.
""")

    # Create example command
    example_command = commands_dir / "example-command.md"
    if not example_command.exists():
        example_command.write_text(f"""# Example Command

Example slash command for the {name} package.

## Instructions

When this command is invoked, do the following:

1. First step
2. Second step
3. Third step
""")

    # Create gitkeep in agents (usually empty initially)
    gitkeep = agents_dir / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("")


@app.command("skill")
def new_skill(
    name: Annotated[
        str,
        typer.Argument(
            help="Name for the new skill",
            metavar="NAME",
        ),
    ],
    package: Annotated[
        str | None,
        typer.Option(
            "--to",
            help="Add to a package",
        ),
    ] = None,
) -> None:
    """Create a new skill scaffold.

    Creates a skill directory with SKILL.md template.

    Examples:
      agr new skill my-skill
      agr new skill my-skill --to my-toolkit
    """
    config = get_or_create_config()
    config_dir = config.path.parent

    if package:
        # Create in package directory
        skill_dir = config_dir / package / "skills" / name
    else:
        # Create in current directory
        skill_dir = config_dir / "skills" / name

    if skill_dir.exists():
        console.print(f"[yellow]Skill '{name}' already exists at {skill_dir}[/yellow]")
        raise typer.Exit(1)

    skill_dir.mkdir(parents=True, exist_ok=True)

    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(f"""# {name}

Description of what this skill does.

## Usage

How to use this skill.

## Configuration

Any configuration options.
""")

    console.print(f"[green]Created skill at {skill_dir}[/green]")

    if package and package in config.packages:
        # Already tracked
        console.print(f"[dim]Skill is part of package '{package}'[/dim]")
    else:
        console.print("[dim]Run 'agr sync' to install to .claude/[/dim]")


@app.command("command")
def new_command(
    name: Annotated[
        str,
        typer.Argument(
            help="Name for the new command",
            metavar="NAME",
        ),
    ],
    package: Annotated[
        str | None,
        typer.Option(
            "--to",
            help="Add to a package",
        ),
    ] = None,
) -> None:
    """Create a new command scaffold.

    Creates a command .md file with template.

    Examples:
      agr new command my-cmd
      agr new command my-cmd --to my-toolkit
    """
    config = get_or_create_config()
    config_dir = config.path.parent

    if package:
        command_file = config_dir / package / "commands" / f"{name}.md"
    else:
        command_file = config_dir / "commands" / f"{name}.md"

    if command_file.exists():
        console.print(f"[yellow]Command '{name}' already exists at {command_file}[/yellow]")
        raise typer.Exit(1)

    command_file.parent.mkdir(parents=True, exist_ok=True)

    command_file.write_text(f"""# {name}

Description of what this command does.

## Instructions

When this command is invoked:

1. First, do this
2. Then, do that
3. Finally, complete

## Examples

Example usage or output.
""")

    console.print(f"[green]Created command at {command_file}[/green]")

    if package and package in config.packages:
        console.print(f"[dim]Command is part of package '{package}'[/dim]")
    else:
        console.print("[dim]Run 'agr sync' to install to .claude/[/dim]")


@app.command("agent")
def new_agent(
    name: Annotated[
        str,
        typer.Argument(
            help="Name for the new agent",
            metavar="NAME",
        ),
    ],
    package: Annotated[
        str | None,
        typer.Option(
            "--to",
            help="Add to a package",
        ),
    ] = None,
) -> None:
    """Create a new agent scaffold.

    Creates an agent .md file with template.

    Examples:
      agr new agent my-agent
      agr new agent my-agent --to my-toolkit
    """
    config = get_or_create_config()
    config_dir = config.path.parent

    if package:
        agent_file = config_dir / package / "agents" / f"{name}.md"
    else:
        agent_file = config_dir / "agents" / f"{name}.md"

    if agent_file.exists():
        console.print(f"[yellow]Agent '{name}' already exists at {agent_file}[/yellow]")
        raise typer.Exit(1)

    agent_file.parent.mkdir(parents=True, exist_ok=True)

    agent_file.write_text(f"""# {name}

Description of this agent's purpose and capabilities.

## Role

Define the agent's role and responsibilities.

## Instructions

When acting as this agent:

1. Understand the context
2. Take appropriate actions
3. Report results

## Constraints

Any limitations or guidelines.
""")

    console.print(f"[green]Created agent at {agent_file}[/green]")

    if package and package in config.packages:
        console.print(f"[dim]Agent is part of package '{package}'[/dim]")
    else:
        console.print("[dim]Run 'agr sync' to install to .claude/[/dim]")
