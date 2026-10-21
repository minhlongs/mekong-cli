# Phase 01: Voyage Weather Routing & CII Dynamic Decarbonization Engine (Phase 375)

## Overview
- **Target File**: `src/core/maritime/phase_375_voyage_weather_routing_cii.py` (< 200 LOC)
- **Standard**: IMO Res. MEPC.328(76), ISO 15016:2015, SEEMP Part III
- **Objective**: Model added wave/wind resistance, cubic propulsion power law ($P \propto V^3$), attained vs required CII ($g CO_2 / (DWT \cdot nm)$), energy rating (A to E), and SEEMP III speed reduction actions.

## Key Formulas
- Added weather resistance: $\Delta P_{weather} = P_{calm} \cdot (1 + \alpha_{Beaufort} \cdot BF^2)$
- Required CII: $CII_{req} = a \cdot DWT^{-c} \cdot (1 - Z / 100)$
- Attained CII: $CII_{att} = \frac{\sum (F_j \cdot C_{F,j})}{DWT \cdot D_{travel}} \cdot 10^6$
- Rating Boundaries:
  - Ratio $\le 0.83 \to$ A (Superior)
  - $0.83 < Ratio \le 0.94 \to$ B (Minor superior)
  - $0.94 < Ratio \le 1.06 \to$ C (Standard)
  - $1.06 < Ratio \le 1.19 \to$ D (Minor inferior - SEEMP alert)
  - $Ratio > 1.19 \to$ E (Inferior - Mandatory CAP plan)
- Optimal JIT speed reduction for storm evasion: $V_{opt} = V_{base} \cdot \left(\frac{CII_{req}}{CII_{att}}\right)^{1/3}$

## Todo Checklist
- [ ] Implement `VoyageRoutingInput`, `CiiRating`, and `VoyageWeatherCiiReport` dataclasses
- [ ] Implement `VoyageWeatherRoutingCiiEngine` with pure Python calculation (no mocks)
- [ ] Verify < 200 LOC constraint
