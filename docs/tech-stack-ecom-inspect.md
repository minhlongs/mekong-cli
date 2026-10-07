# Tech Stack & Architecture — Vietnam E-Commerce, Specialized Inspection, Chemicals & CBAM Suite

**Phase Target:** Phases 175 - 178  
**Architecture Standard:** 100% Python Standard Library Domain Layer (Zero External Runtime Dependencies)  
**Integration Surfaces:** Typer CLI (`mekong ecom`, `mekong inspect`), FastMCP & JSON-RPC tools (`scripts/mcp_server.py`)

---

## 1. Core Principles & Design Invariants

1. **AST Purity & Zero Dependencies:**  
   The core domain module `src/core/ecom_inspect_engine.py` imports exclusively from Python standard library (`dataclasses`, `enum`, `math`, `typing`, `datetime`). Zero third-party packages in domain logic.
2. **Sub-millisecond Determinism:**  
   In-memory state transition graphs, O(1) IMDG segregation lookups, and Euclidean/Ray-casting geo-polygon validation executing in < 1ms.
3. **Dual Surface Compatibility:**  
   All engines expose clean typed return objects consumed seamlessly by Rich terminal visualizers (`src/cli/commands/ecom_inspect_command.py`) and agentic MCP tools (`scripts/mcp_server.py`).
4. **Resilience & Fail-Closed Security:**  
   Strict statutory gating: Banned chemicals (Annex III) and deforestation post-2020 immediately trigger fail-closed rejection.

---

## 2. Component Architecture & Engine Boundaries

```
+-----------------------------------------------------------------------------------+
|                                  CLIENT SURFACES                                  |
|   +------------------------------------+   +------------------------------------+ |
|   |  Typer CLI (Rich UI & JSON)        |   |  FastMCP & JSON-RPC Server         | |
|   |  - mekong ecom <tax|split|platform>|   |  - mekong_ecom_tax_calculation     | |
|   |  - mekong inspect <chem|seg|food>  |   |  - mekong_ecom_split_detection     | |
|   |  - mekong inspect <cbam|eudr>      |   |  - mekong_chemical_nsw_eval        | |
|   |                                    |   |  - mekong_food_safety_inspect_tier | |
|   |                                    |   |  - mekong_cbam_liability_calc      | |
|   +-----------------+------------------+   +-----------------+------------------+ |
+---------------------|----------------------------------------|--------------------+
                      |                                        |
+---------------------v----------------------------------------v--------------------+
|                         ROUTING & PRESENTATION ADAPTERS                           |
|   - src/cli/commands/ecom_inspect_command.py (Rich tables, panels, JSON output)   |
|   - scripts/mcp_server.py (FastMCP schema registration & JSON-RPC dispatch)       |
+------------------------------------+----------------------------------------------+
                                     |
+------------------------------------v----------------------------------------------+
|                    DOMAIN CORE (100% Python Standard Library)                     |
|                         src/core/ecom_inspect_engine.py                           |
|                                                                                   |
|   +------------------------------------+   +------------------------------------+ |
|   | 1. CrossBorderEcomEngine           |   | 2. HazardousChemicalNSWEngine      | |
|   | - Customs valuation & discounts    |   | - Decree 113 & 82 Annex I-V status | |
|   | - Low-value de minimis (1M VND)    |   | - IMDG 9 DG segregation matrix     | |
|   | - 0-VND VAT from Decision 78 repeal|   | - Chemical accident plan threshold | |
|   | - Platform withholding liability   |   | - National Single Window tokens    | |
|   | - Split consignment risk score     |   |                                    | |
|   +------------------------------------+   +------------------------------------+ |
|   | 3. SpecializedInspectionEngine     |   | 4. CBAMEUDRComplianceEngine        | |
|   | - NĐ 15/2018 3-tier inspection     |   | - Specific embedded emissions (SE) | |
|   | - 3-consecutive batch transition   |   | - Net EU CBAM financial liability  | |
|   | - TT 25/2016 Animal quarantine     |   | - 5 CBAM sectors (Steel, Al, etc.) | |
|   | - TT 33/2014 Plant quarantine      |   | - EUDR post-2020 deforestation gate| |
|   |                                    |   | - Parcel polygon closure & title   | |
|   +------------------------------------+   +------------------------------------+ |
+-----------------------------------------------------------------------------------+
```

---

## 3. Technology Stack Breakdown

| Layer | Technology | Version | Rationale |
|---|---|---|---|
| **Core Domain** | Python Standard Library | 3.9+ | 100% portability, zero bloat, AST verified. |
| **CLI Runtime** | Typer + Rich | Latest | Consistent UX across Mekong CLI command groups. |
| **Protocol Layer** | FastMCP + JSON-RPC 2.0 | Latest | Dual-protocol support for Claude Code & Cursor. |
| **Linting & Code Quality** | Ruff + AST Parser | Latest | Sub-second linting and AST dependency verification. |
| **Testing** | Pytest | Latest | Deterministic automated unit and integration tests. |

---

## 4. Architectural Decisions & Trade-offs (ADR)

1. **Pure Python Point-in-Polygon vs GIS Libraries:**  
   *Decision:* Implemented ray-casting algorithm directly in standard library.  
   *Rationale:* Eliminates heavy C-libraries (GDAL, GEOS, Shapely) that break in minimal container environments.
2. **Unified Domain Module vs Multi-file Split:**  
   *Decision:* Consolidate into `src/core/ecom_inspect_engine.py` (matching `fta_duty_engine.py`).  
   *Rationale:* Simplifies cross-engine imports, reduces cognitive load, and keeps single source of truth for international logistics compliance.
3. **Platform Tax Withholding Split:**  
   *Decision:* Isolate seller platform discounts ($D_{direct}$) while treating marketing voucher subsidies as non-deductible under draft E-Com Customs Decree.
