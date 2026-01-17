<div align="center">

# 🧩 agent-resources

**Share and install Claude Code skills, commands, and agents with a single command.**

*A package manager for AI agents.*

[![PyPI](https://img.shields.io/pypi/v/agr?color=blue)](https://pypi.org/project/agr/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Quick Start](#quick-start) • [Dependency Tracking](#dependency-tracking) • [Create Your Own](#create-your-own) • [Community](#community-resources)

</div>

---

## Quick Start

No installation needed. Just run:

```bash
uvx agr add kasperjunge/hello-world
```

**That's it.** The skill is now available in Claude Code. The resource type (skill, command, agent, or bundle) is auto-detected.

Or install permanently:

```bash
pip install agr
agr add kasperjunge/hello-world
```

---

## Install Any Resource

```bash
agr add <username>/<name>                # Auto-detects resource type
agr add <username>/<name> --type skill   # Explicit type (if needed)
agr add <username>/<repo>/<name>         # From a custom repository
```

Resources install to organized namespaced paths:

```
.claude/
└── skills/
    └── kasperjunge/           # Organized by username
        └── hello-world/
```

This prevents naming conflicts and keeps your resources organized.

### Install a Bundle

Install multiple resources at once:

```bash
agr add kasperjunge/anthropic
```

---

## Dependency Tracking

**New in v0.4.0:** Track your project's resources with `agr.toml`.

### The agr.toml File

When you add resources, agr automatically tracks them in `agr.toml`:

```toml
[dependencies]
"kasperjunge/hello-world" = {}
"madsnorgaard/drupal-expert" = { type = "skill" }
"acme/tools/review" = { type = "command" }
```

This file is lightweight, human-readable, and perfect for version control.

### Sync Your Resources

Set up a new machine or share your project? One command installs everything:

```bash
agr sync
```

This reads `agr.toml` and installs any missing resources.

### Keep Things Tidy

Remove resources that aren't in your `agr.toml`:

```bash
agr sync --prune
```

### Workflow

```bash
# Add resources (automatically tracked in agr.toml)
agr add kasperjunge/hello-world
agr add madsnorgaard/drupal-expert

# Commit agr.toml to version control
git add agr.toml && git commit -m "Add agent dependencies"

# On another machine, sync everything
agr sync
```

---

## Run Without Installing (agrx)

Try a skill or command without permanent installation:

```bash
agrx kasperjunge/hello-world              # Auto-detects and runs
agrx kasperjunge/hello-world "my prompt"  # Run with a prompt
agrx kasperjunge/hello-world -i           # Interactive mode
```

The resource is downloaded, executed, and cleaned up automatically.

---

## Local Resource Authoring

**New:** Author resources in convention paths and sync them to `.claude/`.

### Set Up Authoring Structure

```bash
agr init
```

Creates the standard authoring directories:

```
./
├── skills/       # Your skills
├── commands/     # Your commands
├── agents/       # Your agents
└── packages/     # Grouped resources
```

### Create Resources

```bash
agr init skill my-skill       # Creates skills/my-skill/SKILL.md
agr init command deploy       # Creates commands/deploy.md
agr init agent reviewer       # Creates agents/reviewer.md
agr init package my-toolkit   # Creates packages/my-toolkit/
```

### Sync to .claude/

```bash
agr sync
```

Copies your resources to `.claude/{type}/{username}/` where Claude Code can use them. Your Git remote determines the username namespace.

### Benefits

- **Clean separation** — Source files in convention paths, installed files in `.claude/`
- **Automatic namespacing** — Resources are organized by your GitHub username
- **Incremental updates** — Only changed files are synced
- **Prune support** — `agr sync --prune` removes resources you've deleted

---

## Create a Shareable Repository

Create your personal agent-resources library:

```bash
agr init repo --github
```

**Done.** You now have a GitHub repo that anyone can install from.

> Requires [GitHub CLI](https://cli.github.com/). Run without `--github` to set up manually.

### What You Get

- A ready-to-use `agent-resources` repo on your GitHub
- Example skill, command, and agent to learn from
- Instant shareability:

```bash
agr add <your-username>/hello-world
```

### Add Your Own Resources

Author resources in convention paths:

```
your-username/agent-resources/
├── skills/              # Your skills (synced to .claude/)
│   └── hello-world/
│       └── SKILL.md
├── commands/            # Your commands
│   └── hello.md
├── agents/              # Your agents
│   └── hello-agent.md
└── packages/            # Grouped resources
    └── my-toolkit/
        ├── skills/
        ├── commands/
        └── agents/
```

Run `agr sync` to install them locally, then push to GitHub.

---

## Community Resources

### Go Development Toolkit — [@dsjacobsen](https://github.com/dsjacobsen/agent-resources)

A comprehensive Claude Code toolkit for Go developers.

```bash
agr add dsjacobsen/golang-pro      # Expert Go knowledge
agr add dsjacobsen/go-reviewer     # Code review agent
agr add dsjacobsen/go-check        # Quick code check
```

**Includes**: 1 skill, 9 agents, 11 commands covering scaffolding, testing, API building, refactoring, and more.

### Drupal Development Toolkit — [@madsnorgaard](https://github.com/madsnorgaard/agent-resources)

A comprehensive Claude Code toolkit for Drupal developers.

```bash
agr add madsnorgaard/drupal-expert      # Drupal 10/11 modules, themes, hooks
agr add madsnorgaard/drupal-migration   # D7-to-D10 migrations, CSV imports
agr add madsnorgaard/ddev-expert        # DDEV local development, Xdebug
agr add madsnorgaard/drupal-reviewer    # Code review agent
agr add madsnorgaard/drush-check        # Run health checks
```

**Includes**: 4 skills, 1 agent, 5 commands covering Drupal development, migrations, DDEV, Docker, security audits, and more.

---

**Built something useful?** [Open an issue](https://github.com/kasperjunge/agent-resources-project/issues) with a link to your `agent-resources` repo and we'll add it here.

---

## Legacy Commands

The following syntax is deprecated but still supported for backwards compatibility:

```bash
# Old subcommand syntax (deprecated)
agr add skill <username>/<name>
agr remove skill <name>
agrx skill <username>/<name>

# Use instead
agr add <username>/<name>
agr remove <name>
agrx <username>/<name>
```

---

<div align="center">

**MIT License** · Made for the [Claude Code](https://claude.ai/code) community

</div>
