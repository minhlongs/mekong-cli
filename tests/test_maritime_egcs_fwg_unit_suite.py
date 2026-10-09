"""Unit tests for Maritime Phases 399-400 (EGCS Scrubber & Vacuum FWG).

Strictly zero-mock, real physics, strictly < 200 LOC.
"""

from src.core.maritime.phase_399_egcs_sox_wet_scrubber import (
    EgcsMode,
    EgcsScrubberInput,
    EgcsSoxScrubberEngine,
)
from src.core.maritime.phase_400_vacuum_fresh_water_generator import (
    VacuumFreshWaterGeneratorEngine,
    VacuumFwgInput,
)


def test_egcs_scrubber_open_loop_nominal():
    engine = EgcsSoxScrubberEngine()
    inp = EgcsScrubberInput(
        so2_ppm=10.0,
        co2_pct=5.0,
        washwater_ph=6.8,
        inlet_pah_ug_l=5.0,
        discharge_pah_ug_l=15.0,
        turbidity_fnu=8.0,
        operating_mode=EgcsMode.OPEN_LOOP,
        in_eca_or_restricted_port=False,
    )
    res = engine.evaluate(inp)
    assert res.emission_ratio == 2.0
    assert res.mepc_340_77_compliant is True
    assert res.discharge_lockout is False
    assert res.sox_washwater_status == "MEPC_340_77_WASHWATER_COMPLIANT"


def test_egcs_scrubber_eca_exceedance_and_ph_lockout():
    engine = EgcsSoxScrubberEngine()
    inp = EgcsScrubberInput(
        so2_ppm=25.0,
        co2_pct=5.0,
        washwater_ph=5.8,
        inlet_pah_ug_l=5.0,
        discharge_pah_ug_l=65.0,
        turbidity_fnu=30.0,
        operating_mode=EgcsMode.OPEN_LOOP,
        in_eca_or_restricted_port=True,
    )
    res = engine.evaluate(inp)
    assert res.emission_ratio == 5.0
    assert res.mepc_340_77_compliant is False  # Limit is 4.3 in ECA
    assert res.discharge_lockout is True
    assert any("NON-COMPLIANCE" in w for w in res.warnings)


def test_egcs_scrubber_closed_loop_retention():
    engine = EgcsSoxScrubberEngine()
    inp = EgcsScrubberInput(
        so2_ppm=8.0,
        co2_pct=4.0,
        washwater_ph=7.5,
        operating_mode=EgcsMode.CLOSED_LOOP,
        in_eca_or_restricted_port=True,
    )
    res = engine.evaluate(inp)
    assert res.emission_ratio == 2.0
    assert res.mepc_340_77_compliant is True
    assert res.sox_washwater_status == "CLOSED_LOOP_RECIRCULATION_ACTIVE"
    assert res.naoh_dosing_active is True


def test_vacuum_fwg_nominal_potable():
    engine = VacuumFreshWaterGeneratorEngine()
    inp = VacuumFwgInput(
        jacket_water_temp_c=82.0,
        evaporator_vacuum_bar=-0.93,
        distillate_salinity_ppm=2.8,
        feed_seawater_flow_m3_h=12.0,
        distillate_flow_m3_h=1.0,
    )
    res = engine.evaluate(inp)
    assert 39.0 <= res.evaporator_boiling_temp_c <= 45.0
    assert res.potable_grade_certified is True
    assert res.three_way_dump_valve == "DIRECT_TO_FRESHWATER_STORAGE"
    assert res.distillate_purity_status == "POTABLE_PURE_DISTILLATE"
    assert res.scale_formation_risk is False


def test_vacuum_fwg_high_salinity_dump_tripped():
    engine = VacuumFreshWaterGeneratorEngine()
    inp = VacuumFwgInput(
        jacket_water_temp_c=78.0,
        evaporator_vacuum_bar=-0.91,
        distillate_salinity_ppm=18.5,
    )
    res = engine.evaluate(inp)
    assert res.potable_grade_certified is False
    assert res.three_way_dump_valve == "DUMP_OVERBOARD_OR_EVAP_RECIRC"
    assert res.distillate_purity_status == "SALINE_CONTAMINATED_DEFECT"
    assert len(res.warnings) >= 1


def test_vacuum_fwg_loss_of_vacuum():
    engine = VacuumFreshWaterGeneratorEngine()
    inp = VacuumFwgInput(
        jacket_water_temp_c=60.0,
        evaporator_vacuum_bar=-0.75,
        distillate_salinity_ppm=3.0,
    )
    res = engine.evaluate(inp)
    assert res.evaporator_boiling_temp_c > 50.0
    assert res.scale_formation_risk is True
    assert any("POOR VACUUM" in w for w in res.warnings)
