# Implementation Plan: Phases 267-270 Maritime Operations & Port Tariffs Suite

## Overview
- **Phase 267**: Time Charterparty Speed & Consumption Warranty Assessment (VMC 2015 Arts. 215-230, BIMCO NYPE 93/2015, *The Didymi* / *The Gas Enterprise*)
- **Phase 268**: Seaport Electronic Delivery Order (e-D/O) & Container Deposit Reconciliation (VMC 2015 Arts. 160 & 168, Circular 38/2015/TT-BTC, Circular 39/2018/TT-BTC)
- **Phase 269**: Seaport Tonnage Dues & Maritime Safety Tariffs Engine (Circular 39/2023/TT-BGTVT, Circular 12/2024/TT-BGTVT, VMC 2015 Arts. 104, 107-112)
- **Phase 270**: IMDG Dangerous Goods Seaport Handling & Segregation Safety Matrix (IMDG Code Amdt 41-22, Decree 58/2017/NĐ-CP Arts. 73-77, Decree 34/2024/NĐ-CP)

## Implementation Steps
1. **Core Engine**: `src/core/maritime_charterparty_edo_tonnage_imdg_engine.py`
   - Strict standard library only: `dataclasses`, `enum`, `datetime`, `math`, `typing`, `json`.
   - Comprehensive mathematical models and statutory checks.
2. **CLI Commands**: `src/cli/commands/maritime_charterparty_edo_tonnage_imdg_command.py`
   - Commands: `charterpartyspeed`, `edorelease`, `tonnagedues`, `imdgport`.
   - Wire into `src/cli/app_setup.py` with both English and Vietnamese alias groups (8 groups total: `charterpartyspeed` / `tocdotau`, `edorelease` / `lenhgiaohang`, `tonnagedues` / `phitrongtai`, `imdgport` / `hangnguyhiem`).
3. **FastMCP Server**: `scripts/mcp_server.py`
   - Add tool schemas to `CORE_TOOLS_SPEC`.
   - Implement handlers in `CORE_HANDLERS`.
   - Register `@app.tool` functions for FastMCP.
4. **Test Suite**: `tests/test_maritime_charterparty_edo_tonnage_imdg_suite.py`
   - Zero-dependency AST check.
   - Comprehensive test cases covering all 4 phases, edge cases, exceptions.
   - CLI runner and MCP handler invocations.
5. **Quality Verification & Documentation**:
   - Run tests with pytest.
   - Update `docs/development-roadmap.md`, `docs/project-changelog.md`, `docs/system-architecture.md`.
   - Record memory file and index.
