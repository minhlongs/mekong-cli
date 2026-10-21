"""Tests for Maritime Automation Phases 475-478 Suite.

Covers:
- Phase 475: Stern Tube L.O. Forward/Aft Seal Temperature & Air Barrier DP Interlock
- Phase 476: Deck Nitrogen Generator Membrane Separation & O2 Interlock
- Phase 477: Main Engine Scavenge Air Manifold Relief & Fire Snuffing
- Phase 478: BWMS UV Reactor Transmittance & Dose Interlock
- Master MaritimeSafetyAuxiliaryBatch4Engine Coordinator

Zero mocks, strictly deterministic rules.
"""

from src.core.maritime.phase_475_stern_tube_seal_interlock import (
    SternTubeSealInterlockEngine,
    SternTubeSealStatus,
    SternTubeSealTelemetry,
)
from src.core.maritime.phase_476_nitrogen_generator_interlock import (
    NitrogenGeneratorSafetyEngine,
    NitrogenGeneratorStatus,
    NitrogenGeneratorTelemetry,
)
from src.core.maritime.phase_477_scavenge_air_relief_fire_snuffing import (
    ScavengeFireSafetyEngine,
    ScavengeFireStatus,
    ScavengeFireTelemetry,
)
from src.core.maritime.phase_478_bwms_uv_dose_transmittance import (
    BwmsUvSafetyEngine,
    BwmsUvStatus,
    BwmsUvTelemetry,
)
from src.core.maritime_safety_auxiliary_batch4_engine import (
    MaritimePhases475to478Telemetry,
    MaritimeSafetyAuxiliaryBatch4Engine,
)


def test_phase_475_stern_tube_seal():
    # Nominal
    t_nom = SternTubeSealTelemetry(52.0, 0.28, 0.8, 85.0, 5.5, True)
    res_nom = SternTubeSealInterlockEngine.evaluate(t_nom)
    assert res_nom.status == SternTubeSealStatus.NORMAL
    assert not res_nom.propulsion_slowdown_tripped
    assert not res_nom.bearing_cooling_booster_active

    # Bearing Overheat Trip
    t_trip = SternTubeSealTelemetry(78.0, 0.28, 0.8, 85.0, 2.0, True)
    res_trip = SternTubeSealInterlockEngine.evaluate(t_trip)
    assert res_trip.status == SternTubeSealStatus.BEARING_OVERHEAT_SLOWDOWN_TRIP
    assert res_trip.propulsion_slowdown_tripped
    assert res_trip.bearing_cooling_booster_active

    # Air Barrier DP Low
    t_dp = SternTubeSealTelemetry(55.0, 0.15, 0.8, 85.0, 5.5, True)
    res_dp = SternTubeSealInterlockEngine.evaluate(t_dp)
    assert res_dp.status == SternTubeSealStatus.LOW_AIR_BARRIER_DP_ALARM
    assert not res_dp.propulsion_slowdown_tripped


def test_phase_476_nitrogen_generator():
    # Nominal
    t_nom = NitrogenGeneratorTelemetry(8.2, 46.0, 0.8, 0.12, True, True)
    res_nom = NitrogenGeneratorSafetyEngine.evaluate(t_nom)
    assert res_nom.status == NitrogenGeneratorStatus.NORMAL
    assert res_nom.deck_isolation_valve_open
    assert not res_nom.atmospheric_vent_valve_open

    # High O2 Trip
    t_o2 = NitrogenGeneratorTelemetry(8.2, 46.0, 5.8, 0.12, True, True)
    res_o2 = NitrogenGeneratorSafetyEngine.evaluate(t_o2)
    assert res_o2.status == NitrogenGeneratorStatus.HIGH_O2_VENTING_TRIP
    assert not res_o2.deck_isolation_valve_open
    assert res_o2.atmospheric_vent_valve_open

    # Low Pressure Trip
    t_p = NitrogenGeneratorTelemetry(6.2, 46.0, 0.8, 0.12, True, True)
    res_p = NitrogenGeneratorSafetyEngine.evaluate(t_p)
    assert res_p.status == NitrogenGeneratorStatus.LOW_FEED_AIR_PRESSURE_TRIP
    assert not res_p.deck_isolation_valve_open


def test_phase_477_scavenge_air_relief_fire():
    # Nominal
    t_nom = ScavengeFireTelemetry(48.0, 0.85, 12.0, True, 75.0)
    res_nom = ScavengeFireSafetyEngine.evaluate(t_nom)
    assert res_nom.status == ScavengeFireStatus.NORMAL
    assert not res_nom.fuel_rack_cutoff_command
    assert not res_nom.snuffing_medium_permissive

    # Fire Trip
    t_fire = ScavengeFireTelemetry(125.0, 0.90, 40.0, True, 75.0)
    res_fire = ScavengeFireSafetyEngine.evaluate(t_fire)
    assert res_fire.status == ScavengeFireStatus.SCAVENGE_FIRE_ALARM_SNUFFING_TRIP
    assert res_fire.fuel_rack_cutoff_command
    assert res_fire.aux_blower_trip_command
    assert res_fire.snuffing_medium_permissive

    # Explosion Relief Open
    t_exp = ScavengeFireTelemetry(65.0, 1.65, 15.0, True, 75.0)
    res_exp = ScavengeFireSafetyEngine.evaluate(t_exp)
    assert res_exp.status == ScavengeFireStatus.MANIFOLD_EXPLOSION_RELIEF_OPEN
    assert res_exp.explosion_relief_open


def test_phase_478_bwms_uv():
    # Nominal
    t_nom = BwmsUvTelemetry(68.0, 340.0, 28.0, 250.0, 95.0, True)
    res_nom = BwmsUvSafetyEngine.evaluate(t_nom)
    assert res_nom.status == BwmsUvStatus.NORMAL
    assert res_nom.ballast_discharge_permissive
    assert not res_nom.flow_throttle_required

    # Insufficient Transmittance Trip
    t_trip = BwmsUvTelemetry(38.0, 280.0, 28.0, 250.0, 95.0, True)
    res_trip = BwmsUvSafetyEngine.evaluate(t_trip)
    assert res_trip.status == BwmsUvStatus.INSUFFICIENT_DOSE_BALLAST_TRIP
    assert not res_trip.ballast_discharge_permissive
    assert res_trip.flow_throttle_required

    # Low Dose Throttle
    t_low = BwmsUvTelemetry(55.0, 260.0, 28.0, 250.0, 95.0, True)
    res_low = BwmsUvSafetyEngine.evaluate(t_low)
    assert res_low.status == BwmsUvStatus.LOW_UV_DOSE_FLOW_THROTTLE
    assert res_low.flow_throttle_required


def test_maritime_safety_auxiliary_batch4_engine_coordinator():
    t_all = MaritimePhases475to478Telemetry(
        stern_tube_seal=SternTubeSealTelemetry(52.0, 0.28, 0.8, 85.0, 5.5, True),
        nitrogen_generator=NitrogenGeneratorTelemetry(8.2, 46.0, 0.8, 0.12, True, True),
        scavenge_fire=ScavengeFireTelemetry(48.0, 0.85, 12.0, True, 75.0),
        bwms_uv=BwmsUvTelemetry(68.0, 340.0, 28.0, 250.0, 95.0, True),
    )
    res = MaritimeSafetyAuxiliaryBatch4Engine.evaluate(t_all)
    assert res.overall_safe
    assert res.active_alarms_count == 0
