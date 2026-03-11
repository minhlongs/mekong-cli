# Pitch Deck Outline — Mekong CLI Seed Round

**Date:** March 2026
**Covers:** pitch, demo, portfolio
**Format:** 12 slides, ~15 minutes presentation

---

## Slide 1: Title

**Mekong CLI**
*The AI that runs your business.*

- 289 commands • 5 business layers • Universal LLM
- Binh Phap Venture Studio | Seed Round 2026
- [Founder name] | [email] | github.com/longtho638-jpg/mekong-cli

**Visual:** Terminal animation showing `mekong annual "Build a $1M ARR SaaS"` → plan appearing in real time

---

## Slide 2: The Problem

**Running a business requires 50+ different tools. AI tools are fragmented.**

Current state:
- Founder uses ChatGPT for strategy (ad hoc, no execution)
- Developer uses Cursor for code (no business context)
- Ops team uses Zapier for automation (no intelligence)
- Each tool is isolated, no shared context, no execution loop

**The pain:** You spend 40% of time on coordination and tool-switching, not building.

**Quote from target user:** *"I wanted AI to actually do the work, not just give me advice I have to execute manually."*

---

## Slide 3: The Solution

**Mekong CLI: One platform. All 5 business layers. AI executes, verifies, delivers.**

```
👑 Founder    mekong annual / swot / fundraise / okr
🏢 Business   mekong sales / marketing / finance / hr
📦 Product    mekong plan / sprint / roadmap
⚙️ Engineer   mekong cook / fix / deploy / review
🔧 Ops        mekong audit / health / security
```

**Key differentiator:** Not just generation — actual execution via PEV engine:
`Plan → Execute → Verify → Rollback if needed`

**Visual:** Side-by-side: ChatGPT gives advice | Mekong CLI executes and delivers file

---

## Slide 4: Product Demo

**Live demo or recorded walkthrough (3 minutes)**

Demo script:
1. `mekong cook "Build a REST API with JWT auth"` → watch PEV execute → API running in 90 seconds
2. `mekong annual "Plan my SaaS for 2026"` → structured annual plan in 45 seconds
3. `mekong swot` → competitive analysis with real web research
4. `mekong deploy` → Cloudflare Workers deployment, zero config

**Key demo moments:**
- Show the rollback: intentionally break step 2, watch auto-recovery
- Show multi-provider: switch from DeepSeek to Ollama local → same result
- Show the audit trail: `mekong audit` → full execution log

---

## Slide 5: Market Opportunity

**$15B TAM. No direct competitor. Category being created now.**

| Market | Size |
|--------|------|
| AI Developer Tools | $6.2B (28% CAGR) |
| SMB Business Software | $180B total, $12B AI segment |
| AI Automation (RPA replacement) | $13.5B |
| **Addressable intersection** | **~$15B** |

**Why now:**
- LLM costs dropped 90% in 18 months (DeepSeek, Qwen)
- Developer AI adoption crossed 50% in 2025
- "AI business CLI" category gap is wide open
- 10M+ solopreneurs globally seeking structured AI execution

**Visual:** TAM/SAM/SOM funnel → SOM $4.3M by 2028 highlighted

---

## Slide 6: Traction

**[To be updated at time of raise — Q4 2026 targets]**

| Metric | Value |
|--------|-------|
| GitHub Stars | 2,000+ |
| PyPI monthly installs | 10,000+ |
| Paying customers | 100+ |
| MRR | $10,000+ |
| Gross margin | 92.5% |
| LTV:CAC (organic) | 136:1 |
| Commands shipped | 289 |
| Languages/LLM providers | 8+ |

**Logo wall:** Early customers (anonymized or named with permission)

**Quote:** *"I replaced Jira + Notion + ChatGPT with mekong. One tool."*

---

## Slide 7: Business Model

**RaaS — Revenue as a Service. Credits consumed per successful delivery only.**

| Tier | MCU/mo | Price | Gross Margin |
|------|--------|-------|--------------|
| Starter | 200 | $49/mo | 93.5% |
| Pro | 1,000 | $149/mo | 91.8% |
| Enterprise | Unlimited | $499/mo | 89.8% |

**Key economics:**
- Breakeven: 10 customers
- Payback period: <1 month (organic CAC ~$15)
- LTV (blended, 20-month avg lifetime): $2,035

**Revenue forecast:**
- 2026: $150K ARR
- 2027: $900K ARR
- 2028: $4.3M ARR

---

## Slide 8: Technology Moat

**PEV Engine — not just prompting, actual execution with quality gates**

```
Goal Input
    ↓
PLANNER (planner.py)     — LLM decomposes into ordered steps
    ↓
EXECUTOR (executor.py)   — Runs shell/code/API in parallel
    ↓
VERIFIER (verifier.py)   — Exit codes + LLM assessment + tests
    ↓ fail?
ORCHESTRATOR             — Auto-rollback, self-healing, retry
```

**Defensible advantages:**
- 289 commands × 176 JSON contracts = structured task graph (18 months to replicate)
- Universal LLM routing: 8 providers, automatic failover
- `src/raas/` billing: 35+ modules covering metering, idempotency, proration, audit
- Cloudflare-native: $0 infrastructure cost at any scale

---

## Slide 9: Competition

**No direct competitor. Adjacent tools serve 1 layer only.**

| Tool | Layer Coverage | Price | Execution |
|------|---------------|-------|-----------|
| **Mekong CLI** | **All 5 layers** | **$49–$499** | **PEV + rollback** |
| Cursor/Aider | Code only | $20 | Generation only |
| GitHub Copilot | Code only | $10 | Suggestion only |
| Claude Code | Code + agentic | Usage-based | Agentic |
| ChatGPT | General | $20 | Generation only |
| Zapier AI | Workflow only | $19+ | Limited execution |

**Our position:** "The only AI that runs your entire business, not just your code."

---

## Slide 10: Team

**Founder + AI Agents**

**[Founder name]**
- Background: [2-3 lines on relevant experience]
- Built Mekong CLI solo from 0 → 289 commands in [X months]
- Binh Phap Venture Studio — applying 孫子兵法 strategy to software delivery

**AI "team" (Tôm Hùm daemon + specialist agents):**
- LeadHunter, ContentWriter, GitAgent, FileAgent, ShellAgent
- 542 skills catalog, always-on execution
- Equivalent capacity of 5–8 FTE for routine tasks

**Hiring plan (post-raise):**
- Month 1: Senior Python engineer (PEV engine hardening)
- Month 3: Growth marketer (dev community + content)

**Advisors sought:** OSS developer tools founder, SEA SaaS operator

---

## Slide 11: Ask

**Raising $750K on a $4M post-money SAFE**

| Use | Amount |
|-----|--------|
| Engineering hire | $150K |
| Growth hire | $100K |
| LLM API scaling | $80K |
| Paid acquisition | $100K |
| Legal + corp | $30K |
| Founder salary | $200K |
| Buffer | $90K |
| **Total** | **$750K** |

**18-month runway → targets:**
- $3M ARR run-rate
- 500 paying customers
- Agent marketplace live with 100+ community agents
- Series A ready

---

## Slide 12: Vision

**"OpenClaw. I run this company."**

In 5 years:
- Mekong CLI is the default AI operating system for 1M+ businesses
- Agent marketplace with 10,000+ community-contributed agents
- MCP integration: the skill library powering every AI assistant
- IPO candidate: $100M ARR, 89%+ gross margins, $0 infra cost

**The world we're building:** Every founder, developer, and operator has an AI that actually executes — not just advises.

*"Giao việc cho AI → AI lập kế hoạch → thực thi → kiểm tra → giao kết quả."*

---

## Appendix Slides

**A1:** Full command catalog by layer (289 commands)
**A2:** PEV engine architecture deep dive
**A3:** RaaS billing system (`src/raas/` modules)
**A4:** Vietnam market strategy
**A5:** 36-month financial model
**A6:** Technical risk register + mitigations
**A7:** Reference customer case studies
