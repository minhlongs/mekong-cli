# Tech Stack & Architecture — Vietnam Port Terminal, Cold Chain & Trade Finance Suite (Phases 179-182)

## 1. Architectural Principles
- **Zero-Dependency Domain Core**: `src/core/port_supply_chain_engine.py` imports only Python standard library modules (`dataclasses`, `enum`, `typing`, `datetime`, `math`, `json`, `uuid`, `hashlib`).
- **Sub-Microsecond Calculations**: Deterministic formulas with zero network or I/O overhead.
- **Bi-Directional Surfaces**:
  - Human CLI: Typer commands with Rich formatting, tables, panels, and machine-readable `--json` output.
  - Agentic Interface: Dual FastMCP & JSON-RPC tools with schemas and typed input parameters.

## 2. Core Engines Breakdown
1. **`SeaportTerminalOpsEngine` (Phase 179)**:
   - Seaport tariff schedules under Circular 39/2023/TT-BGTVT for Lach Huyen, Cat Lai, Cai Mep, Da Nang.
   - Demurrage / Detention (DEM/DET) multi-tier sliding window with free-time thresholds and carrier lien risk assessment.
   - SOLAS VGM tolerance check (Method 1 vs Method 2) with gate-in validation.
2. **`TradeFinanceLCEngine` (Phase 180)**:
   - UCP 600 / ISBP 745 strict compliance discrepancy engine with 5 banking days examination timeline.
   - Checks for late shipment, stale presentation (>21 days), invoice description mismatch, and credit amount tolerance.
   - Discrepancy fee deduction and usance L/C discount financing interest calculation.
3. **`ColdChainPharmaGDPEngine` (Phase 181)**:
   - Mean Kinetic Temperature (MKT) Arrhenius formulation ($83.144\text{ kJ/mol}$ activation energy).
   - Real-time excursion severity scoring across Deep Frozen, Cold Chain ($2-8^\circ\text{C}$), and CRT.
   - Quality Quarantine Hold decision matrix under Circular 02/2018/TT-BYT & Circular 36/2018/TT-BYT.
4. **`FreightCarbonAccountingEngine` (Phase 182)**:
   - ISO 14083:2023 & GLEC Framework v3.0 Well-to-Wheel (WTW) logistics emissions calculator.
   - Multi-leg multimodal emission aggregation (Truck, Barge, Ocean, Air).
   - Modal shift reduction analysis and Decree 06/2022/NĐ-CP carbon offset valuation.

## 3. Surface Mapping
- **CLI Commands**:
  - `mekong port tariff` & `mekong port dem-det` & `mekong port vgm`
  - `mekong trade-finance lc-check` & `mekong trade-finance lc-discount`
  - `mekong cold-chain mkt` & `mekong cold-chain excursion`
  - `mekong freight-carbon route-emissions` & `mekong freight-carbon modal-shift`
- **Aliases**: `port` / `cangbien`, `trade-finance` / `lc`, `cold-chain` / `daychuyenlanh`, `freight-carbon` / `carbon-vt`.
- **MCP Server Tools**: 8 registered tools matching CLI functionality.
