# Command Audit — Executive Summary

> Audit date: 2026-04-17
> Methodology: structural cross-reference (`find` + basename matching), no execution required.

## How to Read This Audit

Mekong CLI has two distinct namespaces for commands:

| Namespace | Location | Purpose |
|-----------|----------|---------|
| **Markdown specs** | `.claude/commands/**/*.md` | CC CLI discovery — these are prompt templates / spec files |
| **Python modules** | `src/commands/*.py` | Live executable backend modules registered with the FastAPI/Typer CLI |

A command is **LIVE** only when **both** a spec `.md` AND a Python module exist with matching names.
A command is **SPEC_ONLY** when only the `.md` exists (aspirational / CC CLI pass-through).
A command is **GHOST** when only the Python module exists (undocumented / internal helper).

## Audit Results (2026-04-17)

| Metric | Count |
|--------|-------|
| Markdown specs (`.claude/commands/**/*.md`) | **443** |
| Python modules (`src/commands/*.py`) | **43** |
| LIVE (spec + module match, unique modules) | **4** |
| SPEC_ONLY (spec, no Python module) | **435** |
| GHOST (Python module, no spec) | **39** |
| Total CSV rows | **482** |

## Gap vs README Claim

README / CLAUDE.md claims: **"342+ commands"** (or "443 spec files").
Audited live (end-to-end, Python-backed): **4 unique modules**.

> **Gap: 439 commands are spec-only or ghost — not end-to-end shipped.**

This is expected. Mekong CLI follows a "spec-first" philosophy:
- The 443 `.md` specs are CC CLI prompt templates — they work as LLM instructions without Python backends.
- The 43 Python modules provide programmatic CLI subcommands for automation, billing, and RaaS operations.
- "Live" in this audit = Python module exists AND a spec doc exists (both sides covered).

## Important Clarification

Most `.claude/commands/*.md` specs **do NOT require** a Python module to function. They are dispatched
directly by Claude Code CLI (`claude`) as prompt templates. The Python modules in `src/commands/` are
a separate concern: they power `mekong <subcommand>` CLI operations (billing, sync, health, etc.).

The "443 live commands" claim in README refers to CC CLI-discoverable specs, not Python modules.
This audit separates these two populations explicitly for clarity.

## Files in This Directory

| File | Description |
|------|-------------|
| `README.md` | This file — executive summary |
| `live-commands.md` | Specs that have matching Python modules |
| `spec-only-commands.md` | Specs with no Python module (CC CLI templates) |
| `ghost-commands.md` | Python modules with no spec doc |
| `mapping-table.csv` | Machine-readable: all rows, easy to diff |

## Re-running the Audit

```bash
python3 docs/command-audit/audit-script.py --root .
```

## Taxonomy Definitions

| Status | Definition |
|--------|------------|
| `LIVE` | `.md` spec in `.claude/commands/` AND matching `src/commands/*.py` module |
| `SPEC_ONLY` | `.md` spec only — works as CC CLI prompt template, no Python backend |
| `GHOST` | `src/commands/*.py` only — implemented module, not yet documented in `.claude/commands/` |

## Recommended Actions (Post-Audit)

1. **Ghost modules (39)**: Add spec `.md` for each — these are shipped but undocumented for CC CLI users.
2. **SPEC_ONLY (435)**: Clarify in README that "443 commands" = CC CLI templates, not Python modules.
3. **LIVE count (4)**: Not a problem — it reflects the intentional separation of spec vs backend namespaces.
4. **Future**: Add frontmatter `status: live|spec-only|ghost` to all `.md` files for inline clarity.
