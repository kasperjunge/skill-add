---
title: Managing dependencies
---

# Managing dependencies

Track your project's resources with `agr.toml` and sync them across machines.

## The agr.toml file

`agr.toml` declares your project's resource dependencies. It's automatically updated when you add or remove resources.

```toml
dependencies = [
    {handle = "kasperjunge/hello-world", type = "skill"},
    {handle = "madsnorgaard/drupal-expert", type = "skill"},
    {handle = "acme/tools/review", type = "command"},
]
```

### Why use agr.toml?

- **Share dependencies** — Team members install all resources with `agr sync`
- **Reproducible setups** — New machines get the same resources
- **Version control friendly** — Track changes alongside your code
- **Clean projects** — Remove unused resources with `--prune`

## Automatic tracking

When you add a resource, agr automatically records it in `agr.toml`:

```bash
agr add kasperjunge/hello-world
```

Creates or updates `agr.toml`:

```toml
dependencies = [
    {handle = "kasperjunge/hello-world", type = "skill"},
]
```

When you remove a resource, agr removes it from `agr.toml`:

```bash
agr remove hello-world
```

## Dependency reference formats

Dependencies use the same reference format as `agr add`:

| Format | Example | Meaning |
|--------|---------|---------|
| `username/name` | `kasperjunge/hello-world` | From default `agent-resources` repo |
| `username/repo/name` | `acme/tools/review` | From custom repo |

## Specifying resource types

Resource types are specified in the dependency entry:

```toml
dependencies = [
    {handle = "kasperjunge/hello-world", type = "skill"},
    {handle = "kasperjunge/review", type = "command"},
    {handle = "kasperjunge/expert", type = "agent"},
    {handle = "kasperjunge/no-console", type = "rule"},
]
```

Valid types: `skill`, `command`, `agent`, `rule`, `package`

!!! tip
    Explicit types are useful when a resource name exists in multiple types, or to document what each dependency is.

## Syncing resources

### Install missing resources

```bash
agr sync
```

This syncs both:

1. **Local resources** — From `resources/skills/`, `resources/commands/`, `resources/agents/`
2. **Remote dependencies** — From `agr.toml`

Already-installed resources are skipped.

### Sync only remote dependencies

```bash
agr sync --remote
```

Skips local resources and only installs dependencies from `agr.toml`.

### Sync globally

```bash
agr sync --global
```

Syncs resources to `~/.claude/` instead of the current project.

### Remove unlisted resources

```bash
agr sync --prune
```

Installs missing resources and removes any namespaced resources not in `agr.toml`.

!!! note
    Pruning only affects resources in namespaced paths (e.g., `.claude/skills/username:skill/`). Resources installed with older versions of agr in flat paths (e.g., `.claude/skills/hello-world/`) are preserved for backward compatibility.

## Typical workflow

### Setting up a new project

```bash
# Add the resources you need
agr add kasperjunge/hello-world
agr add madsnorgaard/drupal-expert

# Commit agr.toml to version control
git add agr.toml
git commit -m "Add agent resource dependencies"
```

### Onboarding a team member

```bash
# Clone the project
git clone https://github.com/yourteam/project.git
cd project

# Install all declared resources
agr sync
```

### Keeping things tidy

```bash
# Remove a resource you no longer need
agr remove hello-world

# Or clean up everything not in agr.toml
agr sync --prune
```

### Updating resources

To update a resource to the latest version from GitHub:

```bash
agr add kasperjunge/hello-world --overwrite
```

## Where agr.toml lives

agr searches for `agr.toml` from your current directory up to the git root, so you can run `agr sync` from any subdirectory.

If no `agr.toml` exists, `agr add` creates one in your current directory.

## Global dependencies

Global installs (`--global`) are tracked separately in your home directory:

```bash
agr sync --global
```

Project-local and global resources remain separate.

## Multi-tool support

agr can sync resources to multiple AI coding tools (Claude Code, Cursor). Configure target tools in `agr.toml`:

```toml
[tools]
targets = ["claude", "cursor"]
```

### Resolution priority

Target tools are determined by:

1. **CLI `--tool` flags** — Highest priority
2. **Config `[tools].targets`** — From `agr.toml`
3. **Auto-detect** — Based on config directories present
4. **Default** — Claude Code only

### Examples

```bash
# Sync to configured tools (from agr.toml [tools] section)
agr sync

# Override config: sync only to Claude
agr sync --tool claude

# Sync to both Claude and Cursor explicitly
agr sync --tool claude --tool cursor

# Add a resource to specific tools
agr add kasperjunge/commit --tool claude --tool cursor
```

### Multi-tool workflow

A typical multi-tool workflow:

```toml
# agr.toml
dependencies = [
    {handle = "kasperjunge/commit", type = "skill"},
    {handle = "dsjacobsen/golang-pro", type = "skill"},
]

[tools]
targets = ["claude", "cursor"]
```

```bash
# Sync all dependencies to both tools
agr sync

# Check installation status per tool
agr list --tool claude --tool cursor
```
