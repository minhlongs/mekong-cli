# Implementation Plan - Maritime Phases 395-398

## Overview
Implement Maritime Phases 395-398 covering Exhaust Gas Cleaning System (EGCS) SOx Scrubber, Vacuum Plate Fresh Water Generator (FWG), Electro-Hydraulic Deck Crane Anti-Sway & Dynamic SWL, and Ultrasonic Thickness Measurement (UTM) Hull Gauging & Wastage Limits.

## Architecture
- All files strictly < 200 LOC.
- Zero mock dependencies; exact physics, thermodynamics, classification society standards (IMO MEPC.340(77), WHO, DNV-ST-0378, IACS UR Z10).
- 4 Core Engines in `src/core/maritime/`.
- 1 Central Facade in `src/core/maritime_egcs_fwg_crane_utm_engine.py`.
- 4 Typer CLI command groups with 8 bilingual aliases in `src/cli/commands/maritime_egcs_fwg_crane_utm_command.py`.
- Wired into `src/cli/app_setup.py`.
- 4 FastMCP tool endpoints in `scripts/mcp_server.py`.
- 100% test pass rate with unit & integration tests in `tests/`.

## Phases
1. Phase 395: EGCS SOx Wet Scrubber (`phase_395_egcs_sox_wet_scrubber.py`)
2. Phase 396: Vacuum Plate Fresh Water Generator (`phase_396_vacuum_fresh_water_generator.py`)
3. Phase 397: Deck Crane Anti-Sway & Dynamic SWL (`phase_397_deck_crane_anti_sway_swl.py`)
4. Phase 398: UTM Hull Gauging & Wastage Limits (`phase_398_utm_hull_gauging_corrosion.py`)
5. Facade, CLI & FastMCP Tools
6. Zero-Mock Unit & Integration Test Suites
