# Mekong IDE — The One-Person Company Platform

> XONG = $49 vào ACB Bank. PR merged, self-test pass, HTTP 200 đều CHƯA XONG.

## a16z Doctrine: One-Person Billion-Dollar Company

Marc Andreessen predicts single-person billion-dollar startups enabled by autonomous agents.
Mekong IDE IS this — one subscription replaces a 50-person team with 22 autonomous departments.

**Target customer:** Solo founder / solopreneur ONLY. Not teams. Not enterprise.
**Revenue model:** 1 subscription = 1 person = all departments.

## The Product: Mekong IDE

ONE product. ONE subscription. ONE person runs everything.

1 subscription → 22 autonomous departments → 290 operational commands
→ runs on YOUR machine via Ollama (zero cloud cost)
→ or via RaaS API (pay-per-mission)

### What the customer gets

| Tier | Price | Credits | Access |
|------|-------|---------|--------|
| Starter | $49/mo | 200 | All 22 departments, all 290 commands |
| Growth | $149/mo | 1,000 | + priority execution + webhooks |
| Pro | $499/mo | 5,000 | + dedicated support + custom agents |

Every tier gets ALL departments. Credits = how much you run.

### The 22 Departments (built-in)

Finance, Marketing, Sales, Engineering, Legal, Compliance, HR,
Design, Data, Security, Growth, Venture, CTO, CFO, CMO, CRO,
Operations, Incident, Observability, ML/Automation, Customer Success, Product

### How It Works

```
User: "Create Q1 financial report"
→ Classifier: agent=CFO, domain=finance, cost=1
→ Command loader: finance-budget-plan.md (1236 chars)
→ LLM (Ollama local or cloud): executes with command knowledge
→ Output: structured financial report
→ Credits: -1 from balance
```

## 13 Giants — Distribution, Not Products

| Ch | Giant | Relationship | Purpose |
|----|-------|-------------|---------|
| 始計 | Paperclip (45K) | Go together | Org templates for IDE |
| 作戰 | Coolify (35K) | Ride on top | Deploy IDE cheaply |
| 謀攻 | OpenClaw (351K) | Ride the wave | Distribute IDE skills |
| 軍形 | Supabase (75K) | Ride on top | IDE backend |
| 兵勢 | Next.js (139K) | Ride on top | IDE dashboard |
| 虛實 | Polar.sh (7K) | Ride on top | IDE billing |
| 軍爭 | n8n (150K) | Go together | IDE automation |
| 九變 | Ollama (120K) | Ride on top | IDE brain (local LLM) |
| 行軍 | Grafana (73K) | Ride on top | IDE monitoring |
| 地形 | LangChain (132K) | Go together | IDE RAG pipeline |
| 九地 | CrewAI (48K) | Go together | IDE multi-agent |
| 火攻 | OpenCode (139K) | Go together | IDE CLI shell |
| 用間 | PostHog (32K) | Ride on top | IDE analytics |

## 13 Use Cases (Marketing, Not Products)

Same IDE, different landing pages for different audiences:

1. **Trading Desk** — Finance dept commands for algo-traders
2. **Model Router** — Engineering dept for LLM cost optimization
3. **Content Studio** — Marketing dept for content teams
4. **Legal Counsel** — Legal + Compliance dept for law firms
5. **Dev Agency** — Engineering + CTO dept for dev shops
6. **Growth Engine** — Growth + Marketing dept for startups
7. **Compliance Vault** — Compliance + Security dept for regulated
8. **Business Intelligence** — Data + Analytics dept for analysts
9. **HR Operations** — HR dept for people teams
10. **Sales Operations** — Sales + CRO dept for sales teams
11. **Design Studio** — Design dept for creative agencies
12. **Venture Studio** — Venture + Strategy dept for VCs
13. **Operations Center** — Ops + Incident dept for SRE teams

Each "use case" = same IDE subscription + different landing page.

## Execution Order

1. ✅ Core IDE works (commands, gateway, credits, tenant)
2. ✅ E2E test with Ollama on M1 Max (2026-04-12: all endpoints pass)
3. ✅ Create Polar.sh products (Starter/Growth/Pro) — approved
4. ✅ Wire checkout links (Polar URLs verified in /v1/pricing)
5. ✅ Deploy gateway (api.cashclaw.cc → M1 Max:8000 via CF Tunnel)
6. ✅ Resolve dashboard merge conflicts (page.tsx, .env.example, next.config) — required for #7
7. ⬜ Deploy `ide.mekongmind.com` (Cloudflare Pages — see GO_LIVE_PLAYBOOK §3)
8. ⬜ Run `scripts/smoke-test-payment.sh` — green before announcing
9. ⬜ Founder dry-run: buy Starter $49 yourself, verify webhook → credit deduct → 402 on quota
10. ⬜ First external customer pays → XONG

### Production URLs (2026-04-12)

| Service | URL | Status |
|---------|-----|--------|
| Gateway API | https://api.cashclaw.cc | ✅ LIVE |
| Landing Pages | https://www.mekongmind.com | ✅ LIVE (13/13 pages) |
| Starter Checkout | https://buy.polar.sh/a09a5fa0-63db-42a4-a547-3b1523ffc263 | ✅ 302 |
| Growth Checkout | https://buy.polar.sh/c06a03a3-25cd-4cd3-a13d-e795ee592a4e | ✅ 302 |
| Pro Checkout | https://buy.polar.sh/52b7404c-b420-48cc-a382-ab4b5979f766 | ✅ 302 |
