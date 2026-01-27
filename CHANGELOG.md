# Changelog

## [Unreleased]

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
