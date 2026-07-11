# Folder Taxonomy — VentureOS Directory Reference

> **Source:** foundation.md §2.1
> **Status:** IMMUTABLE | **Version:** 0.1.0 | **Date:** 2026-07-11

---

## Tổng quan / Overview

Mỗi folder dưới đây có: mục đích, nội dung cho phép, nội dung cấm, phụ thuộc, và hướng phát triển tương lai. Đây là single source of truth cho folder structure.

---

## Root Directory

| Folder | Purpose | Allowed Contents | Forbidden | Dependencies | Future Evolution |
|---|---|---|---|---|---|
| `blueprint/` | Kiến trúc bất biến / Immutable architecture | `.md` files, one topic per file | Code, generated files, YAML configs | None (self-referential) | New topics only. Never edit existing files. |
| `lib/` | OS runtime engine | `.ts` modules | Business logic, venture data, templates | Node stdlib only | Sub-modules grow independently |
| `workflows/` | Định nghĩa pipeline / Pipeline definitions | `{family}/{id}/workflow.yaml`, `README.md` | Code, venture data | `lib/workflow-runner.ts` | New families as phases grow |
| `compilers/` | Compiler definitions | `{id}/compiler.yaml`, `template.md` | Code, venture data | `lib/compiler.ts` | Mirror workflow growth |
| `tools/` | CLI + build tools | `cli/*.ts`, `tsconfig.json` | Business logic, venture data | `lib/` | MCP server, API server (future) |
| `ventures/` | **THE DATABASE** | Venture directories (venture.toml + structured files) | OS source code, shared knowledge | None (self-contained) | Linear growth with venture count |
| `knowledge/` | OS-level knowledge (shared) | Markdown, JSON data | Venture-specific content | Compilers as input | Curated by operators, versioned |
| `templates/` | Document templates | `.md` template files | Compiled output, venture data | Compilers | Gradually replaced by compiler templates |
| `extensions/` | Community add-ons | Extension schema compliant | Core OS files, hardcoded logic | `lib/` public API | Plugin registry when >5 extensions |
| `config/` | OS configuration | `.yaml` configs | Venture data, secrets | Runtime | Tier system, feature flags |
| `docs/` | Human documentation | `.md`, diagrams | Internal implementation notes | None | README, architecture guide, deployment |
| `adr/` | Architecture decisions | `NNN-slug.md` | Code, configs | None (informational) | Append-only, never delete |
| `plans/` | Implementation plans | `plan.md`, phase files, `reports/` | Production code, venture data | None (project-local) | Cleaned after implementation |
| `mk/` | Build automation | Shell scripts, Makefiles | Runtime code | Shell env | CI/CD integration |

---

## Venture Directory (`ventures/{venture-id}/`)

Tiếng Việt: Đây là cấu trúc của MỘT venture. Copy toàn bộ venture = copy toàn bộ thư mục này.

English: This is the structure of a SINGLE venture. Copying the venture = copying this entire folder.

| File/Folder | Purpose | Format | Size Limit | Notes |
|---|---|---|---|---|
| `venture.toml` | Static identity (name, type, phase, goals) | TOML | < 200 lines | One-way input; edited by user, parsed by system |
| `state.json` | Derived runtime state | JSON | Auto-generated | NEVER edit manually; regenerated from WAL |
| `workspace/` | Active working files | Mixed | Gitignored | Temp files, drafts, scratch work |
| `artifacts/` | All workflow + compiler outputs | Markdown, JSON | Grows unbounded | Organized by {source-family}/{compiler-id} |
| `artifacts/compiled/` | Compiler outputs only | `.md` | — | Must match compiler template schema |
| `decisions/` | Decision records | `.md` (YYYYMMDD-slug.md) | — | Append-only; never overwrite |
| `wal/` | Write-ahead log | `current.jsonl` | Retention: max 1000 events | Append-only, never reorder |
| `knowledge/` | Venture-specific knowledge | `local/*.md` | — | Files consumed by compilers as context |
| `state/` | Internal state | JSON | Gitignored | Chain-state, workflow state snapshots |

### Venture Directory Invariants

1. `venture.toml` MUST exist và phải parse được (bootstrap gate G2)
2. `wal/current.jsonl` MUST tồn tại sau bất kỳ write operation nào (bootstrap gate G4)
3. `state.json` không được edit manually — nó là derived output
4. `workspace/` được gitignore — không bao giờ commit working files
5. `decisions/` là append-only — mỗi file là YYYYMMDD-slug.md
6. Copy venture = `cp -r ventures/{id} ventures/{id}-copy` → hoạt động ngay

### Venture Directory Growth Model

```
Q1 (1-10 ventures):  ~50MB total  (mostly artifacts + WAL)
Q2 (10-50 ventures): ~250MB total
Q4 (50-200 ventures): ~1GB total

Heap growth = artifacts/ (compiler outputs) + wal/ (event log)
Recommended maintenance: quarterly wal compaction + artifact archiving
```

---

## BLOCKED Folders (Không được sử dụng trong v1)

| Folder | Why | When Allowed |
|---|---|---|
| `database/` | P3 = files are database | Never in v1 (external storage = P5 violation) |
| `cache/` | Filesystem is fast enough | Only if benchmark proves >100ms read penalty |
| `node_modules/` | Zero deps policy | Dependencies require ADR approval |
| `logs/` | WAL is the log | If structured logging needed for debugging việc |
| `.snapshots/` | WAL handles recovery | When graph module needs backup logic |