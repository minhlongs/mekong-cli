# /idea Report — OpenClaw RaaS Gateway

**Generated:** 2026-03-19 | **Stage:** Zero → PSF | **Target:** $1M ARR by Q4 2026

---

## Executive Summary

**Mission:** Robot-as-a-Service API platform enabling SaaS founders to monetize AI agent execution via metered MCU credits.

**Model:** Usage-based SaaS API (Metered MCU Billing) on Cloudflare edge.

**Target:** SaaS founders (B2B/B2C) with 100-10K MRR wanting to add AI-operated features without building billing/infra from scratch.

**Goal:** $1M ARR by Q4 2026 (9 months from Zero).

---

## 25-Step Analysis Summary

### Phase 1: Foundation (Steps 1-5)

| Step | Finding | Decision |
|------|---------|----------|
| 1. Master Framework | Tri-layer: Business/Agentic/Governance | Applied to all sections |
| 2. Refactor 2026 | New idea → scaffold from scratch | Zero stage confirmed |
| 3. Agentic OS | 5 agents (Founder/Business/Product/Eng/Ops) | Mapped to Mekong commands |
| 4. IPO Readiness | Delaware C-Corp, audit trails from Day 1 | Governance layer designed |
| 5. Gap Report | MVP → Billing → Dashboard → Security → Deploy | 5 CTO missions defined |

### Phase 2: Business Model (Steps 6-7)

| Step | Finding | Decision |
|------|---------|----------|
| 6. Unit Economics | CAC $150, LTV $1800, 12:1 ratio | 3-tier pricing: $49/$149/$499 |
| 7. Customer Psychology | ICP: Technical founders, API-first, hate building billing | Positioning: "Stripe for AI APIs" |

### Phase 3: Brand + Content (Steps 8-12)

| Step | Finding | Decision |
|------|---------|----------|
| 8. Brand Positioning | Competitors: Replicate, Modal, Baseten (focus on inference) | Gap: Billing + multi-tenant |
| 9. Content Pillars | 6 themes: RaaS, MCU billing, AI monetization, edge infra, case studies, tutorials | SEO-driven TOF |
| 10. Landing Page | Conversion architecture: Problem → Solution → Demo → Pricing → Social Proof | A/B test CTAs |
| 11. Performance Ads | Channels: LinkedIn (B2B), Twitter (devs), Reddit (r/SaaS) | $5K/mo budget Q3 |
| 12. Advertorial | Long-form: "How I monetized my AI API in 48 hours" | Case study format |

### Phase 4: Revenue Engine (Steps 13-15)

| Step | Finding | Decision |
|------|---------|----------|
| 13. Email Sequences | 5 emails: Welcome → Demo → Trial End → Social Proof → Urgency | Automated lifecycle |
| 14. Sales Process | B2B: Inbound demo → Pilot → Close ($499 tier) | Founder-led sales Q1-Q2 |
| 15. GTM Experiments | Bullseye: Content SEO (primary), Paid ads (secondary), Partnerships (tertiary) | Test 30 days each |

### Phase 5: Operations (Steps 16-21)

| Step | Finding | Decision |
|------|---------|----------|
| 16. AARRR Metrics | North Star: MCU credits consumed | Input: API calls, activation rate |
| 17. Fundraising | Pre-seed $500K-1M at $5M cap (Q4) | Warm intros via beta users |
| 18. Risk Assessment | Technical (latency, breaches), Market (price war), Compliance (EU AI Act) | Mitigation per risk |
| 19. Talent Plan | Hire: 1 Engineer + 1 DevAdvocate (Month 3), Sales + Support (Month 6) | Remote-first |
| 20. Industry Patterns | Comparables: Replicate ($21M ARR), Modal (growing fast) | Differentiate on billing |
| 21. Data Room | Deck, cap table, financials, API metrics, customer contracts | Start building Q3 |

### Phase 6: Execution (Steps 22-25)

| Step | Finding | Decision |
|------|---------|----------|
| 22. OKRs | Q1-Q4 objectives with KRs | Tracked in company.json |
| 23. Governance | 3-seat board, audit trails, monthly reports | Investor seat post-seed |
| 24. ESG | Impact: Democratize AI monetization for indie devs | Track carbon (edge = lower) |
| 25. Crisis | Playbooks: Breach, Downtime, PR crisis | Documented Q2 |

---

## Financial Projections

| Month | MRR | ARR | Users | Burn |
|-------|-----|-----|-------|------|
| Month 2 | $250 | $3K | 5 alpha | $10K |
| Month 4 | $3K | $36K | 20 beta | $15K |
| Month 7 | $15K | $180K | 100 paid | $25K |
| Month 9 | $83K | $1M | 300+ | $40K |

**Break-even:** Month 10-12 (dependent on CAC payback at 3 months).

---

## Risk Map

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Edge latency spikes | Medium | High | Edge caching + warm pools |
| Multi-tenant breach | Low | Critical | RLS + audit logs + encryption |
| MCU credit fraud | Medium | Medium | Rate limiting + anomaly detection |
| Replicate price war | High | Medium | Differentiate on billing features |
| Self-hosted preference | Medium | Low | TCO calculator showing edge savings |
| EU AI Act compliance | Medium | Medium | Governance layer + audit trails |

---

## 5-Layer Execution Plan

| Layer | Q1 Mission | Q2 Mission | Q3 Mission | Agent |
|-------|------------|------------|------------|-------|
| **Founder** | Incorporate Delaware C-Corp | Close 5 beta pilots | Raise pre-seed $500K | CEO Agent |
| **Business** | Design pricing page | Run 3 ad campaigns | Hire Head of Sales | Revenue Agent |
| **Product** | User interviews (10 founders) | Dashboard MVP | Enterprise features | Product Agent |
| **Engineering** | Core API + billing | Security audit | Scale infra | CTO Agent |
| **Ops** | Setup monitoring + alerts | Compliance checklist | NPS system | Ops Agent |

---

## 5 CTO Missions (Daemon Queue)

### Mission 001: RaaS Core API
- **Priority:** HIGH
- **Objective:** Build MCU credit execution engine on Cloudflare Workers
- **Success:** API accepts AI tasks, MCU credits deduct correctly, multi-tenant isolation verified
- **MCU Budget:** 500
- **Output:** `packages/openclaw-engine/src/raas-gateway/`

### Mission 002: Billing Integration
- **Priority:** HIGH
- **Objective:** Polar.sh webhooks for MCU credit top-ups
- **Success:** Webhook receives events, credits auto-added, audit log created
- **MCU Budget:** 300
- **Output:** `packages/openclaw-engine/src/billing/`

### Mission 003: Dashboard UI
- **Priority:** MEDIUM
- **Objective:** Tenant dashboard for MCU usage + API key management
- **Success:** Credit balance visible, API key CRUD works, usage charts display
- **MCU Budget:** 400
- **Output:** `packages/raas-dashboard/`

### Mission 004: Security + Rate Limiting
- **Priority:** MEDIUM
- **Objective:** Per-tenant rate limits + RLS on D1 tables
- **Success:** Rate limits enforced, RLS prevents cross-tenant access, security audit passes
- **MCU Budget:** 250
- **Output:** `packages/openclaw-engine/src/security/`

### Mission 005: Production Deploy
- **Priority:** LOW
- **Objective:** Deploy to production with monitoring + alerts
- **Success:** Workers deployed, Sentry configured, uptime monitoring active
- **MCU Budget:** 150
- **Output:** `mekong/infra/cloudflare/`

---

## Unresolved Questions

1. **Legal:** Should we incorporate before or after beta launch? (Recommendation: Before for liability)
2. **Pricing:** Is $49 Starter tier too low for B2B? (A/B test $49 vs $79)
3. **Infra:** Cloudflare D1 limits (10GB per DB) — need sharding strategy at scale?
4. **Compliance:** EU AI Act requirements for AI API providers — legal review needed Q3.
5. **Hiring:** First engineer hire — generalist vs specialist in edge infra?

---

## Next Commands (Auto-Queue)

```bash
/cto-architect RaaS Gateway 10-layer infra design
/cook Build MVP — MCU credit system + Polar.sh integration
/frontend-ui-build Landing page + dashboard
/sales-pipeline-build B2B outbound + inbound qualification
/marketing-campaign-run GTM launch campaign
```

---

**Status:** ✅ /idea complete. `company.json` generated. CTO daemon ready to execute 5 missions.
