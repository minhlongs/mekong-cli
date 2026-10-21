---
name: maritime-phases-363-364-lsa-pms-research
description: Research on LSA free-fall lifeboats (Phase 363) and marine Power Management Systems (Phase 364)
metadata:
  type: reference
---

# Maritime Phases 363-364 Research Report

## Phase 363: LSA Free-Fall Lifeboat & HRU
- **Regs**: SOLAS III/13, LSA Code IV, MSC.81(70).
- **HRU**: Must activate buoyancy-driven between 1.5m and 4.0m depth. Shear-pin release threshold must prevent premature deployment in <1.5m wave slap.
- **Dynamics**: 
  - Water entry angle: 50°-65°.
  - Accel limit: ≤15g (MSC.81(70) criteria).
  - Interlock: Dual-redundant manual release to prevent accidental free-fall.
- **Architecture**:
  ```python
  @dataclass
  class LifeboatDynamics:
      max_acceleration_g: float  # <= 15.0
      entry_angle_deg: float     # 50.0 - 65.0
      hru_activation_depth_m: float # 1.5 - 4.0
  ```

## Phase 364: Marine PMS & Blackout Prevention
- **Regs**: SOLAS II-1/53, IEC 60092-202, Classification (DNV/ABS/VR).
- **Load Sharing**: Droop control for transient robustness; Isochronous for precise frequency.
- **Protection**:
  - Auto-start standby: ≥85% MCR.
  - Blackout protection: Under-frequency trip at 57.0Hz (>0.5s) / Under-voltage 0.85 U_n (>0.5s).
  - Tripping logic: Preferential load shed (Non-essential -> Essential).
- **Architecture**:
  ```python
  @dataclass
  class PMSStatus:
      load_share_mode: str      # 'DROOP' | 'ISOCHRONOUS'
      active_mcr_pct: float     # Trigger standby at 85.0
      blackout_trip_hz: float   # 57.0 (>= 0.5s)
      preferential_shed: List[int] # Stages
  ```

## Trade-offs & Adoption Risk
- **HRU Maturity**: COTS units (Hammar H20) are high-reliability; regulatory compliance is absolute.
- **PMS Complexity**: Isochronous sharing requires robust communication (CAN bus/Modbus) between DG controllers; high-risk of firmware mismatch.

## Unresolved
- Specific inter-manufacturer protocol standards for multi-brand DGs (DNV requirements on protocol abstraction).
