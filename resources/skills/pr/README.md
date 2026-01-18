# /pr

**PR descriptions that reviewers love.**

Generate comprehensive pull request descriptions from your git diffs. Stop writing "please review" and start getting approvals.

## Install

```bash
uvx add-skill kasperjunge/pr
```

## Usage

When you're ready to create a PR:

```
> /pr
```

Or describe what you need:

```
> create a pr
> write a pr description
> help me with this pull request
```

## What You Get

**Before:**
```
## Changes
- Updated auth.ts
- Fixed bug
- Added tests
```

**After:**
```
## Summary

Implement rate limiting on authentication endpoints to prevent
brute force attacks. Limits to 5 attempts/minute per IP with
exponential backoff.

## Changes

- **Rate Limiter**: Add Redis-backed middleware with configurable limits
- **Auth Routes**: Apply limiter to /login, /register, /reset-password
- **Config**: New RATE_LIMIT_* environment variables
- **Monitoring**: Add rate limit metrics to dashboard

## Testing

- [x] Unit tests for rate limiter logic
- [x] Integration tests with Redis
- [x] Manual testing of lockout flow
- [ ] Load testing (tracked in #456)

## Reviewers

Focus on the Redis connection handling in `middleware/rateLimiter.ts` -
first time using ioredis in this codebase.
```

## Features

- **Analyzes full diff**: Understands all changes, not just file names
- **Reads commit history**: Uses your commit messages to understand intent
- **Groups by feature**: Organizes changes logically, not by file
- **Testing section**: Specific about what was verified
- **Reviewer guidance**: Highlights areas needing attention
- **Creates PR directly**: Uses `gh pr create` to submit

## The Difference

| Aspect | Generic | This Skill |
|--------|---------|------------|
| Summary | "Fix auth issues" | "Fix login timeout causing 5% of users to fail" |
| Changes | List of files | Grouped by feature with context |
| Testing | "Tests pass" | Specific flows and edge cases verified |
| Review | Nothing | Points reviewers to key decisions |

---

Part of [agent-resources](https://github.com/kasperjunge/agent-resources) — the package manager for Claude Code.
