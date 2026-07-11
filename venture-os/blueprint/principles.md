# Principles — VentureOS Core Principles

> **Source:** foundation.md §1 (P1–P10)
> **Status:** IMMUTABLE | **Version:** 0.1.0 | **Date:** 2026-07-11

---

## Tổng quan / Overview

VentureOS được xây dựng trên 10 nguyên tắc cốt lõi. Mỗi quyết định kiến trúc phải pass qua lăng kính của P1–P10. Nếu không có nguyên tắc nào cover được → viết ADR mới, không break existing principle.

---

## P1: Venture Sovereignty (Chủ quyền Venture)

**Tiếng Việt:** Mỗi venture là một thư mục tự chủ. Copy nó, fork nó, lưu trữ nó — mà không cần động đến OS.

**English:** Each venture is a self-contained directory. Copy it, fork it, archive it — without touching the OS.

**Implications:**
- `ventures/{id}/` phải là đơn vị di chộn duy nhất (copy + paste → hoạt động ngay)
- Không có registry server, không có "project ID database"
- Git clone một venture → có đủ thông tin để hoạt động
- OS chỉ cung cấp runtime; venture không phụ thuộc vào OS

**Anti-patterns:** Registering ventures in a central DB; requiring OS-side secrets to read a venture; venture IDs that need server-side lookup.

---

## P2: Immutable Events (Sự kiện Bất biến)

**Tiếng Việt:** Mỗi thay đổi trạng thái là event append-only. Không event nào bị xóa, sửa, hoặc ghi đè.

**English:** Every state change is an append-only event. No event is ever deleted, modified, or overwritten.

**Implementation:**
- WAL: `wal/current.jsonl` — never truncate, never reorder
- Decision records: `decisions/YYYYMMDD-slug.md` — never overwrite
- If correction needed → write NEW event, not fix old one
- Full audit trail recoverable from git log + WAL replay

**Why:** Không có "sửa lịch sử" → trust. Mọi decision đều có timestamp + author + context. Replay = reconstruction của bất kỳ moment nào trong venture lifecycle.

---

## P3: Source-of-Truth = Files (Files là State)

**Tiếng Việt:** State được derive từ files, không stored trong shadow database. Đọc file = đọc truth.

**English:** State is derived from files, not stored in a shadow database. Reading files = reading truth.

**Implementation:**
- `state.json` là DERIVED OUTPUT — generated, not primary
- `venture.toml` là một-way input — edited by user, parsed by system
- Không có sync issue: không có "state đang drift khỏi files"
- `grep` + `cat` = debugging + auditing

**Anti-patterns:** Dual-write (file + DB); polling DB for "real state"; cache invalidation bugs.

---

## P4: Declarative Pipelines (Pipeline Khai báo)

**Tiếng Việt:** Workflows và compilers là YAML definitions, không phải code. Đổi workflow = edit YAML, không cần viết lại logic.

**English:** Workflows and compilers are YAML definitions, not code. Change a workflow by editing YAML, not rewriting logic.

**Implementation:**
- `workflows/{family}/{id}/workflow.yaml` — DAG definition
- `compilers/{id}/compiler.yaml` — Compiler definition
- Runtime engine đọc YAML → execute generic DAG executor
- Adding step = thêm entry vào YAML array

**Why:** Non-developers có thể modify workflow. No recompile needed. Git diff của workflow = readable change log.

---

## P5: Zero Lock-in (Không khóa chủ)

**Tiếng Việt:** Không binary formats. Không cloud-only storage. Không proprietary schemas. Bất kỳ tool nào đọc markdown/YAML/TOML đều operate được trên venture.

**English:** No binary formats. No cloud-only storage. No proprietary schemas. Any tool that reads markdown/YAML/TOML can operate on a venture.

**Implementation:**
- Full venture = plain text files
- No vendor-specific formats
- Git is the official "backup" mechanism
- `tar` + `gzip` = portable archive

**Why:** 10 năm sau, bạn vẫn có thể đọc venture files. Không cần legacy reader. OS có thể die; venture files survive.

---

## P6: Bilingual by Default (Song ngữ Mặc định)

**Tiếng Việt:** Vietnamese + English trong tất cả artifacts hướng đến người dùng. Keys machine-readable giữ nguyên tiếng Anh.

**English:** Vietnamese + English in all human-facing artifacts. Machine-readable keys remain English-only.

**Implementation:**
- Decision titles: `## EN Title / Tiếng Việt`
- Workflow step outputs: bilingual
- User-facing CLI messages: `vi|en`
- TOML keys, YAML keys, JSON keys: English only
- Decision rationale: bilingual prose

**Format convention:**
```markdown
## Title (English) / Tiếng Việt

English prose here.

/Bản tiếng Việt ở đây.
```

---

## P7: YAGNI / KISS / DRY (Không cần đến thì đừng làm)

Tiếng Việt: Thêm complexity chỉ khi 3+ ventures cần nó. Một mục đích per file. Một trách nhiệm per module.

English: Add complexity only when 3+ ventures need it. One purpose per file. One responsibility per module.

**Rules:**
- Feature proposal: "Will 3 ventures sử dụng điều này?" → No → skip
- File >200 lines? → Split theo boundary logic
- Same logic xuất hiện 2 nơi? → Extract helper
- Module >3 responsibilities? → Split module

**Exception:** OS-level code (lib/) có thể có complexity cao hơn — vì nó phục vụ N ventures. Venture-level code phải đơn giản nhất có thể.

---

## P8: Human-Readable State (Trạng thái Đọc được)

Tiếng Việt: Founder không-technical phải đọc được bất kỳ venture file nào và hiểu nó. Không encoded blobs.

English: A non-technical founder should be able to read any venture file and understand it. No encoded blobs.

**Rules:**
- Không base64-encoded content trong files
- Không encrypted content trong venture directory (chỉ external keys)
- JSON phải được format với indent 2
- Markdown phải có headings hierarchy rõ ràng
- File path + filename = human understandable

**Anti-patterns:** Binary secrets trong venture files; opaque ID references; compressed archives without index.

---

## P9: AI-Native (Thiết kế cho AI)

Tiếng Việt: Mọi artifact đều consumable bởi AI agent mà không cần special tooling.

English: Every artifact is consumable by an AI agent without special tooling.

**Implementation:**
- Markdown frontmatter cho structured metadata
- Consistent section headings (AI dùng để navigate)
- `## 3. Section Title` format — predictable
- TOML/YAML với keys có nghĩa (không `k1`, `v2`)
- WAL events có `type` field có ý nghĩa (`workflow_run`, `decision_new`, `compile`)

**Why:** OS chính là nơi Claude Code chạy. Nếu OS không AI-native, nó tự-sabotage. Every file = prompt context.

---

## P10: Audit-Ready (Sẵn sàng Audit)

Tiếng Việt: Full history của venture có thể reconstruct từ git + WAL alone.

English: The full history of a venture can be reconstructed from git + WAL alone.

**Implementation:**
- Git: file-level history (ai sửa gì, khi nào)
- WAL: event-level history (trạng thái thay đổi ra sao, sequence nào)
- Kết hợp: reconstruct venture state tại bất kỳ moment nào
- Không cần external backup system → git IS the backup

**Verification:** `git log --oneline ventures/{id}/` + `venture wal replay {id}` = full venture history.

---

## Principle Priority (Khi xung đột)

Khi 2 principles xung đột:

1. **P2 (Immutable Events) > P8 (Human-Readable)** — Nếu phải chọn giữa auditability và aesthetics, chọn auditability
2. **P1 (Sovereignty) > P5 (Zero Lock-in)** — Sovereignty là cá nhân hơn; P5 là về format openness
3. **P3 (Files = Truth) > P4 (Declarative Pipelines)** — File state luôn đúng; pipeline chỉ là transformation
4. **P6 (Bilingual) > P9 (AI-Native)** — Cho người trước, AI thứ hai
5. **P7 (YAGNI) > all others** — Nếu feature không cần thiết, đừng implement dù nó "cool"

---

## Principle Enforcement

| Principle | Enforced By | Verification |
|---|---|---|
| P1 Venture Sovereignty | bootstrap gate G1 | `ls ventures/{id}/` structure check |
| P2 Immutable Events | WAL module | `wal/current.jsonl` append-only check |
| P3 Files = Truth | state derivation | No dual-write patterns in code |
| P4 Declarative Pipelines | workflow YAML schema | YAML parses without custom code |
| P5 Zero Lock-in | Dependency policy | `package.json` deps = [events] only |
| P6 Bilingual | i18n checker | All .md files have `VI / EN` sections |
| P7 YAGNI/KISS/DRY | Code review | File count, line count, complexity metrics |
| P8 Human-Readable | Format checker | No base64, no opaque IDs in venture files |
| P9 AI-Native | Schema consistency | Structured headings, predictable keys |
| P10 Audit-Ready | Replay test | `git log` + WAL replay reconstructs state |
