---
description: "Cook command — intelligent feature implementation with modes: auto, fast, parallel, interactive."
---

# /cook — Smart Feature Implementation

**AUTO-EXECUTE MODE (--auto).** Full end-to-end feature implementation.

## Workflow

```
[Intent Detection] → [Research?] → [Plan] → [Implement] → [Test] → [Review] → [Finalize]
```

## Modes

| Mode | Research | Testing | Review Gates |
|------|----------|---------|--------------|
| --auto (default on Antigravity) | ✓ | ✓ | Auto-approve |
| --fast | ✗ | ✓ | Minimal review |
| --parallel | Optional | ✓ | Normal review |
| --no-test | ✓ | ✗ | Normal review |

## Execution Steps

### Step 1: Intent Detection
- Parse user's request to understand what to build
- Identify: new feature, modification, fix, refactor

### Step 2: Research (if needed)
- Scan relevant codebase areas
- Understand existing patterns
- Check dependencies

### Step 3: Plan
- Create brief implementation plan
- For complex features: save to `./plans/`
- For simple features: inline plan

### Step 4: Implement
- Write the code following existing patterns
- Create new files as needed
- Follow project conventions

### Step 5: Test
// turbo
```bash
if [ -f "pyproject.toml" ]; then python3 -m pytest -q --tb=short 2>/dev/null; fi
if [ -f "package.json" ]; then npm test 2>/dev/null; fi
```
Write additional tests if the feature warrants them.

### Step 6: Review
- Self-review for security, performance, edge cases
- Quality check (lint/type)

### Step 7: Finalize
- Update documentation if needed
- Stage changes for commit
- Report summary of what was built

## RaaS Sub-Commands

When used within a RaaS project, these additional sub-commands are available:

| Command | Description |
|---------|-------------|
| `/raas plan` | Plan RaaS delivery sprint |
| `/raas sprint` | Execute sprint tasks |
| `/raas test` | Test RaaS deliverables |
| `/raas deploy` | Deploy RaaS service |
| `/raas review` | Review RaaS code |
| `/raas status` | Check RaaS project status |
| `/raas debug` | Debug RaaS issues |
| `/raas outreach` | Client outreach |
| `/raas pipeline` | Pipeline management |
| `/raas crm` | CRM operations |
| `/raas retro` | Sprint retrospective |
| `/raas roadmap` | RaaS roadmap planning |
| `/raas security` | Security audit |
| `/raas audit` | Full audit |
| `/raas backlog` | Backlog grooming |
| `/raas finance` | Budget planning |
| `/raas marketing` | Marketing campaign |
| `/raas sales` | Sales pipeline |
| `/raas ops` | Health sweep |
