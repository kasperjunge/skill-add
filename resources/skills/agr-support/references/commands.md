# CLI Command Reference

## agr add

Add resources from GitHub or local paths.

**Syntax**:
```bash
agr add <username>/<name>              # From default repo
agr add <username>/<repo>/<name>       # From custom repo
agr add ./path/to/resource             # Local path
```

**Options**:
| Flag | Description |
|------|-------------|
| `--type`, `-t` | Resource type: `skill`, `command`, `agent`, `bundle` |
| `--global`, `-g` | Install to `~/.claude/` |
| `--overwrite` | Replace existing resource |
| `--to` | Add local resource to a package namespace |

**Examples**:
```bash
agr add kasperjunge/hello-world                    # Auto-detect type
agr add acme/tools/review --global                 # Custom repo, global
agr add kasperjunge/hello --type skill             # Explicit type
agr add username/backend:hello-world               # Nested path
agr add ./scripts/deploy.md --type command --to my-toolkit  # Local to package
```

---

## agr remove

Remove resources with auto-detection.

**Syntax**:
```bash
agr remove <name>
agr remove <username>/<name>
```

**Options**:
| Flag | Description |
|------|-------------|
| `--type`, `-t` | Resource type: `skill`, `command`, `agent`, `bundle` |
| `--global`, `-g` | Remove from `~/.claude/` |

**Examples**:
```bash
agr remove hello-world                # Auto-detect type
agr remove kasperjunge/hello-world    # Full reference
agr remove hello --type skill         # Explicit type
agr remove hello-world --global       # From global
```

---

## agr sync

Synchronize local authoring resources and remote dependencies.

**Syntax**:
```bash
agr sync
agr sync --prune
agr sync --local
agr sync --remote
```

**Options**:
| Flag | Description |
|------|-------------|
| `--global`, `-g` | Sync `~/.claude/` instead of current directory |
| `--prune` | Remove resources not in source or `agr.toml` |
| `--local` | Only sync local authoring resources |
| `--remote` | Only sync remote dependencies from `agr.toml` |

**What gets synced**:
- **Local**: Resources from `skills/`, `commands/`, `agents/`, `packages/`
- **Remote**: Dependencies listed in `agr.toml`

**Output format**:
```
Installed local resource 'my-skill'
Updated local resource 'my-command'
Installed kasperjunge/hello-world (skill)
Sync complete: 2 installed, 1 updated, 0 pruned
```

---

## agr update

Re-fetch resources from GitHub.

**Syntax**:
```bash
agr update <type> <reference>
```

**Examples**:
```bash
agr update skill kasperjunge/hello-world
agr update command kasperjunge/my-repo/hello --global
agr update bundle kasperjunge/anthropic
```

---

## agrx

Run resources temporarily without permanent installation.

**Syntax**:
```bash
agrx <username>/<name>
agrx <username>/<name> "<prompt>"
agrx <username>/<repo>/<name>
```

**Options**:
| Flag | Description |
|------|-------------|
| `--type`, `-t` | Resource type: `skill` or `command` |
| `--interactive`, `-i` | Start interactive Claude session |
| `--global`, `-g` | Install temporarily to `~/.claude/` |

**Examples**:
```bash
agrx kasperjunge/hello-world                      # Auto-detect and run
agrx kasperjunge/hello-world "analyze this code"  # With prompt
agrx kasperjunge/hello-world -i                   # Interactive mode
agrx kasperjunge/hello --type skill               # Explicit type
```

---

## agr init

Create scaffolds for repositories and resources.

### Initialize authoring structure
```bash
agr init
```
Creates: `skills/`, `commands/`, `agents/`, `packages/`

### Create a repository
```bash
agr init repo                    # Creates ./agent-resources/
agr init repo my-resources       # Creates ./my-resources/
agr init repo .                  # Initialize current directory
agr init repo agent-resources --github  # Create and push to GitHub
```

### Create resources
```bash
agr init skill my-skill          # Creates skills/my-skill/SKILL.md
agr init command my-command      # Creates commands/my-command.md
agr init agent my-agent          # Creates agents/my-agent.md
agr init package my-toolkit      # Creates packages/my-toolkit/
```

**Options**:
| Flag | Description |
|------|-------------|
| `--path`, `-p` | Custom output path |
| `--github`, `-g` | Create GitHub repo and push (repo only) |
| `--legacy` | Create in `.claude/` instead of authoring paths |

---

## Deprecated Syntax

Old subcommand syntax still works but shows warnings:

```bash
# Deprecated
agr add skill <username>/<name>
agr remove skill <name>
agrx skill <username>/<name>

# Use instead
agr add <username>/<name>
agr remove <name>
agrx <username>/<name>
```
