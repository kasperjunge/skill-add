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
└── packages/
    └── my-toolkit/
        ├── skills/
        ├── commands/
        └── agents/
```

Add resources to the package using `--path`:

```bash
agr init skill helper --path packages/my-toolkit/skills/helper
agr init command build --path packages/my-toolkit/commands
```

## Sync to .claude/

After creating or editing resources, sync them to `.claude/`:

```bash
agr sync
```

Resources are installed to `.claude/{type}/{username}/{name}` where Claude Code can use them.

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

## Next steps

Edit the generated markdown to match your workflow, then:

1. Run `agr sync` to install to `.claude/`
2. Test with Claude Code
3. Push to GitHub to share with others
