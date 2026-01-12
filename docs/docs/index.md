---
title: Get Started - Agent Resources
description: Install and share skills, commands, and sub-agents for Claude Code.
---

# Get Started

A package manager for Claude Code skills, commands, and agents.

**Agent resources** are the files that make AI coding assistants smarter—skills, commands, and subagents. This CLI lets you install them from GitHub and share your own.

```bash
pip install agr
agr add skill username/code-reviewer
```

---

## Get Started

**1. Install the CLI**

```bash
pip install agr
```

**2. Install a resource from GitHub**

```bash
# Install from someone's agent-resources repo
agr add skill username/code-reviewer

# Or from any GitHub repo
agr add skill username/repo-name/code-reviewer
```

**3. Use it**

Your agent now has the new skill, command, or subagent available.

---

## What Are Agent Resources?

Agent resources are files that extend what your AI coding assistant can do.

| Type | What it does |
|------|--------------|
| **Skills** | Add capabilities your agent uses automatically |
| **Commands** | Add slash commands like `/review` or `/deploy` |
| **Subagents** | Add specialized agents to delegate tasks to |

---

## Share Your Own

Create a GitHub repo to share your agent resources with others.

**Quick setup:**

```bash
# Scaffold a new repo with examples
agr init repo agent-resources

# Push to GitHub
cd agent-resources
git init && git add . && git commit -m "init"
gh repo create agent-resources --public --push
```

**Now anyone can install your resources:**

```bash
agr add yourusername/my-skill
```

**Why name it `agent-resources`?** If your repo is named `agent-resources`, users can install with just `username/resource-name`. Otherwise they need the full path `username/repo-name/resource-name`.

See [Create Your Own Repo](create-your-own-repo.md) for details.

---

## Where Resources Come From

Resources are hosted on GitHub. If your repo is named `agent-resources`, users install with:

```bash
agr add skill username/skill-name
```

From any other repo, use the three-part format:

```bash
agr add skill username/repo-name/skill-name
```

---

## Common Commands

```bash
# Install resources
agr add skill username/my-skill
agr add command username/my-command
agr add agent username/my-agent

# Install globally (all projects)
agr add skill username/my-skill --global

# Overwrite existing
agr add skill username/my-skill --overwrite

# Create new resources
agr init repo my-agent-resources
agr init skill my-skill
agr init command my-command
agr init agent my-agent
```

---

## Next Steps

- [Resource Types](what-is-agent-resources.md) — Learn about skills, commands, subagents, and packages
- [Create Your Own Repo](create-your-own-repo.md) — Share your own resources
