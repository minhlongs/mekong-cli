# Project Changelog

## v6.2.0 — 2026-08-29

**Super Command #5 — Economic Bus + Capability Bus + Agent Registry (PR #11):**
- Clean `src/core/` ↔ `src/core/adapters/` boundary: no vendor SDK imports in core at module level
- Canonical `LLMProvider` port (`generate/stream/structured_output/tool_call/health`); two conformant providers
- YAML single-source agent registry (`agents/registry.yaml`); Python discovery + CLI are adapters
- Capability bus wired into `mekong run` (11 builtin capabilities, failure-tolerant)
- MCP→capability bridge (`mcp:<tool_name>` ids) via `McpCapabilityAdapter` + `ToolCapabilityAdapter`
- Scheme-agnostic economic bus: x402 + MPP providers, fail-closed config, no custody
- Canonical Buzz transport (hermetic-by-injection, fail-loud `BuzzConfigError` at call time)
- `CloudflareTransport(Protocol)` with `.dispatch(payload) -> dict`; single import site isolated
- Agent-loop E2E test driving the full GOAL→CONTEXT→PLAN→DELEGATE→EXECUTE→OBSERVE→VERIFY→REPAIR→REMEMBER→COMMIT lifecycle
- 54 files, +5,127 / −843 lines; Core DNA manifest bumped to v2026.08.29
- Quality gates green: ruff clean, pyright 0 new errors, parity gate EMPTY at 277 baseline
- Architecture doc refreshed to v0.2 (scores + next-actions reflect SC5 deliverables)

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