"""Typer CLI Commands for Seaport Vessel Traffic Service (VTS), Cold Ironing Shore Power, Green Port GHG MRV & Marine Bunkering.

Phases 239-242:
- Phase 239: mekong vtsreporting check / speed / cpa / tariff
- Phase 240: mekong coldironing energy / emissions / cost
- Phase 241: mekong greenportghg cii / rating
- Phase 242: mekong marinebunkering bdn / safety / volume
"""

from __future__ import annotations

from rich.console import Console

from src.cli.commands._maritime_bunkering_cmds import (
    bunker_volume_correction_cmd,
    bunkering_safety_cmd,
    marinebunkering_app,
    verify_bdn_cmd,
)
from src.cli.commands._maritime_coldironing_cmds import (
    cold_ironing_cost_cmd,
    cold_ironing_emissions_cmd,
    cold_ironing_energy_cmd,
    coldironing_app,
)
from src.cli.commands._maritime_ghg_cii_cmds import (
    direct_rating_cmd,
    evaluate_cii_cmd,
    greenportghg_app,
)
from src.cli.commands._maritime_vts_cmds import (
    calculate_cpa_cmd,
    calculate_vts_tariff_cmd,
    check_fairway_speed_cmd,
    check_vts_reporting_cmd,
    vtsreporting_app,
)
from src.core.maritime_vts_coldironing_ghg_bunkering_engine import (
    BunkerGrade,
    CiiRatingGrade,
    CiiShipType,
    ColdIroningEngine,
    GreenPortGhgCiiEngine,
    MarineBunkeringSafetyEngine,
    VesselTrafficServiceEngine,
)

console = Console()

__all__ = [
    "BunkerGrade",
    "CiiRatingGrade",
    "CiiShipType",
    "ColdIroningEngine",
    "GreenPortGhgCiiEngine",
    "MarineBunkeringSafetyEngine",
    "VesselTrafficServiceEngine",
    "bunker_volume_correction_cmd",
    "bunkering_safety_cmd",
    "calculate_cpa_cmd",
    "calculate_vts_tariff_cmd",
    "check_fairway_speed_cmd",
    "check_vts_reporting_cmd",
    "cold_ironing_cost_cmd",
    "cold_ironing_emissions_cmd",
    "cold_ironing_energy_cmd",
    "coldironing_app",
    "console",
    "direct_rating_cmd",
    "evaluate_cii_cmd",
    "greenportghg_app",
    "marinebunkering_app",
    "verify_bdn_cmd",
    "vtsreporting_app",
]
