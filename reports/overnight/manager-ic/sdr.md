# SDR Report — Mekong CLI
*Role: Sales Development Representative | Date: 2026-03-11*

---

## ICP Definition

**Primary ICP: The Productive Developer**
- Title: Senior Engineer, Staff Engineer, Solo Founder/CTO
- Company: 1-10 person startup, indie project, or small agency
- Stack: Python or TypeScript, uses Claude Code or Cursor daily
- Pain: Spends >2hr/day on repetitive scaffolding, deploys, reviews
- Budget: $49-149/mo without approval needed
- Channel: GitHub, HN, r/LocalLLaMA, Twitter/X dev community

**Secondary ICP: The Non-Tech Founder**
- Title: Founder, CEO (non-technical background)
- Pain: Can't code, outsources everything, wants AI to execute tasks
- Entry point: `mekong annual "Business plan 2026"` — zero code required
- Budget: Willing to pay $499/mo if it replaces a VA or consultant

---

## Outreach Templates

### Template 1: GitHub Star → Onboard (automated email)

Subject: Your first `mekong cook` — 2 steps

```
Hey {name},

Thanks for starring Mekong CLI.

Two things to get you running in 2 min:

1. Set your LLM (free with Ollama):
   export OLLAMA_BASE_URL=http://localhost:11434/v1
   ollama pull qwen2.5-coder

2. Run your first cook:
   pip install mekong-cli
   mekong cook "Create a Python REST API with auth"

If you hit any snag, reply here — I read every email.

— Binh, Mekong CLI
```

### Template 2: HN/Reddit Cold Outreach

```
Hey {username}, saw your comment about [repetitive deploy tasks / AI CLI tools].

Built something that might be relevant — Mekong CLI runs a full
Plan→Execute→Verify loop on any goal. Works with Ollama (free) or
any OpenAI-compatible API.

`mekong cook "Fix failing CI tests"` — give it a goal, it handles the rest.

Open source (MIT): github.com/longtho638-jpg/mekong-cli

Curious what you'd try first.
```

### Template 3: Enterprise Outreach (Agency/Team Lead)

Subject: Replace 10 CLI tools with one AI operator

```
{name},

Quick question: how much time does your team spend on
scaffolding, code reviews, and deploy scripts each week?

Mekong CLI covers all of it — 289 commands across engineering,
product, and business ops. One AI operator replaces:
- GitHub Copilot (code generation)
- Manual code reviews
- Deploy scripts
- Sprint planning tools

It's open source and works with any LLM including local Ollama.

Worth a 15-min demo? I can walk through how [Company] could
use it for [specific use case from their stack].
```

---

## Discovery Questions

For qualifying inbound leads:

1. "What does your current workflow look like for [scaffolding / deploys / code review]?"
2. "How many LLM tools are you currently paying for?"
3. "Are you on a team or solo? Who else would use this?"
4. "Have you tried Ollama for local LLM? We support it free."
5. "What's your biggest time sink in a typical dev week?"

Disqualifiers:
- "We don't use Python or Node" → low fit (CLI is Python-based)
- "We have a dedicated DevOps team" → lower urgency, longer cycle
- "We can't use cloud LLMs" → qualify for Ollama path

---

## Outreach Channels & Cadence

| Channel | Sequence | Expected Response Rate |
|---------|----------|----------------------|
| GitHub star email | Day 0, Day 3, Day 7 | 15-25% |
| HN comment reply | Single, contextual | 10-20% |
| Reddit DM | Single, contextual | 5-15% |
| Twitter/X DM | Day 0, Day 5 | 5-10% |
| IndieHackers post reply | Single | 10-20% |

**Rule:** Never more than 2 follow-ups. Developer community = low tolerance for sales spam.

---

## Lead Scoring Model

| Signal | Points |
|--------|--------|
| GitHub star | +5 |
| pip install (tracked via analytics) | +10 |
| Ran `mekong cook` (activation event) | +25 |
| Asked question in GitHub Discussions | +15 |
| Mentioned us on Twitter/X | +20 |
| Opened pricing page | +30 |
| Started Polar.sh checkout (abandoned) | +40 |

Score ≥ 50 → SDR outreach. Score ≥ 80 → AE handoff.

---

## Weekly SDR Targets

| Metric | Weekly Target |
|--------|--------------|
| Outreach sent | 50 |
| Responses received | 8 (16% rate) |
| Demo calls booked | 2 |
| Trials started (free tier) | 5 |
| Qualified leads to AE | 1 |

---

## Tools Needed

- [ ] Email automation: ConvertKit or Loops.so for GitHub star sequence
- [ ] Analytics: PostHog to track pip install → cook → pricing page funnel
- [ ] CRM: Notion database or Airtable for lead tracking (no Salesforce needed yet)
- [ ] Loom: async video demos instead of live calls where possible
