# Implementation Plan - Maritime Phases 399-402 (Maritime Advanced Engineering AH)

## Overview
Implement Maritime Phases 399-402 covering Marine Bow Thruster Dynamic Thrust & Pitch Control, Inflatable Liferaft & Hydrostatic Release Unit (HRU) Float-Free Dynamics, Shipboard Waste High-Temperature Incinerator & Plasma Gasification, and Marine Closed Vapor Emission Control System (VECS / VRU) for Tankers.

## Architecture
- All files strictly < 200 LOC.
- Zero mock dependencies; exact physics, thermodynamics, and classification society standards (SOLAS II-1/III, DNV-RU-SHIP Pt.4 Ch.5, IMO LSA Code, MARPOL Annex V MEPC.244(66), IMO MSC/Circ.585, USCG 46 CFR Part 39).
- 4 Core Engines in `src/core/maritime/`.
- 1 Central Facade in `src/core/maritime_thruster_liferaft_incinerator_vecs_engine.py`.
- 4 Typer CLI command groups with 8 bilingual aliases in `src/cli/commands/maritime_thruster_liferaft_incinerator_vecs_command.py`.
- Registered into `src/cli/app_setup.py`.
- 4 FastMCP tool endpoints in `scripts/mcp_server.py`.
- 100% test pass rate with unit & integration tests in `tests/`.

## Phases
1. Phase 399: Marine Bow Thruster Thrust & Pitch (`phase_399_bow_thruster_thrust_pitch.py`)
2. Phase 400: Liferaft & Hydrostatic Release Unit (`phase_400_inflatable_liferaft_hru_release.py`)
3. Phase 401: Shipboard Waste Incinerator & Gasification (`phase_401_waste_incinerator_gasification.py`)
4. Phase 402: Marine Vapor Emission Control System (`phase_402_vapor_emission_control_vecs.py`)
5. Facade, CLI & FastMCP Tools
6. Zero-Mock Unit & Integration Test Suites
