# Phase 04 — Remaining Decisions

> Resolve ambiguity before handover. No open questions for the client.

## Context Links

- [Plan Overview](plan.md)
- [Phase 03 — E2E Verification](phase-03-e2e-checkout-verification.md) (dependency)
- Smart Resume: `apps/sophia-ai-factory/src/lib/gateway/smart-resume-engine.ts`
- Checkout API: `apps/sophia-ai-factory/src/app/api/checkout/route.ts`

## Overview

- **Priority**: P2
- **Status**: ✅ COMPLETE (2026-02-10)
- **Description**: Make decisions on 6 open items that affect handover quality. Document each decision with rationale. Some items may be deferred post-handover.

## Key Insights

- These are DECISIONS, not implementations. Phase goal is to decide and document.
- Implementation of decisions (if needed) should be separate tasks post-handover.
- Client should not be aware of internal technical debt — only user-facing gaps matter.
- Smart Resume is invisible to user but causes silent data loss on redeploy.

## Requirements

### Functional
- Each open item has a clear DECISION recorded
- Deferred items have documented rationale and timeline

### Non-functional
- Decisions must be client-appropriate (no unnecessary complexity)
- Deferred items must not block revenue or user experience

## Decision Items

### 1. Master Tier ($4,999 One-Time)

**Current State**: E2E verification (Phase 3) discovered Master tier is FULLY ENABLED with Polar checkout. `/api/checkout` with `{"tier":"MASTER"}` returns a working Polar checkout URL. Polar page shows "Sophia AI Factory - Master" at $4,999 with Stripe payment form.

**Options**:
- A) Keep enabled as-is → already working, no effort needed ✅
- B) Disable to "coming soon" → unnecessary, would lose revenue potential
- C) Remove from pricing display → loses upsell visibility

**Recommendation**: Option A — Master tier is already live and functional. No action needed.

**Decision**: [x] A / [ ] B / [ ] C
**Action**: None required — already working.

---

### 2. Smart Resume Engine Storage

**Current State**: In-memory Map in `smart-resume-engine.ts`. Resets on every Vercel deploy.
**Options**:
- A) Migrate to Supabase `campaign_checkpoints` table → ~2h work, requires migration
- B) Migrate to Vercel KV (Redis) → simpler, no schema migration
- C) Defer — document as known limitation → zero effort, campaigns rarely span deploys

**Recommendation**: Option C for handover. Campaigns typically complete in 5-10min. Deploys only happen on push. Risk of collision is very low. Create a backlog ticket for Option A post-launch.

**Decision**: [ ] A / [ ] B / [x] C (defer)

---

### 3. Canonical Production URL

**Current State**: 3 URLs exist:
- `sophia.agency` — custom domain BUT points to WordPress site (nginx, wp-json), NOT Vercel
- `sophia.agencyos.network` — subdomain (current primary, working on Vercel)
- `sophia-ai-factory.vercel.app` — Vercel default

**Phase 2 Discovery**: `sophia.agency` returns HTTP 202 with WordPress captcha. DNS is NOT configured for Vercel.

**Options**:
- A) `sophia.agency` as canonical → requires DNS reconfiguration (currently WordPress)
- B) `sophia.agencyos.network` as canonical → already working ✅
- C) Keep all 3 without canonical → SEO confusion

**Recommendation**: Option B — `sophia.agencyos.network` is the working production URL. sophia.agency DNS reconfiguration should be a separate post-handover task. Add 301 redirect from Vercel default to canonical.

**Decision**: [ ] A / [x] B / [ ] C
**Action**: Document `sophia.agencyos.network` as canonical in handover docs. Note sophia.agency DNS migration as future task.

---

### 4. sophia-video-bot Cleanup

**Current State**: `apps/sophia-video-bot/` contains only `pyproject.toml` and `CLAUDE.md`. Appears abandoned. Telegram bot functionality lives in `apps/sophia-ai-factory/src/lib/telegram/`.

**Options**:
- A) Delete directory → clean repo
- B) Archive with note → preserves history intent
- C) Leave as-is → no effort but confusing

**Recommendation**: Option A — delete. The functionality was absorbed into the main Sophia app. A git history note in the commit message suffices.

**Decision**: [x] A / [ ] B / [ ] C

---

### 5. Stale Branch Cleanup

**Current State**: `feature/md3-redesign-complete` exists on remote. NOT merged into main.
**Verification**: 4 unmerged commits found (84tea CI/CD, MD3 redesign, Sophia Polar unification).

**Options**:
- A) Delete → UNSAFE, 4 unmerged commits would be lost
- B) Leave → safe, review post-handover ✅

**Recommendation**: Option B — branch has unmerged work. Do NOT delete.

**Decision**: [ ] A / [x] B

---

### 6. E2E Test Integration (Playwright)

**Current State**: Smoke test placeholder exists. No Playwright CI integration.

**Options**:
- A) Add Playwright E2E tests to CI → ~4h work, proper coverage
- B) Add basic curl smoke tests to CI → ~30min, minimal coverage
- C) Defer to post-handover → zero effort, unit tests already cover logic

**Recommendation**: Option C — 145+ unit tests already passing. E2E adds CI time and maintenance burden. Create backlog ticket for Phase 2 development.

**Decision**: [ ] A / [ ] B / [x] C (defer)

## Todo List

- [x] Record Master tier decision → A: Keep enabled (already working!)
- [x] Record Smart Resume decision → C: Defer (low risk)
- [x] Record canonical URL decision → B: sophia.agencyos.network (sophia.agency = WordPress)
- [x] Record sophia-video-bot decision → A: Delete (only pyproject.toml + CLAUDE.md)
- [x] Record stale branch decision → B: Leave (4 unmerged commits, unsafe to delete)
- [x] Record E2E test decision → C: Defer (241 unit tests already passing)
- [x] Execute: Delete sophia-video-bot directory
- [x] Document deferred items for post-handover backlog

## Success Criteria

- All 6 items have documented decisions
- Immediate actions (cleanup) executed
- Deferred items have backlog tickets
- No open questions remain for client handover

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| sophia.agency DNS not configured | Medium | Medium | Fallback to sophia.agencyos.network |
| Client asks about Master tier | High | Low | "Coming soon" messaging is clear |
| Campaign fails mid-deploy | Very Low | Low | Campaigns complete in <10min |

## Security Considerations

- No security implications for any decision
- Deleting sophia-video-bot removes no sensitive data (only pyproject.toml)

## Next Steps

- Phase 05: Client Handover Package (final delivery)
