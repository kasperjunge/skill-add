---
title: Creating Skills
---

# Creating Skills

Skills are folders of instructions that give AI agents new capabilities.

## Quick Start

```bash
agr init my-skill
```

Creates `my-skill/SKILL.md` in your current directory:

```
my-skill/
└── SKILL.md
```

## SKILL.md Format

A skill requires YAML frontmatter with `name` and `description`:

```markdown
---
name: my-skill
description: Brief description of what this skill does and when to use it.
---

# My Skill

Instructions for the agent go here.
```

### Required Fields

| Field | Constraints |
|-------|-------------|
| `name` | Max 64 chars. Lowercase letters, numbers, hyphens. Must match directory name. |
| `description` | Max 1024 chars. Describes what the skill does and when to use it. |

### Optional Fields

| Field | Purpose |
|-------|---------|
| `license` | License name or reference to bundled file |
| `compatibility` | Environment requirements (tools, packages, network) |
| `metadata` | Key-value pairs (author, version, etc.) |

## Example: Complete Skill

```markdown
---
name: code-reviewer
description: Reviews code for bugs, security issues, and best practices. Use when reviewing pull requests or code changes.
license: MIT
metadata:
  author: your-username
  version: "1.0"
---

# Code Reviewer

You are a code review expert. When reviewing code:

1. Check for bugs and logic errors
2. Identify security vulnerabilities
3. Suggest performance improvements
4. Ensure code follows project conventions

Be specific and actionable in your feedback. Reference line numbers when possible.
```

## Skills with Supporting Files

For complex skills, add supporting files:

```
my-skill/
├── SKILL.md
├── references/       # Additional documentation
│   └── style-guide.md
├── scripts/          # Executable code
│   └── validate.py
└── assets/           # Templates, data files
    └── template.json
```

Reference them in your SKILL.md:

```markdown
See [style guide](references/style-guide.md) for formatting rules.

Run the validation script:
scripts/validate.py
```

Keep your main SKILL.md under 500 lines. Put detailed reference material in the `references/` folder.

## Test Your Skill

Add your local skill and test it:

```bash
agr add ./my-skill
```

Your skill is now available in Claude Code. Test it by starting Claude and invoking the skill.

## Share with Others

Push to GitHub. Others install with:

```bash
agr add your-username/my-skill
```

Or from a specific repo:

```bash
agr add your-username/my-repo/my-skill
```

## Tips

- Write clear, specific descriptions—agents use them to decide when to activate your skill
- Keep instructions focused on one task
- Use examples to show expected inputs and outputs
- Test thoroughly before sharing

## Learn More

- [Agent Skills Specification](https://agentskills.io/specification) — Full format details
- [Example Skills](https://github.com/anthropics/skills) — Reference implementations
