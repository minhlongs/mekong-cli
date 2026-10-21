# Phase 03: Automatic Draft & Tank Sounding Gauging Radar/Bubbler

## Overview
- Priority: High
- Status: Ready to Implement
- Standards: IMO Res. MSC.267(85) (2008 IS Code), SOLAS XII Reg 12
- Target File: `src/core/maritime/phase_381_draft_tank_sounding_gauging.py` (< 200 LOC)

## Mathematical & Regulatory Rules
- Hydrostatic Draft Survey:
  - Quarter-mean draft: $d_M = (d_{\text{fore}} + 6 \cdot d_{\text{mid}} + d_{\text{aft}}) / 8$.
  - Trim: $t = d_{\text{aft}} - d_{\text{fore}}$ (positive = trim by stern, negative = trim by head).
  - Heel / List angle: $\theta = \arctan((d_{\text{mid\_stbd}} - d_{\text{mid\_port}}) / B)$ in degrees.
  - Hull deflection: $h_{\text{sag}} = d_{\text{mid}} - (d_{\text{fore}} + d_{\text{aft}})/2$ (positive = sagging, negative = hogging).
- Tank Level Sounding & Ullage:
  - Ullage = $H_{\text{tank}} - h_{\text{liquid}}$; Filling percentage = $(h_{\text{liquid}} / H_{\text{tank}}) \times 100\%$.
  - High Level Alarm at $\ge 95.0\%$; Overfill Alarm at $\ge 98.0\%$.
  - Ingress protection alarm if unexpected water ingress rate $> 0.1$ m/h in dry cargo/void space.

## Related Files
- Create: `src/core/maritime/phase_381_draft_tank_sounding_gauging.py`
