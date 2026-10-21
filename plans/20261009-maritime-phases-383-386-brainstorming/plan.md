# Plan: Maritime Phases 383–386 Implementation

**Objective:** Implement Maritime AC Advanced Suite (Phases 383-386) with zero mocks, strict < 200 LOC per file, full bilingual CLI and FastMCP coverage, and 100% green tests.

## Dependency Graph & Phases
- **Phase 01:** Marine Centrifugal Fuel Oil Purifier & Clarifier Automation (`phase-01-fuel-purifier-engine.md`)
- **Phase 02:** Auxiliary Emergency Steering Gear & Hydraulic Power Actuation (`phase-02-emergency-steering-engine.md`)
- **Phase 03:** Automatic Anti-Heeling Ballast Pumping & Rapid Counter-Flooding (`phase-03-anti-heeling-engine.md`)
- **Phase 04:** Tanker Pump Room Atmospheric Hydrocarbon & Bilge Gas Sniffer (`phase-04-pump-room-gas-engine.md`)
- **Phase 05:** Central Facade, Typer CLI Sub-Apps & FastMCP Integration (`phase-05-central-facade-cli-mcp.md`)
- **Phase 06:** Zero-Mock Testing & Quality Verification (`phase-06-zero-mock-testing-verification.md`)

## Key Standards
- ISO 8217:2024 & CIMAC: Fuel separation G-force, Al+Si reduction $\ge 85\%$, sludge discharge cycle $\le 2$h.
- SOLAS II-1 Reg 29/30 & IMO A.1052(27): Steering travel times ($35^\circ \to 30^\circ \le 28$s main, $15^\circ \to 15^\circ \le 60$s aux), 45s power failover.
- IMO Res. MSC.267(85) & DNV Anti-Heeling: Heel angle $|\theta| \le 1.0^\circ$, high-rate reversible ballast pumping.
- SOLAS II-2 Reg 4.5.10 & ISGOTT Ch. 5: Pump room hydrocarbon sampling (10%/20% LEL), H2S $\ge 5$ ppm, $\ge 20$ ACH ventilation.
- Architecture: Strict < 200 LOC per file, 100% type annotations, zero mocks.
