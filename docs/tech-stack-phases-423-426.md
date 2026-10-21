# Tech Stack & Architectural Contract: Maritime Phases 423–426 & Quantitative Waves 211–213

## 1. Track 1: Maritime Automation 423–426 (`mekong-cli`)
- **Language & Runtime**: Python 3.12+, Typer CLI, FastMCP.
- **Typing & Validation**: Strict Pydantic / dataclasses validation with full type hints.
- **Architectural Pattern**: Hybrid Modular Facade. Each phase lives in its own submodule under `src/core/maritime/`, coordinated through a master engine `MaritimeEconomizerThermalBilgeCrankcaseEngine`.
- **File Length Gate**: Strictly $< 180\text{ LOC}$ per file.
- **Safety Doctrines**:
  - Phase 423: MEPC.340(77), IACS M53 (Economizer Soot Washing & Fire Prevention).
  - Phase 424: DIN 4754, ISO 5149 (Thermal Oil Heater & N2 Blanketing).
  - Phase 425: MARPOL Annex I Reg 14/15, MEPC.107(49) (Bilge Vacuum Distillation).
  - Phase 426: IACS UR M9, UR M10, SOLAS II-1 Reg 31 (Crankcase Explosion Relief & OMD).

## 2. Track 2: Quantitative Desk Waves 211–213 (`algo-trader`)
- **Language & Runtime**: TypeScript 5+, Node.js 20+, Vitest.
- **Typing & Standard**: Zero `:any` types, native deterministic mathematical algorithms.
- **Modular Directory Layout**:
  - `src/desk/propagator/`: Bouchaud, Mézard & Potters (2004) Propagator Impact Model.
  - `src/desk/roughheston/`: Jaisson & Rosenbaum (2015, 2016) Rough Heston Hawkes Limit.
  - `src/desk/carteajaimungal/`: Cartea & Jaimungal (2014) Optimal Market Making with Execution Penalty.
- **File Length Gate**: Strictly $< 150\text{ LOC}$ per file.
- **Testing**: Zero mocks, zero fake data, exact analytical benchmark testing.
