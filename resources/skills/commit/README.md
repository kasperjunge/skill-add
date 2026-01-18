# /commit

**Perfect semantic commit messages, every time.**

Generate conventional commit messages that tell the story of your changes. No more "fix stuff" or "update code".

## Install

```bash
uvx add-skill kasperjunge/commit
```

## Usage

Stage your changes, then ask Claude to commit:

```
> /commit
```

Or just describe what you want:

```
> commit these changes
> write a commit message for this
> help me commit
```

## What You Get

**Before:**
```
fixed the thing
```

**After:**
```
fix(auth): handle null response from OAuth provider

The Google OAuth API returns null for revoked tokens.
Add defensive check to prevent TypeError on login page.
```

## Features

- **Semantic types**: feat, fix, docs, refactor, perf, test, build, ci, chore
- **Smart scope detection**: Infers scope from file paths (`src/auth/*` → `auth`)
- **Breaking change detection**: Marks breaking changes with `!` and explains impact
- **Body for context**: Adds explanation when the "why" isn't obvious
- **Conventional commits**: Follows the [Conventional Commits](https://www.conventionalcommits.org/) standard

## Examples

| Change | Commit Message |
|--------|----------------|
| New login feature | `feat(auth): add password reset flow` |
| Bug fix | `fix(api): handle empty response from payment provider` |
| Refactoring | `refactor: consolidate database connection logic` |
| Breaking change | `feat(api)!: migrate from REST to GraphQL` |

---

Part of [agent-resources](https://github.com/kasperjunge/agent-resources) — the package manager for Claude Code.
