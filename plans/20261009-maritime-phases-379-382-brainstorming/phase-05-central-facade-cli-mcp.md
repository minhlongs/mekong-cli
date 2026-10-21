# Phase 05: Central Facade, Typer CLI & FastMCP Tool Integration

## Overview
- Priority: High
- Status: Ready to Implement
- Target Files:
  - `src/core/maritime_air_seachest_draft_pilot_engine.py` (< 200 LOC)
  - `src/cli/commands/maritime_air_seachest_draft_pilot_command.py` (< 200 LOC)
  - `src/cli/app_setup.py` (wiring 8 bilingual CLI command aliases)
  - `scripts/mcp_server.py` (exposing 4 FastMCP async tool endpoints)

## Bilingual CLI Commands & Aliases
1. `marineair` / `khinenkhoidong`: Marine Starting Air & Compressor Automation
2. `seachest` / `vanhutdaylammat`: Seachest & Seawater Cooling Ingress Protection
3. `draftsound` / `mondoquetung`: Automatic Draft & Tank Sounding Gauging
4. `arpapilot` / `hoatieudieuve`: Port Pilotage Navigational Safety & ARPA Collision Avoidance

## FastMCP Tools
- `mekong_maritime_starting_air_evaluate`
- `mekong_maritime_seachest_cooling_evaluate`
- `mekong_maritime_draft_sounding_evaluate`
- `mekong_maritime_arpa_pilotage_evaluate`
