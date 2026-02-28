# BMad Method vs ClaudeKit vs CCPM — Comparison & Integration Strategy

## Framework Overview

| Aspect | BMad Method | ClaudeKit v2.9.1 | CCPM (cleo) |
|--------|-------------|-------------------|-------------|
| **Layer** | Strategy/Planning | Execution/Implementation | Project Management |
| **Focus** | What to build & why | How to build & ship | Track progress & state |
| **Agents** | 12 persona-based | 17+ task-based | N/A (CLI tool) |
| **Commands** | 55 (bmad-*) | 50+ (/plan, /cook, etc.) | 40+ (cleo *) |
| **Phases** | 4 sequential | Flexible per-command | Phase-based tracking |
| **Scope** | Enterprise planning | Code-level execution | Cross-session persistence |

## Phase Mapping: BMad → ClaudeKit

| BMad Phase | BMad Commands | ClaudeKit Equivalent |
|------------|---------------|---------------------|
| 1-Analysis | `/bmad-brainstorming`, research | `/brainstorm`, `/scout` |
| 2-Planning | `/bmad-bmm-create-prd` | `/plan:hard`, `/plan:parallel` |
| 3-Solutioning | `/bmad-bmm-create-architecture` | `/design` (partial) |
| 3-Solutioning | `/bmad-bmm-create-epics-and-stories` | `/plan:parallel` phases |
| 3-Readiness | `/bmad-bmm-check-implementation-readiness` | No direct equivalent |
| 4-Sprint Plan | `/bmad-bmm-sprint-planning` | Plan task breakdown |
| 4-Dev Story | `/bmad-bmm-dev-story` | `/cook "story"` |
| 4-Code Review | `/bmad-bmm-code-review` | `/review` |
| 4-QA | `/bmad-bmm-qa-automate` | `/test` |
| 4-Retro | `/bmad-bmm-retrospective` | `/journal` |

## Agent Mapping: BMad → ClaudeKit

| BMad Agent | ClaudeKit Agent |
|------------|----------------|
| analyst (Mary) | researcher |
| architect (Winston) | planner |
| pm (Sarah) | project-manager |
| dev (Alex) | fullstack-developer |
| qa (Quinn) | tester |
| sm (James) | project-manager (partial) |
| tech-writer | docs-manager |
| ux-designer | ui-ux-designer |

## Overlap Analysis

### Where BMad EXCELS (ClaudeKit lacks)
1. **Structured phase gates** — Required checkpoints before coding
2. **Architecture-first** — Epics derived from architecture, not guesses
3. **Implementation readiness check** — Validation before sprint
4. **Agent personas** — Consistent named agents with memory
5. **Correct course** — Formal scope change management
6. **Party Mode** — Multi-agent collaboration in one session

### Where ClaudeKit EXCELS (BMad lacks)
1. **Code execution** — `/cook` actually writes code, BMad plans only
2. **Parallel execution** — `/plan:parallel` with wave-based phases
3. **CI/CD integration** — GREEN production verification
4. **80+ Skills** — Domain-specific knowledge (React, Supabase, etc.)
5. **Git workflow** — Commit, PR, worktree management
6. **Debug workflow** — `/debug` with root cause analysis

### Where CCPM EXCELS (Both lack)
1. **Cross-session persistence** — Tasks survive conversation restarts
2. **Dependency tracking** — blockedBy/blocks relationships
3. **Focus management** — One active task per scope
4. **Multi-session** — Parallel agents on different epics
5. **Verification gates** — implemented, testsPassed, qaPassed
6. **Audit trail** — Full operation logging

## Proposed Layered Strategy

```
┌─────────────────────────────────────────────┐
│ LAYER 3: CCPM (cleo) — Persistent State     │
│ Track tasks, sessions, phases, dependencies  │
│ Survives conversation restarts               │
├─────────────────────────────────────────────┤
│ LAYER 2: ClaudeKit — Execution Engine        │
│ /cook, /plan, /test, /review, /debug         │
│ 80+ skills, parallel agents, CI/CD           │
├─────────────────────────────────────────────┤
│ LAYER 1: BMad Method — Strategy Framework    │
│ Analysis → Planning → Solutioning → Impl     │
│ Architecture-first, phase gates, personas    │
└─────────────────────────────────────────────┘
```

### Integration Workflow
1. **BMad** generates PRD, Architecture, Epics/Stories
2. **CCPM** imports stories as tasks with dependencies
3. **ClaudeKit** executes tasks via `/cook` per story
4. **CCPM** tracks completion, verification gates
5. **BMad** retrospective at epic boundaries

## Complement vs Overlap Summary

| Area | Winner | Notes |
|------|--------|-------|
| Strategic planning | BMad | Structured, validated phases |
| Code implementation | ClaudeKit | /cook + skills |
| Task persistence | CCPM | Cross-session state |
| Research | Tie | Both have research agents |
| Code review | Tie | Both adequate |
| Testing | ClaudeKit | /test + tester agent |
| Sprint management | BMad + CCPM | BMad plans, CCPM tracks |
| Documentation | BMad | Tech-writer agent superior |

## Unresolved Questions
1. Can BMad stories auto-import to CCPM tasks?
2. Should BMad config.yaml reference CCPM phases?
3. How to handle BMad "Party Mode" within ClaudeKit subagent model?
