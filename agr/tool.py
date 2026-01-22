"""Tool configuration for Claude Code.

All Claude-specific paths and configuration are isolated in this module
for future extensibility to other tools.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ToolConfig:
    """Configuration for an AI coding tool."""

    name: str
    config_dir: str  # e.g., ".claude"
    skills_subdir: str  # e.g., "skills"

    def get_skills_dir(self, repo_root: Path) -> Path:
        """Get the skills directory for this tool in a repo."""
        return repo_root / self.config_dir / self.skills_subdir

    def get_global_skills_dir(self) -> Path:
        """Get the global skills directory (in user home)."""
        return Path.home() / self.config_dir / self.skills_subdir


# Claude Code tool configuration
CLAUDE = ToolConfig(
    name="claude",
    config_dir=".claude",
    skills_subdir="skills",
)

# Default tool for all operations
DEFAULT_TOOL = CLAUDE
