# Changelog

## [Unreleased]

### Changed
- Use `--` separator instead of `:` for installed skill directory names (Windows compatibility)
- Installed names now use format `username--skill` instead of `username:skill`
- Local skills use `local--skillname` instead of `local:skillname`

### Added
- Automatic migration of legacy colon-based directories during `agr sync`
- Validation to reject handles containing reserved `--` sequence
- Backward compatibility for parsing legacy colon-format installed names
- Comprehensive tests for separator migration and validation
