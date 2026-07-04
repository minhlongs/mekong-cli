# 20. Data Room + Investor Materials

> Date: 2026-07-04
> Status: In Progress (Tech Architecture done, remaining 5 documents to create)
> Audience: Angel investors, micro-VCs, strategic angels

---

## Overview

The Mekong CLI data room packages the company for pre-seed due diligence. Six core documents, one repository, one CLI. The thesis: replace $500K/year in team salary with a $49/month AI agent workforce.

| Document | Format | Status | Priority |
|----------|--------|--------|----------|
| One-pager | 1-page PDF | Not started | P0 |
| Pitch deck | 10 slides | Not started | P0 |
| Financial model | 3-year projection | Not started | P0 |
| Tech architecture overview | Markdown + diagrams | Done (ARCHITECTURE.md + docs/) | P1 |
| Competitive landscape | 2-page memo | Not started | P1 |
| User research / beta feedback | Slides + quotes doc | Not started | P2 |

---

## 1. One-Pager (1 Page)

A single printed page that an angel reads and understands in 60 seconds.

**Draft structure:**

```
Header: Mekong CLI — The Venture Studio Operating System

Logline: "$49/month replaces $500K/year in team salary. 22 autonomous departments, 1 human."

Problem:
  - Startups burn $500K+ on team salary before finding PMF
  - Hiring is slow (3-6 months), expensive, and high-risk
  - Founders waste 60% of time on ops, not strategy

Solution:
  - 22 AI agent departments: Marketing, Sales, Engineering, Finance, HR, Ops...
  - One human operator. No headcount. Just outcomes.
  - CLI-first, deploy in 5 minutes

Traction:
  - Product shipped and functional
  - 342+ commands across 6 layers
  - Zero revenue (pre-monetization)

Business Model:
  - SaaS: $49/mo (Starter), $149/mo (Growth), $499/mo (Pro)
  - MCU credit system — pay for compute, not seats
  - Target: 1,000 paid customers, $99K MRR

Team:
  - Founder-market fit. Ship velocity. AI systems expertise.

Ask:
  - $500K pre-seed SAFE ($5M cap / 20% discount)
  - 12-month runway. Key milestones: 1K customers, $50K MRR
```

**Owner:** CEO | **Format:** LaTeX or Canva, export to PDF | **Deadline:** Pre-seed close target

---

## 2. Pitch Deck (10 Slides)

Investor-ready deck following the standard 10-slide VC format.

| Slide | Title | Content Summary |
|-------|-------|-----------------|
| 1 | **Title** | Logo + tagline: "AI agents that run your company" |
| 2 | **Problem** | Startups waste $500K+ on team salary before PMF. Hiring is slow, expensive, high-risk. |
| 3 | **Solution** | 22 autonomous AI departments, 1 human operator, $49/month flat. No HR overhead. |
| 4 | **Product Demo** | CLI walkthrough video (90s). Show: `mekong marketing/campaign-run`, `mekong finance/report`, `mekong eng/cook`. |
| 5 | **Market Size** | TAM: 10M early-stage startups globally. SAM: 500K AI-native founders. Target: $5B ARR at scale. |
| 6 | **Traction** | Product shipped. 342+ commands live. Zero revenue (pre-monetization — billing being built). |
| 7 | **Business Model** | Three SaaS tiers, MCU credit system, no per-seat pricing. Unit economics: 6x LTV/CAC, 85% gross margin. |
| 8 | **Competition** | Traditional BPO ($100K+/yr) vs. single-agent Copilot ($10-20/mo per seat) vs. full-stack Mekong (22 departments, $49/mo). |
| 9 | **Go-to-Market** | Developer community (GitHub, Hacker News). Content marketing. Product-led growth. Affiliate program. |
| 10 | **Ask** | $500K pre-seed. Use of funds: 70% product, 20% GTM, 10% legal/ops. |

**Owner:** CEO | **Format:** Canva + Google Slides | **Deadline:** Pre-seed close target

---

## 3. Financial Model (3-Year Projection)

Built in Google Sheets with three tabs: Inputs, P&L, Cash Flow.

**Key Assumptions (Base Case):**

| Metric | Year 1 | Year 2 | Year 3 |
|--------|--------|--------|--------|
| Paid customers | 1,000 | 5,000 | 20,000 |
| Blended ARPU | $99/mo | $109/mo | $119/mo |
| Monthly churn | 5% | 4% | 3% |
| ARR | $1,188K | $6,540K | $28,560K |
| Gross margin | 85% | 87% | 90% |
| Net burn | $240K | Break-even | Profitable |

**Revenue Breakdown:**

| Stream | Y1 % | Y2 % | Y3 % |
|--------|------|------|------|
| Subscription (monthly) | 60% | 50% | 40% |
| Subscription (annual) | 25% | 30% | 35% |
| Usage overage | 10% | 12% | 15% |
| Professional services | 5% | 8% | 10% |

**Cost Structure (Year 1, $99K MRR):**

- LLM API costs: 10-12% of revenue ($10-12K/mo)
- Infrastructure (Workers, D1, R2): 2-3% of revenue ($2-3K/mo)
- Payment processing: 2-3% of revenue ($2-3K/mo)
- Total COGS: ~15% of revenue
- Headcount: 2 FTEs post-seed (engineer + developer advocate)

**Scenario Analysis:**

| Scenario | Y3 ARR | Probability |
|----------|--------|-------------|
| Bear (2K customers, $89 ARPU, 7% churn) | $2.1M | 20% |
| Base (5K customers, $109 ARPU, 4% churn) | $6.5M | 60% |
| Bull (10K customers, $129 ARPU, 3% churn) | $15.5M | 20% |

**Owner:** Finance (CEO) | **Format:** Google Sheets, export to PDF | **Deadline:** Pre-seed close target

---

## 4. Technical Architecture Overview (Done)

The tech architecture is fully documented and investor-ready.

**Location:** `/Users/macbook/mekong-cli/docs/ARCHITECTURE.md` + supporting docs.

**Key points for investor summary:**

```
Architecture: 6-Layer Model

  Layer 1 — CLI Entry (mekong wrapper → CC CLI / Gemini / Qwen)
  Layer 2 — PEV Engine (Plan → Execute → Verify loop)
  Layer 3 — Agent Layer (22+ autonomous agents)
  Layer 4 — LLM Router (any provider, 3-env-var config)
  Layer 5 — MCU Billing (credit system, HTTP 402 on zero balance)
  Layer 6 — Infrastructure (Cloudflare-only: Workers + D1 + R2 + KV)

Deployment: CF-direct doctrine. Zero server management. $0 base cost.
Security: Zod validation on all inputs. No `:any` types. Audit trail.
Quality Gates: npm run build (0 errors), npm test (all pass), no console.log.
```

**Investor-friendly one-pager on architecture:** Not yet created (follow-up task after core data room).

---

## 5. Competitive Landscape

| Dimension | Mekong CLI | Single-Agent Tools (Copilot) | BPO / Agencies | No-Code Platforms (Bubble) |
|-----------|-----------|------------------------------|----------------|----------------------------|
| Departments | 22 autonomous | 1 (code assistant) | 5+ but $100K+/yr | N/A (build, not operate) |
| Price | $49/mo flat | $10-20/mo per seat | $50-200/hr | $30-200/mo + usage |
| Autonomy | End-to-end workflows | Snippet generation | Task execution | User-driven |
| Time to value | 5 minutes | 10 minutes | 2-4 weeks | 1-4 weeks |
| Scaling | Instant | Limited by human | Headcount-bound | Build-bound |
| Technical skill | CLI (medium) | CLI (medium) | None | Low-code |

**Moat Arguments for Investors:**

1. **Department orchestration** — No competitor ties 22+ autonomous departments into one CLI with cross-department workflows (e.g., Marketing triggers Engineering which triggers Finance).
2. **Provider-agnostic LLM routing** — 7 fallback providers, zero vendor lock-in. The product works if OpenAI goes down.
3. **PEV engine** — Plan-Execute-Verify is a superior reliability pattern vs. single-shot agent execution. Built-in verification gates catch mistakes before they compound.
4. **CLI-first, cloud-native** — Deploy to Cloudflare in 5 minutes. No servers, no ops team, no DevOps hiring.
5. **MCU billing** — Pay for compute, not seats. Aligns cost with value delivered, not headcount.

**Emerging threats to monitor:**
- AI-native agency platforms (autoai, agent.ai)
- Full-stack agent frameworks (LangGraph, CrewAI — these are frameworks, not products)
- Vertical agents (sector-specific automation tools)

**Owner:** CEO/CTO | **Format:** 2-page memo + slide in pitch deck

---

## 6. User Research / Beta Feedback

**Current state:** No formal user research conducted. No beta program running.

**Plan to build this section:**

| Phase | Action | Timeline | Output |
|-------|--------|----------|--------|
| Phase 1 | Early adopter program — 50 founders get 3 months free in exchange for feedback | Month 1-2 | 20 structured interviews, 10 case studies |
| Phase 2 | NPS survey deployment + usage analytics | Month 3 | Quantitative retention data, NPS score |
| Phase 3 | Competitive positioning validation via user interviews | Month 4-6 | Positioning document, messaging framework |

**Interim narrative for investors (pre-data):**

> "Mekong CLI has not yet been user-tested in a formal beta program. The product ships complete — 342+ commands, 22 agent types, full PEV engine — but customer validation is the next milestone. The early adopter program (Month 1-2 post-funding) will generate the structured feedback and case studies needed for the Seed round."

**Template: Beta feedback collection form (to build):**

```
- What department did you use? (Marketing / Sales / Engineering / Finance / HR / Ops)
- What was the task? (free text)
- Did the agent complete it successfully? (Yes / Partial / No)
- How long would this have taken manually? (___ hours)
- Would you use this agent again? (1-5)
- What was missing or broken? (free text)
```

**Owner:** CEO/Product | **Format:** Google Forms → notion or Airtable | **Deadline:** Month 2 post-funding

---

## Data Room Checklist — By Priority

| # | Item | Status | Hours to Create | Owner |
|---|------|--------|-----------------|-------|
| 1 | One-pager (1 page) | Not started | 4h | CEO |
| 2 | Pitch deck (10 slides) | Not started | 12h | CEO |
| 3 | Financial model (3-year) | Not started | 8h | Finance |
| 4 | Tech architecture summary | Done | 0h (exists) | CTO |
| 5 | Competitive landscape memo | Not started | 4h | CEO/CTO |
| 6 | Beta feedback / user research | Not started | 20h (phased) | Product |

**Total estimated creation time:** 28 hours directly + 20 hours phased research.
**Target completion:** Before pre-seed close.

---

## Investor Communication Templates

**Cold email intro:**

> "Subject: Mekong CLI — AI agents that run your company
>
> Hi [Name],
>
> $49/month replaces $500K/year in team salary. That's the Mekong CLI thesis — 22 autonomous AI departments, one human operator, no headcount.
>
> Product is shipped and functional. Zero revenue (pre-monetization). Looking for $500K pre-seed to close the billing loop and scale GTM.
>
> Data room: [link]
> Would love 15 minutes to show you the demo."

**Follow-up after meeting:**

> "Subject: Following up — Mekong CLI
>
> Thanks for the time today, [Name].
>
> Key takeaway from our conversation: [their feedback]
>
> Data room attached. Happy to do a deeper technical walkthrough or share the live product access.
>
> Would you like to schedule a follow-up with the technical team?"

---

## Open Questions

1. Should the one-pager and pitch deck be bilingual (Vietnamese + English) given the operator base, or English-only for US VC targeting?
2. Is Canva sufficient for the pitch deck, or should we invest in a professional designer ($500-1K)?
3. The financial model assumptions (1K customers Y1) require a funded GTM engine — is a slower ramp more credible for a pre-seed deck?
4. Should we commission a third-party market sizing report (e.g., Gartner, Statista) to validate the TAM/SAM/SOM figures?
5. Is the zero-revenue position a dealbreaker for pre-seed, or does a shipped product compensate? Should we monetize before fundraising?

---

*This document is part of the Mekong CLI company blueprint. Last updated: 2026-07-04.*
