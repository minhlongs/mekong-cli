# Implementation Plan: Phases 271-274 Maritime Casualty, e-C/O, Tugboat Tariffs & SOLAS VGM Suite

## Overview
- **Phase 271**: Maritime Collision Investigation, Marine Accident Formal Inquiry & Casualty Board (IMO MSC.255(84), Circular 34/2015/TT-BGTVT, VMC 2015 Arts. 113-116).
- **Phase 272**: Electronic Certificate of Origin (e-C/O) & Maritime Preferential Origin Rules (Decree 31/2018/NĐ-CP, Circular 05/2018/TT-BCT, EVFTA/CPTPP RVC & CTC algorithms).
- **Phase 273**: Seaport Tugboat Towage Tariffs & Assisted Berthing/Unberthing Service Charges (Circular 39/2023/TT-BGTVT Section III, Circular 12/2024/TT-BGTVT).
- **Phase 274**: SOLAS Verified Gross Mass (VGM) Container Weighing & Terminal Gate Tolerance Verification (SOLAS Reg. VI/2, IMO MSC.1/Circ.1475, Circular 39/2023/TT-BGTVT).

## Execution Steps
1. [x] Research & Legal Framework Analysis (`docs/plans/research/researcher-21-casualty-co-tug-vgm.md`).
2. [x] Technical Architecture & Tech Stack (`docs/plans/tech-stack-casualty-co-tug-vgm.md`).
3. [x] Design Guidelines & Terminal Wireframes (`docs/design-guidelines-casualty-co-tug-vgm.md`).
4. [x] Implement Core Engine (`src/core/maritime_casualty_co_tug_vgm_engine.py`):
   - Zero-dependency standard library Python with AST safety.
   - Dataclasses, serialization, calculation logic, edge cases.
5. [x] Wire Typer CLI commands (`src/cli/commands/maritime_casualty_co_tug_vgm_command.py`):
   - 4 sub-applications with 8 bilingual aliases in `src/cli/app_setup.py`.
6. [x] Implement FastMCP Tools & Handlers (`scripts/mcp_server.py`):
   - 4 tools in `CORE_TOOLS_SPEC` and 8 entries in `CORE_HANDLERS`.
7. [x] Build Test Suite (`tests/test_maritime_casualty_co_tug_vgm_suite.py`):
   - 100% test pass rate with zero mocks (20 tests passed).
8. [x] Update Documentation & Persistent Memory:
   - `docs/development-roadmap.md`, `docs/project-changelog.md`, `docs/system-architecture.md`, `MEMORY.md`.
