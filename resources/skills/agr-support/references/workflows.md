# Common Workflows

## Installing Resources

### From the default repo name
If a user has a repo named `agent-resources`:
```bash
agr add username/my-resource
```

### From a custom repo name
```bash
agr add username/custom-repo/my-resource
```

### Install globally
Available in all projects:
```bash
agr add username/my-resource --global
```

### Install nested resources
Use `:` for nested paths:
```bash
agr add username/backend:hello-world
```

### Overwrite existing
```bash
agr add username/my-resource --overwrite
```

### Disambiguate types
When name exists in multiple types:
```bash
agr add username/hello --type skill
agr add username/hello --type command
```

---

## Managing Dependencies

### How agr.toml works
Resources are tracked automatically in `agr.toml`:
```toml
[dependencies]
"kasperjunge/hello-world" = {}
"acme/tools/review" = { type = "command" }
```

### Team workflow

**Project setup**:
```bash
agr add kasperjunge/hello-world
agr add madsnorgaard/drupal-expert
git add agr.toml
git commit -m "Add agent resource dependencies"
```

**Team member onboarding**:
```bash
git clone https://github.com/yourteam/project.git
cd project
agr sync
```

### Keep things tidy
```bash
agr remove hello-world         # Remove from project
agr sync --prune               # Remove unlisted resources
```

### Update to latest version
```bash
agr add kasperjunge/hello-world --overwrite
```

---

## Local Authoring

### Set up authoring structure
```bash
agr init
```
Creates:
```
skills/
commands/
agents/
packages/
```

### Create resources
```bash
agr init skill my-skill        # skills/my-skill/SKILL.md
agr init command my-cmd        # commands/my-cmd.md
agr init agent my-agent        # agents/my-agent.md
agr init package my-toolkit    # packages/my-toolkit/
```

### Edit and sync
```bash
$EDITOR skills/my-skill/SKILL.md
agr sync
```

### Remove a resource
```bash
rm -rf skills/old-skill/
agr sync --prune
```

### Convention paths

| Path | Resource type |
|------|---------------|
| `skills/<name>/SKILL.md` | Skill |
| `commands/<name>.md` | Command |
| `agents/<name>.md` | Agent |
| `packages/<pkg>/skills/<name>/SKILL.md` | Packaged skill |
| `packages/<pkg>/commands/<name>.md` | Packaged command |
| `packages/<pkg>/agents/<name>.md` | Packaged agent |

### Username namespacing
Resources install to `.claude/{type}/{username}/{name}`.

Username is extracted from git remote:
```bash
# If remote is git@github.com:kasperjunge/agent-resources.git
# Resources install to .claude/skills/kasperjunge/my-skill/
```

If no git remote exists, uses `local` as namespace.

---

## Creating a Shareable Repository

### Quick start
```bash
agr init repo
```
Creates `./agent-resources/` with starter structure.

### Specify location
```bash
agr init repo my-resources     # Creates ./my-resources/
agr init repo .                # Initialize current directory
```

### Create and push to GitHub
```bash
agr init repo agent-resources --github
```
Requires `gh auth login` configured.

### Recommended repo name
If named `agent-resources`, users install with shorter syntax:
```bash
agr add username/my-skill
```

If different name, must include it:
```bash
agr add username/custom-repo/my-skill
```

---

## Using Packages and Bundles

### Install a bundle
```bash
agr add kasperjunge/anthropic              # Auto-detect
agr add kasperjunge/anthropic --type bundle  # Explicit
```

### Update a bundle
```bash
agr update bundle kasperjunge/anthropic
```

### Remove a bundle
```bash
agr remove anthropic --type bundle
```

### Create a package
```bash
agr init package my-toolkit
```
Creates:
```
packages/my-toolkit/
├── skills/
├── commands/
└── agents/
```

Add resources to the package:
```bash
agr init skill helper --path packages/my-toolkit/skills/helper
agr init command build --path packages/my-toolkit/commands
```

---

## Using agrx for Temporary Execution

### Try before installing
```bash
agrx kasperjunge/hello-world
```
Resource is downloaded, executed, then cleaned up.

### Run with a prompt
```bash
agrx kasperjunge/hello-world "analyze this code"
```

### Interactive session
```bash
agrx kasperjunge/hello-world -i
```
