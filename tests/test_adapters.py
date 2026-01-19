"""Tests for tool adapter infrastructure (Task #25)."""

from pathlib import Path

import pytest

from agr.adapters import (
    ToolFormat,
    ToolAdapter,
    InstalledResource,
    AdapterRegistry,
    AdapterNotFoundError,
    ToolDetector,
    DetectedTool,
    ClaudeAdapter,
    CursorAdapter,
)
from agr.handle import ParsedHandle


class TestToolFormat:
    """Test ToolFormat dataclass."""

    def test_tool_format_dataclass(self):
        """Test creating a ToolFormat instance."""
        fmt = ToolFormat(
            name="test",
            display_name="Test Tool",
            config_dir=".test",
            skill_dir="skills",
            command_dir="commands",
            agent_dir="agents",
            rule_dir="rules",
            skill_marker="SKILL.md",
            namespace_format="colon",
            cli_command="test",
            global_config_dir=Path.home() / ".test",
        )
        assert fmt.name == "test"
        assert fmt.display_name == "Test Tool"
        assert fmt.config_dir == ".test"

    def test_claude_format_values(self):
        """Test Claude adapter format values."""
        adapter = ClaudeAdapter()
        fmt = adapter.format
        assert fmt.name == "claude"
        assert fmt.display_name == "Claude Code"
        assert fmt.config_dir == ".claude"
        assert fmt.namespace_format == "colon"
        assert fmt.cli_command == "claude"

    def test_cursor_format_values(self):
        """Test Cursor adapter format values."""
        adapter = CursorAdapter()
        fmt = adapter.format
        assert fmt.name == "cursor"
        assert fmt.display_name == "Cursor"
        assert fmt.config_dir == ".cursor"
        assert fmt.namespace_format == "nested"


class TestAdapterRegistry:
    """Test AdapterRegistry singleton."""

    def setup_method(self):
        """Clear registry before each test."""
        # Store original state
        self._original_adapters = AdapterRegistry._adapters.copy()
        self._original_instances = AdapterRegistry._instances.copy()

    def teardown_method(self):
        """Restore registry after each test."""
        AdapterRegistry._adapters = self._original_adapters
        AdapterRegistry._instances = self._original_instances

    def test_register_adapter(self):
        """Test registering an adapter."""
        AdapterRegistry.clear()

        class TestAdapter:
            pass

        AdapterRegistry.register("test", TestAdapter)
        assert "test" in AdapterRegistry.all_names()

    def test_get_claude_adapter(self):
        """Test getting Claude adapter."""
        adapter = AdapterRegistry.get("claude")
        assert isinstance(adapter, ClaudeAdapter)

    def test_get_cursor_adapter(self):
        """Test getting Cursor adapter."""
        adapter = AdapterRegistry.get("cursor")
        assert isinstance(adapter, CursorAdapter)

    def test_get_unknown_raises(self):
        """Test getting unknown adapter raises error."""
        with pytest.raises(AdapterNotFoundError, match="No adapter registered"):
            AdapterRegistry.get("unknown-tool")

    def test_all_names(self):
        """Test getting all registered adapter names."""
        names = AdapterRegistry.all_names()
        assert "claude" in names
        assert "cursor" in names

    def test_get_default_returns_claude(self):
        """Test default adapter is Claude."""
        adapter = AdapterRegistry.get_default()
        assert isinstance(adapter, ClaudeAdapter)

    def test_adapter_singleton(self):
        """Test adapter instances are singletons."""
        adapter1 = AdapterRegistry.get("claude")
        adapter2 = AdapterRegistry.get("claude")
        assert adapter1 is adapter2


class TestToolDetector:
    """Test ToolDetector class."""

    def test_detect_claude_from_config_dir(self, tmp_path):
        """Test detecting Claude from local config directory."""
        # Create .claude directory
        (tmp_path / ".claude").mkdir()

        detector = ToolDetector(base_path=tmp_path)
        detected = detector.detect_all()

        claude_tools = [t for t in detected if t.name == "claude"]
        assert len(claude_tools) == 1
        assert claude_tools[0].config_dir is not None

    def test_detect_cursor_from_config_dir(self, tmp_path):
        """Test detecting Cursor from local config directory."""
        # Create .cursor directory
        (tmp_path / ".cursor").mkdir()

        detector = ToolDetector(base_path=tmp_path)
        detected = detector.detect_all()

        cursor_tools = [t for t in detected if t.name == "cursor"]
        assert len(cursor_tools) == 1
        assert cursor_tools[0].config_dir is not None

    def test_detect_multiple_tools(self, tmp_path):
        """Test detecting multiple tools."""
        # Create both directories
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".cursor").mkdir()

        detector = ToolDetector(base_path=tmp_path)
        detected = detector.detect_all()

        names = {t.name for t in detected}
        assert "claude" in names
        assert "cursor" in names

    def test_detect_none(self, tmp_path):
        """Test detection when no tools are present."""
        detector = ToolDetector(base_path=tmp_path)
        detected = detector.detect_all()

        # All tools should have no config_dir
        for tool in detected:
            assert tool.config_dir is None

    def test_get_target_tools_from_config_dir(self, tmp_path):
        """Test get_target_tools returns tools with config dirs."""
        (tmp_path / ".claude").mkdir()

        detector = ToolDetector(base_path=tmp_path)
        tools = detector.get_target_tools()

        assert "claude" in tools

    def test_get_target_tools_default(self, tmp_path):
        """Test get_target_tools defaults to claude when nothing detected."""
        detector = ToolDetector(base_path=tmp_path)
        tools = detector.get_target_tools()

        assert tools == ["claude"]

    def test_is_tool_available(self, tmp_path):
        """Test is_tool_available check."""
        (tmp_path / ".claude").mkdir()

        detector = ToolDetector(base_path=tmp_path)
        assert detector.is_tool_available("claude")


class TestClaudeAdapter:
    """Test ClaudeAdapter implementation."""

    def setup_method(self):
        """Create adapter instance."""
        self.adapter = ClaudeAdapter()

    def test_format_values(self):
        """Test format property returns correct values."""
        fmt = self.adapter.format
        assert fmt.name == "claude"
        assert fmt.skill_dir == "skills"
        assert fmt.command_dir == "commands"
        assert fmt.agent_dir == "agents"
        assert fmt.rule_dir == "rules"
        assert fmt.skill_marker == "SKILL.md"

    def test_get_skill_path(self):
        """Test skill path building."""
        handle = ParsedHandle(
            username="kasperjunge",
            name="seo",
            path_segments=["seo"],
        )
        result = self.adapter.get_skill_path(Path(".claude"), handle)
        assert result == Path(".claude/skills/kasperjunge:seo")

    def test_get_skill_path_no_username(self):
        """Test skill path without username."""
        handle = ParsedHandle(name="seo", path_segments=["seo"])
        result = self.adapter.get_skill_path(Path(".claude"), handle)
        assert result == Path(".claude/skills/seo")

    def test_get_command_path(self):
        """Test command path building."""
        handle = ParsedHandle(
            username="kasperjunge",
            name="commit",
            path_segments=["commit"],
        )
        result = self.adapter.get_command_path(Path(".claude"), handle)
        assert result == Path(".claude/commands/kasperjunge/commit.md")

    def test_get_agent_path(self):
        """Test agent path building."""
        handle = ParsedHandle(
            username="kasperjunge",
            name="reviewer",
            path_segments=["reviewer"],
        )
        result = self.adapter.get_agent_path(Path(".claude"), handle)
        assert result == Path(".claude/agents/kasperjunge/reviewer.md")

    def test_get_rule_path(self):
        """Test rule path building."""
        handle = ParsedHandle(
            username="kasperjunge",
            name="no-console",
            path_segments=["no-console"],
        )
        result = self.adapter.get_rule_path(Path(".claude"), handle)
        assert result == Path(".claude/rules/kasperjunge/no-console.md")

    def test_is_skill_directory(self, tmp_path):
        """Test skill directory detection."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Skill")

        assert self.adapter.is_skill_directory(skill_dir)
        assert not self.adapter.is_skill_directory(tmp_path)

    def test_transform_rule_content_noop(self):
        """Test rule content transformation is no-op for Claude."""
        content = "# Rule\n\nSome content"
        result = self.adapter.transform_rule_content(content)
        assert result == content

    def test_discover_installed_skills(self, tmp_path):
        """Test discovering installed skills."""
        # Create skill directory
        skill_dir = tmp_path / "skills" / "kasperjunge:seo"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# SEO Skill")

        resources = self.adapter.discover_installed(tmp_path)
        skills = [r for r in resources if r.resource_type == "skill"]

        assert len(skills) == 1
        assert skills[0].name == "seo"
        assert skills[0].username == "kasperjunge"

    def test_discover_installed_commands(self, tmp_path):
        """Test discovering installed commands."""
        # Create command file
        cmd_dir = tmp_path / "commands" / "kasperjunge"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "commit.md").write_text("# Commit")

        resources = self.adapter.discover_installed(tmp_path)
        commands = [r for r in resources if r.resource_type == "command"]

        assert len(commands) == 1
        assert commands[0].name == "commit"
        assert commands[0].username == "kasperjunge"

    def test_discover_installed_rules(self, tmp_path):
        """Test discovering installed rules."""
        # Create rule file
        rule_dir = tmp_path / "rules" / "kasperjunge"
        rule_dir.mkdir(parents=True)
        (rule_dir / "no-console.md").write_text("# No Console")

        resources = self.adapter.discover_installed(tmp_path)
        rules = [r for r in resources if r.resource_type == "rule"]

        assert len(rules) == 1
        assert rules[0].name == "no-console"
        assert rules[0].username == "kasperjunge"


class TestCursorAdapter:
    """Test CursorAdapter implementation."""

    def setup_method(self):
        """Create adapter instance."""
        self.adapter = CursorAdapter()

    def test_format_values(self):
        """Test format property returns correct values."""
        fmt = self.adapter.format
        assert fmt.name == "cursor"
        assert fmt.config_dir == ".cursor"
        assert fmt.namespace_format == "nested"

    def test_get_skill_path_uses_nested(self):
        """Test skill path uses nested format (not colon)."""
        handle = ParsedHandle(
            username="kasperjunge",
            name="seo",
            path_segments=["seo"],
        )
        result = self.adapter.get_skill_path(Path(".cursor"), handle)
        # Cursor uses nested, not colon
        assert result == Path(".cursor/skills/kasperjunge/seo")

    def test_get_command_path(self):
        """Test command path building."""
        handle = ParsedHandle(
            username="kasperjunge",
            name="commit",
            path_segments=["commit"],
        )
        result = self.adapter.get_command_path(Path(".cursor"), handle)
        assert result == Path(".cursor/commands/kasperjunge/commit.md")

    def test_get_rule_path(self):
        """Test rule path building."""
        handle = ParsedHandle(
            username="kasperjunge",
            name="no-console",
            path_segments=["no-console"],
        )
        result = self.adapter.get_rule_path(Path(".cursor"), handle)
        assert result == Path(".cursor/rules/kasperjunge/no-console.md")

    def test_transform_rule_content_paths_to_globs(self):
        """Test rule content transforms paths: to globs:."""
        content = """---
paths: ["src/**/*.ts"]
---

# Rule content
"""
        result = self.adapter.transform_rule_content(content)
        assert "globs:" in result
        assert "paths:" not in result

    def test_transform_rule_content_no_paths(self):
        """Test rule content without paths: is unchanged."""
        content = "# Rule\n\nSome content"
        result = self.adapter.transform_rule_content(content)
        assert result == content

    def test_discover_installed_skills_nested(self, tmp_path):
        """Test discovering installed skills in nested format."""
        # Create skill directory in nested format
        skill_dir = tmp_path / "skills" / "kasperjunge" / "seo"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# SEO Skill")

        resources = self.adapter.discover_installed(tmp_path)
        skills = [r for r in resources if r.resource_type == "skill"]

        assert len(skills) == 1
        assert skills[0].name == "seo"
        assert skills[0].username == "kasperjunge"


class TestInstalledResource:
    """Test InstalledResource dataclass."""

    def test_installed_resource_creation(self):
        """Test creating an InstalledResource."""
        resource = InstalledResource(
            name="seo",
            resource_type="skill",
            path=Path("/path/to/skill"),
            username="kasperjunge",
        )
        assert resource.name == "seo"
        assert resource.resource_type == "skill"
        assert resource.path == Path("/path/to/skill")
        assert resource.username == "kasperjunge"

    def test_installed_resource_no_username(self):
        """Test InstalledResource without username."""
        resource = InstalledResource(
            name="commit",
            resource_type="command",
            path=Path("/path/to/command"),
        )
        assert resource.username is None


class TestDetectedTool:
    """Test DetectedTool dataclass."""

    def test_detected_tool_creation(self):
        """Test creating a DetectedTool."""
        tool = DetectedTool(
            name="claude",
            config_dir=Path(".claude"),
            global_dir=Path.home() / ".claude",
            cli_available=True,
            cli_path="/usr/local/bin/claude",
        )
        assert tool.name == "claude"
        assert tool.config_dir == Path(".claude")
        assert tool.cli_available is True

    def test_detected_tool_no_config(self):
        """Test DetectedTool with no config directories."""
        tool = DetectedTool(
            name="cursor",
            config_dir=None,
            global_dir=None,
            cli_available=False,
            cli_path=None,
        )
        assert tool.config_dir is None
        assert tool.cli_available is False


class TestAdapterProtocol:
    """Test that adapters conform to ToolAdapter protocol."""

    def test_claude_adapter_is_tool_adapter(self):
        """Test ClaudeAdapter implements ToolAdapter."""
        adapter = ClaudeAdapter()
        assert isinstance(adapter, ToolAdapter)

    def test_cursor_adapter_is_tool_adapter(self):
        """Test CursorAdapter implements ToolAdapter."""
        adapter = CursorAdapter()
        assert isinstance(adapter, ToolAdapter)
