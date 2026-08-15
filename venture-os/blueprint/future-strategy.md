# Future Strategy — VentureOS

> **Source:** foundation.md §19 (abridged)
> **Status:** IMMUTABLE | **Version:** 0.1.0 | **Date:** 2026-07-11

---

## 1. Tổng quan / Overview

Tài liệu này định hướng phát triển dài hạn của VentureOS. Mọi quyết định mới phải align với roadmap dưới đây. Khi xung đột → ưu tiên P7 (YAGNI) — đừng implement điều mà chưa đủ evidence cần thiết.

---

## 2. Growth Ladder

### NOW (Q1 2026) — Foundation Complete

| Milestone | Status |
|---|---|
| P1–P10 principles documented | ✅ |
| 9-phase lifecycle defined | ✅ |
| File-as-DB schema stable | ✅ |
| WAL module functional | ✅ |
| Workflow runner (YAML → DAG) | ✅ |
| Compiler runner (Mustache) | ✅ |
| Knowledge graph basic CRUD | ✅ |
| CLI commands working | ✅ |
| First venture walkthrough passing | ✅ |

**Focus:** Correctness. Every module must have ≥5 passing tests.

### Q2 2026 — Ecosystem Seeds

| Milestone | Goal |
|---|---|
| 5+ sample workflows across 3 phases | Template library |
| 3+ sample compilers | Common document types |
| Extension system v1 (registry, install) | Community contributions |
| WAL compaction automated | Maintenance relief |
| `venture import` command | Migration tooling |

**Focus:** Usability. New founder can start in <5 minutes.

### Q4 2026 — Intelligence Layer

| Milestone | Goal |
|---|---|
| AI-native decision assistant | Proactive workflow suggestions |
| Graph-based insight engine | Cross-venture pattern detection |
| Template marketplace | Curated workflow/compiler library |
| Phase auto-unlock logic | Remove manual phase transitions |

**Focus:** Intelligence. OS doesn't just execute — it advises.

### FUTURE (2027+) — Platform Standard

| Milestone | Goal |
|---|---|
| Multi-founder collaboration | Shared ventures, permissions |
| Venture portfolio dashboard | Operator view across all ventures |
| Hosted SaaS option (optional) | Zero-install experience |
| Plugin API (sandboxed extensions) | Safe community code |
| Cross-venture knowledge sharing | Aggregate learnings |

**Focus:** Scale. VentureOS becomes the standard platform for systematic venture creation.

---

## 3. Adding a New Phase (Recipe)

No code changes required. 5-step process:

### Step 1: Define Phase Schema

```yaml
# config/phases.yaml (add new entry)
08:
  name: FUNDRAISE
  name_vi: GỌI VỐN
  order: 8
  unlock_criteria:
    - "phase 07 BUILD completed"
    - "MVP deployed and tested"
  workflows: ["fundraising/pitch-deck", "fundraising/investor Outreach"]
  compilers: ["pitch-deck", "investor-memo"]
  gates: [operator_review]
```

### Step 2: Add Workflow Definitions

```
workflows/fundraising/
├── pitch-deck/
│   └── workflow.yaml
└── investor-outreach/
    └── workflow.yaml
```

### Step 3: Add Compiler Definitions

```
compilers/
├── pitch-deck/
│   ├── compiler.yaml
│   └── template.md
└── investor-memo/
    ├── compiler.yaml
    └── template.md
```

### Step 4: Add Bootstrap Validation

Add unlock criteria validation in `lib/bootstrap.ts` — reads from `config/phases.yaml`, no hardcoded logic.

### Step 5: Add Phase Transition Logic

CLI command `venture phase advance {id}` → reads unlock criteria → validates → updates `venture.toml` → WAL event.

**Total work:** ~2 hours. Zero TypeScript changes if config-driven.

---

## 4. Extension System

### Extension Registry

```yaml
# config/extensions/registry.yaml
extensions:
  - id: custom-research-agent
    version: "0.1.0"
    author: "community"
    description: "Deep research agent with web search"
    license: "MIT"
    entry: extensions/custom-research-agent/index.ts
```

### Extension Manifest

```yaml
# extensions/{id}/manifest.yaml
id: custom-research-agent
version: "0.1.0"
type: agent                              # agent | workflow | compiler | post-processor
capabilities:
  - web_search
  - deep_research
permissions:
  read: [artifacts, knowledge]
  write: [artifacts]
  network: true                          # Allow outbound HTTP (sandboxed)
config_schema:
  search_depth: {type: "integer", default: 3, min: 1, max: 5}
```

### Install/List Commands

```bash
venture extension install custom-research-agent
venture extension list
venture extension uninstall custom-research-agent
```

### Sandboxing Rules

1. Extensions run in isolated Node.js worker thread
2. Network access via OS proxy (no direct fetch)
3. File access restricted to declared permissions
4. No access to other ventures' data
5. Failed extensions don't crash core OS

---

## 5. After 5 Years

| Scenario | State |
|---|---|
| Ventures created | 50+ |
| Active workflows | 20+ custom |
| Extensions available | 10+ community-built |
| Knowledge base | 500+ curated documents |
| Operators | 3–5 team members |

### Maintenance Model

- **Quarterly WAL compaction** — automated cron
- **Annual dependency audit** — verify zero-dependency policy still holds
- **Biannual format review** — must be backward-compatible
- **Community governance** — ADR process for extensions

### Possible Hosted SaaS (Optional)

```
┌─────────────────────────────────────────────┐
│           VentureOS Cloud (Optional)         │
│  ┌─────────────┐    ┌──────────────────┐   │
│  │  Web Dashboard │───│  Venture Runtime │   │
│  └─────────────┘    └──────────────────┘   │
│         │                  │                │
│         ▼                  ▼                │
│  ┌─────────────┐    ┌──────────────────┐   │
│  │  Auth (BYOK) │    │  Teams/Collab    │   │
│  └─────────────┘    └──────────────────┘   │
│                                              │
│  KEY: All venture data ∘ localStorage + sync │
│  User controls backup (git push to their repo) │
└─────────────────────────────────────────────┘
```

**Principle:** If hosted, it MUST preserve P1–P10. User can export at any time. Service is runtime convenience, not data lock-in.

---

## 6. After 100 Projects

### Platform Standard

VentureOS becomes the standard for systematic venture creation:
- **Investors** reference VentureOS structure when evaluating startups
- **Accelerators** use VentureOS as intake format
- **Universities** teach VentureOS in entrepreneurship programs
- **Agencies** offer VentureOS-based venture building services

### Ecosystem

```
VentureOS Ecosystem
├── Core OS (this repo) — MIT license
├── Extension Registry — community contributions
├── Template Library — curated workflows/compilers
├── Knowledge Base — aggregated cross-venture learnings
│   └── Managed by curated contributors
├── Certification — "VentureOS Practitioner" program
└── Events — Annual venture showcase using OS data
```

### Knowledge Base as Moat

The largest competitive advantage is **aggregated venture intelligence**:
- Pattern detection across 100+ ventures
- Phase transition success rates
- Common failure modes and early signals
- Industry-specific benchmark data

**Governance:** Anonymized, opt-in. User owns their data. Aggregation requires explicit consent.

---

## 7. Extension Growth Path

```
Level 1: Custom workflow file (user's venture only)
    ↓ copy
Level 2: Shared workflow in OS repo (all ventures)
    ↓ publish
Level 3: Community extension (install via CLI)
    ↓ certify
Level 4: Certified extension (reviewed, endorsed)
    ↓ govern
Level 5: Core module (merged into OS, maintained by team)
```

Each level requires: automated tests, documentation, backward compatibility guarantee, license clarity.

---

## 8. Risk Mitigation

| Risk | Mitigation |
|---|---|
| Feature creep breaks YAGNI | Every new feature requires "3 ventures need this" evidence |
| Dependency policy violated | CI gate: `npm run verify` fails on new deps |
| Format compatibility broken | Automated migration test suite |
| Community extensions break OS | Sandboxing + permission system |
| Hosted service becomes lock-in | Export API, local-first architecture, open protocols |

---

## 9. Summary

VentureOS grows through **ecosystem, not features**. The core stays minimal. Value accumulates at the edges: templates, extensions, knowledge base, community. The OS is the substrate; everything else is volunteer-built on top.

**The goal is not to build more software. The goal is to build the infrastructure that lets 1000 founders build ventures 10x faster.**
