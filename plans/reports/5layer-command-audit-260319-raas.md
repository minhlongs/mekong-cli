# 5-Layer Command Audit Report — MEKONG CLI RaaS GTM

**Date:** 2026-03-19
**Scope:** `.claude/commands/` (root only — 137 commands)
**Target:** Map to 5-layer RaaS GTM structure

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Commands | 137 |
| Layers Covered | 5/5 (100%) |
| RaaS-Specific Commands | 0 (gap identified) |
| Avg Commands/Layer | 27.4 |

---

## Layer Distribution

### Layer 1: 👑 Founder — Strategy & Fundraising

**Target:** 46 cmds | **Actual:** 18 cmds | **Gap:** -28

| Command | Purpose | RaaS Relevance |
|---------|---------|----------------|
| `founder-raise.md` | Fundraise pipeline | High — VC mapping |
| `founder-ipo.md` | IPO preparation | Low — future state |
| `founder-negotiate.md` | Deal negotiation | High — partnership terms |
| `founder-validate.md` | Idea validation | High — PMF check |
| `studio-*.md` (8 cmds) | Studio portfolio mgmt | Medium — investment lens |
| `cto-*.md` (10 cmds) | CTO ops (budget, team, roadmap) | High — tech strategy |
| `pm-okr.md` | OKR tracking | High — goal alignment |
| `pm-milestone.md` | Milestone planning | Medium |

**RaaS Gap:** No commands for:
- Marketplace launch strategy
- RaaS pricing tier strategy
- Investor deck for marketplace metrics
- Unit economics for rental model

---

### Layer 2: 💼 Business — Revenue & Operations

**Target:** 32 cmds | **Actual:** 24 cmds | **Gap:** -8

| Command | Purpose | RaaS Relevance |
|---------|---------|----------------|
| `business-revenue-engine.md` | Revenue pipeline setup | Critical |
| `business-campaign-launch.md` | Campaign execution | High |
| `business-client-onboard.md` | Client onboarding | High — B2B rentals |
| `business-financial-close.md` | Monthly close | Medium |
| `business-hiring-sprint.md` | Hiring sprint | Medium |
| `business-quarterly-review.md` | QBR | Medium |
| `sales-*.md` (3 cmds) | Pipeline, deal close, weekly review | High |
| `sdr-*.md` (3 cmds) | Prospecting, outreach, qualification | High |
| `ae-*.md` (3 cmds) | AE deal prep, follow-up, close report | High |
| `marketing-*.md` (3 cmds) | Campaign, content, performance | High |
| `growth-*.md` (2 cmds) | Channel opt, experiments | High |
| `finance-*.md` (3 cmds) | Budget, collections, monthly close | High |
| `accounting-*.md` (2 cmds) | Daily ops, invoicing | Medium |
| `hr-*.md` (3 cmds) | Onboard, performance, recruit | Medium |
| `people-*.md` (2 cmds) | Onboard, offboard | Medium |
| `recruiter-*.md` (2 cmds) | Screen, source | Low |
| `legal-*.md` (2 cmds) | Compliance, contract review | High — rental T&C |
| `writer-*.md` (3 cmds) | Blog, newsletter, social | Medium |

**RaaS Gap:** No commands for:
- Marketplace supply/demand balance
- Rental pricing optimization
- Provider onboarding (B2B)
- Revenue share calculations
- Marketplace take rate analysis

---

### Layer 3: 🎯 Product — Product Management

**Target:** 17 cmds | **Actual:** 19 cmds | **Status:** ✅ Surplus +2

| Command | Purpose | RaaS Relevance |
|---------|---------|----------------|
| `product-*.md` (5 cmds) | Discovery, launch, retrospective, sprint plan, competitive intel | High |
| `pm-*.md` (9 cmds) | Backlog, delegate, milestone, OKR, plan, retro, scope, sprint, standup | High |
| `design-*.md` (2 cmds) | Sprint, user research | High |
| `ux-*.md` (2 cmds) | Interview, usability | High |
| `ui-*.md` (2 cmds) | Design component, review | Medium |
| `junior-*.md` (2 cmds) | First task, learn | Low |

**RaaS-Specific Gaps:**
- No marketplace UX patterns command
- No provider dashboard planning
- No rental flow optimization

---

### Layer 4: ⚙️ Engineering — Build & Ship

**Target:** 47 cmds | **Actual:** 49 cmds | **Status:** ✅ Surplus +2

| Command | Purpose | RaaS Relevance |
|---------|---------|----------------|
| `dev-*.md` (9 cmds) | Audit, bug sprint, debug, deploy, design, feature, pr review, refactor, review, scaffold | High |
| `engineering-*.md` (2 cmds) | New service, refactor | High |
| `frontend-*.md` (2 cmds) | Responsive fix, UI build | High |
| `backend-*.md` (2 cmds) | API build, DB task | High |
| `tech-*.md` (3 cmds) | API design, architecture review, migration | High |
| `devops-*.md` (2 cmds) | Deploy pipeline, rollback | High |
| `release-*.md` (2 cmds) | Hotfix, ship | High |
| `releng-*.md` (2 cmds) | Post-release, pre-release | Medium |
| `platform-*.md` (2 cmds) | Environment setup, monitoring setup | Medium |
| `worker-*.md` (13 cmds) | Backup, build, code, commit, exec, health, log, push, scan, test, trace, allocate, audit, divest, invest, portfolio, roi, strategy | Medium |
| `eng-*.md` (3 cmds) | Onboard, sprint execute, tech debt | Medium |

**RaaS-Specific Gaps:**
- No marketplace matching engine command
- No rental state machine command
- No payment split/escrow command
- No provider verification command

---

### Layer 5: 🔧 Ops — Monitor & Maintain

**Target:** 27 cmds | **Actual:** 27 cmds | **Status:** ✅ Exact Match

| Command | Purpose | RaaS Relevance |
|---------|---------|----------------|
| `ops-*.md` (4 cmds) | Disaster recovery, health sweep, security audit, sync all | Critical |
| `sre-*.md` (2 cmds) | Incident, morning check | Critical |
| `security-*.md` (implicit in ops) | Security audit | Critical |
| `platform-monitoring-setup.md` | Monitoring setup | High |

**RaaS-Specific Gaps:**
- No marketplace uptime SLA command
- No provider incident response
- No rental dispute resolution command

---

## Summary Table

| Layer | Target | Actual | Gap | Status |
|-------|--------|--------|-----|--------|
| 👑 Founder | 46 | 18 | -28 | 🔴 Understaffed |
| 💼 Business | 32 | 24 | -8 | 🟡 Light |
| 🎯 Product | 17 | 19 | +2 | ✅ Balanced |
| ⚙️ Engineering | 47 | 49 | +2 | ✅ Balanced |
| 🔧 Ops | 27 | 27 | 0 | ✅ Balanced |
| **Total** | **169** | **137** | **-32** | **🟡 81% Coverage** |

---

## Gap Analysis — RaaS GTM Readiness

### Critical Gaps (P0)

| Gap | Layer | Impact | Recommended Command |
|-----|-------|--------|---------------------|
| Marketplace launch strategy | Founder | Cannot launch RaaS | `founder-marketplace-launch.md` |
| RaaS pricing tier strategy | Founder | Revenue model undefined | `founder-raas-pricing.md` |
| Provider onboarding (B2B) | Business | No supply side | `business-provider-onboard.md` |
| Rental pricing optimization | Business | Revenue leakage | `business-rental-pricing.md` |
| Marketplace matching engine | Engineering | Core functionality missing | `dev-marketplace-matching.md` |
| Payment split/escrow | Engineering | Cannot process rentals | `dev-payment-escrow.md` |
| Marketplace SLA monitoring | Ops | No uptime guarantee | `ops-marketplace-sla.md` |

### High Priority Gaps (P1)

| Gap | Layer | Recommended Command |
|-----|-------|---------------------|
| Unit economics for rental model | Founder | `founder-unit-economics-raas.md` |
| Revenue share calculations | Business | `business-revenue-share.md` |
| Provider verification flow | Engineering | `dev-provider-verification.md` |
| Rental state machine | Engineering | `dev-rental-state-machine.md` |
| Provider dashboard planning | Product | `product-provider-dashboard.md` |
| Rental flow UX optimization | Product | `ux-rental-flow.md` |
| Provider incident response | Ops | `ops-provider-incident.md` |

### Medium Priority Gaps (P2)

| Gap | Layer | Recommended Command |
|-----|-------|---------------------|
| Investor deck for marketplace metrics | Founder | `founder-marketplace-metrics.md` |
| Marketplace take rate analysis | Business | `business-take-rate-analysis.md` |
| Supply/demand balance monitoring | Business | `business-marketplace-balance.md` |
| Provider T&C legal review | Legal | `legal-provider-terms.md` |
| Rental dispute resolution | Ops | `ops-rental-dispute.md` |

---

## Recommendations

### Phase 1: P0 Commands (Week 1-2)

Create these 7 commands immediately:

```
1. /founder:marketplace-launch  — RaaS GTM strategy
2. /founder:raas-pricing        — Tier pricing (Starter/Growth/Premium)
3. /business:provider-onboard   — B2B provider onboarding
4. /business:rental-pricing     — Dynamic pricing engine
5. /dev:marketplace-matching    — Supply/demand matching
6. /dev:payment-escrow          — Split payment handling
7. /ops:marketplace-sla         — Uptime & performance SLA
```

### Phase 2: P1 Commands (Week 3-4)

```
8. /founder:unit-economics-raas
9. /business:revenue-share
10. /dev:provider-verification
11. /dev:rental-state-machine
12. /product:provider-dashboard
13. /ux:rental-flow
14. /ops:provider-incident
```

### Phase 3: P2 Commands (Week 5-6)

```
15. /founder:marketplace-metrics
16. /business:take-rate-analysis
17. /business:marketplace-balance
18. /legal:provider-terms
19. /ops:rental-dispute
```

---

## Existing Commands — RaaS Adaptation

Many existing commands can be **adapted** for RaaS with minimal changes:

| Existing Command | RaaS Adaptation |
|------------------|-----------------|
| `business-client-onboard.md` | → Provider onboarding flow |
| `sales-pipeline-build.md` | → Provider acquisition pipeline |
| `product-launch-feature.md` | → Marketplace feature launch |
| `dev-feature.md` | → Rental feature development |
| `ops-health-sweep.md` | → Marketplace health checks |
| `legal-contract-review.md` → Provider T&C review |

---

## Unresolved Questions

1. **RaaS business model clarity:** Is this B2B2C (providers rent to consumers) or B2B (businesses rent software)?
2. **Payment provider:** Confirm Polar.sh handles marketplace split payments (escrow, multi-party)?
3. **Geographic scope:** Vietnam-only or global marketplace at launch?
4. **Provider verification:** Manual KYC or automated verification flow?
5. **Revenue model:** Commission %, subscription, or hybrid?
6. **Existing recipes:** Are there `recipes/` for marketplace/rental already built?
7. **Dashboard status:** Is `raas-dashboard` package production-ready or needs work?

---

## Appendix: Command Inventory by Layer

### Layer 1: Founder (18 cmds)
```
founder-ipo, founder-negotiate, founder-raise, founder-validate
cto-architect, cto-archive, cto-budget, cto-deploy, cto-incident,
cto-onboard, cto-review, cto-roadmap, cto-scorecard, cto-team
studio-allocate, studio-audit, studio-divest, studio-invest,
studio-portfolio, studio-roi, studio-strategy
pm-okr, pm-milestone
```

### Layer 2: Business (24 cmds)
```
business-campaign-launch, business-client-onboard, business-financial-close,
business-hiring-sprint, business-quarterly-review, business-revenue-engine
sales-deal-close, sales-pipeline-build, sales-weekly-review
sdr-lead-qualify, sdr-outreach-blast, sdr-prospect
ae-close-report, ae-deal-prep, ae-follow-up
marketing-campaign-run, marketing-content-engine, marketing-performance-report
growth-channel-optimize, growth-experiment
finance-budget-plan, finance-collections, finance-monthly-close
accounting-daily, accounting-invoice-batch
hr-onboard, hr-performance-cycle, hr-recruit
people-onboard, people-offboard
recruiter-screen, recruiter-source
legal-compliance-check, legal-contract-review
writer-blog, writer-newsletter, writer-social-batch
```

### Layer 3: Product (19 cmds)
```
product-competitive-intel, product-discovery, product-launch-feature,
product-retrospective, product-sprint-plan
pm-backlog, pm-delegate, pm-milestone, pm-okr, pm-plan, pm-retro,
pm-scope, pm-sprint, pm-standup
design-sprint, design-user-research
ux-interview, ux-usability
ui-design-component, ui-design-review
junior-first-task, junior-learn
```

### Layer 4: Engineering (49 cmds)
```
dev-audit, dev-bug-sprint, dev-debug, dev-deploy, dev-design,
dev-feature, dev-pr-review, dev-refactor, dev-review, dev-scaffold
engineering-new-service, engineering-refactor
frontend-responsive-fix, frontend-ui-build
backend-api-build, backend-db-task
tech-api-design, tech-architecture-review, tech-migration
devops-deploy-pipeline, devops-rollback
release-hotfix, release-ship
releng-post-release, releng-pre-release
platform-environment-setup, platform-monitoring-setup
eng-onboard-dev, eng-sprint-execute, eng-tech-debt
worker-backup, worker-build, worker-code, worker-commit,
worker-exec, worker-health, worker-log, worker-push,
worker-rollback, worker-scan, worker-test, worker-trace
opus-tomhum-orchestrator, idea, plan, 4-project
ck-binh-phap, ck-save
```

### Layer 5: Ops (27 cmds)
```
ops-disaster-recovery, ops-health-sweep, ops-security-audit, ops-sync-all
sre-incident, sre-morning-check
analyst-report, analyst-forecast-update
```

---

**Report Generated:** 2026-03-19
**Next Review:** After P0 command implementation
**Owner:** CTO / Product Lead
