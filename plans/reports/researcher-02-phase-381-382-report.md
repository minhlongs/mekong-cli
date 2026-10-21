# Technical Research Report: Phases 381-382 (Marine Stability & Navigation)

## 1. Phase 381: Draft & Tank Sounding Gauging
### Regulatory Standards & Mathematical Models
- **Stability:** IMO Res. MSC.267(85) (2008 IS Code) requires intact stability verification across all loading conditions.
- **Water Alarms:** SOLAS XII Reg 12 mandates water ingress detection in cargo holds for bulkers.
- **Draft Geometry:**
  - Quarter-mean draft: $d_M = (d_F + 6d_M + d_A) / 8$.
  - Deflection: $h_{sag} = d_{mid} - (d_F + d_A) / 2$.
  - Heel: $\theta = \arctan((d_{mid\_stbd} - d_{mid\_port}) / B)$, where $B$ is ship breadth.
- **Level Gauging:**
  - Radar: FMCW (24/80GHz) for precision ullage ($U = H - h$).
  - Bubbler: Hydrostatic pressure $P = \rho gh + P_{atm}$.
  - Safety Triggers: 95% (High) / 98% (Overfill) logic per MARPOL/IBC/IGC codes.

## 2. Phase 382: Pilotage & Collision Avoidance (ARPA)
### Kinematics & Safety Gates
- **Performance:** IMO Res. A.823(19) & MSC.192(79).
- **Target Tracking:** 
  - $V_r = V_t - V_o$ (Relative velocity vector).
  - $TCPA = -(P_r \cdot V_r) / |V_r|^2$.
  - $CPA = |P_r + V_r \cdot TCPA|$.
- **Safety Thresholds:** Collision alarm at $CPA < 1.0\,\text{nm}$ and $TCPA < 12.0\,\text{min}$.
- **Operational Gates:**
  - Pilot Boarding: $V_{ground} \leq 8.0\,\text{kn}$.
  - Tug Rendezvous: Based on DWT-scaled bollard pull $\geq 10-15\%$ of total deadweight force requirement.

## Evaluation & Trade-offs
| Dimension | Radar (Tank) | Bubbler (Tank) | ARPA (Navigation) |
| :--- | :--- | :--- | :--- |
| **Complexity** | High (Calibration) | Low (Mechanical) | High (Vector Math) |
| **Maintenance** | Low (Non-contact) | Med (Air supply) | Med (Sensor sync) |
| **Reliability** | Excellent | Robust in sludge | Context-dependent |

## Recommendations
1. **Radar/Bubbler:** Prefer 80GHz FMCW for cargo; utilize bubbler for high-viscosity sludge tanks where radar signal scatter is probable.
2. **ARPA/Pilotage:** Implement a state-based safety gate (BCR/BCT) in addition to traditional CPA/TCPA to account for narrow channel geometry (COLREGs Rule 9).
3. **Architecture:** Decouple sensors into NMEA 0183/2000 hardware abstraction layers to facilitate future DNV-class BESS integration.

*Limitations: Does not cover specific proprietary firmware calibration sequences for radar/bubbler units.*
