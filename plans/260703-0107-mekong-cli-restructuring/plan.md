---
title: "Mekong/ Directory Restructuring Plan"
description: "Clarify mekong/ scope, split concerns, fix bootstrap location"
status: pending
priority: P2
effort: 3h
branch: fix/layer2-ruff-tech-debt
tags: [architecture, refactor, mekong, bootstrap, cleanup]
created: 2026-07-03
---

## Current State — What mekong/ Contains

| Directory | Content | Role |
|-----------|---------|------|
| `mekong/bootstrap/` | `index.cjs`, `manifest-builder.cjs`, `self-heal.cjs`, `config-sync.cjs`, `make-managed-hooks.cjs`, `managed-hooks.json`, `reports/` | Init system: asset inventory + self-heal + skill merge |
| `mekong/adapters/` | 5 shell scripts (`cc-cli.sh`, `gemini-cli.sh`, etc.) + `llm-providers.yaml` + `registry.sh` | LLM provider dispatch scripts |
| `mekong/commands/` | 7 `.md` files (`arch.md`, `kanban.md`, `kit.md` + subdirs) | Engine command docs consumed by manifest-builder |
| `mekong/skills/` | 15 `SKILL.md` entries + `kanban.py` | Target for config-sync merges |
| `mekong/workflows/` | 8 `.md` workflow docs | Process/protocol docs |
| `mekong/orchestrator/` | Python: `idea_loop.py`, `safety.py`, `tools.py`, `context_manager.py` + tests | Autonomous ideation loop (Plan→Execute→Verify) |
| `mekong/infra/` | `architecture.yaml`, `scaffold.sh`, CF templates | Cloudflare deploy scaffolding |
| `mekong/mcp.json` | MCP server config | Misc config |

**What it's trying to do:** `mekong/` is the "engine root" — the layer beneath `.claude/` (CC CLI harness) and `.agent/` (Antigravity). It holds: (1) CLI bootstrap/init tooling, (2) adapter scripts for multiple AI runtimes, (3) engine-owned commands and skills, (4) the Python orchestrator for autonomous execution, and (5) deploy infra templates.

## Problem: Responsibility Overload

`mekong/` currently conflates 4 distinct concerns in one tree:
1. **Bootstrap** (runtime init — only needed when running `mekong init`)
2. **Adapters** (provider runtime — needed by wrapper scripts)
3. **Engine content** (skills/commands/workflows — static docs consumed by discovery)
4. **Orchestrator** (Python runtime — autonomous execution engine)

These have different lifecycles, runtimes (Node vs Python), and consumers.

## Proposed Structure

```
mekong/
├── README.md                    # Engine overview (renamed from NAMESPACE.md)
├── CLAUDE.md                    # Engine contract (keep as-is)
├── ARCHITECTURE.md              # Architecture doc (keep as-is)
├── adapters/                    # KEEP — provider runtime scripts
│   ├── cc-cli.sh
│   ├── gemini-cli.sh
│   ├── opencode-cli.sh
│   ├── aider-cli.sh
│   ├── registry.sh
│   └── llm-providers.yaml
│
├── skill-registry/              # NEW — merge of current skills/ + commands/ + workflows/
│   ├── skills/                  #   Current mekong/skills/ (15 SKILL.md entries)
│   ├── commands/                #   Current mekong/commands/ (7 docs)
│   └── workflows/               #   Current mekong/workflows/ (8 docs)
│
├── engine/                      # KEEP — 3-layer deploy templates
│   ├── archives/
│   ├── deployment/
│   ├── deployment-archives/
│   ├── memory/
│   ├── templates/
│   └── ...
│
├── autopilot/                   # RENAME from orchestrator/ — Python autonomous loop
│   ├── idea_loop.py
│   ├── safety.py
│   ├── tools.py
│   ├── context_manager.py
│   ├── __init__.py
│   └── tests/
│       ├── test_cf_filter.py
│       └── test_cf_filter_integration.py
│
└── bootstrap/                   # KEEP IN PLACE — init system stays here
    ├── index.cjs
    ├── manifest-builder.cjs
    ├── self-heal.cjs
    ├── config-sync.cjs          # Now scans skill-registry/ instead of scattered roots
    ├── make-managed-hooks.cjs
    ├── managed-hooks.json
    ├── manifest.json            # Generated, OK to keep
    └── reports/                 # Generated reports (gitignored candidate)
```

## Key Decisions

### 1. bootstrap/ stays in mekong/bootstrap/ (DON'T move)
- **Why:** `bin/mekong` references `mekong/bootstrap/index.cjs` as source of truth (CLAUDE.md:19). `ME_KONG_ROOT` env var can override, but the default path-resolution in all 4 `.cjs` files uses `path.dirname(__dirname)` → `path.dirname()` × 2 to reach `mekong/`. Moving bootstrap breaks every tool.
- **Path to change if moved:** `bin/mekong`, `mekong/bootstrap/index.cjs:21`, `config-sync.cjs:22`, `self-heal.cjs:20`, `make-managed-hooks.cjs`.

### 2. Merge skills/ + commands/ + workflows/ → skill-registry/
- **Why:** All three are static doc content consumed by `manifest-builder.cjs` and displayed to users. No semantic difference in how they're consumed.
- **Impact:** `manifest-builder.cjs` scans: `mekong/skills`, `mekong/commands`, `mekong/workflows`, `.agent/subagents`, `.claude/agents`, `.claude/hooks`, `scripts/`. After merge: scans `mekong/skill-registry/skills`, `mekong/skill-registry/commands`, `mekong/skill-registry/workflows` + same external roots.
- **config-sync.cjs** writes to `mekong/skills/<slug>/SKILL.md` — this needs to write to `mekong/skill-registry/skills/<slug>/SKILL.md` instead.

### 3. Rename orchestrator/ → autopilot/
- **Why:** "autopilot" better describes what this does (autonomous P→E→V loop). "orchestrator" is overloaded in the codebase (shell scripts also call themselves orchestrators in comments).
- **Low risk:** Only Python code imports from `mekong.orchestrator`. Update 4 imports in `idea_loop.py`.

### 4. No symlinks — .claude/ stays flat
Per CLAUDE.md root: "CC CLI reads `.claude/skills/` and `.claude/commands/` directly. NO symlinks." `.claude/skills/` and `.claude/commands/` remain as primary discovery paths. `mekong/skill-registry/` is a second source that `config-sync.cjs` merges FROM, not a symlink target.

## Priority Order (Phased)

### Phase 1: Rename orchestrator/ → autopilot/ (30 min, low risk)
- Rename directory
- Update imports in: `autopilot/idea_loop.py` (4 `from .module import X`)
- Update references in: `ARCHITECTURE.md`, `bootstrap/manifest-builder.cjs` (scans `.agent/subagents` and `.claude/agents` — NOT orchestrator, no change needed)
- Run `python3 -m pytest mekong/orchestrator/tests/` to verify

### Phase 2: Merge skills/commands/workflows → skill-registry/ (1h, medium risk)
- Create `mekong/skill-registry/` with `skills/`, `commands/`, `workflows/` subdirs
- Move all content from `mekong/skills/`, `mekong/commands/`, `mekong/workflows/` into their new homes
- Update `manifest-builder.cjs` scan paths (3 searches for `mekong/skills`, `mekong/commands`, `mekong/workflows`)
- Update `config-sync.cjs` write target (`mekong/skills/` → `mekong/skill-registry/skills/`)
- Update `self-heal.cjs` scan paths if any reference engine content
- Update `ARCHITECTURE.md` and `CLAUDE.md`
- Verify: `node mekong/bootstrap/manifest-builder.cjs` still produces correct manifest

### Phase 3: Clean up redundant/redundant roots (30 min, low risk after Phase 2)
- Delete empty `mekong/skills/`, `mekong/commands/`, `mekong/workflows/` dirs
- Move `mekong/mcp.json` to root or engine/ (it's a standalone config, not content)
- Add `mekong/bootstrap/reports/` to `.gitignore` (generated JSON, not source)
- Archive `.claude-backup/` and `.claude-skills/` if verified stale (self-heal already flags these)

### Phase 4: Add ruff/lint to bootstrap CI gate (30 min, low risk)
- The branch `fix/layer2-ruff-tech-debt` suggests linting is the broader goal
- Add `ruff check mekong/` to the validation that runs alongside `manifest-builder.cjs`
- This ensures bootstrap changes don't accumulate tech debt

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| `bin/mekong` hardcodes old paths | Medium | High | Grep `mekong/skills` and `mekong/commands` in `bin/` and `.claude/hooks/` before Phase 2 |
| config-sync writes to wrong target | Medium | High | Dry-run first (`node mekong/bootstrap/config-sync.cjs` without `--write`), verify output paths |
| manifest.json stale after restructure | Low | Medium | Regenerate via `node mekong/bootstrap/index.cjs --fix` post-move |
| __pycache__ in autopilot/tests/ | Certain | Low | Already present; add to `.gitignore` or cleanup |

## Backwards Compatibility

- `ME_KONG_ROOT` env override still works (all 4 cjs files respect it)
- No API/contract changes — purely internal reorganization
- `mekong init --self --fix` regenerates manifest.json, so stale manifests self-heal

## Test Matrix

| Test | How |
|------|-----|
| bootstrap works post-move | `node mekong/bootstrap/index.cjs --self` |
| manifest correct | `node mekong/bootstrap/manifest-builder.cjs --json \| jq '.skills | length'` |
| config-sync dry-run | `node mekong/bootstrap/config-sync.cjs` (no `--write`) |
| config-sync write | `node mekong/bootstrap/config-sync.cjs --write` on test branch |
| orchestrator→autopilot tests | `python3 -m pytest mekong/autopilot/tests/` |
| adapter scripts still run | `bash mekong/adapters/registry.sh` |

## Rollback

Each phase is independently reversible:
- Phase 1: `git mv autopilot/ orchestrator/` + revert 4 import lines
- Phase 2: `git mv skill-registry/skills skills/` etc. + revert path strings in 3 cjs files
- No database, no deploy, no user-facing changes — rollback is `git revert`
