# /code-review

**Thorough code reviews that catch bugs and improve quality.**

Get a second pair of eyes on your code. Finds bugs, security issues, and opportunities for improvement — with actionable feedback.

## Install

```bash
uvx add-skill kasperjunge/code-review
```

## Usage

Review your current changes:

```
> /review
```

Or be specific:

```
> review this code
> code review my changes
> can you review this PR?
```

## What You Get

```markdown
## Summary

Approve with suggestions. The rate limiting implementation is solid,
but there's one security issue to address before merging.

## Critical Issues

### 1. SQL Injection in User Lookup
**File**: `src/auth/users.ts:47`
**Issue**: User input passed directly to query
**Why it matters**: Attackers could access/modify any user data
**Suggestion**: Use parameterized query:
```typescript
db.query('SELECT * FROM users WHERE id = ?', [userId])
```

## Suggestions

### 1. Consider Connection Pooling
**File**: `src/db/connection.ts:12`
**Current**: New connection per request
**Suggestion**: Use connection pool to reduce latency
**Why**: Current approach adds ~50ms per request

## Praise

[NICE] Clean separation of rate limiter from auth logic —
makes it easy to reuse elsewhere.
```

## What Gets Reviewed

### Critical (Must Fix)
- **Bugs**: Logic errors, null handling, off-by-one
- **Security**: Injection, auth bypass, data exposure
- **Data Loss**: Race conditions, missing transactions

### Quality (Should Consider)
- **Clarity**: Naming, structure, comments
- **Maintainability**: Coupling, duplication, complexity
- **Performance**: N+1 queries, unnecessary computation
- **Testing**: Coverage gaps, edge cases

## Severity Levels

| Label | Meaning |
|-------|---------|
| `[MUST FIX]` | Cannot merge without addressing |
| `[SHOULD FIX]` | Strong recommendation |
| `[CONSIDER]` | Nice to have |
| `[NIT]` | Style preference |
| `[QUESTION]` | Seeking understanding |
| `[NICE]` | Calling out good work |

## Features

- **Security checklist**: OWASP-informed vulnerability detection
- **Common bug patterns**: Off-by-one, null handling, async issues
- **Actionable feedback**: Every issue includes a suggested fix
- **File:line references**: Jump directly to the problem
- **Balanced feedback**: Praise good work, not just criticism

---

Part of [agent-resources](https://github.com/kasperjunge/agent-resources) — the package manager for Claude Code.
