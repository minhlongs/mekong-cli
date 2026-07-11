# BOOTSTRAP — VentureOS Foundation Gate

> **Version:** 0.1.0 | **Status:** IMMUTABLE | **Date:** 2026-07-11
> **Authority:** ADR-004, foundation.md (P1–P10)
> **Invocation:** `venture bootstrap <venture-id>`

---

## 0. Purpose

This document is the **single source of truth for what must be verified and operational before any implementation code is executed**. It is NOT a plan — it is a gate specification.

**Rule:** No module will be coded, tested, or deployed until its corresponding bootstrap gate passes.

---

## 1. Bootstrap Gate Criteria

### 1.1 Filesystem-as-API (ADR-004)

Bootstrap is **viable** when ALL of the following are true:

| # | Check | Method |
|---|-------|--------|
| G1 | Venture directory created with canonical structure | `ls ventures/<id>/` |
| G2 | `venture.toml` parses without error | `cat` + manual TOML validation |
| G3 | `state.json` is valid JSON with required keys | `node -e "JSON.parse(...)"` |
| G4 | WAL file exists (`wal/current.jsonl`) | `ls` |
| G5 | Knowledge dir created (`knowledge/local/`) | `ls` |
| G6 | No external dependencies installed | `cat package.json` → deps: [`events` only] |
| G7 | CLI can `list` and `show` the new venture | `npx tsx tools/cli/venture.ts list` |

### 1.2 Gate Result Format

```
BOOTSTRAP GATE: ventures/saas-2026-test-bootstrap/
├── G1 directory: PASS
├── G2 toml parse: PASS
├── G3 state.json: PASS
├── G4 wal file: PASS
├── G5 knowledge: PASS
├── G6 no deps: PASS
└── G7 cli list: PASS

RESULT: ALL PASS → Bootstrap viable. Code may proceed.
```

If ANY check fails → bootstrap is NOT viable. Code is BLOCKED.

---

## 2. Bootstrap Sequence (Minimal Viable Path)

```
┌─────────────────────────────────────────────────────────┐
│  VENTURE-OS BOOTSTRAP SEQUENCE                          │
│  No code until all gates pass                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Step 1: Verify Foundation (run once per OS install)    │
│  ┌───────────────────────────────────────────────────┐  │
│  │ □ blueprint/foundation.md exists + unmodified     │  │
│  │ □ All 10 ADRs accepted                           │  │
│  │ □ lib/workflow-types.ts compiles                  │  │
│  │ □ lib/workflow-runner.ts compiles                 │  │
│  │ □ lib/compiler.ts compiles                        │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  Step 2: Verify CLI Bootstrap (run once per OS install) │
│  ┌───────────────────────────────────────────────────┐  │
│  │ □ tools/cli/venture.ts compiles                   │  │
│  │ □ tools/cli/venture.ts init creates dir structure │  │
│  │ □ tools/cli/venture.ts list shows new venture     │  │
│  │ □ tools/cli/venture.ts show reads state.json      │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  Step 3: Verify Workflow Engine (run per workflow add)  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ □ YAML parser reads workflow.yaml                 │  │
│  │ □ Step execution produces outputs                 │  │
│  │ □ WAL append records execution                    │  │
│  │ □ Gate check reads WAL                            │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  Step 4: Verify Compiler Engine (run per compiler add)  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ □ Mustache renders template with context          │  │
│  │ □ Output written to compiled/                     │  │
│  │ □ Bilingual markers present in output             │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  Step 5: First Venture Bootstrap (per new venture)      │
│  ┌───────────────────────────────────────────────────┐  │
│  │ □ venture init <name> completes G1–G7             │  │
│  │ □ decision new creates valid decision file        │  │
│  │ □ event log records events                        │  │
│  │ □ workflow run executes without error             │  │
│  │ □ compile generates non-empty output              │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Filesystem Contracts (Immutable)

These contracts are derived from ADR-004 and P1. They NEVER change without a new ADR.

### 3.1 Venture Directory Contract

```
ventures/{type}-{YYYY}-{kebab-slug}/
├── venture.toml        # INI-like config (hand-parsed)
├── state.json          # Runtime state (JSON)
├── workspace/          # Founder scratch space (any format)
├── artifacts/          # Research inputs
│   ├── market-research/
│   └── compiled/       # Compiler outputs
├── decisions/          # Markdown + YAML frontmatter
├── knowledge/
│   └── local/          # Venture-specific knowledge files
└── wal/
    └── current.jsonl   # Append-only event log
```

**Rules:**
- `venture.toml` is the config key: `[id]`, `[lifecycle]`, `[state]` sections
- `state.json` is the runtime mirror: `current_phase`, `phase_label`, `status`, `gates_passed[]`, `decisions_count`, `events_count`
- `wal/current.jsonl` is append-only: NEVER truncate, NEVER reorder
- `decisions/` files use YAML frontmatter with `problem:` as source of truth

### 3.2 File Format Contracts

| File | Format | Encoding | Required Keys |
|------|--------|----------|---------------|
| `venture.toml` | TOML subset | UTF-8 | `[id].name`, `[id].id`, `[id].type`, `[id].created_at`, `[lifecycle].current_phase`, `[lifecycle].phase_label`, `[state].status`, `[state].first_start` |
| `state.json` | JSON | UTF-8 | `current_phase`, `phase_label`, `status`, `created_at`, `updated_at`, `gates_passed`, `decisions_count`, `events_count` |
| `wal/*.jsonl` | JSONL | UTF-8 | `{ts, type, payload}` per line |
| `decisions/*.md` | Markdown + YAML FM | UTF-8 | `id`, `venture_id`, `phase`, `type`, `status`, `created_at`, `title`, `problem` |
| `workflows/*/workflow.yaml` | YAML | UTF-8 | `id`, `name`, `description`, `schema_version`, `lifecycle_phases[]`, `steps[]` |
| `compilers/*/compiler.yaml` | YAML | UTF-8 | `id`, `name`, `version`, `inputs[]`, `outputs[]`, `steps[]` |

### 3.3 Naming Contracts

| Artifact | Pattern | Example |
|----------|---------|---------|
| Venture ID | `{type}-{YYYY}-{kebab-slug}` | `saas-2026-ai-chatbot-platform` |
| Decision ID | `decision-{slug}-{YYYYMM}` | `decision-ai-quality-vs-ui-202607` |
| Event | JSONL raw (no file naming) | `current.jsonl` (append-only) |
| Compiler ID | kebab-case | `business-plan`, `pitch-deck` |
| Workflow ID | kebab-case | `market-research` |
| Plan file | `phase-{NN}-{slug}.md` | `phase-01-market-research.md` |

### 3.4 State Schema (Must-Have Keys)

```json
{
  "current_phase": "01",        // Two-digit string
  "phase_label": "IDENTIFY",    // UPPERCASE
  "status": "active",           // active|completed|stalled|exited
  "created_at": "20260101",     // YYYYMMDD
  "updated_at": "20260101",     // YYYYMMDD
  "gates_passed": [],           // array of gate IDs
  "decisions_count": 0,         // integer counter
  "events_count": 0             // integer counter
}
```

---

## 4. Bootstrap Verification Script

This is the canonical verification sequence. Run before ANY module is coded.

```bash
#!/usr/bin/env bash
# venture-os/bootstrap.sh
# Exit 0 = all gates pass. Exit 1 = bootstrap blocked.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PASS=0; FAIL=0

check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  ✓ $label"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $label"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== VentureOS Bootstrap Gate ==="

# Phase 1: Foundation
echo ""
echo "[Phase 1] Foundation"
check "foundation.md exists" test -f "$ROOT/blueprint/foundation.md"
check "All ADRs exist" test "$(ls adr/*.md | wc -l)" -eq 10
check "lib/workflow-types.ts compiles" test -f "$ROOT/lib/workflow-types.ts"
check "lib/workflow-runner.ts compiles" test -f "$ROOT/lib/workflow-runner.ts"
check "lib/compiler.ts compiles" test -f "$ROOT/lib/compiler.ts"

# Phase 2: CLI
echo ""
echo "[Phase 2] CLI"
check "tools/cli/venture.ts exists" test -f "$ROOT/tools/cli/venture.ts"
check "tsconfig.json exists" test -f "$ROOT/tools/tsconfig.json"

# Phase 3: Workflow Engine
echo ""
echo "[Phase 3] Workflow Engine"
check "workflows/research/market-research/ exists" test -d "$ROOT/workflows/research/market-research"
check "workflow.yaml exists" test -f "$ROOT/workflows/research/market-research/workflow.yaml"

# Phase 4: Compilers
echo ""
echo "[Phase 4] Compilers"
for d in "$ROOT"/workflows/compiler/*/; do
  name=$(basename "$d")
  check "compiler/$name/compiler.yaml" test -f "$d/compiler.yaml"
done

# Phase 5: Sample Venture
echo ""
echo "[Phase 5] Sample Venture"
if [ -d "$ROOT/ventures" ]; then
  for v in "$ROOT"/ventures/*/; do
    id=$(basename "$v")
    check "$id/venture.toml" test -f "$v/venture.toml"
    check "$id/state.json" test -f "$v/state.json"
    check "$id/wal/current.jsonl" test -f "$v/wal/current.jsonl"
  done
fi

echo ""
echo "=== Result: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] && echo "BOOTSTRAP VIABLE" || echo "BOOTSTRAP BLOCKED"
exit "$FAIL"
```

**Run this BEFORE implementing any module.** If it exits 0 → bootstrap is viable. If it exits non-zero → fix blockers first.

---

## 5. Implementation Order (After Bootstrap Passes)

Once bootstrap is viable, implement modules in this dependency order:

```
1. lib/toml-parser.ts          (foundation parsing)
2. tools/cli/venture.ts        (CLI user-facing)
3. lib/workflow-runner.ts      (DAG execution)
4. lib/compiler.ts             (Mustache rendering)
5. lib/workflow-chain.ts       (sequential chaining)
6. lib/portfolio.ts            (cross-venture ops)
7. lib/wal/index.ts            (WAL public API)
8. lib/wal/reader.ts           (line-by-line reader)
9. lib/wal/compaction.ts       (merge + retention)
10. lib/graph/index.ts         (knowledge graph)
11. lib/graph/store.ts         (persistence)
```

**Rules for each module:**
- Write the module
- Write its bootstrap gate test (G1–G7 for CLI, specific gates for engines)
- Run `bootstrap.sh`
- Only proceed to next module if bootstrap stays green

---

## 6. First Venture Walkthrough (Proof of Concept)

After all modules pass bootstrap, run this exact sequence to prove end-to-end viability:

```bash
# Initialize
npx tsx tools/cli/venture.ts init "First Venture" --type startup
# → Creates: ventures/startup-2026-first-venture/
# → Bootstrap G1–G7 must PASS

# Decision
npx tsx tools/cli/venture.ts decision new startup-2026-first-venture strategic \
  --title "Target market" \
  --problem "Should we target SMB or enterprise?"
# → Creates: decisions/decision-target-market-202607.md

# Workflow
npx tsx tools/cli/venture.ts workflow run startup-2026-first-venture research/market-research
# → Executes 5 steps
# → Appends to wal/current.jsonl

# Compile
npx tsx tools/cli/venture.ts compile startup-2026-first-venture business-plan
# → Outputs: compiled/{id}_business-plan.md

# Verify
npx tsx tools/cli/venture.ts show startup-2026-first-venture
# → Shows full state: phase, decisions, latest event
```

**Success criteria:** All 5 commands execute without error. Final output contains non-empty business plan.

---

## 7. Bootstrap BLOCK Conditions

Code implementation is **BLOCKED** if ANY of:

- B1: `blueprint/foundation.md` is modified (immutable)
- B2: Any ADR (001–010) is modified without new ADR
- B3: `bootstrap.sh` fails (exit non-zero)
- B4: `venture init` does not create all required files
- B5: Dependencies added to `package.json` beyond `events`, `toml`, `yaml` parsers
- B6: Workflow or compiler YAML fails validation
- B7: `compile` produces empty or malformed output

---

## 8. Bootstrap Unlock Conditions

Code implementation is **UNLOCKED** only when ALL of:

- U1: `bootstrap.sh` exits 0
- U2: First venture walkthrough (§6) completes end-to-end
- U3: At least 1 decision can be created and read
- U4: At least 1 workflow runs and appends WAL events
- U5: At least 1 compiler produces non-empty output

After U1–U5 pass: Phase 01 is **operational**. Modules for Phase 02+ can be implemented.

---

## 9. Immutable Constraints (Never Change Without New ADR)

| ID | Constraint | Source |
|----|-----------|--------|
| C1 | Filesystem is the database | ADR-004 |
| C2 | Venture directory is the venture unit | ADR-008 |
| C3 | CLI is primary interface; API is derivative | ADR-005 |
| C4 | Append-only WAL, never truncate/rewrite | ADR-003 |
| C5 | Blueprint is immutable after commit | ADR-002 |
| C6 | Decision files use YAML frontmatter | ADR-007 |
| C7 | Monorepo, not multirepo | ADR-001 |
| C8 | 9-phase lifecycle is universal contract | ADR-006 |
| C9 | Extensions are additive, not subtractive | ADR-009 |
| C10 | Knowledge graph is universal substrate | ADR-010 |

---

## 10. Bootstrap Refresh Rules

If bootstrap.sh fails after a module is coded:

1. DO NOT modify `bootstrap.sh` to hide the failure
2. Identify which gate fails
3. Fix the underlying issue (code or setup)
4. Re-run `bootstrap.sh`
5. If a gate test needs to change → that's a NEW gate, not a gate modification → file a new ADR

---

## Summary

**Bootstrap = Foundation Verification Gate.**

```
Before code:  Run bootstrap.sh → must PASS
After module: Run bootstrap.sh → must still PASS
Before ship:  Run full walkthrough (§6) → must PASS
```

Bootstrap is not a one-time event. It runs against every state change.

---

> *This file is immutably referenced by ADR-004. Modifications require ADR-011+.*
