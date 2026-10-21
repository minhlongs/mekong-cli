# Phase 01: Maritime Phases 403-406 Core Engines

## Files to Create (< 200 LOC each)
1. `src/core/maritime/phase_403_bilge_water_separator_odmcs.py`
   - Stokes settling velocity, coalescence efficiency, 15 ppm ASD trip, non-volatile audit logger.
2. `src/core/maritime/phase_404_inert_gas_n2_generator.py`
   - Membrane permeability, O2 < 5% alarm, O2 >= 8% safety trip venting, P/V breaker hydrostatics.
3. `src/core/maritime/phase_405_stern_tube_bio_lubrication.py`
   - Walther-ASTM viscosity, Sommerfeld number, film parameter lambda > 3, draft differential delta P, EAL degradation.
4. `src/core/maritime/phase_406_water_mist_fire_extinguishing.py`
   - Droplet size D99 < 100/300 um, high-pressure K-factor nozzle, latent heat cooling, steam 1:1600 expansion, O2 depletion.

## Success Criteria
- Deterministic physics equations without mocks.
- Strictly < 200 LOC per file.
