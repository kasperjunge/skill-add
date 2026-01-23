"""Orchestrator for coordinating resource installation.

This module provides the Orchestrator class that coordinates the
install/uninstall pipeline, delegating to existing fetcher.py functions
for Phase 1.

Note: This module was moved from agr.core.orchestrator to avoid circular
imports. It is re-exported from agr.core for API compatibility.
"""

from dataclasses import dataclass
from pathlib import Path

from agr.core.registry import get_default_tool, get_resource_spec
from agr.core.resource import ResourceSpec, ResourceType
from agr.core.tool import ToolSpec
from agr.fetcher import (
    copy_resource_to_dest,
    downloaded_repo,
    install_local_skill,
    install_skill_from_repo,
)
from agr.handle import ParsedHandle, parse_handle


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

    def _get_resource_spec(self, resource_type: ResourceType) -> ResourceSpec:
        """Get the resource spec, raising if not found."""
        spec = get_resource_spec(resource_type)
        if spec is None:
            raise ValueError(f"No spec registered for resource type: {resource_type}")
        return spec

    def install(
        self,
        handle: str | ParsedHandle,
        repo_root: Path,
        *,
        resource_type: ResourceType = ResourceType.SKILL,
        overwrite: bool = False,
        temporary: bool = False,
        temp_prefix: str = "_agrx_",
        global_install: bool = False,
    ) -> InstallResult:
        """Install a resource from a handle.

        Args:
            handle: Handle string or ParsedHandle
            repo_root: Repository root path
            resource_type: Type of resource to install
            overwrite: Whether to overwrite existing resources
            temporary: If True, use a temporary prefix for the name
            temp_prefix: Prefix for temporary installations
            global_install: If True, install to global directory

        Returns:
            InstallResult with installation details

        Raises:
            Various exceptions on failure
        """
        from agr.skill import SKILL_MARKER, find_skill_in_repo, is_valid_skill_dir

        resource_spec = self._get_resource_spec(resource_type)

        # Parse handle if string
        if isinstance(handle, str):
            parsed = parse_handle(handle)
        else:
            parsed = handle

        # Determine destination directory
        if global_install:
            dest_dir = self._tool.get_global_resource_dir(resource_type)
        else:
            dest_dir = self._tool.get_resource_dir(repo_root, resource_type)

        # Determine installed name
        if temporary:
            installed_name = f"{temp_prefix}{parsed.name}"
        else:
            installed_name = parsed.to_installed_name()

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
                dest_path = dest_dir / installed_name
                was_overwritten = dest_path.exists()
                copy_resource_to_dest(source_path, dest_path, installed_name)
                return InstallResult(
                    resource_name=installed_name,
                    installed_path=dest_path,
                    was_overwritten=was_overwritten,
                )
            else:
                # Check was_overwritten before the install modifies the path
                expected_path = dest_dir / parsed.to_installed_name()
                was_overwritten = expected_path.exists()
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
                from agr.exceptions import SkillNotFoundError

                skill_source = find_skill_in_repo(repo_dir, parsed.name)
                if skill_source is None:
                    raise SkillNotFoundError(
                        f"Skill '{parsed.name}' not found in repository.\n"
                        f"Searched: resources/skills/{parsed.name}/, skills/{parsed.name}/, {parsed.name}/"
                    )

                dest_path = dest_dir / installed_name
                was_overwritten = dest_path.exists()
                copy_resource_to_dest(skill_source, dest_path, installed_name)
                return InstallResult(
                    resource_name=installed_name,
                    installed_path=dest_path,
                    was_overwritten=was_overwritten,
                )
            else:
                # Check was_overwritten before the install modifies the path
                expected_path = dest_dir / parsed.to_installed_name()
                was_overwritten = expected_path.exists()
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
        resource_type: ResourceType = ResourceType.SKILL,
        global_uninstall: bool = False,
    ) -> bool:
        """Uninstall a resource by its installed name.

        Args:
            installed_name: Installed directory name (e.g., "kasperjunge:commit")
            repo_root: Repository root path
            resource_type: Type of resource to uninstall
            global_uninstall: If True, uninstall from global directory

        Returns:
            True if removed, False if not found
        """
        import shutil

        if global_uninstall:
            resource_dir = self._tool.get_global_resource_dir(resource_type)
        else:
            resource_dir = self._tool.get_resource_dir(repo_root, resource_type)

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
        resource_spec = self._get_resource_spec(resource_type)

        if global_list:
            resource_dir = self._tool.get_global_resource_dir(resource_type)
        else:
            resource_dir = self._tool.get_resource_dir(repo_root, resource_type)

        if not resource_dir.exists():
            return []

        return [
            d.name
            for d in resource_dir.iterdir()
            if d.is_dir() and (d / resource_spec.marker_file).exists()
        ]

    def is_installed(
        self,
        installed_name: str,
        repo_root: Path,
        *,
        resource_type: ResourceType = ResourceType.SKILL,
        global_check: bool = False,
    ) -> bool:
        """Check if a resource is installed.

        Args:
            installed_name: Installed directory name
            repo_root: Repository root path
            resource_type: Type of resource to check
            global_check: If True, check global directory

        Returns:
            True if installed
        """
        resource_spec = self._get_resource_spec(resource_type)

        if global_check:
            resource_dir = self._tool.get_global_resource_dir(resource_type)
        else:
            resource_dir = self._tool.get_resource_dir(repo_root, resource_type)

        resource_path = resource_dir / installed_name
        return resource_path.exists() and (resource_path / resource_spec.marker_file).exists()
