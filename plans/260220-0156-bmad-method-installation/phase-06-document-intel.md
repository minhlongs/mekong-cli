# Phase 06 — Document Intel in `knowledge/`

## Context Links
- Parent plan: [plan.md](plan.md)
- Depends on: [phase-05-compare-and-integrate.md](phase-05-compare-and-integrate.md)
- All research: `research/researcher-01-bmad-method-overview.md`, `research/researcher-02-bmad-vs-claudekit-ccpm.md`
- All test observations from Phases 1-4
- Comparison matrix from Phase 5

## Overview
- **Priority:** P1
- **Status:** pending
- **Effort:** 15min
- **Description:** Compile all findings into a single intel document at `knowledge/bmad-method-framework-intel.md`. This becomes the persistent reference for any agent in the mekong-cli ecosystem that needs to understand BMad Method and how it fits with ClaudeKit and CCPM.

## Key Insights
- Intel doc should be concise (≤150 lines) — agents load it into context
- Structure: What → How → When → Integration → Gotchas
- Referenced by CLAUDE.md deep references table
- Must survive without the test observations — self-contained

## Implementation Steps

1. **Create `knowledge/bmad-method-framework-intel.md`** with this structure:

   ```markdown
   # BMad Method Framework Intel

   ## What is BMad?
   - Version, source, philosophy (3-5 lines)

   ## Installation
   - How installed, modules present, config location

   ## 4 Phases + Commands
   - Table: Phase → Commands → Agent → Purpose

   ## Agent Roster
   - Table: Agent → Name → Specialization

   ## Unique Value (vs ClaudeKit)
   - Architecture-first, phase gates, Party Mode, Correct Course

   ## 3-Layer Strategy
   - BMad (strategy) + ClaudeKit (execution) + CCPM (PM)
   - Integration workflow diagram

   ## When to Use BMad
   - Complexity thresholds
   - Skip for: trivial bugs, simple features → use /cook directly
   - Use for: new products, architecture decisions, enterprise features

   ## Quick Reference
   - Most valuable commands ranked by ROI
   - Common workflow shortcuts

   ## Gotchas & Lessons Learned
   - From testing observations
   ```

2. **Pull content from:**
   - Research report 01 → What, Installation, Phases, Agents
   - Research report 02 → Comparison, Strategy, When-to-use
   - Phase 1-4 observations → Gotchas, Lessons
   - Phase 5 comparison matrix → Strategy, Quick Reference

3. **Update CLAUDE.md deep references table** — add row:
   ```markdown
   | `knowledge/bmad-method-framework-intel.md` | BMad Method: phases, agents, integration strategy | ~150 |
   ```

4. **Verify the doc is loadable** — ensure it's under 150 lines, self-contained, no broken links.

## Todo
- [ ] Create `knowledge/bmad-method-framework-intel.md`
- [ ] Populate from research reports + test observations
- [ ] Add 3-layer strategy workflow
- [ ] Add when-to-use decision tree
- [ ] Add gotchas from testing
- [ ] Update CLAUDE.md deep references table
- [ ] Verify doc is ≤150 lines and self-contained

## Success Criteria
- `knowledge/bmad-method-framework-intel.md` exists and is ≤150 lines
- Covers: What, How, When, Integration, Gotchas
- CLAUDE.md references the doc in deep references table
- Any agent can load this doc and understand BMad's role in the ecosystem

## Risk Assessment
- **Low risk** — documentation only, no code changes
- Risk of the doc being too long — strictly enforce 150 line limit
- If test observations are thin (Phases 2-4 not yet run): note "pending test validation" in Gotchas

## Next Steps
- After all phases complete, this doc becomes the living reference
- Update it as BMad Method releases new versions
- Consider adding to `.claude/rules/` if BMad becomes a mandatory workflow
