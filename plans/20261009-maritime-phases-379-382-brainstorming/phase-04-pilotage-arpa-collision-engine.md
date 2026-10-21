# Phase 04: Port Pilotage Navigational Safety & ARPA Collision Avoidance

## Overview
- Priority: High
- Status: Ready to Implement
- Standards: IMO Res. A.823(19) & MSC.192(79), COLREGs Rule 9 & Rule 10
- Target File: `src/core/maritime/phase_382_port_pilotage_arpa_collision.py` (< 200 LOC)

## Mathematical & Regulatory Rules
- Kinematic Relative Vector Calculations:
  - $\vec{P}_r = \vec{P}_{\text{target}} - \vec{P}_{\text{own}}$ in Cartesian nautical miles.
  - $\vec{V}_r = \vec{V}_{\text{target}} - \vec{V}_{\text{own}}$ in knots.
  - $\text{TCPA} = -(\vec{P}_r \cdot \vec{V}_r) / |\vec{V}_r|^2$ (hours $\rightarrow$ converted to minutes).
  - $\text{CPA} = |\vec{P}_r + \vec{V}_r \cdot \text{TCPA}|$ (nautical miles).
- Collision Danger Thresholds:
  - Alarm if $\text{CPA} < 1.0$ NM and $0 \le \text{TCPA} \le 12.0$ minutes.
- Port Pilotage Constraints:
  - Ground speed at Pilot Boarding Station $\le 8.0$ knots.
  - Tug escort bollard pull ratio check: $T_{\text{bp}} \ge 0.0012 \times \text{DWT}$ for safe escort tethering.

## Related Files
- Create: `src/core/maritime/phase_382_port_pilotage_arpa_collision.py`
