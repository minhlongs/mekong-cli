# Phase 05: Central Facade, Typer CLI & FastMCP Server Tools

## Overview
- **Target Files**:
  - `src/core/maritime_voyage_voc_yard_greywater_engine.py` (< 200 LOC)
  - `src/cli/commands/maritime_voyage_voc_yard_greywater_command.py` (< 200 LOC)
  - `src/cli/app_setup.py` (wire 8 bilingual commands)
  - `scripts/mcp_server.py` (register 4 async FastMCP tools)

## Components
1. **Central Facade**:
   - `MaritimeVoyageVocYardGreywaterEngine.run_all(weather_inp, voc_inp, yard_inp, water_inp)`
   - Computes aggregated multi-domain health status and critical alerts.
2. **Bilingual Typer CLI Commands**:
   - `weathercii` / `dinhhuongcii`: Voyage weather routing & CII evaluation
   - `vocvapor` / `thuhoikhivoc`: Tanker VOC recovery & vapor balancing
   - `yardstack` / `dieudobaicont`: Yard container stacking & RTG dispatch
   - `greywater` / `tuanhoannuocxam`: HVAC condensate harvesting & greywater reclamation
3. **FastMCP Server Tools**:
   - `mekong_maritime_weather_cii_evaluate`
   - `mekong_maritime_voc_recovery_evaluate`
   - `mekong_maritime_yard_rtg_dispatch_evaluate`
   - `mekong_maritime_greywater_reuse_evaluate`
