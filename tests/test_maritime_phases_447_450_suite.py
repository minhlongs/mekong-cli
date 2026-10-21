"""Test Suite for Maritime Phases 447-450:
- Phase 447: Crude Oil Washing (IMO A.446(XI))
- Phase 448: Fixed Deck Foam Fire-Extinguishing (SOLAS II-2 Reg 10.8)
- Phase 449: Boiler Flue Gas Desulfurization (MARPOL Annex VI)
- Phase 450: Vapor Emission Control System (USCG 46 CFR 39)
- Master Facade: TankerSafetyIntegratedEngine
"""

import pytest

from src.core.maritime.phase_447_crude_oil_washing_machine import (
    CrudeOilWashingEngine,
    CowTelemetry,
    CowSafetyStatus,
)
from src.core.maritime.phase_448_fixed_deck_foam_extinguishing import (
    DeckFoamFireSystemEngine,
    DeckFoamTelemetry,
    DeckFoamStatus,
)
from src.core.maritime.phase_449_boiler_flue_gas_desulfurization import (
    BoilerFlueGasScrubberEngine,
    ScrubberTelemetry,
    ScrubberSafetyStatus,
)
from src.core.maritime.phase_450_vapor_emission_control_vecs import (
    VaporEmissionControlEngine,
    VecsTelemetry,
    VecsSafetyStatus,
)
from src.core.maritime_cow_foam_scrubber_vecs_engine import (
    TankerSafetyIntegratedEngine,
    TankerSafetyIntegratedTelemetry,
)


def test_phase_447_cow_nominal_and_trips():
    engine = CrudeOilWashingEngine()

    # Nominal operation
    nominal = engine.evaluate(
        CowTelemetry(
            wash_pressure_bar=9.5,
            inert_gas_o2_vol_pct=5.5,
            stripping_flow_m3_h=150.0,
            washing_flow_m3_h=100.0,
            machine_rotation_deg_s=2.0,
            oil_drain_valve_open=True,
        )
    )
    assert nominal.status == CowSafetyStatus.OPTIMAL
    assert nominal.is_wash_permitted is True
    assert nominal.stripping_ratio == 1.5

    # O2 emergency trip (> 8.0% vol)
    high_o2 = engine.evaluate(
        CowTelemetry(
            wash_pressure_bar=9.5,
            inert_gas_o2_vol_pct=8.5,
            stripping_flow_m3_h=150.0,
            washing_flow_m3_h=100.0,
            machine_rotation_deg_s=2.0,
        )
    )
    assert high_o2.status == CowSafetyStatus.O2_INTERLOCK_TRIP
    assert high_o2.is_wash_permitted is False

    # Stripping deficit (< 1.25)
    low_strip = engine.evaluate(
        CowTelemetry(
            wash_pressure_bar=9.5,
            inert_gas_o2_vol_pct=5.5,
            stripping_flow_m3_h=110.0,
            washing_flow_m3_h=100.0,
            machine_rotation_deg_s=2.0,
        )
    )
    assert low_strip.status == CowSafetyStatus.STRIPPING_DEFICIT_TRIP
    assert low_strip.is_wash_permitted is False


def test_phase_448_deck_foam_extinguishing():
    engine = DeckFoamFireSystemEngine()

    nominal = engine.evaluate(
        DeckFoamTelemetry(
            foam_solution_rate_l_min_m2=0.70,
            induction_ratio_pct=3.0,
            monitor_pressure_bar=6.8,
            throw_distance_m=55.0,
            foam_reserve_duration_min=24.0,
            isolation_valves_open=True,
        )
    )
    assert nominal.status == DeckFoamStatus.OPTIMAL
    assert nominal.is_ready_or_effective is True

    # Low reserve duration trip (< 20 mins)
    depleted = engine.evaluate(
        DeckFoamTelemetry(
            foam_solution_rate_l_min_m2=0.70,
            induction_ratio_pct=3.0,
            monitor_pressure_bar=6.8,
            throw_distance_m=55.0,
            foam_reserve_duration_min=15.0,
        )
    )
    assert depleted.status == DeckFoamStatus.DURATION_DEPLETED
    assert depleted.is_ready_or_effective is False


def test_phase_449_boiler_flue_gas_scrubber():
    engine = BoilerFlueGasScrubberEngine()

    nominal = engine.evaluate(
        ScrubberTelemetry(
            differential_pressure_pa=250.0,
            liquid_to_gas_ratio_l_nm3=2.8,
            demister_moisture_carryover_pct=0.8,
            discharge_ph=6.8,
            so2_ppm=15.0,
            co2_pct=4.5,
        )
    )
    assert nominal.status == ScrubberSafetyStatus.OPTIMAL
    assert nominal.is_scrubber_compliant is True

    # High differential pressure trip (> 550 Pa)
    clogged = engine.evaluate(
        ScrubberTelemetry(
            differential_pressure_pa=580.0,
            liquid_to_gas_ratio_l_nm3=2.8,
            demister_moisture_carryover_pct=0.8,
            discharge_ph=6.8,
            so2_ppm=15.0,
            co2_pct=4.5,
        )
    )
    assert clogged.status == ScrubberSafetyStatus.HIGH_DP_TRIP
    assert clogged.is_scrubber_compliant is False


def test_phase_450_vecs_safety_envelope():
    engine = VaporEmissionControlEngine()

    nominal = engine.evaluate(
        VecsTelemetry(
            manifold_pressure_mbar=30.0,
            vapor_o2_vol_pct=4.0,
            detonation_arrester_temp_c=25.0,
            knockout_drum_level_pct=20.0,
            vapor_shutoff_valve_open=True,
        )
    )
    assert nominal.status == VecsSafetyStatus.OPTIMAL
    assert nominal.is_transfer_permitted is True

    # Detonation arrester thermal trip (> 80 deg C)
    flashback = engine.evaluate(
        VecsTelemetry(
            manifold_pressure_mbar=30.0,
            vapor_o2_vol_pct=4.0,
            detonation_arrester_temp_c=85.0,
            knockout_drum_level_pct=20.0,
        )
    )
    assert flashback.status == VecsSafetyStatus.DETONATION_ARRESTER_TRIP
    assert flashback.is_transfer_permitted is False


def test_integrated_tanker_safety_facade():
    engine = TankerSafetyIntegratedEngine()

    telem = TankerSafetyIntegratedTelemetry(
        cow=CowTelemetry(9.5, 5.0, 150.0, 100.0, 2.0),
        foam=DeckFoamTelemetry(0.70, 3.0, 6.8, 55.0, 24.0),
        scrubber=ScrubberTelemetry(250.0, 2.8, 0.8, 6.8, 15.0, 4.5),
        vecs=VecsTelemetry(30.0, 4.0, 25.0, 20.0),
    )

    assessment = engine.evaluate_all(telem)
    assert assessment.overall_safe is True
    assert len(assessment.critical_trips) == 0
    d = assessment.to_dict()
    assert d["cow_status"] == "OPTIMAL"
    assert d["overall_safe"] is True
