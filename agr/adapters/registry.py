"""Adapter registry for managing tool adapters.

Provides a singleton registry for registering and retrieving tool adapters.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agr.adapters.base import ToolAdapter


class AdapterNotFoundError(Exception):
    """Raised when a requested adapter is not found."""

    pass


class AdapterRegistry:
    """Registry for tool adapters.

    Provides a singleton pattern for managing adapter instances.
    Adapters are lazily instantiated on first access.

    Usage:
        # Register adapters (typically done at import time)
        AdapterRegistry.register("claude", ClaudeAdapter)
        AdapterRegistry.register("cursor", CursorAdapter)

        # Get an adapter instance
        adapter = AdapterRegistry.get("claude")

        # Get all registered adapter names
        names = AdapterRegistry.all_names()
    """

    _adapters: dict[str, type] = {}
    _instances: dict[str, "ToolAdapter"] = {}

    @classmethod
    def register(cls, name: str, adapter_class: type) -> None:
        """Register an adapter class.

        Args:
            name: Name to register the adapter under (e.g., "claude")
            adapter_class: The adapter class to register
        """
        cls._adapters[name] = adapter_class
        # Clear cached instance if re-registering
        if name in cls._instances:
            del cls._instances[name]

    @classmethod
    def get(cls, tool_name: str) -> "ToolAdapter":
        """Get an adapter instance by name.

        Lazily instantiates the adapter on first access.

        Args:
            tool_name: Name of the tool (e.g., "claude", "cursor")

        Returns:
            The adapter instance

        Raises:
            AdapterNotFoundError: If no adapter is registered for the name
        """
        if tool_name not in cls._adapters:
            available = ", ".join(cls._adapters.keys()) if cls._adapters else "none"
            raise AdapterNotFoundError(
                f"No adapter registered for '{tool_name}'. Available: {available}"
            )

        if tool_name not in cls._instances:
            cls._instances[tool_name] = cls._adapters[tool_name]()

        return cls._instances[tool_name]

    @classmethod
    def all_names(cls) -> list[str]:
        """Get all registered adapter names.

        Returns:
            List of registered adapter names
        """
        return list(cls._adapters.keys())

    @classmethod
    def get_default(cls) -> "ToolAdapter":
        """Get the default adapter (Claude).

        Returns:
            The Claude adapter instance

        Raises:
            AdapterNotFoundError: If Claude adapter is not registered
        """
        return cls.get("claude")

    @classmethod
    def clear(cls) -> None:
        """Clear all registered adapters and instances.

        Primarily useful for testing.
        """
        cls._adapters.clear()
        cls._instances.clear()
