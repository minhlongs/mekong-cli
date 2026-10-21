"""Unit and integration test suite for Maritime Phases 399-402.

Covers:
- Phase 399: Marine Bow Thruster Dynamic Thrust & Pitch Control
- Phase 400: Inflatable Liferaft & HRU Float-Free Dynamics
- Phase 401: Shipboard Waste High-Temp Incinerator & Gasification
- Phase 402: Marine Closed Vapor Emission Control System (VECS / VRU)
- Master Facade: MaritimeThrusterLiferaftIncineratorVECSEngine

Strictly zero mocks, 100% deterministic physics & safety interlocks.
"""

import pytest

from src.core.maritime.phase_399_bow_thruster_thrust_pitch import (
    BowThrusterEngine,
    BowThrusterInput,
    CavitationStatus,
    HydraulicInterlockStatus,
)
from src.core.maritime.phase_400_inflatable_liferaft_hru_release import (
    LiferaftHRUEngine,
    LiferaftHRUInput,
    HRUActuationState,
    FloatFreeState,
)
from src.core.maritime.phase_401_waste_incinerator_gasification import (
    IncineratorEngine,
    IncineratorInput,
    IncineratorStatus,
)
from src.core.maritime.phase_402_vapor_emission_control_vecs import (
    VECSEngine,
    VECSInput,
    VECSPressureStatus,
    OverfillAlarmLevel,
)
from src.core.maritime_thruster_liferaft_incinerator_vecs_engine import (
    MaritimeThrusterLiferaftIncineratorVECSEngine,
)


def test_phase_399_bow_thruster_nominal_thrust():
    """Verify bow thruster positive thrust generation under nominal conditions."""
    engine = BowThrusterEngine()
    inp = BowThrusterInput(
        pitch_ratio=0.85,
        tunnel_rpm=300.0,
        tunnel_diameter_m=2.0,
        vessel_speed_knots=2.0,
        submersion_depth_m=3.0,
        hydraulic_oil_temp_c=55.0,
        lube_oil_pressure_bar=4.0,
        motor_rated_kw=2500.0,
    )
    res = engine.evaluate(inp)

    assert res.net_thrust_kn > 15.0
    assert res.tip_speed_m_s == pytest.approx(31.42, rel=1e-2)
    assert res.cavitation_status == CavitationStatus.INCIPIENT_CAVITATION
    assert res.interlock_status == HydraulicInterlockStatus.NOMINAL_PERMITTED
    assert res.operational_permitted is True
    assert res.power_limit_active is False

    # Check power limit trigger on smaller motor rating (e.g. 1200 kW)
    res_mcr_limit = engine.evaluate(BowThrusterInput(motor_rated_kw=1200.0))
    assert res_mcr_limit.power_limit_active is True
    assert res_mcr_limit.motor_load_pct > 100.0

    # Low RPM (e.g. 180 RPM) should have higher sigma and NO_CAVITATION
    res_low_rpm = engine.evaluate(BowThrusterInput(tunnel_rpm=180.0, submersion_depth_m=3.5))
    assert res_low_rpm.cavitation_status == CavitationStatus.NO_CAVITATION


def test_phase_399_bow_thruster_hydraulic_trips():
    """Verify safety trips on overheating hydraulic oil and low lube oil pressure."""
    engine = BowThrusterEngine()

    # Overheating trip >= 85 C
    res_trip = engine.evaluate(BowThrusterInput(hydraulic_oil_temp_c=86.5))
    assert res_trip.operational_permitted is False
    assert res_trip.interlock_status == HydraulicInterlockStatus.EMERGENCY_SHUTDOWN_TRIP

    # Low lube oil pressure trip < 2.5 bar
    res_lube = engine.evaluate(BowThrusterInput(lube_oil_pressure_bar=2.1))
    assert res_lube.operational_permitted is False
    assert res_lube.interlock_status == HydraulicInterlockStatus.LUBE_PRESSURE_LOW_TRIP


def test_phase_400_liferaft_hru_hydrostatic_release_and_weak_link():
    """Verify float-free sequence: depth actuation followed by weak link break."""
    engine = LiferaftHRUEngine()

    # Submerged at 2.5m (within 1.5 - 4.0m) with painter pulling and weak link parted
    inp = LiferaftHRUInput(
        submersion_depth_m=2.5,
        painter_line_tension_kn=2.4,
        weak_link_rating_kn=2.2,
        stowage_height_m=12.0,
        painter_line_length_m=25.0,
        hru_service_age_months=12,
        liferaft_service_age_months=6,
    )
    res = engine.evaluate(inp)

    assert res.hru_actuated is True
    assert res.hru_actuation_state == HRUActuationState.HYDROSTATIC_ACTUATED
    assert res.float_free_state == FloatFreeState.WEAK_LINK_PARTED_FLOAT_FREE
    assert res.weak_link_parted is True
    assert res.painter_length_compliant is True
    assert res.service_valid is True


def test_phase_400_liferaft_hru_service_expired():
    """Verify deployment blocked when HRU exceeds 24 months service life."""
    engine = LiferaftHRUEngine()
    inp = LiferaftHRUInput(
        submersion_depth_m=0.0,
        hru_service_age_months=26,
    )
    res = engine.evaluate(inp)

    assert res.service_valid is False
    assert res.float_free_state == FloatFreeState.DEPLOYMENT_BLOCKED


def test_phase_401_incinerator_nominal_and_dioxin_destruction():
    """Verify compliant incineration temperatures and MEPC.244(66) emissions."""
    engine = IncineratorEngine()
    inp = IncineratorInput(
        primary_chamber_temp_c=880.0,
        secondary_chamber_temp_c=1120.0,
        residence_time_s=1.2,
        flue_gas_co_mg_mj=95.0,
        oxygen_content_pct=8.0,
        smoke_density_ringelmann=0.5,
        draft_pressure_pa=-140.0,
        flame_detected=True,
    )
    res = engine.evaluate(inp)

    assert res.status == IncineratorStatus.NOMINAL_BURNING
    assert res.waste_charging_permitted is True
    assert res.dioxin_destruction_verified is True
    assert res.flue_emissions_compliant is True
    assert res.safety_trip_active is False
    assert res.combustion_efficiency_pct > 95.0


def test_phase_401_incinerator_flame_failure_trip():
    """Verify emergency fuel cut-off when flame is lost."""
    engine = IncineratorEngine()
    inp = IncineratorInput(flame_detected=False)
    res = engine.evaluate(inp)

    assert res.safety_trip_active is True
    assert res.status == IncineratorStatus.SAFETY_TRIPPED
    assert res.waste_charging_permitted is False


def test_phase_402_vecs_nominal_and_overfill_trip():
    """Verify VECS pressure envelope, inerting, and 98% High-High overfill trip."""
    engine = VECSEngine()

    # Nominal loading
    res_nom = engine.evaluate(VECSInput(manifold_pressure_bar=0.03, cargo_level_pct=80.0, vapor_oxygen_pct=4.0))
    assert res_nom.pressure_status == VECSPressureStatus.NOMINAL_SAFE
    assert res_nom.oxygen_safe is True
    assert res_nom.cargo_loading_permitted is True
    assert res_nom.max_allowable_loading_rate_m3_h == 2500.0

    # Overfill 98% High-High shutdown
    res_over = engine.evaluate(VECSInput(cargo_level_pct=98.5))
    assert res_over.overfill_level == OverfillAlarmLevel.HIGH_HIGH_SHUTDOWN_98PCT
    assert res_over.cargo_loading_permitted is False
    assert res_over.max_allowable_loading_rate_m3_h == 0.0

    # High pressure manifold trip
    res_p_trip = engine.evaluate(VECSInput(manifold_pressure_bar=0.15))
    assert res_p_trip.pressure_status == VECSPressureStatus.HIGH_PRESSURE_TRIP
    assert res_p_trip.cargo_loading_permitted is False


def test_maritime_phases_399_402_facade():
    """Verify Master Facade aggregation across all 4 auxiliary systems."""
    facade = MaritimeThrusterLiferaftIncineratorVECSEngine()
    res = facade.evaluate()

    assert res.overall_system_status in ("ALL_SYSTEMS_NOMINAL", "OPERATIONAL_WARNING_ACTIVE")
    data = res.to_dict()
    assert "bow_thruster" in data
    assert "liferaft_hru" in data
    assert "waste_incinerator" in data
    assert "vecs" in data
    assert data["bow_thruster"]["operational_permitted"] is True
