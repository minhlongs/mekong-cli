# Growth Strategy & Go-To-Market — Mekong CLI

**Date:** March 2026
**Covers:** grow, growth-experiment, growth-channel-optimize, launch, founder-launch

---

## Growth Philosophy

Mekong CLI is a developer tool with a founder layer. Growth follows the classic OSS playbook:
**Awareness (GitHub/HN) → Activation (install + first cook) → Retention (weekly usage) → Revenue (paid tier) → Referral (community agents)**

The moat is not marketing spend — it is the 289-command depth that makes Mekong irreplaceable once integrated into a workflow.

---

## Acquisition Channels

### Channel 1: GitHub / Open Source (Primary)

**Why:** Developer tools live and die on GitHub stars. Stars → installs → paid conversions.

Tactics:
- Publish compelling README with animated terminal GIF (cook demo)
- Tag all releases properly — GitHub trending page exposure
- "Awesome AI CLI" list submissions
- GitHub Discussions as community hub
- Dependabot-friendly — appear in project dependency graphs

**Target:** 5,000 stars by Dec 2026
**CAC:** ~$0 (founder time only)
**Conversion rate:** GitHub star → trial install ~15%, trial → paid ~2%

### Channel 2: Hacker News (High-Value, One-Shot)

**"Show HN: Mekong CLI — I built 289 AI commands that cover every business layer"**

Timing: Tuesday–Thursday, 9–11am EST for maximum visibility.

Pre-launch prep:
- 5 detailed comment responses written in advance (address "why not just use ChatGPT?")
- Demo video linked in post (shows PEV engine, rollback, multi-provider)
- Metrics ready: commands count, gross margin, breakeven point
- Founder available for 6 hours of comment engagement

**Target:** >200 points, front page for 6+ hours
**Expected installs:** 2,000–5,000 in 48 hours
**CAC:** ~$0

### Channel 3: ProductHunt (Mass Awareness)

**Launch date:** April 2026 (Q2 OKR milestone)

Pre-launch checklist:
- [ ] Hunter recruited (well-known dev tools figure)
- [ ] 50+ upvotes secured from warm network day-of
- [ ] Launch assets: thumbnail, gallery (5 screenshots), demo video
- [ ] "First 100 users get 3 months Pro free" incentive
- [ ] Maker comment thread pre-written

**Target:** Top 5 Product of the Day, Dev Tools category
**Expected trials:** 500–1,500
**CAC:** ~$5 (PH prep time amortized)

### Channel 4: Vietnamese Developer Community (Home Market)

Communities:
- **Viblo.asia** — publish 4 technical deep-dives (PEV engine, RaaS billing, etc.)
- **TopDev.vn** — job board + tech blog, sponsored post ($50)
- **Facebook groups:** Vietnam Developers (180K members), Vietnam Startup Network
- **HCMC/Hanoi tech meetups** — live demo presentations

Content strategy: Vietnamese-language tutorials, real use cases by VN founders.
**Target:** 300 active VN users by Jun 2026
**CAC:** ~$10

### Channel 5: Content Marketing (Compounding)

Blog topics (publish 2/month):
1. "I replaced 7 SaaS tools with 289 CLI commands"
2. "How the PEV engine auto-rolled back my broken deploy at 2am"
3. "mekong annual: I asked AI to plan my entire year. Here's the output."
4. "Why I built Mekong CLI on Cloudflare Workers ($0 hosting at any scale)"
5. "OSS vs. proprietary AI tools: the unit economics breakdown"
6. "From 0 to $10K MRR with one CLI tool and no marketing budget"

**Distribution:** Dev.to, Hashnode, Medium (Towards Data Science), personal blog
**Target:** 1,000 organic visits/month by Q3 2026
**CAC:** ~$20 per converted customer

### Channel 6: YouTube / Video (Q3 Launch)

Series: **"AI Operates My Business"**
- Episode 1: Full day running a startup with only Mekong CLI
- Episode 2: mekong cook builds a SaaS from scratch (real-time)
- Episode 3: mekong fundraise — AI writes my seed pitch deck
- Episode 4: PEV engine explained with visualizations

**Target:** 1,000 subscribers, 4 videos by Q3 2026

---

## Growth Experiments Backlog

| # | Experiment | Hypothesis | Metric | Status |
|---|------------|------------|--------|--------|
| G1 | Free tier (100 MCU, no CC) | Lowers barrier → more signups | Trial → paid 30d rate | Planned Q2 |
| G2 | $29 "indie" Starter tier | Lower price → volume increase | MRR delta vs. conversion lift | Planned Q2 |
| G3 | "Cook a project" viral mechanic | Users share cook output → referrals | Referral rate | Planned Q3 |
| G4 | VS Code extension | Expands to non-CLI users | New installs from extension | Planned Q2 |
| G5 | MCP integration (Claude Code) | Appears in Claude's skill library | Organic installs via MCP | Planned Q3 |
| G6 | Agent marketplace open PRs | Community contributions → SEO | PRs merged / month | Planned Q2 |
| G7 | "Powered by Mekong" badge | Backlinks + awareness | Referral traffic | Ongoing |
| G8 | Affiliate: $20/referral for Starter | Dev influencers promote | Affiliate MRR % | Planned Q3 |

---

## Activation Optimization

Current funnel:
```
Install → First cook → Second cook → Paid conversion
```

Known friction points:
1. **pip install** — Python env issues on Mac (pyenv conflicts)
2. **LLM key setup** — 3 env vars is easy but unfamiliar for non-devs
3. **First cook failure** — if task is too complex, user gives up

Activation fixes:
- `mekong onboard` command — guided setup wizard
- Pre-configured `.env.example` with DeepSeek (cheapest, easy signup)
- "Quick wins" command list in README — tasks that succeed in <30 seconds
- Error messages that suggest fixes (not just stack traces)

**Target:** Time-to-first-value < 5 minutes

---

## Retention Strategy

Weekly active users are the leading indicator of paid conversion.

Retention levers:
- **`mekong daily`** — daily briefing command (habit formation)
- **`mekong standup`** — replaces daily standups (team workflow integration)
- **Webhook alerts** — Mekong notifies on completed tasks (Slack/Discord)
- **Usage analytics** — show users their MCU consumption and ROI in dashboard
- **Changelog emails** — weekly "new commands added" digest

**Target:** 30-day retention of trial users > 40%

---

## Channel Optimization Matrix (Q2 Review)

| Channel | Cost | Volume | Quality | Priority |
|---------|------|--------|---------|----------|
| GitHub organic | Low | High | High | P1 |
| Hacker News | Low | Very High | Very High | P1 |
| Vietnamese community | Low | Medium | High | P1 |
| ProductHunt | Low | High | Medium | P2 |
| Content blog | Medium | Low | High | P2 |
| YouTube | Medium | Medium | High | P3 |
| Paid ads | High | High | Low-Medium | P4 (post-raise) |

---

## Launch Sequence Calendar 2026

| Date | Launch Event | Expected Reach |
|------|-------------|----------------|
| Feb 2026 | Blog post "289 commands" on Dev.to | 5,000 reads |
| Mar 2026 | GitHub README overhaul + GIF demo | +500 stars |
| Apr W2 | ProductHunt launch | 1,500 installs |
| Apr W3 | Hacker News Show HN | 3,000 installs |
| May 2026 | VS Code extension beta | +2,000 installs |
| Jun 2026 | Vietnamese community campaign | +300 active users |
| Aug 2026 | YouTube channel launch | 500 subscribers |
| Sep 2026 | PyConVietnam presentation | 200 qualified leads |
| Oct 2026 | Seed round announcement | Press + awareness |

---

## Founder-Led Launch Playbook

The founder is the #1 growth asset pre-PMF. Personal credibility drives OSS adoption.

**Founder content commitments:**
- 3 tweets/week about building Mekong CLI in public
- 1 detailed blog post/month (build-in-public narrative)
- Respond to every GitHub issue within 24h (first 100 issues)
- Comment on every HN / Reddit thread mentioning AI CLI tools
- Attend 2 Vietnamese tech meetups per quarter

**"Build in public" metrics to share:**
- Weekly MRR updates
- Command usage stats ("most-used command this week: mekong cook")
- Funny/interesting things Tôm Hùm did autonomously
- Honest failures (rollback events, failed experiments)

**Why this works:** Developers trust builders who show their work. Transparency is distribution.
