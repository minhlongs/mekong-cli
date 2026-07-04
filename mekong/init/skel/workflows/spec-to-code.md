# Workflow: spec-to-code

**Triggered by:** Founder mission, CEO initiative, feature request
**Departments involved:** CEO, CTO, Designer (via AI/roles/), QA (via AI/roles/), Engineering (AI/org/engineering-*)

## Overview

The spec-to-code pipeline transforms a vague intent into production code through five phases.
Port of gstack `/spec` + `/plan-ceo-review` + `/plan-eng-review` + `/review` pipeline,
adapted to ZenOS 39-agent architecture.

## Phase 1: Spec Refinement (CEO + Founder)

1. **Premise challenge** -- CEO applies Office Hours Reframing:
   - Is this the right problem? Could a simpler framing work?
   - What would happen if we did nothing?
   - What existing agents/workflows already solve this?
2. **10-star vision** -- CEO identifies the 10x version: "what makes this a 10-star product?"
3. **Scope calibration** -- CEO selects mode: EXPANSION / SELECTIVE / HOLD / REDUCTION
4. **Decision log** -- CEO logs the scope decision in `AI/decisions/`
5. **GitHub issue** -- CEO files a GitHub issue with spec template:
   - **Title:** `{type}: {feature name}`
   - **Labels:** `spec`, `phase-1`
   - **Body:** Problem statement, success criteria, scope mode, 10-star vision, rejected alternatives

**Deliverable:** Filed GitHub issue with structured spec

## Phase 2: Architecture Lock (CTO)

1. **Architecture review** -- CTO reviews against:
   - Component boundaries (seed/tree/forest/land compliance)
   - Data flow trace (happy + 3 shadow paths per new flow)
   - Dependency check (no circular imports, no layer violations)
   - Existing code leverage (what already solves this?)
2. **Distribution check** -- If new artifact, include build/publish pipeline in spec
3. **TODOS cross-reference** -- Does this spec conflict with or unlock deferred work?
4. **Worktree plan** -- CTO determines parallelization strategy:
   - Which agents work in parallel? (engineering-frontend + engineering-backend)
   - Which are sequential? (API first, then UI)
   - What's the merge order?

**Deliverable:** Architecture decision record + worktree plan added to issue

## Phase 3: Design (Designer via roles/designer.md)

1. **Design spec** -- Generate DESIGN.md or update existing:
   - Color palette, typography, spacing, component tokens
2. **Screen mockups** -- Using Stitch pipeline:
   - `stitch-ui-design-spec-generator` -> Design Spec JSON
   - `stitch-mcp-generate-screen-from-text` -> UI mockups
   - `stitch-mcp-generate-variants` -> alternatives (if needed)
3. **Dimension rating** -- Rate each screen 0-10 on all 10 design dimensions
4. **Interaction states** -- Default, hover, active, loading, error, empty for every component
5. **Accessibility check** -- WCAG AA: keyboard nav, contrast, touch targets, screen reader

**Deliverable:** DESIGN.md + screen mockups + dimension ratings attached to issue

## Phase 4: Implementation (CEO dispatches to Engineering agents)

1. **Worktree creation** -- CTO creates isolated worktree for this feature:
   ```
   ck worktree create {feature-name}
   ```
2. **Agent dispatch** -- CEO assigns tasks to Engineering agents:
   - `engineering-backend` -> API + database
   - `engineering-frontend` -> UI components
   - `engineering-fullstack` -> integration
3. **Parallel execution** -- Independent workstreams execute in parallel worktrees
4. **Continuous verification** -- Each agent runs tests before committing

**Deliverable:** Code changes in feature worktree, passing tests

## Phase 5: QA + Merge (QA via roles/qa.md)

1. **Pre-landing review** -- QA runs the PR Review Protocol:
   - Structural check (SQL injection, trust boundaries, secrets)
   - Edge case coverage (4 shadow paths per flow)
   - Silent failure detection
   - Interaction edge cases (double-click, stale state, timeout)
2. **Bug detection** -- QA probes for CI-passing-but-prod-breaking bugs:
   - Race conditions, timing dependencies, environment differences
3. **E2E test verification** -- Run full Playwright suite against the branch
4. **Regression check** -- Full test suite must pass (unit + integration + E2E)
5. **PR approval** -- QA signs off, CTO approves architecture, CEO approves scope
6. **Merge to main** -- Squash merge, close source issue

**Deliverable:** Merged PR, closed GitHub issue, deployed feature

## Auto-Close Convention

When a PR merges to main that contains `Closes #{issue-number}` in the PR description,
the GitHub issue auto-closes. The merge commit body must include:

```
Closes #{issue-number}

## What
{one-line description}

## Why
{one-line rationale}

## How
{architecture approach}

## Verification
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] QA sign-off
```

## Phase Transition Rules

| From | To | Gate |
|------|----|------|
| Phase 1 | Phase 2 | CEO approves spec, GitHub issue filed |
| Phase 2 | Phase 3 | CTO approves architecture, worktree plan ready |
| Phase 3 | Phase 4 | Founder approves design mockups |
| Phase 4 | Phase 5 | All unit + integration tests pass |
| Phase 5 | Deploy | QA sign-off + CTO approval + CEO scope sign-off |

## Cross-Department Handoffs

| Step | From | To | Deliverable |
|------|------|----|-------------|
| 1 | Founder | CEO | Mission/request |
| 2 | CEO | GitHub | Filed issue with spec |
| 3 | CEO | CTO | Spec + scope decision |
| 4 | CTO | Designer | Architecture constraints |
| 5 | Designer | CEO | DESIGN.md + mockups |
| 6 | CEO | Engineering | Approved spec + design |
| 7 | Engineering | QA | Code + passing tests |
| 8 | QA | CEO | Review report + sign-off |
| 9 | CEO | CI/CD | Merge approval |

## Dependencies

- GitHub CLI (`gh`) for issue and PR management
- Stitch MCP for design mockup generation
- Playwright for E2E testing
- Worktree isolation (`ck worktree` or `git worktree`)
- ZenOS 39-agent hierarchy (C-Levels + AI/org/ department heads)
