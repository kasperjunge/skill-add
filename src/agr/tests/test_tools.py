"""Tests for tool adapter architecture."""

import tempfile
from pathlib import Path

import pytest

from agr.tools import ResourceType, Tool, ToolResourceConfig
from agr.tools.claude import ClaudeCodeAdapter
from agr.tools.registry import ToolRegistry, get_registry, get_tool_adapter


class TestToolResourceConfig:
    """Tests for ToolResourceConfig dataclass."""

    def test_skill_config(self):
        """Test skill resource configuration."""
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

    def test_command_config(self):
        """Test command resource configuration."""
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
    def adapter(self):
        """Create a ClaudeCodeAdapter instance."""
        return ClaudeCodeAdapter()

    def test_name(self, adapter):
        """Test adapter name."""
        assert adapter.name == "Claude Code"

    def test_tool_id(self, adapter):
        """Test adapter tool_id."""
        assert adapter.tool_id == Tool.CLAUDE_CODE

    def test_base_directory(self, adapter):
        """Test adapter base_directory."""
        assert adapter.base_directory == ".claude"

    def test_cli_binary(self, adapter):
        """Test adapter cli_binary."""
        assert adapter.cli_binary == "claude"

    def test_get_resource_config_skill(self, adapter):
        """Test get_resource_config for skills."""
        config = adapter.get_resource_config(ResourceType.SKILL)
        assert config is not None
        assert config.base_dir == ".claude"
        assert config.subdir == "skills"
        assert config.is_directory is True
        assert config.file_extension is None
        assert config.entry_file == "SKILL.md"

    def test_get_resource_config_command(self, adapter):
        """Test get_resource_config for commands."""
        config = adapter.get_resource_config(ResourceType.COMMAND)
        assert config is not None
        assert config.base_dir == ".claude"
        assert config.subdir == "commands"
        assert config.is_directory is False
        assert config.file_extension == ".md"

    def test_get_resource_config_agent(self, adapter):
        """Test get_resource_config for agents."""
        config = adapter.get_resource_config(ResourceType.AGENT)
        assert config is not None
        assert config.base_dir == ".claude"
        assert config.subdir == "agents"
        assert config.is_directory is False
        assert config.file_extension == ".md"

    def test_supports_resource_type(self, adapter):
        """Test supports_resource_type for all types."""
        assert adapter.supports_resource_type(ResourceType.SKILL) is True
        assert adapter.supports_resource_type(ResourceType.COMMAND) is True
        assert adapter.supports_resource_type(ResourceType.AGENT) is True

    def test_is_project_configured_true(self, adapter):
        """Test is_project_configured when .claude exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / ".claude").mkdir()
            assert adapter.is_project_configured(project_path) is True

    def test_is_project_configured_false(self, adapter):
        """Test is_project_configured when .claude doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            assert adapter.is_project_configured(project_path) is False

    def test_transform_resource_identity(self, adapter):
        """Test transform_resource for same tool (identity)."""
        content = "# Test content"
        result = adapter.transform_resource(content, Tool.CLAUDE_CODE, ResourceType.SKILL)
        assert result == content

    def test_get_source_subdir(self, adapter):
        """Test get_source_subdir."""
        assert adapter.get_source_subdir(ResourceType.SKILL) == ".claude/skills"
        assert adapter.get_source_subdir(ResourceType.COMMAND) == ".claude/commands"
        assert adapter.get_source_subdir(ResourceType.AGENT) == ".claude/agents"

    def test_get_dest_subdir(self, adapter):
        """Test get_dest_subdir."""
        assert adapter.get_dest_subdir(ResourceType.SKILL) == "skills"
        assert adapter.get_dest_subdir(ResourceType.COMMAND) == "commands"
        assert adapter.get_dest_subdir(ResourceType.AGENT) == "agents"


class TestToolRegistry:
    """Tests for ToolRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a fresh ToolRegistry instance."""
        return ToolRegistry()

    def test_default_adapters(self, registry):
        """Test that Claude Code is registered by default."""
        adapters = registry.all()
        assert len(adapters) >= 1
        tool_ids = [a.tool_id for a in adapters]
        assert Tool.CLAUDE_CODE in tool_ids

    def test_get_claude_code(self, registry):
        """Test getting Claude Code adapter."""
        adapter = registry.get(Tool.CLAUDE_CODE)
        assert adapter is not None
        assert adapter.name == "Claude Code"

    def test_get_by_name_claude(self, registry):
        """Test get_by_name for Claude Code."""
        adapter = registry.get_by_name("claude")
        assert adapter is not None
        assert adapter.name == "Claude Code"

    def test_get_by_name_unknown(self, registry):
        """Test get_by_name for unknown tool."""
        adapter = registry.get_by_name("unknown")
        assert adapter is None

    def test_get_default(self, registry):
        """Test get_default returns Claude Code."""
        adapter = registry.get_default()
        assert adapter.name == "Claude Code"
        assert adapter.tool_id == Tool.CLAUDE_CODE

    def test_detect_tools_with_claude_dir(self, registry):
        """Test detect_tools when .claude directory exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / ".claude").mkdir()

            detected = registry.detect_tools(project_path)
            assert len(detected) >= 1
            tool_ids = [a.tool_id for a in detected]
            assert Tool.CLAUDE_CODE in tool_ids

    def test_detect_tools_empty_project(self, registry):
        """Test detect_tools on empty project still includes default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            detected = registry.detect_tools(project_path)
            # Should still include Claude Code as default (if installed)
            # or at minimum as fallback
            assert len(detected) >= 1

    def test_detect_source_tools_claude(self, registry):
        """Test detect_source_tools finds .claude directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            (repo_dir / ".claude").mkdir()

            found = registry.detect_source_tools(repo_dir)
            assert Tool.CLAUDE_CODE in found

    def test_detect_source_tools_empty(self, registry):
        """Test detect_source_tools on empty repo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)

            found = registry.detect_source_tools(repo_dir)
            assert found == []


class TestGetToolAdapter:
    """Tests for get_tool_adapter helper function."""

    def test_get_default(self):
        """Test getting default adapter."""
        adapter = get_tool_adapter()
        assert adapter.name == "Claude Code"

    def test_get_claude(self):
        """Test getting Claude adapter by name."""
        adapter = get_tool_adapter("claude")
        assert adapter.name == "Claude Code"

    def test_get_unknown_raises(self):
        """Test getting unknown tool raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_tool_adapter("unknown")
        assert "Unknown tool: unknown" in str(exc_info.value)
        assert "Available: claude" in str(exc_info.value)


class TestGetRegistry:
    """Tests for get_registry singleton."""

    def test_returns_registry(self):
        """Test that get_registry returns a ToolRegistry."""
        registry = get_registry()
        assert isinstance(registry, ToolRegistry)

    def test_singleton(self):
        """Test that get_registry returns the same instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2
