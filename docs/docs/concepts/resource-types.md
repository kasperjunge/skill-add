---
title: Resource types
---

# Resource types

agr manages four resource types for Claude Code.

| Type | File | Path format | Purpose |
|------|------|-------------|---------|
| Skill | `SKILL.md` | `username:name/` | Define behavior and instructions |
| Command | `name.md` | `username/name.md` | Slash commands |
| Agent | `name.md` | `username/name.md` | Sub-agents for delegation |
| Rule | `name.md` | `username/name.md` | Constraints and guidelines |

## Skills

A skill is a directory with a `SKILL.md` file that defines behavior and instructions.

```
./
└── .claude/
    └── skills/
        └── username:code-reviewer/
            └── SKILL.md
```

Skills use a flattened colon format (`username:skill-name`) because Claude Code only discovers top-level directories.

## Commands

A command is a markdown file that defines what happens when a user runs a slash command.

```
./
└── .claude/
    └── commands/
        └── username/
            └── review.md
```

## Agents

An agent is a markdown file that defines a sub-agent that your main agent can delegate to.

```
./
└── .claude/
    └── agents/
        └── username/
            └── test-writer.md
```

## Rules

A rule is a markdown file that defines constraints or guidelines for Claude to follow.

```
./
└── .claude/
    └── rules/
        └── username/
            └── no-console.md
```

Rules define project-specific constraints like coding standards, security requirements, or behavioral guidelines.
