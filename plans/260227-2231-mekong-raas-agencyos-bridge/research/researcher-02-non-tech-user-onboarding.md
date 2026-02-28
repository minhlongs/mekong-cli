# Research: Bridging CLI Tools to Non-Tech Users via Dashboard/Web Interface

**Date:** 2026-02-27
**Researcher:** researcher-02
**Topic:** Patterns for exposing CLI/AI agent systems to non-technical users

---

## 1. CLI → Web Dashboard Patterns (Reference: Vercel, Railway, Render, Coolify)

### Core pattern: "Git push → Done"
All successful platforms abstract CLI complexity into 3-step onboarding:
1. Connect GitHub repo (OAuth)
2. Configure via form/env vars in UI
3. One-click deploy → logs stream in real-time

### Key UX decisions that won users:
- **Railway**: Clean UI, GitHub connect → live in minutes, logs front-and-center
- **Vercel**: Instant preview deploys, domain auto-assigned, no config file needed
- **Render**: Near-zero config; docker or buildpack auto-detected
- **Coolify** (self-hosted): Same Vercel-like dashboard, on your own server — proves the pattern is replicable

### Lessons for Mekong/AgencyOS:
- Never show raw CLI commands to end-user — translate to "Run Task" buttons
- All outputs (logs, errors, success) streamed as readable prose, not terminal output
- Onboarding: Connect account → pick template/recipe → execute; no config file writing

---

## 2. Dashboard Patterns for Autonomous AI Agent Monitoring

### What the market shows (2025–2026):
- AI agent tool sprawl hit 67% of orgs — unified dashboard is the killer feature
- Winning dashboards track: task status, token cost, latency, error rate, agent decision trail
- LangGraph, Datadog LLM Observability, Braintrust lead in observability tooling

### Must-have panels for Mekong dashboard:
| Panel | Data |
|-------|------|
| Mission Queue | Pending / Running / Done / Failed tasks |
| Agent Activity | Which agent ran, what command, duration |
| Cost Tracker | Credits consumed per mission, cumulative |
| Health Status | Proxy alive, model, last ping |
| Log Stream | Real-time tail of agent output (redacted for non-tech) |

### Non-tech UX rule:
- Replace "RESOURCE_EXHAUSTED 429" with "Agent is cooling down, retry in 2 min"
- Replace task IDs with human labels: "Menu Update Task #3 — 84Tea"
- Color-coded: green=done, yellow=running, red=failed

---

## 3. Exposing CLI as API Endpoints

### Pattern: HTTP wrapper over CLI process

```
POST /api/missions          → spawn new task (maps to task-watcher.js)
GET  /api/missions/:id      → poll status
GET  /api/missions/:id/logs → stream logs (SSE or WebSocket)
POST /api/missions/:id/cancel → kill task
GET  /api/agents/health     → proxy + brain status
```

### Implementation approaches:
- **Node.js**: `child_process.spawn` wraps expect brain; stdout piped to SSE stream
- **FastAPI**: Python subprocess wrapper; `/run` endpoint triggers `mekong cook`
- **Existing**: `apps/raas-gateway/` (Cloudflare Worker) already provides gateway layer — extend it

### Auth pattern:
- API key per agency account (Bearer token)
- Dashboard uses same key as backend — single auth layer
- Webhook callbacks: task done → POST to agency's webhook URL

---

## 4. Credit/Billing System for AI Task Execution

### Industry pricing models (2025):

| Model | Example | Best for |
|-------|---------|---------|
| Per-resolution | $0.99/task (Intercom Fin AI) | Predictable SMB |
| Credit bundles | 100 credits = $9 | Prepay, low churn |
| Tiered subscription | $49/$99/$199/mo | Agency reseller |
| Usage-based | Token-count billing | High-volume |

### Recommended for AgencyOS RaaS:
- **Credit bundles** as primary: Vietnamese SMBs prefer prepay (no surprise bills)
- 1 credit = 1 simple mission (e.g., social post), 5 credits = complex mission (menu update + photo)
- Bundle tiers: Starter 50cr/$5, Growth 200cr/$15, Agency 1000cr/$50
- Track cost per mission via LLM token count × rate + execution time flat fee

### Polar.sh integration:
- Sell credit bundles as Polar products (already mandated in project rules)
- Webhook: `subscription.created` → provision credits in DB
- UI shows credit balance prominently; alert at <20% remaining

---

## 5. Vietnamese Market Considerations (F&B, Service SMBs)

### Context:
- Target: café owners, restaurant chains, hair salons, local franchises (84Tea profile)
- Pain: want automation but zero coding background; Zalo/Facebook-native users
- Budget: VND 500K–2M/month (~$20–$80 USD); prefer one-time or monthly prepay

### Key UX adaptations:
- **Language**: Full Vietnamese UI mandatory; use familiar terms ("tác vụ" not "mission", "kết quả" not "output")
- **Entry point**: Zalo Mini App or Facebook Messenger bot as onboarding — not web-first
- **Simplicity**: Max 3 fields to start a task: "What do you want?" + "Which store?" + "When?"
- **Trust signals**: Show "AI đã xử lý X tác vụ cho bạn hôm nay" (AI completed X tasks for you today)
- **Mobile-first**: iPhone SE / Android mid-range; dashboard must be responsive, no complex tables

### Competitive gap:
- No Vietnamese-native AI automation dashboard exists for F&B SMBs (2026)
- Chinese players (ByteDance tools) entering VN market — window is 12–18 months
- Local agencies charge VND 5–20M/project one-time; subscription model undercuts this

---

## Summary: Recommended Architecture for AgencyOS Bridge

```
Non-tech user (Zalo/Web)
    ↓
AgencyOS Dashboard (Next.js, Vietnamese UI)
    ↓ REST API (Bearer token)
raas-gateway (Cloudflare Worker) — existing
    ↓ HTTP → File IPC
Tôm Hùm daemon (openclaw-worker)
    ↓ stdin injection
CC CLI (expect brain) → executes /cook missions
```

**3 build phases:**
1. API layer: expose 5 endpoints from raas-gateway → openclaw-worker
2. Dashboard: mission queue + log stream + credit balance (Next.js)
3. Billing: Polar credit bundles + webhook provisioning

---

## Unresolved Questions

1. Zalo Mini App feasibility — requires Zalo OA verification; timeline unknown
2. Multi-tenant isolation: how to separate tasks per agency account in openclaw-worker (currently single-user)
3. Credit cost calibration: actual token cost per mission type needs profiling from live runs
4. Compliance: Vietnamese data residency requirements for storing mission logs (PDPA-equivalent)

---

**Sources:**
- [Railway vs Vercel comparison](https://docs.railway.com/platform/compare-to-vercel)
- [Vercel vs Railway vs Render AI deployment 2026](https://getathenic.com/blog/vercel-vs-railway-vs-render-ai-deployment)
- [Coolify self-hosted alternative](https://northflank.com/blog/render-alternatives)
- [AI Agent Monitoring best practices 2026](https://uptimerobot.com/knowledge-hub/monitoring/ai-agent-monitoring-best-practices-tools-and-metrics/)
- [AI Observability tools buyer guide 2026](https://www.braintrust.dev/articles/best-ai-observability-tools-2026)
- [Claude Code CLI as HTTP API wrapper](https://github.com/xiaoju111a/Claude-Code-warpper)
- [AI Agent Pricing Models](https://www.ema.co/additional-blogs/addition-blogs/ai-agents-pricing-strategies-models-guide)
- [AI Pricing 2025 field report](https://metronome.com/blog/ai-pricing-in-practice-2025-field-report-from-leading-saas-teams)
- [AI Automation Agency Pricing 2025](https://automatenexus.com/blog/ai-automation-agency-pricing-complete-cost-guide-2025)
