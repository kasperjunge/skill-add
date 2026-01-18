---
name: code-review
description: Perform thorough code reviews with actionable feedback. Use when the user says "review", "/review", "code review", asks for feedback on code, wants a PR reviewed, or needs a second pair of eyes on their changes. Analyzes code for bugs, security issues, performance, maintainability, and best practices.
---

# Code Review

Perform thorough code reviews that catch bugs, improve code quality, and help developers grow.

## Philosophy

A great code review:
- Finds bugs before users do
- Shares knowledge across the team
- Improves code without blocking progress
- Teaches, doesn't lecture

## Workflow

1. Understand context (what is this change trying to do?)
2. Review for correctness (does it work?)
3. Review for quality (is it good?)
4. Provide actionable feedback

## Step 1: Gather Context

```bash
# Get the changes to review
git diff main...HEAD

# Or for a specific PR
gh pr diff <number>

# Understand the commit history
git log main..HEAD --oneline

# Check what tests exist
find . -name "*test*" -o -name "*spec*" | head -20
```

Before reviewing code, understand:
- What problem is being solved?
- What approach was chosen?
- Are there constraints I should know about?

## Step 2: Review for Correctness

### Critical Issues (Must Fix)

| Category | What to Look For |
|----------|------------------|
| **Bugs** | Logic errors, off-by-one, null handling |
| **Security** | Injection, auth bypass, data exposure |
| **Data Loss** | Race conditions, missing transactions |
| **Breaking** | API changes, removed functionality |

### Security Checklist

- [ ] User input validated/sanitized
- [ ] SQL queries parameterized
- [ ] Auth checks on protected routes
- [ ] Secrets not hardcoded
- [ ] HTTPS for sensitive data
- [ ] No sensitive data in logs

### Common Bug Patterns

```javascript
// Off-by-one
for (i = 0; i <= arr.length; i++)  // Bug: should be <

// Null/undefined
user.name.toLowerCase()  // Bug: user might be null

// Async issues
const data = fetchData();  // Bug: missing await
console.log(data);         // undefined

// Type coercion
if (value == null)  // Catches null AND undefined
if (value === null) // Only catches null
```

## Step 3: Review for Quality

### Suggestions (Should Consider)

| Category | What to Look For |
|----------|------------------|
| **Clarity** | Naming, structure, comments |
| **Maintainability** | Coupling, duplication, complexity |
| **Performance** | N+1 queries, unnecessary work |
| **Testing** | Coverage, edge cases, mocking |

### Code Smells

- Functions > 50 lines
- Deep nesting (> 3 levels)
- Magic numbers without constants
- Comments explaining "what" not "why"
- Catch blocks that swallow errors
- Boolean parameters (use options object)

### Testing Gaps

- [ ] Happy path tested
- [ ] Error cases handled
- [ ] Edge cases covered (empty, null, max)
- [ ] Integration points mocked appropriately
- [ ] No flaky async tests

## Step 4: Provide Feedback

### Format

```markdown
## Summary

[Overall assessment: approve, request changes, or needs discussion]

## Critical Issues

[Must fix before merge]

### 1. [Issue Title]
**File**: `path/to/file.ts:42`
**Issue**: [What's wrong]
**Why it matters**: [Impact if not fixed]
**Suggestion**: [How to fix]

## Suggestions

[Improvements to consider]

### 1. [Suggestion Title]
**File**: `path/to/file.ts:87`
**Current**: [What exists]
**Suggestion**: [What could be better]
**Why**: [Benefit of change]

## Praise

[What was done well - be specific]

---
*Review generated with [agent-resources](https://github.com/kasperjunge/agent-resources)*
```

### Feedback Guidelines

**Be specific, not vague:**
- Bad: "This function is confusing"
- Good: "Consider splitting `processOrder` into `validateOrder` and `submitOrder` - it's doing two distinct things"

**Explain why:**
- Bad: "Use `const` here"
- Good: "Use `const` here since `config` is never reassigned - signals intent to readers"

**Offer alternatives:**
- Bad: "This is inefficient"
- Good: "This O(n^2) loop could be O(n) with a Set lookup. Here's how: ..."

**Acknowledge tradeoffs:**
- "This adds complexity but the performance gain is worth it for this hot path"
- "Simpler but less flexible - fine if we don't need X later"

### Severity Levels

| Level | Label | Action |
|-------|-------|--------|
| **Blocker** | `[MUST FIX]` | Cannot merge without addressing |
| **Major** | `[SHOULD FIX]` | Strong recommendation |
| **Minor** | `[CONSIDER]` | Nice to have |
| **Nit** | `[NIT]` | Style/preference, take it or leave it |
| **Question** | `[QUESTION]` | Seeking understanding |
| **Praise** | `[NICE]` | Calling out good work |

## Review Types

### Quick Review
Focus: Correctness only
For: Small changes, trusted authors, time pressure

### Standard Review
Focus: Correctness + quality
For: Most PRs

### Deep Review
Focus: All aspects + architecture
For: New features, security-sensitive, public APIs
