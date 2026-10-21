# Implementation Plan - Maritime Phases 391-394

## Overview
Implement Phases 391-394 covering Oily Water Separator (OWS), ICCP, Central Titanium PHE, and Chemical Tanker Cofferdam Vapor Sniffing.

## Architecture
- All files strictly < 200 LOC.
- Zero mock dependencies; exact physics, thermodynamics, and classification society formulas.
- 4 Core Engines in `src/core/maritime/`.
- 1 Central Facade in `src/core/maritime_ows_iccp_phe_cofferdam_engine.py`.
- 4 Typer CLI command groups with 8 bilingual aliases in `src/cli/commands/maritime_ows_iccp_phe_cofferdam_command.py`.
- Register in `src/cli/app_setup.py`.
- 4 FastMCP tool endpoints in `scripts/mcp_server.py`.
- 100% test pass rate with unit & integration tests in `tests/`.

## Phases
1. Phase 391: OWS MEPC.107(49) Ceramic Membrane (`phase_391_oily_water_separator_ceramic.py`)
2. Phase 392: ICCP Cathodic Protection & Shaft Grounding (`phase_392_iccp_cathodic_protection_shaft.py`)
3. Phase 393: Central Titanium Plate Heat Exchanger & Ultrasonic Cleaning (`phase_393_central_titanium_phe_ultrasonic.py`)
4. Phase 394: Chemical Tanker Cofferdam Vapor Sniffing & Inerting (`phase_394_chemical_cofferdam_vapor_inerting.py`)
5. Facade, CLI & FastMCP Tools
6. Zero-Mock Unit & Integration Test Suites
