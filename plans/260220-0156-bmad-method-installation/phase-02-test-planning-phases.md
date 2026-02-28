# Phase 02 — Test Planning Phases (Architecture → Epics → Readiness)

## Context Links
- Parent plan: [plan.md](plan.md)
- Depends on: [phase-01-verify-installation.md](phase-01-verify-installation.md)
- Existing PRD: `_bmad-output/planning-artifacts/prd.md`
- Output dir: `_bmad-output/`
- Research: `research/researcher-01-bmad-method-overview.md`

## Overview
- **Priority:** P1
- **Status:** pending
- **Effort:** 45min
- **Description:** Test BMad Phase 3 (Solutioning) — the three required commands that must run in sequence before any implementation can begin. Architecture is generated first, epics/stories are derived from it, then a readiness gate validates everything.

## Key Insights
- PRD already exists at `_bmad-output/planning-artifacts/prd.md` — architect (Winston) will read it
- **Architecture-first principle:** Epics must be created AFTER architecture, not before — this prevents "vibe-coding"
- `/bmad-bmm-check-implementation-readiness` is a formal gate — Winston validates PRD + Architecture + Stories are coherent before any code is written
- All outputs land in `_bmad-output/` per config.yaml paths
- Commands activate persona agents: Winston (architect), Sarah (pm)

## Implementation Steps

1. **Read the existing PRD** before testing — understand what the architect will work with:
   ```bash
   cat _bmad-output/planning-artifacts/prd.md | head -60
   ```

2. **Test `/bmad-bmm-create-architecture`** — activate Winston (architect agent):
   ```
   /bmad-bmm-create-architecture
   ```
   - Winston will read the PRD from `_bmad-output/planning-artifacts/prd.md`
   - He will ask clarifying questions about tech stack, constraints, scale
   - Answer with mekong-cli context: Python 3.11+, Typer, Rich, Node.js orchestration, Antigravity Proxy port 9191
   - Expected output: architecture document saved to `_bmad-output/planning-artifacts/` (e.g., `architecture.md`)
   - Verify file was created before proceeding

3. **Test `/bmad-bmm-create-epics-and-stories`** — activate Sarah (pm agent):
   ```
   /bmad-bmm-create-epics-and-stories
   ```
   - Sarah will read BOTH PRD and Architecture to create aligned epics
   - She will ask how many epics and stories per epic to generate
   - Suggest: 2-3 epics, 3-4 stories each (enough to test without overloading)
   - Expected output: epics/stories document in `_bmad-output/planning-artifacts/`
   - Verify stories reference architectural components (not vague descriptions)

4. **Test `/bmad-bmm-check-implementation-readiness`** — reactivate Winston:
   ```
   /bmad-bmm-check-implementation-readiness
   ```
   - Winston validates: PRD completeness, Architecture clarity, Story-architecture alignment
   - He will flag any gaps or inconsistencies
   - Expected: either "READY" approval or list of items to fix
   - Document what Winston flags — this is the gate quality signal

5. **Capture outputs** — verify all three artifacts exist:
   ```bash
   ls _bmad-output/planning-artifacts/
   # Expected: prd.md, architecture.md (or similar), epics-and-stories.md (or similar)
   ```

6. **Note observations** for Phase 5 comparison:
   - How long did each command take?
   - Did the agents ask good clarifying questions?
   - Were the outputs high-quality and consistent with each other?
   - What would `/plan:hard` + `/design` produce by comparison?

## Todo
- [ ] Read existing PRD to understand context
- [ ] Run `/bmad-bmm-create-architecture` — get Winston's architecture doc
- [ ] Verify architecture file created in `_bmad-output/planning-artifacts/`
- [ ] Run `/bmad-bmm-create-epics-and-stories` — get Sarah's epics
- [ ] Verify epics/stories reference architecture decisions
- [ ] Run `/bmad-bmm-check-implementation-readiness` — get Winston's gate verdict
- [ ] Document all outputs and observations

## Success Criteria
- Architecture document generated with tech decisions for mekong-cli
- Epics/stories reference the architecture (not generic user stories)
- Readiness check produces clear READY/NOT-READY verdict with reasons
- All output files present in `_bmad-output/planning-artifacts/`

## Risk Assessment
- **Medium risk** — interactive agents may ask many questions; be prepared to answer
- If Winston can't find PRD: check config.yaml `planning_artifacts` path is correct
- If stories don't reference architecture: this is a finding to document in Phase 5

## Next Phase
→ [phase-03-test-implementation-phase.md](phase-03-test-implementation-phase.md)
