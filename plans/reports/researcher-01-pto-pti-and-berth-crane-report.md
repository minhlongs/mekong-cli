---
name: researcher-01-pto-pti-and-berth-crane-report
description: Maritime Phases 371 (PTO/PTI Hybrid) and 372 (BAP/QCSP) technical/regulatory analysis
metadata:
  type: reference
---

# Research Report: Maritime Phases 371 & 372

## Phase 371: Marine PTO/PTI Hybrid System
### Regulatory Framework
- **DNV-RU-SHIP Pt.4 Ch.8**: Defines requirements for shaft generator systems.
- **IEC 60092-501**: Special features for electric propulsion/power systems.
- **IMO MEPC.333(76)**: EEXI/CII compliant operational reduction via power limiting.

### Performance Logic
- ** PTO (Take-Off)**: ME (Main Engine) drives shaft generator to feed auxiliary grid.
  - Constraint: Inhibit if ME speed < 65% MCR; Torque > 80% MCR.
  - Gain: $SFOC_{eff} = [(P_{aux} * SFC_{aux}) - (P_{shaft} * SFC_{ME})] / P_{total}$.
- **PTI (Take-In)**: Power Take-In mode for boost or PTH (emergency).

## Phase 372: Port BAP & QCSP Optimization
### Operational Criteria
- **Berth Allocation (BAP)**:
  - Safety clearance: $L_{ship} + 30m$ (15m each side).
  - Draft check: $d_{ship} + 1.5m (UKC) <= Depth_{berth}$.
- **Crane Scheduling (QCSP)**:
  - Minimum clearance: $D_{crane} >= 35m$.
  - Crane productivity: 25-32 moves/hr.
  - Tidal window: Deep-draft access gated on high-tide delta for Cai Mep-Thi Vai.

### Compliance
- **UNCTAD/PIANC**: Global standard for port quay scheduling.
- **Decision 1579/QD-TTg**: Vietnam seaport master plan alignment.

## Trade-off Matrix
| Dimension | PTO/PTI (Phase 371) | BAP/QCSP (Phase 372) |
| :--- | :--- | :--- |
| **Complexity** | High (Hard real-time I/O) | High (NP-Hard combinatorial) |
| **Performance** | Fuel/Emission reduction | Turnaround time/Throughput |
| **Maintenance** | Mechanical/Electrical safety | Algorithmic state updates |

## Architectural Fit
- **Requirement**: Integrate logic as encapsulated services. 
- **PTO/PTI**: Zod schema for real-time engine telemetry validation.
- **BAP/QCSP**: Graph-based approach for non-crossing crane constraints.
