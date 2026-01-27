# Changelog

## [Unreleased]

### Added
- `@pytest.mark.requires_cli(name)` marker to skip tests when required CLI tools aren't installed
- **Multi-tool support**: Skills can now be installed to multiple AI coding tools simultaneously
- CLI testing infrastructure with fluent assertion API (`assert_cli(result).succeeded().stdout_contains("...")`)
- Test coverage for `agr add`, `remove`, `init`, `sync`, `list`, `--version`, `--help`
- Test coverage for `agrx` command with network marker for external dependency tests
- Edge case tests: adding already-installed skill, removing non-installed skill, init with existing directory
- Negative assertion helpers: `stdout_not_contains()`, `stderr_not_contains()`
- `@pytest.mark.network` marker for tests requiring network access (skip with `-m "not network"`)
- Cursor tool configuration with nested directory structure (e.g., `.cursor/skills/username/skill/`)
- `tools` configuration in `agr.toml` to specify target tools: `tools = ["claude", "cursor"]`
- `fetch_and_install_to_tools()` function for atomic multi-tool installation with rollback
- Validation that empty tools list raises `ValueError` in `fetch_and_install_to_tools`
- Type hints to `_get_installation_status` in list command

### Changed
- Reorganized `.gitignore` to group tool directories (`.claude/`, `.cursor/`) at top
- `ParsedHandle` now generates tool-appropriate paths (flat for Claude, nested for Cursor)
- Commands (`add`, `remove`, `list`, `sync`) now operate on all configured tools
- Rollback failures in `fetch_and_install_to_tools` now log warnings instead of being silently ignored
- Extracted common installation logic into `_copy_skill_to_destination` helper (DRY refactor)
- Tool names in `agr.toml` are now validated at config load time, catching typos early
- Error messages in `agr remove` now distinguish between "not found" and actual errors
- Release workflow now extracts notes from CHANGELOG.md instead of requiring RELEASE_NOTES.md
- Workflow checkouts the tag directly (fixes race condition with main branch)
- Only release job has contents:write permission (security improvement)
- Added tag format validation in workflow
- Updated /make-release skill to match new automated workflow (6 steps instead of 8)

### Fixed
- Use `SKILL_MARKER` constant instead of hardcoded `"SKILL.md"` string in sync command
- Shell injection risk in workflow by using environment variables instead of direct interpolation
- Hardcoded repository URL in release notes now uses GitHub context variables

## [0.6.4] - 2026-01-27

### Fixed
- Fix CI/CD publish workflow to use virtualenv instead of system Python

## [0.6.3] - 2026-01-27

### Fixed
- Added dev dependencies (ruff, pytest) to pyproject.toml for CI/CD
- Fixed linting and formatting issues for ruff compatibility

## [0.6.2] - 2026-01-27

### Changed
- Use `--` separator instead of `:` for installed skill directory names (Windows compatibility)
- Installed names now use format `username--skill` instead of `username:skill`
- Local skills use `local--skillname` instead of `local:skillname`

### Added
- Development workflow skills: `/research`, `/discover-solution-space`, `/make-plan`, `/code-review`, `/make-commit`, `/make-release`
- Skills implement a structured feature development cycle: research → solution exploration → planning → code review → commit → release
- Automatic migration of legacy colon-based directories during `agr sync`
- Validation to reject handles containing reserved `--` sequence
- Backward compatibility for parsing legacy colon-format installed names
- Comprehensive tests for separator migration and validation
- GitHub Actions workflow for automated PyPI publishing via trusted publishing (OIDC)
