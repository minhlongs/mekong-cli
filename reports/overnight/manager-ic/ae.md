# Account Executive Report — Mekong CLI
*Role: Account Executive | Date: 2026-03-11*

---

## Deal Framework

Mekong CLI's primary motion is self-serve PLG — most deals close without AE involvement.
AE engagement triggers when:
- Lead score ≥ 80 (per SDR scoring model)
- Inbound request for Enterprise tier ($499/mo)
- Company size > 10 engineers
- Custom integration or SLA requirements

---

## Deal Sizing by Segment

| Segment | Typical Deal | Close Time | AE Effort |
|---------|-------------|------------|-----------|
| Individual Dev | $49-149/mo | Self-serve | None |
| Small Team (2-10) | $149-499/mo | 1-2 weeks | Light |
| Agency (10-50) | $499/mo × seats | 2-4 weeks | Medium |
| Enterprise (50+) | Custom ($1K+/mo) | 4-12 weeks | Full |

**Focus:** AE should target Agency and small Enterprise segments. Individual devs
self-close via PLG — AE touching these deals wastes time.

---

## Enterprise Pitch Framework

### Opening Hook (30 seconds)
"Mekong CLI is an AI business operator with 289 commands covering everything from
code scaffolding to sprint planning to financial modeling. It runs on any LLM —
including your existing OpenAI or Anthropic contract — and deploys to Cloudflare
for zero infrastructure cost. Most teams see 40% reduction in repetitive dev tasks
within the first two weeks."

### Discovery Questions
1. "How many engineers are currently spending time on scaffolding and boilerplate?"
2. "Do you have a preferred LLM provider, or are you open to DeepSeek/Qwen for cost savings?"
3. "What does your current deploy pipeline look like? Cloudflare, AWS, or both?"
4. "Who approves developer tooling purchases — is it you or engineering leadership?"
5. "What does success look like 90 days after adopting a new dev tool?"

### Value Proposition by Role

| Stakeholder | Message |
|-------------|---------|
| CTO/Tech Lead | "PEV engine with automatic rollback — safer than manual scripts" |
| Engineering Manager | "289 commands replace 10+ tools — one subscription, one workflow" |
| CFO | "$0 Cloudflare infra + DeepSeek LLM = 60% lower tooling cost than Copilot" |
| Founder (non-tech) | "`mekong annual` generates business plans, `mekong okr` sets quarterly goals" |

---

## POC (Proof of Concept) Framework

For Enterprise deals, offer a 2-week POC:

**Week 1: Technical Validation**
- Install `mekong-cli` on team's existing machine
- Configure with their LLM provider (or Ollama for zero cost)
- Run 5 `mekong cook` tasks from their actual backlog
- Measure: time saved vs manual approach

**Week 2: Business Case**
- Run `mekong review` on 3 existing PRs
- Run `mekong deploy` for one non-production environment
- Calculate MCU consumption → map to correct pricing tier
- Present ROI analysis to decision maker

**POC Success Criteria:**
- ≥3 tasks completed successfully by PEV engine
- Team member ran at least one command independently
- Estimated time savings ≥ 2 hours/week per developer

---

## Objection Handling

**"We already have GitHub Copilot"**
Copilot is code completion in IDE. Mekong CLI is end-to-end task execution — it
plans, executes, verifies, and rolls back. Different tools, complementary use cases.
Many teams use both.

**"We can't use external LLM APIs (security)"**
Ollama support means everything runs locally — no prompts leave your machine.
Zero external API calls if you want.

**"The open source version is free, why pay?"**
The CLI is free forever. The RaaS credits (MCU) fund the cloud dashboard, Tôm Hùm
daemon, and priority support. Enterprise tier includes unlimited credits + SLA.

**"We'd need to integrate with our existing CI/CD"**
The Python SDK (Q3 2026) enables CI/CD integration. In the meantime,
`mekong cook` can be called from any shell script in your GitHub Actions workflow.

**"What if the LLM gives wrong output?"**
The Verifier catches failures before they land. The Orchestrator rolls back
completed steps automatically. It's safer than manual execution.

---

## Enterprise Deal Structure

| Component | Included |
|-----------|---------|
| Unlimited MCU credits | Yes |
| Priority email support (4hr SLA) | Yes |
| Custom LLM provider configuration | Yes |
| Private Slack channel | Yes (>$2K/mo deals) |
| Custom command development | Add-on ($150/hr) |
| On-prem deployment support | Add-on ($500 setup) |
| SLA guarantee (99.9% uptime) | Yes (CF provides this) |

---

## Pipeline Management

**Stage definitions:**
1. **Qualified** — Lead score ≥ 80, confirmed budget and authority
2. **Discovery** — 5 questions answered, use case validated
3. **POC** — 2-week trial underway
4. **Proposal** — Pricing sent, in negotiation
5. **Closed Won/Lost** — Decision made

**Pipeline velocity target:** 30-day average from Qualified → Closed

---

## Q2 AE Actions

- [ ] Create Enterprise one-pager (PDF, 1 page, no fluff)
- [ ] Build ROI calculator spreadsheet (MCU cost vs current tooling cost)
- [ ] Define POC success metrics document for prospects
- [ ] Identify 5 design partner Enterprise candidates from GitHub stargazers
- [ ] Set up Calendly for async demo scheduling (Loom preferred over live calls)
