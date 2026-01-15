"""Tests for tool adapter architecture."""

import tempfile
from pathlib import Path

import pytest

from agr.tools import ResourceType, Tool, ToolResourceConfig
from agr.tools.claude import ClaudeCodeAdapter
from agr.tools.registry import ToolRegistry, get_registry, get_tool_adapter


class TestToolResourceConfig:
    """Tests for ToolResourceConfig dataclass."""

    def test_skill_config(self) -> None:
        config = ToolResourceConfig(
            base_dir=".claude",
            subdir="skills",
            is_directory=True,
            file_extension=None,
            entry_file="SKILL.md",
        )
        assert config.base_dir == ".claude"
        assert config.subdir == "skills"
        assert config.is_directory is True
        assert config.file_extension is None
        assert config.entry_file == "SKILL.md"

    def test_command_config(self) -> None:
        config = ToolResourceConfig(
            base_dir=".claude",
            subdir="commands",
            is_directory=False,
            file_extension=".md",
            entry_file=None,
        )
        assert config.base_dir == ".claude"
        assert config.subdir == "commands"
        assert config.is_directory is False
        assert config.file_extension == ".md"
        assert config.entry_file is None


class TestClaudeCodeAdapter:
    """Tests for ClaudeCodeAdapter."""

    @pytest.fixture
    def adapter(self) -> ClaudeCodeAdapter:
        return ClaudeCodeAdapter()

    def test_name(self, adapter: ClaudeCodeAdapter) -> None:
        assert adapter.name == "Claude Code"

    def test_tool_id(self, adapter: ClaudeCodeAdapter) -> None:
        assert adapter.tool_id == Tool.CLAUDE_CODE

    def test_base_directory(self, adapter: ClaudeCodeAdapter) -> None:
        assert adapter.base_directory == ".claude"

    def test_cli_binary(self, adapter: ClaudeCodeAdapter) -> None:
        assert adapter.cli_binary == "claude"

    def test_get_resource_config_skill(self, adapter: ClaudeCodeAdapter) -> None:
        config = adapter.get_resource_config(ResourceType.SKILL)
        assert config is not None
        assert config.base_dir == ".claude"
        assert config.subdir == "skills"
        assert config.is_directory is True
        assert config.file_extension is None
        assert config.entry_file == "SKILL.md"

    def test_get_resource_config_command(self, adapter: ClaudeCodeAdapter) -> None:
        config = adapter.get_resource_config(ResourceType.COMMAND)
        assert config is not None
        assert config.base_dir == ".claude"
        assert config.subdir == "commands"
        assert config.is_directory is False
        assert config.file_extension == ".md"

    def test_get_resource_config_agent(self, adapter: ClaudeCodeAdapter) -> None:
        config = adapter.get_resource_config(ResourceType.AGENT)
        assert config is not None
        assert config.base_dir == ".claude"
        assert config.subdir == "agents"
        assert config.is_directory is False
        assert config.file_extension == ".md"

    def test_is_project_configured_true(self, adapter: ClaudeCodeAdapter) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / ".claude").mkdir()
            assert adapter.is_project_configured(project_path) is True

    def test_is_project_configured_false(self, adapter: ClaudeCodeAdapter) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            assert adapter.is_project_configured(project_path) is False


class TestToolRegistry:
    """Tests for ToolRegistry."""

    @pytest.fixture
    def registry(self) -> ToolRegistry:
        return ToolRegistry()

    def test_default_adapters(self, registry: ToolRegistry) -> None:
        adapters = registry.all()
        assert len(adapters) >= 1
        tool_ids = [a.tool_id for a in adapters]
        assert Tool.CLAUDE_CODE in tool_ids

    def test_get_claude_code(self, registry: ToolRegistry) -> None:
        adapter = registry.get(Tool.CLAUDE_CODE)
        assert adapter is not None
        assert adapter.name == "Claude Code"

    def test_get_by_name_claude(self, registry: ToolRegistry) -> None:
        adapter = registry.get_by_name("claude")
        assert adapter is not None
        assert adapter.name == "Claude Code"

    def test_get_by_name_unknown(self, registry: ToolRegistry) -> None:
        adapter = registry.get_by_name("unknown")
        assert adapter is None

    def test_get_default(self, registry: ToolRegistry) -> None:
        adapter = registry.get_default()
        assert adapter.name == "Claude Code"
        assert adapter.tool_id == Tool.CLAUDE_CODE


class TestGetToolAdapter:
    """Tests for get_tool_adapter helper function."""

    def test_get_default(self) -> None:
        adapter = get_tool_adapter()
        assert adapter.name == "Claude Code"

    def test_get_claude(self) -> None:
        adapter = get_tool_adapter("claude")
        assert adapter.name == "Claude Code"

    def test_get_unknown_raises(self) -> None:
        with pytest.raises(ValueError) as exc_info:
            get_tool_adapter("unknown")
        assert "Unknown tool: unknown" in str(exc_info.value)
        assert "Available: claude" in str(exc_info.value)


class TestGetRegistry:
    """Tests for get_registry singleton."""

    def test_returns_registry(self) -> None:
        registry = get_registry()
        assert isinstance(registry, ToolRegistry)

    def test_singleton(self) -> None:
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2
