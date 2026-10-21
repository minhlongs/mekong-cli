# Phase 05: Central Facade, Typer CLI Sub-Apps & FastMCP Integration

## Overview
- Priority: High
- Status: Ready to Implement
- Standards: Mekong CLI Architecture, FastMCP, Typer Bilingual Support
- Target Files:
  - `src/core/maritime_purifier_steering_heeling_sniffer_engine.py` (< 200 LOC)
  - `src/cli/commands/maritime_purifier_steering_heeling_sniffer_command.py` (< 200 LOC)
  - `src/cli/app_setup.py` (Integration)
  - `scripts/mcp_server.py` (FastMCP 4 async tools)

## Architecture
- Central facade `MaritimePurifierSteeringHeelingSnifferEngine` running all 4 engines and producing an aggregate evaluation.
- Typer CLI command groups:
  - `purifier` / `mayloclytam`
  - `emergsteering` / `laikhancap`
  - `antiheeling` / `chongnghiengtau`
  - `pumproomgas` / `khibuongbom`
- FastMCP async tools:
  - `mekong_maritime_fuel_purifier_evaluate`
  - `mekong_maritime_emergency_steering_evaluate`
  - `mekong_maritime_anti_heeling_evaluate`
  - `mekong_maritime_pumproom_gas_evaluate`
