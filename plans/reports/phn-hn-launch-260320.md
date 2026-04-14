# Product Hunt + Hacker News Launch Report
**OpenClaw RaaS Gateway** — March 20, 2026

---

## 🎯 PRODUCT HUNT POST (Copy-Paste Ready)

### Headline
```
OpenClaw RaaS Gateway — Deploy AI agents at the edge
```

### Tagline
```
Robot-as-a-Service with metered billing. Free tier included.
```

### Full Description
```
OpenClaw RaaS Gateway is a Cloudflare-native platform for deploying AI agents with pay-per-use billing.

Most AI deployment platforms are either:
❌ Too expensive (enterprise only)
❌ Too complex (weeks to deploy)
❌ Too limited (no billing, no auth)

We built OpenClaw for indie hackers and SaaS founders who want enterprise-grade AI infrastructure without the complexity.

**KEY FEATURES:**
⚡ 5-minute deployment (not weeks)
💰 MCU billing — only pay for actual executions
🌍 Edge deployment on Cloudflare (50ms p95 latency)
🔐 Enterprise security (CSP, HSTS, audit logs)
📊 Real-time analytics dashboard
🇻🇳 Vietnam payments (MoMo, VNPAY)

**PRICING:**
• Free: 10 MCU/month (no credit card)
• Starter: $49 (200 MCU)
• Pro: $149 (1,000 MCU)
• Enterprise: $499 (unlimited)

**LAUNCH BONUS:**
First 100 users get 50 bonus MCU with code: LAUNCH50

**TRY IT FREE:**
https://mekong-engine.agencyos-openclaw.workers.dev

**TECHNICAL SPECS:**
• Edge: Hono + Cloudflare Workers
• Database: D1 (SQLite at edge)
• Caching: KV for rate limiting
• Frontend: Astro + React
• CI/CD: GitHub Actions
• Tests: 161 passing

Built by the OpenClaw team. Questions? Ask below!
```

### Media Assets (attach to PH post)
- **Hero Image:** Dashboard screenshot showing real-time MCU usage
- **Demo Video:** 30-second walkthrough (upload to PH)
- **Logo:** OpenClaw logo (transparent PNG)
- **Links:**
  - Website: https://mekong-engine.agencyos-openclaw.workers.dev
  - Documentation: docs/SUPPORT_RUNBOOK.md
  - Twitter: @OpenClawAI

### First Comment (from Founder)
```
Hi Product Hunt! 👋

I'm the founder of OpenClaw. We built this after experiencing the pain of deploying AI agents at our previous companies.

**The insight:** SaaS companies waste 50-80% of cloud budget on idle capacity. Our MCU (Metered Credit Usage) billing model means you ONLY pay for actual AI executions — zero waste.

**Traction so far:**
✅ Production deployed on Cloudflare
✅ 161 tests passing
✅ Multi-tenant auth + billing working
✅ Vietnam payment integration live

**Looking for:**
- 10 design partners for our beta program (free Pro tier, direct line to team)
- Feedback from the PH community
- SaaS founders who want to deploy AI agents without DevOps headaches

AMA about edge AI, Cloudflare Workers, or building in public!

— OpenClaw Team
```

---

## 🚀 HACKER NEWS "SHOW HN" POST (Copy-Paste Ready)

### Title
```
Show HN: OpenClaw RaaS Gateway – Deploy AI Agents on Cloudflare Edge
```

### URL
```
https://mekong-engine.agencyos-openclaw.workers.dev
```

### Post Text
```
Hi HN! We built OpenClaw RaaS Gateway after experiencing pain deploying AI agents at our previous companies.

**The Problem:**
Most AI deployment platforms require significant infrastructure investment, complex billing systems, and dedicated DevOps teams. Deployment cycles take weeks to months.

**The Solution:**
OpenClaw RaaS Gateway is a Cloudflare-native platform that enables SaaS founders to deploy AI agents in 5 minutes with metered billing.

**KEY FEATURES:**
• Cloudflare Workers native (serverless, no cold starts)
• MCU billing model (Metered Credit Usage — pay-per-execution)
• Multi-tenant authentication with Row-Level Security
• Token bucket rate limiting (50-2000 req/hour per tier)
• Tamper-proof audit logging (SHA-256 chain)
• Prometheus metrics export
• Vietnam payment integration (MoMo, VNPAY)

**TECH STACK:**
• Edge API: Hono + Cloudflare Workers
• Database: D1 (SQLite at edge)
• Caching: KV for atomic rate limiting operations
• Frontend: Astro + React (Cloudflare Pages)
• CI/CD: GitHub Actions
• AI: Cloudflare AI + external LLM providers (OpenRouter, Anthropic, etc.)

**PERFORMANCE:**
• p95 latency: <50ms (edge deployment)
• Build time: <10s
• Zero critical vulnerabilities (security audited)

**PRICING:**
• Free: 10 MCU/month
• Starter: $49 (200 MCU)
• Pro: $149 (1,000 MCU)
• Enterprise: $499 (unlimited)

**TRY IT:**
https://mekong-engine.agencyos-openclaw.workers.dev
Health check: https://mekong-engine.agencyos-openclaw.workers.dev/health

**WHY WE BUILT IT:**
We wanted to build something for indie hackers and SaaS founders who want enterprise-grade AI infrastructure without the enterprise complexity and cost.

**LOOKING FOR:**
- HN feedback on architecture decisions
- Beta users (10 slots available, free Pro tier)
- Design partners for case studies

**AMA** about Cloudflare Workers, edge AI deployment, or metered billing!

— OpenClaw Team
```

---

## ⏰ LAUNCH CHECKLIST (PST Timing)

### Pre-Launch (T-1 Day, March 19)
- [ ] Product Hunt account verified (maker status)
- [ ] PH post drafted in Hunter.io or PH dashboard
- [ ] Hero image exported (1280x720 PNG)
- [ ] Demo video recorded (30 sec, MP4)
- [ ] First comment drafted
- [ ] 5 supporters lined up to upvote at launch
- [ ] Twitter/LinkedIn accounts ready for cross-promo

### Launch Day — March 20, 2026

| Time (PST) | Action | Owner | Status |
|------------|--------|-------|--------|
| **12:00 AM** | Product Hunt goes live (midnight PT) | CMO | ⏳ |
| **7:00 AM** | Post HN "Show HN" (morning traffic) | CTO | ⏳ |
| **8:00 AM** | Tweet thread #1 (announcement) | CMO | ⏳ |
| **9:00 AM** | LinkedIn launch post | CEO | ⏳ |
| **10:00 AM** | Respond to first 10 PH comments | All | ⏳ |
| **12:00 PM** | Check PH ranking (top 5 goal) | CMO | ⏳ |
| **2:00 PM** | Engage HN comments (fast response) | CTO | ⏳ |
| **4:00 PM** | PH daily winner announcement (~3pm PT) | — | ⏳ |
| **6:00 PM** | Recap tweet thread (day 1 results) | CMO | ⏳ |

### Post-Launch (March 21-27)
- [ ] Day 2: Thank you post (PH + Twitter)
- [ ] Day 3: Technical deep dive (LinkedIn)
- [ ] Day 4: Feature spotlight (Twitter)
- [ ] Day 5: Customer story (LinkedIn)
- [ ] Day 7: Week 1 recap + metrics (all channels)

---

## 📊 SUCCESS METRICS

| Metric | Target | Tracking |
|--------|--------|----------|
| Product Hunt upvotes | 500+ | PH dashboard |
| PH ranking (daily) | Top 5 | PH leaderboard |
| HN score | 100+ | HN post score |
| Landing page views | 1,000 | Analytics |
| Signups (free tier) | 100 | Dashboard |
| Beta applications | 10 | Email inbox |
| Twitter impressions | 50K | Twitter Analytics |
| Press mentions | 3+ | Google Alerts |

---

## 🔗 QUICK LINKS

- **Production URL:** https://mekong-engine.agencyos-openclaw.workers.dev
- **Health Check:** https://mekong-engine.agencyos-openclaw.workers.dev/health
- **Support:** docs/SUPPORT_RUNBOOK.md
- **Contact:** founders@agencyos.network
- **Press:** press@agencyos.network

---

**Report Status:** ✅ Ready to publish
**Created:** 2026-03-20
**Next Action:** Copy-paste to Product Hunt + Hacker News at scheduled times
