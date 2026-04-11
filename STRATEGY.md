# Mekong automation OS — Strategy

> XONG = Mekong tự bán Mekong, có $ vào tài khoản.
> PR merged, self-test pass, HTTP 200 đều CHƯA XONG.

## The Product: Mekong IDE

Mekong IDE is ONE product. Not 13. Not 22. ONE.

1 subscription → 22 automation departments → 290 operational commands
→ runs on M1 Max via Ollama (zero cloud cost)
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
2. ⬜ E2E test with Ollama on M1 Max
3. ⬜ Create Polar.sh products (Starter/Growth/Pro)
4. ⬜ Wire checkout links
5. ⬜ Deploy gateway
6. ⬜ First customer pays → XONG
