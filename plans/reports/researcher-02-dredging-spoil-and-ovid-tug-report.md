---
name: maritime-phases-365-366-dredging-ovid-tug-research
description: Research on Port Dredging Sediment Quality & Reuse (Phase 365) and OCIMF OVID Tugboat Vetting (Phase 366)
metadata:
  type: reference
---

# Maritime Phases 365-366 Research Report

## Phase 365: Port Dredging Sediment Quality & Beneficial Reuse
- **Regs**: London Protocol (1996) "Specific Guidelines for Assessment of Dredged Material" vs. Vietnam QCVN 43:2017/BTNMT.
- **Contamination Metrics (mg/kg dry weight)**:
  - Heavy Metals: As, Cd, Pb, Hg, Cu, Zn limits; QCVN 43 Class 1 sets baseline restriction for marine disposal.
  - PAHs: Total 16 EPA PAHs <= 10.0 mg/kg for Class 1.
  - Organotins (TBT): Threshold 0.001 mg/kg; any detection generally disqualifies open-water disposal.
- **Classification & Reuse**:
  - Beneficial Reuse Gate (Land Reclamation & Coastal Dykes): Dewatering solids content >= 60.0%, Unconfined Compressive Strength (UCS) >= 50.0 kPa after 28 days of lime/cement stabilization.
  - Capped disposal required for moderate contamination; hazardous categorization if exceeding threshold.
- **Architecture**:
  ```python
  @dataclass
  class SedimentQualityInput:
      sample_id: str
      tbt_mg_kg: float              # <= 0.001
      total_pah_mg_kg: float        # <= 10.0
      heavy_metals_mg_kg: dict      # As, Cd, Pb, Hg, Cu, Zn
      solids_content_pct: float     # >= 60.0%
      stabilized_ucs_kpa: float     # >= 50.0 kPa
  ```

## Phase 366: OCIMF OVID Port Tug Vetting & Towing Winch Safety
- **Regs**: OCIMF Offshore Vessel Inspection Database (OVID), DNV-GL/ABS Towing Gear Rules, STCW Code III/3.
- **Bollard Pull (BP)**: Verification of certified continuous BP (t-pull / kN) vs trial maximum.
- **Winch Brake Holding Capacity**:
  - Mandatory static brake holding capacity >= 80.0% of towline Minimum Breaking Load (MBL).
  - Emergency towline release under full load (< 3.0s trip).
- **Escort Tug Hydrodynamic Forces**:
  - Steering force F_y and braking force F_x at speed (up to 10 knots).
- **Crew Competency**:
  - STCW III/3 endorsement mandatory for senior tug officers.
- **Architecture**:
  ```python
  @dataclass
  class TugVettingInput:
      vessel_id: str
      certified_continuous_bp_kn: float
      towline_mbl_kn: float
      winch_brake_holding_kn: float # >= 0.80 * towline_mbl_kn
      escort_speed_knots: float
      stcw_iii_3_compliant: bool
  ```
