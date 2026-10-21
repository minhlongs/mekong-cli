---
name: maritime-phases-487-490-report
description: Research report for Maritime Safety Automation Phases 487-490 for mekong-cli.
metadata:
  type: reference
---

# Maritime Safety Automation Phases 487-490 Report

## Phase 487: ME Cylinder Head Jacket Cooling
**Focus**: IACS UR M10/M3 compliance.
- **Specs**: HT water inlet/outlet delta monitoring. Trip at >= 92°C outlet. 
- **Interlock**: Flowrate (dP) + Expansion tank level (alarm < 30%).
- **Arch**: PID loop for jacket temp vs engine load command.

## Phase 488: Deck Water Seal Dry-Run
**Focus**: SOLAS II-2/4.5.5 Inert Gas Systems (IGS).
- **Specs**: Non-return seal maintenance. Min water column > 450mm.
- **Interlock**: Level sensor + auto-fill pump logic.
- **Environmental**: Trace heating interlock for ambients < 5°C.

## Phase 489: Central Cooling (HT/LT) 3-Way Valve
**Focus**: IACS UR M14 optimization.
- **Specs**: LT target 36°C constant. 
- **Arch**: HT jacket mixing valve PID based on engine demand. Seawater pump VSD control based on cooling head differential.

## Phase 490: Starting Air Compressor (SAC)
**Focus**: IACS UR M12 safety.
- **Specs**: Receiver max 30 bar. Relief valve at 31.5 bar.
- **Interlock**: Condensate purge (pre-start), stage-discharge temp check (> 160°C trip).

## Trade-off Matrix
| Feature | Complexity | Criticality | Risk |
| :--- | :--- | :--- | :--- |
| Phase 487 PID | Medium | High | Over-cooling during load dip |
| Phase 488 Dry-Run | Low | Extreme | IGS gas-backflow |
| Phase 489 3-Way | Medium | Medium | Thermal shock (HT side) |
| Phase 490 Unload | Low | High | Air supply loss |

## Adoption / Architectural Fit
- Fit: Logic maps directly to existing state-machine patterns in `mekong-cli`.
- Risk: Calibration hysteresis for temp sensors in turbulent flow. Need robust debouncing.

## Unresolved Questions
1. Does the current `mekong-cli` hardware abstraction layer support VSD control for seawater pumps (Phase 489)?
2. Is the trace heating control (Phase 488) handled via GPIO/Relay or an external PLC?
