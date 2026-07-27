---
description: "Mekong Brainstorm — Động não chiến lược Binh Pháp cho mekong-cli restructuring plan."
argument-hint: "[topic|problem|opportunity]"
allowed-tools: Bash, Read
---

# /mk:brainstorm

> **Dịch nguồn:** `/ak/aktiviteter/brainstorming` (ak:brainstorm)
> **Mục đích:** Transform unclear intent → bounded delivery contract for mekong-cli restructuring.

## Brainstorm Contract (Bắt buộc)

Mỗi brainstorming session phải capture 4 fields trước khi đi tiếp:

| Field | Mô tả | Ví dụ |
|-------|-------|-------|
| **Outcome** | User-visible / operational end state | "Deep-mapped restructuring plan cho mekong-cli" |
| **Constraints** | Safety, compatibility, time, technology, ownership | "Không break existing CLI commands", "Trong 1 phiên" |
| **Non-goals** | Work phiên này sẽ KHÔNG absorb | "Không implement", "Không migrate data" |
| **Acceptance Criteria** | Observable evidence chứng minh hoàn thành | "Plan file written to docs/", "Reviewed by suntzu" |

## Execution Flow

```
User Topic
   │
   ▼
[1] Brainstorm Contract? ──Yes──▶ Reuse existing contract
   │
   No
   ▼
[2] Capture 4 fields (Hỏi user nếu thiếu)
   │
   ▼
[3] Inspect relevant evidence
   │ (read src/, .claude/, existing plans)
   │
   ▼
[4] Compare approaches (max 3)
   │ (trade-off analysis)
   │
   ▼
[5] Recommend smallest viable approach
   │ (YAGNI, KISS, DRY in order)
   │
   ▼
[6] Pass to /mk:plan or /mk:cook
```

## Quy tắc

- **Proportional:** Concrete request → summarize 4 fields → continue. Only ask if missing answer materially changes safety/public contract.
- **Autonomous execution:** Once 4 fields concrete, autonomous execution continues WITHOUT approval pause.
- **Direct answers / read-only utilities** → NO brainstorm gate needed.
- **Separate target from evidence:** Inspect actual codebase before claiming any approach is feasible.
- **Style:** Sacrifice grammar for concision. Dùng bullet points, tables, mermaid — tránh prose dài.

## Bug Routing (nếu troubleshooting)

1. Scout affected path → capture failing state
2. Diagnose + prove root cause
3. Compare cause-aligned solutions only after diagnosis
4. Full options discussion only when multiple viable fixes remain

## Handoff

Pass 4 contract fields + chosen direction + evidence + unresolved risks to:

| Target |when |
|--------|-----|
| `/mk:plan` | Feature / documentation delivery |
| `/ak:cook` | Implementation delivery |
| Direct report | Exploration only |

## Boundaries

- Shapes intent and choices only — **never implements**
- Never claim current behavior from intent alone
- Never expose secrets or unrelated private files

## Usage

```bash
# Vietnamese — strategic planning
/mk:brainstorm "ánh xạ deep Binh Pháp vào restructuring mekong-cli"

# English — technical architecting
/mk:brainstorm "restructure mekong-cli source tree for better separation of concerns"

# With arguments
/mk:brainstorm "Silicon Valley expansion plan" --auto
```

## Related Commands

| Command | Purpose |
|---------|---------|
| `/mk:plan` | Turn approved brainstorm into executable plan |
| `/mk:cook` | Execute plan with interactive gates |
| `/ask` | Quick Q&A, routing fallback |
| `/mk:design` | Architecture diagrams & design docs |
