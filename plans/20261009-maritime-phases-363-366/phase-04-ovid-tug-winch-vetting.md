# Phase 04: OCIMF OVID Tug Vetting & Towing Winch Safety Engine

## Overview
- Module: `src/core/maritime/phase_366_ovid_tug_winch_vetting.py`
- Regulatory Standards: OCIMF OVID Guidelines, IMCA M 149 / CMID, STCW III/3 endorsement.

## Technical Requirements
- Certified Continuous Bollard Pull (BP) verification.
- Towing winch static brake holding capacity: $\ge 80.0\% \cdot \text{MBL}_{\text{towline}}$.
- Emergency quick release actuation: $< 3.0\text{ s}$ under maximum load.
- Escort steering force $F_y$ and braking force $F_x$ calculation at 10 knots.
- Crew competency: Master and Chief Engineer STCW III/3 towing endorsement.

## Data Schema
```python
@dataclass
class TugVettingInput:
    tug_id: str
    certified_bollard_pull_t: float
    towline_mbl_t: float
    winch_brake_hold_t: float
    quick_release_time_s: float
    escort_speed_knots: float
    has_stcw_iii_3_endorsement: bool

@dataclass
class TugVettingResult:
    tug_id: str
    brake_hold_ratio_pct: float
    is_winch_brake_compliant: bool
    is_quick_release_safe: bool
    escort_steering_force_kn: float
    escort_braking_force_kn: float
    vetting_status: str
    advisories: List[str]
```
