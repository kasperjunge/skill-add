"""Tool adapter infrastructure for multi-tool support.

This package provides adapters for different AI coding tools,
enabling agr to work with Claude Code, Cursor, and potentially others.

Public exports:
- ToolFormat: Configuration dataclass for tool-specific formats
- ToolAdapter: Protocol defining the adapter interface
- InstalledResource: Dataclass for discovered resources
- AdapterRegistry: Singleton registry for adapter management
- AdapterNotFoundError: Exception for missing adapters
- ToolDetector: Utility for detecting available tools
- DetectedTool: Dataclass for tool detection results
- ClaudeAdapter: Adapter implementation for Claude Code
- CursorAdapter: Adapter implementation for Cursor
"""

from agr.adapters.base import ToolFormat, ToolAdapter, InstalledResource, discover_md_resources
from agr.adapters.registry import AdapterRegistry, AdapterNotFoundError
from agr.adapters.detector import ToolDetector, DetectedTool

# Import adapters to trigger registration
from agr.adapters.claude import ClaudeAdapter
from agr.adapters.cursor import CursorAdapter

__all__ = [
    # Base types
    "ToolFormat",
    "ToolAdapter",
    "InstalledResource",
    "discover_md_resources",
    # Registry
    "AdapterRegistry",
    "AdapterNotFoundError",
    # Detection
    "ToolDetector",
    "DetectedTool",
    # Adapters
    "ClaudeAdapter",
    "CursorAdapter",
]
