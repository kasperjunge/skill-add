# Multi-Tool Support Tasks

## Overview

Adding support for multiple AI coding tools (Claude Code, Cursor, and future tools) to agr.

## Tasks

| # | Task | Issue | Status |
|---|------|-------|--------|
| 1 | Add Rule Resource Type | [#24](https://github.com/kasperjunge/agent-resources/issues/24) | DONE |
| 2 | Implement Tool Adapter Infrastructure | [#25](https://github.com/kasperjunge/agent-resources/issues/25) | DONE |
| 2.5 | Implement Resource Format Converter | [#30](https://github.com/kasperjunge/agent-resources/issues/30) | DONE |
| 3 | Implement Claude Code Adapter | [#26](https://github.com/kasperjunge/agent-resources/issues/26) | TODO |
| 4 | Implement Cursor Adapter | [#27](https://github.com/kasperjunge/agent-resources/issues/27) | TODO |
| 5 | Multi-Tool CLI Integration | [#28](https://github.com/kasperjunge/agent-resources/issues/28) | TODO |
| 6 | Documentation and Migration | [#29](https://github.com/kasperjunge/agent-resources/issues/29) | TODO |

## Execution Order

```
#24 (Rules) + #25 (Adapter Infra)  [can be parallel]
            ↓
      #30 (Converter)
            ↓
      #26 (Claude Adapter)
            ↓
      #27 (Cursor Adapter)
            ↓
      #28 (Multi-Tool CLI)
            ↓
      #29 (Documentation)
```

## Instructions for Agent

1. Read the issue for the next TODO task
2. Enter plan mode and create an implementation plan
3. Wait for user approval
4. Implement the plan, ensuring all tests pass
5. Update this file: change status from `TODO` to `DONE`
6. Commit the changes
