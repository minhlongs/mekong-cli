---
title: "Mekong-CLI RaaS Bridge to AgencyOS"
description: "Build open-core bridge layer connecting mekong-cli (OSS) to AgencyOS (closed) for non-tech RaaS"
status: completed
priority: P1
effort: 24h
branch: master
tags: [raas, bridge, agencyos, open-core, billing, api]
created: 2026-02-27
---

# Mekong-CLI RaaS Bridge to AgencyOS

## Vision

```
Non-tech user (Zalo/Web) --> AgencyOS Dashboard (closed, Next.js)
                                    |
                              [THIS BRIDGE]
                                    |
                        mekong-cli engine (open, Python)
```

## Dependency Graph

```
Phase 01 (Auth/Tenant) ─────────────────────────────────┐
Phase 02 (Credit System) ───────────────────────────┐    │
Phase 03 (RaaS Mission API) ────────────────────┐   │    │
      |           |           |                  │   │    │
      ▼           ▼           ▼                  ▼   ▼    ▼
Phase 04 (Dashboard SSE API)  ◄── needs 01+02+03 combined
Phase 05 (Mission SDK)        ◄── needs 03
Phase 06 (Recipe Registry)    ◄── needs 03
      |           |           |
      ▼           ▼           ▼
Phase 07 (Integration Tests + Docs) ◄── needs all above
```

## Parallel Execution Groups

| Group | Phases | Parallel? | Est. |
|-------|--------|-----------|------|
| A | 01 + 02 + 03 | YES (independent modules) | 8h |
| B | 04 + 05 + 06 | YES (after Group A) | 10h |
| C | 07 | Sequential (after B) | 6h |

## File Ownership Matrix (NO OVERLAP)

| Phase | Owns (creates/modifies) |
|-------|------------------------|
| 01 | `src/raas/auth.py`, `src/raas/tenant.py`, `src/raas/__init__.py` |
| 02 | `src/raas/credits.py`, `src/raas/billing.py` |
| 03 | `src/raas/missions.py`, `src/raas/mission_models.py` |
| 04 | `src/raas/dashboard.py`, `src/raas/sse.py` |
| 05 | `src/raas/sdk.py` (thin client class) |
| 06 | `src/raas/registry.py` |
| 07 | `tests/test_raas_*.py`, `docs/raas-api.md` |
| Gateway | `src/core/gateway.py` (mount raas router ONCE after Phase 03) |

## Phase Status

| # | Phase | Priority | Status | File |
|---|-------|----------|--------|------|
| 01 | Auth & Multi-Tenant | P1 | ✅ completed | [phase-01](phase-01-auth-tenant.md) |
| 02 | Credit/Billing System | P1 | ✅ completed | [phase-02](phase-02-credit-billing.md) |
| 03 | RaaS Mission API | P1 | ✅ completed | [phase-03](phase-03-raas-mission-api.md) |
| 04 | Dashboard SSE API | P2 | ✅ completed | [phase-04](phase-04-dashboard-sse-api.md) |
| 05 | Mission SDK | P2 | ✅ completed | [phase-05](phase-05-mission-sdk.md) |
| 06 | Recipe Registry | P3 | ✅ completed | [phase-06](phase-06-recipe-registry.md) |
| 07 | Integration Tests & Docs | P2 | ✅ completed | [phase-07](phase-07-integration-tests-docs.md) |

## Key Decisions

- **MIT license** for all `src/raas/` code (open-core bridge)
- **Polar.sh** for billing (project mandate, no PayPal)
- **SQLAlchemy** for credit/tenant persistence (already in deps)
- **SSE** over WebSocket for dashboard streaming (simpler for non-tech clients)
- **API key auth** (Bearer token) -- no OAuth complexity for v1
- **File IPC** preserved for Tôm Hùm dispatch (proven stable)

## Validation Log

### Session 1 — 2026-02-27
**Trigger:** Initial plan creation, pre-implementation validation
**Questions asked:** 4 (grouped as Binh Pháp ánh xạ)

#### Questions & Answers

1. **[始計 Database]** Database cho auth, credits, missions — SQLite hay PostgreSQL?
   - Options: SQLite WAL (Recommended) | PostgreSQL ngay | SQLite + Litestream
   - **Answer:** SQLite WAL
   - **Rationale:** Pháp=KISS. Zero-config, đủ cho 1000 tenants v1. Migrate PostgreSQL khi scale.

2. **[作戰 Refund]** Credit refund policy khi mission fail?
   - Options: Auto-refund 100% (Recommended) | Refund 50% | Manual review
   - **Answer:** Auto-refund 100%
   - **Rationale:** Đạo=WIN-WIN. VN market sensitive về tiền. Trust > margin cho launch.

3. **[謀攻 Kênh]** AgencyOS (Next.js) gọi mekong-cli engine qua kênh nào?
   - Options: HTTP REST API (Recommended) | Message Queue | gRPC
   - **Answer:** HTTP REST API
   - **Rationale:** Mưu Công=Bất chiến nhi khuất. Next.js fetch() gọi /raas/* trực tiếp. Zero extra infra.

4. **[軍爭 Scope]** Scope v1 cho launch?
   - Options: P1 only 3 phases (Recommended) | P1+P2 5 phases | Full 7 phases
   - **Answer:** Full 7 phases
   - **Rationale:** User chọn feature-complete. Tất cả 7 phases sẽ implement, parallel execution để giảm wall-clock time.

#### Confirmed Decisions
- Database: SQLite WAL — KISS, zero-config
- Refund: 100% auto — WIN-WIN trust
- Integration: HTTP REST — đơn giản thắng
- Scope: Full 7 phases — feature-complete launch

#### Action Items
- [ ] Tất cả 7 phases implement (không cut scope)
- [ ] Parallel Group A (01+02+03) → Group B (04+05+06) → Group C (07)

#### Impact on Phases
- All phases: Confirm proceed — no scope reduction needed
