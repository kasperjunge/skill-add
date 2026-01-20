<div align="center">

# 🧩 agent-resources (agr)

**A package and project manager for Claude Code.**

Install skills, commands, and subagents from GitHub with a single command.

[![PyPI](https://img.shields.io/pypi/v/agr?color=blue)](https://pypi.org/project/agr/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## Highlights

- **One command installs agent skills from GitHub**: `agr add user/skill` — no manual file copying to `.claude/`
- **Try before you install**: `agrx user/skill` runs temporarily, then cleans up
- **Team reproducibility**: `agr.toml` tracks dependencies; `agr sync` installs everything
- **Multi-tool support**: Sync resources to Claude Code, Cursor, and other AI tools with `--tool` flag
- **Auto-detects resource type**: Skills, commands, subagents, rules — agr figures it out
- **Build your personal library**: Create a GitHub repo of your best skills and share them with anyone
- **Package related resources**: Package skills, commands, and subagents together for easy distribution
- **Install entire repositories**: `agr sync owner/repo` installs all resources from a GitHub repo
- **Stop editing `.claude/` directly**: Treat it like `.venv/` — let agr manage it, you manage source files

---

## Installation

No installation needed — run directly:

```bash
uvx agr add kasperjunge/hello-world
```

Or install permanently:

```bash
pip install agr
```

---

## Quick Start

### Install a resource

```bash
agr add kasperjunge/commit         # Semantic commit messages
agr add dsjacobsen/golang-pro      # Go development toolkit
```

Done. The resource is now available in Claude Code.

**Handle format:** `username/repo/resource` — if the repo is named `agent-resources`, omit it: `username/resource`

```bash
agr add alice/agent-resources/my-skill   # Full path
agr add alice/my-skill                   # Same thing (agent-resources is default)
agr add alice/my-repo/my-skill           # From a different repo
agr add alice/toolkit/nested/skill       # Nested resource: toolkit/nested/skill
```

### Try without installing

```bash
agrx kasperjunge/hello-world              # Runs and cleans up
agrx kasperjunge/hello-world "my prompt"  # With a prompt
agrx kasperjunge/hello-world -i           # Interactive mode
```

### Share with your team

```bash
# Your dependencies are tracked automatically
cat agr.toml
```

```toml
dependencies = [
    {handle = "kasperjunge/commit", type = "skill"},
    {handle = "dsjacobsen/golang-pro", type = "skill"},
]
```

```bash
# Teammates run one command
agr sync
```

---

## Commands

| Command | What it does |
|---------|-------------|
| `agr add <handle>` | Install a resource |
| `agr remove <name>` | Uninstall a resource |
| `agr sync` | Install all dependencies from `agr.toml` |
| `agr sync owner/repo` | Install all resources from a GitHub repo |
| `agr list` | Show installed resources with status |
| `agr init` | Set up authoring directories |
| `agr init skill <name>` | Create a new skill |
| `agr init command <name>` | Create a new command |
| `agr init agent <name>` | Create a new subagent |
| `agrx <handle>` | Run a resource temporarily |

Use `--tool claude --tool cursor` on any command to target specific AI tools.

---

## Create Your Own

### Set up your project

```bash
agr init
```

Creates the authoring structure:

```
resources/
├── skills/       # Your skills
├── commands/     # Your commands
├── agents/       # Your subagents
└── packages/     # Grouped resources
```

### Create a resource

```bash
agr init skill my-skill       # Creates resources/skills/my-skill/SKILL.md
agr init command deploy       # Creates resources/commands/deploy.md
agr init agent reviewer       # Creates resources/agents/reviewer.md
```

### Sync to Claude Code

```bash
agr sync
```

Your resources are now available in Claude Code.

### Share with the world

Push to GitHub. Others can install with:

```bash
agr add your-username/my-skill
```

---

## Community Resources

### Go Development — [@dsjacobsen](https://github.com/dsjacobsen/agent-resources)

```bash
agr add dsjacobsen/golang-pro      # Expert Go development
agr add dsjacobsen/go-reviewer     # Code review agent
```

1 skill, 9 agents, 11 commands for Go development.

### Drupal Development — [@madsnorgaard](https://github.com/madsnorgaard/agent-resources)

```bash
agr add madsnorgaard/drupal-expert      # Drupal 10/11 expertise
agr add madsnorgaard/drupal-migration   # D7-to-D10 migrations
```

4 skills, 1 agent, 5 commands for Drupal development.

---

**Built something?** [Share it here](https://github.com/kasperjunge/agent-resources-project/issues).

---

<div align="center">

**MIT License** · Made for the [Claude Code](https://claude.ai/code) community

</div>
