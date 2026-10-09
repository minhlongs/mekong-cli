"""Deterministic zero-mock test suite for Maritime Phases 403-406.

Validates:
- Phase 403 Boiler Water Chemistry & Deaeration
- Phase 404 Stern Tube Lubrication & EAL Water Ingress
- Phase 405 Sludge Incinerator Thermal Destruction
- Phase 406 Sewage Treatment Plant MBR & Nutrient Removal
- Maritime Auxiliary Environmental Unified Facade Engine
- CLI Typer command execution & FastMCP server tools
Strictly < 200 LOC, zero mocks.
"""

import pytest
from typer.testing import CliRunner

from src.core.maritime.phase_403_boiler_water_chemistry import (
    BoilerWaterEngine,
    BoilerWaterInput,
    BoilerWaterStatus,
)
from src.core.maritime.phase_404_stern_tube_eal import (
    SternTubeEngine,
    SternTubeInput,
    SternTubeSealStatus,
)
from src.core.maritime.phase_405_incinerator_sludge import (
    SludgeIncinerationStatus,
    SludgeIncineratorEngine,
    SludgeIncineratorInput,
)
from src.core.maritime.phase_406_sewage_treatment_mbr import (
    SewageDischargeStatus,
    SewageTreatmentEngine,
    SewageTreatmentInput,
)
from src.core.maritime_auxiliary_environmental_engine import (
    MaritimeAuxiliaryEnvironmentalEngine,
)
from src.cli.commands.maritime_boiler_tube_incinerator_stp_command import (
    boiler_app,
    incinerator_app,
    sewage_app,
    sterntube_app,
)
from scripts.mcp_server import (
    mekong_maritime_auxiliary_environmental_evaluate,
    mekong_maritime_boiler_water_evaluate,
    mekong_maritime_sewage_treatment_evaluate,
    mekong_maritime_sludge_incinerator_evaluate,
    mekong_maritime_stern_tube_eal_evaluate,
)

runner = CliRunner()


def test_phase_403_boiler_chemistry_nominal_and_blowdown():
    engine = BoilerWaterEngine()
    nominal = engine.evaluate(BoilerWaterInput())
    assert nominal.status == BoilerWaterStatus.OPTIMAL_PASSIVATED
    assert nominal.oxygen_scavenging_pass is True
    assert nominal.phosphate_buffer_pass is True
    assert nominal.magnetite_passivation_stable is True
    assert nominal.blowdown_recommended is False

    high_tds = engine.evaluate(BoilerWaterInput(tds_ppm=1200.0, conductivity_us_cm=800.0))
    assert high_tds.blowdown_recommended is True
    assert high_tds.status == BoilerWaterStatus.BLOWDOWN_REQUIRED

    o2_leak = engine.evaluate(BoilerWaterInput(dissolved_oxygen_ppm=0.06, hydrazine_residual_ppm=0.005))
    assert o2_leak.status == BoilerWaterStatus.OXYGEN_PITTING_CRITICAL
    assert o2_leak.magnetite_passivation_stable is False


def test_phase_404_stern_tube_eal_differential_and_water():
    engine = SternTubeEngine()
    nominal = engine.evaluate(SternTubeInput())
    assert nominal.status == SternTubeSealStatus.SEAL_INTEGRITY_NORMAL
    assert nominal.seal_barrier_intact is True
    assert nominal.eal_water_compliant is True
    assert nominal.pressure_diff_bar == 0.23

    low_dp = engine.evaluate(SternTubeInput(lube_header_pressure_bar=0.35, seawater_draft_pressure_bar=0.32))
    assert low_dp.status == SternTubeSealStatus.PRESSURE_DIFFERENTIAL_ALARM
    assert low_dp.seal_barrier_intact is False

    crit_water = engine.evaluate(SternTubeInput(water_content_ppm=1650.0))
    assert crit_water.status == SternTubeSealStatus.WATER_INGRESS_CRITICAL
    assert crit_water.eal_water_compliant is False


def test_phase_405_incinerator_sludge_interlocks():
    engine = SludgeIncineratorEngine()
    nominal = engine.evaluate(SludgeIncineratorInput())
    assert nominal.status == SludgeIncinerationStatus.PERMITTED_RUNNING
    assert nominal.sludge_feed_permitted is True
    assert nominal.temperature_compliant is True

    cold_chamber = engine.evaluate(SludgeIncineratorInput(combustion_chamber_temp_c=810.0))
    assert cold_chamber.status == SludgeIncinerationStatus.COMBUSTION_TEMP_LOCKOUT
    assert cold_chamber.sludge_feed_permitted is False

    port_lockout = engine.evaluate(SludgeIncineratorInput(in_port_or_estuary=True))
    assert port_lockout.status == SludgeIncinerationStatus.PORT_LIMIT_FORBIDDEN_ZONE
    assert port_lockout.sludge_feed_permitted is False


def test_phase_406_sewage_mbr_special_area_and_fouling():
    engine = SewageTreatmentEngine()
    nominal = engine.evaluate(SewageTreatmentInput(operating_in_special_area=True))
    assert nominal.status == SewageDischargeStatus.DISCHARGE_COMPLIANT_SPECIAL_AREA
    assert nominal.overboard_discharge_permitted is True
    assert nominal.nutrient_removal_pass is True

    high_n = engine.evaluate(SewageTreatmentInput(total_nitrogen_mg_l=26.0, operating_in_special_area=True))
    assert high_n.status == SewageDischargeStatus.NUTRIENT_NON_COMPLIANT
    assert high_n.overboard_discharge_permitted is False

    fouled = engine.evaluate(SewageTreatmentInput(transmembrane_pressure_bar=0.52))
    assert fouled.status == SewageDischargeStatus.MEMBRANE_FOULING_TRIP
    assert fouled.membrane_fouling_safe is False
    assert fouled.backwash_recommended is True


def test_unified_facade_engine():
    facade = MaritimeAuxiliaryEnvironmentalEngine()
    res = facade.evaluate(
        BoilerWaterInput(),
        SternTubeInput(),
        SludgeIncineratorInput(),
        SewageTreatmentInput(),
    )
    assert res.all_systems_green is True
    assert res.overall_auxiliary_status == "AUXILIARY_ENVIRONMENTAL_NOMINAL_OPTIMAL"

    data = res.to_dict()
    assert data["all_systems_green"] is True
    assert "boiler_water" in data
    assert "stern_tube" in data
    assert "incinerator" in data
    assert "sewage_treatment" in data


def test_typer_cli_commands():
    b_res = runner.invoke(boiler_app, ["--o2-ppm", "0.004", "--ph", "10.1"])
    assert b_res.exit_code == 0
    assert "Maritime Phase 403" in b_res.output

    st_res = runner.invoke(sterntube_app, ["--water-ppm", "400.0"])
    assert st_res.exit_code == 0
    assert "Maritime Phase 404" in st_res.output

    inc_res = runner.invoke(incinerator_app, ["--chamber-temp", "930.0"])
    assert inc_res.exit_code == 0
    assert "Maritime Phase 405" in inc_res.output

    sew_res = runner.invoke(sewage_app, ["--bod5", "10.0"])
    assert sew_res.exit_code == 0
    assert "Maritime Phase 406" in sew_res.output


@pytest.mark.asyncio
async def test_fastmcp_endpoints():
    b_out = await mekong_maritime_boiler_water_evaluate(dissolved_oxygen_ppm=0.004)
    assert b_out["oxygen_scavenging_pass"] is True

    st_out = await mekong_maritime_stern_tube_eal_evaluate(lube_header_pressure_bar=0.55)
    assert st_out["seal_barrier_intact"] is True

    inc_out = await mekong_maritime_sludge_incinerator_evaluate(combustion_chamber_temp_c=910.0)
    assert inc_out["sludge_feed_permitted"] is True

    sew_out = await mekong_maritime_sewage_treatment_evaluate(bod5_mg_l=11.0)
    assert sew_out["overboard_discharge_permitted"] is True

    uni_out = await mekong_maritime_auxiliary_environmental_evaluate()
    assert uni_out["all_systems_green"] is True
