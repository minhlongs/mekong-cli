# Project Changelog

## v6.1.0 — 2026-08-23

**Design Intelligence (Hallmark deep integration):**
- New `src/design_intelligence/` package: Pydantic v2 schemas (DesignDNA 23 fields,
  DesignBrief, AuditReport, Theme), 58 gates (29 objective / 29 heuristic / 8 visual),
  9-axis scoring, archetype→macrostructure pipeline, provider-agnostic visual QA
- Knowledge base: 58 gates, 21 macrostructures, 12 themes, 4 genres, 16 archetypes
- New `mekong ui` sub-app: audit, study, redesign, build, approve, benchmark
- Three evidence tiers (objective/heuristic/opinion) and three visual-QA tiers
  (full/screenshot/static) kept strictly separate — never over-claimed
- Design memory: approved DNA / rejected patterns via MemoryStore `design:` namespace
  (Sophia contract); `study --export-json` emits parseable DesignDNA JSON
- Change detection + opt-in `mekong deploy --design-audit` advisory hook
  (frontend diffs suggest audit; backend/migration/CLI/infra-only skip)
- Anti-gaming benchmark: 10 fixtures, 7 derived metrics, good vs slop separation
- 140 design-intelligence tests; docs/design-intelligence.md

## v6.0.0 — 2026-08-16

**Highlights:**
- MIT license applied
- Python-only contributor workflow finalized
- 48 commands mapped in COMMAND_REGISTRY.md
- spec-kit SDD artifacts added (specs/, trace.rb, traceability.json)

**Repo parity fixes:**
- Release metadata synced to `minhlongs/mekong-cli`
- GitHub Actions PyPI-only publish path validated