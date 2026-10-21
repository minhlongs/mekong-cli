"""Unit & Integration Tests for Maritime Automation Phases 467-470.

Covers:
- Phase 467: Chilled Water Anti-Freeze & Low Suction Protection
- Phase 468: Incinerator Flue Gas High Temperature & Draft Vacuum Protection
- Phase 469: Deepwell Cargo Pump Stripping & Dry-Running Cavitation Protection
- Phase 470: Fuel Oil Settling Tank Temperature & Quick-Closing Valve Safety
- Master Coordinator: MaritimeSafetyAuxiliaryBatch2Engine

Strictly zero mocks, < 140 LOC.
"""

import pytest

from src.core.maritime.phase_467_chilled_water_antifreeze import (
    ChilledWaterAntiFreezeEngine,
    ChilledWaterStatus,
    ChilledWaterTelemetry,
)
from src.core.maritime.phase_468_incinerator_flue_protection import (
    IncineratorProtectionEngine,
    IncineratorStatus,
    IncineratorTelemetry,
)
from src.core.maritime.phase_469_deepwell_pump_stripping import (
    DeepwellPumpProtectionEngine,
    DeepwellPumpStatus,
    DeepwellPumpTelemetry,
)
from src.core.maritime.phase_470_settling_tank_safety import (
    SettlingTankSafetyEngine,
    SettlingTankStatus,
    SettlingTankTelemetry,
)
from src.core.maritime_safety_auxiliary_batch2_engine import (
    MaritimePhases467to470Telemetry,
    MaritimeSafetyAuxiliaryBatch2Engine,
)


def test_phase_467_chilled_water_antifreeze():
    # Normal operation
    normal_telem = ChilledWaterTelemetry(7.0, 12.0, 3.5, 25.0, True)
    res_normal = ChilledWaterAntiFreezeEngine.evaluate(normal_telem)
    assert res_normal.status == ChilledWaterStatus.NORMAL
    assert res_normal.delta_t_c == 5.0
    assert res_normal.compressor_permissive is True
    assert res_normal.hot_gas_bypass_active is False

    # Freeze stat trip (supply <= 3.0 C)
    freeze_telem = ChilledWaterTelemetry(2.8, 8.0, 3.5, 25.0, True)
    res_freeze = ChilledWaterAntiFreezeEngine.evaluate(freeze_telem)
    assert res_freeze.status == ChilledWaterStatus.FREEZE_STAT_TRIP
    assert res_freeze.compressor_permissive is False
    assert res_freeze.hot_gas_bypass_active is True

    # Low flow interlock trip
    flow_trip_telem = ChilledWaterTelemetry(7.0, 12.0, 3.5, 10.0, True)
    res_flow = ChilledWaterAntiFreezeEngine.evaluate(flow_trip_telem)
    assert res_flow.status == ChilledWaterStatus.FLOW_INTERLOCK_TRIP
    assert res_flow.compressor_permissive is False


def test_phase_468_incinerator_flue_protection():
    # Normal operation
    normal_telem = IncineratorTelemetry(920.0, 280.0, -25.0, True, True)
    res_normal = IncineratorProtectionEngine.evaluate(normal_telem)
    assert res_normal.status == IncineratorStatus.NORMAL
    assert res_normal.waste_feed_permissive is True
    assert res_normal.emergency_damper_open is False

    # Flue overheat trip (flue >= 350.0 C)
    overheat_telem = IncineratorTelemetry(980.0, 360.0, -25.0, True, True)
    res_overheat = IncineratorProtectionEngine.evaluate(overheat_telem)
    assert res_overheat.status == IncineratorStatus.FLUE_OVERHEAT_TRIP
    assert res_overheat.emergency_damper_open is True
    assert res_overheat.waste_feed_permissive is False

    # Draft loss trip (draft >= -5 mm WG)
    draft_telem = IncineratorTelemetry(900.0, 280.0, -2.0, True, True)
    res_draft = IncineratorProtectionEngine.evaluate(draft_telem)
    assert res_draft.status == IncineratorStatus.DRAFT_LOSS_TRIP
    assert res_draft.emergency_damper_open is True


def test_phase_469_deepwell_pump_stripping():
    # Normal discharge
    normal_telem = DeepwellPumpTelemetry(6.5, 42.0, 85.0, False, 5.0, True)
    res_normal = DeepwellPumpProtectionEngine.evaluate(normal_telem)
    assert res_normal.status == DeepwellPumpStatus.NORMAL_DISCHARGE
    assert res_normal.auto_stop_permissive is False

    # Stripping active
    strip_telem = DeepwellPumpTelemetry(2.0, 48.0, 45.0, True, 5.0, True)
    res_strip = DeepwellPumpProtectionEngine.evaluate(strip_telem)
    assert res_strip.status == DeepwellPumpStatus.STRIPPING_ACTIVE
    assert res_strip.stripping_n2_valve_open is True

    # Dry run cavitation trip (motor current <= 30% and discharge P <= 1.5 bar)
    dry_telem = DeepwellPumpTelemetry(1.0, 60.0, 25.0, True, 5.0, True)
    res_dry = DeepwellPumpProtectionEngine.evaluate(dry_telem)
    assert res_dry.status == DeepwellPumpStatus.DRY_RUN_CAVITATION_TRIP
    assert res_dry.auto_stop_permissive is True


def test_phase_470_settling_tank_safety():
    # Normal operation
    normal_telem = SettlingTankTelemetry(75.0, 65.0, True, False, False)
    res_normal = SettlingTankSafetyEngine.evaluate(normal_telem)
    assert res_normal.status == SettlingTankStatus.NORMAL
    assert res_normal.steam_shutoff_valve_closed is False
    assert res_normal.quick_closing_valve_tripped is False

    # Emergency QCV trip via remote pull
    qcv_telem = SettlingTankTelemetry(75.0, 65.0, True, False, True)
    res_qcv = SettlingTankSafetyEngine.evaluate(qcv_telem)
    assert res_qcv.status == SettlingTankStatus.EMERGENCY_QCV_TRIPPED
    assert res_qcv.quick_closing_valve_tripped is True
    assert res_qcv.steam_shutoff_valve_closed is True
    assert res_qcv.transfer_pump_permissive is False

    # Overheat steam trip (oil temp >= 85 C)
    overheat_telem = SettlingTankTelemetry(86.5, 70.0, True, False, False)
    res_overheat = SettlingTankSafetyEngine.evaluate(overheat_telem)
    assert res_overheat.status == SettlingTankStatus.OVERHEAT_STEAM_TRIP
    assert res_overheat.steam_shutoff_valve_closed is True


def test_master_maritime_auxiliary_batch2_engine():
    telem = MaritimePhases467to470Telemetry(
        chilled_water=ChilledWaterTelemetry(7.0, 12.0, 3.5, 25.0, True),
        incinerator=IncineratorTelemetry(900.0, 280.0, -20.0, True, True),
        deepwell_pump=DeepwellPumpTelemetry(6.0, 45.0, 80.0, False, 5.0, True),
        settling_tank=SettlingTankTelemetry(75.0, 70.0, True, False, False),
    )
    res = MaritimeSafetyAuxiliaryBatch2Engine.evaluate(telem)
    assert res.overall_safe is True
    assert res.active_alarms_count == 0
