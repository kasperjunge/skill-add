"""Tool registry for managing available tool adapters."""

from agr.tools import Tool, ToolAdapter
from agr.tools.claude import ClaudeCodeAdapter


class ToolRegistry:
    """Registry for managing tool adapters."""

    def __init__(self) -> None:
        self._adapters: dict[Tool, ToolAdapter] = {}
        self.register(ClaudeCodeAdapter())

    def register(self, adapter: ToolAdapter) -> None:
        self._adapters[adapter.tool_id] = adapter

    def get(self, tool: Tool) -> ToolAdapter | None:
        return self._adapters.get(tool)

    def get_by_name(self, name: str) -> ToolAdapter | None:
        for tool in Tool:
            if tool.value == name:
                return self._adapters.get(tool)
        return None

    def all(self) -> list[ToolAdapter]:
        return list(self._adapters.values())

    def get_default(self) -> ToolAdapter:
        adapter = self.get(Tool.CLAUDE_CODE)
        if adapter is None:
            raise RuntimeError("Claude Code adapter not registered")
        return adapter


_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def get_tool_adapter(tool_name: str | None = None) -> ToolAdapter:
    """Get a tool adapter by name, or the default."""
    registry = get_registry()

    if tool_name is None:
        return registry.get_default()

    adapter = registry.get_by_name(tool_name)
    if adapter is None:
        available = [t.value for t in Tool]
        raise ValueError(f"Unknown tool: {tool_name}. Available: {', '.join(available)}")

    return adapter
