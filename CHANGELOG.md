# Changelog

All notable changes to agr are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.6] - 2025-01-20

### Added

- **Multi-tool support**: Sync resources to multiple AI coding tools (Claude Code, Cursor)
  - Added `--tool` flag to `add`, `remove`, `sync`, and `list` commands
  - Added `[tools]` config section in `agr.toml` for persistent tool targets
  - Auto-detection of available tools based on config directories

- **Repository sync**: Install all resources from a GitHub repository with one command
  - Added `agr sync owner/repo` syntax
  - Added `--overwrite` flag to replace existing resources
  - Added `--yes` flag to skip confirmation prompt

- **Rules resource type**: Support for rule files that define constraints for Claude
  - Rules install to `.claude/rules/` with nested path structure
  - Added `rule` to valid resource types

- **PACKAGE.md support**: Explicit package identification via marker files
  - Packages can define custom namespaces via `name` field in frontmatter
  - Auto-detect resource type from parent directories

- **Tool adapter infrastructure**: Foundation for supporting multiple AI coding tools
  - Added `ClaudeAdapter` and `CursorAdapter`
  - Centralized path constants derived from adapter format

### Changed

- Improved path namespacing for all resource types
- Enhanced handle parsing for 3-part slash handles (owner/repo/resource)

## [0.5.0] - 2025-01-15

### Added

- Initial unified CLI with auto-detection
- `agr add` command with automatic resource type detection
- `agr remove` command with auto-detection
- `agrx` for temporary resource execution
- `agr sync` for synchronizing resources from `agr.toml`
- `agr list` for showing installed resources
- `agr init` for scaffolding new resources
- Support for skills, commands, agents, and packages
- Namespaced resource paths (colon-flattened for skills, nested for commands/agents)
- Local authoring workflow with `resources/` convention directories

## [0.4.0] - 2025-01-10

### Added

- Local dependency support in `agr.toml`
- Package explosion for installing package contents
- Workspace support for organizing related dependencies

### Changed

- Migrated config format from tables to unified list format
- Auto-migration of old `agr.toml` format on load

## [0.3.0] - 2025-01-05

### Added

- GitHub integration for fetching resources
- Resource discovery from repository structure
- Bundle support for multi-resource packages

## [0.2.0] - 2024-12-20

### Added

- Basic CLI structure with Typer
- Rich console output
- TOML configuration support

## [0.1.0] - 2024-12-15

### Added

- Initial release
- Core project structure
