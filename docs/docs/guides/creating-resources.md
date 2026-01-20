---
title: Creating resources
---

# Creating resources

Use `agr init` to scaffold new skills, commands, agents, and packages.

## Set up authoring structure

Before creating resources, initialize the convention directories:

```bash
agr init
```

Creates:

```
./
├── agr.toml
└── resources/
    ├── skills/
    ├── commands/
    ├── agents/
    └── packages/
```

## Create a skill

```bash
agr init skill code-reviewer
```

Creates:

```
./
└── resources/
    └── skills/
        └── code-reviewer/
            └── SKILL.md
```

## Create a command

```bash
agr init command review
```

Creates:

```
./
└── resources/
    └── commands/
        └── review.md
```

## Create an agent

```bash
agr init agent test-writer
```

Creates:

```
./
└── resources/
    └── agents/
        └── test-writer.md
```

## Create a package

Packages group related resources under a single namespace:

```bash
agr init package my-toolkit
```

Creates:

```
./
└── resources/
    └── packages/
        └── my-toolkit/
            ├── skills/
            ├── commands/
            └── agents/
```

Add resources to the package using `--path`:

```bash
agr init skill helper --path resources/packages/my-toolkit/skills/helper
agr init command build --path resources/packages/my-toolkit/commands
```

## Sync to .claude/

After creating or editing resources, sync them to `.claude/`:

```bash
agr sync
```

Skills are installed with flattened colon names (e.g., `.claude/skills/username:code-reviewer/`) for Claude Code discoverability. Commands and agents use nested paths (e.g., `.claude/commands/username/review.md`).

## Use a custom path

Each subcommand supports `--path` if you want to place files elsewhere:

```bash
agr init skill code-reviewer --path ./custom/skills/code-reviewer
agr init command review --path ./custom/commands
```

## Legacy mode

To create resources directly in `.claude/` (old behavior):

```bash
agr init skill code-reviewer --legacy
agr init command review --legacy
agr init agent test-writer --legacy
```

Creates:

```
./
└── .claude/
    ├── skills/
    │   └── code-reviewer/
    │       └── SKILL.md
    ├── commands/
    │   └── review.md
    └── agents/
        └── test-writer.md
```

!!! note
    Legacy resources aren't managed by `agr sync`. Use convention paths for the best workflow.

## PACKAGE.md marker files

For repositories with multiple resources, you can use a `PACKAGE.md` marker file to explicitly define the package namespace. This is useful when:

- Your repository structure doesn't follow conventions
- You want a custom package name
- You have resources in non-standard locations

### PACKAGE.md format

Create a `PACKAGE.md` file with YAML frontmatter:

```markdown
---
name: my-toolkit
---

# My Toolkit

Description of your package.
```

The `name` field determines the namespace used when installing resources from this package.

### Example structure

```
./
├── PACKAGE.md          # Contains: name: my-toolkit
├── skills/
│   └── helper/
│       └── SKILL.md
└── commands/
    └── build.md
```

When installed via `agr add`, resources will be namespaced under `my-toolkit`:

```
.claude/
├── skills/
│   └── username:my-toolkit:helper/
│       └── SKILL.md
└── commands/
    └── username/
        └── my-toolkit/
            └── build.md
```

### Validation rules

- The `name` field is required
- Names must be alphanumeric with hyphens or underscores
- Names must start and end with an alphanumeric character
- Nested PACKAGE.md files are not allowed (packages cannot contain other packages)

## Next steps

Edit the generated markdown to match your workflow, then:

1. Run `agr sync` to install to `.claude/`
2. Test with Claude Code
3. Push to GitHub to share with others
