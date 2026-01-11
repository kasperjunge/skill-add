# Agent Resources

A package manager for AI coding tools.

**Agent resources** are the files that make AI coding assistants smarter—skills, commands, subagents, and packages. This CLI lets you install them from GitHub or a central registry, and share your own.

```bash
pip install agr
agr install username/code-reviewer
```

Works with Claude Code, Cursor, Codex, GitHub Copilot, and OpenCode.

---

## Get Started

**1. Install the CLI**

```bash
pip install agr
```

**2. Install a resource from GitHub**

```bash
# Install from someone's agent-resources repo
agr install username/code-reviewer

# Or from any GitHub repo
agr install username/repo-name/code-reviewer
```

The CLI auto-detects your tools and installs to the right locations.

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
| **Packages** | Bundles of skills, commands, and agents |

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
agr install yourusername/my-skill
```

**Why name it `agent-resources`?** If your repo is named `agent-resources`, users can install with just `username/resource-name`. Otherwise they need the full path `username/repo-name/resource-name`.

See [Create Your Own Repo](create-your-own-repo.md) for details.

---

## Where Resources Come From

| Source | Example |
|--------|---------|
| **GitHub** (default) | `agr install username/skill-name` |
| **Central registry** | `agr install skill-name` |

Most resources live on GitHub. The central registry indexes popular resources for easier discovery.

---

## Common Commands

```bash
# Install from GitHub
agr install username/packagename

# Install to a specific tool
agr install username/packagename --tool=cursor

# Install globally (all projects)
agr install username/packagename --global

# Install a specific resource type
agr install skill username/my-skill
agr install command username/my-command
agr install agent username/my-agent
```

---

## Next Steps

- [Resource Types](what-is-agent-resources.md) — Learn about skills, commands, subagents, and packages
- [Supported Tools](supported-platforms.md) — See which AI tools are supported
- [Create Your Own Repo](create-your-own-repo.md) — Share your own resources
