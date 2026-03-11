# Mekong CLI — Current Sprint Plan (Q1 2026 Sprint 2)

## Sprint: 2026-03-10 to 2026-03-21 (2 weeks)
**Theme:** PEV Loop Stability + Plugin Marketplace v1
**Sprint Goal:** Ship `mekong plugin install` + harden rollback coverage to 100% on core 20 commands

---

## Sprint Scope

### Scope Definition
Based on roadmap Q1 priorities. Bounded by: 2 engineers (OpenClaw CTO + CC CLI subagent), 10 working days.

**In scope:**
- Plugin marketplace install flow (`src/core/plugin_marketplace.py`)
- Rollback coverage for `cook`, `fix`, `deploy`, `test`, `review`, `plan`
- AGI score exposed in `mekong status`
- MCU gate HTTP 402 end-to-end test
- Cross-session intelligence initial wiring

**Out of scope (next sprint):**
- Browser agent GA
- Swarm mode
- Supabase adapter

---

## Backlog Items (Prioritized)

### P0 — Must Ship

| ID | Task | Estimate | Owner |
|----|------|----------|-------|
| S2-01 | `plugin_marketplace.py`: `install`, `list`, `remove` commands | 2d | CTO |
| S2-02 | `mekong plugin install <name>` → CLI entry in `src/main.py` | 0.5d | CTO |
| S2-03 | Rollback wiring for `cook` command (orchestrator.py) | 1d | CTO |
| S2-04 | Rollback wiring for `deploy` command | 1d | CTO |
| S2-05 | `mekong status` exposes `agi_score.py` output | 0.5d | CTO |
| S2-06 | MCU gate: HTTP 402 → CLI user-facing error message | 0.5d | CTO |

### P1 — Should Ship

| ID | Task | Estimate | Owner |
|----|------|----------|-------|
| S2-07 | Cross-session context: persist last 3 tasks in `.mekong/context.json` | 1d | CTO |
| S2-08 | `mekong cook --watch` file watcher skeleton (inotify/FSEvents) | 1d | CTO |
| S2-09 | `retry_policy.py` → exponential backoff on LLM timeout errors | 0.5d | CTO |
| S2-10 | Factory contract validation: `make self-test` targets 95/100 | 1d | CTO |

### P2 — Nice to Have

| ID | Task | Estimate | Owner |
|----|------|----------|-------|
| S2-11 | `--json` flag audit: verify output consistency for 20 top commands | 0.5d | CC CLI |
| S2-12 | `learner.py`: log planner token usage per command for cost baseline | 0.5d | CC CLI |
| S2-13 | README: add "Plugin System" section with install example | 0.25d | CC CLI |

---

## Daily Plan

### Day 1-2 (Mon-Tue): Plugin marketplace core
- S2-01: `plugin_marketplace.py` — install downloads from PyPI / GitHub URL
- S2-02: CLI wiring — `mekong plugin install requests-plugin`
- Write tests: `tests/test_plugin_marketplace.py`

### Day 3-4 (Wed-Thu): Rollback hardening
- S2-03: `cook` command rollback — reverse steps on verifier failure
- S2-04: `deploy` command rollback — undo Cloudflare deployment on gate fail
- Unit tests for each rollback path

### Day 5 (Fri): MCU gate + AGI score
- S2-05: Wire `agi_score.py` → `mekong status --verbose`
- S2-06: HTTP 402 error → clean user message + credit purchase link
- Integration test: zero-balance → `cook` → 402 → meaningful error

### Day 6-7 (Mon-Tue): Cross-session + retry
- S2-07: `.mekong/context.json` write/read in `orchestrator.py`
- S2-09: Exponential backoff in `llm_client.py` (3 attempts, 2x factor)

### Day 8-9 (Wed-Thu): Quality
- S2-10: `make self-test` — fix failing factory contracts
- S2-11: JSON flag audit on `cook`, `fix`, `plan`, `review`, `deploy`
- S2-12: Learner baseline logging

### Day 10 (Fri): Wrap-up
- Sprint review: demo `mekong plugin install` flow
- Update `docs/project-roadmap.md`
- Tag: `git tag v0.3.0-sprint2`
- Retrospective notes → `reports/overnight/product/retrospective.md`

---

## Definition of Done

- [ ] All P0 tasks merged to `main`
- [ ] `python3 -m pytest tests/` — 0 failures
- [ ] `mekong plugin install <name>` works end-to-end with test plugin
- [ ] `mekong status` shows AGI score
- [ ] HTTP 402 shows user-friendly message (not stack trace)
- [ ] `make self-test` score >= 95/100
- [ ] No new `TODO` or `FIXME` introduced

---

## Risks This Sprint

| Risk | Mitigation |
|------|------------|
| Plugin sandboxing complexity (security) | V1 ships without sandbox — document risk, add to Q2 |
| FSEvents/inotify cross-platform for `--watch` | Ship skeleton only, mark experimental |
| Factory contract test failures >5 | Cap fix effort at 4h, defer rest to S3 |

---

## Metrics at Sprint End

- Sprint velocity: P0 items shipped / planned
- Test count: target 70+ tests (currently 62)
- `make self-test`: target 95/100
- Plugin installs in first week post-release: target 50

---

_Sprint lead: OpenClaw CTO_
_Board: `.mekong/tasks/`_
_Updated: 2026-03-11_
