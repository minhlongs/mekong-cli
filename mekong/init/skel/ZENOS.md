# {{NAME}} — ZenOS Economic Particle

**Born:** {{DATE}}
**Mission:** {{MISSION}}
**Guardian:** {{FOUNDER}}

---

## Constitution

This project is a ZenOS Economic Particle governed by the
[ZenOS Constitution](../../mekong/constitution/ZENOS.md) (9 articles).

**Key articles:**
1. **Human > AI > Capital** — technology serves people
2. **Mission > Revenue** — purpose before profit
3. **Transparency > Growth** — every decision explainable
4. **Freedom > Lock-in** — users own their data
5. **AI Shall Not Rule** — humans remain in control

---

## Org Structure

See `AI/` directory for your C-Level agents (CEO, CTO, CMO, CFO, CSO, CHRO, COO)
and `AI/org/` for Department Heads.

## Workflows

See `workflows/` for cross-department pipelines.

## Setup

```bash
# CK init (if not already done)
npx ck init -g --kit engineer --yes --force

# Verify compliance
mekong audit . --fix
```
