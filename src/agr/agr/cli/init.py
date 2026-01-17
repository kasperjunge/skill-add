"""Init subcommand for agr - create new resources and repos."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from agr.github import check_gh_cli, create_github_repo, get_github_username, repo_exists
from agr.scaffold import (
    create_agent_resources_repo,
    init_git,
    scaffold_repo,
    write_gitignore,
    write_readme,
    write_starter_agent,
    write_starter_command,
    write_starter_skill,
)

console = Console()

app = typer.Typer(
    help="Create new agent resources or repositories.",
    invoke_without_command=True,
)


def _create_convention_structure(base_path: Path) -> list[Path]:
    """Create the convention directory structure for local authoring.

    Creates:
    - skills/
    - commands/
    - agents/
    - packages/

    Args:
        base_path: Directory to create structure in

    Returns:
        List of created directories
    """
    dirs = [
        base_path / "skills",
        base_path / "commands",
        base_path / "agents",
        base_path / "packages",
    ]
    created = []
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(d)
    return created


@app.callback()
def init_callback(
    ctx: typer.Context,
) -> None:
    """Create convention directory structure for local resource authoring.

    When called without a subcommand, creates the skills/, commands/, agents/,
    and packages/ directories for local resource authoring.

    With subcommands:
      agr init skill <name>    Create a new skill scaffold
      agr init command <name>  Create a new command scaffold
      agr init agent <name>    Create a new agent scaffold
      agr init package <name>  Create a new package scaffold
      agr init repo [name]     Create a full agent-resources repository
    """
    # Only run if no subcommand was invoked
    if ctx.invoked_subcommand is None:
        base_path = Path.cwd()

        created = _create_convention_structure(base_path)

        if created:
            console.print("[green]Created authoring directories:[/green]")
            for d in created:
                console.print(f"  {d.relative_to(base_path)}/")
            console.print("\nNext steps:")
            console.print("  agr init skill <name>    # Create a new skill")
            console.print("  agr init command <name>  # Create a new command")
            console.print("  agr init agent <name>    # Create a new agent")
            console.print("  agr init package <name>  # Create a new package")
            console.print("\nAfter creating resources, run:")
            console.print("  agr sync                 # Sync to .claude/")
        else:
            console.print("[dim]Authoring directories already exist.[/dim]")


@app.command("repo")
def init_repo(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the repository to create, or '.' for current directory",
            metavar="NAME",
        ),
    ] = "agent-resources",
    path: Annotated[
        Path | None,
        typer.Option(
            "--path",
            "-p",
            help="Custom path for the repository (default: ./<name>)",
        ),
    ] = None,
    github: Annotated[
        bool,
        typer.Option(
            "--github",
            "-g",
            help="Create a GitHub repository and push",
        ),
    ] = False,
) -> None:
    """Create a new agent-resources repository with starter content.

    Creates a directory structure with example skill, command, and agent files.

    Examples:
      agr init repo                          # Creates ./agent-resources/
      agr init repo my-resources             # Creates ./my-resources/
      agr init repo .                        # Initialize in current directory
      agr init repo agent-resources --github # Creates and pushes to GitHub
    """
    # Determine target path
    if name == ".":
        target_path = Path.cwd()
        # Use directory name for GitHub repo name
        name = target_path.name
    else:
        target_path = path or Path.cwd() / name

        if target_path.exists():
            console.print(f"[red]Error: Directory already exists: {target_path}[/red]")
            raise typer.Exit(1)

    # Check if .claude directory already exists
    claude_dir = target_path / ".claude"
    if claude_dir.exists():
        console.print(f"[red]Error: .claude directory already exists at {claude_dir}[/red]")
        raise typer.Exit(1)

    # Check GitHub CLI if --github flag is set
    if github:
        if not check_gh_cli():
            console.print(
                "[red]Error: GitHub CLI (gh) is not installed or not authenticated.[/red]\n"
                "Install it from https://cli.github.com/ and run 'gh auth login'"
            )
            raise typer.Exit(1)

        if repo_exists(name):
            console.print(f"[red]Error: GitHub repository '{name}' already exists.[/red]")
            raise typer.Exit(1)

    # Get GitHub username for README
    username = get_github_username() or "<username>"

    # Create the repository
    console.print(f"Creating agent-resources repository at {target_path}...")
    create_agent_resources_repo(target_path, username)

    # Initialize git
    if init_git(target_path):
        console.print("[green]Initialized git repository[/green]")
    else:
        console.print("[yellow]Warning: Could not initialize git repository[/yellow]")

    # Create GitHub repo if requested
    if github:
        console.print("Creating GitHub repository...")
        repo_url = create_github_repo(target_path, name)
        if repo_url:
            console.print(f"[green]Created and pushed to {repo_url}[/green]")
            console.print(f"\nOthers can now install your resources:")
            console.print(f"  agr add skill {username}/hello-world")
            console.print(f"  agr add command {username}/hello")
            console.print(f"  agr add agent {username}/hello-agent")
        else:
            console.print("[yellow]Warning: Could not create GitHub repository[/yellow]")
    else:
        console.print(f"\n[green]Created agent-resources repository at {target_path}[/green]")
        console.print("\nNext steps:")
        console.print(f"  cd {target_path}")
        console.print("  git remote add origin <your-repo-url>")
        console.print("  git push -u origin main")


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
      agr init skill my-skill --legacy     # Creates ./.claude/skills/my-skill/SKILL.md
      agr init skill code-reviewer --path ./custom/path/
    """
    if path:
        target_path = path
    elif legacy:
        target_path = Path.cwd() / ".claude" / "skills" / name
    else:
        target_path = Path.cwd() / "skills" / name

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
      agr init command my-command --legacy  # Creates ./.claude/commands/my-command.md
      agr init command deploy --path ./custom/path/
    """
    if path:
        target_path = path
    elif legacy:
        target_path = Path.cwd() / ".claude" / "commands"
    else:
        target_path = Path.cwd() / "commands"

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
      agr init agent my-agent --legacy  # Creates ./.claude/agents/my-agent.md
      agr init agent test-writer --path ./custom/path/
    """
    if path:
        target_path = path
    elif legacy:
        target_path = Path.cwd() / ".claude" / "agents"
    else:
        target_path = Path.cwd() / "agents"

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
