# Phase 02: Oil Tanker VOC Emission Recovery & Vapor Balancing Engine (Phase 376)

## Overview
- **Target File**: `src/core/maritime/phase_376_voc_vapor_recovery_balancing.py` (< 200 LOC)
- **Standard**: MARPOL Annex VI Reg 15, IMO MSC/Circ.585, OCIMF Vapor Emission Control (VEC)
- **Objective**: Monitor closed-loop vapor recovery during cargo loading, enforce inert gas $O_2 \le 8\%$ safety interlocks, calculate vapor balancing ratio ($Q_{vapor} \ge 1.25 \times Q_{loading}$), and estimate GHG carbon offset ($2.8\text{ kg } CO_2\text{ eq / kg VOC}$).

## Key Formulas
- Vapor balancing requirement: $Q_{vapor\_req} = 1.25 \cdot Q_{loading\_rate}\ (m^3/h)$
- Recovered VOC mass: $M_{VOC} = V_{vapor} \cdot \rho_{VOC} \cdot \eta_{recovery}$
- CO2 equivalent offset: $\Delta E_{CO2} = M_{VOC} \cdot 2.8\text{ kg } CO_2\text{ eq}$
- Safety envelope:
  - $O_2 \le 8.0\%\text{ vol}$ (mandatory inerting lockout if exceeded)
  - Tank pressure $P \le 80\%\ P/V_{setting}$ (pressure relief trigger)
  - $H_2S \le 5.0\text{ ppm}$ toxic gas threshold

## Todo Checklist
- [ ] Implement `VocRecoveryInput` and `VocRecoveryReport` dataclasses
- [ ] Implement `VocVaporRecoveryBalancingEngine` with strict validation rules
- [ ] Verify < 200 LOC constraint
