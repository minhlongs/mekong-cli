# 🏯 Unified Agent Architecture

> **Version**: v6.0.0 | **Date**: 2026-04-29
> **ClaudeKit-Engineer** + **Antigravity IDE** Unified Framework
> **Status**: PRODUCTION (post-cleanup) | Layer Contract enforced

---

## 📐 Layer Contract (NEW 2026-04-29)

| Layer | Path | Owns | Boundary |
|-------|------|------|----------|
| **Layer 1** Global ClaudeKit | `~/.claude/` | Universal primitives: 16 agents, ~57 universal skills, 14 commands, Binh Pháp + Manus L1-L7 rules | NO mekong-specific code |
| **Layer 2** Project Mekong | `~/mekong-cli/.claude/` | Domain extension: 6 mekong-only agents, ~501 domain skills, 338+ domain commands, factory contracts, clipmart | NO duplicate Layer-1 primitives |
| **Layer 3** Antigravity (Gemini) | `~/mekong-cli/.agent/` | 106 task-based subagents + 40 workflows for Gemini IDE | Parallel ecosystem, separate concern |

**Forbidden:** Layer 2 MUST NOT redefine Layer 1 primitives. Pre-commit guard enforces.

---

## 📁 Directory Structure (post-cleanup)

```
mekong-cli/
├── .claude/                    # Layer 2 — ClaudeKit-Engineer (Project)
│   ├── agents/         (6)     # Layer-2 only: agentic-overlord, content-agent, docs-writer-agent, file-scout-agent, git-ops-agent, shell-runner-agent
│   ├── commands/      (338)    # Mekong domain commands (Studio/Founder/Business/Product/Engineering/Ops)
│   ├── skills/        (501)    # Domain skills (post-dedup of 56 IDENTICAL with global)
│   ├── hooks/                  # Project hooks (statusline, antigravity)
│   ├── rules/                  # Project rules (m3-strict, cc-cli-input-rules, ...)
│   └── settings.json
│
├── .agent/                     # Layer 3 — Antigravity IDE (Gemini)
│   ├── subagents/    (106)
│   ├── workflows/     (40)
│   └── crews/
│
├── packages/                   # Public SDK (PUBLIC repo boundary OK)
├── factory/contracts/          # 567 JSON machine contracts
├── clipmart/                   # Paperclip Agent Companies marketplace
├── apps/                       # PRIVATE — DO NOT commit (algo-trader, sophia, well, ...)
├── mekong/daemon/              # PRIVATE — internal CTO brain
└── GEMINI.md                   # Cross-tool shared memory (Layers 1-3)
```

---

## 📊 Statistics (live counts post-cleanup 2026-04-29 21:11)

| Metric | Layer 1 (Global) | Layer 2 (Mekong) | Layer 3 (Gemini) | Total Distinct |
|--------|------------------|-------------------|-------------------|---------------|
| Agents | 16 | 6 | 106 | **128** |
| Skills | 151 | 501 | 6 categories | **652+ distinct** |
| Commands | 18 | 338 | n/a | **356** |
| Workflows | n/a | n/a | 40 | **40** |
| Rules (Binh Pháp + Manus L1-L7) | shared | inherited | inherited | **18 files** |

**Cleanup audit (260429-2108):** Removed 56 IDENTICAL skill copies from Layer 2 (auto-fall-through to Layer 1). 6 DIVERGENT skills + 32 incomplete (missing SKILL.md) kept for manual review.

---

## 🔗 Synced Components

| Component | Layer 1 | Layer 2 | Layer 3 | Status |
|-----------|---------|---------|---------|--------|
| **Binh Pháp** | `~/.claude/rules/binh-phap-*.md` | `.claude/agents/binh-phap-strategist.md` | `.agent/subagents/hubs/binh-phap-hub.md` | ✅ SYNCED |
| **Memory** | `~/.claude/memory/` | `agent-memory/` | `GEMINI.md` | ✅ SHARED |
| **Subagent dispatch** | global agents auto-discovered | mekong agents extend | Gemini parallel | ✅ |

---

## 🎯 Mekong-First Policy

User Assertion #1: All slash commands dispatch to mekong CLI engine.

When CWD = `~/mekong-cli`, CC CLI discovers `.claude/commands/` (338 cmds) + falls through to `~/.claude/commands/` (18 cmds, only those NOT shadowed). Total runtime surface: 356.

When CWD = elsewhere, only global 18 commands available. Hence `mekong` wrapper always launches from `~/mekong-cli` root.

---

## 📦 Product Catalog

| Tier | Product | Price |
|------|---------|-------|
| FREE | VSCode Pack | $0 |
| Basic | AI Skills, Auth | $27 |
| Pro | AgencyOS Pro | $197 |
| Enterprise | AgencyOS Enterprise | $497 |

**Total Catalog Value:** $916+

---

## 🛡️ CI Guard (Phase G — Pending)

To prevent future drift:
- `.husky/pre-commit` runs `scripts/audit-architecture.sh`
- Fails if Layer 1 primitive modified inside Layer 2
- Fails if counts in this doc lệch >0 vs filesystem reality

Status: NOT yet implemented.

---

## 🏯 Core Wisdom

> **"Bất chiến nhi khuất nhân chi binh"**
> Win without fighting — the highest form of victory.

---

_Unified Architecture by AgencyOS | v6.0.0 | 2026-04-29 (post-claudekit-layer-cleanup)_
