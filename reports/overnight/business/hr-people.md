# HR & People Operations — Mekong CLI

## Overview
Mekong CLI operates as a lean, AI-first team. People ops are managed via CLI commands — from recruiting and onboarding to performance reviews and offboarding. The philosophy: humans make strategic decisions, AI handles execution and documentation.

---

## Organizational Structure (Current: Bootstrap Phase)

```
Founder/CTO (1 human)
├── OpenClaw AI (primary operator — handles 80% of execution)
├── Part-time contractors (as needed)
│   ├── Content (1-2 freelancers)
│   ├── Design (1 freelancer)
│   └── Customer success (1 part-time)
└── Future: Full-time hires at $20K MRR milestone
```

**Headcount plan:**
| MRR Milestone | New Hire |
|--------------|----------|
| $20K MRR | Full-stack developer (core engine) |
| $50K MRR | Sales/GTM lead |
| $100K MRR | Customer success manager |
| $200K MRR | Head of Marketing |

---

## Recruiting (commands: `mekong hr-recruit`, `mekong recruiter-source`, `mekong recruiter-screen`)

### Hiring Philosophy
- Hire for AI-native skills: comfort with LLMs, CLI tools, automation mindset
- Remote-first: async-first culture (Vietnamese timezone base, global team)
- Prefer contractors to start → full-time on proven value
- Interview includes: "Use Mekong CLI to solve X problem live"

### Recruiting Workflow
```
1. mekong hr-recruit "Role: Full-stack Python developer"
   → Generates: job description, requirements, eval criteria

2. mekong recruiter-source
   → Sources from: GitHub contributors, HN "who wants to be hired", LinkedIn

3. mekong recruiter-screen "candidate_cv.pdf"
   → Initial screen: skills match, culture fit signals, async assessment

4. Live interview: mekong cook "Build X" — evaluate problem-solving in real-time

5. Offer: mekong invoice-gen (contractor) or standard employment contract
```

### Job Description Template (via `mekong hr-recruit`)
**Core criteria for any Mekong CLI hire:**
- Python 3.9+ proficiency
- CLI/terminal-native (comfortable in bash/zsh)
- LLM API experience (OpenAI, Anthropic, or open source)
- Async communication (Loom, GitHub issues, written docs)
- Bonus: Contributor to Mekong CLI repo

---

## Onboarding (commands: `mekong hr-onboard`, `mekong people-onboard`, `mekong eng-onboard-dev`)

### Day 1 Checklist (`mekong people-onboard`)
```
- [ ] Access: GitHub org, Cloudflare dashboard, Polar.sh admin
- [ ] LLM setup: .env with LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
- [ ] Run: make setup && make self-test (should show 100/100)
- [ ] Run: mekong cook "hello world" (first command)
- [ ] Read: CLAUDE.md, docs/code-standards.md, docs/system-architecture.md
- [ ] Complete: mekong jr/first-task (assigned starter issue)
```

### Week 1 Onboarding (`mekong hr-onboard`)
- Day 1: Setup + orientation (above checklist)
- Day 2: Read PEV engine source (`src/core/planner.py`, `executor.py`, `verifier.py`)
- Day 3: Fix a bug from GitHub issues (guided by `mekong fix`)
- Day 4: Add a new command to `.agencyos/commands/`
- Day 5: PR review + retrospective (`mekong retrospective`)

### Engineering Onboarding (`mekong eng-onboard-dev`)
- Full PEV engine walkthrough
- Agent architecture: `src/agents/` deep dive
- Test suite: `python3 -m pytest tests/` (62 tests, must all pass)
- LLM router: `src/core/llm_client.py` — how provider fallback works
- Deploy: `mekong deploy` to Cloudflare Workers (staging first)

---

## Performance Management (commands: `mekong hr-performance-cycle`, `mekong performance-review`)

### Performance Review Cadence
- **Monthly**: 1:1 async check-in (Loom video + written summary)
- **Quarterly**: Structured review via `mekong hr-performance-cycle`
- **Annual**: Compensation review + role evolution discussion

### Performance Review Framework (`mekong performance-review`)
**4 dimensions rated 1-5:**
1. **Output quality**: Code quality, tests passing, command quality
2. **Velocity**: PRs merged, tasks closed, MCU delivered
3. **Autonomy**: Works independently, minimal back-and-forth needed
4. **AI leverage**: Uses Mekong CLI effectively for their own work

**Review process:**
```
1. mekong performance-review "teammate_name Q1 2026"
   → Generates structured template with metrics pulled from GitHub
2. Self-assessment: teammate fills in wins, blockers, goals
3. Manager review: 30-min async video (Loom)
4. Action plan: specific goals for next quarter
5. Compensation adjustment: tied to output metrics
```

### Compensation Philosophy
- Base salary: market rate for role + location
- No equity vesting cliff: immediate 12-month vest for contractors going full-time
- Performance bonus: 10-20% based on quarterly review score
- Tool stipend: $100/mo for any LLM API costs (work-related)
- Learning budget: $500/year for courses, conferences

---

## People Offboarding (command: `mekong people-offboard`)

### Offboarding Checklist (`mekong people-offboard`)
```
Knowledge transfer:
- [ ] Document all owned systems/processes in GitHub wiki
- [ ] Record Loom walkthrough of key responsibilities
- [ ] Hand off active GitHub issues to replacement

Access revocation:
- [ ] Remove from GitHub org
- [ ] Revoke Cloudflare dashboard access
- [ ] Remove Polar.sh admin access
- [ ] Rotate any shared API keys

Final deliverables:
- [ ] Final invoice/payroll settled
- [ ] 30-day transition support period (if applicable)
- [ ] Exit survey via mekong feedback
```

---

## HR Compliance

| Requirement | Status | Command |
|------------|--------|---------|
| Contractor agreements | Template via `mekong contract` | `mekong contract` |
| IP assignment clauses | Included in all agreements | `mekong legal-contract-review` |
| Data privacy (GDPR) | Cloudflare data residency | `mekong ops-security-audit` |
| Tax forms (1099/W-9) | Polar.sh handles international | Polar.sh dashboard |
| Non-disclosure agreements | Standard NDA template | `mekong agreement` |

---

## Culture & Values

**Core operating principles for Mekong CLI team:**
1. **Ship, verify, iterate** — PEV is not just for code, it's for work
2. **AI-first execution** — Default to `mekong cook` before doing manually
3. **Async by default** — Write it down, record it, don't meeting it
4. **Dogfood always** — Use Mekong CLI for all ops tasks
5. **Open source mindset** — Default to public, document everything

**Communication tools:**
- GitHub Issues: Primary task tracker
- Loom: Async video updates
- `mekong standup`: Generate daily standup in 30 seconds
- `mekong journal`: Log work for visibility

---

## HR Metrics

| Metric | Target | Command |
|--------|--------|---------|
| Time to hire | <30 days | `mekong hr-recruit` |
| Onboarding completion | 100% Day 1 checklist | `mekong hr-onboard` |
| Performance review cadence | Quarterly, 100% completion | `mekong hr-performance-cycle` |
| Contractor → FT conversion | 50% of proven contractors | `mekong performance-review` |
| Team NPS | >50 | `mekong feedback` |
