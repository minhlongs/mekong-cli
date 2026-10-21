# Phase 04: Shipboard HVAC Condensate & Greywater Circular Reclamation Engine (Phase 378)

## Overview
- **Target File**: `src/core/maritime/phase_378_hvac_condensate_greywater_reuse.py` (< 200 LOC)
- **Standard**: IMO Res. MEPC.227(64), WHO Guide to Ship Sanitation, QCVN 14:2008/BTNMT Class A
- **Objective**: Model tropical air conditioning moisture condensation harvesting ($\dot{m}_{cond} = \dot{m}_{air} \Delta w$), test condensate TDS (< 30 ppm) for auxiliary boiler feed reuse, evaluate multi-stage greywater filtration/UV disinfection, and enforce zero discharge in sensitive marine zones.

## Key Formulas
- Condensate yield: $\dot{m}_{cond} = \dot{m}_{air} \cdot (w_{in} - w_{out})\ (kg/h)$
- Freshwater bunkering cost savings: $Savings = (V_{cond} + V_{grey\_reclaimed}) \cdot Cost_{water}$
- Quality standards (QCVN 14:2008/BTNMT Class A):
  - $BOD_5 \le 20\text{ mg/L}$
  - $TSS \le 10\text{ mg/L}$
  - Coliform $\le 100\text{ MPN/100mL}$
  - Turbidity $\le 2.0\text{ NTU}$
  - Condensate TDS $< 30\text{ ppm}$

## Todo Checklist
- [ ] Implement `WaterReclamationInput` and `WaterReclamationReport` dataclasses
- [ ] Implement `HvacCondensateGreywaterEngine` with circular reuse logic
- [ ] Verify < 200 LOC constraint
