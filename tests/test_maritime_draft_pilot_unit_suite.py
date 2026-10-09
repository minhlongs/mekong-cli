"""Zero-mock unit tests for Maritime Phases 381 & 382.

Phase 381: Hydrostatic Draft & Tank Sounding Gauging (IMO MSC.267(85), SOLAS XII)
Phase 382: Port Pilotage Safety & ARPA Collision Avoidance (IMO MSC.192(79))
Strictly kept under 200 lines.
"""

from src.core.maritime.phase_381_draft_tank_sounding_gauging import (
    DraftTankGaugingInput,
    DraftTankSoundingGaugingEngine,
)
from src.core.maritime.phase_382_port_pilotage_arpa_collision import (
    PilotageArpaInput,
    PortPilotageArpaCollisionEngine,
    TargetTrack,
)


def test_draft_sounding_even_keel_optimal() -> None:
    inp = DraftTankGaugingInput(
        vessel_id="IMO9923456",
        draft_fore_m=10.0,
        draft_mid_port_m=10.0,
        draft_mid_starboard_m=10.0,
        draft_aft_m=10.0,
        beam_m=32.0,
        tank_height_m=15.0,
        sounding_level_m=10.5,
        dry_void_ingress_detected=False,
    )
    res = DraftTankSoundingGaugingEngine().evaluate(inp)
    assert res.quarter_mean_draft_m == 10.0
    assert res.trim_m == 0.0
    assert res.heel_angle_deg == 0.0
    assert res.hull_deflection_m == 0.0
    assert res.deflection_type == "SAGGING"
    assert res.tank_ullage_m == 4.5
    assert res.tank_filling_pct == 70.0
    assert res.is_high_level_alarm is False
    assert res.is_overfill_alarm is False
    assert res.is_water_ingress_alarm is False
    assert res.system_status == "OPTIMAL"


def test_draft_sounding_sagging_trim_by_stern() -> None:
    inp = DraftTankGaugingInput(
        vessel_id="IMO9923456",
        draft_fore_m=9.5,
        draft_mid_port_m=10.5,
        draft_mid_starboard_m=10.5,
        draft_aft_m=11.1,
        beam_m=32.0,
        tank_height_m=12.0,
        sounding_level_m=11.5,  # 11.5 / 12.0 = 95.83% -> High level alarm
    )
    res = DraftTankSoundingGaugingEngine().evaluate(inp)
    # d_mid = 10.5, baseline_mid = (9.5 + 11.1) / 2 = 10.3 -> deflection = 0.2m (SAGGING)
    assert res.deflection_type == "SAGGING"
    assert res.hull_deflection_m == 0.2
    assert res.trim_m == 1.6  # by stern
    assert res.is_high_level_alarm is True
    assert res.is_overfill_alarm is False
    assert res.system_status == "WARNING"


def test_draft_sounding_overfill_and_water_ingress() -> None:
    inp = DraftTankGaugingInput(
        vessel_id="IMO9923456",
        draft_fore_m=11.2,
        draft_mid_port_m=10.0,
        draft_mid_starboard_m=10.0,
        draft_aft_m=9.2,  # Hogging: baseline = 10.2, d_mid = 10.0 -> -0.2m
        beam_m=32.0,
        tank_height_m=10.0,
        sounding_level_m=9.9,  # 99% Overfill
        dry_void_ingress_detected=True,  # Critical alarm
    )
    res = DraftTankSoundingGaugingEngine().evaluate(inp)
    assert res.deflection_type == "HOGGING"
    assert res.hull_deflection_m == -0.2
    assert res.is_overfill_alarm is True
    assert res.is_water_ingress_alarm is True
    assert res.system_status == "CRITICAL_ALARM"
    assert any("WATER INGRESS ALARM" in w for w in res.warnings)


def test_pilotage_arpa_safe_clearance() -> None:
    # Own ship heading East (90 deg) at 12 kn. Target 10 NM away heading parallel East at 12 kn.
    # Relative speed = 0, distance remains constant 10 NM -> no collision.
    targets = [
        TargetTrack(
            target_id="TGT_SAFE",
            relative_x_nm=0.0,
            relative_y_nm=10.0,
            target_speed_knots=12.0,
            target_course_deg=90.0,
        )
    ]
    inp = PilotageArpaInput(
        vessel_id="IMO9923456",
        own_speed_knots=12.0,
        own_course_deg=90.0,
        targets=targets,
        pilot_boarding_active=False,
        dwt_tonnes=40000.0,
        available_tug_bollard_pull_tonnes=60.0,
    )
    res = PortPilotageArpaCollisionEngine().evaluate(inp)
    assert res.system_status == "OPTIMAL"
    assert len(res.assessed_targets) == 1
    assert res.assessed_targets[0].is_collision_risk is False
    assert res.is_pilot_speed_compliant is True
    assert res.is_tug_escort_adequate is True


def test_pilotage_arpa_head_on_collision_alarm() -> None:
    # Own ship heading North (0 deg) at 10 kn from (0,0).
    # Target ship located 4 NM North (0, 4) heading South (180 deg) at 10 kn.
    # Relative closing speed = 20 kn. CPA = 0.0 NM, TCPA = 4 / 20 * 60 = 12.0 min.
    targets = [
        TargetTrack(
            target_id="TGT_HEADON",
            relative_x_nm=0.0,
            relative_y_nm=4.0,
            target_speed_knots=10.0,
            target_course_deg=180.0,
        )
    ]
    inp = PilotageArpaInput(
        vessel_id="IMO9923456",
        own_speed_knots=10.0,
        own_course_deg=0.0,
        targets=targets,
    )
    res = PortPilotageArpaCollisionEngine().evaluate(inp)
    assert res.critical_cpa_target_id == "TGT_HEADON"
    assert res.min_cpa_nm == 0.0
    assert res.assessed_targets[0].tcpa_minutes == 12.0
    assert res.assessed_targets[0].is_collision_risk is True
    assert res.system_status == "CRITICAL_COLLISION_ALARM"
    assert any("COLLISION RISK" in w for w in res.warnings)


def test_pilotage_boarding_speed_exceeded() -> None:
    inp = PilotageArpaInput(
        vessel_id="IMO9923456",
        pilot_boarding_active=True,
        ground_speed_knots=9.5,  # Exceeds 8.0 kn safe limit
        dwt_tonnes=50000.0,
        available_tug_bollard_pull_tonnes=65.0,
    )
    res = PortPilotageArpaCollisionEngine().evaluate(inp)
    assert res.is_pilot_speed_compliant is False
    assert res.system_status == "WARNING"
    assert any("Pilot boarding speed" in w for w in res.warnings)


def test_pilotage_tug_bollard_pull_insufficient() -> None:
    # DWT = 80000 tonnes -> Required BP = 80000 * 0.0012 = 96.0 TBP. Available = 70.0 TBP.
    inp = PilotageArpaInput(
        vessel_id="IMO9923456",
        dwt_tonnes=80000.0,
        available_tug_bollard_pull_tonnes=70.0,
    )
    res = PortPilotageArpaCollisionEngine().evaluate(inp)
    assert res.is_tug_escort_adequate is False
    assert res.system_status == "WARNING"
    assert any("Escort tug bollard pull" in w for w in res.warnings)
