# Sales Manager Report — Mekong CLI
*Role: Sales Manager | Date: 2026-03-11*

---

## Executive Summary

Mekong CLI is positioned as an AI-operated business platform with a self-serve PLG motion
and three clear revenue tiers. The product is open-source with a RaaS (Revenue as a Service)
monetization layer — a compelling land-and-expand play for the developer tools market.

---

## Pricing Tiers & Pipeline Targets

| Tier     | Credits/mo | Price | ACV    | Target Conv. |
|----------|-----------|-------|--------|--------------|
| Starter  | 200       | $49   | $588   | 70% of signups |
| Pro      | 1,000     | $149  | $1,788 | 20% upgrade |
| Enterprise | Unlimited | $499 | $5,988 | 10% of Pro |

Monthly Recurring Revenue targets (Q2 2026):
- 200 Starter @ $49 = $9,800 MRR
- 50 Pro @ $149 = $7,450 MRR
- 10 Enterprise @ $499 = $4,990 MRR
- **Total target: $22,240 MRR ($266K ARR)**

---

## ICP (Ideal Customer Profile)

**Primary:** Solo founders and indie hackers building AI-assisted businesses
- Python/TypeScript developers
- Uses OpenRouter, DeepSeek, or Ollama
- Budget-conscious: values $0 infra (Cloudflare Pages/Workers)
- Pain: repetitive scaffold/deploy/review tasks

**Secondary:** Small dev agencies (2-10 devs)
- Already using Claude Code, wants CLI workflow automation
- Values the 289 commands covering business + technical layers
- Starter → Pro upgrade path within 30 days of activation

**Tertiary:** Non-tech founders
- `mekong annual "Business plan 2026"` zero-code entry
- Needs hand-holding → potential high-touch Enterprise

---

## Conversion Funnel

```
GitHub Star → pip install → first cook → credit purchase
    100%         40%           25%           8%
```

Key drop-off: pip install → first cook (60% drop)
Root cause: LLM env var setup friction (3 exports required)
Fix: Add `mekong init --wizard` to auto-configure API key

---

## Pipeline Tracking Metrics

| Metric | Current Baseline | Q2 Target |
|--------|-----------------|-----------|
| GitHub stars/week | TBD | 50 |
| pip installs/month | TBD | 1,000 |
| Activated users (ran cook) | TBD | 400 |
| Free → Paid conversion | TBD | 8% |
| Starter → Pro upgrade | TBD | 20% |
| Net Revenue Retention | TBD | 110% |

---

## Competitive Positioning

| Competitor | Price | Differentiator vs Mekong |
|------------|-------|--------------------------|
| GitHub Copilot | $10/mo | IDE-only, no CLI business layer |
| Cursor | $20/mo | Code editor, not ops/business |
| Devin (Cognition) | $500+/mo | No founder/business commands |
| LangChain CLI | Free | No MCU billing, no PEV loop |

**Mekong advantage:** Only CLI covering all 5 layers (Founder → Ops) with PEV self-healing.

---

## Q2 Sales Priorities

1. **GitHub README optimization** — Star conversion is the top-of-funnel gate
2. **`mekong init --wizard`** — Remove 3-export friction for first activation
3. **Polar.sh webhook verification** — Ensure no payment drops at checkout
4. **Dev community seeding** — r/LocalLLaMA, HN Show, IndieHackers posts
5. **Enterprise pilot** — 2 design partners at $499/mo for feedback loop

---

## Risk Flags

- MCU credit exhaustion before delivery = churn risk → add usage warnings at 80%
- Ollama local users may never convert (free forever) → add cloud model upsell prompt
- HTTP 402 hard stop without grace period → 24hr grace = retention tool

---

## Next Actions (30 days)

- [ ] Define activation event (first successful `mekong cook`)
- [ ] Instrument funnel with PostHog or Mixpanel
- [ ] Draft 3 email sequences: onboard / upgrade nudge / win-back
- [ ] Set up Polar.sh webhooks monitoring dashboard
