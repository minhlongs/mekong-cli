# Phần 6: Delivery — Tái Cấu Trúc Mekong-CLI

> Status: DRAFT

## 1. Brainstorm Contract (reuse P1)
Outcome: Target file structure, migration checklist, and acceptance criteria for the restructuring.
Constraints: (1) Zero downtime for existing CLI (2) Backward compatible (3) Incremental migration possible
Non-goals: (1) No data migration (2) No breaking API changes
Acceptance: File tree + migration script + acceptance test checklist

## 2. Target File Structure

```
mekong-cli/
├── src/
│   ├── cli/                        # EXISTING — keep as-is
│   │   ├── app_setup.py
│   │   ├── binh_phap_commands.py
│   │   ├── autonomous_commands.py
│   │   ├── governance_commands.py
│   │   ├── binh_phap_dispatcher.py  # EXISTING — keep
│   │   └── sdlc/                   # EXISTING — keep
│   │
│   ├── core/                       # EXISTING — restructure
│   │   ├── binh_phap/              # MOVE topology.py HERE
│   │   │   └── topology.py         # from src/binh_phap/
│   │   ├── binh_phap_escalation.py # KEEP (single source of truth)
│   │   ├── binh_phap_dispatcher.py # KEEP (already in core)
│   │   └── providers.py            # KEEP
│   │
│   ├── commercial/                 # NEW — Ch1/2/5/11/12 domain
│   │   ├── __init__.py
│   │   ├── terrain.py              # Ch1: venture:terrain, positioning
│   │   ├── situation.py            # Ch2: founder:validate, five-factors
│   │   ├── finance.py              # Ch5: finance, pricing, budget
│   │   ├── marketing.py            # Ch11: campaign, outreach
│   │   └── growth.py               # Ch12: launch, growth:experiment
│   │
│   ├── finance/                    # NEW — Ch5 core
│   │   ├── __init__.py
│   │   └── stripe_integration.py   # move from src/auth/
│   │
│   ├── research/                   # NEW — Ch6
│   │   ├── __init__.py
│   │   ├── competitive.py          # from src/core/competitive_intel.py
│   │   └── scout.py                # from src/core/scout_block/
│   │
│   ├── marketing/                  # NEW — Ch11
│   │   └── __init__.py
│   │
│   ├── observability/              # NEW — Ch10
│   │   ├── __init__.py
│   │   └── health.py               # from src/cli/system_commands.py
│   │
│   ├── governance/                 # NEW — Ch2/9
│   │   ├── __init__.py
│   │   └── rbac.py                 # from src/auth/rbac.py
│   │
│   ├── binh_phap/                  # DEPRECATE — move to src/core/binh_phap/
│   │   └── topology.py             # MIGRATE -> src/core/binh_phap/
│   │
│   └── daemon/                     # EXISTING — keep
│       └── jidoka.py
│
├── docs/
│   └── binh-phap-mapping/          # NEW
│       ├── 01-overview.md
│       ├── 02-vertical.md
│       ├── 03-horizontal.md
│       ├── 04-diagonal.md
│       ├── 05-infrastructure.md
│       └── 06-delivery.md          # THIS FILE
│
├── plans/
│   └── binh-phap-deep-mapping/     # NEW — migration artifacts
│       ├── phase1-routing.md       # Fable-only migration (DONE)
│       ├── phase2-structure.md     # This plan
│       └── phase3-commands.md      # New cfo/cmo/cso
│
└── .mekong/
    └── company.json                # EXISTING — add binh_phap_state if missing
```

## 3. Migration Checklist

### Phase 1: DONE
- [x] Fable-only routing in binh_phap_escalation.py
- [x] Dual-path auth (ZuneF + Anthropic fallback)
- [x] mk-brainstorm command created

### Phase 2: Structure Migration (THIS PHASE)
- [ ] Move src/binh_phap/topology.py -> src/core/binh_phap/topology.py
- [ ] Create 5 new directories: commercial/, finance/, research/, marketing/, observability/, governance/
- [ ] Update imports in affected files (app_setup.py, dispatcher)
- [ ] Add __init__.py to all new dirs

### Phase 3: Command Migration
- [ ] Create cfo command (Ch2 financial oversight)
- [ ] Create cmo command (Ch11/12 marketing/growth)
- [ ] Update .claude/settings.json modelRouting rules (note: do NOT change runtime)
- [ ] Wire new commands into app_setup.py

### Phase 4: Testing
- [ ] Unit test: binh_phap_escalation.py resolve_llm_provider() for all levels
- [ ] Unit test: TopologyEngine with new directory structure
- [ ] Integration test: full vertical chain (swot -> plan -> cook -> test -> deploy -> audit)
- [ ] Load test: Jidoka auto-fix on simulated breaking change

## 4. Acceptance Criteria

| ID | Criterion | Verification |
|----|-----------|-------------|
| AC1 | All 13 chapters map to a concrete module | grep -r "Ch[0-9]+" docs/binh-phap-mapping/ |
| AC2 | Single provider source of truth | Only binh_phap_escalation.py imports ANTHROPIC_API_KEY |
| AC3 | ZuneF/Anthropic dual-path works | Test with ZUNEF_API_KEY set and unset |
| AC4 | mk-brainstorm command functional | /mk:brainstorm "test topic" produces brain contract |
| AC5 | No breakage in existing CLI | python3 -m src.main --help runs without error |
| AC6 | Jidoka hooks fire correctly | Simulate error -> check jidoka-alerts.log |

## 5. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Import path breakage during migration | HIGH | MEDIUM | Run import check script after each move |
| ZuneF gateway unavailable | MEDIUM | HIGH | Automatic fallback to direct Anthropic |
| LLM timeout on Fable 1M context | MEDIUM | MEDIUM | 120s timeout, fallback to Opus 4.8 |
| Phiên bị rớt lại (session loss) | HIGH | HIGH | Write plan to docs/ immediately after each part |

## 6. One-Liner Summary (cho dev mới onboard)

> Mekong-CLI uses Binh Pháp (Sun Tzu) 3D topology: vertical chain for sequential execution, horizontal groups for parallel dispatch, diagonal loop for growth feedback. All strategic chapters route to Fable 5 (1M context), everything else to Opus 4.8. Auth goes through ZuneF gateway (team) with Anthropic fallback (dev). Jidoka self-heals on errors. Changes: add 6 new directories, move topology.py to core, create 3 new mk commands.

## 7. Next Actions

1. Review this plan with team
2. Approve Phase 2 migration (or adjust)
3. Execute: move files + update imports
4. Verify: run acceptance tests
5. Deploy: merge to main
