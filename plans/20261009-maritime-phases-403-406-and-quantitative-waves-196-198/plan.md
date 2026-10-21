# Plan: Maritime Phases 403-406 & Quantitative Waves 196-198

## Overview
Implement Maritime Engineering Phases 403-406 in `mekong-cli` and Quantitative Desk Waves 196-198 in `algo-trader`.

## Architecture & Invariants
- `mekong-cli`: Strictly < 200 LOC per file, zero mocks, 100% green pytest.
- `algo-trader`: Strictly < 180 LOC per file, zero `:any` types, zero mocks, 100% green vitest.

## Dependency Graph
```
Phase 1: Maritime 403-406 Engines ──► Phase 2: Facade, CLI & MCP ──► Phase 3: Maritime Tests
Phase 4: Wave 196 Carr-Madan (Parallel)
Phase 5: Wave 197 Variance Gamma (Parallel)
Phase 6: Wave 198 Hasbrouck VAR (Parallel)
```

## Phases
- [ ] [Phase 01: Maritime 403-406 Core Engines](phase-01-maritime-core-engines.md)
- [ ] [Phase 02: Maritime Facade, CLI & FastMCP](phase-02-maritime-facade-cli-mcp.md)
- [ ] [Phase 03: Maritime Zero-Mock Test Suite](phase-03-maritime-test-suite.md)
- [ ] [Phase 04: Wave 196 Carr-Madan Static Replication](phase-04-wave-196-carr-madan.md)
- [ ] [Phase 05: Wave 197 Variance Gamma Option Pricing](phase-05-wave-197-variance-gamma.md)
- [ ] [Phase 06: Wave 198 Hasbrouck Microstructure VAR/VECM](phase-06-wave-198-hasbrouck-vecm.md)
