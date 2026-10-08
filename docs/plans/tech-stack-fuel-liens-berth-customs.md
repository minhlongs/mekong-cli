# Tech Stack Specification: Phases 275-278 Fuel Switchover, Maritime Liens, Berth Planning & Customs VASSCM Suite

## Architectural Blueprint
Zero external dependencies across the core engine layer, adhering to pure Python standard library principles (`dataclasses`, `datetime`, `enum`, `math`, `typing`).

```
mekong (CLI) / FastMCP (Agent Tools)
  │
  ├── src/core/maritime_fuel_liens_berth_customs_engine.py
  │     ├── FuelSwitchoverEngine (Phase 275 - MARPOL Annex VI Reg. 14 / MEPC.1/Circ.864)
  │     ├── MaritimeLienWaterfallEngine (Phase 276 - VMC 2015 Arts. 37-43)
  │     ├── BerthPlanningUkcEngine (Phase 277 - Decree 58/2017 & PIANC 158)
  │     └── CustomsRiskVasscmEngine (Phase 278 - Law on Customs 2014 & Decision 2185)
  │
  ├── src/cli/commands/maritime_fuel_liens_berth_customs_command.py
  │     ├── fuelswitch_app ("fuelswitch" / "doinhenlieu")
  │     ├── lienswaterfall_app ("maritimeliens" / "camgiuhanghai")
  │     ├── berthplan_app ("berthplan" / "dieudocau")
  │     └── vasscm_app ("customsvasscm" / "haiquancang")
  │
  ├── scripts/mcp_server.py
  │     ├── mekong_marpol_fuel_switchover_calculate
  │     ├── mekong_maritime_lien_waterfall_distribute
  │     ├── mekong_berth_allocation_ukc_evaluate
  │     └── mekong_customs_risk_vasscm_verify
  │
  └── tests/test_maritime_fuel_liens_berth_customs_suite.py
        ├── AST zero-dependency verification
        ├── Core mathematical, thermodynamic, waterfall & channeling tests
        ├── Typer CLI command and bilingual alias execution tests
        └── FastMCP tool specification and handler invocation tests
```

## Key Technical Invariants
1. **Zero External Dependencies**: Core engine operates purely on Python standard library, validated via AST inspection during test runs.
2. **Physics & Thermodynamics Rigor**: Fuel switchover respects exponential dilution mixing, thermal ramping limit ($\le 2.0^\circ\text{C/min}$), and minimum kinematic viscosity constraint ($\ge 2.0\text{ cSt}$).
3. **Strict Statutory Priority**: Maritime lien waterfall implements the 5 VMC Art. 37 ranks with inverse chronological ordering for salvage (Art. 38), 1-year timebar enforcement (Art. 39), senior court costs deduction, and pro-rata tier distribution.
4. **Dynamic UKC & PIANC Safety**: Tidal window UKC dynamically integrates harmonic tide height, Barass squat, freshwater sinkage, and $10\%$ LOA berth spacing with PIANC $65\%/70\%$ BOR limits.
5. **Customs 3-Way Triad**: VASSCM gate clearance enforces 3-way match across released declaration, valid e-D/O, and tamper-evident container seal token.
