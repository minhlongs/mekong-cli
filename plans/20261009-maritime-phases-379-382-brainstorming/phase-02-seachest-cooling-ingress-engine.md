# Phase 02: Seachest & Main Seawater Cooling Ingress Protection

## Overview
- Priority: High
- Status: Ready to Implement
- Standards: IACS UR M62, SOLAS Chapter II-1 Reg 26
- Target File: `src/core/maritime/phase_380_seachest_cooling_ingress.py` (< 200 LOC)

## Mathematical & Regulatory Rules
- Seachest Selection: High Seachest in river/shallow draft ($< 2.0$ m under-keel clearance) to prevent mud/sand ingestion; Low Seachest in deep open sea.
- Duplex Strainer Differential Pressure: $\Delta P = P_{\text{in}} - P_{\text{out}}$. If $\Delta P > 0.5$ bar $\rightarrow$ Clog alarm and switchover/backwash required.
- Marine Growth Prevention System (MGPS): Anode dissolution current $I = k \cdot Q_{\text{flow}}$ (where $k = 0.005$ A/(m³/h)); verify current output within $\pm 10\%$ of setpoint.
- Cold Water Protection: If $T_{\text{seawater}} < 2.0^\circ\text{C}$, trigger de-icing recirculation / steam purge interlock to prevent frazil ice blockage.

## Related Files
- Create: `src/core/maritime/phase_380_seachest_cooling_ingress.py`
