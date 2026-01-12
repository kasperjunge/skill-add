<div align="center">

# 🧩 agent-resources

**Share and install Claude Code skills, commands, and agents with a single command.**

*Like uv, but for Claude Code resources.*

[![PyPI](https://img.shields.io/pypi/v/agr?color=blue)](https://pypi.org/project/agr/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Try It](#try-it-now) • [Install](#install-any-resource) • [Create Your Own](#create-your-own) • [Community](#community-resources)

</div>

---

## Try It Now

No installation needed. Just run:

```bash
uvx agr add skill kasperjunge/hello-world
```

**That's it.** The skill is now available in Claude Code.

Or install permanently:

```bash
pip install agr
agr add skill kasperjunge/hello-world
```

---

## Install Any Resource

```bash
agr add skill <username>/<skill-name>       # Skills
agr add command <username>/<command-name>   # Slash commands
agr add agent <username>/<agent-name>       # Sub-agents
```

### Default Repository Convention

If you name your repo `agent-resources`, users only need to specify your username and resource name:

```bash
# Installs from github.com/kasperjunge/agent-resources
agr add skill kasperjunge/hello-world
```

### Install From Any Repository

You can install from any GitHub repository that has the `.claude/` structure. Just use the three-part format:

```bash
# Installs from github.com/username/custom-repo
agr add skill username/custom-repo/my-skill
```

---

## Create Your Own Library

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
agr add skill <your-username>/hello-world
```

### Add Your Own Resources

Edit the files in your repo:

```
your-username/agent-resources/
└── .claude/
    ├── skills/          # Skill folders with SKILL.md
    ├── commands/        # Slash command .md files
    └── agents/          # Sub-agent .md files
```

Push to GitHub.

---

## Community Resources

### Go Development Toolkit — [@dsjacobsen](https://github.com/dsjacobsen/agent-resources)

A comprehensive Claude Code toolkit for Go developers.

```bash
agr add skill dsjacobsen/golang-pro      # Expert Go knowledge
agr add agent dsjacobsen/go-reviewer     # Code review agent
agr add command dsjacobsen/go-check      # Quick code check
```

**Includes**: 1 skill, 9 agents, 11 commands covering scaffolding, testing, API building, refactoring, and more.

### Drupal Development Toolkit — [@madsnorgaard](https://github.com/madsnorgaard/agent-resources)

A comprehensive Claude Code toolkit for Drupal developers.

```bash
agr add skill madsnorgaard/drupal-expert      # Drupal 10/11 modules, themes, hooks
agr add skill madsnorgaard/drupal-migration   # D7-to-D10 migrations, CSV imports
agr add skill madsnorgaard/ddev-expert        # DDEV local development, Xdebug
agr add agent madsnorgaard/drupal-reviewer    # Code review agent
agr add command madsnorgaard/drush-check      # Run health checks
```

**Includes**: 4 skills, 1 agent, 5 commands covering Drupal development, migrations, DDEV, Docker, security audits, and more.

---

**Built something useful?** [Open an issue](https://github.com/kasperjunge/agent-resources-project/issues) with a link to your `agent-resources` repo and we'll add it here.

---

## Legacy Commands

The following commands are deprecated but still supported for backwards compatibility:

```bash
uvx add-skill <username>/<skill-name>
uvx add-command <username>/<command-name>
uvx add-agent <username>/<agent-name>
uvx create-agent-resources-repo
```

Use `agr add` and `agr init` instead.

---

<div align="center">

**MIT License** · Made for the [Claude Code](https://claude.ai/code) community

</div>
