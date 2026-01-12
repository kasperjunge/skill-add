# Resource Types

Agent Resources supports four types of resources for Claude Code.

---

## Skills

Skills extend your agent with new capabilities. They're directories containing a `SKILL.md` file that defines behavior, context, and instructions.

```
.claude/skills/code-reviewer/
└── SKILL.md
```

---

## Commands

Commands give your agent new slash commands to execute. They're markdown files that define what happens when you run `/command-name`.

```
.claude/commands/
└── review.md
```

---

## Subagents

Subagents are specialized agents that your main agent can delegate tasks to. They're markdown files that define the agent's role and capabilities.

```
.claude/agents/
└── reviewer-agent.md
```

---

## Packages

Packages bundle skills, commands, and subagents together. A single package can contain any combination of resource types, plus dependencies on other packages.

```
.claude/packages/code-reviewer/
└── PACKAGE.md
```
