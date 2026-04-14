# OpenClaw — ProductHunt Listing Draft

**Status:** Ready to submit
**Date:** 2026-03-23

---

## Name
OpenClaw

## Tagline
`Your AI employee that runs your entire business`
*(57 chars)*

**Alternates (A/B test):**
- `342 AI commands. One platform. Infinite business.` (49 chars)
- `Submit a goal. AI executes it. Ship faster.` (44 chars)

---

## Description (3 paragraphs)

**Paragraph 1 — What**
OpenClaw is an open-source AI-operated business platform with 342+ commands across 6 layers: Studio, Founder, Business, Product, Engineering, and Ops. You submit a business goal — write a sales email, plan a sprint, audit your infrastructure, build a feature — and OpenClaw's PEV engine (Plan → Execute → Verify) handles the execution loop autonomously.

**Paragraph 2 — How**
Built on a universal LLM endpoint (works with Claude, GPT-4, Gemini, Qwen, local Ollama), OpenClaw routes tasks through a layered agent system: planner decomposes goals, executors run shell/LLM/API actions, and verifiers enforce quality gates before delivery. Every command costs 1 MCU (Mission Credit Unit) — deducted only on successful delivery. API lives at api.agencyos.network. Dashboard at agencyos.network.

**Paragraph 3 — Why**
Most AI tools handle one thing: chat, code, or content. OpenClaw handles all six layers of a business in one platform, from fundraising decks to CI/CD deploys. It's open source (MIT), so you can self-host, fork, or extend it. Start free. Scale when it ships.

---

## Topics
- Artificial Intelligence
- Developer Tools
- SaaS
- Productivity
- Open Source

---

## Pricing

| Tier | Credits/mo | Price | Best for |
|------|-----------|-------|----------|
| Free | 50 MCU | $0 | Try it out |
| Starter | 200 MCU | $49/mo | Solo founders |
| Pro | 1,000 MCU | $149/mo | Small teams |
| Enterprise | Unlimited | $499/mo | Agencies & scale |

API: api.agencyos.network
Dashboard: agencyos.network

---

## Maker Comment (First-person, ~200 words)

> Hey PH! I'm the builder behind OpenClaw — and I'll be honest with you.
>
> I got tired of context-switching between 15 AI tools that each do one thing. Cursor for code. ChatGPT for copy. Some other tool for research. Another for planning. It's chaos.
>
> So I built OpenClaw: an AI employee that runs every layer of your business. 342 commands. 6 layers. One universal LLM endpoint — works with Claude, GPT-4, Gemini, Qwen, even local Ollama.
>
> The core idea: you submit a goal, the PEV engine (Plan → Execute → Verify) handles the loop. It decomposes the task, executes it via agents, and verifies quality before delivering. You don't babysit it.
>
> What can it do today?
> - `/cook` → write + ship a feature
> - `/sales` → draft outbound campaigns
> - `/audit` → full infrastructure audit
> - `/fundraise` → pitch deck + cap table
> - `/deploy` → Cloudflare Workers + D1
>
> It's fully open source (MIT). Self-host it, fork it, extend it. Or use the hosted API at api.agencyos.network starting at $49/mo.
>
> Building in public. Would love your feedback — especially on what layer you'd use first.
>
> Ask me anything below.

*(198 words)*

---

## First Comment Reply Templates

### "How is this different from just using ChatGPT?"

> Great question. ChatGPT is a chat interface — you prompt, it responds, you copy-paste. OpenClaw is an execution engine. It has 342 purpose-built commands, a PEV loop that plans + executes + verifies autonomously, and it connects to your shell, APIs, and git. It's the difference between a consultant who talks and one who actually ships.

### "Is it really open source?"

> Yes — MIT license. Full source at github.com/mekong-cli/mekong-cli. You can self-host the entire stack: the CLI, the PEV engine, the agent layer. The hosted API (api.agencyos.network) is optional — it's there if you don't want to manage infra. Fork it, extend it, build on top of it.

### "What's an MCU?"

> MCU = Mission Credit Unit. 1 MCU = 1 completed mission. The key word is *completed* — credits only deduct on successful delivery (verified by the verifier agent). Failed runs don't cost you. Free tier gives you 50 MCU/mo to test it out. Starter is 200 MCU/$49, Pro is 1,000 MCU/$149.

### "What LLMs does it support?"

> Any LLM with an OpenAI-compatible endpoint. Set 3 env vars: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` — and you're pointed at Claude, GPT-4, Gemini, Qwen, DeepSeek, or a local Ollama instance. We test primarily against Claude Sonnet + Opus 4.6.

### "Can I use it for my dev team?"

> Absolutely. The Engineering layer (`/cook`, `/fix`, `/review`, `/deploy`, `/test`) is the most mature. Teams use it to run feature development loops, CI debugging, and infra deploys. Pro plan ($149/mo, 1,000 MCU) fits a 3-5 person dev team comfortably.

---

## Thumbnail Concepts

### Concept 1 — "The Terminal That Runs Your Company"
- Dark terminal background (#0a0a0a)
- Green-on-black ASCII art: `mekong cook "launch my SaaS"`
- Animated typing effect showing PEV loop output
- Bottom-right: OpenClaw claw logo in orange
- Tagline overlay: "342 commands. One AI employee."

### Concept 2 — "6-Layer Business Stack"
- Clean white/light background
- Vertical stack of 6 colored bars (Studio → Founder → Business → Product → Engineering → Ops)
- Each bar shows 2-3 command names in small type
- Center: large OpenClaw logo
- Bold headline: "Your entire business. One platform."

### Concept 3 — "Before / After"
- Split screen layout
- LEFT (chaotic): 15 app logos scattered (Cursor, ChatGPT, Notion, Slack, Figma, Linear...)
- RIGHT (clean): Single OpenClaw terminal, one command
- Dividing line with arrow pointing right
- Caption: "All of this → one command"

---

*Draft v1 — 2026-03-23*
