"""Orchestrator for coordinating resource installation.

This module provides the Orchestrator class that coordinates the
install/uninstall pipeline, delegating to existing fetcher.py functions
for Phase 1.
"""

from dataclasses import dataclass
from pathlib import Path

from agr.core.registry import get_default_tool
from agr.core.resource import ResourceType
from agr.core.tool import ToolSpec
from agr.handle import ParsedHandle, parse_handle

# Import specs to ensure they're registered
import agr.core.specs  # noqa: F401


@dataclass
class InstallResult:
    """Result of an install operation."""

    resource_name: str
    installed_path: Path
    was_overwritten: bool


class Orchestrator:
    """Coordinates the install/uninstall pipeline for resources.

    In Phase 1, this class delegates to existing fetcher.py functions
    while providing a cleaner API for future extensibility.
    """

    def __init__(self, tool: ToolSpec | None = None) -> None:
        """Initialize the orchestrator.

        Args:
            tool: Tool specification to use. If None, uses the default tool.
        """
        self._tool = tool or get_default_tool()
        if self._tool is None:
            raise ValueError("No tool specification available")

    @property
    def tool(self) -> ToolSpec:
        """Get the tool specification."""
        return self._tool

    def install(
        self,
        handle: str | ParsedHandle,
        repo_root: Path,
        *,
        overwrite: bool = False,
        temporary: bool = False,
        temp_prefix: str = "_agrx_",
        global_install: bool = False,
    ) -> InstallResult:
        """Install a resource from a handle.

        Args:
            handle: Handle string or ParsedHandle
            repo_root: Repository root path
            overwrite: Whether to overwrite existing resources
            temporary: If True, use a temporary prefix for the name
            temp_prefix: Prefix for temporary installations
            global_install: If True, install to global directory

        Returns:
            InstallResult with installation details

        Raises:
            Various exceptions on failure
        """
        # Import here to avoid circular imports
        from agr.fetcher import (
            downloaded_repo,
            install_local_skill,
            install_skill_from_repo,
        )
        from agr.skill import SKILL_MARKER, is_valid_skill_dir

        # Parse handle if string
        if isinstance(handle, str):
            parsed = parse_handle(handle)
        else:
            parsed = handle

        # Determine destination directory
        if global_install:
            dest_dir = self._tool.get_global_resource_dir(ResourceType.SKILL)
        else:
            dest_dir = self._tool.get_resource_dir(repo_root, ResourceType.SKILL)

        # Check if resource already exists
        if temporary:
            installed_name = f"{temp_prefix}{parsed.name}"
        else:
            installed_name = parsed.to_installed_name()

        existing_path = dest_dir / installed_name
        was_overwritten = existing_path.exists()

        if parsed.is_local:
            # Local skill installation
            if parsed.local_path is None:
                raise ValueError("Local handle missing path")

            source_path = parsed.local_path
            if not source_path.is_absolute():
                source_path = (repo_root / source_path).resolve()

            if not is_valid_skill_dir(source_path):
                from agr.exceptions import SkillNotFoundError
                raise SkillNotFoundError(
                    f"'{source_path}' is not a valid skill (missing {SKILL_MARKER})"
                )

            # For temporary installs, we need custom logic
            if temporary:
                import shutil

                # Remove existing if present
                if existing_path.exists():
                    shutil.rmtree(existing_path)

                # Ensure parent exists
                existing_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy skill
                shutil.copytree(source_path, existing_path)

                # Update SKILL.md name field
                from agr.skill import update_skill_md_name
                update_skill_md_name(existing_path, installed_name)

                return InstallResult(
                    resource_name=installed_name,
                    installed_path=existing_path,
                    was_overwritten=was_overwritten,
                )
            else:
                installed_path = install_local_skill(source_path, dest_dir, overwrite)
                return InstallResult(
                    resource_name=installed_path.name,
                    installed_path=installed_path,
                    was_overwritten=was_overwritten,
                )

        # Remote skill installation
        username, repo_name = parsed.get_github_repo()

        with downloaded_repo(username, repo_name) as repo_dir:
            if temporary:
                import shutil

                from agr.skill import find_skill_in_repo, update_skill_md_name

                # Find the skill in the repo
                from agr.exceptions import SkillNotFoundError

                skill_source = find_skill_in_repo(repo_dir, parsed.name)
                if skill_source is None:
                    raise SkillNotFoundError(
                        f"Skill '{parsed.name}' not found in repository.\n"
                        f"Searched: resources/skills/{parsed.name}/, skills/{parsed.name}/, {parsed.name}/"
                    )

                # Remove existing if present
                if existing_path.exists():
                    shutil.rmtree(existing_path)

                # Ensure parent exists
                existing_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy skill
                shutil.copytree(skill_source, existing_path)

                # Update SKILL.md name field
                update_skill_md_name(existing_path, installed_name)

                return InstallResult(
                    resource_name=installed_name,
                    installed_path=existing_path,
                    was_overwritten=was_overwritten,
                )
            else:
                installed_path = install_skill_from_repo(
                    repo_dir, parsed.name, parsed, dest_dir, overwrite
                )
                return InstallResult(
                    resource_name=installed_path.name,
                    installed_path=installed_path,
                    was_overwritten=was_overwritten,
                )

    def uninstall(
        self,
        installed_name: str,
        repo_root: Path,
        *,
        global_uninstall: bool = False,
    ) -> bool:
        """Uninstall a resource by its installed name.

        Args:
            installed_name: Installed directory name (e.g., "kasperjunge:commit")
            repo_root: Repository root path
            global_uninstall: If True, uninstall from global directory

        Returns:
            True if removed, False if not found
        """
        import shutil

        if global_uninstall:
            resource_dir = self._tool.get_global_resource_dir(ResourceType.SKILL)
        else:
            resource_dir = self._tool.get_resource_dir(repo_root, ResourceType.SKILL)

        resource_path = resource_dir / installed_name

        if not resource_path.exists():
            return False

        shutil.rmtree(resource_path)
        return True

    def list_installed(
        self,
        repo_root: Path,
        resource_type: ResourceType = ResourceType.SKILL,
        *,
        global_list: bool = False,
    ) -> list[str]:
        """Get list of installed resource names.

        Args:
            repo_root: Repository root path
            resource_type: Type of resources to list
            global_list: If True, list from global directory

        Returns:
            List of installed resource directory names
        """
        from agr.skill import SKILL_MARKER

        if global_list:
            resource_dir = self._tool.get_global_resource_dir(resource_type)
        else:
            resource_dir = self._tool.get_resource_dir(repo_root, resource_type)

        if not resource_dir.exists():
            return []

        return [
            d.name
            for d in resource_dir.iterdir()
            if d.is_dir() and (d / SKILL_MARKER).exists()
        ]

    def is_installed(
        self,
        installed_name: str,
        repo_root: Path,
        *,
        global_check: bool = False,
    ) -> bool:
        """Check if a resource is installed.

        Args:
            installed_name: Installed directory name
            repo_root: Repository root path
            global_check: If True, check global directory

        Returns:
            True if installed
        """
        from agr.skill import SKILL_MARKER

        if global_check:
            resource_dir = self._tool.get_global_resource_dir(ResourceType.SKILL)
        else:
            resource_dir = self._tool.get_resource_dir(repo_root, ResourceType.SKILL)

        resource_path = resource_dir / installed_name
        return resource_path.exists() and (resource_path / SKILL_MARKER).exists()
