---
description: Build/implement features end-to-end. 1 command, ~30-60 min.
argument-hint: [feature description or plan path]
allowed-tools: Read, Write, Edit, Bash, Task, Agent
---

# /cook — Cook (Smart Feature Implementation)

**Engineering** — single command.

## Estimated: 3 credits, 30-60 minutes

## Workflow

```
[Intent Detection] → [Research?] → [Plan] → [Implement] → [Test] → [Review] → [Finalize]
```

## Modes

| Mode | Research | Testing | Review Gates |
|------|----------|---------|--------------|
| interactive (default) | ✓ | ✓ | User approval at each step |
| --fast | ✗ | ✓ | User approval at each step |
| --auto | ✓ | ✓ | Auto-approve if score≥9.5 |
| --parallel | Optional | ✓ | User approval at each step |
| --no-test | ✓ | ✗ | User approval at each step |

## Execution

1. Detect intent from arguments
2. Research (if needed)
3. Create/update plan in `./plans/`
4. Implement code
5. Test (spawn tester agent)
6. Review (spawn code-reviewer agent)
7. Finalize (spawn project-manager, docs-manager, git-manager)

## Goal context

<goal>$ARGUMENTS</goal>
