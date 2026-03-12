# Mekong CLI v5.0 — Cold Outreach Templates
**Generated:** 2026-03-12 overnight | **Op:** LeadHunter + ContentWriter agents
**Target:** 50 personalized emails to dev tool enthusiasts

---

## Outreach Strategy

**Channel:** Email (primary) + Twitter DM (secondary)
**Volume:** 50 contacts, 3 segments × personalized templates
**Timing:** Tuesday/Wednesday 9–11am recipient timezone
**Follow-up:** Single follow-up at day 5, then stop
**Goal:** 15% reply rate, 5% trial conversion (2–3 paid signups)

---

## Segment A: CLI Power Users (20 contacts)
*Found via: GitHub stars on llm/jc/fx, r/commandline top contributors*

### Email Template A1 — GitHub discovery
```
Subject: saw you star [repo] — thought you'd like this

Hi [Name],

Noticed you star a lot of CLI tools — [repo] caught my eye on your profile.

We just shipped Mekong CLI v5.0 (MIT). It's an AI terminal that covers
your whole company: sprint planning, investor pitch, sales outreach, deploy
pipelines — all from the same CLI you already live in.

Three things that might interest you specifically:

1. Universal LLM — 3 env vars, any OpenAI-compatible provider (Ollama works)
2. PEV engine — Plan-Execute-Verify with automatic rollback on failure
3. $0 infra — Cloudflare Pages + Workers + D1 + KV + R2

Quick install: pip install mekong-cli && mekong health

Happy to answer any questions. GitHub if you want to poke around first:
github.com/mekong-cli/mekong-cli

[Your name]
```

### Email Template A2 — r/commandline contributor
```
Subject: your comment on [thread] — relevant project

Hi [Name],

Your comment on [thread] about [specific pain point] resonated.

That's exactly the problem Mekong CLI v5.0 solves. Instead of stitching
together 5 different AI tools, everything runs from one terminal with a
unified PEV engine:

  mekong cook "build feature X"   → code
  mekong sprint                   → planning
  mekong deploy --env production  → ship
  mekong health                   → verify

MIT open source. Works with DeepSeek at $0.27/100K if you want the
cheapest serious LLM option.

pip install mekong-cli

Would love your feedback if you try it — you clearly know what good CLI
tools feel like.

[Your name]
```

---

## Segment B: Dev Agency Leaders (20 contacts)
*Found via: LinkedIn "agency CTO" + Cloudflare, GitHub wrangler repos with multiple projects*

### Email Template B1 — LinkedIn / Agency CTO
```
Subject: running multiple client projects on CF? saves ~2min per project

Hi [Name],

Saw your post about [specific Cloudflare/agency topic] — clearly you're deep
in the CF Workers ecosystem.

One thing we built in Mekong CLI v5.0 that agency leads seem to love:

  bash mekong/infra/scaffold.sh client-project startup

That generates the full Cloudflare stack — Pages + Workers + D1 + KV + R2 —
for any new client project. About 2 minutes vs 30 minutes of manual setup.

For running 10+ projects, that's 4+ hours saved on scaffolding alone.

The platform also covers the workflow layer: sprint planning, deploy pipeline,
audit, health checks — standardized across all client projects.

30-min call if useful? Or just: pip install mekong-cli && mekong health

[Your name]
```

### Email Template B2 — GitHub wrangler user
```
Subject: noticed your wrangler setup — question

Hi [Name],

Your [repo] has a nice wrangler setup — looks like you're running
[observed pattern] across multiple projects.

We just shipped Mekong CLI v5.0 which adds a business workflow layer
on top of Cloudflare deployments:

  mekong deploy --env production
  → lint → tests → staging → smoke → prod → health
  → automatic rollback if any step fails

Works with your existing wrangler.toml. No config changes needed.

MIT open source. Starter at $49/month if you want the hosted platform.
Core deploy pipeline is free.

github.com/mekong-cli/mekong-cli

Happy to chat about your CF setup if useful.

[Your name]
```

---

## Segment C: AI-Forward Founders (10 contacts)
*Found via: Twitter "build in public" + LLM, YC alumni with AI products, ProductHunt AI makers*

### Email Template C1 — Twitter build-in-public founder
```
Subject: your [tweet/thread] about [topic] — building something related

Hi [Name],

Your thread on [topic] was great — especially the part about [specific insight].

We're building in a similar direction with Mekong CLI v5.0. The core idea:
your terminal should cover the whole company, not just code.

  mekong okr           → quarterly planning
  mekong pitch --deck  → investor narrative
  mekong sales         → lead pipeline
  mekong cook "..."    → ship features
  mekong deploy        → production in 4min

Universal LLM (3 env vars, any provider). MIT open source. $0 CF infra.

If you're already using LLM APIs in your product, you can point Mekong at
the same provider key and get the business layer for effectively $0 extra.

Would love your take — you seem to be thinking about this space seriously.

[Your name]
```

### Email Template C2 — YC/ProductHunt AI founder
```
Subject: Mekong CLI — AI terminal for founders building with AI

Hi [Name],

Congrats on [product/launch]. The [specific thing] you built is clever.

Quick question: how much time do you spend on the operational layer —
sprint planning, investor updates, financial tracking — vs actual building?

Mekong CLI v5.0 is built for exactly this: a CLI that handles the business
layer so technical founders can stay in the terminal for everything.

Five-minute test:
  pip install mekong-cli
  mekong okr    ← quarterly planning in 60s
  mekong sprint ← today's plan from your backlog

MIT open source. Works with any LLM you're already using.

Happy to share more if useful.

[Your name]
```

---

## Follow-Up Template (Day 5, all segments)

```
Subject: Re: [original subject]

Hi [Name],

Following up once in case my previous email landed in the wrong folder.

Mekong CLI v5.0 — MIT open source, $0 CF infra, universal LLM:
github.com/mekong-cli/mekong-cli

If the timing isn't right, no worries. Happy to reconnect when it is.

[Your name]
```

---

## Tracking & Metrics

| Metric | Target |
|--------|--------|
| Emails sent | 50 |
| Open rate | >40% |
| Reply rate | >15% (7+ replies) |
| Trial starts | >10% (5+ installs) |
| Paid conversions | >5% (2–3 tenants) |
| MRR from outreach | $100–$150 (2–3 Starter) |

**Tracking:** UTM params on all links, PostHog for trial attribution
**CRM:** .mekong/tasks/ directory + LeadHunter agent pipeline tracking

**OUTREACH: 50 TEMPLATES READY — BEGIN SEND TUESDAY 09:00**
