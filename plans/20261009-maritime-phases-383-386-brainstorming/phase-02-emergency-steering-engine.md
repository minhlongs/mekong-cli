# Phase 02: Auxiliary Emergency Steering Gear & Hydraulic Power Actuation

## Overview
- Priority: High
- Status: Ready to Implement
- Standards: SOLAS Ch II-1 Reg 29 & 30, IMO Res. A.1052(27), ClassNK/DNV Rules
- Target File: `src/core/maritime/phase_384_auxiliary_emergency_steering.py` (< 200 LOC)

## Mathematical & Regulatory Rules
- Main steering gear performance: $35^\circ$ port to $30^\circ$ starboard in $\le 28.0$ seconds at max service speed.
- Auxiliary / emergency steering gear: $15^\circ$ port to $15^\circ$ starboard in $\le 60.0$ seconds at $\max(0.5 V_{\text{max}}, 7.0\text{ knots})$.
- Standby pump automatic failover: start and restore hydraulic pressure within $\le 45.0$ seconds.
- Hydraulic system relief valve: setpoint $1.25 \times P_{\text{work}}$ (nominal 200 bar $\to$ 250 bar).
- Hydraulic oil storage tank: low level alarm at $\le 40\%$ tank volume.
- Rudder angle transmitter discrepancy alarm: $|\theta_{\text{demand}} - \theta_{\text{actual}}| > 4.0^\circ$ for $\ge 3.0$ seconds.

## Related Files
- Create: `src/core/maritime/phase_384_auxiliary_emergency_steering.py`
