# ZenOS Architecture: Article-to-Module Mapping

> Maps each ZENOS.md article to its implementing code module.
> See also: `ZENOS.md` (the constitution), `docs/03_constitution.md` through `docs/14_manifesto_review.md` (research basis).

---

## Mapping

| Article | Module | Implementation |
|---------|--------|----------------|
| **Art 1** (Human Supremacy) | `mekong/hooks/` | Session init enforces human-first: AI Cells start at L0 (observer), log all decisions to Behavior Graph, require human approval above threshold. Hooks intercept shell/task creation and inject constitutional checks before privilege escalation. |
| **Art 2** (Mission Integrity) | `src/mekong/constitution/` | Constitutional review engine evaluates every action against the particle's mission clause. `format_schema.py` provides the shared format contract. Compliance AI Cell runs quarterly reviews — score below 0.71 triggers escalation to founder. |
| **Art 3** (AI Cell Boundaries) | `src/mekong/graph/` | Collusion detection via Behavior Graph analysis. Independent Guardian AI Cell monitors cross-cell interactions. Privilege escalation requires a signed constitutional review. Tripartite separation (Strategy, Operations, Compliance) enforced at the Cell runtime level. |
| **Art 4** (Economic Agency) | `mekong/skel/` | Particle scaffold templates instantiate new Economic Particles with treasury, constitution, and behavior graph references. Dissolution automation guarantees settlement before closure. |
| **Art 5** (Financial Sovereignty) | `core/treasury/` | Multi-currency treasury with constitutional hooks on every transaction. Supports fiat, stablecoin, MCU credits. Payment routing layer (Stripe, Wise, stablecoin) chosen per particle. |
| **Art 6** (Behavioral Integrity) | `src/mekong/graph/` | Trust score computation from observed behavior. Collusion detection runs continuously on graph edges. Anti-concentration monitors voting power distribution. Evaluation metrics rotate periodically to resist gaming. |
| **Art 7** (Commons Governance) | `mekong/orchestrator/` | Governance dispatch: routes proposals through tripartite separation (Legislation/Execution/Adjudication). Dispute resolution via Guardian mediation -> Community vote. Amendment process enforces cooling periods and supermajority thresholds. |
| **Art 8** (Right to Exit) | `cli/commands/` | Exit commands (`particle/export`, `particle/fork`, `particle/dissolve`) guarantee data portability, IP licensing, and identity portability. Protocol-level enforcement — no proprietary format traps. |
| **Art 9** (Anti-Capture & Evolution) | `docs/` | Amendment documentation, sunset clause registry, adversarial sandbox specifications. Constitutional review history and article-level audit trail. |

---

## Dependencies

```
ZENOS.md (constitution)
  -> format_schema.py (shared format contract)
    -> mekong/skel/ (particle scaffold — Art 4)
      -> core/treasury/ (treasury — Art 5)
        -> mekong/hooks/ (session hooks — Art 1)
          -> src/mekong/constitution/ (review engine — Art 2)
            -> src/mekong/graph/ (behavior graph — Art 3, 6)
              -> mekong/orchestrator/ (governance — Art 7)
                -> cli/commands/ (exit — Art 8)
                  -> docs/ (evolution — Art 9)
```

Modules lower in this chain may import from modules above them. No circular dependencies.

---

## Development Status

| Module | Phase | Status |
|--------|-------|--------|
| `src/mekong/constitution/format_schema.py` | Phase 2 | Done |
| `ZENOS.md` | Phase 2 | Done |
| `mekong/ARCHITECTURE.md` | Phase 2 | Done |
| `mekong/hooks/` | Phase 1 | Done (hooks canonical) |
| `src/mekong/graph/` | Phase 4 | Planned |
| `mekong/skel/` | Phase 3 | Planned |
| `core/treasury/` | Phase 7 | Planned |
| `mekong/orchestrator/` | Phase 5 | Planned |
| `cli/commands/` | Phase 7 | Planned |
| `docs/` | Ongoing | Active |

---

*Last updated: 2026-07-04*
