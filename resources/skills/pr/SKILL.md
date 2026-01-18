---
name: pr
description: Generate comprehensive PR descriptions from git diffs. Use when creating or updating pull requests, when asked to write a PR description, or when the user says "pr", "/pr", or asks for help with their pull request. Analyzes staged/unstaged changes and commit history to produce thorough, reviewer-friendly descriptions.
---

# PR Description Generator

Generate pull request descriptions that reviewers love and that get PRs merged faster.

## Workflow

1. Gather context (diff, commits, branch info)
2. Analyze changes (what, why, impact)
3. Generate description
4. Create PR with gh CLI

## Step 1: Gather Context

```bash
# Determine base branch
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main"

# Get full diff from base
git diff main...HEAD

# Get commit history with full messages
git log main..HEAD --format="%B---"

# Check for related issues/tickets in commits
git log main..HEAD --oneline | grep -iE "(fix|close|resolve|ref)[s]?\s*#"
```

## Step 2: Analyze Changes

For each significant change, identify:

| Aspect | Question |
|--------|----------|
| **What** | What code changed? |
| **Why** | What problem does this solve? |
| **How** | What approach was taken? |
| **Impact** | What does this affect? |
| **Risk** | What could go wrong? |

Look for clues in:
- Commit messages (especially first lines)
- Code comments and TODOs
- Test file names (reveal intent)
- Deleted code (what was wrong?)

## Step 3: Generate Description

```markdown
## Summary

[1-2 sentences: What does this PR do and why? Lead with the WHY.]

## Changes

[Group by feature/area, not by file]

- **[Component]**: What changed and why
- **[Component]**: What changed and why

## Testing

[Be specific about what was verified]

- [ ] Unit tests pass
- [ ] Tested [specific user flow]
- [ ] Verified [edge case]

## Reviewers

[Optional: Guide the review]

- Focus on: [specific area needing attention]
- Question: [any decisions you're unsure about]

---
*Generated with [agent-resources](https://github.com/kasperjunge/agent-resources)*
```

### Quality Standards

**Summary**
- Lead with WHY, not WHAT
- Be specific: "Fix login timeout causing 5% of users to fail" > "Fix bug"
- One PR = one purpose

**Changes**
- Group logically (by feature, not file)
- Highlight breaking changes with **BREAKING:**
- Note migrations or setup steps

**Testing**
- Include manual testing steps
- Flag areas needing extra review
- Note what ISN'T tested

## Step 4: Create PR

```bash
gh pr create --title "<type>: <description>" --body "$(cat <<'EOF'
<generated description>
EOF
)"
```

For draft PRs: add `--draft`
For specific reviewers: add `--reviewer @username`

## Examples

### Good Summary
> Implement rate limiting on auth endpoints to prevent brute force attacks. Limits to 5 attempts/minute with exponential backoff, reducing attack surface without impacting legitimate users.

### Bad Summary
> Fix auth issues

### Good Changes
```markdown
## Changes

- **Rate Limiter**: Add Redis-backed rate limiting middleware
- **Auth Routes**: Apply limiter to /login, /register, /reset-password
- **Config**: New RATE_LIMIT_* environment variables with sensible defaults
- **Monitoring**: Add rate limit metrics to Datadog dashboard
```

### Bad Changes
```markdown
## Changes

- Changed auth.ts
- Updated config
- Added middleware
```

## Edge Cases

**Large PRs**: Add "Overview" section, consider splitting
**Refactoring**: Emphasize behavior unchanged, explain structural changes
**Bug fixes**: Include symptoms, root cause, fix approach
**Dependencies**: Note new deps and why chosen
**Migrations**: Include rollback steps
