---
description: ⚡⚡⚡⚡ CMO Launch Playbook — Product Hunt, Hacker News, social media launch orchestration
argument-hint: [phase: pre-launch|launch|post-launch] [platform: ph|hn|social|all]
---

**Ultrathink parallel** CMO launch playbook: <args>$ARGUMENTS</args>

**CWD:** `apps/algo-trader` | **REF:** `docs/cmo-sops.md` SOP-M04

---

## LAUNCH TIMELINE

### PRE-LAUNCH (2 weeks before)

**Week -2: Assets**
- [ ] README polish: hero GIF/screenshot, badges, quickstart
- [ ] Landing page live (if applicable)
- [ ] Demo video (2 min Loom/YouTube)
- [ ] Twitter thread drafted (10-15 posts)
- [ ] Discord server seeded (20+ active members)
- [ ] Email waitlist (50+ signups)
- [ ] PH/HN post drafted and reviewed

**Week -1: Community**
- [ ] Ping early testers for feedback
- [ ] Collect testimonials/quotes
- [ ] Schedule social posts
- [ ] Brief supporters on launch day plan
- [ ] Test all links, install flow, onboarding

### LAUNCH DAY

```
Timeline (PST):
00:01  → Post Product Hunt (midnight PST)
06:00  → Post HN: "Show HN: CLI-first autonomous crypto trading"
06:30  → Tweet thread (10 posts, 2 min spacing)
07:00  → Reddit r/algotrading + r/cryptocurrency + r/programming
07:30  → Dev.to / Hashnode cross-post
08:00  → Email waitlist blast
08:00+ → Monitor ALL channels, respond to EVERY comment
12:00  → Midday metrics check + 2nd social push
18:00  → Evening update tweet + thank supporters
```

**Launch Messaging:**
```
Headline: "Algo-Trader: CLI-first autonomous crypto trading with 4-tier safety"
Subhead:  "1216 tests. 10-layer stealth. Circuit breakers you can't disable."
CTA:      "Star on GitHub → Install → Run your first backtest in 60 seconds"
```

### POST-LAUNCH (1 week after)

- [ ] Respond ALL remaining comments (48h max)
- [ ] Fix reported issues within 24h
- [ ] Post day-1 metrics (stars, installs, users)
- [ ] Post day-7 retrospective
- [ ] Thank + onboard new users via Discord
- [ ] Write "Lessons from launching" blog post

---

## PLATFORM PLAYBOOKS

### Product Hunt
```
Title: "Algo-Trader — CLI-first autonomous crypto trading"
Tagline: "Trade smarter with AI signals, stealth execution, and safety you can't disable"
Topics: Developer Tools, Crypto, Trading, Open Source
Maker comment: Technical deep-dive on architecture
```

### Hacker News
```
Title: "Show HN: Algo-Trader – CLI crypto trading with 4-tier autonomy and stealth arb"
Body: Technical focus, architecture decisions, test count, safety philosophy
```

### Twitter/X Thread
```
1. Hook: "I built a CLI trading bot that trades crypto autonomously..."
2. Problem: Closed-source bots, fragile scripts
3. Solution: 4-tier autonomy, CLI-first
4. Safety: Circuit breakers, 1216 tests
5. Stealth: 10-layer phantom cloaking
6. Demo: GIF/video
7. Architecture: diagram
8. Results: backtest data
9. Open source: GitHub link
10. CTA: star + install
```

---

## METRICS TO TRACK

| Metric | Hour 1 | Day 1 | Day 7 | Target |
|--------|--------|-------|-------|--------|
| PH upvotes | | | | Top 5 |
| HN points | | | | 100+ |
| GitHub stars | | | | 200+ |
| Installs | | | | 50+ |
| Discord joins | | | | 30+ |
| Twitter impressions | | | | 10K+ |

## USAGE
```bash
/trading:cmo:launch pre-launch       # Prep checklist
/trading:cmo:launch launch all       # Execute launch day
/trading:cmo:launch post-launch      # Post-launch follow-up
```
