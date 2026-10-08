# Tech Stack & Design Guidelines — Maritime SAR, AtoN, Oil Spill & Dredging Suite (Phases 247-250)

## 1. Statutory & Technical Framework
- **Phase 247 (Maritime SAR):** IMO/ICAO IAMSAR Manual Vol. II, SAR Convention 1979, Decision 06/2014/QĐ-TTg, Circular 29/2020/TT-BGTVT.
  - Search radius: $R = f_s \cdot (d_e + d_t)$ with safety factor $f_s \in [1.1, 1.6]$.
  - Area: $A = 4 R^2$. Search patterns: Expanding Square (SS), Sector Search (VS), Parallel Track (PS), Creeping Line (CS).
  - Allocation: Sweep width $W$, track spacing $S$, coverage $C = W/S$, probability of detection (POD).
- **Phase 248 (IALA AtoN):** IALA Guideline G1078, Circular 47/2023/TT-BGTVT, Vietnam Maritime Code 2015 Arts. 113–120.
  - AtoN availability target categories: Cat 1 ($\ge 99.8\%$), Cat 2 ($\ge 99.0\%$), Cat 3 ($\ge 97.0\%$).
  - Circular 47 AtoN dues: Base tariff rate per GT per call, coastal vs channel zone multipliers.
  - Notice to Mariners (Thông báo hàng hải) urgency triggers.
- **Phase 249 (Tiered Oil Spill Response):** Decision 12/2021/QĐ-TTg, MARPOL Annex I, Circular 33/2018/TT-BTNMT.
  - Tier 1: Local facility level ($< 20\text{ tons}$), response within 1 hour.
  - Tier 2: Provincial / Regional level ($20 - 100\text{ tons}$), response within 2 hours.
  - Tier 3: National / International level ($> 100\text{ tons}$), National Committee activation.
  - Dispersant chemical safety approval criteria: water depth $> 20\text{m}$, distance offshore $> 3\text{ NM}$, sensitive mangrove/aquaculture prohibition.
  - Boom containment recovery: Minimum boom length $L \ge 3 \times \text{vessel LOA}$ or skim swath buffer.
- **Phase 250 (Channel Maintenance Dredging & Dumping):** Decree 159/2018/NĐ-CP, Decree 08/2022/NĐ-CP, Circular 35/2019/TT-BGTVT, Law on Sea 2012.
  - Infill siltation rate: $\Delta V = L \cdot W \cdot (h_{target} - h_{actual})$.
  - Sea dumping permit criteria: Sediments Class A (unrestricted), Class B (confined), Class C (toxic prohibited).
  - Environmental monitoring stations and turbidity TSS baseline thresholds.

## 2. Architecture & Design Invariants
- **Core Engine:** Zero external dependencies (`src/core/maritime_sar_aton_spill_dredging_engine.py`) using only Python standard library.
- **CLI Commands:** Dual-language naming (`sar`/`cuunanthanghai`, `aton`/`baohieuhanghai`, `spill`/`sucoctd`, `dredging`/`naovetluong`) with Typer & Rich.
- **FastMCP Protocol:** Clean typed JSON schemas with automated handlers in `scripts/mcp_server.py`.
- **Quality Gates:** 100% test coverage in `tests/test_maritime_sar_aton_spill_dredging_suite.py` with AST invariant check.
