## agr v0.7.1b2

Manage which AI coding tools your skills sync to with the new `agr tools` command.

### Highlights

- **Tool Management CLI**: New `agr tools list/add/remove` commands to configure which tools (Claude, Cursor, Copilot) receive your skills
- **Multi-tool agrx**: Run temporary skills with any supported CLI using `agrx skill --tool cursor`

### What's Changed

- Added `agr tools` command group for managing configured tools
- Added `--tool` flag to `agrx` for specifying which CLI to use
- Fixed config being saved before sync completes in `agr tools add`
- Fixed tool remaining in config when skill deletion fails in `agr tools remove`
- Code cleanup: replaced hardcoded values with constants, added type annotations

---

**Full changelog**: https://github.com/kasperjunge/agent-resources/blob/main/CHANGELOG.md
