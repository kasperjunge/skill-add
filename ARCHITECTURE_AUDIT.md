# Architecture Audit: Agent Resources (agr)

> **Audit Date:** 2026-01-19
> **Scope:** DRY improvements, multi-tool support (Claude Code, Codex, Cursor, GitHub Copilot), auto-detection, and architectural recommendations

---

## Implementation Progress

| Issue | Status | Notes |
|-------|--------|-------|
| **#1: Hardcoded `.claude` references** | ✅ **ADDRESSED** | Created `agr/constants.py` with `TOOL_DIR_NAME` constant. Updated all code paths in `paths.py`, `types.py`, `resolver.py`, `bundle.py`, and `init.py` to use constants. |
| **#2: Error handling patterns** | ✅ **ADDRESSED** | Added `error_exit()` and `warn()` helpers to `agr/cli/paths.py`. Updated all CLI modules (`handlers.py`, `init.py`, `add.py`, `remove.py`, `run.py`) to use standardized error handling. |
| **#3: SKILL.md detection patterns** | ⏳ Pending | To be centralized in future iteration |
| **#4: Tool abstraction layer** | ⏳ Pending | Adapter pattern proposed but not yet implemented |

---

## Executive Summary

The `agr` codebase demonstrates solid foundational architecture with well-designed abstractions (`ResourceType`, `ResourceConfig`, `ParsedHandle`). However, there are significant opportunities for improvement:

1. ~~**144+ hardcoded `.claude` references** that prevent multi-tool support~~ ✅ **ADDRESSED** - Now uses `TOOL_DIR_NAME` constant from `agr/constants.py`
2. ~~**52+ repeated error handling patterns** that increase maintenance burden~~ ✅ **ADDRESSED** - Now uses `error_exit()` helper from `agr/cli/paths.py`
3. **18+ SKILL.md detection patterns** that could be centralized
4. **No tool abstraction layer** - currently tightly coupled to Claude Code

This audit provides a roadmap for transforming `agr` into a universal AI coding tool resource manager.

---

## Part 1: Current Architecture Analysis

### 1.1 Strengths

| Strength | Implementation | Location |
|----------|----------------|----------|
| **Clean resource type abstraction** | `ResourceType` enum + `ResourceConfig` dataclass | `agr/fetcher/types.py` |
| **Centralized handle parsing** | `ParsedHandle` with format conversion | `agr/handle.py` |
| **Three-tier resolution** | agr.toml → .claude/ → repo root | `agr/resolver.py` |
| **Auto-migration for config** | Old format → new format seamless | `agr/config.py` |
| **Context manager for downloads** | Prevents double-downloads, auto-cleanup | `agr/fetcher/download.py` |

### 1.2 Current Data Flow

```
User Input: "agr add kasperjunge/seo"
    │
    ├── Parse Handle (handle.py)
    │   └── ParsedHandle(username="kasperjunge", name="seo", path_segments=["seo"])
    │
    ├── Download Repo (fetcher/download.py)
    │   └── Tarball → /tmp/extracted/
    │
    ├── Discover Resource (fetcher/discovery.py)
    │   └── Check .claude/skills/, .claude/commands/, .claude/agents/
    │
    ├── Install Resource (fetcher/resource.py)
    │   └── Copy to .claude/skills/kasperjunge:seo/
    │
    └── Update Config (config.py)
        └── Add to agr.toml dependencies
```

### 1.3 Module Responsibilities

```
agr/
├── cli/                    # User interaction layer
│   ├── main.py            # Typer command routing
│   ├── add.py             # Install resources
│   ├── remove.py          # Uninstall resources
│   ├── sync.py            # Batch install from agr.toml
│   ├── list.py            # Display installed resources
│   ├── init.py            # Scaffold new projects
│   ├── run.py             # Temporary resource execution (agrx)
│   ├── paths.py           # Path utilities, constants
│   ├── handlers.py        # Business logic
│   └── discovery.py       # Local resource detection
│
├── fetcher/               # Resource acquisition layer
│   ├── types.py           # ResourceType, ResourceConfig
│   ├── download.py        # HTTP download, tarball extraction
│   ├── resource.py        # Single resource installation
│   ├── bundle.py          # Multi-resource package handling
│   └── discovery.py       # Remote resource detection
│
├── config.py              # Configuration management
├── resolver.py            # Resource resolution strategies
├── handle.py              # Handle parsing/conversion
├── utils.py               # Utility functions
├── scaffold.py            # Project initialization
├── github.py              # Git/GitHub integration
└── exceptions.py          # Custom exceptions
```

---

## Part 2: DRY Violations Analysis

### 2.1 Critical: Hardcoded Tool Directory (144 occurrences) ✅ ADDRESSED

**Problem:** The string `.claude` appears 144 times across 16 files.

**Files Most Affected:**
- `agr/resolver.py` - 23 occurrences
- `agr/fetcher/bundle.py` - 15 occurrences
- `agr/handle.py` - 14 occurrences
- `agr/cli/handlers.py` - 13 occurrences

**Impact:** Makes multi-tool support impossible without massive search-replace.

**Solution:** ✅ **IMPLEMENTED**
```python
# agr/constants.py (created)
TOOL_DIR_NAME = ".claude"
SKILLS_SUBDIR = "skills"
COMMANDS_SUBDIR = "commands"
AGENTS_SUBDIR = "agents"
PACKAGES_SUBDIR = "packages"
```

All code paths in `paths.py`, `types.py`, `resolver.py`, `bundle.py`, and `init.py` now use these constants.

### 2.2 High: SKILL.md Detection Pattern (18 occurrences)

**Problem:** This pattern appears 18 times:
```python
if skill_path.is_dir() and (skill_path / "SKILL.md").exists():
```

**Files:**
- `agr/resolver.py:163,240,274,345`
- `agr/cli/handlers.py:279,329`
- `agr/cli/discovery.py:64,76,150,210,270`
- `agr/fetcher/discovery.py:44`
- `agr/fetcher/bundle.py:100,282`

**Solution:**
```python
# agr/utils.py
def is_skill_directory(path: Path) -> bool:
    """Check if a directory contains a valid skill (has SKILL.md)."""
    return path.is_dir() and (path / SKILL_MARKER).exists()
```

### 2.3 High: Error Handling Pattern (52 occurrences) ✅ ADDRESSED

**Problem:** Two inconsistent patterns used throughout:
```python
# Pattern A
typer.echo(f"Error: {message}", err=True)
raise typer.Exit(1)

# Pattern B
console.print(f"[red]Error: {message}[/red]")
raise typer.Exit(1)
```

**Solution:** ✅ **IMPLEMENTED**
```python
# agr/cli/paths.py (added)
def error_exit(message: str, code: int = 1) -> NoReturn:
    """Print error message and exit with code."""
    console.print(f"[red]Error: {message}[/red]")
    raise typer.Exit(code)

def warn(message: str) -> None:
    """Print warning message."""
    console.print(f"[yellow]Warning: {message}[/yellow]")
```

All CLI modules (`handlers.py`, `init.py`, `add.py`, `remove.py`, `run.py`) now use `error_exit()` for consistent error handling. Re-exported via `agr/cli/common.py`.

### 2.4 Medium: Type-to-Enum Mapping (3+ occurrences)

**Problem:** Repeated mapping definitions:
```python
# Found in handlers.py:566, 705, sync.py:26
type_map = {
    "skill": (ResourceType.SKILL, "skills"),
    "command": (ResourceType.COMMAND, "commands"),
    "agent": (ResourceType.AGENT, "agents"),
}
```

**Solution:** Already have `TYPE_TO_SUBDIR` in paths.py. Extend it:
```python
# agr/fetcher/types.py
def string_to_resource_type(type_str: str) -> ResourceType:
    """Convert string to ResourceType enum."""
    mapping = {
        "skill": ResourceType.SKILL,
        "command": ResourceType.COMMAND,
        "agent": ResourceType.AGENT,
    }
    if type_str not in mapping:
        raise ValueError(f"Unknown resource type: {type_str}")
    return mapping[type_str]
```

### 2.5 Medium: Config Load Pattern (13 occurrences)

**Problem:** Repeated null-checking after config load:
```python
config_path = find_config()
if not config_path:
    # handle not found
    return
config = AgrConfig.load(config_path)
```

**Solution:**
```python
# agr/config.py
def load_config_or_none() -> tuple[AgrConfig | None, Path | None]:
    """Load config if exists, return (None, None) if not found."""
    config_path = find_config()
    if not config_path:
        return None, None
    return AgrConfig.load(config_path), config_path
```

### 2.6 Summary: DRY Violations by Severity

| Severity | Issue | Count | Effort | Status |
|----------|-------|-------|--------|--------|
| **Critical** | Hardcoded `.claude` | 144 | High | ✅ ADDRESSED |
| **High** | SKILL.md detection | 18 | Low | ⏳ Pending |
| **High** | Error handling | 52 | Medium | ✅ ADDRESSED |
| **Medium** | Type mapping | 3+ | Low | ⏳ Pending |
| **Medium** | Config load | 13 | Low | ⏳ Pending |
| **Low** | Parent mkdir | 9 | Low | ⏳ Pending |

---

## Part 3: Multi-Tool Support Architecture

### 3.1 Current Tool Support

The codebase only supports Claude Code:
- Hardcoded `.claude/` directory
- Hardcoded `SKILL.md` marker
- No abstraction for tool-specific behavior

### 3.2 Target Tool Matrix

| Tool | Config Dir | Skill Marker | Namespace Format | Config File |
|------|------------|--------------|------------------|-------------|
| **Claude Code** | `.claude/` | `SKILL.md` | Colon (`:`) | `agr.toml` |
| **Cursor** | `.cursor/` | `SKILL.md` | Colon (`:`) | `agr.toml` |
| **OpenCode** | `.opencode/` | `SKILL.md` | Nested | `agr.toml` |
| **Codex** | `.codex/` | TBD | TBD | `agr.toml` |
| **GitHub Copilot** | `.github/` | Rules-based | Flat | `copilot.yml` |

### 3.3 Proposed: Tool Adapter Pattern

```python
# agr/adapters/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ToolFormat:
    """Tool-specific format configuration."""
    name: str                    # "claude", "cursor", "opencode"
    display_name: str            # "Claude Code", "Cursor", "OpenCode"
    config_dir: str              # ".claude", ".cursor", ".opencode"
    skill_dir: str               # "skills"
    command_dir: str             # "commands"
    agent_dir: str               # "agents"
    skill_marker: str            # "SKILL.md"
    namespace_format: str        # "colon" | "nested" | "flat"
    supports_bundles: bool       # True if tool supports bundles


class ToolAdapter(ABC):
    """Base class for tool-specific adapters."""

    @property
    @abstractmethod
    def format(self) -> ToolFormat:
        """Return the tool format configuration."""
        pass

    @abstractmethod
    def get_skill_path(self, base: Path, handle: "ParsedHandle") -> Path:
        """Build skill installation path for this tool."""
        pass

    @abstractmethod
    def get_command_path(self, base: Path, handle: "ParsedHandle") -> Path:
        """Build command installation path for this tool."""
        pass

    @abstractmethod
    def get_agent_path(self, base: Path, handle: "ParsedHandle") -> Path:
        """Build agent installation path for this tool."""
        pass

    @abstractmethod
    def is_skill_directory(self, path: Path) -> bool:
        """Check if directory contains a valid skill for this tool."""
        pass

    @abstractmethod
    def discover_installed(self, base: Path) -> list["DiscoveredResource"]:
        """Discover installed resources for this tool."""
        pass
```

### 3.4 Proposed: Claude Code Adapter (Reference Implementation)

```python
# agr/adapters/claude.py
from pathlib import Path
from .base import ToolAdapter, ToolFormat


class ClaudeCodeAdapter(ToolAdapter):
    """Adapter for Claude Code."""

    @property
    def format(self) -> ToolFormat:
        return ToolFormat(
            name="claude",
            display_name="Claude Code",
            config_dir=".claude",
            skill_dir="skills",
            command_dir="commands",
            agent_dir="agents",
            skill_marker="SKILL.md",
            namespace_format="colon",  # kasperjunge:seo
            supports_bundles=True,
        )

    def get_skill_path(self, base: Path, handle: ParsedHandle) -> Path:
        dirname = handle.to_skill_dirname()  # Uses colon format
        return base / self.format.config_dir / self.format.skill_dir / dirname

    def get_command_path(self, base: Path, handle: ParsedHandle) -> Path:
        if handle.username:
            return base / self.format.config_dir / self.format.command_dir / handle.username / f"{handle.simple_name}.md"
        return base / self.format.config_dir / self.format.command_dir / f"{handle.simple_name}.md"

    def get_agent_path(self, base: Path, handle: ParsedHandle) -> Path:
        if handle.username:
            return base / self.format.config_dir / self.format.agent_dir / handle.username / f"{handle.simple_name}.md"
        return base / self.format.config_dir / self.format.agent_dir / f"{handle.simple_name}.md"

    def is_skill_directory(self, path: Path) -> bool:
        return path.is_dir() and (path / self.format.skill_marker).exists()

    def discover_installed(self, base: Path) -> list[DiscoveredResource]:
        # Implementation for discovering installed Claude Code resources
        ...
```

### 3.5 Proposed: Adapter Registry

```python
# agr/adapters/registry.py
from typing import Type
from .base import ToolAdapter
from .claude import ClaudeCodeAdapter
from .cursor import CursorAdapter
from .opencode import OpenCodeAdapter


class AdapterRegistry:
    """Registry for tool adapters."""

    _adapters: dict[str, Type[ToolAdapter]] = {
        "claude": ClaudeCodeAdapter,
        "cursor": CursorAdapter,
        "opencode": OpenCodeAdapter,
    }

    _instances: dict[str, ToolAdapter] = {}

    @classmethod
    def get(cls, tool_name: str) -> ToolAdapter:
        """Get adapter instance by tool name."""
        if tool_name not in cls._instances:
            if tool_name not in cls._adapters:
                raise ValueError(f"Unknown tool: {tool_name}")
            cls._instances[tool_name] = cls._adapters[tool_name]()
        return cls._instances[tool_name]

    @classmethod
    def register(cls, name: str, adapter_class: Type[ToolAdapter]) -> None:
        """Register a new adapter."""
        cls._adapters[name] = adapter_class

    @classmethod
    def all_names(cls) -> list[str]:
        """Get all registered tool names."""
        return list(cls._adapters.keys())
```

---

## Part 4: Auto-Detection System

### 4.1 Detection Strategy

Auto-detect which tool(s) a user has by checking for:
1. **Config directories**: `.claude/`, `.cursor/`, `.opencode/`, etc.
2. **Config files**: `agr.toml`, `cursor.toml`, etc.
3. **Environment variables**: `CLAUDE_CODE_PATH`, `CURSOR_PATH`, etc.
4. **Running processes**: Check if tools are currently running

### 4.2 Proposed: Tool Detector

```python
# agr/detection.py
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from .adapters.registry import AdapterRegistry


@dataclass
class DetectedTool:
    """Information about a detected tool."""
    name: str
    config_dir: Path
    is_active: bool  # Tool is running
    has_resources: bool  # Has installed resources


class ToolDetector:
    """Detect which AI coding tools are present."""

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.cwd()

    def detect_all(self) -> list[DetectedTool]:
        """Detect all present tools."""
        detected = []
        for name in AdapterRegistry.all_names():
            adapter = AdapterRegistry.get(name)
            config_dir = self.base_path / adapter.format.config_dir

            if config_dir.exists():
                detected.append(DetectedTool(
                    name=name,
                    config_dir=config_dir,
                    is_active=self._is_tool_running(name),
                    has_resources=self._has_resources(config_dir, adapter),
                ))
        return detected

    def detect_primary(self) -> Optional[DetectedTool]:
        """Detect the primary (most likely in use) tool."""
        detected = self.detect_all()

        # Priority: running tool > has resources > first found
        running = [t for t in detected if t.is_active]
        if running:
            return running[0]

        with_resources = [t for t in detected if t.has_resources]
        if with_resources:
            return with_resources[0]

        return detected[0] if detected else None

    def _is_tool_running(self, name: str) -> bool:
        """Check if a tool is currently running."""
        # Platform-specific process detection
        import subprocess
        try:
            if name == "claude":
                result = subprocess.run(["pgrep", "-f", "claude"], capture_output=True)
                return result.returncode == 0
            # Add other tools...
        except Exception:
            return False
        return False

    def _has_resources(self, config_dir: Path, adapter: "ToolAdapter") -> bool:
        """Check if config dir has any installed resources."""
        skills_dir = config_dir / adapter.format.skill_dir
        commands_dir = config_dir / adapter.format.command_dir
        agents_dir = config_dir / adapter.format.agent_dir

        return any(d.exists() and any(d.iterdir())
                   for d in [skills_dir, commands_dir, agents_dir])
```

### 4.3 Proposed: Multi-Tool Sync

```python
# agr/sync_manager.py
from pathlib import Path
from typing import Optional
from .adapters.registry import AdapterRegistry
from .detection import ToolDetector, DetectedTool


class SyncManager:
    """Manage resource synchronization across multiple tools."""

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.cwd()
        self.detector = ToolDetector(self.base_path)

    def sync_to_all(self, source_tool: str, resource_handle: str) -> dict[str, bool]:
        """Sync a resource from source tool to all detected tools.

        Returns dict of {tool_name: success_bool}
        """
        detected = self.detector.detect_all()
        source_adapter = AdapterRegistry.get(source_tool)
        results = {}

        for target in detected:
            if target.name == source_tool:
                continue  # Skip source

            target_adapter = AdapterRegistry.get(target.name)
            try:
                self._sync_resource(source_adapter, target_adapter, resource_handle)
                results[target.name] = True
            except Exception as e:
                results[target.name] = False
                # Log error

        return results

    def sync_all_resources(self, source_tool: str) -> dict[str, dict[str, bool]]:
        """Sync all resources from source tool to all other detected tools."""
        source_adapter = AdapterRegistry.get(source_tool)
        source_dir = self.base_path / source_adapter.format.config_dir

        resources = source_adapter.discover_installed(source_dir)
        results = {}

        for resource in resources:
            handle = resource.to_handle_string()
            results[handle] = self.sync_to_all(source_tool, handle)

        return results

    def _sync_resource(
        self,
        source: "ToolAdapter",
        target: "ToolAdapter",
        handle: str
    ) -> None:
        """Sync a single resource between tools."""
        # Implementation: copy + transform as needed
        ...
```

---

## Part 5: Configuration Enhancement

### 5.1 Enhanced agr.toml Format

```toml
# agr.toml - Enhanced for multi-tool support

# Tool configuration
[tools]
default = "claude"  # Primary tool
sync_to = ["cursor", "opencode"]  # Auto-sync to these tools

# Dependencies (unchanged, but now tool-aware)
dependencies = [
    { handle = "kasperjunge/commit", type = "skill" },
    { handle = "dsjacobsen/golang-pro", type = "skill" },
    { path = "./resources/commands/docs.md", type = "command" },
]

# Tool-specific overrides (optional)
[tools.claude]
namespace_format = "colon"

[tools.cursor]
namespace_format = "colon"

[tools.opencode]
namespace_format = "nested"

# Packages (unchanged)
[packages.myworkspace]
path = "./packages/myworkspace"
dependencies = [
    { path = "./skills/tool-use", type = "skill" },
]
```

### 5.2 Backward Compatibility

The enhanced config maintains full backward compatibility:
- Old configs without `[tools]` section default to Claude Code
- Migration logic auto-detects and preserves existing behavior
- New features are opt-in

---

## Part 6: Implementation Roadmap

### Phase 1: DRY Cleanup (Foundation) - PARTIALLY COMPLETE
**Estimated complexity: Low-Medium**

1. ✅ Create `agr/constants.py` with centralized constants
2. ⏳ Add `is_skill_directory()` helper to `agr/utils.py`
3. ✅ Add `error_exit()` and `warn()` to `agr/cli/paths.py`
4. ⏳ Add `string_to_resource_type()` to `agr/fetcher/types.py`
5. ⏳ Add `load_config_or_none()` to `agr/config.py`
6. ✅ Replace `.claude` hardcodes with constant (code paths updated)
7. ⏳ Replace all 18 SKILL.md checks with helper
8. ✅ Replace all 52 error patterns with helper
9. ✅ **Tests:** Unit tests for new helpers (`test_constants.py`, `test_paths.py`)

### Phase 2: Adapter Infrastructure
**Estimated complexity: Medium**

1. Create `agr/adapters/` package
2. Implement `ToolAdapter` base class
3. Implement `ClaudeCodeAdapter` (refactor existing logic)
4. Implement `AdapterRegistry`
5. Refactor `fetcher/` to use adapters
6. Refactor `cli/` to use adapters
7. **Tests:** Adapter interface tests, Claude adapter tests

### Phase 3: Multi-Tool Support
**Estimated complexity: Medium-High**

1. Implement `CursorAdapter`
2. Implement `OpenCodeAdapter`
3. Implement `ToolDetector`
4. Add `--tool` flag to CLI commands
5. Update `agr.toml` parser for `[tools]` section
6. **Tests:** Cross-tool installation tests, detection tests

### Phase 4: Sync System
**Estimated complexity: High**

1. Implement `SyncManager`
2. Add `agr sync --to-all` command
3. Add `agr sync --from <tool>` command
4. Add file watcher for automatic sync (optional)
5. **Tests:** Multi-tool sync tests, conflict resolution tests

### Phase 5: Additional Tools
**Estimated complexity: Per-tool**

1. Research Codex format and implement adapter
2. Research GitHub Copilot format and implement adapter
3. Add any tool-specific transformations needed
4. **Tests:** Tool-specific installation and discovery tests

---

## Part 7: Critical Files to Modify

### High-Impact Files (Modify First)

| File | Changes | Impact | Status |
|------|---------|--------|--------|
| `agr/fetcher/types.py` | Add constants, type converter | Foundation | ✅ Constants added |
| `agr/utils.py` | Add `is_skill_directory()` | 18 replacements | ⏳ Pending |
| `agr/cli/paths.py` | Add error helpers, use constants | 52+ replacements | ✅ Done |
| `agr/handle.py` | Use constants instead of hardcoded | 14 replacements | ⏳ Pending |
| `agr/resolver.py` | Use constants, helpers | 23 replacements | ✅ Done |

### New Files Created

| File | Purpose | Status |
|------|---------|--------|
| `agr/constants.py` | Centralized constants | ✅ Created |
| `tests/test_constants.py` | Tests for constants | ✅ Created |

### New Files to Create (Future)

| File | Purpose |
|------|---------|
| `agr/adapters/__init__.py` | Adapter package |
| `agr/adapters/base.py` | Base adapter class |
| `agr/adapters/claude.py` | Claude Code adapter |
| `agr/adapters/cursor.py` | Cursor adapter |
| `agr/adapters/opencode.py` | OpenCode adapter |
| `agr/adapters/registry.py` | Adapter registry |
| `agr/detection.py` | Tool detection |
| `agr/sync_manager.py` | Multi-tool sync |

---

## Part 8: Testing Strategy

### 8.1 New Test Files Needed

```
tests/
├── test_constants.py          # Constants and helpers
├── test_adapters/
│   ├── test_base.py           # Adapter interface contracts
│   ├── test_claude.py         # Claude adapter
│   ├── test_cursor.py         # Cursor adapter
│   └── test_registry.py       # Registry functionality
├── test_detection.py          # Tool detection
├── test_sync_manager.py       # Multi-tool sync
└── fixtures/
    ├── cursor_project/        # Cursor test fixture
    └── opencode_project/      # OpenCode test fixture
```

### 8.2 Testing Principles

1. **Contract Testing**: All adapters must pass base interface tests
2. **Cross-Tool Tests**: Verify resources work across all supported tools
3. **Migration Tests**: Ensure backward compatibility with old configs
4. **Detection Tests**: Test auto-detection across scenarios

---

## Part 9: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing installs | Medium | High | Phased rollout, migration scripts |
| Tool format changes | Medium | Medium | Adapter abstraction isolates changes |
| Performance regression | Low | Medium | Benchmark critical paths |
| Config migration failures | Low | High | Extensive migration tests |

---

## Part 10: Success Metrics

1. **Code Quality**: Zero hardcoded tool references
2. **DRY Compliance**: Each pattern appears in exactly one place
3. **Tool Coverage**: Support for Claude, Cursor, OpenCode minimum
4. **Test Coverage**: >90% on adapter and sync code
5. **User Experience**: Single command syncs to all tools

---

## Appendix A: Quick Reference - Current Violations

```bash
# Count .claude references
grep -r "\.claude" --include="*.py" agr/ | wc -l  # 144

# Count SKILL.md pattern
grep -r "SKILL.md" --include="*.py" agr/ | wc -l  # 23

# Count error exit patterns
grep -r "raise typer.Exit" --include="*.py" agr/ | wc -l  # 52
```

## Appendix B: File Dependencies Graph

```
constants.py (NEW)
    ↓
utils.py ←──────────────────────────────────────┐
    ↓                                           │
fetcher/types.py ←──────────────────────────────┤
    ↓                                           │
adapters/base.py (NEW)                          │
    ↓                                           │
adapters/claude.py (NEW) ←──────────────────────┤
adapters/cursor.py (NEW)                        │
adapters/opencode.py (NEW)                      │
    ↓                                           │
adapters/registry.py (NEW)                      │
    ↓                                           │
detection.py (NEW)                              │
    ↓                                           │
sync_manager.py (NEW)                           │
    ↓                                           │
cli/paths.py ───────────────────────────────────┤
cli/handlers.py ────────────────────────────────┤
resolver.py ────────────────────────────────────┤
config.py ──────────────────────────────────────┘
```

---

*End of Architecture Audit*
