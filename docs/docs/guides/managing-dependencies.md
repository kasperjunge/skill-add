---
title: Managing dependencies
---

# Managing dependencies

Track your project's resources with `agr.toml` and sync them across machines.

## The agr.toml file

`agr.toml` is a lightweight manifest that declares your project's resource dependencies. It's automatically created and updated when you add or remove resources.

```toml
[dependencies]
"kasperjunge/hello-world" = {}
"madsnorgaard/drupal-expert" = { type = "skill" }
"acme/tools/review" = { type = "command" }
```

### Why use agr.toml?

- **Share dependencies** — Team members can install all project resources with one command
- **Reproducible setups** — New machines get the same resources as existing ones
- **Version control friendly** — Track resource changes alongside your code
- **Clean projects** — Remove resources you no longer need with `--prune`

## Automatic tracking

When you add a resource, agr automatically records it in `agr.toml`:

```bash
agr add kasperjunge/hello-world
```

Creates or updates `agr.toml`:

```toml
[dependencies]
"kasperjunge/hello-world" = {}
```

When you remove a resource, agr removes it from `agr.toml`:

```bash
agr remove hello-world
```

## Dependency reference formats

Dependencies use the same reference format as `agr add`:

| Format | Example | Meaning |
|--------|---------|---------|
| `username/name` | `"kasperjunge/hello-world"` | From default `agent-resources` repo |
| `username/repo/name` | `"acme/tools/review"` | From custom repo |

## Specifying resource types

By default, agr auto-detects resource types. You can make the type explicit:

```toml
[dependencies]
"kasperjunge/hello-world" = { type = "skill" }
"kasperjunge/review" = { type = "command" }
"kasperjunge/expert" = { type = "agent" }
```

Valid types: `skill`, `command`, `agent`

!!! tip
    Explicit types are useful when a resource name exists in multiple types, or to document what each dependency is.

## Syncing resources

### Install missing resources

```bash
agr sync
```

This syncs both:

1. **Local authoring resources** — From `skills/`, `commands/`, `agents/`, `packages/`
2. **Remote dependencies** — From `agr.toml`

Resources that are already installed are skipped.

### Sync only remote dependencies

```bash
agr sync --remote
```

Skips local authoring resources and only installs dependencies from `agr.toml`.

### Sync globally

```bash
agr sync --global
```

Syncs resources to `~/.claude/` instead of the current project.

### Remove unlisted resources

```bash
agr sync --prune
```

In addition to installing missing resources, this removes any namespaced resources that aren't listed in `agr.toml`.

!!! note
    Pruning only affects resources in namespaced paths (e.g., `.claude/skills/username/`). Resources installed with older versions of agr in flat paths (e.g., `.claude/skills/hello-world/`) are preserved for backward compatibility.

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

agr looks for `agr.toml` starting from your current directory and searching up to the git root. This means you can run `agr sync` from any subdirectory of your project.

If no `agr.toml` exists, `agr add` creates one in your current directory.

## Global dependencies

Global installs (`--global`) don't use `agr.toml` in your project directory. Instead, they're tracked separately in your home directory and synced with:

```bash
agr sync --global
```

This keeps project-local and global resources separate.
