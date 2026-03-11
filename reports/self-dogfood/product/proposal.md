# Product Proposal — Mekong CLI Enterprise Tier

**Document type:** Internal product proposal
**Date:** March 2026 | **Author:** Product
**Decision needed by:** April 1, 2026 (before Product Hunt launch)
**Proposal status:** Draft — pending founder approval

---

## Executive Summary

Propose launching an Enterprise tier at $499/month (or $5,000/year) targeting digital agencies and internal dev teams at Series A–B startups. The tier adds unlimited MCU credits, dedicated support SLA, custom recipe libraries, and a white-label API path. This is not a feature problem — the core product already serves Enterprise users. This is a packaging, pricing, and commitment problem.

**Recommendation:** Launch Enterprise as a "contact us" tier at Product Hunt launch. Close first 3 Enterprise customers manually before building self-serve Enterprise checkout.

---

## Why Enterprise Now

### The Revenue Math

Current public tiers:
- Starter: $49/mo × 1,000 customers = $49K MRR (optimistic 12-month target)
- Pro: $149/mo × 200 customers = $29.8K MRR

A single Enterprise customer at $499/mo = 10 Starter customers in revenue.
Three Enterprise customers = $1,497 MRR from 3 conversations vs. 300 Starter conversions.

At this stage of the company, 3 Enterprise LOIs are worth more than 200 Starter signups.

### The Agency Signal

Agencies are the highest-intent segment (per `persona.md` — Sarah the agency owner). They:
- Can justify $499/mo if it saves 5 hours/month for one developer ($100/hr → $500 saved)
- Have multiple projects → high MCU consumption → would hit Starter/Pro caps
- Want dedicated support — they are billing clients and cannot afford CLI downtime
- Want custom recipes — their workflows are proprietary and repeatable

### The Competition Gap

Devin charges $500/month for one AI software engineer. Mekong at $499/month gives an agency an AI that covers all 5 business layers — not just engineering. The Enterprise tier framing positions Mekong as "your AI operating system" not just "a coding tool."

---

## Proposed Enterprise Tier: "Enterprise"

### Pricing

| Billing | Price | Effective monthly |
|---------|-------|------------------|
| Monthly | $499/mo | $499 |
| Annual | $5,000/year | $417/mo (16% discount) |
| Custom (>$5K/year) | Negotiated | For agencies reselling at scale |

**Pricing rationale:**
- $499/mo is the psychological anchor of "one junior hire's hourly cost for a day"
- Below Devin ($500/mo for one engineering task type) — we do more for the same price
- Above Pro ($149/mo) with clear differentiation — unlimited credits is the key unlock

---

## What's Included

### Unlimited MCU Credits
- No monthly credit cap — run as many commands as needed
- Fair use policy: not for crypto mining or LLM abuse (defined in ToS)
- Credit burn monitoring — flag if account runs >10,000 MCU/day (unusual activity alert)

**Why this matters:** Agencies running Mekong for 5+ clients on Pro tier would hit the 1,000 MCU/month cap. Unlimited removes the anxiety of "will I run out mid-project."

### Dedicated Support SLA
- Response time: 4 hours during business hours (9 AM–6 PM, Mon–Fri, Vietnam/US Pacific)
- Direct Slack channel with the core team (not a ticket system)
- Priority bug fixes: issues reported by Enterprise customers move to top of engineering backlog
- Quarterly check-in call: 30 min with product team to review usage and roadmap

**Why this matters:** Agencies are billing clients. If `mekong deploy` fails at 3 PM on a client delivery day, they need a human, not a support bot. This is a trust feature.

### Custom Recipe Library
- Up to 50 custom private recipes stored server-side
- Recipe Editor UI access (once built — see `estimate.md`)
- Recipes are private to the account — not shared to community marketplace
- Core team will build 3 custom recipes for Enterprise customers as part of onboarding

**Why this matters:** An agency's "client onboarding workflow" or "weekly report generation flow" is a competitive advantage. They need private, version-controlled recipes.

### Priority LLM Routing
- Enterprise requests routed through a dedicated LLM queue
- Lower latency than shared Pro/Starter queue during peak hours
- Able to specify preferred LLM model per recipe (e.g., always use Claude Opus for strategy recipes, Claude Haiku for quick ops tasks)

**Why this matters:** Agencies run time-sensitive workflows. Waiting 60 seconds for a command that Starter users waited 20 seconds for creates a two-tier experience that feels broken.

### White-Label API (Roadmap — v5.2)
- Custom domain: `mekong.youragency.com`
- Custom API key prefix: `sk-agency-xxxx`
- Restrict command set to agency-approved commands only
- Separate billing for agency's clients (agency pays Mekong wholesale, charges clients retail)

**Note:** White-label is on the roadmap but not available at v5.1 launch. Enterprise customers who sign now get access as a committed beta user when it ships. This is a commitment device for early Enterprise signups.

---

## SLA Guarantees

### What We're Committing To

| Metric | Commitment | Measurement |
|--------|-----------|-------------|
| API uptime | 99.5% monthly | Measured by UptimeRobot, public status page |
| Support response | 4 hours business hours | Slack message acknowledgment |
| LLM availability | Best effort (dependent on upstream providers) | Not a hard SLA — disclosed upfront |
| Data retention | Mission history retained 12 months | Per account, exportable |
| Security | SOC 2 Type I target (2027 roadmap) | Not committed for v5.1 |

### What We're Explicitly Not Guaranteeing (yet)

- LLM output quality (we commit to execution, not perfect results)
- Same-day bug fixes (Enterprise bugs get priority, not instant resolution)
- Custom feature development (custom features require a separate contract)
- SOC 2 or ISO 27001 compliance (on roadmap, not current)

**Why be explicit?** Trust is built by not overpromising. The first Enterprise customer who discovers a commitment we can't keep will churn and tell others.

---

## Onboarding Plan (Enterprise Customer)

**Week 1:**
- Account provisioned, API key issued, Slack channel created
- 60-minute onboarding call: use case deep-dive, recipe design session
- Core team builds 3 custom recipes based on onboarding call output

**Week 2:**
- Customer runs first 10 missions independently
- Daily async check-in via Slack: any friction, any blocked commands
- First custom recipe iteration based on feedback

**Month 1:**
- Weekly 30-minute sync: what's working, what's not
- Usage report review: which commands used most, which MCU patterns
- Recipe library expanded based on actual usage

**Quarter 1 review:**
- Full account review: ROI assessment (time saved vs. $499/mo cost)
- Roadmap preview: what Enterprise features are coming
- Renewal discussion if on monthly billing

---

## Pricing Justification

### Cost-to-Serve Analysis (Enterprise)

| Cost item | Monthly estimate |
|-----------|-----------------|
| LLM API costs (unlimited MCU, estimated 3,000–8,000 MCU/mo) | $12–$32 |
| Dedicated support time (est. 2 hrs/mo per customer) | $100 (at $50/hr internal cost) |
| Infrastructure (API, DB, CDN — marginal cost per customer) | $5 |
| Recipe building (onboarding: 3 recipes × 2 hrs) amortized | $25/mo (12-month amortization) |
| **Total cost to serve** | **~$142–$162/mo** |

**Gross margin at $499/mo:** ~68% — strong for a services-adjacent product at this stage.

At $5,000/year (annual): $416/mo effective → ~61% gross margin. Still healthy.

**Break-even:** 1 Enterprise customer covers infrastructure costs for ~30 Starter customers. This tier is disproportionately valuable.

---

## Go-to-Market for Enterprise

### v5.1 Launch Approach: "Contact Us" Not Self-Serve

Do not build Enterprise self-serve checkout at launch. Reasons:
1. We need to learn what Enterprise customers actually need before automating the flow
2. Direct sales conversations uncover use cases we haven't anticipated
3. Enterprise customers expect a human touch at $499/mo — a Polar checkout feels cheap

**Process at launch:**
- agencyos.network/pricing shows Enterprise tier with "Contact Us" button
- Button links to a Typeform: company name, use case, team size, timeline
- Founder responds within 24 hours with a Loom video demo + Calendly link
- 30-minute call → custom Polar invoice → account provisioned manually

**Target: close 3 Enterprise customers before automating the process.**

### Who to Target First

1. **Agencies already using Cursor** — they understand "AI-accelerated development" and are ready to pay for tools that work
2. **Indie hacker agencies** — 1–3 person shops who discovered Mekong through Product Hunt, are on Pro, and are burning through credits
3. **Developer tool studios** — studios that build multiple SaaS products for clients and need the white-label API path

---

## Decision Points

| Decision | Options | Recommendation |
|----------|---------|---------------|
| Launch price | $299, $499, $799 | $499 — matches Devin, above Pro, justified by unlimited MCU |
| Launch timing | At Product Hunt launch vs. 30 days after | At launch — "contact us" requires no engineering |
| Annual discount | 10%, 16%, 20% | 16% (2 months free) — standard SaaS anchor |
| White-label commitment | Promise in v5.1, deliver in v5.2 | Yes — with clear "roadmap beta access" framing |
| Support channel | Slack vs. email vs. ticket | Slack for Enterprise, email for Pro/Starter |

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Enterprise customer churns after 1 month | Medium | High | Strong onboarding + weekly check-in → identify problems early |
| LLM costs exceed estimate for power users | Low | Medium | Fair use policy + usage alerts if >10K MCU/day |
| SLA promise not met (support response) | Low-Medium | High | Only commit if founder has capacity; hire support before scaling past 5 Enterprise |
| White-label delay damages trust | Medium | Medium | Set clear roadmap milestone (v5.2 = Q3 2026), communicate in contract |
