# Plan 260712-1849-mekong-warptask

**Status:** active
**Source:** xia Warp→mekong-cli analysis (2026-07-12)
**Mode:** improve + port (dual-track parallel)

## Phases

### Phase 1: Improve AI Search [--improve]
Enhance natural language command routing so users can type free-form intent instead of memorizing slash commands.

### Phase 2: Port Workflow Concept [--port]
Document and expose FABRIC DAG + skills as user-facing "Workflows" — zero new code, make existing power discoverable.

## Dependencies
- Phase 2 depends on Phase 1 for shared NL-routing logic
- Meant to be run via: `/ck:cook plans/260712-1849-mekong-warptask/ plan.md --auto --parallel`

## Acceptance Criteria
- [ ] Users can type free-form NL → mekong auto-resolves to right command
- [ ] Existing `/ask` and `/cook` commands enhanced with NL routing
- [ ] Workflow documentation exists and is bilingual (VI+EN)
- [ ] Skills discoverable as "workflow extensions"
