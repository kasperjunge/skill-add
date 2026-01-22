"""agr init command implementation."""

from pathlib import Path

from rich.console import Console

from agr.config import AgrConfig, find_config
from agr.skill import create_skill_scaffold

console = Console()


def init_config(path: Path | None = None) -> tuple[Path, bool]:
    """Initialize agr.toml if it doesn't exist.

    Args:
        path: Directory to create agr.toml in (defaults to cwd)

    Returns:
        Tuple of (config_path, created). created=False if already existed.
    """
    base = path or Path.cwd()
    config_path = base / "agr.toml"

    # Check if config already exists anywhere up the tree
    existing = find_config(base)
    if existing:
        return existing, False

    # Create new config
    config = AgrConfig()
    config.save(config_path)

    return config_path, True


def init_skill(name: str, base_dir: Path | None = None) -> Path:
    """Initialize a new skill scaffold.

    Args:
        name: Name of the skill
        base_dir: Directory to create skill in (defaults to cwd)

    Returns:
        Path to created skill directory

    Raises:
        ValueError: If name is invalid
        FileExistsError: If directory already exists
    """
    return create_skill_scaffold(name, base_dir)


def run_init(skill_name: str | None = None) -> None:
    """Run the init command.

    Args:
        skill_name: If provided, creates a skill scaffold instead of agr.toml
    """
    if skill_name:
        # Create skill scaffold
        try:
            skill_path = init_skill(skill_name)
            console.print(f"[green]Created skill scaffold:[/green] {skill_path}")
            console.print(f"  [dim]Edit {skill_path}/SKILL.md to customize your skill[/dim]")
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise SystemExit(1)
        except FileExistsError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise SystemExit(1)
    else:
        # Create agr.toml
        config_path, created = init_config()
        if created:
            console.print(f"[green]Created:[/green] {config_path}")
        else:
            console.print(f"[yellow]Already exists:[/yellow] {config_path}")
