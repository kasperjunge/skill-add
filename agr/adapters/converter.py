"""Resource format converter for bidirectional conversion between AI coding tools."""

import re
from dataclasses import dataclass, field
from enum import Enum


class WarningLevel(Enum):
    """Severity level for conversion warnings."""

    INFO = "info"
    WARNING = "warning"


@dataclass
class ConversionWarning:
    """A warning generated during format conversion."""

    field_name: str
    message: str
    level: WarningLevel = WarningLevel.WARNING


@dataclass
class ConversionResult:
    """Result of a format conversion operation."""

    content: str
    warnings: list[ConversionWarning] = field(default_factory=list)
    fields_dropped: list[str] = field(default_factory=list)
    fields_mapped: dict[str, str] = field(default_factory=dict)
    had_frontmatter: bool = True


@dataclass
class ToolConversionConfig:
    """Configuration for a tool's format differences.

    Attributes:
        name: Identifier for the tool
        specific_fields: Fields specific to this tool by resource type,
                        dropped when converting to other tools
        model_mappings: Model value mappings when converting from this tool
    """

    name: str
    specific_fields: dict[str, set[str]]
    model_mappings: dict[str, str] = field(default_factory=dict)


TOOL_CONFIGS: dict[str, ToolConversionConfig] = {
    "claude": ToolConversionConfig(
        name="claude",
        specific_fields={
            "skill": {
                "allowed-tools",
                "model",
                "context",
                "agent",
                "user-invocable",
                "hooks",
                "disable-model-invocation",
            },
            "agent": {"skills"},
            "rule": set(),
            "command": set(),
        },
        model_mappings={
            "sonnet": "fast",
            "opus": "inherit",
            "haiku": "fast",
        },
    ),
    "cursor": ToolConversionConfig(
        name="cursor",
        specific_fields={
            "skill": set(),
            "agent": {"readonly", "is_background"},
            "rule": {"description", "alwaysApply"},
            "command": set(),
        },
        model_mappings={
            "fast": "sonnet",
            "inherit": "opus",
        },
    ),
}

FIELD_MAPPINGS: dict[tuple[str, str, str], dict[str, str]] = {
    ("claude", "cursor", "rule"): {"paths": "globs"},
    ("cursor", "claude", "rule"): {"globs": "paths"},
}


class ResourceConverter:
    """Converts resource content between AI coding tool formats."""

    def __init__(self) -> None:
        self._tool_configs = TOOL_CONFIGS.copy()
        self._field_mappings = FIELD_MAPPINGS.copy()

    def convert(
        self,
        content: str,
        resource_type: str,
        source_tool: str,
        target_tool: str,
        strict: bool = False,
    ) -> ConversionResult:
        """Convert resource content from source to target tool format."""
        self._validate_tool(source_tool, "source")
        self._validate_tool(target_tool, "target")

        if source_tool == target_tool:
            return ConversionResult(content=content)

        frontmatter, body, had_frontmatter = self._parse_frontmatter(content)
        if not had_frontmatter:
            return ConversionResult(content=content, had_frontmatter=False)

        warnings: list[ConversionWarning] = []
        fields_dropped: list[str] = []
        fields_mapped: dict[str, str] = {}

        frontmatter, mapped = self._apply_field_mappings(
            frontmatter, resource_type, source_tool, target_tool
        )
        fields_mapped.update(mapped)

        frontmatter, model_warning = self._map_model_value(
            frontmatter, source_tool, target_tool
        )
        if model_warning:
            warnings.append(model_warning)

        frontmatter, dropped, drop_warnings = self._drop_tool_specific_fields(
            frontmatter, resource_type, source_tool, target_tool
        )
        fields_dropped.extend(dropped)
        warnings.extend(drop_warnings)

        if strict and fields_dropped:
            raise ValueError(
                f"Conversion would drop fields: {', '.join(fields_dropped)}. "
                "Use strict=False to allow this."
            )

        converted_content = self._rebuild_content(frontmatter, body)

        return ConversionResult(
            content=converted_content,
            warnings=warnings,
            fields_dropped=fields_dropped,
            fields_mapped=fields_mapped,
            had_frontmatter=True,
        )

    def _validate_tool(self, tool: str, label: str) -> None:
        """Validate that a tool is supported."""
        if tool not in self._tool_configs:
            available = ", ".join(self._tool_configs.keys())
            raise ValueError(
                f"Unknown {label} tool: {tool}. Available tools: {available}"
            )

    def _parse_frontmatter(self, content: str) -> tuple[dict[str, str], str, bool]:
        """Parse YAML frontmatter from content."""
        if not content.startswith("---"):
            return {}, content, False

        match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", content, re.DOTALL)
        if not match:
            return {}, content, False

        frontmatter_str = match.group(1)
        body = content[match.end() :]

        frontmatter: dict[str, str] = {}
        current_key: str | None = None
        current_value_lines: list[str] = []

        for line in frontmatter_str.split("\n"):
            key_match = re.match(r"^([a-zA-Z_-][a-zA-Z0-9_-]*)\s*:\s*(.*)$", line)
            if key_match:
                if current_key is not None:
                    frontmatter[current_key] = "\n".join(current_value_lines)
                current_key = key_match.group(1)
                value = key_match.group(2)
                current_value_lines = [value] if value else []
            elif current_key is not None:
                current_value_lines.append(line)

        if current_key is not None:
            frontmatter[current_key] = "\n".join(current_value_lines)

        return frontmatter, body, True

    def _apply_field_mappings(
        self,
        frontmatter: dict[str, str],
        resource_type: str,
        source_tool: str,
        target_tool: str,
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Apply field name mappings (e.g., paths -> globs)."""
        mappings = self._field_mappings.get((source_tool, target_tool, resource_type), {})
        if not mappings:
            return frontmatter, {}

        applied: dict[str, str] = {}
        result = frontmatter.copy()

        for old_name, new_name in mappings.items():
            if old_name in result:
                result[new_name] = result.pop(old_name)
                applied[old_name] = new_name

        return result, applied

    def _map_model_value(
        self,
        frontmatter: dict[str, str],
        source_tool: str,
        target_tool: str,
    ) -> tuple[dict[str, str], ConversionWarning | None]:
        """Map model values between tools (e.g., sonnet -> fast)."""
        if "model" not in frontmatter:
            return frontmatter, None

        source_config = self._tool_configs[source_tool]
        target_config = self._tool_configs[target_tool]
        old_value = frontmatter["model"].strip()
        result = frontmatter.copy()

        if old_value in source_config.model_mappings:
            intermediate = source_config.model_mappings[old_value]
            for target_model, mapped_to in target_config.model_mappings.items():
                if mapped_to == old_value or target_model == intermediate:
                    result["model"] = target_model
                    return result, ConversionWarning(
                        field_name="model",
                        message=f"Mapped model '{old_value}' to '{target_model}'",
                        level=WarningLevel.INFO,
                    )

        return result, ConversionWarning(
            field_name="model",
            message=f"Model value '{old_value}' kept as-is (no mapping to {target_tool})",
            level=WarningLevel.INFO,
        )

    def _drop_tool_specific_fields(
        self,
        frontmatter: dict[str, str],
        resource_type: str,
        source_tool: str,
        target_tool: str,
    ) -> tuple[dict[str, str], list[str], list[ConversionWarning]]:
        """Drop fields that are specific to the source tool."""
        source_config = self._tool_configs[source_tool]
        specific_fields = source_config.specific_fields.get(resource_type, set())

        dropped: list[str] = []
        warnings: list[ConversionWarning] = []
        result = frontmatter.copy()

        for field_name in specific_fields:
            if field_name in result:
                del result[field_name]
                dropped.append(field_name)
                warnings.append(
                    ConversionWarning(
                        field_name=field_name,
                        message=f"Field '{field_name}' is {source_tool}-specific and was dropped",
                        level=WarningLevel.WARNING,
                    )
                )

        return result, dropped, warnings

    def _rebuild_content(self, frontmatter: dict[str, str], body: str) -> str:
        """Rebuild content from frontmatter dict and body."""
        if not frontmatter:
            return body.lstrip("\n")

        lines = ["---"]
        for key, value in frontmatter.items():
            if "\n" in value:
                first_line, *rest = value.split("\n")
                lines.append(f"{key}: {first_line}" if first_line else f"{key}:")
                lines.extend(rest)
            else:
                lines.append(f"{key}: {value}" if value else f"{key}:")
        lines.append("---")

        if body:
            if not body.startswith("\n"):
                lines.append("")
            return "\n".join(lines) + body
        return "\n".join(lines) + "\n"

    def get_supported_tools(self) -> list[str]:
        """Get list of supported tool names."""
        return list(self._tool_configs.keys())

    def add_tool_config(self, config: ToolConversionConfig) -> None:
        """Add or update a tool configuration."""
        self._tool_configs[config.name] = config

    def add_field_mapping(
        self,
        source_tool: str,
        target_tool: str,
        resource_type: str,
        mappings: dict[str, str],
    ) -> None:
        """Add field mappings for a tool/resource combination."""
        key = (source_tool, target_tool, resource_type)
        if key in self._field_mappings:
            self._field_mappings[key].update(mappings)
        else:
            self._field_mappings[key] = mappings
