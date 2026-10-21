# Phase 05: Facade, CLI & FastMCP Wiring

## Requirements
- Multi-domain Facade: `src/core/maritime_pto_berth_biofoul_waste_engine.py` (< 200 LOC).
- Typer CLI with 8 bilingual aliases: `src/cli/commands/maritime_pto_berth_biofoul_waste_command.py` (< 200 LOC).
  - `shaftpto` / `mayphattruc`
  - `berthalloc` / `dieudocauport`
  - `biofoul` / `sambanhabien`
  - `wasteoil` / `dauthaicang`
- Wire CLI into `src/cli/app_setup.py`.
- Wire 4 FastMCP endpoints into `scripts/mcp_server.py`.
