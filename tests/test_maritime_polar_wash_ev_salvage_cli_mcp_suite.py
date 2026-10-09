"""Zero-mock CLI and FastMCP Test Suite for Maritime Phases 339-342.

Covers:
- Typer CLI commands for polar, holdwash, evfire, and salvage
- 8 Vietnamese Aliases: bangtuyet, polarisrio, ruahamhang, marpolhme, chayxedien, pctcro, cuuhohanghai, scopiclof
- FastMCP async tool handlers
Strictly adheres to KISS/YAGNI/DRY and kept under 200 lines.
"""

import json
import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app

runner = CliRunner()
app = build_app()


def test_cli_polar_and_vietnamese_aliases():
    """CLI execution for polar evaluate, bangtuyet, and polarisrio."""
    for cmd in ["polar", "bangtuyet", "polarisrio"]:
        result = runner.invoke(
            app,
            [
                cmd, "evaluate",
                "--vessel", "MV ARCTIC VOYAGER",
                "--polar-class", "PC5",
                "--ice-type", "MEDIUM_FIRST_YEAR",
                "--ice-tenths", "7",
                "--mdlt", "-25.0",
                "--speed", "6.0",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["vessel_name"] == "MV ARCTIC VOYAGER"
        assert data["rio_score"] == 0.0
        assert data["operational_status"] == "NORMAL_OPERATION"


def test_cli_holdwash_and_vietnamese_aliases():
    """CLI execution for holdwash check, ruahamhang, and marpolhme."""
    for cmd in ["holdwash", "ruahamhang", "marpolhme"]:
        result = runner.invoke(
            app,
            [
                cmd, "check",
                "--hold-id", "HOLD-01",
                "--cargo", "Thermal Coal",
                "--dist-nm", "15.0",
                "--wash-vol", "80.0",
                "--ph", "7.2",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["hold_id"] == "HOLD-01"
        assert data["discharge_permitted"] is True


def test_cli_evfire_and_vietnamese_aliases():
    """CLI execution for evfire monitor, chayxedien, and pctcro."""
    for cmd in ["evfire", "chayxedien", "pctcro"]:
        result = runner.invoke(
            app,
            [
                cmd, "monitor",
                "--zone-id", "ZONE-DK04",
                "--deck-no", "4",
                "--ev-count", "120",
                "--area", "850.0",
                "--soc", "45.0",
                "--co", "15.0",
                "--h2", "50.0",
                "--temp-rate", "0.2",
                "--deluge-lpm", "9500.0",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["zone_id"] == "ZONE-DK04"
        assert data["alarm_level"] == "NORMAL"
        assert data["deluge_capacity_adequate"] is True


def test_cli_salvage_and_vietnamese_aliases():
    """CLI execution for salvageclaim settle, cuuhohanghai, and scopiclof."""
    for cmd in ["salvageclaim", "cuuhohanghai", "scopiclof"]:
        result = runner.invoke(
            app,
            [
                cmd, "settle",
                "--incident", "SALV-2026-01",
                "--vessel", "MV PACIFIC CARRIER",
                "--salved-value", "50000000.0",
                "--tariff-cost", "2500000.0",
                "--severity", "HIGH",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["incident_id"] == "SALV-2026-01"
        assert data["article_13_gross_award_usd"] == 6630000.0
        assert data["net_salvor_payable_usd"] == 5753750.0


@pytest.mark.asyncio
async def test_fastmcp_handlers_phases_339_342():
    """Verify FastMCP tool endpoints execute with zero-mock data."""
    from scripts.mcp_server import (
        mekong_hold_washwater_check,
        mekong_pctc_ev_fire_monitor,
        mekong_polar_navigation_evaluate,
        mekong_salvage_lof_scopic_settle,
    )

    # 1. Polar Code FastMCP
    polar_res = await mekong_polar_navigation_evaluate(
        vessel_name="MV POLAR MCP",
        polar_class="PC5",
        ice_type="MEDIUM_FIRST_YEAR",
        ice_tenths=7,
    )
    assert polar_res["vessel_name"] == "MV POLAR MCP"
    assert polar_res["operational_status"] == "NORMAL_OPERATION"
    assert polar_res["rio_score"] == 0.0

    # 2. Hold Washwater FastMCP
    wash_res = await mekong_hold_washwater_check(
        hold_id="HOLD-MCP-01",
        cargo_name="Coking Coal",
        distance_from_nearest_land_nm=20.0,
        effluent_ph=7.0,
    )
    assert wash_res["hold_id"] == "HOLD-MCP-01"
    assert wash_res["discharge_permitted"] is True

    # 3. PCTC EV Fire FastMCP
    ev_res = await mekong_pctc_ev_fire_monitor(
        zone_id="ZONE-DK02",
        ev_count=80,
        battery_avg_soc_pct=40.0,
    )
    assert ev_res["zone_id"] == "ZONE-DK02"
    assert ev_res["alarm_level"] == "NORMAL"

    # 4. Salvage LOF/SCOPIC FastMCP
    salvage_res = await mekong_salvage_lof_scopic_settle(
        incident_id="SALV-MCP-01",
        vessel_name="MV SALVAGE ONE",
        salved_value_usd=40000000.0,
        scopic_tariff_costs_usd=2000000.0,
    )
    assert salvage_res["incident_id"] == "SALV-MCP-01"
    assert salvage_res["paying_party"] == "PROPERTY_UNDERWRITERS"
