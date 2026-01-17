---
title: Repository structure
---

# Repository structure

agr supports two directory structures: **authoring paths** for local development and **`.claude/` paths** for published/installed resources.

## Authoring paths (recommended)

When authoring resources, use convention paths at the repository root:

```
./
├── skills/
│   └── <skill-name>/
│       └── SKILL.md
├── commands/
│   └── <command-name>.md
├── agents/
│   └── <agent-name>.md
└── packages/
    └── <package-name>/
        ├── skills/
        ├── commands/
        └── agents/
```

Run `agr sync` to copy these to `.claude/` where Claude Code can use them.

### Benefits

- **Clean separation** — Source files stay organized outside `.claude/`
- **Automatic namespacing** — Resources install to `.claude/{type}/{username}/`
- **Incremental sync** — Only changed files are copied
- **Package support** — Group related resources together

### Discovery rules

agr discovers resources in these locations:

| Path | Resource type |
|------|---------------|
| `skills/<name>/SKILL.md` | Skill |
| `commands/<name>.md` | Command |
| `agents/<name>.md` | Agent |
| `packages/<pkg>/skills/<name>/SKILL.md` | Packaged skill |
| `packages/<pkg>/commands/<name>.md` | Packaged command |
| `packages/<pkg>/agents/<name>.md` | Packaged agent |

## .claude/ paths (installed/legacy)

Resources are installed to `.claude/` with username namespacing:

```
./
└── .claude/
    ├── skills/
    │   └── <username>/
    │       └── <skill-name>/
    │           └── SKILL.md
    ├── commands/
    │   └── <username>/
    │       └── <command-name>.md
    └── agents/
        └── <username>/
            └── <agent-name>.md
```

This is where:

- `agr add` installs remote resources
- `agr sync` copies local authoring resources
- Claude Code reads resources from

## Publishing resources

When others install your resources with `agr add`, agr looks for them in this order:

1. **agr.toml definitions** — `[resource.*]` and `[package.*]` sections
2. **`.claude/` directory** — Standard installed paths

### Using agr.toml for custom paths

Define custom resource locations in `agr.toml`:

```toml
[resource.my-skill]
path = "skills/my-skill"
type = "skill"

[resource.my-command]
path = "commands/my-command.md"
type = "command"

[package.my-toolkit]
path = "packages/my-toolkit"
```

This allows consumers to install resources even if you use non-standard paths.

### Using .claude/ for publishing

Alternatively, sync your resources to `.claude/` before publishing:

```bash
agr sync
git add .claude/
git commit -m "Sync resources for publishing"
git push
```

Others can then install directly from the `.claude/` paths.

## Branch requirement

Resources are fetched from the `main` branch. Repositories that only have `master`
won't work until you create a `main` branch or change the default branch to `main`.

## Naming convention

If your repository is named `agent-resources`, users can install with the short form:

```
username/resource-name
```

If the repository name is different, users must include it:

```
username/repo-name/resource-name
```
