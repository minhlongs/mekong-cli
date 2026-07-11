# VentureOS Blueprint
> Version: 1.0-spec
> Status: IMMUTABLE FOUNDATION
> Author: Founding Architect
> Date: 2026-07-11

---

## 0. Core Philosophy

VentureOS treats **venture creation as an operating system process**.

Every venture is a *process*. Every artifact is a *file*. Every decision is an *immutable event*. Every workflow is a *program*. Every compiler is a *transformation pipeline*.

The OS never owns the venture. The OS only provides the runtime environment. Ventures are sovereign — portable, versionable, forkable.

**Paradigm:** Filesystem-as-database. Git-as-VCS-for-ventures. Markdown-as-data-format. Claude-as-runtime-process.

---

## 1. Core Principles

| # | Principle | What it means |
|---|---|---|
| P1 | **Venture Sovereignty** | Each venture is a self-contained directory. Copy it, fork it, archive it — without touching the OS. |
| P2 | **Immutable Events** | Every state change is an append-only event. No event is ever deleted, modified, or overwritten. |
| P3 | **Source-of-Truth = Files** | State is derived from files, not stored in a shadow database. Reading files = reading truth. |
| P4 | **Declarative Pipelines** | Workflows and compilers are YAML definitions, not code. Change a workflow by editing YAML, not rewriting logic. |
| P5 | **Zero Lock-in** | No binary formats. No cloud-only storage. No proprietary schemas. Any tool that reads markdown/YAML/TOML can operate on a venture. |
| P6 | **Bilingual by Default** | Vietnamese + English in all human-facing artifacts. Machine-readable keys remain English-only. |
| P7 | **YAGNI / KISS / DRY** | Add complexity only when 3+ ventures need it. One purpose per file. One responsibility per module. |
| P8 | **Human-Readable State** | A non-technical founder should be able to read any venture file and understand it. No encoded blobs. |
| P9 | **AI-Native** | Every artifact is consumable by an AI agent without special tooling. Markdown frontmatter, structured sections, consistent naming. |
| P10 | **Audit-Ready** | The full history of a venture can be reconstructed from git + WAL alone. |

---

## 2. Folder Structure

```
venture-os/                          ← OS root (this repository)
├── blueprint/                       ← IMMUTABLE architecture documents
│   ├── foundation.md                ← This document. Never modified after commit.
│   ├── principles.md                ← Core principles (P1–P10)
│   ├── folder-taxonomy.md           ← Purpose of every folder, verbatim
│   ├── naming-conventions.md        ← All naming rules
│   ├── file-format-specs.md         ← YAML/TOML/Markdown schemas
│   └── future-strategy.md           ← Extension roadmap, module deprecation policy
│
├── lib/                             ← OS runtime library (shared engine)
│   ├── index.ts                     ← Barrel re-exports
│   ├── workflow-types.ts            ← Shared types (WorkflowContext, Step, etc.)
│   ├── workflow-runner.ts           ← DAG executor
│   ├── workflow-chain.ts            ← Sequential chain orchestrator
│   ├── compiler.ts                  ← Compiler engine (Mustache renderer)
│   ├── portfolio.ts                 ← Cross-venture operations
│   ├── toml-parser.ts               ← TOML parser (single source of truth)
│   ├── venture-toml-parser.ts       ← Rich TOML extension
│   ├── wal/                         ← Write-ahead log module (POPULATE NEXT)
│   │   ├── index.ts                 ← Public API: append, read, compact, replay
│   │   ├── reader.ts                ← Sequential line reader
│   │   └── compaction.ts            ← Merge logic, retention policy
│   └── graph/                       ← Knowledge graph engine (POPULATE NEXT)
│       ├── index.ts                 ← Public API: add, query, trace
│       └── store.ts                 ← Graph persistence layer
│
├── workflows/                       ← Pipeline definitions (YAML)
│   ├── {family}/                    ← Namespace by domain
│   │   └── {workflow-id}/
│   │       ├── workflow.yaml        ← Definition: steps, dependencies, gates
│   │       └── README.md            ← Human description, trigger conditions, outputs
│   ├── research/                    ← Research workflows
│   │   └── market-research/
│   ├── validation/                  ← Validation workflows (FUTURE)
│   ├── building/                    ← Build workflows (FUTURE)
│   └── compiler/                    ← Compiler-to-workflow bridges (FUTURE)
│
├── compilers/                       ← Compiler YAML definitions
│   └── {compiler-id}/
│       ├── compiler.yaml            ← Definition: inputs, outputs, steps
│       └── template.md              ← Mustache template (Markdown output)
│
├── tools/                           ← OS tooling
│   ├── cli/
│   │   └── venture.ts               ← Primary CLI entry point
│   └── tsconfig.json                ← TS config for tools/
│
├── ventures/                        ← VENTURE DATA (this IS the database)
│   └── {venture-id}/
│       ├── venture.toml             ← Static identity (name, type, phase)
│       ├── state.json               ← Derived runtime state
│       ├── workspace/               ← Active working files (gitignored)
│       ├── artifacts/               ← Workflow/compiler outputs
│       │   ├── {source-family}/     ← Organized by origin workflow
│       │   └── compiled/            ← Compiler outputs
│       ├── decisions/               ← Append-only decision records (.md)
│       ├── wal/                     ← Write-ahead log (crash recovery)
│       ├── knowledge/               ← Venture-specific knowledge
│       │   └── local/               ← Files consumed by compilers as context
│       └── state/                   ← Internal state (chain-state, etc.)
│
├── knowledge/                       ← OS-level knowledge (shared across ventures)
│   ├── legal/                       ← Legal templates, entity docs, compliance
│   ├── market/                      ← Market taxonomy, industry data
│   ├── methodology/                 ← Venture creation methodologies
│   ├── people/                      ← Role definitions, team templates
│   ├── precedent/                   ← Case studies, reference ventures
│   └── technology/                  ← Tech stack templates, architecture patterns
│
├── templates/                       ← Reusable document templates
│   ├── decks/                       ← Pitch deck, investor deck templates
│   ├── plans/                       ← Business plan, financial model templates
│   └── docs/                        ← Policy, charter, bylaws templates
│
├── extensions/                      ← Community extensions (POPULATE NEXT)
│   ├── {extension-name}/
│   │   ├── extension.yaml           ← Manifest
│   │   └── {implementation}         ← Workflows, compilers, templates
│   └── README.md                    ← Extension development guide
│
├── config/                          ← OS-level configuration (POPULATE NEXT)
│   └── tiers.yaml                   ← Venture tier definitions
│
├── docs/                            ← Human documentation
│   ├── README.md                    ← Getting started
│   ├── architecture.md              ← System architecture
│   └── diagrams/                    ← Mermaid architecture diagrams
│
├── adr/                             ← Architecture Decision Records
│   └── {NNN}-{slug}.md              ← ADR format: context, decision, consequences
│
├── plans/                           ← Implementation plans (project-local)
│   ├── {YYYYMMDD}-{slug}/
│   │   ├── plan.md                  ← Short plan overview
│   │   ├── phase-01-{name}.md       ← Phase detail
│   │   └── reports/                 ← Agent reports during execution
│   └── reports/                     ← Root-level reports
│
├── mk/                              ← Build scripts (POPULATE NEXT)
│   └── scripts/
│
└── VentureOS-Blueprint.md           ← THIS FILE. Immutable foundation.
```

### Folder Taxonomy (Complete)

| Folder | Purpose | Allowed Contents | Forbidden Contents | Dependencies | Future Evolution |
|---|---|---|---|---|---|
| `blueprint/` | Immutable architecture docs | `.md` only, one per topic | Code, generated files, YAML configs | None (self-referential) | New topics only. Never edit existing files. |
| `lib/` | OS runtime engine | `.ts` modules | Business logic, venture data, templates | Node stdlib only | Sub-modules (`wal/`, `graph/`) can grow independently |
| `workflows/` | Pipeline definitions | `{family}/{id}/workflow.yaml`, `README.md` | Code, venture-specific data | `lib/workflow-runner.ts` | New families as phases grow |
| `compilers/` | Compiler definitions | `{id}/compiler.yaml`, `template.md` | Code, venture data | `lib/compiler.ts` | Mirror workflow growth |
| `tools/` | CLI and build tools | `cli/*.ts`, `tsconfig.json` | Business logic, venture data | `lib/` | May add MCP server, API server |
| `ventures/` | **THE DATABASE** | Venture directories per `venture.toml` | OS source code, shared knowledge | None (self-contained) | Grows linearly with venture count |
| `knowledge/` | OS-level knowledge base | Markdown, JSON data | Venture-specific content | Compilers (as input source) | Curated by operators, versioned |
| `templates/` | Reusable document templates | `.md` templates | Compiled output, venture data | Compilers | Replaced by compiler templates over time |
| `extensions/` | Community add-ons | Follow extension schema | Core OS files, hardcoded logic | `lib/` public API | Plugin registry when >5 extensions |
| `config/` | OS configuration | `.yaml` configs | Venture data, secrets | Runtime | Tier system, feature flags |
| `docs/` | User/operator docs | `.md`, diagrams | Internal implementation notes | None | README, architecture, deployment |
| `adr/` | Architecture decisions | `NNN-slug.md` | Code, configs | None (informational) | Append-only |
| `plans/` | Implementation plans | `plan.md`, phase files, reports | Production code, venture data | None (project-local) | Cleaned after implementation |
| `mk/` | Build automation | Shell scripts, Makefiles | Runtime code | Shell env | CI/CD integration |

---

## 3. Runtime Concept

```
┌──────────────────────────────────────────────────────┐
│                    VentureOS Runtime                   │
│                                                       │
│  CLI (venture.ts) → Router → Command Handler         │
│                                      ↓                │
│                         ┌──────────────────┐          │
│                         │   Module Dispatcher│         │
│                         └────────┬─────────┘          │
│                                  ↓                     │
│              ┌──────────────────┼──────────────────┐  │
│              ↓                  ↓                   ↓  │
│         [Workflow]         [Compiler]           [CLI] │
│              ↓                  ↓                   │  │
│         YAML steps        Mustache tmpl        Direct│  │
│         → agent calls     → resolveInput       → op  │
│              ↓                  ↓                   │  │
│         WAL events        Artifact output         │  │
│              ↓                                       │  │
│         ┌─────────────────────────────────────┐      │
│         │         Venture Directory            │     │
│         │  venture.toml + state.json + wal/    │     │
│         │  artifacts/ + decisions/ + wal/      │     │
│         └─────────────────────────────────────┘      │
└──────────────────────────────────────────────────────┘
```

**Invariants:**
- Every command reads from the venture directory. No in-memory state survives process exit.
- Every state change writes to WAL first, then derives `state.json` from WAL replay.
- Every agent invocation is a subprocess (`claude --print`). The OS never embeds an LLM.
- Every output is a file. There are no "return values" that exist only in memory.

---

## 4. Architecture Overview (Layer Model)

```
┌─────────────────────────────────────────────────────┐
│  Layer 4: OPERATIONS    — CLI, MCP, API            │  User interface
├─────────────────────────────────────────────────────┤
│  Layer 3: PIPELINES     — Workflows, Compilers      │  Declarative definitions
├─────────────────────────────────────────────────────┤
│  Layer 2: MODULES       — lib/ engine modules       │  Runtime logic
├─────────────────────────────────────────────────────┤
│  Layer 1: FOUNDATION    — Filesystem, Markdown, Git │  Immutable substrate
└─────────────────────────────────────────────────────┘
```

| Layer | Responsibility | Extensibility | Change frequency |
|---|---|---|---|
| Foundation | File formats, folder layout, naming | Never (immutable after v1.0) | < 1/year |
| Modules | Parsing, execution, rendering | Modules can be added | ~1/quarter |
| Pipelines | Workflow/compiler definitions | Freely add new YAML | Per venture need |
| Operations | CLI commands, MCP tools | Add new commands freely | Per feature request |

---

## 5. Venture Lifecycle (9 Phases)

```
 01 IDENTIFY
    ↓ [gate: clarity-score ≥ 7/10]
 02 IDEA
    ↓ [gate: problem-solution fit validated]
 03 VALIDATE
    ↓ [gate: PMF Sean Ellis ≥ 40%]
 04 ARCHITECT
    ↓ [gate: system design approved]
 05 INCORPORATE
    ↓ [gate: legal entity active]
 06 SEED
    ↓ [gate: funding secured or bootstrap viable]
 07 BUILD
    ↓ [gate: MVP functional]
 08 SCALE
    ↓ [gate: repeatable acquisition]
 09 EXIT
```

**Key insight:** A venture may stall at any gate. The OS preserves all artifacts at every phase. "Exit" means the venture stopped progressing — not that data is deleted.

---

## 6. Workflow System

### 6.1 Definition

A workflow is an **ordered sequence of steps** with dependency resolution (DAG execution). Defined entirely in YAML. The runner (`lib/workflow-runner.ts`) is generic — it executes any workflow that conforms to the schema.

### 6.2 Step Types

| Type | Purpose | Implementation |
|---|---|---|
| `agent` | Delegate to an AI agent | Subprocess call to Claude |
| `parallel` | Fan-out to multiple agents | Concurrent subprocess calls |
| `workflow_call` | Nest another workflow | Recursive invocation |
| `action` | Direct OS operation | Execute a registered action handler |
| `gate` | Human validation checkpoint | Emit gate event, halt until resolved |

### 6.3 Naming Convention

```
workflows/
└── {phase-namespace}/{workflow-id}/
    ├── workflow.yaml      ← kebab-case ID matches directory
    └── README.md          ← Human description
```

Examples: `research/market-research`, `validation/pmf-check`, `validation/tech-vetting`

### 6.4 Lifecycle Phases

Workflows declare which lifecycle phases they target:
```yaml
lifecycle_phases: ["01", "02"]  # IDENTIFY, IDEA
```

The runtime skips workflow execution if the venture's current phase doesn't match.

---

## 7. Compiler System

### 7.1 Definition

A compiler is a **Mustache-template renderer** that takes venture files as input and produces a structured artifact. Inputs are resolved from the venture directory (or OS knowledge base). Outputs are written to `artifacts/compiled/`.

### 7.2 Resolution Order

```
resolveInput(name):
  1. If name === 'idea_description' → check decisions/*.md for `problem:` field
  2. Check venture artifacts/ for matching path
  3. Check venture knowledge/local/ for matching path
  4. Check OS knowledge/ for matching path
  5. Fall back to venture state.json
  6. Return null (template renders empty)
```

### 7.3 Template Syntax

| Syntax | Meaning |
|---|---|
| `{{venture.name}}` | Flat key access in template context |
| `{{idea.description}}` | Nested key access |
| `{{#market}}...{{/market}}` | Section iteration (array context) |
| `{{#market.trends}}...{{/market.trends}}` | Nested array iteration |

### 7.4 Naming Convention

```
compilers/
└── {compiler-id}/
    ├── compiler.yaml      ← Inputs, outputs, metadata
    └── template.md        ← Mustache template output
```

---

## 8. Knowledge System

### 8.1 Two-Level Knowledge

| Level | Location | Scope | Examples |
|---|---|---|---|
| OS | `knowledge/{domain}/` | Shared across all ventures | Legal templates, market taxonomies, methodology |
| Venture | `ventures/{id}/knowledge/local/` | Single venture | Industry-specific research, competitor notes |

### 8.2 Usage

Compilers reference knowledge via `input.path`. The resolver checks venture-local first, then falls back to OS-level. This means a single compiler template works for any venture, automatically picking up the most specific context available.

---

## 9. Decision System

### 9.1 Format

Decisions are **append-only Markdown files** with YAML frontmatter:

```markdown
---
id: decision-{slug}-{YYYYMM}
venture_id: {venture-id}
phase: "{phase}"
type: "{type}"
status: proposed | accepted | rejected | superseded
created_at: "{ISO-timestamp}"
title: "{short title}"
problem: "{the actual problem text}"
options:
  - "{option 1}"
  - "{option 2}"
chosen: "{selected option}"
rationale: "{why}"
consequences:
  - "{consequence 1}"
  - "{consequence 2}"
---

## Discussion

Free-form markdown body. Not parsed by OS. Used by humans and agents for context.
```

### 9.2 Conventions

- Filename: `{YYYYMMDD}-{short-slug}.md` — chronological, scannable
- `id` field: `decision-{slug}-{YYYYMM}` — unique, referenceable
- Status progression: `proposed` → `accepted` | `rejected` | `superseded` — never deleted
- `problem:` field is the single source of truth for "what is this venture about?" — consumed by compilers as `idea_description`

---

## 10. Memory System (WAL)

### 10.1 Write-Ahead Log

The WAL is the **single source of truth for event history**. Every state change appends a line to the WAL before any file is modified.

```
ventures/{id}/wal/
├── current.jsonl       ← Active log (appends go here)
└── run-{YYYYMMDD}.jsonl ← Rotated daily
```

### 10.2 Event Schema

```json
{
  "type": "event-type",
  "venture_id": "{id}",
  "timestamp": "{ISO-8601}",
  "data": { ... }
}
```

### 10.3 Recovery

At any point, `state.json` can be reconstructed by replaying the WAL from the last known-good snapshot. This means `state.json` is **derived state** — it can be regenerated, cached, or discarded.

---

## 11. Portfolio System

The portfolio module (`lib/portfolio.ts`) provides cross-venture operations:

| Operation | Function | Returns |
|---|---|---|
| List all ventures | `listVentures(root)` | `VentureSummary[]` |
| Show venture detail | `getVentureDetail(root, id)` | `VentureDetail` |
| Compare ventures | `compareVentures(root, ids[])` | `ComparisonResult` |
| Extract decisions | From `decisions/*.md` frontmatter | Parsed arrays |
| Extract events | From `wal/*.jsonl` | Parsed lines |

---

## 12. Naming Conventions

| Entity | Convention | Example |
|---|---|---|
| Venture ID | `{type}-{YYYY}-{slug}` | `saas-2026-ai-chatbot-platform` |
| Venture directory | Same as ID | `ventures/saas-2026-ai-chatbot-platform/` |
| Workflow ID | `{namespace}/{slug}` | `research/market-research` |
| Compiler ID | `{slug}` | `business-plan` |
| Decision file | `{YYYYMMDD}-{slug}.md` | `20260710-mvp-scope.md` |
| Decision ID field | `decision-{slug}-{YYYYMM}` | `decision-mvp-scope-chatbot-202607` |
| WAL file | `run-{YYYYMMDD}.jsonl` | `run-20260710.jsonl` |
| Plan directory | `{YYYYMMDD}-{slug}/` | `260711-0255-ventureos-next/` |
| ADR file | `{NNN}-{slug}.md` | `001-filesystem-as-db.md` |
| Extension ID | `{slug}` | `custom-research-agent` |
| Knowledge domain | `{domain}` | `legal`, `market`, `technology` |

**Rules:**
- All IDs use kebab-case (`lowercase-with-hyphens`)
- Dates use `YYYYMMDD` for filenames, ISO-8601 for content
- Slugs are max 60 characters, alphanumeric + hyphens only
- No version numbers in IDs (versioning happens in git, not filenames)

---

## 13. File Conventions

### 13.1 Markdown Files

All human-readable documents use Markdown with YAML frontmatter:
```markdown
---
key: value
list:
  - item1
  - item2
---

# Title

Body content...
```

### 13.2 TOML Files

`venture.toml` uses nested TOML with string values:
```toml
[id]
name = "Venture Name"
id = "venture-id"
type = "saas"
created_at = "20260711"

[lifecycle]
current_phase = "01"
phase_label = "IDENTIFY"

[state]
status = "active"
first_start = false
```

### 13.3 JSON Files

`state.json` is always pretty-printed (2-space indent). JSONL files (WAL) are one JSON object per line, no decoration.

### 13.4 YAML Files

Workflow and compiler definitions use a **custom minimal YAML subset** parsed by `lib/workflow-runner.ts` and `lib/compiler.ts`. Supported:
- `[section]` headers
- Dotted-key arrays: `steps.0.id = value`
- Nested inline objects via indentation
- String values (quoted or unquoted)
- Array values via `- item` syntax

**Not supported:** Anchors (`&`), aliases (`*`), multi-line strings with `|`/`>`.

---

## 14. Documentation Standards

| Document | Location | Purpose | Audience |
|---|---|---|---|
| Blueprint | `blueprint/foundation.md` | Immutable architecture | Architects, new contributors |
| ADR | `adr/NNN-{slug}.md` | Decision rationale | Developers, architects |
| Plan | `plans/{date}-{slug}/plan.md` | Implementation planning | Developers |
| Phase file | `plans/{date}-{slug}/phase-XX-{name}.md` | Phase detail | Executing agents |
| Report | `plans/reports/{context}-{date}-{slug}-report.md` | Agent output | Developers |
| Workflow README | `workflows/{fam}/{id}/README.md` | Workflow description | Users, operators |
| Getting Started | `docs/README.md` | Onboarding | New users |
| Architecture | `docs/architecture.md` | System overview | Developers |

### Report Naming

```
{context}-{YYYYMMDD}-{HHMM}-{slug}-report.md
```

Context describes WHO → WHAT: e.g., `from-code-reviewer-to-planner`, `brainstorm-ventureos-next`, `workflow-subagent-portfolio`.

---

## 15. Repository Standards

### 15.1 Git Standards

- **Main branch:** `main` (always deployable)
- **Feature branches:** `fix/{slug}`, `feat/{slug}`, `refactor/{slug}`
- **Commit format:** Conventional commits — `type(scope): description`
  - Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `adr`
  - No AI attribution in commit messages
- **Venture data:** `ventures/` is in the repo (versioned). Workspace files (`.gitignore`d) are ephemeral.

### 15.2 Code Standards

- Language: TypeScript (strict mode, ESM)
- Zero runtime dependencies (Node stdlib only)
- Lint: ESLint on `src/**`
- Format: 2-space indent, semicolons, single quotes
- No `:any` types in production code
- No `console.log` — use logger utility
- Branch `fix/layer2-ruff-tech-debt` for Python lint (if applicable)

### 15.3 Quality Gates

| Gate | Command | Requirement |
|---|---|---|
| Typecheck | `tsc --noEmit` | 0 errors |
| Lint | `npm run lint` | Pass |
| Test | `npm test` | All green |
| Build | `npm run build` | 0 errors |

---

## 16. Future Extension Strategy

### 16.1 Module Growth Path

```
NOW:                Q2 FUTURE:           Q4 FUTURE:
lib/                 lib/wal/ (done)      lib/graph/ (done)
├── compiler.ts      ├── wal/index.ts     ├── graph/index.ts
├── workflow-*.ts    ├── wal/reader.ts    └── graph/store.ts
└── portfolio.ts     └── wal/compact.ts
```

### 16.2 New Phase Addition (Recipe)

To add Phase NN (e.g., VALIDATE):

1. Create `workflows/validation/{wf-id}/workflow.yaml` with `lifecycle_phases: ["03"]`
2. Create `workflows/validation/{wf-id}/README.md`
3. If a new compiler is needed, create `compilers/{id}/compiler.yaml` + `template.md`
4. Add gate criteria in `workflow-chain.ts` or a gate workflow
5. Test: `venture workflow run <venture-id> validation/{wf-id}`

No code changes required. Entirely YAML + Markdown.

### 16.3 Extension System (Future)

When `extensions/` grows beyond 5 community contributions:
- Add `extensions/registry.yaml` (index of available extensions)
- Add `venture extension install <name>`, `venture extension list` CLI commands
- Extension manifest schema: `name`, `version`, `workflows[]`, `compilers[]`, `templates[]`
- Sandboxing: extensions can only write to their own venture subdirectory

### 16.4 After 5 Years

- 50+ ventures in production
- 10+ community extensions
- Knowledge base matured (500+ curated documents)
- Optional: hosted SaaS layer on top of the filesystem (still git-compatible)

### 16.5 After 100 Projects

- VentureOS becomes a platform standard for venture creation
- The blueprint is stable — new ventures install it like an OS
- Extensions form an ecosystem
- The knowledge base is the competitive moat

---

## Appendix A: Immutable Decisions (Do Not Change)

| # | Decision | Rationale |
|---|---|---|
| D1 | Filesystem as primary storage | Zero lock-in, human-readable, git-native |
| D2 | No runtime dependencies | Survives npm deprecation, works offline |
| D3 | Markdown as universal data format | Any LLM can read/write it without special parsers |
| D4 | WAL append-only | Audit trail, crash recovery, state reconstruction |
| D5 | Venture-per-directory | Process isolation, easy backup, trivial deployment |
| D6 | YAML for pipelines (not code) | Non-engineers can create/iterate workflows |
| D7 | Bilingual templates | Primary user base (Vietnamese founders) + global standard |
| D8 | Claude as subprocess, not embedded | OS stays model-agnostic |
| D9 | No cloud-only features | Every feature works locally-first |
| D10 | Zero `console.log` in production | Operator observability via logger, never ad-hoc |

---

## Appendix B: Glossary

| Term | Definition |
|---|---|
| Venture | A single business endeavor, stored as a directory |
| Venture ID | Unique identifier: `{type}-{YYYY}-{kebab-slug}` |
| Phase | One of 9 lifecycle stages (01–09) |
| Workflow | Declarative pipeline defined in YAML |
| Compiler | Template renderer that produces artifacts from venture data |
| WAL | Write-ahead log — append-only event stream |
| Gate | Validation checkpoint that requires human/agent confirmation |
| Decision | Append-only Markdown record of a business decision |
| Artifact | Any output file produced by a workflow or compiler |
| Knowledge | Curated reference data consumed by compilers |
| OS | VentureOS — the operating system for venture creation |

---

*End of Blueprint v1.0. This document is immutable after commit. To propose changes, create an ADR.*
