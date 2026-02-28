# Phase 04 — Test Advanced Features (Party Mode, Correct Course)

## Context Links
- Parent plan: [plan.md](plan.md)
- Depends on: [phase-03-test-implementation-phase.md](phase-03-test-implementation-phase.md)
- Research: `research/researcher-01-bmad-method-overview.md` (Utility Commands section)
- Research: `research/researcher-02-bmad-vs-claudekit-ccpm.md` (Where BMad EXCELS)

## Overview
- **Priority:** P2
- **Status:** pending
- **Effort:** 30min
- **Description:** Test the two most distinctive BMad utility commands — Party Mode (multi-agent collaboration in one session) and Correct Course (formal scope change management). These have no direct ClaudeKit equivalents and reveal BMad's unique value proposition.

## Key Insights
- **Party Mode** activates multiple BMad agents simultaneously in one Claude session — analyst, architect, pm, dev all present at once for complex decisions
- **Correct Course** is triggered when scope changes mid-project — a formal re-planning command that re-evaluates PRD, Architecture, and Stories without losing progress
- Both are "anytime" commands — can be called at any point in the workflow
- Party Mode is particularly interesting for comparing against ClaudeKit's parallel subagent model
- Correct Course is BMad's answer to the common problem: "The requirements changed, now what?"

## Implementation Steps

### Test A: Party Mode

1. **Invoke `/bmad-party-mode`** with a multi-stakeholder question:
   ```
   /bmad-party-mode
   ```
   Suggested prompt after activation:
   > "We're considering adding a real-time collaboration feature to mekong-cli where multiple agents can share a live context. Evaluate this from analyst, architect, pm, and dev perspectives."

2. **Observe agent coordination:**
   - Do agents take turns or respond simultaneously?
   - Does each agent stay in persona (Mary = business, Winston = tech, Sarah = scope, Alex = effort)?
   - Is there a facilitator or do they self-organize?

3. **Note findings** for Phase 5:
   - How does this compare to ClaudeKit's Task tool spawning parallel subagents?
   - Party Mode = one session, multiple personas vs CK = separate agent threads
   - Key difference: Party Mode maintains shared context; CK subagents have isolated contexts

### Test B: Correct Course

4. **Set up a scope change scenario** — use a realistic change relevant to mekong-cli:
   > "New constraint: mekong-cli must now support Windows PowerShell in addition to macOS/Linux bash. This affects the CLI layer, shell commands, and path handling."

5. **Invoke `/bmad-bmm-correct-course`**:
   ```
   /bmad-bmm-correct-course
   ```
   - Describe the scope change when prompted
   - Observe which agent activates (likely architect Winston or pm Sarah)
   - The command should: assess impact on PRD, flag architecture changes, identify affected stories

6. **Evaluate the output:**
   - Did it identify all impacted artifacts? (PRD sections, architecture decisions, stories)
   - Did it produce a change impact assessment?
   - Did it suggest which stories need rework vs which are unaffected?
   - Did it avoid requiring a full restart of the planning process?

### Optional: Test Utility Commands

7. **Test `/bmad-bmm-quick-spec`** for a small isolated feature (if time permits):
   ```
   /bmad-bmm-quick-spec
   ```
   Use case: "Add a `--json` output flag to the `mekong run` command"
   - This is the fast path for trivial features — bypasses full PRD/Architecture flow
   - Compare output quality vs `/plan:fast` in ClaudeKit

8. **Document all observations** for Phase 5 comparison matrix.

## Todo
- [ ] Run `/bmad-party-mode` with multi-stakeholder question
- [ ] Observe and document agent coordination behavior
- [ ] Note Party Mode vs ClaudeKit parallel subagent differences
- [ ] Set up Windows PowerShell scope change scenario
- [ ] Run `/bmad-bmm-correct-course` with scope change
- [ ] Evaluate: does it identify all impacted artifacts correctly?
- [ ] (Optional) Run `/bmad-bmm-quick-spec` for small feature
- [ ] Document all findings for Phase 5

## Success Criteria
- Party Mode activates multiple distinct agent personas in one session
- Each agent stays in character with their domain perspective
- Correct Course produces a change impact assessment (not a full restart)
- Impact assessment identifies affected PRD sections, architecture decisions, stories

## Risk Assessment
- **Low-medium risk** — these are demonstration commands, no file writes expected for Party Mode
- Correct Course may ask to modify existing artifacts — answer conservatively during test (say "assess only, don't modify yet")
- Party Mode in a single Claude context may hit context limits with 4+ agent personas — if so, document as a finding

## Next Phase
→ [phase-05-compare-and-integrate.md](phase-05-compare-and-integrate.md)
