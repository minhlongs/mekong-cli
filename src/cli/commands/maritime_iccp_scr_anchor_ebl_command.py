"""CLI Commands for Maritime Phases 347-350.

Covers:
- iccp: NACE SP0176 / DNV-RP-B401 Hull Cathodic Protection & ICCP Rectifier
- scrnox: IMO MARPOL Annex VI Tier III Engine SCR & Methane Slip Engine
- anchorwindlass: IACS UR A1 / OCIMF MEG4 Anchorage Windlass Holding Power
- eblmletr: UNCITRAL MLETR / DCSA e-BL Blockchain Title Transfer & Cargo Release
Strictly under 200 lines.
"""

import json
import typer

from src.core.maritime_iccp_scr_anchor_ebl_engine import (
    AnchorageHoldingEngine,
    AnchorageHoldingInput,
    EblMletrEngine,
    EblMletrInput,
    EblTransferEvent,
    EngineScrNoxEngine,
    EngineScrNoxInput,
    IccpCathodicEngine,
    IccpCathodicInput,
)

iccp_app = typer.Typer(help="Hull ICCP & Sacrificial Anode Cathodic Protection Engine")
scrnox_app = typer.Typer(help="Marine Engine SCR & Dual-Fuel ME-GI NOx Tier III Engine")
anchorwindlass_app = typer.Typer(help="Port Anchorage Windlass Holding Power & Scope Engine")
eblmletr_app = typer.Typer(help="Electronic Bill of Lading (e-BL) MLETR Transfer Engine")


@iccp_app.command("evaluate")
def evaluate_iccp(
    vessel: str = typer.Option("VN-VESSEL-01", "--vessel", help="Vessel Identifier"),
    lbp: float = typer.Option(180.0, "--lbp", help="Length between perpendiculars (m)"),
    beam: float = typer.Option(30.0, "--beam", help="Beam/Breadth (m)"),
    draft: float = typer.Option(10.0, "--draft", help="Vessel draft (m)"),
    cb: float = typer.Option(0.80, "--cb", help="Block coefficient Cb"),
    potential: float = typer.Option(-850.0, "--potential", help="Reference potential vs Ag/AgCl (mV)"),
    current_density: float = typer.Option(30.0, "--current-density", help="Design current density (mA/m2)"),
    anode_material: str = typer.Option("ZINC", "--anode", help="Anode material (ZINC or ALUMINUM)"),
):
    inp = IccpCathodicInput(
        vessel_id=vessel,
        length_bp_m=lbp,
        breadth_m=beam,
        draft_m=draft,
        block_coefficient_cb=cb,
        reference_potential_mv=potential,
        design_current_density_ma_m2=current_density,
        anode_material=anode_material,
    )
    res = IccpCathodicEngine.evaluate(inp)
    print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))


@scrnox_app.command("evaluate")
def evaluate_scr_nox(
    engine: str = typer.Option("MAN-ME-6S50ME", "--engine", help="Engine Identifier"),
    rpm: float = typer.Option(120.0, "--rpm", help="Rated engine speed (RPM)"),
    power: float = typer.Option(8500.0, "--power", help="Engine MCR power (kW)"),
    raw_nox: float = typer.Option(12.5, "--raw-nox", help="Raw NOx emissions (g/kWh)"),
    temp: float = typer.Option(320.0, "--temp", help="Exhaust temperature (°C)"),
    neca: bool = typer.Option(True, "--neca/--no-neca", help="Is vessel in NOx-ECA zone"),
    gas_mode: bool = typer.Option(False, "--gas-mode", help="Is running in dual-fuel gas mode"),
    methane_slip: float = typer.Option(1.2, "--methane-slip", help="Methane slip rate (g/kWh)"),
):
    inp = EngineScrNoxInput(
        engine_id=engine,
        rated_speed_rpm=rpm,
        engine_power_kw=power,
        raw_nox_g_kwh=raw_nox,
        exhaust_temp_celsius=temp,
        is_neca_zone=neca,
        is_dual_fuel_gas_mode=gas_mode,
        methane_slip_g_kwh=methane_slip,
    )
    res = EngineScrNoxEngine.evaluate(inp)
    print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))


@anchorwindlass_app.command("evaluate")
def evaluate_anchorage(
    vessel: str = typer.Option("MV-SAIGON", "--vessel", help="Vessel Identifier"),
    disp: float = typer.Option(45000.0, "--displacement", help="Displacement (tonnes)"),
    beam: float = typer.Option(32.2, "--beam", help="Vessel beam (m)"),
    height_a: float = typer.Option(14.5, "--height-a", help="Freeboard + deckhouse height (m)"),
    wind_area: float = typer.Option(1250.0, "--wind-area", help="Lateral windage area (m2)"),
    depth: float = typer.Option(20.0, "--depth", help="Water depth (m)"),
    shackles: float = typer.Option(6.0, "--shackles", help="Anchor shackles paid out"),
    wind_knots: float = typer.Option(30.0, "--wind-knots", help="Wind speed (knots)"),
    current_knots: float = typer.Option(2.0, "--current-knots", help="Current speed (knots)"),
):
    inp = AnchorageHoldingInput(
        vessel_id=vessel,
        displacement_tonnes=disp,
        breadth_m=beam,
        freeboard_superstructure_height_m=height_a,
        lateral_windage_area_m2=wind_area,
        water_depth_m=depth,
        shackles_paid_out=shackles,
        wind_speed_knots=wind_knots,
        current_speed_knots=current_knots,
    )
    res = AnchorageHoldingEngine.evaluate(inp)
    print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))


@eblmletr_app.command("verify")
def verify_ebl(
    bl: str = typer.Option("EBL-2026-MEKONG-01", "--bl", help="Electronic BL Number"),
    carrier: str = typer.Option("MEKONG SHIPPING LINE", "--carrier", help="Carrier Name"),
    shipper: str = typer.Option("VIET TRADING CORP", "--shipper", help="Shipper Name"),
    consignee: str = typer.Option("TO ORDER", "--consignee", help="Consignee / Order"),
    current_holder: str = typer.Option("MARITIME BANK", "--current-holder", help="Current Holder"),
    release_party: str = typer.Option("GLOBAL LOGISTICS", "--release-party", help="Requesting release party"),
):
    events = [
        EblTransferEvent(
            event_type="ISSUE",
            from_party=shipper,
            to_party="MARITIME BANK",
            timestamp_iso="2026-10-09T08:00:00Z",
            notes="e-BL issued and pledged to bank",
        ),
        EblTransferEvent(
            event_type="SURRENDER",
            from_party="MARITIME BANK",
            to_party=carrier,
            timestamp_iso="2026-10-09T10:00:00Z",
            notes="Surrendered for cargo delivery",
        ),
    ]
    inp = EblMletrInput(
        bl_number=bl,
        carrier_name=carrier,
        shipper_name=shipper,
        consignee_name=consignee,
        notify_party="GLOBAL LOGISTICS",
        cargo_description="Containerized Agricultural Goods",
        container_count=10,
        gross_weight_kg=240000.0,
        current_holder=current_holder,
        events=events,
        requested_release_party=release_party,
    )
    res = EblMletrEngine.evaluate(inp)
    print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))
