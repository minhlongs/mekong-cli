---
name: vts-css-cargo-research
description: VTS navigation management (COLREGs/IMO) and Project Cargo/OOG sea fastening (CSS Code) technical standards.
metadata:
  type: reference
---

# Maritime Phases 335-336 Technical Research

## Phase 335: VTS & TSS Navigation Management
- Regulatory: [[IMO Res. A.1158(32)]] establishes mandatory VTS criteria.
- Core Metrics: 
  - CPA/TCPA: Closest Point of Approach (distance) / Time to Closest Point of Approach.
  - Cross-Track Error (XTE): $|Distance_{nav} - Distance_{plan}|$
- Logic: Wrong-way traffic in lanes (Rule 10) trigger TOS alerts.
- Edge Case: Shadow/Ghost peaks in radar clutter mimicking targets.

## Phase 336: Project Cargo & Heavy Lift OOG (CSS Code)
- Regulatory: [[IMO Code of Safe Practice for Cargo Stowage and Securing (CSS Code)]] Annex 13.
- Force Algebra (Accelerations):
  - $a_x = \text{longitudinal}, a_y = \text{transverse}, a_z = \text{vertical}$
  - Requirement: $S_F = \frac{MSL \times n}{F_i} \ge 1.25$ (Sliding/Tipping Stability).
- Friction Model: $F_{fric} = \mu \times (W \times (1 - a_v) - F_v)$, where $\mu \in [0.1, 0.4]$ based on dunnage.

## Architecture Guidelines
- Data Models: 
  - `VtsTarget`: {id, lat, lon, sog, cog, cpa, tcpa, lane_id}
  - `LashingPlan`: {cargo_id, total_msl, acc_x, acc_y, friction, safety_factor}
- Validation: Enforce $S_F \ge 1.25$ on every calculation iteration.
