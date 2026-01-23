"""Tool configuration for Claude Code.

All Claude-specific paths and configuration are isolated in this module
for future extensibility to other tools.

DEPRECATED: This module provides backward compatibility shims.
For new code, use agr.core.tool (ToolSpec, ToolResourceConfig) instead.
"""

import warnings
from dataclasses import dataclass
from pathlib import Path


# Lazy imports to avoid circular imports
_ToolSpec = None
_ToolResourceConfig = None
_get_default_tool = None


def _lazy_import_core_tool():
    """Lazily import from agr.core.tool to avoid circular imports."""
    global _ToolSpec, _ToolResourceConfig
    if _ToolSpec is None:
        from agr.core.tool import ToolResourceConfig, ToolSpec
        _ToolSpec = ToolSpec
        _ToolResourceConfig = ToolResourceConfig
    return _ToolSpec, _ToolResourceConfig


def _lazy_import_get_default_tool():
    """Lazily import get_default_tool to avoid circular imports."""
    global _get_default_tool
    if _get_default_tool is None:
        from agr.core.registry import get_default_tool
        _get_default_tool = get_default_tool
    return _get_default_tool


def __getattr__(name: str):
    """Emit deprecation warning when accessing deprecated exports."""
    if name == "ToolSpec":
        warnings.warn(
            "Importing ToolSpec from agr.tool is deprecated. "
            "Use 'from agr.core.tool import ToolSpec' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        ToolSpec, _ = _lazy_import_core_tool()
        return ToolSpec
    if name == "ToolResourceConfig":
        warnings.warn(
            "Importing ToolResourceConfig from agr.tool is deprecated. "
            "Use 'from agr.core.tool import ToolResourceConfig' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        _, ToolResourceConfig = _lazy_import_core_tool()
        return ToolResourceConfig
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


@dataclass(frozen=True)
class ToolConfig:
    """Configuration for an AI coding tool.

    DEPRECATED: Use ToolSpec from agr.core.tool instead.
    """

    name: str
    config_dir: str  # e.g., ".claude"
    skills_subdir: str  # e.g., "skills"

    def __post_init__(self):
        warnings.warn(
            "ToolConfig is deprecated. Use ToolSpec from agr.core.tool instead.",
            DeprecationWarning,
            stacklevel=3,
        )

    def get_skills_dir(self, repo_root: Path) -> Path:
        """Get the skills directory for this tool in a repo."""
        return repo_root / self.config_dir / self.skills_subdir

    def get_global_skills_dir(self) -> Path:
        """Get the global skills directory (in user home)."""
        return Path.home() / self.config_dir / self.skills_subdir


class _DefaultToolProxy:
    """Proxy that returns the default tool from the registry.

    This provides backward compatibility for code that uses DEFAULT_TOOL
    while allowing the new lazy registration to work.
    """

    def __getattr__(self, name: str):
        get_default_tool = _lazy_import_get_default_tool()
        tool = get_default_tool()
        if tool is None:
            raise AttributeError("No default tool registered")
        return getattr(tool, name)

    def __repr__(self) -> str:
        get_default_tool = _lazy_import_get_default_tool()
        tool = get_default_tool()
        return f"<DefaultToolProxy wrapping {tool}>"


# Default tool for all operations - now a proxy to the registry
DEFAULT_TOOL = _DefaultToolProxy()

# Keep CLAUDE for backward compatibility but it's deprecated
# Users should use get_default_tool() or get_tool_spec("claude") instead
CLAUDE = DEFAULT_TOOL
