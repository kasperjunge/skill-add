## agr v0.7.1b1

Beta release adding GitHub Copilot support and private repository authentication.

### Highlights

- **GitHub Copilot Support**: Skills can now be installed to GitHub Copilot (`.github/skills/` for project, `~/.copilot/skills/` for global)
- **Private Repositories**: Install skills from private repos using GITHUB_TOKEN/GH_TOKEN environment variables

### What's Changed

- GitHub Copilot tool configuration with flat directory structure
- `global_config_dir` field in `ToolConfig` for tools with different personal/project paths
- Private repository support via GitHub token authentication
- `AuthenticationError` exception for 401/403 responses
- Comprehensive CLI integration tests for Cursor, Copilot, and private repos
- Tests for multi-tool scenarios and token security

---

**Full changelog**: https://github.com/kasperjunge/agent-resources/blob/main/CHANGELOG.md
