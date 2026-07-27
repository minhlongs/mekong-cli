---
description: "Guardian term limit inspection and election management"
argument-hint: "[status | elect <guardian-id>]"
allowed-tools: Read, Bash, Glob
---

# /ck-govern term — Guardian Term Limits

Inspect current Guardian term status and initiate elections.

## Usage

```bash
mekong ck-govern term status
mekong ck-govern term elect <guardian-id>
```

## Rules

- Guardian term: 1 year max, 2 terms maximum (ZENOS Art 7)
- Term expiry blocks L1/L2 amendment execution
- L3 (soft) proposals remain executable during expired terms to prevent deadlock
- No Guardian elected: founder acts as default Guardian per F1 transition Art 10

## Source of Truth

- `src/mekong/constitution/term_limits.py` — GuardianRegistry
- `mekong/constitution/ZENOS-COMMONS.md` Art 6 — Anti-Capture Mechanisms table
