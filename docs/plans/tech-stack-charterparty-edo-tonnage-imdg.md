# Tech Stack & Architectural Design: Phases 267-270

## Architecture Principles
1. **Zero External Dependencies**: Core engine must rely strictly on Python 3 standard library (`dataclasses`, `enum`, `datetime`, `math`, `typing`, `json`, `sys`, `os`).
2. **Deterministic Mathematical Formulas**: Pure functions without side effects or network calls.
3. **Statutory Adherence**: Vietnam Maritime Code 2015, Circular 39/2023/TT-BGTVT, Circular 12/2024/TT-BGTVT, Circular 38/2015/TT-BTC, IMDG Code Amendment 41-22, BIMCO standard time charterparty clauses.
4. **Bilingual Terminal & API Interfaces**: English & Vietnamese commands in Typer and schema descriptions in FastMCP.

---

## Component Layout
- **Core Engine File**: `src/core/maritime_charterparty_edo_tonnage_imdg_engine.py`
  - `CharterpartyPerformanceEngine`: Analyzes speed deficiencies, fuel overconsumption, good weather filtering, and financial netting under *The Didymi* / *The Gas Enterprise*.
  - `ElectronicDeliveryOrderEngine`: Validates e-D/O release state machine, container deposit escrow, IICL repair deductions, and net refund reconciliation.
  - `SeaportTonnageTariffEngine`: Calculates statutory tonnage dues, maritime safety charges, and anchorage tariffs under Circular 39/2023/TT-BGTVT and Circular 12/2024/TT-BGTVT.
  - `IMDGSafetyHandlingEngine`: Enforces dangerous goods segregation matrix (1 to 4), direct delivery mandates, fire buffers, and statutory port handling surcharges.
- **CLI Commands**: `src/cli/commands/maritime_charterparty_edo_tonnage_imdg_command.py`
  - Group 1: `charterpartyspeed` / `tocdotau`
  - Group 2: `edorelease` / `lenhgiaohang`
  - Group 3: `tonnagedues` / `phitrongtai`
  - Group 4: `imdgport` / `hangnguyhiem`
- **MCP Server Registration**: `scripts/mcp_server.py`
  - `mekong_charterparty_speed_consumption_evaluate`
  - `mekong_edo_deposit_settlement_calculate`
  - `mekong_seaport_tonnage_safety_dues_calculate`
  - `mekong_imdg_port_safety_handling_evaluate`
- **Automated Test Suite**: `tests/test_maritime_charterparty_edo_tonnage_imdg_suite.py`
  - Zero-dependency AST verification.
  - Unit calculations & legal edge cases.
  - CLI runner integration tests.
  - MCP handler integration tests.
