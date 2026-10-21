"""CLI Commands for Ship Technical, Registration, Dredging & Seaport Masterplan (Phases 195-198)."""

import dataclasses
import enum
import json
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table

from src.core.ship_tech_masterplan_engine import (
    ConditionOfClass, ShipClassificationEngine, RegistryType, MortgagePriority,
    MaritimeMortgage, ShipRegistrationEngine, ChannelType, MaritimeDredgingUKCEngine,
    SeaportCategory, SeaportMasterplanEngine,
)

console = Console()

shipclass_app = typer.Typer(name="shipclass", help="Phase 195: Ship Classification, HSSC Survey Intervals & Vietnam Register (VR).", no_args_is_help=True)
shipreg_app = typer.Typer(name="shipreg", help="Phase 196: Ship Registration, Bareboat Charters & Maritime Mortgages (NĐ 171/2016).", no_args_is_help=True)
dredging_app = typer.Typer(name="dredging", help="Phase 197: Maritime Channel Dredging & Dynamic Under Keel Clearance (UKC) Squat.", no_args_is_help=True)
masterplan_app = typer.Typer(name="masterplan", help="Phase 198: Decision 1579/QĐ-TTg Seaport Masterplan Capacity & Queuing Dynamics.", no_args_is_help=True)


def _json_serial(obj):
    if isinstance(obj, enum.Enum):
        return obj.value
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    return str(obj)


def _dump_json(obj):
    data = dataclasses.asdict(obj) if dataclasses.is_dataclass(obj) else (obj.__dict__ if hasattr(obj, "__dict__") else obj)
    print(json.dumps(data, indent=2, default=_json_serial))


def _print_table(title: str, col1: str, col2: str, rows: list[tuple[str, str]]) -> None:
    table = Table(title=title)
    table.add_column(col1, style="cyan")
    table.add_column(col2, style="white")
    for k, v in rows:
        table.add_row(k, v)
    console.print(table)


@shipclass_app.command("audit")
def audit_class(
    imo: str = typer.Option("9481234", "--imo", help="IMO vessel identification number"),
    vessel: str = typer.Option("MV MEKONG PRIDE", "--vessel", help="Vessel registered name"),
    society: str = typer.Option("VIETNAM_REGISTER", "--society", help="Classification society (VR, DNV, NK, etc.)"),
    issued_date: str = typer.Option("2023-01-15", "--issued", help="Certificate issue date (YYYY-MM-DD)"),
    last_renewal: str = typer.Option("2023-01-15", "--last-renewal", help="Last renewal survey date (YYYY-MM-DD)"),
    last_drydock: str = typer.Option("2024-06-01", "--last-drydock", help="Last bottom drydock date (YYYY-MM-DD)"),
    assessment_date: str = typer.Option("2026-10-01", "--assess-date", help="Assessment evaluation date (YYYY-MM-DD)"),
    coc: Optional[List[str]] = typer.Option(None, "--coc", help="Outstanding CoC format: 'ID:Desc:DueYYYY-MM-DD'"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Audit statutory HSSC survey compliance and condition of class under Circular 17/2023/TT-BGTVT."""
    cocs = [
        ConditionOfClass(coc_id=p[0], description=":".join(p[1:-1]), due_date_iso=p[-1])
        for c in (coc or []) if len(p := c.split(":")) >= 3
    ]
    audit = ShipClassificationEngine.audit_classification(imo, vessel, society, issued_date, last_renewal, last_drydock, assessment_date, cocs)
    if json_out:
        _dump_json(audit)
        return
    sc = "green" if audit.is_in_class else "red"
    _print_table(f"VR Classification & HSSC Audit: {audit.vessel_name} (IMO {audit.imo_number})", "Parameter", "Value", [
        ("Class Society", audit.class_society), ("Class Status", f"[{sc}]{audit.class_status.value}[/{sc}]"),
        ("In Class Valid", f"[{sc}]{audit.is_in_class}[/{sc}]"), ("5-Year Cycle Year", f"Year {audit.current_cycle_year} of 5"),
        ("Drydock Interval", f"{audit.drydock_interval_months:.1f} months (Limit: 36.0m)"),
        ("Active Windows", ", ".join(audit.active_survey_windows) or "None"),
        ("Overdue Surveys", f"[red]{', '.join(audit.overdue_surveys)}[/red]" if audit.overdue_surveys else "[green]None[/green]"),
        ("Outstanding CoCs", f"{len(audit.outstanding_cocs)} items"), ("Days to Window End", str(audit.days_to_next_survey)),
        ("Action Required", audit.action_required),
    ])


@shipreg_app.command("evaluate")
def evaluate_registration(
    reg_no: str = typer.Option("VN-HP-8899", "--reg-no", help="Official ship registry number"),
    vessel: str = typer.Option("MV MEKONG PIONEER", "--vessel", help="Vessel name"),
    reg_type: str = typer.Option("OFFICIAL", "--type", help="Registry type: OFFICIAL, PROVISIONAL, BAREBOAT_IN, BAREBOAT_OUT"),
    docs: Optional[List[str]] = typer.Option(["BILL_OF_SALE", "BUILDER_CERTIFICATE", "CLASS_CERTIFICATE", "TONNAGE_CERTIFICATE", "DELETION_CERTIFICATE"], "--doc", help="Submitted statutory documents"),
    mortgage: Optional[List[str]] = typer.Option(None, "--mortgage", help="Mortgage format: 'MORT_ID:BANK:AMOUNT:DATE:PRIORITY'"),
    arrested: bool = typer.Option(False, "--arrested", help="Whether vessel is under judicial arrest"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Evaluate statutory ship registration and mortgage liens under Decree 171/2016/NĐ-CP."""
    m_list = [
        MaritimeMortgage(p[0], p[1], float(p[2]), p[3], MortgagePriority.FIRST_RANK if p[4] == "FIRST_RANK" else MortgagePriority.SECOND_RANK)
        for m in (mortgage or []) if len(p := m.split(":")) >= 5
    ]
    eval_res = ShipRegistrationEngine.evaluate_registration(reg_no, vessel, RegistryType(reg_type), docs or [], m_list, arrested)
    if json_out:
        _dump_json(eval_res)
        return
    fs = "green" if eval_res.is_valid_vietnamese_flag else "red"
    _print_table(f"Ship Registration & Lien Status: {eval_res.vessel_name} ({eval_res.registration_no})", "Attribute", "Details", [
        ("Registry Type", eval_res.registry_type.value), ("Flag State", f"[{fs}]{eval_res.flag_state}[/{fs}]"),
        ("Dossier Complete", str(eval_res.required_dossier_complete)),
        ("Missing Documents", ", ".join(eval_res.missing_documents) or "None"),
        ("Total Encumbrance", f"{eval_res.total_encumbrance_vnd:,.0f} VND"),
        ("Free From Arrest", "[green]YES[/green]" if eval_res.is_free_from_arrest else "[red]NO (ARRESTED)[/red]"),
        ("Summary", eval_res.status_summary),
    ])


@dredging_app.command("ukc-calc")
def calculate_ukc(
    channel: str = typer.Option("Soai Rap Channel", "--channel", help="Navigation channel name"),
    channel_type: str = typer.Option("CONFINED", "--type", help="CONFINED or OPEN_WATER"),
    designed_depth: float = typer.Option(9.5, "--depth", help="Designed channel dredged depth (meters)"),
    tide: float = typer.Option(2.8, "--tide", help="Height of tide above chart datum (meters)"),
    draft: float = typer.Option(9.8, "--draft", help="Maximum vessel static draft (meters)"),
    speed: float = typer.Option(8.0, "--speed", help="Vessel transit speed through water (knots)"),
    cb: float = typer.Option(0.80, "--cb", help="Vessel block coefficient Cb"),
    wave: float = typer.Option(0.20, "--wave", help="Wave/swell dynamic allowance (meters)"),
    sediment: float = typer.Option(0.15, "--sediment", help="Channel siltation / sediment allowance (meters)"),
    safety_margin: float = typer.Option(0.30, "--margin", help="Statutory minimum UKC safety margin (meters)"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Calculate Dynamic Under Keel Clearance (UKC) and shallow-water squat per PIANC guidelines."""
    res = MaritimeDredgingUKCEngine.calculate_ukc(channel, ChannelType(channel_type), designed_depth, tide, draft, speed, cb, wave, sediment, safety_margin)
    if json_out:
        _dump_json(res)
        return
    ss = "green" if res.is_passage_safe else "red"
    _print_table(f"Dynamic UKC & Squat Hydrodynamic Evaluation: {res.channel_name}", "Hydrodynamic Parameter", "Value", [
        ("Channel Type", res.channel_type.value),
        ("Total Water Depth", f"{res.designed_depth_m + res.tide_height_m:.2f} m (Depth {res.designed_depth_m}m + Tide {res.tide_height_m}m)"),
        ("Static Vessel Draft", f"{res.vessel_draft_m:.2f} m"),
        ("Dynamic Squat (Barrass)", f"[amber]{res.calculated_squat_m:.2f} m[/amber] (Speed {res.speed_knots} kts, Cb {res.block_coefficient})"),
        ("Wave & Silt Allowances", f"{res.wave_swell_allowance_m + res.sediment_allowance_m:.2f} m"),
        ("Gross UKC", f"{res.gross_ukc_m:.2f} m"), ("Net UKC", f"[{ss}]{res.net_ukc_m:.2f} m[/{ss}]"),
        ("Required Safety Margin", f"{res.safety_margin_m:.2f} m"), ("Passage Verdict", f"[{ss}]{res.clearance_verdict}[/{ss}]"),
    ])


@masterplan_app.command("port-capacity")
def evaluate_port_capacity(
    port: str = typer.Option("HCMC Seaport Group (Cat Lai / Hiep Phuoc)", "--port", help="Port facility or group name"),
    category: str = typer.Option("CLASS_I", "--category", help="SPECIAL, CLASS_I, CLASS_II, CLASS_III"),
    berths: int = typer.Option(10, "--berths", help="Total operational container/cargo berths"),
    throughput: float = typer.Option(4500000.0, "--throughput", help="Actual annual throughput in TEU"),
    crane_rate: float = typer.Option(30.0, "--crane-rate", help="Average crane productivity in TEU/hour"),
    util_limit: float = typer.Option(70.0, "--util-limit", help="Masterplan berth utilization threshold percent"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Evaluate seaport capacity, berth utilization and queuing delay under Decision 1579/QĐ-TTg."""
    res = SeaportMasterplanEngine.evaluate_port_capacity(port, SeaportCategory(category), berths, throughput, crane_rate, util_limit)
    if json_out:
        _dump_json(res)
        return
    us = "green" if res.is_within_masterplan_limit else "red"
    _print_table(f"Seaport Masterplan Capacity & Congestion Audit: {res.port_name}", "Metric", "Value", [
        ("Port Category", res.category.value), ("Total Berths", str(res.total_berths)),
        ("Annual Throughput", f"{res.annual_actual_throughput_teu:,.0f} TEU"),
        ("Designed Annual Capacity", f"{res.annual_capacity_teu:,.0f} TEU"),
        ("Berth Occupancy (rho)", f"[{us}]{res.occupancy_rate_pct:.2f}%[/{us}] (Limit: {util_limit:.0f}%)"),
        ("Expected Queue Delay (Wq)", f"{res.expected_queue_delay_hours:.2f} hours"),
        ("Growth Headroom", f"{res.expansion_headroom_pct:.2f}%"), ("Masterplan Recommendation", f"[{us}]{res.recommendation}[/{us}]"),
    ])
