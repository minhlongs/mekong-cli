# Phase 01: Marine Shaft Generator PTO/PTI Hybrid Engine

## Context & Standards
- DNV-RU-SHIP Pt.4 Ch.8, IEC 60092-501, IMO MEPC.333(76) (EEXI/CII).

## Requirements
- Mode: `PTO` (Power Take-Off), `PTI` (Power Take-In / Booster), `PTH` (Take-Me-Home / Emergency), or `DISENGAGED`.
- Inhibit PTO if main engine load/speed < 65.0% MCR.
- Over-torque warning if ME load + PTO power equivalent > 80.0% MCR.
- Calculate fuel savings: $\Delta F = P_{\text{shaft}} \cdot (\text{SFOC}_{\text{aux}} - \text{SFOC}_{\text{ME}}) / 1000\text{ kg/h}$.

## Target File
- `src/core/maritime/phase_371_shaft_generator_pto_pti.py` (< 200 LOC)
