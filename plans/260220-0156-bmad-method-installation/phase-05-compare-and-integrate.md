# Phase 05 — Compare BMad vs ClaudeKit vs CCPM + Layered Strategy

## Context Links
- Parent plan: [plan.md](plan.md)
- Depends on: [phase-04-test-advanced-features.md](phase-04-test-advanced-features.md)
- Research: `research/researcher-02-bmad-vs-claudekit-ccpm.md`
- Testing observations from Phases 1-4

## Overview
- **Priority:** P1
- **Status:** pending
- **Effort:** 30min
- **Description:** Synthesize all test observations into a formal comparison. Define the layered strategy: BMad (strategy) + ClaudeKit (execution) + CCPM (PM). Map commands, agents, and workflows across all 3 frameworks.

## Key Insights
- BMad excels at structured planning with phase gates and architecture-first
- ClaudeKit excels at code execution with /cook, 80+ skills, parallel agents
- CCPM excels at cross-session persistence, dependency tracking, verification gates
- All 3 are complementary, not competing — different layers of the stack

## Implementation Steps

1. **Compile test observations** from Phases 1-4:
   - Which BMad commands produced high-quality output?
   - Which felt redundant with ClaudeKit equivalents?
   - Where did BMad add value that ClaudeKit can't?
   - What surprised you (positive or negative)?

2. **Create comparison matrix** — update/validate the draft from research report 02:
   | Area | BMad | ClaudeKit | CCPM | Winner |
   |------|------|-----------|------|--------|
   | Strategic planning | Phase gates | /plan:hard | — | BMad |
   | Code implementation | /dev-story | /cook | — | ClaudeKit |
   | Task persistence | — | — | sessions | CCPM |
   | Architecture design | /create-architecture | /design | — | BMad |
   | Sprint management | /sprint-planning | — | phases | BMad+CCPM |
   | Code review | /code-review | /review | — | Tie |
   | Testing | /qa-automate | /test | verification | CK+CCPM |
   | Scope changes | /correct-course | — | — | BMad |
   | Multi-agent | Party Mode | Task subagents | multi-session | Context-dependent |

3. **Define the 3-layer integration workflow:**
   ```
   STRATEGY (BMad):  /bmad-brainstorming → /bmad-create-prd → /bmad-create-architecture
                     → /bmad-create-epics-and-stories → /bmad-check-implementation-readiness

   PM (CCPM):        cleo add epics → cleo session start → cleo focus set story
                     → cleo complete → cleo verify → cleo retrospective

   EXECUTION (CK):   /cook "story from sprint plan" → /test → /review → /commit
   ```

4. **Map BMad phases to combined workflow:**
   - **BMad Phase 1-3** = Pre-implementation planning (runs once per epic)
   - **CCPM** = Import stories as tasks, track sprint progress
   - **CK Phase 4** = Per-story execution loop: `/cook` → `/test` → `/review`

5. **Identify integration points:**
   - BMad epics/stories output → auto-import to CCPM tasks?
   - BMad readiness gate → CCPM phase transition trigger?
   - BMad retro findings → CCPM session notes?

6. **Document recommendations** for `knowledge/bmad-method-framework-intel.md`:
   - When to use BMad vs skip it (complexity threshold)
   - Which BMad commands add most value
   - Which can be replaced by ClaudeKit equivalents

## Todo
- [ ] Compile observations from Phases 1-4 tests
- [ ] Validate comparison matrix with real test data
- [ ] Define 3-layer integration workflow
- [ ] Map BMad phases to combined BMad+CK+CCPM workflow
- [ ] Identify automation opportunities (BMad → CCPM import)
- [ ] Document when-to-use recommendations

## Success Criteria
- Comparison matrix validated against actual test observations
- 3-layer strategy clearly defined with specific commands per layer
- Integration workflow described step-by-step
- Recommendations include complexity thresholds for when to use each tool

## Risk Assessment
- **Low risk** — this is analysis and documentation only
- Risk of bias toward ClaudeKit (it's the active execution engine) — try to be objective
- Some comparisons may be apples-to-oranges — note where frameworks serve different purposes

## Next Phase
→ [phase-06-document-intel.md](phase-06-document-intel.md)
