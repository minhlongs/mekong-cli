# Tech Stack Specification: Maritime Admiralty, General Average, Liens & Collision Suite (Phases 203-206)

## 1. Architecture & Design Principles
- **AST Zero-External-Dependency Invariant**: The domain core engine `src/core/maritime_admiralty_ga_collision_engine.py` strictly utilizes Python standard library modules (`dataclasses`, `datetime`, `enum`, `math`, `typing`, `json`, `hashlib`, `re`).
- **YAGNI / KISS / DRY**: Simple, elegant, pure computational pipelines. No bloated ORM or mock layers.
- **Fail-Closed Statutory Validation**: Strict statutory guardrails for Vietnamese Maritime Code 2015, Ordinance 05/2008/UBTVQH12, York-Antwerp Rules 2016, and Bunker Convention 2001.

## 2. Component Layout
1. **Core Domain Module**: `src/core/maritime_admiralty_ga_collision_engine.py`
   - `MaritimeShipArrestEngine` (Phase 203)
   - `GeneralAverageYAREngine` (Phase 204)
   - `MaritimeLienPriorityEngine` (Phase 205)
   - `CollisionAndBunkerPollutionEngine` (Phase 206)
2. **CLI Surface**: `src/cli/commands/maritime_admiralty_ga_collision_command.py`
   - Typer sub-apps:
     - `shiparrest` (alias `battau`)
     - `genaverage` (alias `tonthatchung`)
     - `lienpriority` (alias `hangcamgiu`)
     - `collision` (alias `damva`)
3. **App Integration**: `src/cli/app_setup.py`
   - Register groups and aliases into Typer main tree.
4. **FastMCP Server**: `scripts/mcp_server.py`
   - 4 tools: `handle_ship_arrest_audit`, `handle_general_average_adjust`, `handle_maritime_lien_waterfall`, `handle_collision_bunker_assess`.
5. **Testing Suite**: `tests/test_maritime_admiralty_ga_collision_suite.py`
   - 100% test coverage with AST inspection, domain calculations, CLI runner, and FastMCP endpoints.
