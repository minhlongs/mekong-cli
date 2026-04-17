---
audit_date: 2026-04-17
spec_count: 443
py_module_count: 43
live: 4
spec_only: 435
ghost: 39
---

# Command Audit Index

Last run: **2026-04-17**

> Note: `.claude/commands/_audit.md` is gitignored (per repo policy — `.claude/` is private namespace).
> This file (`docs/command-audit/audit-index.md`) is the public-facing equivalent.
> Re-run `python3 docs/command-audit/audit-script.py` to refresh both.

## Counts

| Metric | Value |
|--------|-------|
| Markdown specs (`.claude/commands/**/*.md`) | 443 |
| Python modules (`src/commands/*.py`) | 43 |
| LIVE (spec + module match, unique modules) | 4 |
| SPEC_ONLY (spec, no module) | 435 |
| GHOST (module, no spec) | 39 |

## Gap vs README Claim

README claims: **443 commands**
Audited live (unique Python modules): **4**
Gap: **439** commands are spec-only or ghost (not end-to-end shipped)

See [README.md](README.md) for full explanation of why this gap is expected and intentional.

## Links

- [README.md](README.md) — how to read this audit
- [live-commands.md](live-commands.md) — 4 verified-live entries
- [spec-only-commands.md](spec-only-commands.md) — 435 CC CLI template specs
- [ghost-commands.md](ghost-commands.md) — 39 Python modules without spec docs
- [mapping-table.csv](mapping-table.csv) — 482 rows, machine-readable
