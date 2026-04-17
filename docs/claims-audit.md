# Claims Audit — Mekong CLI README

**Audit Date:** 2026-04-17  
**Auditor:** Phase A3 automated evidence count  
**Purpose:** Evidence ledger for every quantitative claim in README.md — traceable to file paths and commands.

---

## Evidence Table

| Claim (README before rewrite) | Evidence Command | Verified Count | Delta vs README | File Path |
|---|---|---|---|---|
| "22 departments" | `cat factory/contracts/layers.json \| python3 -c "..."` | 10 layers defined | README: 22, Reality: 10 defined, 7 named in copy | `factory/contracts/layers.json` |
| "385 pre-built workflow templates" | `find .claude/commands -name '*.md' \| wc -l` | 443 command markdown defs | README: 385 "templates", Reality: 443 command specs (not workflow templates) | `.claude/commands/` |
| "5,713 passing tests (1,263 TS + 4,450 Python)" | `python3 -m pytest --collect-only -q 2>/dev/null \| tail -1` | 7,041 Python tests collected | TS vitest currently failing (module not found). Python count higher than claimed. | `tests/`, `packages/*/tests/` |
| "300+ commands" | `find .claude/commands -name '*.md' \| wc -l` + `find src/commands -name '*.py' -not -name '_*' \| wc -l` | 443 command defs + 43 live Python modules | 443 command definitions exist; 43 are backed by live Python code | `.claude/commands/`, `src/commands/` |
| "248 Skills" (README architecture block) | `find .claude/skills -name 'SKILL.md' \| wc -l` | 197 SKILL.md files | README arch block: 248; CLAUDE.md: 542; Reality: 197 | `.claude/skills/` |
| "388 machine contracts" | `ls factory/contracts/commands/ \| wc -l` | 567 contract files | README undercounts: 567 actual (updated contracts shipped in later PRs) | `factory/contracts/commands/` |
| "206 commands" (README architecture block) | `find .claude/commands -name '*.md' \| wc -l` | 443 command defs | Architecture block (line ~149) uses stale 206 count | `.claude/commands/` |
| M1/M2 Ultra 32B-70B perf claim | N/A — no benchmark scripts found | 0 benchmark files | No `scripts/benchmark/` or `tests/perf/` directory | N/A — claimed not verified |
| "Autonomous operations engine (OpenClaw) runs 24/7" | `ls src/daemon/` | Scaffolded (heartbeat_scheduler.py, dispatcher.py) | No stress-test or 24h uptime proof in repo | `src/daemon/` |
| Agent count (19 Python agent files) | `ls src/agents/*.py \| wc -l` | 19 files (20 incl `__init__.py`) | Not directly claimed in README but backs "department" count | `src/agents/` |

---

## Layers (Departments) — Full List

From `factory/contracts/layers.json` v2.0.0:

| ID | Role | Status |
|----|------|--------|
| studio | VC Studio / Chairman | Defined |
| cto | CTO / Chief Architect | Defined |
| pm | Product Manager | Defined |
| dev | Developer / Tech Lead | Defined |
| worker | Worker / Atomic Executor | Defined |
| founder | Founder / CEO | Defined |
| business | Business Lead / GTM | Defined |
| product | Product Manager / Designer | Defined |
| engineering | Engineer / Tech Lead | Defined |
| ops | DevOps / Platform | Defined |

Total: **10 layers** across 2 chains (ROIaaS: studio→cto→pm→dev→worker; Legacy: founder→business→product→engineering→ops)

---

## Surviving Claims (post-rewrite)

| Claim | Verified Count | Evidence |
|---|---|---|
| Command definitions | 443 | `find .claude/commands -name '*.md' \| wc -l` |
| Live command modules (Python) | 43 | `find src/commands -name '*.py' -not -name '_*' \| wc -l` |
| Skill definitions | 197 | `find .claude/skills -name 'SKILL.md' \| wc -l` |
| Machine contracts (JSON) | 567 | `ls factory/contracts/commands/ \| wc -l` |
| Agent files | 19 | `ls src/agents/*.py \| wc -l` |
| Python tests collected | 7,041 | `python3 -m pytest --collect-only -q` |
| Business layers / departments | 10 | `factory/contracts/layers.json` |

---

## Notes

- TS test suite (vitest, packages/mekong-cli-core) failing locally due to ESM module resolution error. Test file count: ~228 files across packages. Pass count: pending CI.
- "385 templates" was never accurate: `.claude/commands/` are command specs, not workflow templates. Accurate label: "443 command definitions."
- CLAUDE.md `542 skill definitions` discrepancy: not counted in file system audit. Only SKILL.md files under `.claude/skills/` are counted (197). If `~/.claude/skills/` (global) are included the count may be higher — but those are not shipped in this repo.
- All verified counts frozen as of commit on `feat/readme-truthful-rewrite` branch, 2026-04-17.
