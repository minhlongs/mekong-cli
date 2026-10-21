# Tech Stack & Architectural Spec: Maritime Phases 419-422

## Overview
Automates auxiliary marine machinery and life-safety systems under SOLAS, MARPOL, and IACS mandates.

## Systems Architecture
- **Phase 419: Marine Boiler Drum Level & Blowdown (`phase_419_boiler_drum_blowdown.py`)**
  - Standards: IACS M53, SOLAS II-1 Reg 32, ASME BPVC Sec I.
  - Controls: 3-element feedwater PID (drum level, steam flow, feedwater flow) to counter shrink/swell.
  - Telemetry: Drum differential pressure, continuous surface TDS, bottom blowdown timer, flame safeguard.
- **Phase 420: STP Electrolytic Chlorination & Dechlorination (`phase_420_stp_electrolytic_chlorination.py`)**
  - Standards: IMO Res MEPC.227(64), MARPOL Annex IV.
  - Controls: Electrolytic cell current regulation, sodium hypochlorite generation, bisulfite dosing.
  - Telemetry: Total residual chlorine (TRC < 0.5 mg/L), turbidity, COD/BOD5 proxies, fecal coliforms.
- **Phase 421: Ballast Tank ICCP & Sacrificial Anode Tracking (`phase_421_ballast_anodic_protection.py`)**
  - Standards: DNV-RP-B401, MSC.215(82) PSPC.
  - Controls: Ag/AgCl reference potential tracking (-850 mV to -1050 mV), current density, zinc consumption.
  - Safety: Over-protection lockout (< -1150 mV) against hydrogen embrittlement.
- **Phase 422: Hyper-Mist Machinery Space Fire Extinguishing (`phase_422_hypermist_water_fire.py`)**
  - Standards: SOLAS II-2 Reg 10.5.6, IMO MSC/Circ.1165, FSS Code Ch 7.
  - Controls: High-pressure 140 bar water-mist atomization (Dv0.9 < 100 μm), 2-out-of-2 flame/IR voting.
  - Telemetry: Section solenoid activation, suction head pressure, automatic sea chest changeover.

## Constraints & Standards
- Python 3.11+, typed dataclasses, zero mocks, strict deterministic physics.
- Each core module strictly < 180 LOC.
- Integration: `MaritimeAuxiliarySafetyEngine` facade and CLI/FastMCP exposure.
