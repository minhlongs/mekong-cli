"""CLI Commands for Maritime Wreck Removal, LLMC, Marine Salvage & Sanctions (Phases 199-202)."""

import dataclasses
import enum
import json
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table

from src.core.maritime_wreck_llmc_salvage_engine import (
    MaritimeWreckRemovalEngine, MaritimeLLMCEngine, SalvageContractType,
    MaritimeSalvageSCOPICEngine, MaritimeViolationType, EntityType, MaritimePenaltiesEngine,
)

console = Console()

wreck_app = typer.Typer(name="wreck", help="Phase 199: Maritime Wreck Removal, 30/60d Deadlines & Auction Waterfalls (VMC Arts. 109-114).", no_args_is_help=True)
llmc_app = typer.Typer(name="llmc", help="Phase 200: Limitation of Liability for Maritime Claims - LLMC (VMC Arts. 299-309).", no_args_is_help=True)
salvage_app = typer.Typer(name="salvage", help="Phase 201: Marine Salvage, LOF 2024 & SCOPIC Remuneration (VMC Arts. 280-294).", no_args_is_help=True)
maritimepen_app = typer.Typer(name="maritimepen", help="Phase 202: Port State Maritime Administrative Penalties & Sanctions (Decree 162/2016 & 123/2021).", no_args_is_help=True)


def _json_serial(obj):
    if isinstance(obj, enum.Enum):
        return obj.value
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    return str(obj)


def _dump_json(obj):
    data = dataclasses.asdict(obj) if dataclasses.is_dataclass(obj) else (obj.__dict__ if hasattr(obj, "__dict__") else obj)
    print(json.dumps(data, indent=2, default=_json_serial))


def _print_table(title: str, cols: list[tuple[str, str]], rows: list[tuple[str, ...]]) -> None:
    table = Table(title=title)
    for c_name, c_style in cols:
        table.add_column(c_name, style=c_style)
    for r in rows:
        table.add_row(*r)
    console.print(table)


@wreck_app.command("evaluate")
def evaluate_wreck(
    vessel: str = typer.Option("MV SEA DRAGON", "--vessel", help="Vessel name of sunken obstruction"),
    gt: float = typer.Option(4500.0, "--gt", help="Gross Tonnage (GT)"),
    location: str = typer.Option("Vung Tau Fairway Buoy #0", "--location", help="Obstruction location"),
    notice_date: str = typer.Option("2026-08-01", "--notice", help="Date notice served by Port Authority (YYYY-MM-DD)"),
    assess_date: str = typer.Option("2026-09-15", "--assess", help="Evaluation assessment date (YYYY-MM-DD)"),
    plan_submitted: bool = typer.Option(True, "--plan-sub/--no-plan", help="Whether salvage plan was submitted"),
    plan_date: Optional[str] = typer.Option("2026-08-20", "--plan-date", help="Plan submission date (YYYY-MM-DD)"),
    salvage_commenced: bool = typer.Option(True, "--salvage-start/--no-salvage", help="Whether salvage commenced"),
    salvage_date: Optional[str] = typer.Option("2026-09-10", "--salvage-date", help="Salvage start date (YYYY-MM-DD)"),
    wrc_insurance: bool = typer.Option(True, "--wrc/--no-wrc", help="Has valid Nairobi WRC 2007 certificate"),
    gross_auction: float = typer.Option(0.0, "--auction-gross", help="Gross auction proceeds in VND"),
    salvage_cost: float = typer.Option(0.0, "--salvage-cost", help="Direct salvage expenditures in VND"),
    marking_dues: float = typer.Option(0.0, "--marking-dues", help="Port marking and channel dues in VND"),
    admin_cost: float = typer.Option(0.0, "--admin-cost", help="Storage and admin auction costs in VND"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Evaluate wreck clearance deadlines, compulsory insurance and auction waterfall."""
    eval_res = MaritimeWreckRemovalEngine.evaluate_wreck(vessel, gt, location, notice_date, assess_date, plan_submitted, plan_date, salvage_commenced, salvage_date, wrc_insurance, gross_auction, salvage_cost, marking_dues, admin_cost)
    if json_out:
        _dump_json(eval_res)
        return
    sc = "green" if not eval_res.forced_salvage_triggered else "red"
    _print_table(f"Wreck Removal Audit: {eval_res.vessel_name} ({eval_res.gross_tonnage:,.0f} GT)", [("Parameter", "cyan"), ("Value", "white")], [
        ("Wreck Status", f"[{sc}]{eval_res.status.value}[/{sc}]"), ("Days Since Notice", f"{eval_res.days_since_notice} days"),
        ("Plan Filed (30d Limit)", "[green]PASS[/green]" if eval_res.is_plan_timely else "[red]FAIL[/red]"),
        ("Salvage Started (60d Limit)", "[green]PASS[/green]" if eval_res.is_commencement_timely else "[red]FAIL[/red]"),
        ("WRC 2007 Insurance", "[green]VALID[/green]" if eval_res.wrc_insurance_valid else "[red]DEFICIENT[/red]"),
        ("Forced Salvage Triggered", f"[{sc}]{eval_res.forced_salvage_triggered}[/{sc}]"),
        ("Net Auction Surplus", f"{eval_res.net_auction_surplus_vnd:,.0f} VND"),
        ("Escrow Days Remaining", f"{eval_res.escrow_days_remaining} days"), ("Verdict", eval_res.verdict),
    ])


@llmc_app.command("calc")
def calculate_llmc(
    vessel: str = typer.Option("MV OCEAN FREIGHTER", "--vessel", help="Vessel name"),
    gt: float = typer.Option(25000.0, "--gt", help="Gross Tonnage (GT)"),
    life_claims: float = typer.Option(20000000.0, "--life-claims", help="Actual loss of life / personal injury claims (SDR)"),
    property_claims: float = typer.Option(15000000.0, "--prop-claims", help="Actual property claims (SDR)"),
    sdr_rate: float = typer.Option(33500.0, "--sdr-rate", help="SDR to VND exchange rate"),
    reckless: bool = typer.Option(False, "--reckless", help="Intentional act or recklessness proven (barring limitation)"),
    fund_constituted: bool = typer.Option(True, "--fund-lodged/--no-fund", help="Court limitation fund lodged"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Calculate LLMC statutory limitation funds and arrest immunity under VMC Arts. 299-309."""
    res = MaritimeLLMCEngine.calculate_limits(vessel, gt, life_claims, property_claims, sdr_rate, reckless, fund_constituted)
    if json_out:
        _dump_json(res)
        return
    lc = "green" if res.can_limit_liability else "red"
    _print_table(f"LLMC Maritime Claims Limitation Audit: {res.vessel_name} ({res.gross_tonnage:,.0f} GT)", [
        ("Limitation Fund Component", "cyan"), ("SDR Quantum", "white"), ("VND Equivalent", "green")
    ], [
        ("Life & Injury Limit (Art. 302)", f"{res.life_injury_limit_sdr:,.0f} SDR", f"{res.life_injury_limit_vnd:,.0f} VND"),
        ("Property Claims Limit (Art. 303)", f"{res.property_claims_limit_sdr:,.0f} SDR", f"{res.property_claims_limit_vnd:,.0f} VND"),
        ("Total Statutory Fund", f"{res.total_fund_limit_sdr:,.0f} SDR", f"{res.total_fund_limit_vnd:,.0f} VND"),
        ("Life Claims Rollover (Art. 304)", f"{res.rollover_to_property_sdr:,.0f} SDR", f"{res.rollover_to_property_sdr * res.sdr_to_vnd_rate:,.0f} VND"),
        ("Can Limit Liability", f"[{lc}]{res.can_limit_liability}[/{lc}]", "-"),
        ("Vessel Arrest Barred", f"[{lc}]{res.vessel_arrest_barred}[/{lc}]", "-"), ("Admiralty Verdict", res.verdict, "-"),
    ])


@salvage_app.command("evaluate")
def evaluate_salvage(
    contract: str = typer.Option("SCOPIC_INVOKED", "--contract", help="NO_CURE_NO_PAY_ART13, SCOPIC_INVOKED, COMMERCIAL_TOWAGE"),
    ship_val: float = typer.Option(3000000.0, "--ship-val", help="Post-casualty ship salved value in USD"),
    cargo_val: float = typer.Option(1500000.0, "--cargo-val", help="Salved cargo value in USD"),
    freight_val: float = typer.Option(300000.0, "--freight-val", help="Salved freight and bunkers in USD"),
    liens: float = typer.Option(100000.0, "--liens", help="Prior maritime liens in USD"),
    useful_result: bool = typer.Option(True, "--useful/--no-useful", help="Operations achieved useful result"),
    expenses: float = typer.Option(250000.0, "--expenses", help="Base salvor operational expenses in USD"),
    scopic_tariffs: float = typer.Option(600000.0, "--scopic-tariffs", help="SCOPIC equipment & tug tariffs in USD"),
    out_of_pocket: float = typer.Option(100000.0, "--out-of-pocket", help="Out-of-pocket expenses in USD"),
    pi_security: float = typer.Option(3000000.0, "--pi-security", help="P&I Club security lodged in USD"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Evaluate LOF 2024 Article 13 salvage rewards and SCOPIC Clause remuneration."""
    res = MaritimeSalvageSCOPICEngine.evaluate_salvage(
        contract_type=SalvageContractType(contract), ship_salved_val_usd=ship_val, cargo_salved_val_usd=cargo_val,
        freight_bunker_salved_val_usd=freight_val, prior_liens_usd=liens, useful_result=useful_result,
        base_salvor_expenses_usd=expenses, scopic_tariff_costs_usd=scopic_tariffs,
        out_of_pocket_expenses_usd=out_of_pocket, pi_security_lodged_usd=pi_security,
    )
    if json_out:
        _dump_json(res)
        return
    _print_table(f"Marine Salvage & SCOPIC Evaluation ({res.contract_type.value})", [("Salvor Metric", "cyan"), ("USD Amount", "white")], [
        ("Salved Fund Cap", f"${res.salved_fund_usd:,.2f}"), ("Article 13 Assessed Award", f"${res.article13_assessed_reward_usd:,.2f}"),
        ("SCOPIC Remuneration (Tariff + 25%)", f"${res.scopic_remuneration_usd:,.2f}"),
        ("Sub-Clause 6 Clawback Discount", f"${res.subclause6_discount_usd:,.2f}"),
        ("Final Payable to Salvor", f"[green]${res.final_payable_salvor_usd:,.2f}[/green]"),
        ("P&I Initial Security Adequate", "[green]YES[/green]" if res.pi_security_adequate else "[red]NO[/red]"),
        ("Salvage Award Verdict", res.verdict),
    ])


@maritimepen_app.command("assess")
def assess_penalties(
    vessel: str = typer.Option("MV VIOLATOR", "--vessel", help="Vessel registered name"),
    violator: str = typer.Option("Mekong Ocean Shipping Ltd", "--violator", help="Violator entity name"),
    entity: str = typer.Option("ORGANIZATION", "--entity", help="ORGANIZATION or INDIVIDUAL"),
    violation: Optional[List[str]] = typer.Option(["NO_PILOT", "DRAFT_EXCESS"], "--violation", help="NO_PILOT, SPEED_EXCESS, DRAFT_EXCESS, ILLEGAL_DISCHARGE, ACCIDENT_REPORTING_FAIL, ACCIDENT_CONCEALMENT"),
    severity: float = typer.Option(0.5, "--severity", help="Severity ratio between 0.0 (min fine) and 1.0 (max fine)"),
    paid: bool = typer.Option(False, "--paid", help="Has paid fine to State Treasury (KBNN)"),
    guarantee: bool = typer.Option(False, "--guarantee", help="Has posted bank or P&I guarantee"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Assess port state administrative penalties and departure clearance under Decree 162/2016 & 123/2021."""
    res = MaritimePenaltiesEngine.assess_penalties(vessel, violator, EntityType(entity), [MaritimeViolationType(v) for v in (violation or [])], severity, paid, guarantee)
    if json_out:
        _dump_json(res)
        return
    cc = "green" if res.clearance_status == "CLEARANCE_GRANTED" else "red"
    _print_table(f"Maritime Administrative Sanctions Assessment: {res.vessel_name}", [("Category", "cyan"), ("Finding", "white")], [
        ("Violator Entity", f"{res.violator_name} ({res.entity_type.value})"),
        ("Total Assessed Fines", f"[red]{res.total_fine_vnd:,.0f} VND[/red]"),
        ("Max Certificate Suspension", f"{res.max_suspension_months} months"),
        ("Departure Clearance Status", f"[{cc}]{res.clearance_status}[/{cc}]"),
        ("Mandatory Remediation", "; ".join(res.remedial_measures) or "None"),
        ("Port Authority Recommendation", f"[{cc}]{res.recommendation}[/{cc}]"),
    ])
