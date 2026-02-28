# Phase 03 — Test Implementation Phase (Sprint → Dev → Review → Retro)

## Context Links
- Parent plan: [plan.md](plan.md)
- Depends on: [phase-02-test-planning-phases.md](phase-02-test-planning-phases.md)
- Inputs: architecture doc + epics/stories from `_bmad-output/planning-artifacts/`
- Output dir: `_bmad-output/implementation-artifacts/`
- Research: `research/researcher-01-bmad-method-overview.md`

## Overview
- **Priority:** P1
- **Status:** pending
- **Effort:** 45min
- **Description:** Test BMad Phase 4 (Implementation) commands using one story from Phase 2. Tests the full inner loop: sprint planning → dev story execution → code review → retrospective. No real code is shipped — this is a workflow validation test.

## Key Insights
- James (sm) runs sprint planning — selects stories from epics, creates sprint plan
- Alex (dev) executes a single story — reads story, writes implementation plan, then code
- `/bmad-bmm-dev-story` is the core loop command; Alex follows the story spec precisely
- `/bmad-bmm-code-review` is Alex reviewing his own code or another dev's — uses structured checklist
- `/bmad-bmm-retrospective` is James facilitating a team reflection at epic end — generates improvement actions
- For this test, pick the **smallest/simplest story** from Phase 2 output to keep scope tight

## Implementation Steps

1. **Read epics/stories** from Phase 2 — select the smallest story to test with:
   ```bash
   cat _bmad-output/planning-artifacts/epics-and-stories.md | head -80
   ```
   Pick one story that is: well-defined, small scope, no external dependencies.

2. **Test `/bmad-bmm-sprint-planning`** — activate James (sm agent):
   ```
   /bmad-bmm-sprint-planning
   ```
   - James will read epics/stories and ask about sprint capacity and goals
   - Input: ~1 sprint, select 1-2 stories for testing purposes
   - Expected output: sprint plan document in `_bmad-output/implementation-artifacts/`
   - Note: James may ask about team velocity — give a simple answer (e.g., "1 developer, 1 week")

3. **Test `/bmad-bmm-create-story`** — prepare the selected story for dev handoff:
   ```
   /bmad-bmm-create-story
   ```
   - James refines the selected story with acceptance criteria, technical notes, DoD
   - Expected output: refined story file in `_bmad-output/implementation-artifacts/`
   - Verify the story references the architecture document

4. **Test `/bmad-bmm-dev-story`** — activate Alex (dev agent):
   ```
   /bmad-bmm-dev-story
   ```
   - Alex reads the refined story and creates an implementation plan
   - Alex may ask clarifying questions about edge cases or tech choices
   - For this test: Alex should plan but NOT write real production code (flag this is a test)
   - Or optionally: let Alex write code for a trivial piece (e.g., a new CLI flag) to see full flow
   - Expected output: implementation notes or stub code in `_bmad-output/implementation-artifacts/`

5. **Test `/bmad-bmm-code-review`** — Alex reviews the story output:
   ```
   /bmad-bmm-code-review
   ```
   - Alex applies a structured code review checklist (security, quality, tests, docs)
   - Even for stub/test code, he should produce a review with findings
   - Expected output: code review document with PASS/FAIL per criterion

6. **Test `/bmad-bmm-retrospective`** — James facilitates end-of-epic reflection:
   ```
   /bmad-bmm-retrospective
   ```
   - James asks: What went well? What to improve? Action items?
   - Answer based on the BMad testing experience so far in this session
   - Expected output: retrospective doc with concrete action items
   - This is valuable real feedback to capture for Phase 6 intel doc

7. **Document observations** for Phase 5 comparison:
   - Did James's sprint plan align with the architecture from Phase 2?
   - Did Alex's story execution follow the story spec precisely?
   - How does `/bmad-bmm-dev-story` compare to `/cook "story"` in ClaudeKit?
   - What did the retro surface that `/journal` in ClaudeKit wouldn't?

## Todo
- [ ] Read Phase 2 epics/stories — select smallest story for test
- [ ] Run `/bmad-bmm-sprint-planning` — get James's sprint plan
- [ ] Run `/bmad-bmm-create-story` — get refined story for dev handoff
- [ ] Run `/bmad-bmm-dev-story` — get Alex's implementation plan/stub
- [ ] Run `/bmad-bmm-code-review` — get structured review output
- [ ] Run `/bmad-bmm-retrospective` — get James's retro with action items
- [ ] Document all observations for Phase 5

## Success Criteria
- Sprint plan generated and references Phase 2 stories
- Story refined with acceptance criteria and technical notes
- Dev story execution produces an implementation plan (even if stub)
- Code review produces a structured checklist result
- Retrospective generates at least 3 concrete action items
- All outputs land in `_bmad-output/implementation-artifacts/`

## Risk Assessment
- **Medium risk** — Alex (/bmad-bmm-dev-story) may want to write extensive code; constrain scope early
- If sprint planning asks for too much team context: keep answers simple ("1 dev, 1 week sprint")
- If retro feels generic: provide specific observations from the Phase 2/3 testing experience

## Security Considerations
- Do NOT let Alex commit or push any generated code during this test phase
- This is workflow validation only — no production changes

## Next Phase
→ [phase-04-test-advanced-features.md](phase-04-test-advanced-features.md)
