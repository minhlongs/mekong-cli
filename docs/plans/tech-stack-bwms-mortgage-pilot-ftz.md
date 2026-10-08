# Tech Stack Specification: Phases 279-282 BWMS, Ship Mortgage, Pilotage & Seaport FTZ Suite

## Architectural Blueprint
Zero external dependencies across the core engine layer, adhering to pure Python standard library principles (`dataclasses`, `datetime`, `enum`, `math`, `typing`, `hashlib`).

```
mekong (CLI) / FastMCP (Agent Tools)
  │
  ├── src/core/maritime_bwms_mortgage_pilot_ftz_engine.py
  │     ├── BwmsComplianceEngine (Phase 279 - BWM Convention Regs. D-1/D-2, BWM.2/Circ.70)
  │     ├── ShipMortgageEnforcementEngine (Phase 280 - VMC 2015 Arts. 31-36, Decree 58/2017)
  │     ├── MaritimePilotageDuesEngine (Phase 281 - VMC 2015 Arts. 246-258, Circular 39/2023)
  │     └── SeaportFtzTransshipmentEngine (Phase 282 - Customs Law Arts. 42-44, Decree 08/2015)
  │
  ├── src/cli/commands/maritime_bwms_mortgage_pilot_ftz_command.py
  │     ├── bwms_app ("bwms" / "nuocdanthuyen")
  │     ├── mortgage_app ("mortgage" / "thechaptaubien")
  │     ├── pilotage_app ("pilotage" / "hoatieuhanghai")
  │     └── ftz_app ("seaportftz" / "trungchuyenhanghai")
  │
  ├── scripts/mcp_server.py
  │     ├── mekong_bwms_d2_compliance_calculate
  │     ├── mekong_ship_mortgage_enforcement_distribute
  │     ├── mekong_maritime_pilotage_dues_calculate
  │     └── mekong_seaport_ftz_transshipment_verify
  │
  └── tests/test_maritime_bwms_mortgage_pilot_ftz_suite.py
        ├── AST zero-dependency verification
        ├── Core mathematical, stoichiometric, waterfall & corridor tracking tests
        ├── Typer CLI command and bilingual alias execution tests
        └── FastMCP tool specification and handler invocation tests
```

## Key Technical Invariants
1. **Zero External Dependencies**: Core engine operates purely on Python standard library, validated via AST inspection during test runs.
2. **Stoichiometric Neutralization Rigor**: TRO chemical neutralization accurately models sodium bisulfite dosing ($\text{NaHSO}_3 / \text{Cl}_2$ ratio $1.465$) with safety margins, evaluating BWM Reg. D-2 microbe thresholds and D-1 volumetric dilution ($1 - e^{-3} \ge 95\%$).
3. **Strict Statutory Mortgage Ranking**: Mortgage enforcement implements the statutory 15-day notice period (VMC Art. 34), Civil Code Art. 468 $20\%$ interest cap, and priority waterfall (Enforcement costs -> VMC Art. 37 Maritime Liens -> Registered Mortgages -> Unsecured -> Residual).
4. **Dynamic Pilotage & SOLAS Safety**: Calculates Circular 39/2023 dues ($GT \times NM$), night $+40\%$ surcharge, bad weather standby ($20\text{ USD/h}$), and verifies SOLAS V/23 pilot ladder rules (mandatory combination arrangement if freeboard $> 9\text{m}$).
5. **FTZ 30-Day Dwell & GPS E-Seal Corridor**: Monitors 30-day statutory international transshipment limit with extension tracking and evaluates Haversine corridor route deviation ($\le 500\text{m}$) and anti-tamper triggers with SHA-256 tokens.
