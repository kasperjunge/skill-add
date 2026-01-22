"""agr remove command implementation."""

from pathlib import Path

from rich.console import Console

from agr.config import AgrConfig, find_config, find_repo_root
from agr.fetcher import uninstall_skill
from agr.handle import parse_handle

console = Console()


def run_remove(refs: list[str]) -> None:
    """Run the remove command.

    Args:
        refs: List of handles or paths to remove
    """
    # Find repo root
    repo_root = find_repo_root()
    if repo_root is None:
        console.print("[red]Error:[/red] Not in a git repository")
        raise SystemExit(1)

    # Find config
    config_path = find_config()
    if config_path is None:
        console.print("[red]Error:[/red] No agr.toml found")
        raise SystemExit(1)

    config = AgrConfig.load(config_path)

    # Track results
    results: list[tuple[str, bool, str]] = []

    for ref in refs:
        try:
            # Parse handle to get installed name
            handle = parse_handle(ref)
            installed_name = handle.to_installed_name()

            # Remove from filesystem
            removed_fs = uninstall_skill(installed_name, repo_root)

            # Remove from config
            # Try both handle format and path format
            removed_config = config.remove_dependency(ref)
            if not removed_config and handle.is_local:
                # Try with the path
                removed_config = config.remove_dependency(str(handle.local_path))
            if not removed_config:
                # Try with toml handle
                removed_config = config.remove_dependency(handle.to_toml_handle())

            if removed_fs or removed_config:
                results.append((ref, True, "Removed"))
            else:
                results.append((ref, False, "Not found"))

        except Exception as e:
            results.append((ref, False, str(e)))

    # Save config if any changes
    successes = [r for r in results if r[1]]
    if successes:
        config.save(config_path)

    # Print results
    for ref, success, message in results:
        if success:
            console.print(f"[green]Removed:[/green] {ref}")
        else:
            console.print(f"[yellow]Not found:[/yellow] {ref}")

    # Summary
    if len(refs) > 1:
        console.print()
        console.print(
            f"[bold]Summary:[/bold] {len(successes)}/{len(refs)} skills removed"
        )
