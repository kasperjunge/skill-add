"""Add subcommand for agr - install resources from GitHub."""

from pathlib import Path
from typing import Annotated, List, Optional

import typer
from rich.console import Console

from agr.cli.common import handle_add_bundle, handle_add_resource, handle_add_unified
from agr.config import AgrConfig, LocalResourceSpec, get_or_create_config
from agr.fetcher import ResourceType

console = Console()

# Deprecated subcommand names
DEPRECATED_SUBCOMMANDS = {"skill", "command", "agent", "bundle"}


def extract_options_from_args(
    args: list[str] | None,
    explicit_type: str | None,
    explicit_to: str | None,
) -> tuple[list[str], str | None, str | None]:
    """
    Extract --type/-t and --to options from args list if present.

    When options appear after the resource reference, Typer captures them
    as part of the variadic args list. This function extracts them.

    Args:
        args: The argument list (may contain --type/-t and --to)
        explicit_type: The resource_type value from Typer (may be None if type was in args)
        explicit_to: The to_package value from Typer (may be None if --to was in args)

    Returns:
        Tuple of (cleaned_args, resource_type, to_package)
    """
    if not args:
        return [], explicit_type, explicit_to

    cleaned_args = []
    resource_type = explicit_type
    to_package = explicit_to
    i = 0
    while i < len(args):
        if args[i] in ("--type", "-t") and i + 1 < len(args) and resource_type is None:
            resource_type = args[i + 1]
            i += 2  # Skip both --type and its value
        elif args[i] == "--to" and i + 1 < len(args) and to_package is None:
            to_package = args[i + 1]
            i += 2  # Skip both --to and its value
        else:
            cleaned_args.append(args[i])
            i += 1

    return cleaned_args, resource_type, to_package

def _is_local_path(ref: str) -> bool:
    """Check if a reference is a local path."""
    return ref.startswith("./") or ref.startswith("/") or ref.startswith("../")


def _detect_local_type(path: Path) -> str | None:
    """Detect resource type from a local path.

    Returns:
        "skill", "command", "agent", or None if unknown
    """
    if path.is_dir():
        if (path / "SKILL.md").exists():
            return "skill"
    elif path.is_file() and path.suffix == ".md":
        # Could be command or agent - default to command
        return "command"
    return None


def handle_add_local(
    local_path: str,
    resource_type: str | None,
    package: str | None = None,
) -> None:
    """Handle adding a local resource to agr.toml.

    Args:
        local_path: Path to the local resource
        resource_type: Explicit type (skill, command, agent)
        package: Optional package to add this resource to
    """
    path = Path(local_path)

    # Verify path exists
    if not path.exists():
        console.print(f"[red]Error: Path does not exist: {path}[/red]")
        raise typer.Exit(1)

    # Auto-detect type if not specified
    if not resource_type:
        resource_type = _detect_local_type(path)
        if not resource_type:
            console.print(
                f"[red]Error: Could not detect resource type for '{path}'.[/red]\n"
                "Use --type to specify: skill, command, or agent"
            )
            raise typer.Exit(1)

    # Get name from path
    name = path.stem if path.is_file() else path.name

    # Get or create config
    config_path, config = get_or_create_config()

    # Add to [local] section
    spec = LocalResourceSpec(
        path=local_path,
        type=resource_type,
        package=package,
    )
    config.add_local(name, spec)
    config.save(config_path)

    console.print(f"[green]Added local {resource_type} '{name}' to agr.toml[/green]")
    console.print(f"  path: {local_path}")
    if package:
        console.print(f"  package: {package}")
    console.print("\n[dim]Run 'agr sync' to install to .claude/[/dim]")


app = typer.Typer(
    help="Add skills, commands, or agents from GitHub.",
)


@app.callback(invoke_without_command=True)
def add_unified(
    ctx: typer.Context,
    args: Annotated[
        Optional[List[str]],
        typer.Argument(help="Resource reference and optional arguments"),
    ] = None,
    resource_type: Annotated[
        Optional[str],
        typer.Option(
            "--type",
            "-t",
            help="Explicit resource type: skill, command, agent, or bundle",
        ),
    ] = None,
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite existing resource if it exists.",
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
    to_package: Annotated[
        Optional[str],
        typer.Option(
            "--to",
            help="Add local resource to a package namespace",
        ),
    ] = None,
) -> None:
    """Add a resource from a GitHub repository or local path.

    REFERENCE format:
      - username/name: installs from github.com/username/agent-resources
      - username/repo/name: installs from github.com/username/repo
      - ./path/to/resource: adds local path to agr.toml [local] section

    Auto-detects the resource type (skill, command, agent, or bundle).
    Use --type to explicitly specify when a name exists in multiple types.

    Examples:
      agr add kasperjunge/hello-world
      agr add kasperjunge/my-repo/hello-world --type skill
      agr add kasperjunge/productivity --global
      agr add ./custom/skill --type skill
      agr add ./scripts/deploy.md --type command --to my-toolkit
    """
    # Extract --type/-t and --to from args if captured there (happens when options come after ref)
    cleaned_args, resource_type, to_package = extract_options_from_args(args, resource_type, to_package)

    if not cleaned_args:
        console.print(ctx.get_help())
        raise typer.Exit(0)

    first_arg = cleaned_args[0]

    # Handle local paths
    if _is_local_path(first_arg):
        handle_add_local(first_arg, resource_type, to_package)
        return

    # Handle deprecated subcommand syntax: agr add skill <ref>
    if first_arg in DEPRECATED_SUBCOMMANDS:
        if len(cleaned_args) < 2:
            console.print(f"[red]Error: Missing resource reference after '{first_arg}'.[/red]")
            raise typer.Exit(1)

        resource_ref = cleaned_args[1]
        console.print(
            f"[yellow]Warning: 'agr add {first_arg}' is deprecated. "
            f"Use 'agr add {resource_ref}' instead.[/yellow]"
        )

        if first_arg == "skill":
            handle_add_resource(resource_ref, ResourceType.SKILL, "skills", overwrite, global_install)
        elif first_arg == "command":
            handle_add_resource(resource_ref, ResourceType.COMMAND, "commands", overwrite, global_install)
        elif first_arg == "agent":
            handle_add_resource(resource_ref, ResourceType.AGENT, "agents", overwrite, global_install)
        elif first_arg == "bundle":
            handle_add_bundle(resource_ref, overwrite, global_install)
        return

    # Normal unified add: agr add <ref>
    resource_ref = first_arg
    handle_add_unified(resource_ref, resource_type, overwrite, global_install)
