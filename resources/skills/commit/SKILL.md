---
name: commit
description: Generate perfect semantic commit messages from staged changes. Use when the user says "commit", "/commit", asks for a commit message, wants to commit changes, or needs help writing a commit. Analyzes git diff to produce conventional commit format messages with appropriate type, scope, and description.
---

# Commit Message Generator

Generate semantic commit messages that tell the story of your changes.

## Workflow

1. Analyze staged changes (git diff --cached)
2. Identify change type and scope
3. Generate commit message following conventional commits
4. Present for approval and commit

## Step 1: Gather Context

```bash
# Get staged changes
git diff --cached

# Get file list for scope detection
git diff --cached --name-only

# Check for related recent commits (style reference)
git log -5 --oneline
```

If nothing is staged, inform the user and suggest staging with `git add`.

## Step 2: Analyze Changes

Determine:
- **Type**: What category of change is this?
- **Scope**: What module/component is affected?
- **Breaking**: Does this break existing functionality?

### Commit Types

| Type | When to Use |
|------|-------------|
| `feat` | New feature for users |
| `fix` | Bug fix for users |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code change, no feature/fix |
| `perf` | Performance improvement |
| `test` | Adding/fixing tests |
| `build` | Build system, dependencies |
| `ci` | CI configuration |
| `chore` | Maintenance tasks |

### Scope Detection

Infer scope from file paths:
- `src/auth/*` → `auth`
- `components/Button/*` → `button`
- `api/users.ts` → `users`
- Multiple areas → omit scope or use parent

## Step 3: Generate Message

Format: `type(scope): description`

Rules:
- Imperative mood: "add" not "added" or "adds"
- Lowercase first letter
- No period at end
- Max 72 characters for subject
- Body for complex changes (what + why)

### Examples

**Simple feature:**
```
feat(auth): add password reset flow
```

**Bug fix with context:**
```
fix(api): handle null response from payment provider

The Stripe API returns null for cancelled subscriptions.
Add defensive check to prevent TypeError in billing page.
```

**Breaking change:**
```
feat(api)!: change authentication to OAuth 2.0

BREAKING CHANGE: Remove support for API key authentication.
All clients must migrate to OAuth tokens by v3.0.
```

**Multi-file refactor:**
```
refactor: consolidate database connection logic

Move connection pooling from individual services to
shared db module. Reduces connection overhead by 40%.
```

## Step 4: Commit

After user approves the message:

```bash
git commit -m "$(cat <<'EOF'
<commit message here>

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Quality Checklist

- [ ] Type accurately reflects the change
- [ ] Scope matches affected area (or omitted if broad)
- [ ] Subject is clear without reading the diff
- [ ] Body explains WHY for non-obvious changes
- [ ] Breaking changes are marked with `!` and explained
