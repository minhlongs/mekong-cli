# Budget Plan — Q2 2026
**Generated:** 2026-03-12 | **Period:** April–June 2026 | **Strategy:** Bootstrap

---

## Executive Summary

Q2 2026 operates on full bootstrap discipline. Zero external capital, zero marketing spend,
zero headcount cost. Growth driven by organic community (GitHub, Discord, HackerNews).
Infrastructure ceiling hard-capped at $20/mo. LLM costs externalized via BYOK model.

---

## Budget Philosophy

Mekong CLI v5.0 follows the **Zero-Burn Bootstrap** strategy:
1. Cloudflare-only infra = $0 fixed platform cost
2. BYOK (Bring Your Own Key) = LLM cost passed to user, not absorbed
3. No paid marketing until $5K MRR achieved
4. No salaries until $10K MRR or external funding
5. Every dollar of revenue goes to runway extension, not growth spend

---

## Q2 Infrastructure Budget

| Service               | Monthly Cap | Q2 Total | Trigger to Upgrade         |
|-----------------------|-------------|----------|----------------------------|
| Cloudflare Workers    | $0 (free)   | $0       | >100K req/day paid tier    |
| Cloudflare D1         | $0 (free)   | $0       | >5GB database              |
| Cloudflare KV         | $0 (free)   | $0       | >100K reads/day            |
| Cloudflare R2         | $0 (free)   | $0       | >10GB storage              |
| Cloudflare Pages      | $0 (free)   | $0       | Never (static sites free)  |
| Domain renewals       | $1          | $3       | agencyos.network + .net    |
| GitHub (Actions)      | $0          | $0       | Free for public repos      |
| Monitoring (optional) | $0–$5       | $0–$15   | If Sentry free tier hit    |
| **Hard Cap**          | **$20/mo**  | **$60**  | Alert if exceeded          |

---

## LLM Cost Model

Mekong CLI uses a BYOK architecture — users supply their own API keys:

```bash
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-yourkey
export LLM_MODEL=anthropic/claude-sonnet-4
```

- **Internal dev usage:** ~$5–10/mo (OpenRouter personal account)
- **Customer cost:** $0 to Mekong (fully externalized)
- **MCU credits:** Charged per successful task delivery, not per token
- **Revenue from MCU:** Margin on credit packs covers future infra scaling

---

## Marketing Budget — Q2 2026

| Channel             | Budget | Strategy                                       |
|---------------------|--------|------------------------------------------------|
| Product Hunt launch | $0     | Organic — community upvotes                    |
| HackerNews Show HN  | $0     | Organic — technical writeup                    |
| GitHub Trending     | $0     | Star campaigns, good README                    |
| Discord community   | $0     | Free server, organic growth                    |
| Twitter/X           | $0     | Founder account, build-in-public               |
| YouTube demos       | $0     | Screen recordings, no production budget        |
| Paid ads            | $0     | Deferred until $5K MRR milestone               |
| **Total Marketing** | **$0** | Zero paid spend Q2                             |

---

## Engineering Budget

| Item                     | Cost  | Notes                                  |
|--------------------------|-------|----------------------------------------|
| Developer salaries       | $0    | Founder-only, deferred compensation    |
| Contractor/freelance     | $0    | Community contributions only           |
| Dev tooling (IDE, etc.)  | $0    | VSCode + Claude Code (existing subs)   |
| Test infrastructure      | $0    | pytest + GitHub Actions (free)         |
| **Total Engineering**    | **$0**|                                        |

---

## Revenue Targets (Q2 2026)

| Month    | Target MRR | Customers     | Actions                            |
|----------|------------|---------------|------------------------------------|
| April    | $490       | 10 Starter    | Product Hunt launch                |
| May      | $1,500     | 10 Pro        | HackerNews Show HN                 |
| June     | $3,500     | Mix of tiers  | Enterprise pilot outreach          |
| **EOQ2** | **$5,000** | 30–50 active  | Trigger: hire community manager    |

---

## Contingency

- **If infra costs spike:** Upgrade CF paid plan ($5/mo Workers Paid). Still under $20 cap.
- **If LLM needed internally:** OpenRouter free credits + personal key. No budget impact.
- **If first enterprise customer:** Legal templates ready (see legal/contract-review.md). No legal spend needed pre-signature.
- **Emergency fund:** N/A — zero burn means zero emergency needed.

---

## Q2 Budget Summary

| Category        | Q2 Total  |
|-----------------|-----------|
| Infrastructure  | $3–$60    |
| Marketing       | $0        |
| Engineering     | $0        |
| Legal           | $0        |
| **Total Spend** | **<$60**  |
| **Revenue**     | **$5,000+** (target) |
| **Net**         | **$4,940+** |

---

## Budget Review Triggers

Review and revise budget if any of these occur:
- MRR crosses $5,000 → allocate 10% to paid marketing
- MRR crosses $10,000 → allocate first salary ($3,000/mo founder draw)
- Enterprise deal signed → allocate legal review budget ($500 one-time)
- Security incident → allocate Sentry paid ($26/mo)

---

*Approved by: Founder | Next review: 2026-04-01*
