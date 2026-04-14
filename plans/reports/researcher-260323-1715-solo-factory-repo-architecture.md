# Solo AI Factory — Open Source Repo Architecture Research
**Date:** 2026-03-23 | **Researcher:** researcher-a86ae8b1

---

## Repo Snapshots

### aider (Aider-AI/aider) — 42k stars, Paul Gauthier, solo founder

**Top-level dirs (7):** `.github`, `aider/`, `benchmark/`, `docker/`, `requirements/`, `scripts/`, `tests/`

**README:** ~13k chars. Structure: logo/tagline → badges (stars, PyPI DLs, tokens) → 9 feature bullets → install snippet → 3 LLM examples → docs links → 30+ user quotes.

**NOT in repo:** compiled binaries, web UI/dashboard, API docs, cloud infra, pricing/billing code.

**Mono vs separate:** Single repo. Separate installer at `aider-install` org repo. Conventions community repo.

**Publishing:** PyPI (`aider-chat`) — 5.7M+ installs. Docker secondary. No npm.

**Scope control:** One concern per dir. benchmark/ isolated. No bloat. Cloud features kept entirely off-repo (no SaaS code visible).

---

### plandex (plandex-ai/plandex) — Go, monorepo, WOUND DOWN Oct 2025

**Top-level dirs (8):** `.github/`, `app/`, `docs/`, `images/`, `plans/`, `releases/`, `scripts/`, `test/`

**README:** ~3k words. Features (emoji bullets) → context mgmt → control/autonomy → install → hosting → docs.

**NOT in repo:** cloud platform UI, database schemas, billing/subscription code.

**Mono vs separate:** Monorepo — CLI + server in one repo. Tags: `cli/v2.2.1` and `server/vX`.

**Publishing:** Go binary releases. Cloud was separate (dead). Org has 4 total repos.

**Scope control:** Tight — one product, clear CLI/server split. Wound down: founder burnout from solo grind with family obligations. Key lesson: **cloud SaaS kept separate from CLI tool**.

---

### khoj (khoj-ai/khoj) — 33.6k stars, AGPL-3.0, small team (2-3 devs)

**Top-level dirs (7):** `.devcontainer/`, `.github/`, `.vscode/`, `documentation/`, `scripts/`, `src/`, `tests/`

**README:** Lean. Overview → live demo link → full feature list (external) → self-host → enterprise → FAQ → contributors.

**NOT in repo:** cloud billing, client apps (separate repos), Helm charts (separate).

**Mono vs separate:** Main repo = core Python+TypeScript. Org has 12 repos: `khoj` (core), `openpaper` (research), `pipali` (AI coworker), `terrarium` (sandbox), `flint` (WhatsApp), `sandbox-runtime`, `flare` (blog), etc.

**Publishing:** PyPI + Docker. npm for web components.

**Scope control:** Each concern = separate repo. Core stays clean. Integrations/infra live elsewhere.

---

### smol-developer (smol-ai/developer) — minimal, early-viral

**Top-level dirs (5):** `.devcontainer/`, `dist/`, `examples/`, `smol_dev/`, `v0/`

**README:** Short and punchy. Concept → 3 usage modes → examples gallery → forks list → innovations section → future directions. Deliberately minimal.

**NOT in repo:** web UI, billing, deployment infra, database, auth.

**Scope control:** Markdown-driven design philosophy baked in. "smol" = explicit scope constraint in the name. Single library function exposure (`plan`, `specify_file_paths`, `generate_code_sync`).

---

### OpenHands (All-Hands-AI/OpenHands) — VC-backed, not solo

**Architecture:** V0 monolith → V1 modular SDK. Separate repos: `OpenHands` (core), `OpenHands-Cloud` (Helm/K8s), `openhands-aci` (computer interface), `software-agent-sdk`.

**Key pattern:** Core tool stays open. Cloud/infra ops live in private/separate repos. SDK published independently.

**Not directly comparable** — team + VC, not solo. But confirms: **decouple cloud ops from core SDK**.

---

## Patterns Synthesis

### Repo Structure (Solo/Small Team Winners)

```
public-repo/
├── .github/          # CI workflows only
├── src/ or tool/     # Core tool code
├── tests/            # Tests
├── scripts/          # Dev utilities
├── docs/             # Minimal, link to external site
└── README.md         # Killer first impression
```

**Avg top-level dirs: 6-8.** Never more than 10. Kitchen sink = credibility loss.

### README Formula (Proven)

1. Logo + 1-line tagline
2. 3 badges (stars, installs, latest version)
3. Demo GIF or screenshot (above the fold)
4. 3-5 bullet feature list
5. 2-line install snippet
6. Link to full docs (external site)
7. Social proof (quotes or star count)

**Length:** 2k-13k chars. Sweet spot ~4k. Aider's 13k works because 30% is user testimonials (social proof machine).

### Scope Control Tactics

| Tactic | Used by |
|--------|---------|
| Separate installer repo | aider |
| Integrations in separate repos | khoj |
| Cloud/SaaS fully off-repo | all of them |
| Naming constraint ("smol") | smol-ai |
| Monorepo CLI+server, cloud separate | plandex |
| `v0/` legacy folder for old code | smol-ai |
| benchmark/ isolated | aider |

### What NEVER Goes in Public Repo

- Cloud billing / payment code
- Customer data schemas
- Infra secrets or deploy configs
- Internal dashboards
- Business logic that is the "moat"
- Private app code (clients, SaaS UI)
- Daemon / autonomous internal tools

---

## Ideal "Solo AI Factory" Architecture

### Public Repo (the product)
```
mekong-cli/  ← what the world sees
├── packages/       # SDK, CLI core (publishable to npm/PyPI)
├── .claude/        # Skills + commands (value-add, open)
├── factory/        # Contract templates (differentiator)
├── scripts/        # Shell utilities
├── tests/
└── README.md       # 4k chars max, demo GIF, 1-line install
```

### Private Repos (the business)
```
[org]-apps/         # Customer SaaS instances
[org]-infra/        # Cloudflare, D1, KV configs
[org]-daemon/       # Autonomous CTO brain
[org]-billing/      # Polar.sh hooks, MCU engine
[org]-crm/          # Lead/customer data
```

### Publishing Strategy
- npm: `@openclaw/sdk` and `mekong-cli` (public packages)
- No monorepo if avoidable — separate concerns = separate repos
- GitHub releases for binaries

---

## Key Takeaways for mekong-cli

1. **7 dirs max** in public repo — current structure has contamination risk from `apps/` and `mekong/daemon/`
2. **README needs demo GIF** — currently text-heavy; install snippet should be 2 lines
3. **Move ALL cloud/billing/daemon to private repo** — already partially done per recent commits
4. **Publish `packages/` to npm** — openclaw-engine and mekong-cli-core as installable SDKs
5. **Khoj model works best**: core open, integrations separate repos, cloud fully private
6. **Plandex cautionary tale**: solo grind with SaaS + OSS simultaneously = burnout. Keep boundary hard.

---

## Unresolved Questions

- Should `.claude/skills/` (542 definitions) remain in public repo? Aider doesn't expose its internal prompts. Risk: competitors clone the playbook.
- Is `factory/contracts/` (410 JSONs) a differentiator to keep public, or IP to lock down?
- npm publish cadence — who triggers releases? Manual or CI on tag?
- README demo GIF target — which command is the "wow" moment to film?
