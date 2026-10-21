# Phase 01: Marine Centrifugal Fuel Oil Purifier & Clarifier Automation

## Overview
- Priority: High
- Status: Ready to Implement
- Standards: ISO 8217:2024, CIMAC Fuel Treatment Guidelines, MEPC.1/Circ.753
- Target File: `src/core/maritime/phase_383_marine_fuel_purifier_clarifier.py` (< 200 LOC)

## Mathematical & Regulatory Rules
- Centrifugal G-force: $G = r \omega^2 / g$, nominal $5,000\times g$ to $7,500\times g$ for high-speed bowl.
- Separation efficiency: $\eta = (C_{\text{in}} - C_{\text{out}}) / C_{\text{in}} \ge 85\%$.
- Residual catalytic fines limit: $C_{\text{out}} \le 15.0$ ppm (warning at $> 15.0$ ppm, trip at $> 25.0$ ppm).
- Separation temperature interlock: $98.0^\circ\text{C} \pm 2.0^\circ\text{C}$ for heavy fuel oil (HFO).
- Vibration velocity limit: $\le 7.1$ mm/s RMS (ISO 10816-3).
- Operating water pressure: $P \ge 2.5$ bar; sludge discharge interval $\le 2.0$ hours.

## Related Files
- Create: `src/core/maritime/phase_383_marine_fuel_purifier_clarifier.py`
