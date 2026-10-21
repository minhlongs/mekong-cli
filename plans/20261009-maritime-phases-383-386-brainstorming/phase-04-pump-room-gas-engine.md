# Phase 04: Tanker Pump Room Atmospheric Hydrocarbon & Bilge Gas Sniffer

## Overview
- Priority: High
- Status: Ready to Implement
- Standards: SOLAS Ch II-2 Reg 4.5.10, ISGOTT Ch. 5, IMO MSC.1/Circ.1370
- Target File: `src/core/maritime/phase_386_tanker_pumproom_gas_sniffer.py` (< 200 LOC)

## Mathematical & Regulatory Rules
- Hydrocarbon gas sampling: pre-alarm at $\ge 10.0\%$ LEL; critical alarm & cargo pump trip at $\ge 20.0\%$ LEL.
- Hydrogen Sulfide ($H_2S$): warning at $\ge 5.0$ ppm; toxic evacuation alarm at $\ge 10.0$ ppm.
- Oxygen ($O_2$): normal $\ge 20.8\%$; deficient alarm at $< 19.5\%$.
- Mechanical extraction ventilation: minimum rate $\ge 20.0$ air changes per hour (ACH).
- Interlock: Cargo pump drive turbines/motors cannot start without ventilation differential pressure confirmation.
- Bilge flood sensor: independent optical/float switch triggers alarm if bilge water depth $> 0.30$ m.

## Related Files
- Create: `src/core/maritime/phase_386_tanker_pumproom_gas_sniffer.py`
