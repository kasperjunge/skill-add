"""Tool registry for managing available tool adapters."""

from pathlib import Path

from agr.tools import Tool, ToolAdapter
from agr.tools.claude import ClaudeCodeAdapter


class ToolRegistry:
    """Registry for managing tool adapters.

    Provides methods to register, retrieve, and detect tools.
    """

    def __init__(self) -> None:
        """Initialize registry with default tools."""
        self._adapters: dict[Tool, ToolAdapter] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default tool adapters."""
        self.register(ClaudeCodeAdapter())

    def register(self, adapter: ToolAdapter) -> None:
        """Register a tool adapter.

        Args:
            adapter: The tool adapter to register
        """
        self._adapters[adapter.tool_id] = adapter

    def get(self, tool: Tool) -> ToolAdapter | None:
        """Get an adapter by tool identifier.

        Args:
            tool: The tool identifier

        Returns:
            The tool adapter, or None if not registered
        """
        return self._adapters.get(tool)

    def get_by_name(self, name: str) -> ToolAdapter | None:
        """Get an adapter by its CLI name.

        Args:
            name: The CLI name (e.g., "claude", "cursor")

        Returns:
            The tool adapter, or None if not found
        """
        for tool in Tool:
            if tool.value == name:
                return self._adapters.get(tool)
        return None

    def all(self) -> list[ToolAdapter]:
        """Get all registered adapters.

        Returns:
            List of all registered tool adapters
        """
        return list(self._adapters.values())

    def detect_tools(self, project_path: Path | None = None) -> list[ToolAdapter]:
        """Detect which tools to target for a project.

        Priority:
        1. Project detection - which tool directories exist
        2. System detection - which CLIs are installed
        3. Default - Claude Code (always)

        Args:
            project_path: Path to the project directory, or None for current directory

        Returns:
            List of detected tools. Always includes at least Claude Code.
        """
        if project_path is None:
            project_path = Path.cwd()

        detected: list[ToolAdapter] = []

        for adapter in self._adapters.values():
            # Check if tool is configured in project
            if adapter.is_project_configured(project_path):
                detected.append(adapter)
            # Or if CLI is installed (for new projects)
            elif adapter.is_installed():
                detected.append(adapter)

        # Always include Claude Code as default
        claude_adapter = self.get(Tool.CLAUDE_CODE)
        if claude_adapter and claude_adapter not in detected:
            detected.append(claude_adapter)

        return detected

    def detect_source_tools(self, repo_dir: Path) -> list[Tool]:
        """Detect which tool formats exist in a source repository.

        Scans the repository for tool-specific directories to determine
        which formats are available.

        Args:
            repo_dir: Path to the extracted repository

        Returns:
            List of tools found in the repository
        """
        found: list[Tool] = []

        for adapter in self._adapters.values():
            if (repo_dir / adapter.base_directory).is_dir():
                found.append(adapter.tool_id)

        return found

    def get_default(self) -> ToolAdapter:
        """Get the default tool adapter (Claude Code).

        Returns:
            The Claude Code adapter

        Raises:
            RuntimeError: If Claude Code adapter is not registered
        """
        adapter = self.get(Tool.CLAUDE_CODE)
        if adapter is None:
            raise RuntimeError("Claude Code adapter not registered")
        return adapter


# Global registry instance
_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    """Get the global tool registry instance.

    Returns:
        The global ToolRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def get_tool_adapter(tool_name: str | None = None) -> ToolAdapter:
    """Get a tool adapter by name, or the default.

    Args:
        tool_name: CLI name of the tool (e.g., "claude"), or None for default

    Returns:
        The requested tool adapter

    Raises:
        ValueError: If the tool name is not recognized
    """
    registry = get_registry()

    if tool_name is None:
        return registry.get_default()

    adapter = registry.get_by_name(tool_name)
    if adapter is None:
        available = [t.value for t in Tool]
        raise ValueError(f"Unknown tool: {tool_name}. Available: {', '.join(available)}")

    return adapter
