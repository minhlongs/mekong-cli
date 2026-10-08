"""CLI Commands for Ship Technical, Registration, Dredging & Seaport Masterplan (Phases 195-198).

Typer Apps:
- mekong shipclass / dangkiem (Phase 195: Ship Classification & HSSC Survey Windows)
- mekong shipreg / dangky (Phase 196: Ship Registration & Encumbrances)
- mekong dredging / naovet (Phase 197: Channel Dredging & Dynamic UKC Squat)
- mekong masterplan / quyhoach (Phase 198: Seaport Masterplan 1579 & Capacity)
"""

import dataclasses
import enum
import json
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table

from src.core.ship_tech_masterplan_engine import (
    ConditionOfClass,
    ShipClassificationEngine,
    RegistryType,
    MortgagePriority,
    MaritimeMortgage,
    ShipRegistrationEngine,
    ChannelType,
    MaritimeDredgingUKCEngine,
    SeaportCategory,
    SeaportMasterplanEngine,
)

console = Console()

shipclass_app = typer.Typer(
    name="shipclass",
    help="Phase 195: Ship Classification, HSSC Survey Intervals & Vietnam Register (VR).",
    no_args_is_help=True,
)

shipreg_app = typer.Typer(
    name="shipreg",
    help="Phase 196: Ship Registration, Bareboat Charters & Maritime Mortgages (NĐ 171/2016).",
    no_args_is_help=True,
)

dredging_app = typer.Typer(
    name="dredging",
    help="Phase 197: Maritime Channel Dredging & Dynamic Under Keel Clearance (UKC) Squat.",
    no_args_is_help=True,
)

masterplan_app = typer.Typer(
    name="masterplan",
    help="Phase 198: Decision 1579/QĐ-TTg Seaport Masterplan Capacity & Queuing Dynamics.",
    no_args_is_help=True,
)


def _json_serial(obj):
    if isinstance(obj, enum.Enum):
        return obj.value
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    return str(obj)


def _dump_json(obj):
    if dataclasses.is_dataclass(obj):
        data = dataclasses.asdict(obj)
    elif hasattr(obj, "__dict__"):
        data = obj.__dict__
    else:
        data = obj
    print(json.dumps(data, indent=2, default=_json_serial))


# ---------------------------------------------------------------------------
# Phase 195: Ship Classification Commands
# ---------------------------------------------------------------------------

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
    cocs: List[ConditionOfClass] = []
    if coc:
        for c in coc:
            parts = c.split(":")
            if len(parts) >= 3:
                c_id = parts[0]
                due_date = parts[-1]
                desc = ":".join(parts[1:-1])
                cocs.append(ConditionOfClass(coc_id=c_id, description=desc, due_date_iso=due_date))

    audit = ShipClassificationEngine.audit_classification(
        imo_number=imo,
        vessel_name=vessel,
        class_society=society,
        certificate_issued_iso=issued_date,
        last_renewal_survey_iso=last_renewal,
        last_drydock_survey_iso=last_drydock,
        assessment_date_iso=assessment_date,
        cocs=cocs,
    )

    if json_out:
        _dump_json(audit)
        return

    table = Table(title=f"VR Classification & HSSC Audit: {audit.vessel_name} (IMO {audit.imo_number})")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Class Society", audit.class_society)
    status_color = "green" if audit.is_in_class else "red"
    table.add_row("Class Status", f"[{status_color}]{audit.class_status.value}[/{status_color}]")
    table.add_row("In Class Valid", f"[{status_color}]{audit.is_in_class}[/{status_color}]")
    table.add_row("5-Year Cycle Year", f"Year {audit.current_cycle_year} of 5")
    table.add_row("Drydock Interval", f"{audit.drydock_interval_months:.1f} months (Limit: 36.0m)")
    table.add_row("Active Windows", ", ".join(audit.active_survey_windows) or "None")
    table.add_row("Overdue Surveys", f"[red]{', '.join(audit.overdue_surveys)}[/red]" if audit.overdue_surveys else "[green]None[/green]")
    table.add_row("Outstanding CoCs", f"{len(audit.outstanding_cocs)} items")
    table.add_row("Days to Window End", str(audit.days_to_next_survey))
    table.add_row("Action Required", audit.action_required)

    console.print(table)


# ---------------------------------------------------------------------------
# Phase 196: Ship Registration & Mortgage Commands
# ---------------------------------------------------------------------------

@shipreg_app.command("evaluate")
def evaluate_registration(
    reg_no: str = typer.Option("VN-HP-8899", "--reg-no", help="Official ship registry number"),
    vessel: str = typer.Option("MV MEKONG PIONEER", "--vessel", help="Vessel name"),
    reg_type: str = typer.Option("OFFICIAL", "--type", help="Registry type: OFFICIAL, PROVISIONAL, BAREBOAT_IN, BAREBOAT_OUT"),
    docs: Optional[List[str]] = typer.Option(
        ["BILL_OF_SALE", "BUILDER_CERTIFICATE", "CLASS_CERTIFICATE", "TONNAGE_CERTIFICATE", "DELETION_CERTIFICATE"],
        "--doc",
        help="Submitted statutory documents",
    ),
    mortgage: Optional[List[str]] = typer.Option(None, "--mortgage", help="Mortgage format: 'MORT_ID:BANK:AMOUNT:DATE:PRIORITY'"),
    arrested: bool = typer.Option(False, "--arrested", help="Whether vessel is under judicial arrest"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Evaluate statutory ship registration and mortgage liens under Decree 171/2016/NĐ-CP."""
    m_list: List[MaritimeMortgage] = []
    if mortgage:
        for m in mortgage:
            parts = m.split(":")
            if len(parts) >= 5:
                p_enum = MortgagePriority.FIRST_RANK if parts[4] == "FIRST_RANK" else MortgagePriority.SECOND_RANK
                m_list.append(MaritimeMortgage(
                    mortgage_id=parts[0],
                    mortgagee_name=parts[1],
                    secured_amount_vnd=float(parts[2]),
                    registration_date_iso=parts[3],
                    priority=p_enum,
                ))

    rtype = RegistryType(reg_type)
    eval_res = ShipRegistrationEngine.evaluate_registration(
        registration_no=reg_no,
        vessel_name=vessel,
        registry_type=rtype,
        submitted_documents=docs or [],
        mortgages=m_list,
        is_arrested=arrested,
    )

    if json_out:
        _dump_json(eval_res)
        return

    table = Table(title=f"Ship Registration & Lien Status: {eval_res.vessel_name} ({eval_res.registration_no})")
    table.add_column("Attribute", style="cyan")
    table.add_column("Details", style="white")

    flag_style = "green" if eval_res.is_valid_vietnamese_flag else "red"
    table.add_row("Registry Type", eval_res.registry_type.value)
    table.add_row("Flag State", f"[{flag_style}]{eval_res.flag_state}[/{flag_style}]")
    table.add_row("Dossier Complete", str(eval_res.required_dossier_complete))
    table.add_row("Missing Documents", ", ".join(eval_res.missing_documents) or "None")
    table.add_row("Total Encumbrance", f"{eval_res.total_encumbrance_vnd:,.0f} VND")
    table.add_row("Free From Arrest", "[green]YES[/green]" if eval_res.is_free_from_arrest else "[red]NO (ARRESTED)[/red]")
    table.add_row("Summary", eval_res.status_summary)

    console.print(table)


# ---------------------------------------------------------------------------
# Phase 197: Maritime Dredging & UKC Commands
# ---------------------------------------------------------------------------

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
    ctype = ChannelType(channel_type)
    res = MaritimeDredgingUKCEngine.calculate_ukc(
        channel_name=channel,
        channel_type=ctype,
        designed_depth_m=designed_depth,
        tide_height_m=tide,
        vessel_draft_m=draft,
        speed_knots=speed,
        block_coefficient=cb,
        wave_swell_allowance_m=wave,
        sediment_allowance_m=sediment,
        safety_margin_m=safety_margin,
    )

    if json_out:
        _dump_json(res)
        return

    table = Table(title=f"Dynamic UKC & Squat Hydrodynamic Evaluation: {res.channel_name}")
    table.add_column("Hydrodynamic Parameter", style="cyan")
    table.add_column("Value", style="white")

    safe_style = "green" if res.is_passage_safe else "red"
    table.add_row("Channel Type", res.channel_type.value)
    table.add_row("Total Water Depth", f"{res.designed_depth_m + res.tide_height_m:.2f} m (Depth {res.designed_depth_m}m + Tide {res.tide_height_m}m)")
    table.add_row("Static Vessel Draft", f"{res.vessel_draft_m:.2f} m")
    table.add_row("Dynamic Squat (Barrass)", f"[amber]{res.calculated_squat_m:.2f} m[/amber] (Speed {res.speed_knots} kts, Cb {res.block_coefficient})")
    table.add_row("Wave & Silt Allowances", f"{res.wave_swell_allowance_m + res.sediment_allowance_m:.2f} m")
    table.add_row("Gross UKC", f"{res.gross_ukc_m:.2f} m")
    table.add_row("Net UKC", f"[{safe_style}]{res.net_ukc_m:.2f} m[/{safe_style}]")
    table.add_row("Required Safety Margin", f"{res.safety_margin_m:.2f} m")
    table.add_row("Passage Verdict", f"[{safe_style}]{res.clearance_verdict}[/{safe_style}]")

    console.print(table)


# ---------------------------------------------------------------------------
# Phase 198: Seaport Masterplan Commands
# ---------------------------------------------------------------------------

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
    cat = SeaportCategory(category)
    res = SeaportMasterplanEngine.evaluate_port_capacity(
        port_name=port,
        category=cat,
        total_berths=berths,
        annual_actual_throughput_teu=throughput,
        crane_productivity_teu_per_hour=crane_rate,
        utilization_limit_pct=util_limit,
    )

    if json_out:
        _dump_json(res)
        return

    table = Table(title=f"Seaport Masterplan Capacity & Congestion Audit: {res.port_name}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    util_style = "green" if res.is_within_masterplan_limit else "red"
    table.add_row("Port Category", res.category.value)
    table.add_row("Total Berths", str(res.total_berths))
    table.add_row("Annual Throughput", f"{res.annual_actual_throughput_teu:,.0f} TEU")
    table.add_row("Designed Annual Capacity", f"{res.annual_capacity_teu:,.0f} TEU")
    table.add_row("Berth Occupancy (rho)", f"[{util_style}]{res.occupancy_rate_pct:.2f}%[/{util_style}] (Limit: {util_limit:.0f}%)")
    table.add_row("Expected Queue Delay (Wq)", f"{res.expected_queue_delay_hours:.2f} hours")
    table.add_row("Growth Headroom", f"{res.expansion_headroom_pct:.2f}%")
    table.add_row("Masterplan Recommendation", f"[{util_style}]{res.recommendation}[/{util_style}]")

    console.print(table)
