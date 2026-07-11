# File Format Specifications — VentureOS

> **Source:** foundation.md §7, §8, §9, §10 (abridged)
> **Status:** IMMUTABLE | **Version:** 0.1.0 | **Date:** 2026-07-11

---

## Tổng quan / Overview

Tài liệu này định nghĩa exact schema của từng file format VentureOS sử dụng. Mỗi format phải parse được bởi cả máy và người. Không binary formats. No proprietary formats.

---

## 1. TOML Files (`venture.toml`)

Tiếng Việt: Định danh venture. Được user edit trực tiếp, OS chỉ đọc.

English: Venture identity. Edited by user, read by OS. One-way input.

### Schema

```toml
[venture]
id = "saas-2026-ai-chatbot"          # Required. Must match directory name.
name = "AI Chatbot Platform"          # Required. Human-readable.
type = "startup"                      # Required. startup | side-project | nonprofit | research
phase = "01"                          # Required. Two-digit lifecycle phase: "01"–"09"
language = "en"                       # Default "en". "vi" | "en" | "both"
status = "active"                     # active | paused | archived | exit

[venture.goals]
primary = "Build AI chatbot for SMB"  # Optional. One sentence.
target_market = "SMB retail"          # Optional.

# Any custom keys allowed (forward-compatible)
# OS ignores unknown keys during parse
```

### Rules
- `[venture]` table is REQUIRED, never empty
- `[venture.goals]` is OPTIONAL but highly recommended
- String values: max 200 chars (enforced at bootstrap)
- No nested tables beyond one level (`[a.b]` OK, `[a.b.c]` NOT in v1)
- Unicode allowed in value strings (Vietnamese, accents)
- Keys MUST be lowercase ASCII

### Parser Behavior
- Unknown keys → silently ignored (forward-compatible)
- Missing required keys → BOOTSTRAP BLOCKED (error: "Missing required key: {key}")
- Invalid `type` → BOOTSTRAP BLOCKED (error: "Invalid type. Allowed: startup|side-project|nonprofit|research")
- Invalid `phase` → BOOTSTRAP BLOCKED (error: "Phase must be 01–09")

---

## 2. JSON Files (`state.json`, graph entities)

Tiếng Việt: state.json là DERIVED. Không edit manually.

English: state.json is DERIVED output. Never edit manually.

### `state.json` Schema

```json
{
  "ventureId": "saas-2026-ai-chatbot",
  "phase": "01",
  "currentPhase": "01",
  "workflowRuns": [],
  "decisions": [],
  "compiledOutputs": [],
  "knowledge": {},
  "lastModified": "2026-07-10T20:22:14.616Z",
  "version": "0.1.0",
  "generatedBy": "venture-os",
  "generatedAt": "2026-07-10T20:22:14.616Z"
}
```

### Rules
- `ventureId`: must match parent directory name exactly
- `phase` / `currentPhase`: two-digit string "01"–"09"
- `workflowRuns`: array of workflow run records
- `decisions`: array of decision metadata (id + title only)
- `compiledOutputs`: array of `{compilerId, path, timestamp}`
- `lastModified`: ISO-8601 with milliseconds
- `generatedBy` and `generatedAt`: always present, set by OS
- No other top-level keys in v1 (forward-compatible: unknown keys ignored on read)

### Write Order (OS Responsibility)
1. Read current `state.json` (if exists)
2. Merge new state with existing (preserve unknown keys)
3. Write atomically (write to temp, rename)

### Graph Entity JSON (`knowledge/graph/entities/{id}.json`)

```json
{
  "id": "entity-saas-2026-market-20260710",
  "ventureId": "saas-2026-ai-chatbot",
  "type": "market",
  "labels": ["target", "smb"],
  "properties": {
    "name": "SMB Retail",
    "description": "Small and medium business retail sector",
    "size_estimate": "large"
  },
  "createdAt": "2026-07-10T20-22-14-616Z",
  "updatedAt": "2026-07-10T20-22-14-616Z"
}
```

### Graph Relationship JSONL (`knowledge/graph/relationships.jsonl`)

```jsonl
{"id":"rel-saas-2026-market-venture-20260710","ventureId":"saas-2026-ai-chatbot","type":"targets","sourceId":"venture-saas-2026","targetId":"entity-saas-2026-market-20260710","properties":{},"createdAt":"2026-07-10T20-22-14-616Z"}
```

Rules:
- One JSON object per line (JSONL format)
- No trailing commas
- Append-only — never truncate, never reorder
- Sort order: insertion order (FIFO)

---

## 3. YAML Files (Workflows, Compilers)

Tiếng Việt: Định nghĩa pipeline hoàn toàn bằng YAML. No code changes để thay đổi behavior.

English: Pipeline definitions entirely in YAML. No code changes needed to change behavior.

### Workflow YAML Schema

```yaml
# workflows/{family}/{id}/workflow.yaml
id: research/market-research          # Must match directory path
name: Market Research                 # Human-readable
description: |
  Research target market, competitors, and trends.
  /Nghiên cứu thị trường mục tiêu, đối thủ, xu hướng.
lifecycle_phases: ["01", "02"]        # Which phases this workflow targets
version: "0.1.0"

steps:
  - id: step-1-research-market         # Unique within workflow
    type: agent                         # agent | parallel | workflow_call | action | gate
    prompt: |
      Research the target market for {{venture.name}}.
      /Nghiên cứu thị trường mục tiêu cho {{venture.name}}.
    output: market-research.md

  - id: step-2-analyze-competitors
    type: parallel
    branches:
      - agent:
          prompt: "Find top 5 competitors..."
          output: competitors.md
      - agent:
          prompt: "Analyze pricing models..."
          output: pricing-analysis.md

  - id: step-3-synthesize
    type: agent
    depends_on: [step-1-research-market, step-2-analyze-competitors]
    prompt: |
      Synthesize findings into a market overview...
    output: market-overview.md

  - id: step-4-human-review
    type: gate
    depends_on: [step-3-synthesize]
    message: "Review market overview before proceeding?"
```

### Compiler YAML Schema

```yaml
# compilers/{id}/compiler.yaml
id: business-plan                       # Must match directory name
name: Business Plan                     # Human-readable
description: |
  Compile venture state into a business plan document.
  /Tổng hợp trạng thái venture thành tài liệu business plan.
version: "0.1.0"

inputs:                                 # Mustache variable sources
  - venture.name                         # Flat key → venture.toml [venture] section
  - venture.type                         # → venture.toml [venture] section
  - idea.description                     # → decisions/*.md problem: field
  - market_overview                      # → artifacts/research/market-overview.md
  - decision_history                     # → decisions/*.md all titles

outputs:
  - path: artifacts/compiled/{venture-id}_{id}.md
    format: markdown

template: template.md                   # Relative to this compiler directory
```

### YAML Rules
- All strings quoted unless they are pure lowercase/numbers
- Indentation: 2 spaces (never tabs)
- Multi-line strings: `|` (literal) or `>` (folded)
- Arrays: `[]` or `- item` for objects
- No anchors (`&`) or aliases (`*`) in v1 (added complexity)

---

## 4. Markdown Files (Decisions, Workflows README, Docs)

Tiếng Việt: Tất cả human-facing markdown có heading bilingual. Machine-readable keys = tiếng Anh.

English: All human-facing markdown has bilingual headings. Machine-readable keys = English only.

### Decision Record Format

```markdown
---
id: decision-mvp-scope-chatbot-202607
type: strategic                         # strategic | technical | business | operational
status: approved                        # pending | approved | rejected | superseded
date: 2026-07-10
ventureId: saas-2026-ai-chatbot
authors: ["founder"]
supersedes:                             # Optional. IDs of decisions this replaces.
---

# MVP Scope Decision / Quyết định Phạm vi MVP

> **Context:** We need to define MVP scope before BUILD phase.
> **Bối cảnh:** Cần định nghĩa phạm vi MVP trước phase BUILD.

---

## Options / Lựa chọn

### Option A: Single Feature (chat only)
- **Pros:** Fast to build, lower risk
- **Cons:** Limited differentiation
- **Cons:** Hạn chế khác biệt

### Option B: Chat + Analytics
- **Pros:** More value proposition
- **Cons:** Longer timeline, more complexity
- **Cons:** Timeline dài hơn, complexity cao hơn

---

## Decision / Quyết định

**Option A (chat only).** Build single-feature chatbot with core messaging.
**Lựa chọn A (chat only).** Xây chatbot single-feature với messaging core.

---

## Rationale / Lý do

### Core Thread (English)
Speed to market is critical for early validation. Adding analytics
delays launch by 3+ weeks without proven demand. Ship first, iterate.

### Luồng suy nghĩ chính (Tiếng Việt)
Tốc độ ra thị trường quan trọng cho validation sớm. Thêm analytics
delay launch 3+ tuần không có demand đã chứng minh. Ship trước, iterate sau.

---
```

### Rules
- **Frontmatter** (YAML between `---`): REQUIRED for all decision files
- **Bilingual sections**: `## EN Title / Tiếng Việt` format for headings
- **Dual prose**: English first, `/` separator, Vietnamese second
- **Status values**: `pending` | `approved` | `rejected` | `superseded` (lowercase)
- **Type values**: `strategic` | `technical` | `business` | `operational`
- **Date in frontmatter**: `YYYY-MM-DD` (ISO-8601 date only)
- **Date in filename**: `YYYYMMDD` (no dashes)

### Workflow README Format

```markdown
# Market Research / Nghiên cứu Thị trường

> **ID:** `research/market-research`
> **Phases:** 01 IDENTIFY, 02 IDEA
> **Steps:** 4 | **Est. time:** 15 phút

## Mục đích / Purpose

English description...

/Bản tiếng Việt...

## Khi nào dùng / When to Use

- Giai đoạn IDENTIFY: khi chưa rõ thị trường mục tiêu
- Giai đoạn IDEA: khi cần validate market size

## Inputs / Đầu vào

| Input | Source | Required |
|---|---|---|
| `venture.name` | venture.toml | Yes |
| `idea.description` | decisions/*.md | Yes |

## Outputs / Đầu ra

| Output | Location |
|---|---|
| `market-research.md` | `artifacts/research/` |
| `competitors.md` | `artifacts/research/` |

## Step Overview

1. **Research market** — AI agent: Tổng quan thị trường
2. **Analyze competitors** — Parallel: Top 5 competitors + pricing
3. **Synthesize** — AI agent: Kết hợp findings
4. **Gate** — Human review checkpoint
```

---

## 5. WAL Format (JSONL — Append-Only Event Log)

Tiếng Việt: WAL là event log bất biến. Mỗi line = 1 event.

English: WAL is immutable event log. Each line = 1 event.

### Event Schema

```jsonl
{"ts":"2026-07-10_20-22-14-616Z","type":"venture_init","ventureId":"saas-2026-ai-chatbot","payload":{"name":"AI Chatbot Platform","type":"startup"}}
{"ts":"2026-07-10_20-22-30-123Z","type":"decision_new","ventureId":"saas-2026-ai-chatbot","payload":{"decisionId":"decision-mvp-scope-chatbot-202607","title":"MVP Scope Decision / Quyết định Phạm vi MVP","type":"strategic"}}
{"ts":"2026-07-10_20-23-00-456Z","type":"workflow_run","ventureId":"saas-2026-ai-chatbot","payload":{"workflowId":"research/market-research","stepsCompleted":4,"status":"complete","graphEntities":[{"type":"market","properties":{"name":"SMB Retail"}},{"type":"competitor","properties":{"name":"Competitor A"}}]}}
{"ts":"2026-07-10_20-23-30-789Z","type":"compile","ventureId":"saas-2026-ai-chatbot","payload":{"compilerId":"business-plan","outputPath":"artifacts/compiled/saas-2026-ai-chatbot_business-plan.md"}}
```

### WAL Event Types

| Type | When Emitted | Payload Fields |
|---|---|---|
| `venture_init` | Venture directory created | `name`, `type`, `phase` |
| `decision_new` | New decision recorded | `decisionId`, `title`, `type` |
| `decision_updated` | Decision status changed | `decisionId`, `oldStatus`, `newStatus` |
| `workflow_run` | Workflow execution starts/completes | `workflowId`, `stepsCompleted`, `status`, `graphEntities?` |
| `workflow_step` | Individual step completes | `workflowId`, `stepId`, `status` |
| `compile` | Compiler produces output | `compilerId`, `outputPath` |
| `wal_compact` | WAL compaction runs | `originalLines`, `compactedLines` |
| `graph_entity_add` | Entity added to knowledge graph | `entityId`, `entityType` |
| `graph_entity_update` | Entity modified | `entityId`, `changes` |
| `error` | Recoverable error | `context`, `message` |

### Rules
- **One JSON object per line** — no pretty-print, no trailing commas
- **Never reorder lines** — sequence is the truth
- **Never delete lines** — compaction creates new file + verification, doesn't modify original
- **Timestamp format**: `YYYY-MM-DD_HH-MM-SS-mmmZ` (ISO-8601 with `_` instead of `T`, `-` for time separators)
- **Max file size**: 1000 events (enforced by compaction)
- **Recovery**: `venture wal replay {id}` reconstructs full state

---

## 6. Human-Readable Formats Summary

| Format | Extension | Use Case | Parse Tool |
|---|---|---|---|
| TOML | `.toml` | Venture identity, OS config | `lib/toml-parser.ts` |
| JSON | `.json` | State, graph entities, config | `JSON.parse()` |
| JSONL | `.jsonl` | WAL (append-only log) | Line-by-line parser |
| YAML | `.yaml` | Workflows, compilers, config | Any YAML parser |
| Markdown | `.md` | Decisions, docs, templates | `##` heading parser |
| Mustache | `.md` | Compiler templates | `{{var}}` regex |

### Format Decision Tree

```
Need structured config? → TOML (human-edited) or JSON (machine-generated)
Need append-only log? → JSONL
Need pipeline definition? → YAML
Need human-readable artifact? → Markdown
Need document generation? → Markdown + Mustache
Need cross-venture data? → JSON (graph entities) + JSONL (relationships)
```

---

## 7. Compatibility Rules

1. **Forward compatibility:** Unknown keys in TOML/JSON/YAML are IGNORED (not errors)
2. **Backward compatibility:** Removing a key from `state.json` must not break old ventures (provide default)
3. **Format versioning:** Each format has implicit version from VentureOS version. Explicit `version` field if format changes
4. **Migration:** Format changes → new migration script in `mk/scripts/`, not auto-migration
5. **Reader tolerance:** Parser must handle missing optional fields gracefully; reject only required fields
