# Plan: Maritime Phases 371–374 Implementation

- **Slug:** `20261009-maritime-phases-371-374`
- **Scope:** PTO/PTI Hybrid Engine, Berth & Crane BAP/QCSP, Biofouling & In-Water Cleaning, Port Circular Waste Oil Recovery
- **Architecture:** Hybrid Modular Facade (< 200 LOC per file), Zero-Mock Tests, 8 Bilingual Typer Aliases, 4 FastMCP Tools

## Phases
1. [Phase 01: Marine Shaft Generator PTO/PTI Hybrid](phase-01-pto-pti.md) - DNV-RU-SHIP Pt.4 Ch.8, SFOC fuel savings, ME load/speed inhibits.
2. [Phase 02: Port Berth & Quay Crane BAP/QCSP](phase-02-berth-crane.md) - UNCTAD & PIANC, 35m crane buffer, UKC >= 1.5m, tidal window gating.
3. [Phase 03: Biofouling & In-Water Cleaning](phase-03-biofouling.md) - IMO MEPC.378(80), LoF 0-5 scale, 99% filtration capture >= 5um, drydock gate.
4. [Phase 04: Port Circular Waste Oil Recovery](phase-04-waste-oil.md) - MARPOL Annex I & TT 02/2022, 60°C flash point, 15 ppm effluent, RFO clinker offset.
5. [Phase 05: Central Facade, CLI & FastMCP Wiring](phase-05-facade-cli-mcp.md) - Aggregator engine, 8 Typer CLI bilingual commands, 4 FastMCP tools.
6. [Phase 06: Zero-Mock Unit & Integration Testing](phase-06-tests.md) - 3 modular test suites (< 200 LOC), 100% green pass rate.
