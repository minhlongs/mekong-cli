# VentureOS Blueprint
> Immutable Foundation — Version 1.0.0
> *"An operating system for venture creation."*

---

## SECTION 1: CORE PHILOSOPHY

### What VentureOS Is

VentureOS is the **operating system layer** between an idea and a company. It does not build products. It builds the *process* by which products are built. Every venture that runs on VentureOS follows the same lifecycle phases, the same decision protocols, the same knowledge flows — but produces a different outcome for each unique idea.

VentureOS is not:
- A SaaS platform (no multi-tenant server)
- A prompt collection (no magic strings)
- A framework (no rigid API)
- An app (no UI required)

VentureOS is:
- A **specification**: a well-defined contract for what a venture looks like at every lifecycle phase
- A **workflow engine**: composable, auditable, replayable pipelines
- A **knowledge substrate**: persistent memory across ventures and time
- A **compiler**: transforms structured inputs into venture artifacts (plans, financials, artifacts, code, pitches)

### The God Metaphor

Think of VentureOS as a **seed genome**. The genome does not grow the tree — it encodes *how* the tree grows given soil (market), water (capital), and light (execution). Every venture is a unique expression of the same genome.

| Layer | What it is | Analog |
|-------|-----------|--------|
| `blueprint/` | Immutable foundation | DNA |
| `workflows/` | Composable pipelines | Enzymes |
| `knowledge/` | Persistent learning | Immune system |
| `memory/` | Cross-venture context | Epigenetics |
| `ventures/` | Individual company instances | Organisms |
| `extensions/` | Community contributions | Adaptations |

### Why Now, Why This Shape

AI coding agents (Claude Code, Codex, Cursor) are powerful but ephemeral. They have no memory across sessions, no institutional knowledge, no reproducibility. The next leap is not a smarter agent — it is a **structured substrate** that makes every venture decision auditable, replayable, and composable.

VentureOS provides that substrate. It is the filesystem on which ventures are built.

---

## SECTION 2: CORE PRINCIPLES

### The Nine Laws

1. **Everything Is Versionable**
   Every artifact — a plan, a decision, a financial model, a pitch — lives in version control. Nothing exists only in a conversation.

2. **Everything Is Composable**
   Workflows, knowledge nodes, and decisions are independent units. Replace one without breaking the whole.

3. **Everything Is Replaceable**
   No component is sacred. Any workflow, knowledge source, or compiler module can be swapped for a better one without a "migration."

4. **Everything Has a Single Source of Truth**
   For every concept, there is exactly one canonical location. Duplicates are derived, not stored.

5. **Decisions Over Actions**
   VentureOS records *why* a decision was made, not just *what* was done. Reverse any decision; replay all dependent actions.

6. **Ideas Before Code**
   The research phase is first-class. An idea without evidence is a hypothesis, not a plan. VentureOS enforces evidence collection before implementation.

7. **Ventures Are Experiments**
   Every venture is a structured experiment with defined inputs, outputs, and success metrics. All results feed the knowledge base.

8. **Human-in-the-Loop, AI-at-Scale**
   AI handles processing, synthesis, research, drafting. Humans make irreversible decisions, allocate capital, and define vision.

9. **Survive Voyager 1**
   The system must be comprehensible to a new engineer 30 years from now, reading only the blueprint and the knowledge base.

---

## SECTION 3: FOLDER STRUCTURE

```
venture-os/
├── blueprint/                    # IMMUTABLE FOUNDATION — never modified, only versioned
│   ├── philosophy.md             # Core beliefs (this document's parent)
│   ├── principles.md             # The Nine Laws, operationally defined
│   ├── lifecycle-phases.md       # Canonical venture lifecycle with phase contracts
│   ├── naming-conventions.md     # Universal naming rules
│   ├── file-standards.md         # File format, encoding, storage standards
│   ├── workflow-architecture.md  # Workflow composition principles
│   ├── knowledge-model.md        # Knowledge graph schema, node types, edge types
│   ├── memory-model.md           # Memory hierarchy and retention policies
│   ├── decision-model.md         # Decision types, authority levels, audit requirements
│   ├── compiler-architecture.md  # Compiler pipeline stages and module contracts
│   ├── repository-standards.md   # Repo layout, git conventions, hosting standards
│   └── extension-strategy.md     # How new capabilities are added without breaking existing ones
│
├── workflows/                    # COMPOSABLE PIPELINE DEFINITIONS
│   ├── research/                 # Research workflow family
│   │   ├── market-research/      # Market sizing, TAM/SAM/SOM, competitive landscape
│   │   ├── customer-research/    # Jobs-to-be-done, personas, interviews
│   │   ├── technology-research/  # Tech stack evaluation, feasibility, build-vs-buy
│   │   ├── financial-research/   # Comparable analysis, unit economics, funding benchmarks
│   │   └── legal-research/       # Incorporation, IP, regulatory landscape
│   │
│   ├── compile/                  # Compiler workflow family
│   │   ├── business-plan/        # Financial model, go-to-market, operations plan
│   │   ├── pitch-deck/           # Investor presentation, narrative arc, Q&A preparation
│   │   ├── technical-landscape/  # Architecture decisions, MVP spec, tech debt forecast
│   │   ├── cap-table/            # Equity model, vesting schedules, dilution scenarios
│   │   └── incorporation/        # Entity setup, jurisdiction selection, bylaws
│   │
│   ├── decision/                 # Decision workflow family
│   │   ├── go-no-go/             # Phase-gate decisions (proceed, pivot, kill)
│   │   ├── budget-approval/      # Capital allocation decisions
│   │   ├── pivot/                # Strategic pivot decisions
│   │   └── partner/              # Co-founder, investor, key hire decisions
│   │
│   ├── knowledge/                # Knowledge workflow family
│   │   ├── ingestor/             # External knowledge → internal graph
│   │   ├── synthesizer/          # Multi-source synthesis → insights
│   │   ├── validator/            # Claim verification, source tracing
│   │   └── curator/              # Knowledge graph maintenance, pruning, linking
│   │
│   └── orchestrate/              # Cross-workflow coordination
│       ├── phase-transition/     # Moving a venture between lifecycle phases
│       ├── portfolio/            # Multi-venture oversight (studio mode)
│       └── handoff/              # Session continuity, context serialization
│
├── knowledge/                    # PERSISTENT KNOWLEDGE SUBSTRATE
│   ├── graph/                    # Knowledge graph (nodes + edges by domain)
│   │   ├── market/               # Market size data, trends, competitive maps
│   │   ├── methodology/          # Proven methodologies, frameworks, playbooks
│   │   ├── precedent/            # Historical venture outcomes, lessons learned
│   │   ├── technology/           # Stack evaluations, build-cost benchmarks, tooling
│   │   ├── financial/            # Comparable multiples, unit economics benchmarks
│   │   ├── legal/                # Jurisdictional rules, compliance frameworks
│   │   └── people/               # Operator profiles, network maps, advisor relationships
│   │
│   ├── schemas/                  # Schema definitions for all knowledge node types
│   │   ├── market-node.schema.json
│   │   ├── methodology-node.schema.json
│   │   ├── precedent-node.schema.json
│   │   └── ...
│   │
│   └── sources/                  # Raw knowledge sources (indexed, not duplicated)
│       ├── contracts/            # Web crawler configs, API subscriptions, feed URLs
│       ├── datasets/             # External dataset references (URLs, DOIs)
│       └── human/                # Expert interviews, advisory sessions, fieldwork
│
├── memory/                       # WORKING AND LONG-TERM MEMORY
│   ├── sessions/                 # Per-session working memory (ephemeral)
│   │   └── {venture-id}/
│   │       └── {session-id}.jsonl
│   ├── ventures/                 # Per-venture persistent memory
│   │   └── {venture-id}/
│   │       ├── identity.json     # Name, mission, founding date, lifecycle phase
│   │       ├── decisions.jsonl   # Append-only decision log
│   │       ├── context.json      # Current working context (what's in flight)
│   │       └── history.jsonl     # Full session history (indexed)
│   ├── global/                   # Cross-venture memory
│   │   ├── patterns.jsonl       # Patterns observed across ventures
│   │   ├── preferences.json     # Global operator preferences
│   │   └── lessons.jsonl        # Lessons learned (append-only)
│   └── index/                    # Memory indices for fast retrieval
│       ├── ventures.idx
│       ├── decisions.idx
│       └── knowledge.idx
│
├── ventures/                     # INDIVIDUAL VENTURE INSTANCES
│   └── {venture-id}/
│       ├── README.md             # Human-readable venture overview (bilingual)
│       ├── metadata.json         # Structured metadata (auto-generated)
│       ├── lifecycle/            # Phase-by-phase venture state
│       │   ├── 01-ideation/
│       │   │   ├── idea.md       # The raw idea (phase contract)
│       │   │   ├── research.md   # Compiled research
│       │   │   ├── hypothesis.json # Structured hypothesis
│       │   │   └── go-no-go.md   # Ideation gate decision
│       │   ├── 02-validation/
│       │   │   ├── customer-interviews/
│       │   │   ├── problem-fit.md
│       │   │   ├── competitive-map.md
│       │   │   └── validation-report.md
│       │   ├── 03-architecture/
│       │   │   ├── business-model.md
│       │   │   ├── unit-economics.md
│       │   │   ├── technical-architecture.md
│       │   │   └── hiring-plan.md
│       │   ├── 04-incorporation/
│       │   │   ├── entity-setup.md
│       │   │   ├── cap-table.json
│       │   │   ├── incorporation-checklist.md
│       │   │   └── jurisdiction.md
# <!-- integrated from lifecycle research: stage KPIs per phase -->
# KPI gate (02): 10+ active users (free/pilot), problem-fit signals >= 3/5
# KPI gate (05): PMF 40% Very Disappointed + $100K ARR or equivalent; 10+ paying customers
# KPI gate (06-07): MVP deployed, 100+ beta users, WAU > 30% target segment
# KPI gate (08-09): $5M+ ARR (Series A) or $20M+ ARR (Series B+); NDR > 100%
# <!-- end lifecycle research integration -->
│       │   ├── 05-seeding/
│       │   │   ├── pitch-deck/
│       │   │   ├── financial-model/
│       │   │   ├── investor-targets.md
│       │   │   └── term-sheet-draft.md
│       │   ├── 06-building/
│       │   │   ├── mvp-spec/
│       │   │   ├── sprint-plan/
│       │   │   ├── product-spec/
│       │   │   └── technical-spec/
│       │   ├── 07-launch/
│       │   │   ├── launch-plan.md
│       │   │   ├── marketing/
│       │   │   ├── ops/
│       │   │   └── metrics/
│       │   ├── 08-scale/
│       │   │   ├── hiring/
│       │   │   ├── capital-raising/
│       │   │   ├── partnerships/
│       │   │   └── expansion/
│       │   └── 09-exit/
│       │       ├── exit-strategy.md
│       │       └── succession-plan.md
│       ├── decisions/            # All venture-specific decisions
│       │   └── {date}-{slug}.md
│       ├── financials/           # Financial artifacts
│       │   ├── model/
│       │   ├── projections/
│       │   ├── actuals/
│       │   └── investor-reports/
│       ├── people/               # People involved in this venture
│       │   ├── founders/
│       │   ├── team/
│       │   ├── investors/
│       │   └── advisors/
│       └── assets/               # Venture-specific assets
│           ├── brand/
│           ├── legal/
│           └── products/
│
├── extensions/                   # COMMUNITY AND CUSTOM EXTENSIONS
│   ├── workflows/                # Custom workflow definitions
│   ├── knowledge-sources/        # Custom knowledge ingestion sources
│   ├── compilers/                # Custom compiler modules
│   ├── skills/                   # Claude Code skills for VentureOS
│   └── templates/                # Document templates by lifecycle phase
│
├── config/                       # SYSTEM CONFIGURATION
│   ├── ventures.config.yaml      # Venture registry, lifecycle settings
│   ├── knowledge.config.yaml     # Knowledge source enablement, refresh rates
│   ├── memory.config.yaml        # Retention policies, indexing settings
│   ├── workflow.config.yaml      # Workflow defaults, overrides per venture
│   └── operators.yaml            # Operator profiles, authorities, preferences
│
├── lib/                          # SHARED LIBRARIES (not a venture's concern)
│   ├── schemas/                  # JSON Schema definitions
│   ├── validators/               # Input validation, contract checking
│   ├── indexers/                 # Search and retrieval libraries
│   ├── serializers/              # Format conversion (JSON, Markdown, PDF)
│   ├── crypto/                   # Signing, verification, audit trails
│   └── git/                      # Version control abstraction layer
│
├── tools/                        # EXECUTION TOOLING
│   ├── cli/                      # VentureOS CLI (what you type)
│   ├── watch/                    # File watchers, event-driven triggers
│   ├── run/                      # Workflow runners per engine type
│   └── validate/                 # Schema validators, contract checkers
│
├── templates/                    # DOCUMENT TEMPLATES
│   ├── lifecycle/
│   │   ├── 01-ideation/
│   │   ├── 02-validation/
│   │   ├── ...
│   │   └── 09-exit/
│   ├── decisions/
│   │   └── {type}.template.md
│   └── reports/
│       └── {type}.template.md
│
└── README.md                     # Entry point — what is this, how to start
```

---

## SECTION 4: ARCHITECTURE OVERVIEW

### Layered Architecture

```
╔══════════════════════════════════════════════════════════════════╗
║                         VENTUREOS                                ║
╠══════════════════════════════════════════════════════════════════╣
║  LAYER 4 — INTERFACE                                        🌐  ║
║  CLI | IDE Extension | API | Web Dashboard                      ║
║  "How humans and AI agents interact with VentureOS"             ║
╠══════════════════════════════════════════════════════════════════╣
║  LAYER 3 — WORKFLOW ENGINE                                 ⚙️   ║
║  Research | Compile | Decision | Knowledge | Memory | Orchestrate║
║  "Composable pipelines that transform inputs into artifacts"    ║
╠══════════════════════════════════════════════════════════════════╣
║  LAYER 2 — KNOWLEDGE SUBSTRATE                            🧠   ║
║  Knowledge Graph | Memory System | Decision Registry             ║
║  "What VentureOS knows and remembers across all ventures"       ║
╠══════════════════════════════════════════════════════════════════╣
║  LAYER 1 — FOUNDATION (blueprint/)                         🏛️   ║
║  Philosophy | Principles | Contracts | Schemas | Standards       ║
║  "What VentureOS is — immutable, versioned, never mutated"     ║
╚══════════════════════════════════════════════════════════════════╝
```

### Invariants

1. **Layer N can only depend on layers below it.** Interface → Workflow → Knowledge → Foundation.
2. **Every artifact has a workflow that produced it.** Nothing appears without provenance.
3. **Every decision has a decision node.** Actions defer to decisions; decisions defer to operators.
4. **Every knowledge claim traces to a source.** The graph is always auditable.
5. **Every memory entry has a retention policy.** Nothing accumulates forever by default.

### Data Flow

```
Raw Input (idea, research, conversation)
    │
    ▼
[Research Workflow] ──► Knowledge Graph (new nodes)
    │
    ▼
[Compile Workflow] ──► Venture Artifacts (plans, specs, models)
    │
    ▼
[Decision Workflow] ──► Decision Registry (append-only log)
    │
    ▼
[Memory Workflow] ──► Memory Store (session → venture → global)
    │
    ▼
[Claude Code Agent] ──► consumes all of the above
```

Every arrow is a versioned, replayable, auditable step.

---

## SECTION 5: RUNTIME CONCEPT

### What is a VentureOS Runtime?

A **Runtime** is a single, self-contained environment where one venture instance lives and evolves. A Runtime is:

- **Isolated**: One venture's state never pollutes another's
- **Composable**: A Runtime can fork (two co-founders), merge (two ventures), or export (to investor)
- **Serializable**: The entire state of a Runtime can be captured, transferred, and restored
- **Replayable**: Every operation on a Runtime is an event in an append-only log

### Runtime Structure

A Runtime is a **directory on disk**:

```
venture-os/runtimes/{runtime-id}/
├── venture/          # symlink or copy of ventures/{venture-id}
├── workspace/        # active working files (git-ignored by default)
├── .state/           # runtime state machine (current phase, locked steps)
│   ├── state.json
│   └── checkpoint.json
├── .events/          # append-only event log (every write, every decision)
│   └── {timestamp}-{event}.jsonl
└── .meta/            # runtime metadata (created, last active, operator)
    └── info.json
```

### Runtime Lifecycle

```
CREATE ──► IDLE ──► RUNNING ──► PAUSED ──► RUNNING ──► ARCHIVED
              │         │         │
              │         │         └──→ DESTROYED (explicit deletion)
              │         └──→ IDLE (savepoint, export)
              └──→ DESTROYED (venture killed)
```

### Runtime Guarantees

1. **Crash-safe**: WAL (Write-Ahead Log) ensures no event is lost
2. **Consistent**: Same inputs + same seeds + same workflow versions = same outputs
3. **Portable**: Runtime directory can be copied, zipped, committed to git, shared
4. **Serializable**: `venture-os export runtime/{id}` → single file containing full state
5. **Auditable**: Every change has an event with timestamp, actor, and diff

### Multi-Runtime Operations

- **Portfolio view**: Enumerate all active runtimes, show phase distribution
- **Fork**: Create a new runtime from an existing one (used for "what if" scenarios)
- **Merge**: Combine two runtimes (used for co-founder collaboration)
- **Diff**: Compare two runtimes at the same phase (used for parallel exploration)
- **Export**: Package a runtime for delivery to an investor, accelerator, or acquirer

---

## SECTION 6: RESEARCH WORKFLOW

### Purpose

The Research workflow turns raw signals (web pages, reports, conversations, data) into **verified, structured, queryable knowledge**. It is the foundation layer — everything else depends on research quality.

### Research Pipeline Stages

```
DISCOVER ──► COLLECT ──► PROCESS ──► VALIDATE ──► SYNTHESIZE ──► PUBLISH
```

| Stage | What happens | Output | Artifacts |
|-------|-------------|--------|-----------|
| **Discover** | Identify what needs to be known for the current venture phase | Research plan (questions, sources, depth) | `research-plan.md` |
| **Collect** | Fetch raw data from sources (web, API, human, dataset) | Raw evidence files | `raw/` directory |
| **Process** | Extract structured data from raw evidence | Structured claims with citations | `claims.jsonl` |
| **Validate** | Cross-check claims, verify sources, flag conflicts | Validated claims + confidence scores | `validated.jsonl` |
| **Synthesize** | Combine claims into coherent findings | Research findings | `findings.md` |
| **Publish** | Merge into knowledge graph, link to existing nodes | Graph updates + venture integration | Knowledge graph mutation |

### Research Contract

Every research output MUST contain:

1. **Source**: Where did the information come from? (URL, interview, dataset DOI)
2. **Timestamp**: When was it collected? (raw news rots; validate freshness)
3. **Confidence**: How reliable is the source? (primary/secondary/tertiary)
4. **Context**: What question was being answered? (link to the research plan)
5. **Conflict**: Does this contradict existing knowledge? (if yes, flag for validation)

### Research Scope by Phase

| Lifecycle Phase | Research Focus | Depth |
|----------------|---------------|-------|
| 01-ideation | Market existence, problem severity, opportunity size | Broad |
| 02-validation | Customer segments, willingness-to-pay, competitive landscape | Deep |
| 03-architecture | Technology feasibility, build costs, comparable business models | Deep |
<!-- integrated from lifecycle research: SEA benchmarks context for all financial modeling -->
| *(all phases)* | **SEA regional context**: valuations 40–60% lower than US equivalents; higher cash-burn sensitivity; monthly burn-rate consciousness in investor expectations; localize all financial assumptions to target market | Ongoing |
<!-- end lifecycle research integration -->
| 04-incorporation | Legal frameworks, tax jurisdictions, compliance requirements | Focused |
| 05-seeding | Investor landscape, term sheet norms, comparable raises | Deep |
| 06-building | Technical benchmarks, vendor evaluations, stack comparisons | Focused |
| 07-launch | Go-to-market channels, marketing benchmarks, launch metrics | Focused |
| 08-scale | Growth benchmarks, hiring market data, expansion opportunities | Focused |
| 09-exit | M&A landscape, IPO pathways, succession benchmarks | Broad |

### Research Quality Gates

- **Seriousness threshold**: Before compiling the business plan (phase 03), at least 10% of claims must come from primary sources (not secondary summaries)
- **Freshness rule**: Market data older than 18 months must be flagged `[stale]` and supplemented
- **Contradiction rule**: Any finding that contradicts the founding hypothesis must stop the pipeline until resolved
- **Citation rule**: Every quantitative claim must have a traceable source. "Studies show..." is not a citation.

---

## SECTION 7: COMPILER WORKFLOW

### Purpose

The Compiler transforms **structured inputs** (decisions, research, market data) into **venture artifacts** (plans, financial models, pitch decks, specifications). It is the translation layer between abstract knowledge and concrete deliverables.

### Compiler Philosophy

A compiler has **input** (source code / venture state), **stages** (parsing / analysis / transformation / generation), and **output** (machine code / venture artifacts). The VentureOS compiler follows the same logic:

```
VENTURE STATE (decisions, research, market data)
    │
    ▼
Parser ──► normalize inputs into canonical internal representation
    │
    ▼
Analyzer ──► validate completeness, check dependencies, identify gaps
    │
    ▼
Transformer ──► apply business logic (financial models, unit economics, dilution math)
    │
    ▼
Generator ──► produce output artifacts in target format
    │
    ▼
Artifacts (plans, decks, models, specs)
```

### Compiler Modules (Per Artifact Type)

| Module | Input | Output | Complexity |
|--------|-------|--------|-----------|
| `business-plan` | Research + decisions | CO/CM1 financial model, GTM plan, org chart | High |
| `pitch-deck` | Business plan + visual brand | 10-12 slide deck (Markdown → PDF/HTML) | Medium |
| `technical-landscape` | Technical research + constraints | Architecture diagram, MVP spec, tech decisions | High |
| `cap-table` | Founder profiles + target raise | Equity split, dilution scenarios, option pool | Medium |
| `incorporation` | Jurisdiction research + founders | Entity docs, bylaws, first board minutes | Low |
| `hiring-plan` | Org chart + budget | Role definitions, compensation benchmarks, timeline | Medium |
| `go-to-market` | Customer research + positioning | Channel strategy, messaging, launch sequence | High |
| `financial-model` | Market data + business model | Revenue projections, cash flow, break-even analysis | High |

<!-- integrated from lifecycle research: SEA financial modeling assumptions -->
### Regional Financial Modeling Assumptions

The compiler's financial modules **must** accept a `region` parameter that adjusts:

- **Valuation multiples**: SEA = 0.4–0.6× US comparables (apply to all `financial-model` and `pitch-deck` compiler outputs)
- **Burn-rate sensitivity**: Monthly burn scrutiny is 2–3× more intense for SEA investors; financial models must show monthly, not quarterly, burn assertions
- **Raise sizing**: SEA rounds are typically 30–50% smaller than US equivalents for comparable stage; cap table scenarios should model both
- **Currency assumptions**: Default to USD for international investor reports; local currency (VND, IDR, THP, PHP) for domestic financial planning

```yaml
financial_model_regional_config:
  default_region: SEA
  valuation_multiplier_vs_us: 0.4 # lower bound; range 0.4-0.6
  currency_reports_international: USD
  currency_planning_domestic: VND # configurable per venture
  burn_rate_scrutiny: monthly # monthly reporting expected
  raise_size_vs_us_factor: 0.5 # median
```

<!-- end lifecycle research integration -->

### Compiler Contract

Every compiled artifact MUST include:

1. **Source references**: Which decisions, research findings, or data points fed into each section
2. **Assumptions**: What was assumed vs. verified (clearly labeled)
3. **Sensitivity**: Which assumptions materially change the output if varied
4. **Recompilable**: Running the compiler again with updated inputs produces a new version, not a patch

<!-- integrated from lifecycle research: typical dilution curve reference -->
### Typical Dilution Curve

- Founders: 55–70% at seed close → 40–50% at Series A → 28–35% at Series C+
- Weighted-average anti-dilution on preferred (not full ratchet)
- Option pool: 10–15% post-dilution, refreshed before each priced round
- Vesting: 4-year with 1-year cliff (founders), 4-year vesting (employees)
<!-- end lifecycle research integration -->

### Compiler Versioning

- Each compiler module has a semantic version (`business-plan@1.2.0`)
- Artifacts stamped with compiler version and input hash
- Re-running compiler = new artifact file, not modification of old one
- Old artifacts preserved for audit trail

---

## SECTION 8: KNOWLEDGE WORKFLOW

### Purpose

The Knowledge workflow maintains the **collective intelligence** of VentureOS. Every research finding, precedent, methodology, and lesson flows through this system. It is the substrate that makes each new venture smarter than the last.

### Knowledge Graph Schema

Every node in the knowledge graph has:

```yaml
id: unique identifier (hash of content + source)
type: market | methodology | precedent | technology | financial | legal | people
content: the structured claim or datum
sources: [list of source references]
confidence: primary (1.0) | secondary (0.7) | tertiary (0.4) | inferred (0.2)
created: ISO timestamp
last_verified: ISO timestamp
venture_origin: which venture this knowledge came from (or null for global)
tags: [free-form taxonomy]
relations: [list of connected node IDs]
deprecated: boolean (soft delete; never hard-delete)
```

Every edge in the knowledge graph has:

```yaml
from: source node ID
to: target node ID
type: contradicts | supports | supersedes | references | part_of | analogous_to
weight: 0.0 to 1.0 (confidence in the relationship)
created: ISO timestamp
```

### Knowledge Hierarchy

Knowledge flows from specific to general:

```
VENTURE-SPECIFIC (this startup's research, customer interviews)
    │  merges into
    ▼
DOMAIN (all SaaS research, all fintech research)
    │  merges into
    ▼
GLOBAL (cross-domain patterns, universal business principles)
```

The knowledge graph is **append-only with soft deprecation**. A node is never deleted — it is marked `deprecated: true` and linked from its replacement node via `supersedes` edge.

### Knowledge Ingestion

| Source Type | Ingestor | Frequency | Schema |
|------------|----------|-----------|--------|
| Web pages | HTTP fetcher + readability extract | On-demand + weekly refresh | `web-node.schema.json` |
| Reports/PDFs | PDF extractor + OCR | On-demand | `document-node.schema.json` |
| Conversations | Session transcript parser | Real-time (per session) | `conversation-node.schema.json` |
| Data files | CSV/JSON parser | On-demand | `dataset-node.schema.json` |
| Human input | Interview wizard | On-demand | `interview-node.schema.json` |
| API feeds | Webhook/API client | Per-feed schedule | `feed-node.schema.json` |

### Knowledge Quality

- **Graph integrity**: Every node's `sources` must resolve (no dead links)
- **Freshness hygiene**: Nodes have `last_verified`; stale nodes flagged in weekly review
- **Conflict resolution**: When a new claim contradicts an existing node, both remain with a `contradicts` edge; the newer one gets `confidence += 0.1`
- **Pruning**: Zero-access nodes after 12 months → moved to `archive/` (not deleted)

---

## SECTION 9: MEMORY WORKFLOW

### Purpose

Memory is VentureOS's **episodic and working memory**. It answers: "What has happened? What is happening now? What did we learn?"

### Memory Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│  GLOBAL MEMORY (memory/global/)                         │
│  Cross-venture patterns, lessons, operator preferences  │
│  Retention: FOREVER (pruned by relevance, not time)     │
├─────────────────────────────────────────────────────────┤
│  VENTURE MEMORY (memory/ventures/{id}/)                 │
│  Decisions, context, full history per venture           │
│  Retention: Until venture exits or is archived          │
├─────────────────────────────────────────────────────────┤
│  SESSION MEMORY (memory/sessions/{id}/)                 │
│  Working context, scratch space, conversation state     │
│  Retention: Until session ends or is explicitly saved   │
└─────────────────────────────────────────────────────────┘
```

### Memory Entry Schema

```yaml
id: unique identifier
type: event | decision | insight | context | lesson | pattern
runtime_id: which runtime this belongs to
session_id: which session (null for global)
venture_id: which venture (null for global)
timestamp: ISO timestamp
actor: system | {operator-name} | {agent-name}
content: the memory content (free-form, structured when possible)
related: [list of related memory IDs]
tags: [taxonomy]
sensitivity: public | internal | confidential  # for selective sharing
```

### Memory Operations

| Operation | Description | Trigger |
|-----------|-------------|---------|
| `IMPRESS` | Store a memory from a workflow event | Automatic (every workflow step) |
| `RECALL` | Retrieve memories by query (semantic + metadata) | Agent request |
| `REFLECT` | Synthesize memories into higher-order insights | Weekly (global), per milestone (venture) |
| `CONSOLIDATE` | Merge session memories into venture memory | Session end |
| `ARCHIVE` | Move old memory to cheaper storage | Scheduled (retention policy) |
| `EXPORT` | Package memories for external delivery | User request |

### Memory Retrieval Model

VentureOS uses **two-tier retrieval**:

1. **Index-first**: Metadata filter (venture, type, date range, tags)
2. **Semantic-second**: Vector similarity on content for relevance ranking

The index layer is always accurate. The semantic layer is approximate but fast. Together they enable natural-language queries like "What happened the last time we evaluated a React vs. Vue decision?"

### Forgetting Policy

Enterprise-grade memory systems must forget intelligently:

- **Session memory**: Auto-forget after 30 days (promoted to venture memory if significant)
- **Venture memory**: Retained until venture archived
- **Global memory**: Never auto-deleted. Marked `deprecated` when superseded.
- **Promotion rule**: If a session memory is referenced in 3+ future sessions, it gets promoted to venture memory

---

## SECTION 10: DECISION WORKFLOW

### Purpose

Decisions are the **immutable spine** of any venture. VentureOS treats decisions as first-class citizens — more important than actions, because actions are replayable given a decision, but decisions are not replayable without the context that created them.

### Decision Types

| Type | Reversibility | Approval Required | Examples |
|------|--------------|-------------------|---------|
| **STRATEGIC** | Low | Founder / Operator | Pivot, major hire, fundraising approach |
| **ARCHITECTURAL** | Medium | Technical authority | Tech stack, platform choice, vendor selection |
| **OPERATIONAL** | High | Team lead | Feature priority, marketing channel, vendor |
| **FINANCIAL** | Medium | Financial authority | Budget allocation, burn rate, pricing |
| **LEGAL** | Low | Legal authority | Entity type, jurisdiction, equity terms |
| **GO/NO-GO** | Terminal | Fundamental | Kill or proceed to next phase |

### Decision Node Schema

```yaml
id: unique identifier (slug + timestamp)
type: strategic | architectural | operational | financial | legal | go-no-go
venture_id: which venture this governs
phase: which lifecycle phase (01-09)
status: proposed | under_review | approved | rejected | executed | superseded
authority: who can approve (operator level)
author: who proposed it
reviewers: [who must weigh in]
decided_at: ISO timestamp (null until approved)
decided_by: who approved (null until approved)
superseded_by: decision ID that replaced this one (null unless superseded)

problem: >
  What problem or question is this decision addressing?
  Must be answerable from the venture context alone.

options:
  - id: A
    description: first option
    pros: [...]
    cons: [...]
    evidence: [research findings that support/reject]
  - id: B
    ...

chosen: option ID selected (null until decided)
rationale: >
  Why was this option chosen? Recorded at decision time,
  not reconstructed later. Must be in the operator's own words.

consequences:
  - description: what happens because of this decision
    affects: [downstream artifacts, decisions, or workflows]
    reversible: boolean

artifacts_affected:
  - file_path: relative to venture directory
    change: created | updated | deleted
```

### Decision Authority Matrix

```
Decision Type          │  Operator  │  Technical  │  Financial  │  Legal  │
───────────────────────┼────────────┼─────────────┼─────────────┼─────────┤
STRATEGIC              │    ✅      │     —       │      —      │    —    │
ARCHITECTURAL          │    —      │     ✅      │      —      │    —    │
OPERATIONAL            │    —      │     ✅      │      ✅     │    —    │
FINANCIAL              │    —      │     —       │      ✅     │    —    │
LEGAL                  │    —      │     —       │      —      │    ✅   │
GO/NO-GO              │    ✅      │     ✅      │      ✅     │    ✅   │
```

### Decision Audit Requirements

Every decision MUST be auditable:
1. Read the decision node → understand the problem
2. Read the evidence links → verify the data the decision was based on
3. Read the rationale → understand the reasoning
4. Read affected artifacts → see what changed because of the decision

If any of these six items (problem, options, evidence per option, rationale, chosen, consequences) are empty, the decision is **incomplete** and cannot be considered executed.

<!-- integrated from lifecycle research: PMF-Gate section added below -->
### Product-Market Fit Gate (GO/NO-GO Criterion)

Every GO/NO-GO decision for the validation phase (02) and seed phase (05) **must** include a PMF gate assessment.

```yaml
pmf_gate:
  method: Sean Ellis test (40% "Very Disappointed" threshold)
  administration: >
    Survey 10+ active users after initial engagement with the product:
    "How would you feel if you could no longer use [product]?"
    Options: Very Disappointed | Somewhat Disappointed | Not Disappointed
  pass_criterion: ">= 40% respond 'Very Disappointed'"
  fail_criterion: "< 40% respond 'Very Disappointed'"
  decision_on_fail:
    - Pivot: Change target segment or problem framing, re-test
    - Kill: Stop if pivot exhausted
  num_users_required: 10 (minimum); 40+ for confidence at Series A stage
  notes: >
    The 40% threshold is empirically validated across B2B SaaS (slower ramp)
    and B2C (faster convergence). B2B may require 15-20 users due to
    smaller addressable segment per niche.
```

PMF gate results are recorded as a **GO/NO-GO decision** with evidence (survey responses, user count, date). The gate cannot be bypassed — it is a hard precondition for the seeding phase (05).

<!-- end lifecycle research integration -->

---

## SECTION 11: NAMING CONVENTIONS

### Why Naming Matters at OS Level

Names are the public API of a file system. They must be:
- **Predictable**: A new user should guess the right name without looking
- **Unique**: No two things share a name in the same directory
- **Stable**: A name does not change because the content changed
- **Sortable**: Alphabetical order is useful

### Universal Rules

| Rule | Rationale |
|------|-----------|
| All lowercase, hyphen-separated | Works on all filesystems; URL-safe |
| Use full words, no abbreviations | `customer-interviews` not `cust-int` |
| Begin with lifecycle phase number | `01-ideation` not `ideation` |
| Nouns for directories, verbs for actions | `research/` not `do-research/` |
| Descriptive over concise | `competitive-landscape-analysis` not `comp` |
| No version numbers in names | Version in metadata, not filename |
| Timestamps are ISO 8601 with `-` | Not `2026_07_10` or `07-10-26` |
| Decision slugs: kebab-case | `tech-stack-react-vue` not `tech-stack-v1` |
| Venture IDs: `{org-type}-{year}-{short-name}` | `startup-2026-modular-commerce` |

### Lifecycle Phase Naming

| Phase | Number | Directory | Artifacts prefix |
|-------|--------|-----------|-----------------|
| Ideation | 01 | `01-ideation/` | `01-ideation-` |
| Validation | 02 | `02-validation/` | `02-validation-` |
| Architecture | 03 | `03-architecture/` | `03-architecture-` |
| Incorporation | 04 | `04-incorporation/` | `04-incorporation-` |
| Seeding | 05 | `05-seeding/` | `05-seeding-` |
| Building | 06 | `06-building/` | `06-building-` |
| Launch | 07 | `07-launch/` | `07-launch-` |
| Scale | 08 | `08-scale/` | `08-scale-` |
| Exit | 09 | `09-exit/` | `09-exit-` |

### Workflow Naming

| Type | Pattern | Example |
|------|---------|---------|
| Workflow directory | `{domain}-{action}` | `market-research`, `customer-interviews` |
| Workflow instance | `{venture-id}-{workflow}-{run-number}` | `startup-2026-mc-market-research-001` |
| Workflow output | `{workflow}-output-{timestamp}` | `market-research-output-2026-07-10` |

### Memory Naming

| Type | Pattern | Example |
|------|---------|---------|
| Session | `{session-id}.jsonl` | `s-20260710-a3f8c2.jsonl` |
| Venture context | `context.json` | (fixed) |
| Decision log | `decisions.jsonl` | (fixed) |
| Decision file | `{date}-{slug}.md` | `2026-07-10-tech-stack-react-vue.md` |

### Knowledge Node IDs

Generated deterministically: `sha256(content + source + type)` truncated to 16 chars.

---

## SECTION 12: FILE CONVENTIONS

### File Format Selection

| Content Type | Primary Format | Secondary | Why |
|-------------|----------------|-----------|-----|
| Narrative documents | Markdown (`.md`) | HTML | Human-readable, version-control-friendly |
| Structured data | JSON (`.json`) | YAML | JSON is universally parseable; YAML for config only |
| Tabular data | CSV (`.csv`) | JSON | CSV for human edits; JSON for programmatic |
| Schemas | JSON Schema (`.schema.json`) | — | Machine-validable contracts |
| Configuration | YAML (`.yaml`) | — | YAML is config-ini-successor |
| Binary assets | Stored separately, referenced | — | Never binary in git |
| Conversations | JSONL (`.jsonl`) | — | Append-only, line-oriented |
| Financial models | JSON Schema on top of CSV | — | Structured but human-editable |
| Decisions | Markdown (`.md`) | — | Human-readable, structured frontmatter |

### Frontmatter Convention

Every structured document has YAML frontmatter:

```yaml
---
id: unique-id
type: document-type
venture: venture-id-or-null
phase: lifecycle-phase-or-null
created: ISO-8601
updated: ISO-8601
author: system | operator-name
status: draft | review | approved | archived | deprecated
sources: [source references]
tags: [taxonomy]
---
```

### Encoding

- **UTF-8 only** (no BOM)
- **LF line endings** (Unix), never CRLF
- **Max line length**: 120 characters (for code), 80 characters for prose
- **No trailing whitespace**

### Size Limits

| File Type | Max Size | Action if exceeded |
|-----------|----------|-------------------|
| Markdown documents | 200KB | Split into sections |
| JSON data files | 50MB | Split into chunks |
| JSONL logs | Unlimited | Segment by date |
| Binary assets | 200MB | Store externally, reference |

---

## SECTION 13: DOCUMENTATION STANDARDS

### Diátaxis Quadrants

Every piece of documentation serves exactly one of four purposes:

| Quadrant | Purpose | Examples | Format |
|----------|---------|---------|--------|
| **Tutorial** | Learning-oriented | Getting started, first venture walkthrough | Step-by-step guide |
| **How-to** | Task-oriented | "How to run market research", "How to compile a pitch deck" | Procedure document |
| **Reference** | Information-oriented | API docs, schema definitions, CLI reference | Specification |
| **Explanation** | Understanding-oriented | Design decisions, architecture rationale | Discussion |

### Documentation Hierarchy

```
README.md                     # Landing / index — what is this, where to start
├── docs/
│   ├── getting-started/      # Tutorials (learn by doing)
│   │   ├── first-venture.md
│   │   ├── file-structure.md
│   │   └── cli-reference.md
│   │
│   ├── how-to/               # How-to guides (solve a specific problem)
│   │   ├── run-market-research.md
│   │   ├── compile-business-plan.md
│   │   ├── make-a-decision.md
│   │   ├── fork-a-venture.md
│   │   └── export-for-investor.md
│   │
│   ├── reference/            # Reference (complete description)
│   │   ├── knowledge-graph-schema.md
│   │   ├── memory-api.md
│   │   ├── workflow-spec.md
│   │   ├── decision-schema.md
│   │   └── lifecycle-phases.md
│   │
│   ├── explanation/          # Explanation (clarify, discuss)
│   │   ├── why-phases.md
│   │   ├── why-immutable-blueprint.md
│   │   ├── why-append-only.md
│   │   └── knowledge-graph-design.md
│   │
│   └── adr/                  # Architecture Decision Records
│       └── {YYYYMMDD}-{slug}.md
│       # Example: 20260415-append-only-event-log.md
```

### ADR Format

```markdown
# ADR-{NNN}: {Title}
> **Status:** accepted | rejected | deprecated | superseded
> **Date:** YYYY-MM-DD
> **Deciders:** {names}

## Context
What is the issue we're facing?

## Decision
What is the change we're proposing/making?

## Consequences
What becomes easier or harder because of this decision?

## Alternatives Considered
What else did we evaluate and why didn't we choose it?
```

### Documentation Principles

1. **One topic per file**: If a file has two unrelated topics, split it
2. **Forward-looking**: Documentation should help the next person, not just explain what exists
3. **Citable**: Every doc has a stable identifier (ADR number, path+anchor)
4. **Living**: Docs that fall out of sync with code are worse than no docs. Attach validation to documentation.
5. **Bilingual where relevant**: Operator-facing content in both English and Vietnamese.

---

## SECTION 14: REPOSITORY STANDARDS

### Repository Structure

```
venture-os/                    # <-- ONE repository, one venture OS instance
├── blueprint/                 # Immutable foundation (versioned independently)
├── workflows/                 # Workflow definitions (versioned independently)
├── knowledge/                 # Knowledge base (versioned, grows over time)
├── ventures/                  # Active ventures (each is a sub-project)
├── extensions/                # Extensions (versioned independently)
├── config/                    # System configuration
├── lib/                       # Shared libraries (versioned independently)
├── tools/                     # CLI and tooling (versioned independently)
├── templates/                 # Document templates (versioned independently)
├── mk/                        # Knowledge base management scripts
└── README.md                  # Entry point
```

### Git Conventions

| Convention | Rule |
|-----------|------|
| **Default branch** | `main` (immutable blueprint), `develop` (active work) |
| **Branch naming** | `feat/{slug}`, `fix/{slug}`, `blueprint/{slug}` |
| **Commit format** | Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `blueprint:` |
| **Blueprint changes** | Require ADR + peer review before merge (immutable = hard to change) |
| **Workflow changes** | Require migration path for existing ventures |
| **Knowledge changes** | Direct to `develop`; merged to `main` weekly |
| **Tagging** | Semver tags on releases: `v1.2.0` |
| **Ignored** | `runtimes/*/workspace/`, `runtimes/*/.events/`, `*.env` |

### Monorepo vs. Multi-Repo Decision

**VentureOS is a monorepo** for its first decade. Rationale:

- **Cognitive simplicity**: One clone, one install, one set of tooling
- **Atomic changes**: A workflow change that needs a schema change is one PR
- **Lifecycle coupling**: Blueprint, workflows, and knowledge co-evolve
- **Discovery**: All ventures, all knowledge, all workflows in one tree

After 10 years, if size becomes a problem, split by domain. Until then, YAGNI.

### Versioning Strategy

```
v{major}.{minor}.{patch}

MAJOR: Blueprint change (new phase, new workflow type, schema migration)
MINOR: Workflow addition, knowledge update, new compiler module
PATCH: Bug fix, documentation update, template refinement

Professional versioning: Each subdomain (blueprint, workflows, knowledge, lib)
is independently versioned. The overall version is a superset: `1.2.3` means
"blueprint at 1.x.x, workflows at 2.x.x, knowledge at 1.x.x..." etc.
```

---

## SECTION 15: FUTURE EXTENSION STRATEGY

### The Extension Problem

How do you add new capabilities to VentureOS without:
1. Breaking existing ventures?
2. Modifying the blueprint?
3. Creating migration debt?

### Extension Design Principles

1. **Extend by adding, not modifying**: New workflows, new knowledge nodes, new compiler modules — all additive
2. **Interface contracts are versioned**: Public interfaces follow semver; breaking changes are new versions, not patches
3. **Extensions are self-describing**: Every extension declares what it provides, what it requires, and what it replaces
4. **Extensions are optional**: The system boots without any extensions

### Extension Types

| Type | Description | Example | Versioning |
|------|-------------|---------|-----------|
| **Workflow** | New pipeline definition | Arabic market research workflow | Semver |
| **Compiler Module** | New artifact type | SAFE agreement generator | Semver |
| **Knowledge Source** | New data feed | Crunchbase API integration | Semver |
| **Decision Type** | New decision template | Regulatory approval decision | Blueprint version bump |
| **Lifecycle Phase** | New phase definition | Pre-exit readiness assessment | Blueprint version bump |
| **Template** | New document template | Series-A investor Q&A | Semver |
| **CLI Plugin** | New command | Interactive cap-table builder | Semver |

### Extension Metadata (required)

Every extension has a `manifest.yaml`:

```yaml
id: extensions/my-extension
name: Arabic Market Research Workflow
description: Research workflow adapted for MENA market
version: 1.0.0
author: {name, url}
extends:
  - workflows/research/market-research
provides:
  - workflow: market-research-ar
  - templates: market-research-ar-templates
requires:
  - knowledge/graph/schemas/market-node.schema.json >= 2.0
compatibility:
  venture-os: ">=2.0.0"
```

### Extension Installation

```bash
venture-os install extensions/market-research-ar
venture-os enable extension market-research-ar --venture startup-2026-x
venture-os list extensions                    # Show installed
venture-os update all extensions             # Update to latest semver-compatible
venture-os remove extension market-research-ar # Clean removal
```

### Extension Boundaries

An extension **can**:
- Add new workflow definitions
- Add new compiler modules
- Add new knowledge nodes and schemas
- Add new document templates
- Add new CLI commands
- Extend existing schemas (by adding optional fields)

An extension **cannot**:
- Modify schema definitions of existing types
- Remove or rename existing workflows
- Change the lifecycle phase definitions
- Modify blueprint documents
- Change the memory or knowledge model
- Access another venture's data (canonical isolation)

### Backward Compatibility Policy

```
When the blueprint changes:
  - Blueprint v1.x ventures continue running on blueprint v1.x
  - Blueprint v2.x creates new kinds explicitly
  - A migration path is always published with the new blueprint

When a workflow changes:
  - Workflows are versioned in-extension
  - Old workflow definitions remain available
  - Ventures can pin to a workflow version

When knowledge graph schema changes:
  - New fields are additive only (never remove)
  - Deprecated fields are flagged, migrated lazily
  - A migration tool runs automatically on install
```

### What Happens After 100 Ventures?

After 100 ventures run on VentureOS:

- The knowledge graph has **100× more data** than after 1 venture
- Each new venture benefits from the synthesized patterns of all 99 before it
- The compiler modules have been exercised 100 times → they are production-tested
- The decision templates are battle-proven
- The ecosystem of extensions has grown organically

This is the **flywheel**. VentureOS gets better with every venture it runs. The system improves by use, not by redesign.

---

## SECTION 16: WORKFLOW EXECUTION MODEL

### Workflow Definition Format

Every workflow is a declarative YAML file:

```yaml
id: workflows/research/market-research
name: Market Research
version: 2.1.0
description: Comprehensive market analysis for opportunity assessment
lifecycle_phases: [01, 02, 05]
estimated_duration: 2-8 hours (scales with depth)

inputs:
  - name: venture_context
    type: object
    required: true
    description: Current venture state (problem hypothesis, industry)
  - name: depth
    type: enum [broad | standard | deep]
    default: standard
    description: Research depth level

outputs:
  - name: research_plan
    type: markdown
    path: lifecycle/01-ideation/research-plan.md
  - name: findings
    type: markdown
    path: lifecycle/01-ideation/research-findings.md
  - name: claims
    type: jsonl
    path: lifecycle/01-ideation/claims.jsonl
  - name: knowledge_entries
    type: object
    description: Nodes to merge into knowledge graph

steps:
  - id: scout
    type: agent
    prompt: |
      Given {venture_context}, identify the Top-5 questions
      that must be answered before this venture can proceed.
      Rank by decisiveness (which answer most changes the decision).
    output_to: research_questions

  - id: source_discovery
    type: agent
    prompt: |
      For each question in {research_questions}, identify
      the best 3-5 sources to answer it. Prioritize:
      primary > secondary > tertiary.
      Avoid sources older than 18 months unless timeless.
    output_to: source_list
    depends_on: [scout]

  - id: collection
    type: parallel
    steps:
      - id: fetch_web
        type: tool
        tool: web-fetcher
        input: {sources: source_list.filter(web)}
      - id: fetch_data
        type: tool
        tool: data-loader
        input: {sources: source_list.filter(datasets)}
    depends_on: [source_discovery]

  - id: processing
    type: agent
    prompt: |
      Extract structured claims from the collected data.
      Each claim must have: text, source, confidence, question_answered.
    input: {raw_data: collection.outputs}
    output_to: raw_claims
    depends_on: [collection]

  - id: validation
    type: agent
    prompt: |
      Validate each claim in {raw_claims}:
      1. Source resolves? (URL alive, DOI found)
      2. Confidence matches source quality?
      3. Contradicts existing knowledge? (check graph)
    output_to: validated_claims
    depends_on: [processing]

  - id: synthesis
    type: agent
    prompt: |
      Synthesize {validated_claims} into coherent findings.
      Structure: Executive summary → Key findings (per question) →
      Confidence assessment → Recommended next steps.
    output_to: findings
    depends_on: [validation]

  - id: knowledge_publish
    type: action
    action: merge-claims-to-graph
    input: {claims: validated_claims, venture_id: $VENTURE_ID}
    depends_on: [validation]

  - id: memory_store
    type: action
    action: impression
    input: {type: research, content: findings.metadata}
    depends_on: [synthesis]
```

### Workflow Contract Rules

1. Every workflow has a **unique ID** matching its file path (no renames without migration)
2. Every workflow declares **inputs**, **outputs**, and **side effects** (graph mutations, memory writes)
3. Every step declares its **dependencies** and outputs a **named result**
4. Workflows are **deterministic** given the same inputs + same seed
5. Failed workflows can be **resumed** from any step (inputs preserved, steps re-runnable)
6. Workflow outputs are **immutable** (new run = new version, never overwrite)

<!-- integrated from lifecycle research: premature scaling guard -->
### Premature Scaling Guard

Before a GO/NO-GO decision passes up to seed phase (05) or beyond, the following guard conditions **must** be checked. Failure of any guard blocks progression to the next phase.

```yaml
premature_scaling_guards:
  condition_1_pmf:
    description: "PMF gate passed (see Section 10 PMF Gate subsection)"
    required: true
    error_action: "HALT. Return to validation phase (02) or earlier."

  condition_2_unit_economics:
    description: "Unit economics are positive or have a credible path to positive within 18 months"
    required_for: [05-seeding, 06-building, 07-launch]
    error_action: "WARN. Document path to profitability; do not proceed to scale-phase (08) without resolution."

  condition_3_runway:
    description: "≥ 18 months runway after planned raise close"
    required_for: [05-seeding, 06-building]
    check: "current_cash / monthly_burn_rate >= 18"
    error_action: "HALT. Defer raising or reduce burn before proceeding."

  condition_4_burn_sensitivity:
    description: "Burn rate changes ≥ 20% require re-evaluation of all downstream financials"
    required: true
    action_on_violation: "Trigger financial-model recompilation before any further phase advancement"

  condition_5_no_feature_bloat_before_pmf:
    description: "Feature scope after PMF validation must be ≤ 3 core features"
    required_for: [06-building]
    rationale: "Premature scaling includes feature bloat before PMF is confirmed"
    error_action: "WARN. Require explicit operator override with documented rationale."
```

> "Premature scaling is the #1 cause of startup death." — Startup Genome Project
>
> These guards are not suggestions. They are **hard gates** enforced by the GO/NO-GO decision workflow. An operator can override any gate, but the override is recorded as a decision node with explicit rationale — creating an auditable trail of risk acceptance.

<!-- end lifecycle research integration -->

### Workflow Composition

Workflows can call other workflows:

```yaml
- id: full_validation
  type: workflow_call
  workflow: workflows/research/market-research
  input: {venture_context: ..., depth: deep}

- id: customer_validation
  type: workflow_call
  workflow: workflows/research/customer-research
  input: {market_findings: full_validation.outputs.findings}
  depends_on: [full_validation]
```

This enables building complex pipelines from simple, tested components.

---

## SECTION 17: CROSS-CUTTING CONCERNS

### Logging

- **Structured logging** via JSONL in `.events/` per runtime
- Log levels: `debug`, `info`, `warn`, `error`, `fatal`
- Every log entry: `{timestamp, actor, level, event, metadata}`
- Logs are the primary debugging and audit mechanism

### Audit Trail

- Every action on a runtime creates an event
- Event format: `{timestamp, event_type, actor, inputs_hash, outputs_hash, diff}`
- Events are append-only and signed
- Full replay of any runtime from events alone

### Backup and Recovery

- **Eventual**: Check every runtime directory into git (exclude `.events/` → use event replay for recovery)
- **Full backup**: `venture-os backup {runtime-id}` creates tarball
- **Granular restore**: Replay events from a specific checkpoint

### Security

- **Isolation**: Runtime directories are independent; no shared state
- **Access control**: Operator-level permissions (who can see/edit which venture)
- **Encryption at rest**: Sensitive financials encrypted with operator key
- **Signing**: Decision nodes can be cryptographically signed
- **No telemetry without consent**: The system works fully offline

### Internationalization

- All interface strings externalized to `locales/`
- Primary: English. Secondary: Vietnamese (for Mekong operator base)
- Documents: English for technical, bilingual (EN+VI) for reports
- Metadata fields available in both languages where relevant

---

## SECTION 18: FIRST-START GUIDE

For the implementer reading this blueprint:

### Phase 0: Bootstrap (Week 1)
1. Create repository from this blueprint
2. Build the CLI tool (`tools/cli/venture`) with core commands: `init`, `list`, `show`, `export`
3. Implement the directory structure (empty shell)
4. Implement the runtime state machine
5. Write 3 ADRs to lock key decisions

### Phase 1: First Workflow (Weeks 2-3)
1. Implement the market research workflow first (highest value, lowest complexity)
2. Build the knowledge graph with 3 node types (market, methodology, precedent)
3. Implement basic memory (session → venture promotion)

### Phase 2: First Compile (Weeks 4-5)
1. Implement the business-plan compiler module
2. Build the decision workflow (go/no-go)
3. Wire decisions → artifacts (decision drives what gets compiled)

### Phase 3: Knowledge Flywheel (Weeks 6-8)
1. Build knowledge ingestion from web sources
2. Implement source verification
3. Build the first 50 knowledge nodes manually (seed the graph)
4. Add knowledge → research integration (research consults graph before trusting a claim)

### Phase 4: Multi-Venture (Weeks 9-12)
1. Portfolio view across runtimes
2. Fork/merge/diff operations
3. Global memory synthesis (weekly reflection)
4. Performance metrics (how well does VentureOS serve each venture?)

### Beyond
- Extension system
- IDE integration
- Web dashboard
- Community contributions
- Multi-operator (studio mode with multiple founders)

---

## APPENDIX: DECISION LOG

This blueprint itself is a sequence of decisions. Recording them here:

| ADR | Decision | Date | Rationale |
|-----|----------|------|-----------|
| 001 | Monorepo, not multi-repo | 2026-07 | Cognitive simplicity; atomic changes; all ventures in one tree |
| 002 | Blueprint is immutable, not mutable | 2026-07 | Immutable foundation = reliable substrate; changes are ADRs |
| 003 | Append-only event log as primary data mechanism | 2026-07 | Auditability, replay, crash-safety, reproducibility |
| 004 | Knowledge graph as universal knowledge substrate | 2026-07 | One format for everything; queryability; composability |
| 005 | File system as primary API (not database) | 2026-07 | Human-readable, versionable, git-native, portable |
| 006 | CLI-first, API and web as derivatives | 2026-07 | CLI is universal; API/web are wrappers over the same logic |
| 007 | 9-phase lifecycle as universal contract | 2026-07 | Derived from universal venture patterns; every venture follows it |
| 008 | Decision nodes as first-class citizens | 2026-07 | Actions without decisions are unreliable; decisions without actions are pointless |
| 009 | Extensions are additive, never subtractive | 2026-07 | Existing ventures must never break; new capabilities via extension |
| 010 | Runtime = directory on disk | 2026-07 | Portability, serializability, no lock-in; can be committed to git |

---

*VentureOS Blueprint v1.0.0*
*Founding Architect: Claude (Anthropic), 2026-07-10*
*"Build the OS that builds the companies."*
