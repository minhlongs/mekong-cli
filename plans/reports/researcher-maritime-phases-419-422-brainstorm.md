---
name: maritime-phases-419-422
description: Engineering research for maritime auxiliary systems (Boilers, STP, Ballast, Fire suppression)
metadata:
  type: reference
---

# Maritime Phases 419-422 Research

## Phase 419: Marine Auxiliary Boiler (IACS/SOLAS/ASME)
- **Regs**: IACS M53, SOLAS II-1/32, ASME BPVC Sec I.
- **Physics**: 3-element level (Feed Flow, Steam Flow, Drum Level). PID gain scheduling for swell/shrink suppression.
- **Telemetry**: Drum level (DP), Main steam flow, Feed water flow. 
- **Trips**: Low-low water (LLWL), High-high steam pressure.

## Phase 420: STP Electrolytic Chlorination (MEPC.227(64))
- **Regs**: MARPOL Annex IV.
- **Physics**: Electrolytic NaOCl generation. Residual Cl2 monitoring for dechlorination (Na2S2O3 / Activated Carbon).
- **Telemetry**: Turbidity, BOD5 proxies (COD), TColi count, Residual Cl2.
- **Trips**: Aeration blower failure, Effluent valve interlock.

## Phase 421: ICCP/Zn Anode Depletion (DNV-RP-B401/PSPC)
- **Regs**: MSC.215(82) PSPC.
- **Physics**: Polarization (E_corr). Cathodic protection potential drift tracking. Zn sacrificial mass balance.
- **Telemetry**: Ref electrode potential (Ag/AgCl), Anode current (I_anode).
- **Trips**: Anode ground fault, Reference electrode signal drift.

## Phase 422: Hyper-Mist/Water-Mist (SOLAS/FSS/MSC.1165)
- **Regs**: FSS Code Ch 7.
- **Physics**: Droplet diameter (Dv0.9 < 100um), momentum (inertia mass), Latent heat of vaporization.
- **Telemetry**: Nozzle line pressure (P_line), Flow rate (Q_mist).
- **Trips**: Low pump suction pressure, High nozzle pressure burst.

## Implementation Architecture
- Separate dataclass per phase (<180 LOC).
- Architecture: `TelemetryInput` -> `StateTransition` -> `SafetyInterlockDelegate`.

## Unresolved Questions
- Sensor calibration range for STP residual Cl2 (target < 0.5 ppm).
- FSS Code fire pump suction head margin for specific Hyper-Mist nozzle arrays.
