# Content Writer Report — Mekong CLI
*Role: Content Writer | Date: 2026-03-11*

---

## Content Mission

Educate developers and founders on using Mekong CLI as an AI business operator.
Every piece of content must demonstrate real commands with real output — no vague
AI marketing fluff. Show the terminal, show the result.

---

## Documentation Style Guide

### Voice & Tone
- Direct, technical, no hedging ("you can" → "run this command")
- Vietnamese-friendly: bilingual examples welcome in tutorials targeting VN market
- Binh Pháp philosophy visible but subtle — no forced military metaphors
- Show > tell: always include a code block before explaining it

### Code Block Standards
```bash
# Always include the full command with context
export LLM_API_KEY=sk-or-v1-yourkey
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_MODEL=anthropic/claude-sonnet-4
mekong cook "Create a FastAPI REST API with JWT auth"
```

- Always show the 3 env var exports before `mekong` commands
- Include expected output snippet (truncated to key lines)
- Flag Ollama alternative where relevant: `# Free alternative: use Ollama`

### File Naming (docs)
- kebab-case: `getting-started-with-ollama.md`
- Descriptive enough that grep/LLM tools understand without opening: `mekong-cook-rest-api-tutorial.md`

---

## Content Calendar (Q2 2026)

### Blog Posts

| Title | Target Keyword | Audience | Priority |
|-------|---------------|----------|----------|
| "Getting started with Mekong CLI + Ollama (free)" | mekong cli ollama | Junior devs | P0 |
| "PEV engine: How Mekong CLI plans, executes, and verifies" | ai cli automation | Mid devs | P0 |
| "Replace 10 dev tools with Mekong CLI 289 commands" | developer cli tools | Senior devs | P1 |
| "Zero-cost deployment: Cloudflare Pages + Workers in 15 min" | cloudflare deploy cli | Full-stack devs | P1 |
| "mekong annual: AI business planning for non-tech founders" | ai business plan tool | Founders | P1 |
| "Deep dive: Tôm Hùm daemon — autonomous AI task dispatch" | ai agent daemon | Advanced devs | P2 |
| "Mekong CLI vs Cursor vs Copilot: honest comparison" | cursor alternative cli | All devs | P2 |

### Tutorial Series: "Cook Like a Pro"

Part 1: `mekong cook "Create a Python REST API"` — scaffold to working API
Part 2: `mekong test` — automated test generation and execution
Part 3: `mekong deploy` — CF Workers deploy from zero
Part 4: `mekong review` — code quality gates, what passes, what fails
Part 5: `mekong fix "TypeError in auth middleware"` — debug loop walkthrough

### Changelog Posts (per release)
- Publish to blog + Discord + Twitter on each minor/major release
- Format: "What's new in v0.3.0" with GIF demo of headline feature

---

## README Improvement Plan

Current README is functional but needs conversion optimization:

| Section | Status | Action |
|---------|--------|--------|
| Hero/headline | Good | Add GIF demo above the fold |
| Quick Start | Good | Add `mekong init --wizard` when available |
| Architecture diagram | Exists | Add visual 5-layer diagram |
| Command table | Exists | Link each command to docs |
| Pricing section | Exists | Add "Start free with Ollama" callout |
| Contributing guide | Missing | Add `CONTRIBUTING.md` link |
| Badge row | Missing | Add: stars / downloads / license / version |

---

## Documentation Structure (Proposed)

```
docs/
├── getting-started/
│   ├── installation.md
│   ├── first-cook.md
│   └── llm-setup-guide.md          # All 8 providers
├── commands/
│   ├── engineer/cook.md
│   ├── engineer/deploy.md
│   ├── founder/annual.md
│   └── ... (289 commands)
├── architecture/
│   ├── pev-engine.md
│   ├── agent-system.md
│   └── cloudflare-infrastructure.md
├── tutorials/
│   └── cook-like-a-pro/
└── reference/
    ├── cli-flags.md
    └── mcu-credits.md
```

---

## SEO Strategy

Primary keywords (high intent, low competition):
- "ai cli tool open source" — low competition, high dev intent
- "mekong cli" — brand term, own it early
- "pev engine ai" — unique term, own it
- "cloudflare workers deploy cli" — technical, high intent

Content interlinking: Every tutorial links to pricing page + GitHub repo.
Every GitHub README section links to full docs site.

---

## Social Content Templates

### Twitter/X (launch announcement)
```
Just shipped: Mekong CLI v0.3.0

289 commands. 5 business layers. Any LLM.

mekong cook "Build a REST API with auth"
→ Plans it. Executes it. Verifies it. Rolls back if wrong.

Open source (MIT) + free with Ollama.

github.com/longtho638-jpg/mekong-cli
```

### IndieHackers (monthly update)
Template: What we shipped / numbers / what's next / ask for feedback

---

## Q2 Content Actions

- [ ] Write "Getting started with Ollama" tutorial (P0, target: week 1)
- [ ] Write "PEV engine deep dive" blog post (P0, target: week 2)
- [ ] Record `mekong cook` 90-second demo GIF
- [ ] Create `CONTRIBUTING.md` for open source onboarding
- [ ] Add badge row to README (stars, downloads, license, CI status)
- [ ] Set up docs site (Docusaurus on CF Pages — $0 hosting)
