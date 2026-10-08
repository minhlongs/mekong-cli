# Implementation Plan: Phases 279-282 BWMS, Ship Mortgage, Pilotage & Seaport FTZ Suite

## Overview
- **Phase 279**: Ballast Water Management System (BWMS) D-2 Compliance, Commissioning Testing & Salinity Exchange Engine (IMO BWM Convention Regs. D-1/D-2, BWM.2/Circ.70/Rev.1, Circular 39/2023/TT-BGTVT).
- **Phase 280**: Ship Mortgage Enforcement, Private Sale vs Judicial Auction & Escrow Distribution Engine (Vietnam Maritime Code 2015 Arts. 31-36, Decree 58/2017/NĐ-CP, Decree 21/2021/NĐ-CP, Civil Code 2015 Art. 468).
- **Phase 281**: Maritime Pilotage Service Allocation, Pilot Ladder Safety & Pilotage Dues Engine (Vietnam Maritime Code 2015 Arts. 246-258, Circular 39/2023/TT-BGTVT, Decree 58/2017/NĐ-CP, SOLAS Reg. V/23 & IMO Res. A.1045(27)).
- **Phase 282**: Seaport Free Trade Zone (FTZ) / Bonded Transshipment Cargo Supervision & E-Seal Tracking Engine (Law on Customs 2014 Arts. 42-44, Decree 08/2015/NĐ-CP, Decree 59/2018/NĐ-CP, Circular 38/2015/TT-BTC, Circular 39/2018/TT-BTC).

## Execution Steps
1. [x] Research & Legal Framework Analysis (`docs/plans/research/researcher-29-bwms-mortgage-foreclosure.md` & `researcher-30-pilotage-tariff-ftz-bonded.md`).
2. [x] Technical Architecture & Tech Stack (`docs/plans/tech-stack-bwms-mortgage-pilot-ftz.md`).
3. [x] Design Guidelines & Terminal Wireframes (`docs/design-guidelines-bwms-mortgage-pilot-ftz.md`).
4. [x] Implement Core Engine (`src/core/maritime_bwms_mortgage_pilot_ftz_engine.py`):
   - Zero-dependency standard library Python with AST safety.
   - Dataclasses, serialization, calculations, validation rules, edge cases.
5. [x] Wire Typer CLI commands (`src/cli/commands/maritime_bwms_mortgage_pilot_ftz_command.py`):
   - 4 sub-applications with 8 bilingual aliases in `src/cli/app_setup.py`.
6. [x] Implement FastMCP Tools & Handlers (`scripts/mcp_server.py`):
   - 4 tools in `CORE_TOOLS_SPEC` and 8 entries in `CORE_HANDLERS`.
7. [x] Build Test Suite (`tests/test_maritime_bwms_mortgage_pilot_ftz_suite.py`):
   - 100% test pass rate with zero mocks (33 passed, 0 failed).
8. [x] Update Documentation & Persistent Memory:
   - `docs/development-roadmap.md`, `docs/project-changelog.md`, `docs/system-architecture.md`, `MEMORY.md`.
