# Phần 1: Tổng Quan Kiến Trúc — Binh Pháp × Mekong-CLI

> Generated: 2026-07-25 | Status: DRAFT

---

## 1. Brainstorm Contract (Accepted)

| Field | Content |
|-------|---------|
| **Outcome** | Deep-mapped restructuring plan: 13 chương Binh Pháp -> mekong-cli module tree |
| **Constraints** | (1) Không break existing CLI commands (2) Fable 5 / Opus 4.8 dual-path routing giữ nguyên runtime signature (3) Single source of truth = binh_phap_escalation.py (4) ZuneF gateway scope riêng cho team |
| **Non-goals** | (1) Không implement code (2) Không migrate company.json schema (3) Không thay đổi .claude/settings.json rules (chỉ note) |
| **Acceptance** | (1) 6 phần đều có output (2) Mỗi phần có trade-off comparison (3) Files: docs/binh-phap-mapping/01-06-*.md |

## 2. Current State Assessment

### Relevant Tree
```
mekong-cli/
├── src/
│   ├── cli/                        # Typer app factory + sub-commands
│   │   ├── app_setup.py            # build_app() wires 40+ sub-apps
│   │   ├── binh_phap_commands.py
│   │   ├── autonomous_commands.py
│   │   └── sdlc/                   # Design / Code / Deploy / Spec
│   ├── core/                       # Shared runtime
│   │   ├── binh_phap_escalation.py # PROVIDER ROUTING (single source of truth)
│   │   ├── binh_phap_dispatcher.py # topology -> PEV bridge
│   │   └── topology.py             # 3D engine: vertical/horizontal/diagonal
│   └── binh_phap/                  # Strategic layer
│       └── topology.py
├── .claude/
│   ├── commands/                   # mk-* slash commands
│   └── settings.json               # modelRouting (legacy, still referenced by hooks)
└── docs/                           # Target: docs/binh-phap-mapping/
```

### Pain Points
- Model routing split 3 nơi -> đã consolidate vào Fable-only trong escalation
- No structured plan cho mapping Binh Phap into code
- mekong/ directory has 4 concerns conflated (bootstrap/adapters/skills/orchestrator)

## 3. 13 Chương -> Module Mapping

| Chương | Tên | Module Target | LLM Tier |
|--------|-----|---------------|----------|
| 1 | Tính Địa | src/commercial/ (NEW) | Fable 5 |
| 2 | Tình Hình | src/governance/ | Fable 5 |
| 3 | Chiến Lược | src/cli/idea_commands/ | Opus 4.8 |
| 4 | Thế Lực | src/cli/cook_command.py + sdlc/ | Opus 4.8 |
| 5 | Căn Cứ | src/finance/ (NEW) | Fable 5 |
| 6 | Trống Hư | src/research/ (NEW) | Opus 4.8 |
| 7 | Chuyển | src/cli/sdlc/deploy/ + swarm | Opus 4.8 |
| 8 | Biến | src/cli/schedule_commands.py | Opus 4.8 |
| 9 | Địa Hình | src/governance/ + particle | Opus 4.8 |
| 10 | Căn Thủ | src/observability/ (NEW) | Opus 4.8 |
| 11 | Hỏa Công | src/marketing/ (NEW) | Fable 5 |
| 12 | Xâm Phạm | src/cli/workflow_commands.py | Fable 5 |
| 13 | Hỗn Hợp | src/daemon/jidoka.py | Opus 4.8 |

## 4. Trade-off Analysis

| Approach | Keeps Current | Consolidates Routing | Commercial First |
|----------|--------------|---------------------|------------------|
| A: Incremental | YES | Partial | NO |
| B: Big-bang refactor | NO | Full | YES |
| **C: Hybrid (RECOMMENDED)** | **Existing modules untouched** | **escalation.py as single source** | **Ch1/2/5/11/12 -> Fable, rest -> Opus** |

## 5. Recommendation

**Hybrid approach — minimal delta, maximum clarity:**

1. KEEP existing src/cli/*, src/core/* structure — no renames
2. ADD src/commercial/, src/finance/, src/research/, src/marketing/, src/governance/ directories
3. MOVE dispatcher logic deeper: topology.py stays in src/core/binh_phap/, dispatcher calls it
4. CREATE docs/binh-phap-mapping/ with this plan + per-chapter YAML contracts

## 6. Next Steps (Phần 2)

- Vertical dispatch flow (swot -> plan -> cook -> test -> deploy -> audit)
- Battle groups (alpha/beta/gamma/delta) dependency graph
