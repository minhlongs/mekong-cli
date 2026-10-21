# Phase 03: Automatic Anti-Heeling Ballast Pumping & Rapid Counter-Flooding

## Overview
- Priority: High
- Status: Ready to Implement
- Standards: IMO Res. MSC.267(85), DNV Anti-Heeling Guidelines, Container Port Cargo Safety
- Target File: `src/core/maritime/phase_385_anti_heeling_ballast_pumping.py` (< 200 LOC)

## Mathematical & Regulatory Rules
- Heel angle operational limits: Max allowable static list during container handling $|\theta| \le 1.0^\circ$.
- Warning threshold: $|\theta| > 1.5^\circ$; Emergency cargo loading stop: $|\theta| \ge 2.5^\circ$.
- Dynamic heel rate threshold: $d\theta/dt > 0.15^\circ/\text{s}$ triggers rapid counter-flooding.
- Counter-flooding restoring moment: $M_{\text{restore}} = \Delta \cdot GM_T \cdot \sin(\theta)$.
- Reversible propeller pump / valve response time: flow reversal in $\le 10.0$ seconds.
- Tank level interlocks: minimum level $5\%$ (cavitation protection), maximum level $95\%$ (overfill).

## Related Files
- Create: `src/core/maritime/phase_385_anti_heeling_ballast_pumping.py`
