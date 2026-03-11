# Email Sequences — Mekong CLI

**Platform:** Resend (free 3K emails/mo) + simple templates | **Updated:** March 2026

---

## Email Infrastructure

| Tool | Purpose | Cost |
|------|---------|------|
| Resend | Transactional + marketing emails | Free (3K/mo) |
| Polar.sh | Billing notifications (built-in) | Included |
| Supabase | Email list storage | Free tier |
| Custom CLI | `mekong /email` to draft sequences | 1 MCU |

---

## Sequence 1: Onboarding (Triggered: Polar.sh signup)

### Email 1 — Welcome (Day 0, immediate)
```
Subject: Welcome to Mekong CLI — your first mission awaits

You now have [200] MCU credits. Here's how to use them:

1. Set your LLM: export LLM_API_KEY=your-key
2. Run your first mission: mekong cook "write a one-page business plan"
3. See what OpenClaw can do

Most-used commands this week:
- mekong plan "launch my SaaS"
- mekong cook "write sales email sequence"
- mekong review (code review)

Questions? Reply to this email — I read every one.
— Founder, Mekong CLI
```

### Email 2 — Day 3: Tips (if no command run yet)
```
Subject: Haven't run your first mission yet?

Here are the 3 easiest first commands:

mekong ask "explain my codebase"
mekong plan "Q2 roadmap for my startup"
mekong cook "write a job description for a senior engineer"

Each costs 1–3 MCU. You have [credits] remaining.

If you're stuck on setup, reply and I'll help directly.
```

### Email 3 — Day 7: Social proof
```
Subject: What other founders are building with Mekong

This week, Mekong CLI users ran:
- 847 missions
- Top command: mekong cook (38%)
- Most time saved: business plan generation (~2 hrs → 3 min)

Your usage: [X missions, Y MCU used]

Tip: Try mekong /weekly-brief for your Monday CEO report.
```

---

## Sequence 2: Upgrade Nudge (Triggered: 80% MCU used)

### Email 1 — 80% used
```
Subject: You've used 160 of your 200 MCU credits

You're getting real value from Mekong CLI.

Upgrade to Pro ($149/mo) for 1,000 MCU — 5× more missions,
priority support, and advanced commands.

[Upgrade to Pro →]

Or top up with 50 extra credits for $12.
```

### Email 2 — Credits exhausted
```
Subject: Your MCU credits ran out — here's how to continue

Your 200 MCU are used up. To keep running missions:

Option 1: Renew Starter — $49 for 200 more MCU
Option 2: Upgrade to Pro — $149 for 1,000 MCU (best value)
Option 3: Buy 50 credits — $12 one-time top-up

[Continue with Mekong →]
```

---

## Sequence 3: Win-Back (Triggered: No login in 14 days)

### Email 1 — Day 14 inactive
```
Subject: Still there? New commands since you last logged in

Since your last mission, we shipped:
- 12 new commands in the Founder layer
- mekong /weekly-brief (CEO Monday report)
- Faster PEV execution (~30% speed improvement)

Run one mission this week — it takes 30 seconds.

mekong cook "write a tweet thread about my product"
```

### Email 2 — Day 30 inactive (final)
```
Subject: Should we pause your subscription?

You haven't run a mission in 30 days. A few possibilities:

1. Setup was confusing → reply and I'll walk you through it
2. You don't need it right now → pause your subscription here
3. You forgot it existed → here's your login link

No hard feelings either way. But if there's something broken,
I want to fix it.
```

---

## Email Metrics Targets

| Metric | Target | Industry Avg |
|--------|--------|-------------|
| Open rate (onboarding) | 50% | 40% |
| Open rate (nudge) | 35% | 25% |
| Click rate (onboarding) | 15% | 8% |
| Unsubscribe rate | < 0.5% | 0.5% |
| Win-back conversion | 15% | 10% |
