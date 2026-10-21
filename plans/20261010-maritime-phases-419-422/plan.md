# Plan: Maritime Phases 419-422 Auxiliary & Safety Automation

## Scope
Deliver Phases 419-422 in `mekong-cli`:
1. Phase 419: Marine Auxiliary Boiler Drum Level & Blowdown (`src/core/maritime/phase_419_boiler_drum_blowdown.py`)
2. Phase 420: STP Electrolytic Chlorination & Dechlorination (`src/core/maritime/phase_420_stp_electrolytic_chlorination.py`)
3. Phase 421: Ballast Tank Anodic Impressed Current & Zinc Depletion (`src/core/maritime/phase_421_ballast_anodic_protection.py`)
4. Phase 422: Hyper-Mist Local Water-Based Machinery Fire Extinguishing (`src/core/maritime/phase_422_hypermist_water_fire.py`)
5. Master Facade & CLI/FastMCP wiring
6. Zero-mock pytest test suite (`tests/test_maritime_phases_419_422_unit_suite.py`)

## Constraints
- Strictly < 180 LOC per module.
- Zero mocks, 100% deterministic physics & safety interlocks.
