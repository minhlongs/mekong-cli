# Plan: Maritime Phases 379–382 Implementation

**Objective:** Implement Maritime AB Advanced Suite (Phases 379-382) with zero mocks, strict < 200 LOC per file, full bilingual CLI and FastMCP coverage, and 100% green tests.

## Dependency Graph & Phases
- **Phase 01:** Marine Starting Air & Air Reservoir Compressor Automation (`phase-01-marine-air-compressor-engine.md`)
- **Phase 02:** Seachest & Main Seawater Cooling Ingress Protection (`phase-02-seachest-cooling-ingress-engine.md`)
- **Phase 03:** Automatic Draft & Tank Sounding Gauging Radar/Bubbler (`phase-03-draft-tank-gauging-engine.md`)
- **Phase 04:** Port Pilotage Navigational Safety & ARPA Collision Avoidance (`phase-04-pilotage-arpa-collision-engine.md`)
- **Phase 05:** Central Facade, Typer CLI Sub-Apps & FastMCP Integration (`phase-05-central-facade-cli-mcp.md`)
- **Phase 06:** Zero-Mock Testing & Quality Verification (`phase-06-zero-mock-testing-verification.md`)

## Key Standards
- SOLAS II-1 Reg 26 & ClassNK/DNV: 12 starts without replenishment, dual compressor 1h recharge to 30 bar.
- IACS UR M62: High/low seachest switchover, duplex strainer $\Delta P > 0.5$ bar, MGPS anode current $I = k \cdot Q$.
- IMO Res. MSC.267(85) & SOLAS XII: Hydrostatic draft survey (quarter-mean $d_M$, trim, list, deflection), radar/bubbler sounding (95%/98% alarm).
- IMO Res. MSC.192(79) & COLREGs Rule 9/10: ARPA relative vector math, CPA/TCPA, pilot speed $\le 8$ kn, tug escort clearance.
- Architecture: Strict < 200 LOC per file, 100% type annotations, zero mocks.
