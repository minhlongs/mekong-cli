# IP Protection Strategy — March 2026
**Generated:** 2026-03-12 | **Entity:** Mekong CLI / OpenClaw | **Stage:** Pre-Revenue

---

## Executive Summary

Mekong CLI employs a dual-track IP strategy: MIT open source for the CLI engine
(community growth vector) and trade secret protection for the Recipe system
(388 proprietary contracts). Binh Pháp methodology is a trademark candidate.
No patents filed — trade secret + first-mover is the preferred moat.

---

## IP Asset Inventory

| Asset                        | Type          | Protection      | Value Estimate   |
|------------------------------|---------------|-----------------|------------------|
| CLI codebase (src/)          | Copyright     | MIT license     | Community value  |
| Recipe system (388 contracts)| Trade secret  | Server-side only| Core moat        |
| PEV engine (plan/exec/verify)| Copyright     | MIT license     | Architecture IP  |
| Binh Pháp methodology        | Trademark TBD | Common law TM   | Brand value      |
| Agent definitions (14)       | Copyright     | MIT license     | Open source      |
| Command set (261 commands)   | Copyright     | MIT license     | Community value  |
| MCU billing system           | Copyright     | MIT license     | Infra value      |
| "OpenClaw" brand             | Trademark TBD | Common law TM   | Brand value      |
| "Mekong CLI" name            | Trademark TBD | Common law TM   | Brand value      |

---

## Track 1: MIT Open Source (Growth Moat)

### Rationale
Open source CLI maximizes distribution and community adoption. The codebase itself
is not the competitive advantage — the Recipe system, agent network, and community
are the moat. MIT license enables:

- Fork-friendly (encourages ecosystem building)
- Enterprise-friendly (no copyleft risk for customers)
- Developer trust (full code inspection)
- Community contributions (free labor for non-core features)

### What MIT Covers
- `src/core/` — PEV engine, LLM router, orchestrator
- `src/agents/` — All 14 agent definitions
- `.claude/commands/` — All 261 command definitions
- `.claude/skills/` — All 241 skill definitions
- `mekong/infra/` — 3-layer Cloudflare deploy templates

### MIT License Enforcement
- Copyright notice in `LICENSE` file at repo root
- Copyright header in each source file (optional but recommended)
- Annual copyright year update: 2026 → 2027 → ...
- SPDX identifier in package files: `SPDX-License-Identifier: MIT`

---

## Track 2: Trade Secret (Core Moat)

### The Recipe System — 388 Proprietary Contracts

The `factory/contracts/` directory contains 388 JSON machine contracts.
These define the exact execution recipes for each business operation.

**Why trade secret (not patent):**
- Patent requires disclosure → competitors see exact implementation
- Trade secret requires secrecy → maintained indefinitely if protected
- Software patents are expensive ($15K–$30K) and often unenforceable
- First-mover advantage stronger than patent in developer tools market

### Trade Secret Protection Measures

| Measure                          | Status      | Notes                              |
|----------------------------------|-------------|------------------------------------|
| Contracts never in public repo   | ENFORCED    | `factory/contracts/` in .gitignore |
| Server-side execution only       | ENFORCED    | Contracts never sent to client     |
| Employee NDAs                    | PENDING     | Template in Section 4 below        |
| Contractor NDAs                  | PENDING     | Required before any contract access|
| Access logging                   | PLANNED     | CF Workers access log for contracts|
| Encryption at rest               | ACTIVE      | CF D1 AES-256                      |
| No printing/export policy        | PLANNED     | Internal policy doc needed         |

### .gitignore Entries (Verify These Exist)
```
factory/contracts/
.env
.env.*
*.key
secrets/
```

### Recipe System Architecture (Trade Secret Boundary)

```
Public (MIT)              │  Private (Trade Secret)
─────────────────────────────────────────────────
src/core/executor.py     │  factory/contracts/*.json
  calls /v1/recipe API   │  Recipe lookup logic
  receives execution plan│  Proprietary scoring
  runs shell commands    │  Business logic templates
                         │  OCOP contract definitions
```

The executor is MIT. The recipes it executes are proprietary.
Customers get outputs, never recipe internals.

---

## Track 3: Trademark Strategy

### Priority Candidates

**"Binh Pháp" (兵法) as Methodology Mark**
- Distinctive: Vietnamese/Chinese classical reference in tech context
- Descriptive risk: LOW (not descriptive of software)
- Registrability: HIGH (distinctive term in tech category)
- Action: File intent-to-use TM application when revenue begins
- Cost: ~$350 per class (USPTO), ~$1,500 with attorney

**"OpenClaw" as Product Mark**
- Distinctiveness: Medium (compound word)
- Search required: USPTO TESS database check pending
- Action: Common law TM rights established by use in commerce
- Priority: File after first commercial sale

**"Mekong CLI" as Product Mark**
- Geographic term risk: "Mekong" may face descriptiveness challenge
- Strategy: Build common law rights via use, evaluate registration after $100K revenue
- Alternative: Focus TM budget on "OpenClaw" and "Binh Pháp"

### Common Law Trademark Rights (Current)
Rights established by use in commerce, even without registration:
- Use ™ symbol immediately (no registration needed)
- Document first use dates (git commit history serves as evidence)
- Geographic scope: Where product is actively used/distributed

### Trademark Monitoring
- Set Google Alerts for "Mekong CLI", "OpenClaw", "Binh Pháp methodology"
- Check USPTO monthly for conflicting applications
- Domain monitoring: Register .com, .io, .net, .ai variants when revenue allows

---

## Track 4: Copyright Strategy

### Automatic Protection
All original code is automatically protected by copyright upon creation.
No registration required for protection, but registration enables statutory damages.

### Copyright Registration (US)
- Cost: $65 per work (online registration)
- Benefit: Enables statutory damages ($750–$150K per infringement)
- Recommendation: Register when codebase is stable (post-v1.0)
- Priority: LOW until commercially significant

### Copyright Notices
All source files should include:
```python
# Copyright (c) 2026 Mekong CLI Contributors
# SPDX-License-Identifier: MIT
```

---

## Competitive IP Analysis

| Competitor Pattern          | Our Counter                              |
|-----------------------------|------------------------------------------|
| Clone MIT CLI code          | Fine — they can't clone recipe system    |
| Copy command structure      | Fine — commands are templates, not moat  |
| Hire our contributors       | Recipes stay server-side, can't walk out |
| Patent PEV pattern          | Prior art exists (Plan-Execute-Verify)   |
| AGPL to force open source   | MIT — we choose openness strategically   |

---

## IP Due Diligence Checklist (Pre-Fundraise)

Investors will check these before signing:

- [ ] All code in git with clear commit history (provenance)
- [ ] No GPL/AGPL dependencies in MIT-licensed code
- [ ] Employment agreements with IP assignment clauses
- [ ] No prior employer IP contamination (founder declaration)
- [ ] Domain names registered and controlled
- [ ] Trademark searches completed for key marks
- [ ] Trade secret protection measures documented (this file)
- [ ] Open source contributions tracked (CLA or DCO)

---

## Action Items

| Item                                    | Priority | Due         | Cost    |
|-----------------------------------------|----------|-------------|---------|
| Verify factory/contracts/ in .gitignore | Critical | Immediately | $0      |
| USPTO search: "OpenClaw"                | High     | Apr 2026    | $0      |
| USPTO search: "Binh Pháp"              | High     | Apr 2026    | $0      |
| File TM intent-to-use (Binh Pháp)      | Medium   | At $5K MRR  | $350    |
| Copyright registration (codebase)       | Low      | Post-v1.0   | $65     |
| Founder IP assignment agreement         | High     | Apr 2026    | $0 self |
| NDA template for contractors            | Medium   | May 2026    | $0 self |
| Domain portfolio (.com, .io, .ai)       | Medium   | At $1K MRR  | ~$100   |

---

*Next IP review: Pre-fundraise or upon first enterprise inquiry.*
