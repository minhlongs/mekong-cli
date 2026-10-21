# Research Report: Phases 379-380

## 1. Phase 379: Marine Air Systems (SOLAS Ch II-1, Reg 26)
- **Capacity:** Reversible (12 starts), Non-reversible (6 starts) without replenishment.
- **Charging:** < 1h from 0 to 30 bar. 
- **Safety:** Relief valves @ 1.1x working pressure. Emergency floor: 12 bar.
- **Logic:** `replenishment_time = hours(1.0)`, `starts_min = engine_type == 'reversible' ? 12 : 6`.
- **Interlock:** Moisture blowdown solenoid active after compressor cycle > 30m.

## 2. Phase 380: Cooling Ingress (IACS UR M62)
- **Architecture:** High/Low switchover required for siltation/stability.
- **Thresholds:** `dP_clog > 0.5 bar` triggers duplex switch/backwash.
- **Anti-Fouling:** Electrolytic current `I = k * Q`. `T_sea < 2.0C` enables steam purge. 

## Trade-off Matrix
| Option | Complexity | Performance | Cost | Maintenance |
| :--- | :--- | :--- | :--- | :--- |
| PLC Logic | Low | High | Medium | Predictable |
| Analog Logic | High | Low | Low | Hard to debug |

## Adoption Risk
- **Regulatory:** Compliance with IACS/SOLAS is mandatory; non-compliance leads to PSC detention.
- **Maturity:** Standardized industrial patterns (PLC/SCADA); low abandonment risk.

## Recommendations
- **Rank 1:** PLC-based distributed I/O for system interlocks.
- **Rank 2:** Manual pneumatic fallback for critical engine start air.

## Unresolved Questions
- Specific `k` constant for MGPS varying by anode alloy composition.
- Integration requirement for specific class society (DNV vs ClassNK) emergency protocols.
