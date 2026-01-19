"""Tests for the resource format converter."""

import pytest

from agr.adapters.converter import (
    ConversionResult,
    ConversionWarning,
    FIELD_MAPPINGS,
    ResourceConverter,
    TOOL_CONFIGS,
    ToolConversionConfig,
    WarningLevel,
)


class TestParseFrontmatter:
    """Tests for _parse_frontmatter method."""

    def test_simple_frontmatter(self):
        converter = ResourceConverter()
        content = """---
name: test-skill
description: A test skill
---

Body content here.
"""
        frontmatter, body, had_frontmatter = converter._parse_frontmatter(content)

        assert had_frontmatter is True
        assert frontmatter["name"] == "test-skill"
        assert frontmatter["description"] == "A test skill"
        assert "Body content here." in body

    def test_no_frontmatter(self):
        converter = ResourceConverter()
        content = "Just plain content without frontmatter."

        frontmatter, body, had_frontmatter = converter._parse_frontmatter(content)

        assert had_frontmatter is False
        assert frontmatter == {}
        assert body == content

    def test_multiline_value(self):
        converter = ResourceConverter()
        content = """---
name: test
description: |
  Line 1
  Line 2
---

Body
"""
        frontmatter, body, had_frontmatter = converter._parse_frontmatter(content)

        assert had_frontmatter is True
        assert frontmatter["name"] == "test"
        assert "Line 1" in frontmatter["description"]
        assert "Line 2" in frontmatter["description"]

    def test_empty_value(self):
        converter = ResourceConverter()
        content = """---
name: test
description:
---

Body
"""
        frontmatter, body, had_frontmatter = converter._parse_frontmatter(content)

        assert had_frontmatter is True
        assert frontmatter["name"] == "test"
        assert frontmatter["description"] == ""

    def test_array_value(self):
        converter = ResourceConverter()
        content = """---
name: test
paths:
  - "src/**/*.ts"
  - "lib/**/*.ts"
---

Body
"""
        frontmatter, body, had_frontmatter = converter._parse_frontmatter(content)

        assert had_frontmatter is True
        assert "paths" in frontmatter
        assert "src/**/*.ts" in frontmatter["paths"]


class TestApplyFieldMappings:
    """Tests for _apply_field_mappings method."""

    def test_paths_to_globs(self):
        converter = ResourceConverter()
        frontmatter = {"paths": '["src/**/*.ts"]', "description": "A rule"}

        result, applied = converter._apply_field_mappings(
            frontmatter, "rule", "claude", "cursor"
        )

        assert "globs" in result
        assert "paths" not in result
        assert result["globs"] == '["src/**/*.ts"]'
        assert applied == {"paths": "globs"}

    def test_globs_to_paths(self):
        converter = ResourceConverter()
        frontmatter = {"globs": '["src/**/*.ts"]', "description": "A rule"}

        result, applied = converter._apply_field_mappings(
            frontmatter, "rule", "cursor", "claude"
        )

        assert "paths" in result
        assert "globs" not in result
        assert result["paths"] == '["src/**/*.ts"]'
        assert applied == {"globs": "paths"}

    def test_no_mapping_needed(self):
        converter = ResourceConverter()
        frontmatter = {"name": "test", "description": "A skill"}

        result, applied = converter._apply_field_mappings(
            frontmatter, "skill", "claude", "cursor"
        )

        assert result == frontmatter
        assert applied == {}

    def test_preserves_other_fields(self):
        converter = ResourceConverter()
        frontmatter = {"paths": '["src/**"]', "description": "desc", "name": "test"}

        result, applied = converter._apply_field_mappings(
            frontmatter, "rule", "claude", "cursor"
        )

        assert "globs" in result
        assert "description" in result
        assert "name" in result
        assert result["description"] == "desc"
        assert result["name"] == "test"


class TestMapModelValue:
    """Tests for _map_model_value method."""

    def test_sonnet_from_claude(self):
        converter = ResourceConverter()
        frontmatter = {"model": "sonnet", "name": "test"}

        result, warning = converter._map_model_value(frontmatter, "claude", "cursor")

        assert warning is not None
        assert warning.level == WarningLevel.INFO

    def test_no_model_field(self):
        converter = ResourceConverter()
        frontmatter = {"name": "test"}

        result, warning = converter._map_model_value(frontmatter, "claude", "cursor")

        assert result == frontmatter
        assert warning is None

    def test_unknown_model_value(self):
        converter = ResourceConverter()
        frontmatter = {"model": "unknown-model", "name": "test"}

        result, warning = converter._map_model_value(frontmatter, "claude", "cursor")

        assert result["model"] == "unknown-model"
        assert warning is not None
        assert "kept as-is" in warning.message


class TestDropToolSpecificFields:
    """Tests for _drop_tool_specific_fields method."""

    def test_claude_skill_fields(self):
        converter = ResourceConverter()
        frontmatter = {
            "name": "test",
            "allowed-tools": "Read, Write",
            "model": "sonnet",
            "context": "some context",
            "user-invocable": "true",
        }

        result, dropped, warnings = converter._drop_tool_specific_fields(
            frontmatter, "skill", "claude", "cursor"
        )

        assert "name" in result
        assert "allowed-tools" not in result
        assert "model" not in result
        assert "context" not in result
        assert "user-invocable" not in result
        assert set(dropped) == {"allowed-tools", "model", "context", "user-invocable"}
        assert len(warnings) == 4

    def test_cursor_agent_fields(self):
        converter = ResourceConverter()
        frontmatter = {
            "name": "test",
            "readonly": "true",
            "is_background": "true",
            "description": "An agent",
        }

        result, dropped, warnings = converter._drop_tool_specific_fields(
            frontmatter, "agent", "cursor", "claude"
        )

        assert "name" in result
        assert "description" in result
        assert "readonly" not in result
        assert "is_background" not in result
        assert set(dropped) == {"readonly", "is_background"}

    def test_no_fields_to_drop(self):
        converter = ResourceConverter()
        frontmatter = {"name": "test", "description": "A command"}

        result, dropped, warnings = converter._drop_tool_specific_fields(
            frontmatter, "command", "claude", "cursor"
        )

        assert result == frontmatter
        assert dropped == []
        assert warnings == []

    def test_unknown_resource_type_passthrough(self):
        converter = ResourceConverter()
        frontmatter = {"name": "test", "custom-field": "value"}

        result, dropped, warnings = converter._drop_tool_specific_fields(
            frontmatter, "unknown-type", "claude", "cursor"
        )

        assert result == frontmatter
        assert dropped == []
        assert warnings == []


class TestRebuildContent:
    """Tests for _rebuild_content method."""

    def test_simple_content(self):
        converter = ResourceConverter()
        frontmatter = {"name": "test", "description": "A test"}
        body = "\nBody content here.\n"

        result = converter._rebuild_content(frontmatter, body)

        assert result.startswith("---\n")
        assert "name: test" in result
        assert "description: A test" in result
        assert "---" in result
        assert "Body content here." in result

    def test_empty_frontmatter(self):
        converter = ResourceConverter()
        frontmatter = {}
        body = "\nBody content here.\n"

        result = converter._rebuild_content(frontmatter, body)

        assert not result.startswith("---")
        assert "Body content here." in result

    def test_multiline_value(self):
        converter = ResourceConverter()
        frontmatter = {"name": "test", "description": "Line 1\n  Line 2"}
        body = "\nBody\n"

        result = converter._rebuild_content(frontmatter, body)

        assert "---" in result
        assert "Line 1" in result
        assert "Line 2" in result

    def test_preserves_field_order(self):
        converter = ResourceConverter()
        frontmatter = {"first": "1", "second": "2", "third": "3"}
        body = "\n"

        result = converter._rebuild_content(frontmatter, body)

        first_pos = result.index("first:")
        second_pos = result.index("second:")
        third_pos = result.index("third:")

        assert first_pos < second_pos < third_pos


class TestSkillConversion:
    """Tests for skill resource conversion."""

    def test_claude_to_cursor(self):
        converter = ResourceConverter()
        content = """---
name: test-skill
description: A test skill
allowed-tools: Read, Write
model: sonnet
context: current-context
user-invocable: true
---

# Test Skill

This is the skill body.
"""
        result = converter.convert(content, "skill", "claude", "cursor")

        assert result.had_frontmatter is True
        assert "name: test-skill" in result.content
        assert "description: A test skill" in result.content
        assert "allowed-tools" not in result.content
        assert "model" not in result.content
        assert "context" not in result.content
        assert "user-invocable" not in result.content
        assert "# Test Skill" in result.content
        assert len(result.fields_dropped) == 4

    def test_cursor_to_claude(self):
        converter = ResourceConverter()
        content = """---
name: test-skill
description: A cursor skill
---

# Test Skill
"""
        result = converter.convert(content, "skill", "cursor", "claude")

        assert "name: test-skill" in result.content
        assert "description: A cursor skill" in result.content
        assert result.fields_dropped == []

    def test_without_frontmatter(self):
        converter = ResourceConverter()
        content = "# Test Skill\n\nJust body content."

        result = converter.convert(content, "skill", "claude", "cursor")

        assert result.content == content
        assert result.had_frontmatter is False


class TestAgentConversion:
    """Tests for agent resource conversion."""

    def test_claude_to_cursor(self):
        converter = ResourceConverter()
        content = """---
name: test-agent
skills:
  - skill1
  - skill2
---

Agent instructions.
"""
        result = converter.convert(content, "agent", "claude", "cursor")

        assert "name: test-agent" in result.content
        assert "skills" not in result.content
        assert "Agent instructions." in result.content
        assert "skills" in result.fields_dropped

    def test_cursor_to_claude(self):
        converter = ResourceConverter()
        content = """---
name: test-agent
readonly: true
is_background: false
---

Agent instructions.
"""
        result = converter.convert(content, "agent", "cursor", "claude")

        assert "name: test-agent" in result.content
        assert "readonly" not in result.content
        assert "is_background" not in result.content


class TestRuleConversion:
    """Tests for rule resource conversion."""

    def test_claude_to_cursor(self):
        converter = ResourceConverter()
        content = """---
paths:
  - "src/**/*.ts"
  - "lib/**/*.ts"
---

Always use TypeScript for type safety.
"""
        result = converter.convert(content, "rule", "claude", "cursor")

        assert "globs:" in result.content
        assert "paths:" not in result.content
        assert "src/**/*.ts" in result.content
        assert result.fields_mapped == {"paths": "globs"}

    def test_cursor_to_claude(self):
        converter = ResourceConverter()
        content = """---
globs:
  - "*.py"
description: Python rules
alwaysApply: true
---

Use type hints.
"""
        result = converter.convert(content, "rule", "cursor", "claude")

        assert "paths:" in result.content
        assert "globs:" not in result.content
        assert "description" not in result.content
        assert "alwaysApply" not in result.content
        assert result.fields_mapped == {"globs": "paths"}


class TestCommandConversion:
    """Tests for command resource conversion."""

    def test_passthrough(self):
        converter = ResourceConverter()
        content = """---
name: test-command
description: A test command
---

Command instructions.
"""
        result = converter.convert(content, "command", "claude", "cursor")

        assert "name: test-command" in result.content
        assert "description: A test command" in result.content
        assert result.fields_dropped == []


class TestStrictMode:
    """Tests for strict mode behavior."""

    def test_raises_on_dropped_fields(self):
        converter = ResourceConverter()
        content = """---
name: test
allowed-tools: Read
---

Body
"""
        with pytest.raises(ValueError) as exc_info:
            converter.convert(content, "skill", "claude", "cursor", strict=True)

        assert "would drop fields" in str(exc_info.value)
        assert "allowed-tools" in str(exc_info.value)

    def test_allows_clean_conversion(self):
        converter = ResourceConverter()
        content = """---
name: test
description: A command
---

Body
"""
        result = converter.convert(content, "command", "claude", "cursor", strict=True)

        assert "name: test" in result.content
        assert result.fields_dropped == []


class TestEdgeCases:
    """Tests for edge cases."""

    def test_same_tool_no_conversion(self):
        converter = ResourceConverter()
        content = """---
name: test
allowed-tools: Read
---

Body
"""
        result = converter.convert(content, "skill", "claude", "claude")

        assert result.content == content
        assert result.fields_dropped == []
        assert result.fields_mapped == {}

    def test_unknown_source_tool_raises(self):
        converter = ResourceConverter()

        with pytest.raises(ValueError) as exc_info:
            converter.convert("content", "skill", "unknown-tool", "cursor")

        assert "Unknown source tool" in str(exc_info.value)
        assert "unknown-tool" in str(exc_info.value)
        assert "Available tools" in str(exc_info.value)

    def test_unknown_target_tool_raises(self):
        converter = ResourceConverter()

        with pytest.raises(ValueError) as exc_info:
            converter.convert("content", "skill", "claude", "unknown-tool")

        assert "Unknown target tool" in str(exc_info.value)
        assert "unknown-tool" in str(exc_info.value)

    def test_empty_content(self):
        converter = ResourceConverter()
        result = converter.convert("", "skill", "claude", "cursor")

        assert result.content == ""
        assert result.had_frontmatter is False

    def test_frontmatter_only(self):
        converter = ResourceConverter()
        content = """---
name: test
---
"""
        result = converter.convert(content, "command", "claude", "cursor")

        assert "name: test" in result.content

    def test_malformed_frontmatter(self):
        converter = ResourceConverter()
        content = """---
name: test
no closing delimiter
"""
        result = converter.convert(content, "skill", "claude", "cursor")

        assert result.content == content
        assert result.had_frontmatter is False

    def test_special_characters_in_values(self):
        converter = ResourceConverter()
        content = """---
name: test-skill
description: A "quoted" value with special: chars
---

Body
"""
        result = converter.convert(content, "command", "claude", "cursor")

        assert "test-skill" in result.content
        assert 'A "quoted" value' in result.content

    def test_unknown_fields_preserved(self):
        converter = ResourceConverter()
        content = """---
name: test
future-field: some-value
another-unknown: data
---

Body
"""
        result = converter.convert(content, "skill", "claude", "cursor")

        assert "future-field: some-value" in result.content
        assert "another-unknown: data" in result.content


class TestExtensibility:
    """Tests for extensibility features."""

    def test_get_supported_tools(self):
        converter = ResourceConverter()
        tools = converter.get_supported_tools()

        assert "claude" in tools
        assert "cursor" in tools

    def test_add_new_tool_config(self):
        converter = ResourceConverter()
        new_config = ToolConversionConfig(
            name="codex",
            specific_fields={
                "skill": {"codex-only-field"},
                "agent": set(),
                "rule": set(),
                "command": set(),
            },
            model_mappings={"gpt-4": "sonnet"},
        )
        converter.add_tool_config(new_config)

        assert "codex" in converter.get_supported_tools()

        content = """---
name: test
codex-only-field: value
---

Body
"""
        result = converter.convert(content, "skill", "codex", "claude")
        assert "codex-only-field" not in result.content
        assert "codex-only-field" in result.fields_dropped

    def test_add_field_mapping(self):
        converter = ResourceConverter()
        converter.add_field_mapping(
            source_tool="claude",
            target_tool="cursor",
            resource_type="agent",
            mappings={"claude-agent-field": "cursor-agent-field"},
        )

        content = """---
name: test
claude-agent-field: value
---

Body
"""
        result = converter.convert(content, "agent", "claude", "cursor")
        assert "cursor-agent-field: value" in result.content
        assert "claude-agent-field" not in result.content
        assert result.fields_mapped == {"claude-agent-field": "cursor-agent-field"}

    def test_tool_configs_are_copied(self):
        converter1 = ResourceConverter()
        converter2 = ResourceConverter()

        converter1.add_tool_config(
            ToolConversionConfig(
                name="test-tool",
                specific_fields={"skill": set()},
            )
        )

        assert "test-tool" in converter1.get_supported_tools()
        assert "test-tool" not in converter2.get_supported_tools()

    def test_unknown_resource_type_passthrough(self):
        converter = ResourceConverter()
        content = """---
name: test
custom-field: value
---

Body
"""
        result = converter.convert(content, "widget", "claude", "cursor")

        assert "name: test" in result.content
        assert "custom-field: value" in result.content


class TestConversionWarning:
    """Tests for ConversionWarning dataclass."""

    def test_defaults(self):
        warning = ConversionWarning(field_name="test", message="A warning message")
        assert warning.level == WarningLevel.WARNING

    def test_info_level(self):
        warning = ConversionWarning(
            field_name="model", message="Model mapped", level=WarningLevel.INFO
        )
        assert warning.level == WarningLevel.INFO


class TestConversionResult:
    """Tests for ConversionResult dataclass."""

    def test_defaults(self):
        result = ConversionResult(content="test")

        assert result.warnings == []
        assert result.fields_dropped == []
        assert result.fields_mapped == {}
        assert result.had_frontmatter is True

    def test_all_fields(self):
        warnings = [ConversionWarning("field", "message")]
        result = ConversionResult(
            content="test",
            warnings=warnings,
            fields_dropped=["dropped"],
            fields_mapped={"old": "new"},
            had_frontmatter=False,
        )

        assert result.content == "test"
        assert result.warnings == warnings
        assert result.fields_dropped == ["dropped"]
        assert result.fields_mapped == {"old": "new"}
        assert result.had_frontmatter is False


class TestToolConversionConfig:
    """Tests for ToolConversionConfig dataclass."""

    def test_defaults(self):
        config = ToolConversionConfig(name="test", specific_fields={"skill": set()})

        assert config.name == "test"
        assert config.model_mappings == {}

    def test_with_model_mappings(self):
        config = ToolConversionConfig(
            name="test",
            specific_fields={"skill": {"field1", "field2"}},
            model_mappings={"model1": "model2"},
        )

        assert config.model_mappings == {"model1": "model2"}
        assert "field1" in config.specific_fields["skill"]


class TestGlobalConfigs:
    """Tests for global configuration constants."""

    def test_tool_configs_has_claude(self):
        assert "claude" in TOOL_CONFIGS
        assert TOOL_CONFIGS["claude"].name == "claude"

    def test_tool_configs_has_cursor(self):
        assert "cursor" in TOOL_CONFIGS
        assert TOOL_CONFIGS["cursor"].name == "cursor"

    def test_field_mappings_has_paths_globs(self):
        assert ("claude", "cursor", "rule") in FIELD_MAPPINGS
        assert FIELD_MAPPINGS[("claude", "cursor", "rule")] == {"paths": "globs"}
        assert ("cursor", "claude", "rule") in FIELD_MAPPINGS
        assert FIELD_MAPPINGS[("cursor", "claude", "rule")] == {"globs": "paths"}
