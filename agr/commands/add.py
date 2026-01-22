"""agr add command implementation."""

from pathlib import Path

from rich.console import Console

from agr.config import AgrConfig, Dependency, find_config, find_repo_root
from agr.exceptions import AgrError, InvalidHandleError
from agr.fetcher import fetch_and_install
from agr.handle import parse_handle

console = Console()


def run_add(refs: list[str], overwrite: bool = False) -> None:
    """Run the add command.

    Args:
        refs: List of handles or paths to add
        overwrite: Whether to overwrite existing skills
    """
    # Find repo root
    repo_root = find_repo_root()
    if repo_root is None:
        console.print("[red]Error:[/red] Not in a git repository")
        raise SystemExit(1)

    # Find or create config
    config_path = find_config()
    if config_path is None:
        config_path = repo_root / "agr.toml"
        config = AgrConfig()
    else:
        config = AgrConfig.load(config_path)

    # Track results for summary
    results: list[tuple[str, bool, str]] = []  # (ref, success, message)

    for ref in refs:
        try:
            # Parse handle
            handle = parse_handle(ref)

            # Install the skill
            installed_path = fetch_and_install(handle, repo_root, overwrite)

            # Add to config
            if handle.is_local:
                config.add_dependency(Dependency(
                    type="skill",
                    path=ref,
                ))
            else:
                config.add_dependency(Dependency(
                    type="skill",
                    handle=handle.to_toml_handle(),
                ))

            results.append((ref, True, str(installed_path)))

        except InvalidHandleError as e:
            results.append((ref, False, str(e)))
        except FileExistsError as e:
            results.append((ref, False, str(e)))
        except AgrError as e:
            results.append((ref, False, str(e)))
        except Exception as e:
            results.append((ref, False, f"Unexpected error: {e}"))

    # Save config if any successes
    successes = [r for r in results if r[1]]
    if successes:
        config.save(config_path)

    # Print results
    for ref, success, message in results:
        if success:
            console.print(f"[green]Added:[/green] {ref}")
            console.print(f"  [dim]Installed to {message}[/dim]")
        else:
            console.print(f"[red]Failed:[/red] {ref}")
            console.print(f"  [dim]{message}[/dim]")

    # Summary
    if len(refs) > 1:
        console.print()
        console.print(
            f"[bold]Summary:[/bold] {len(successes)}/{len(refs)} skills added"
        )

    # Exit with error if any failures
    failures = [r for r in results if not r[1]]
    if failures:
        raise SystemExit(1)
