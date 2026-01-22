---
title: Home
---

# AGR — Skills for AI Agents

A package and project manager for AI agent skills. Install, share, and manage skills from GitHub.

## Install

```bash
pip install agr
```

## Add a Skill

```bash
agr add anthropics/skills/frontend-design
```

Done. The skill is available in Claude Code.

## Run a Skill Directly

Run skills from your terminal without installing:

```bash
agrx anthropics/skills/pdf                  # Run once, then clean up
agrx anthropics/skills/pdf -p "Extract tables from report.pdf"
agrx anthropics/skills/pdf -i               # Interactive: run skill, then continue chatting
```

The `-i` flag runs the skill first, then starts an interactive session so you can continue the conversation.

## Share with Your Team

Dependencies are tracked in `agr.toml`:

```toml
dependencies = [
    {handle = "anthropics/skills/frontend-design"},
    {handle = "anthropics/skills/skill-creator"},
]
```

Teammates install everything with:

```bash
agr sync
```

## Commands

| Command | What it does |
|---------|-------------|
| `agr add <handle>` | Install a skill |
| `agr remove <handle>` | Uninstall a skill |
| `agr sync` | Install all dependencies from `agr.toml` |
| `agr list` | Show skills and installation status |
| `agr init` | Create `agr.toml` |
| `agr init <name>` | Create a skill scaffold |
| `agrx <handle>` | Run a skill temporarily |

## Handle Format

```bash
agr add user/skill              # From user's "agent-resources" repo
agr add user/repo/skill         # From a different repo
```

If a user's repo is named `agent-resources`, you can skip the repo name:

```bash
agr add kasperjunge/commit                    # From kasperjunge/agent-resources
agr add kasperjunge/agent-resources/commit    # Same thing (explicit)
```

## Skill Discovery

When you run `agr add user/repo/skill`, agr automatically searches the repo for a skill named `skill`. It doesn't matter where the skill is located—it will be found if it exists anywhere in:

- `resources/skills/{skill}/SKILL.md`
- `skills/{skill}/SKILL.md`
- `{skill}/SKILL.md`

If two skills have the same name, you'll get an error.

## Example Skills

```bash
agr add anthropics/skills/frontend-design    # Build production-grade UIs
agr add anthropics/skills/skill-creator      # Create new skills
agr add anthropics/skills/pdf                # Work with PDF documents
```

Browse more at [github.com/anthropics/skills](https://github.com/anthropics/skills).

## Next Steps

- [Create your own skill](creating.md)
- [CLI reference](reference.md)
