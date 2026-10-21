# Phase 02: Maritime Facade, CLI & FastMCP

## Files to Create/Update (< 200 LOC each)
1. `src/core/maritime_bilge_inertgas_sterntube_watermist_engine.py` (~140 LOC)
   - Facade integrating all 4 core engines with consolidated health evaluation.
2. `src/cli/commands/maritime_bilge_inertgas_sterntube_watermist_command.py` (~175 LOC)
   - 4 Typer apps with 8 bilingual aliases (`bilgeseparator`/`tachnuocdaytau`, `inertgas`/`khitro`, `sterntube`/`ongbaotruc`, `watermist`/`suongmuphongchay`).
3. Update `src/cli/app_setup.py`: Register command groups.
4. Update `scripts/mcp_server.py`: Expose 4 FastMCP tool endpoints.

## Success Criteria
- CLI invocable with bilingual aliases.
- FastMCP tool endpoints operational.
