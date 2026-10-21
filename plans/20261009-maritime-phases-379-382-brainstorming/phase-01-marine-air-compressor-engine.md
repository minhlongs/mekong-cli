# Phase 01: Marine Starting Air & Air Reservoir Compressor Automation

## Overview
- Priority: High
- Status: Ready to Implement
- Standards: SOLAS Ch II-1 Reg 26, ClassNK / DNV Machinery Rules
- Target File: `src/core/maritime/phase_379_marine_starting_air_compressor.py` (< 200 LOC)

## Mathematical & Regulatory Rules
- Reversible engine: $\ge 12$ consecutive starts without replenishment; non-reversible: $\ge 6$ starts.
- Nominal working pressure: 30.0 bar (3.0 MPa).
- Low air alarm threshold: $< 18.0$ bar; Emergency starting floor: $< 12.0$ bar (lockout/blackout hazard).
- Compressor recharge time: dual compressors must recharge from 0 (or atmospheric) to 30.0 bar in $\le 60.0$ min.
- Safety relief valve setpoint: $1.10 \times P_{\text{work}} = 33.0$ bar.
- Automatic moisture blowdown: active if compressor running time $> 30$ min and drain valve opens 5 seconds.

## Related Files
- Create: `src/core/maritime/phase_379_marine_starting_air_compressor.py`
