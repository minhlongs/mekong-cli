# OpenClaw/AgencyOS Launch Content Drafts

---

## 1. Show HN Submission

### Title
**AgencyOS: Open Source AI Platform That Runs Your Business**

### Body

We built AgencyOS because running a startup is repetitive: fundraising decks, financial models, product roadmaps, API deployments, security audits — all decomposable into discrete tasks an AI can handle.

**The Problem:** Founders waste 70% of time on operational busywork. Hiring for every role is expensive. Most "AI" tools are narrow (writing, coding, design).

**Our Solution:** AgencyOS is a unified command line that describes a business goal → AI plans → executes → verifies → delivers.

```bash
$ mekong founder:raise "Series A for AI platform"
$ mekong cook "Deploy production API with auth"
$ mekong annual "2026 business plan"
```

342 commands across 6 business layers (Founder, Business, Product, Engineering, Ops, Studio). Behind each: a DAG orchestrator planning parallel subtasks, executing them, catching failures, and auto-healing.

**How it works:** Universal LLM routing (3 environment vars, any provider — OpenRouter, Qwen, DeepSeek, local Ollama). Python CLI reads 542 skills + 410 JSON contracts. Built on Cloudflare Workers (zero infra cost).

**Free tier:** 50 MCU/month. Paid: $49 (200 MCU), $149 (1K MCU), $499 unlimited.

Open source (github.com/longtho638-jpg/mekong-cli, MIT license). Dashboard: app.agencyos.network.

We're a solo founder. This is dogfood — we run our company with it.

**What we're asking:** Try the free tier. Report issues/feature requests on GitHub. Star if useful. Feedback on parity with what a real founder/exec needs.

---

## 2. ProductHunt Maker Comment

**Username/Handle:** [Your PH Maker Name]

I built this because I couldn't hire fast enough.

Last year, I tried to run a startup solo. I'd spend Tuesday writing a 20-page fundraising memo, Wednesday on financial models, Thursday building features, Friday firefighting ops. The manual grind was killing velocity.

**Why AgencyOS exists:** I realized 80% of what I did was transferable to a choreographed LLM. So I built orchestration around it — planning tasks like a project manager, executing them in parallel (DAG scheduling), catching failures, and auto-healing when things break.

That became the PEV Engine (Plan→Execute→Verify). Wrap 342 business commands around it, and suddenly one person can do the work of a lean team.

**What it does:** You describe a goal (`mekong cook "Deploy an API"`) and the system decomposes it, plans dependencies, executes steps in parallel, verifies output quality, and rolls back on failure. Works across all 6 business functions — fundraising, hiring, product planning, engineering, ops, VC studio operations.

**Why it's different:** Most "AI for business" tools are narrow (writing, design, coding). We handle **the orchestration problem** — coordinating multiple specialists (LLM + shell + Git + tests) and surfacing confidence to you. Think of it as "hiring a CTO who coordinates everyone else."

**Free forever:** 50 MCU (credits) per month. $49 gets you 200. No aggressive upsell. Open source. Run locally if you want (Ollama support).

We've been dogfooding it for 6 months. It's raw but real — not a demo.

Looking for feedback: What would *you* delegate to an AI assistant if it actually worked?

---

## 3. Tagline Options

1. **"Hire an AI CTO to run your startup."** (48 chars)
   - Direct benefit, emotional hook, concise

2. **"Open Source Platform for Solo Founders"** (42 chars)
   - Market positioning, honesty about audience

3. **"Plan → Execute → Verify. Automate Your Ops."** (47 chars)
   - Technical credibility, shows the loop

4. **"AI + Orchestration = Your Business Ops Team"** (47 chars)
   - Problem solved, emphasizes coordination

5. **"From Founder Idea to Deployed Product in Minutes"** (52 chars)
   - Outcome-focused, competitive positioning

---

## Content Strategy Notes

### Tone Alignment
- **Honest:** Admit it's raw, not perfect, built by a solo founder
- **Technical:** Show the architecture (PEV loop, DAG scheduling, LLM routing)
- **Practical:** Real commands, real use cases, not hype
- **Humble:** "We're dogfooding it" = credibility > marketing speak

### Key Messages to Hammer
1. **Orchestration, not just automation** — Many AI tools code/write. We *coordinate* specialists.
2. **Free tier is real** — 50 MCU/month, no trick to charge later (we have paid tiers, but free is usable).
3. **Open source + hackable** — 342 commands, 542 skills, 410 contracts. Modify anything.
4. **Proven by usage** — Solo founder running company on it daily.
5. **Zero-cost infra** — Cloudflare means marginal cost per user is near zero.

### What Resonates with HN/PH Audience
- Technical depth (PEV engine, DAG scheduling)
- Founder authenticity (solo builder, not VC-backed hype)
- Pragmatism (free tier, honest about limitations)
- Openness (MIT license, GitHub first, no dark patterns)

### Potential Objections (Preempt)
- "Isn't this just LLM wrappers?" → No. The coordination layer is the hard part.
- "Will it replace developers?" → No. It augments operators and solo founders.
- "Is the free tier limited?" → 50 MCU/mo is real work. Paid is for scale/concurrency.
- "Why open source?" → Lower barrier, attracts contributors, trust signal.

---

## Follow-up Content (Not in Scope, But Keep Ideas)
- Comparison matrix: AgencyOS vs. Make.com vs. Zapier vs. hiring interns
- Video: 2min demo of `mekong founder:raise` in action
- Blog: "Why I Built an AI CTO Instead of Hiring One"
- Benchmarks: Speed (15 min to financial model), cost ($1.23 LLM, $0 infra vs. $200 consultant hour)
