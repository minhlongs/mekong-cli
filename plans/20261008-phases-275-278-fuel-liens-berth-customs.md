# Implementation Plan: Phases 275-278 Fuel Switchover, Maritime Liens, Berth Planning & Customs VASSCM Suite

## Overview
- **Phase 275**: MARPOL Annex VI Fuel Sulfur Cap & Port/ECA Fuel Oil Switchover Engine (MARPOL Annex VI Reg. 14, MEPC.1/Circ.864/Rev.1, Circular 39/2023/TT-BGTVT).
- **Phase 276**: Maritime Lien Priority Waterfall & Judicial Auction Proceeds Distribution Engine (VMC 2015 Arts. 37-43, Civil Code 2015, Decree 58/2017/NĐ-CP, Decree 62/2015/NĐ-CP).
- **Phase 277**: Seaport Berth Allocation Planning, Tidal Window UKC & Berth Occupancy Factor (BOR) Engine (Decree 58/2017/NĐ-CP Arts. 53-61, Circular 39/2023/TT-BGTVT, PIANC Report 158 / WG 121).
- **Phase 278**: Automated Customs Clearance Risk Channeling & Seaport VASSCM Clearance Engine (Law on Customs 2014 Arts. 16-17, Circular 38/2015 & Circular 39/2018/TT-BTC, Decisions 1399/QĐ-TCHQ & 2185/QĐ-TCHQ).

## Execution Steps
1. [x] Research & Legal Framework Analysis (`docs/plans/research/researcher-27-fuel-switchover-maritime-liens.md` & `researcher-28-berth-planning-customs-vasscm.md`).
2. [x] Technical Architecture & Tech Stack (`docs/plans/tech-stack-fuel-liens-berth-customs.md`).
3. [x] Design Guidelines & Terminal Wireframes (`docs/design-guidelines-fuel-liens-berth-customs.md`).
4. [x] Implement Core Engine (`src/core/maritime_fuel_liens_berth_customs_engine.py`):
   - Zero-dependency standard library Python with AST safety.
   - Dataclasses, serialization, calculations, validation rules, edge cases.
5. [x] Wire Typer CLI commands (`src/cli/commands/maritime_fuel_liens_berth_customs_command.py`):
   - 4 sub-applications with 8 bilingual aliases in `src/cli/app_setup.py`.
6. [x] Implement FastMCP Tools & Handlers (`scripts/mcp_server.py`):
   - 4 tools in `CORE_TOOLS_SPEC` and 8 entries in `CORE_HANDLERS`.
7. [x] Build Test Suite (`tests/test_maritime_fuel_liens_berth_customs_suite.py`):
   - 100% test pass rate with zero mocks (25/25 passing).
8. [x] Update Documentation & Persistent Memory:
   - `docs/development-roadmap.md`, `docs/project-changelog.md`, `docs/system-architecture.md`, `MEMORY.md`.
