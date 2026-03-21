# ProductHunt Launch Kit — Mekong CLI

## Taglines (pick one)

- **A:** Run your entire company from 319 CLI commands
- **B:** Your AI CTO — open source, any LLM, $0 infra
- **C:** 542 AI skills that actually run your business

**Recommended:** Option A — specific, curiosity-driven, measurable.

---

## PH Listing Description (260 chars)

Mekong CLI is an open-source AI business platform. 319 commands across 5 layers (Founder to Ops). Works with Claude, GPT, Gemini, Qwen, or Ollama. Deploy on Cloudflare for $0. Your AI CTO that plans, executes, verifies, and ships.

---

## Maker Comment (~300 words)

Hey PH! I'm the solo builder behind Mekong CLI.

Quick backstory: I was running a small agency in Vietnam, juggling 4 client projects, doing sales calls in the morning and debugging code at night. Classic founder burnout.

Then I thought — what if I could teach an AI to actually run the business operations, not just chat about them?

That became Mekong CLI. It's not another AI wrapper or chatbot. It's a full operating system for businesses, packaged as a CLI with 319 commands across 5 layers:

- Founder: OKRs, fundraising, SWOT analysis
- Business: Sales outreach, marketing campaigns, financial modeling
- Product: Sprint planning, roadmaps, brainstorming
- Engineering: Code, test, deploy, review (the PEV loop)
- Ops: Security audits, health checks, monitoring

The core is OpenClaw Engine — our mission orchestration SDK with circuit breakers, AGI scoring, and self-healing. Every command costs "credits" (Robot-as-a-Service model).

What makes it different:
1. It works with ANY LLM — Claude, GPT, Gemini, Qwen, even local Ollama
2. Infrastructure costs $0 — everything runs on Cloudflare Workers
3. It's fully open source (MIT) — fork it, extend it, sell it
4. It actually executes — not just plans, but runs shell commands, writes code, deploys

We're pre-revenue but the architecture is production-ready: 1,028+ tests passing, 20 gateway waves deployed, 4 npm packages published.

Pricing: Starter $49/mo, Pro $149/mo, Enterprise $499/mo.

Would love your feedback. What commands would you want an AI CTO to have?

---

## First Comment (post immediately after launch)

For the technical folks — here's what's under the hood:

- TypeScript monorepo with 40+ packages
- Cloudflare Workers (Hono framework) for the API gateway
- D1 + KV + R2 for storage (zero traditional servers)
- OpenClaw Engine SDK with circuit breaker patterns
- PEV Loop: Plan → Execute → Verify (autonomous mission cycle)

GitHub: github.com/mekong-cli/mekong-cli
Docs: mekong-raas.pages.dev

Ask me anything about the architecture!

---

## Twitter/X Thread (5 tweets)

**Tweet 1:**
I just launched Mekong CLI on @ProductHunt.

319 commands. 542 AI skills. One CLI to run your entire company.

Open source. Works with any LLM. $0 infrastructure.

[link]

**Tweet 2:**
Most "AI tools" are glorified chat wrappers.

Mekong CLI actually executes:
- Writes and deploys code
- Runs sales outreach campaigns
- Generates financial reports
- Plans sprints and roadmaps

All from your terminal.

**Tweet 3:**
The secret sauce: OpenClaw Engine.

It's a mission orchestration SDK with:
- Circuit breakers (auto-recovery)
- AGI scoring (track your AI's reliability)
- PEV Loop (Plan → Execute → Verify)
- Self-healing (fixes its own failures)

**Tweet 4:**
Why open source?

Because AI business tools shouldn't be black boxes.

Fork it. Add your own commands. Sell your recipes on our marketplace. Keep 70% of revenue.

MIT license. No strings attached.

**Tweet 5:**
Pricing is dead simple:
- Starter: $49/mo (200 credits)
- Pro: $149/mo (1,000 credits)
- Enterprise: $499/mo (unlimited)

1 command = 1-5 credits depending on complexity.

Try it: [link]

---

## LinkedIn Post

I spent 6 months building an AI that runs businesses. Not advises. Runs.

Mekong CLI is an open-source platform with 319 commands across every business function — from fundraising to deployment, from sales outreach to security audits.

Today we launched on ProductHunt.

What I learned building it:
1. AI agents need structure, not freedom. The PEV loop (Plan, Execute, Verify) prevents hallucination disasters.
2. Universal LLM support matters. Not everyone can afford Claude Opus. Ollama on a M1 Mac works fine for 80% of tasks.
3. $0 infrastructure is possible. Cloudflare Workers + D1 + KV handles everything.

This is Robot-as-a-Service (RaaS) — you pay per mission, the AI does the work.

Link in comments. Would love feedback from agency owners and startup founders.

---

## Launch Day Schedule

| Time | Action |
|------|--------|
| T-12h | Final check: screenshots, GIFs, description ready |
| T-1h | Post preview to close friends for early comments |
| T-0 | Launch! Post maker comment immediately |
| T+5m | Post first comment (technical details) |
| T+15m | Tweet thread |
| T+30m | LinkedIn post |
| T+1h | DM 20 supporters asking for upvotes |
| T+2h | Reply to every comment on PH |
| T+4h | Share in relevant Discord/Slack communities |
| T+8h | Post update with traction numbers |
| T+12h | Thank everyone, share milestones |
| T+24h | Publish "lessons learned" tweet |

---

## Upvote Strategy (Ethical Only)

1. **Personal network:** DM 50 friends/colleagues with direct PH link
2. **Community:** Post in IndieHackers, HackerNews, r/SideProject, r/startups
3. **Developer communities:** CLI-focused Discords, TypeScript communities
4. **Vietnamese tech community:** Share in local dev groups (5,000+ devs)
5. **Open source channels:** GitHub discussions, npm weekly newsletter submission
6. **Target:** 200+ upvotes on Day 1

**DO NOT:** Buy votes, use bots, or mass-DM strangers.

---

## Visual Assets Checklist

- [ ] Hero screenshot: terminal with mekong CLI running
- [ ] GIF: live demo of `/cook` command building a feature
- [ ] Architecture diagram: Hub-and-Spoke (Engine + CLI + Gateway)
- [ ] Pricing table screenshot
- [ ] Dashboard screenshot (raas-dashboard)
- [ ] Before/After: manual workflow vs. mekong CLI
- [ ] Logo in PH-required sizes (240x240, 1270x760)
- [ ] Social share image (1200x630)

---

## FAQ — Top 10 Anticipated Questions

**Q: Is this just another AI wrapper?**
A: No. Mekong CLI executes real shell commands, writes actual code, and deploys to production. It's an operating system, not a chatbot.

**Q: How much does it cost?**
A: Starter $49/mo (200 credits), Pro $149/mo (1,000 credits), Enterprise $499/mo (unlimited). Free tier coming soon.

**Q: Which LLMs does it support?**
A: All major ones — Claude, GPT-4, Gemini, Qwen, DeepSeek, and local Ollama models.

**Q: Is it actually open source?**
A: Yes, MIT license. The CLI and engine are fully open. The gateway API is our hosted service.

**Q: Can I self-host?**
A: The CLI runs locally. For the full RaaS experience, you need the gateway (Cloudflare Workers), which we host.

**Q: Is it safe to let AI run shell commands?**
A: Yes — PEV loop (Plan, Execute, Verify) includes safety guards, circuit breakers, and rollback. You approve before execution.

**Q: What's the difference from Cursor/Copilot?**
A: Cursor helps you write code. Mekong CLI runs your business — sales, marketing, finance, HR, not just engineering.

**Q: Can I add my own commands?**
A: Yes! Create recipes (custom commands) and sell them on our marketplace. Keep 70%.

**Q: Does it work on Windows?**
A: macOS and Linux are primary. Windows via WSL2.

**Q: How do credits work?**
A: 1 command = 1-25 credits based on complexity (trivial=1, standard=3, complex=10, epic=25).

---

## Post-Launch Week 1

| Day | Action |
|-----|--------|
| Day 1 | Reply to ALL PH comments, share results |
| Day 2 | Publish blog post: "Building an AI CTO — technical deep dive" |
| Day 3 | Submit to HackerNews |
| Day 4 | Reach out to tech bloggers/YouTubers for reviews |
| Day 5 | Analyze signup data, identify top user segments |
| Day 6 | Launch AppSumo LTD deal (if PH goes well) |
| Day 7 | Weekly retro + plan Week 2 outreach |
