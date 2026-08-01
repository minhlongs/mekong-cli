---
description: "Execute right-to-fork export for ZenOS Commons"
argument-hint: "[export] [output-dir]"
allowed-tools: Read, Bash, Glob, Write
---

# /mk:govern fork — ZenOS Right to Fork

Execute the ZENOS Art 8 Right to Fork — export all member data as
standard JSON plus Git clone instructions for the forked repository.

## Usage

```bash
mekong ck-govern fork export [output-dir]
```

Defaults to `./zenos-fork-exports/` when no output directory is given.

## Guarantees (Protocol-Level, Not Policy)

1. No lock-in — all data in standard JSON
2. No penalty — voting power and trust score are carried over
3. Perpetual MIT license at the fork commit
4. 30-day notice period enforced programmatically

## Source of Truth

- `src/mekong/commons/fork.py` — ForkExecutor
- `src/mekong/constitution/member_registry.py` — member export
- `src/mekong/constitution/vote_engine.py` — voting history export
