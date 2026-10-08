# Implementation Plan: Maritime Admiralty, General Average, Liens & Collision Suite (Phases 203-206)

## 1. Overview
Implement Phases 203–206 for Mekong CLI:
- **Phase 203**: Ship Arrest & Judicial Release for Maritime Claims (VMC Arts. 129–144, Ordinance 05/2008).
- **Phase 204**: General Average Adjustment under York-Antwerp Rules (YAR 2016, VMC Arts. 295–298).
- **Phase 205**: Maritime Liens & In Rem Priority Waterfall (VMC Arts. 37–42, Geneva 1993).
- **Phase 206**: Collision Liability & Bunker Oil Pollution (VMC Arts. 285–294, Bunker Convention 2001).

## 2. Architecture & File Plan
1. `src/core/maritime_admiralty_ga_collision_engine.py`:
   - Pure standard library Python with AST zero-dependency verification.
   - Enums: `MaritimeClaimType` (22 claims), `ArrestReleaseStatus`, `GeneralAverageCategory`, `MaritimeLienRank`, `CollisionFaultType`.
   - Engines:
     - `MaritimeShipArrestEngine`: Evaluates arrest eligibility, counter-security quantum, and release conditions.
     - `GeneralAverageYAREngine`: Evaluates sacrifice/expenditure, commissions, contributory values, and net balance settlements.
     - `MaritimeLienPriorityEngine`: Models the statutory waterfall from judicial auction proceeds down to junior unsecured claims.
     - `CollisionAndBunkerPollutionEngine`: Calculates proportional fault cross-liabilities, joint & several personal injury recourse, and Bunker 2001 certification.
2. `src/cli/commands/maritime_admiralty_ga_collision_command.py`:
   - Typer sub-apps: `shiparrest`, `genaverage`, `lienpriority`, `collision`.
3. `src/cli/app_setup.py`:
   - Register the 4 apps and Vietnamese aliases (`battau`, `tonthatchung`, `hangcamgiu`, `damva`).
4. `scripts/mcp_server.py`:
   - Add tool definitions, handlers, and FastMCP annotations.
5. `tests/test_maritime_admiralty_ga_collision_suite.py`:
   - Full test coverage with 100% pass rate.
