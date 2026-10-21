"""CLI Commands for Maritime Cargo Claims, Charterparty Laytime, Seafarer Wages & Towage/Pilotage (Phases 207-210)."""

import json
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from src.core.maritime_cargo_charterparty_seafarer_engine import (
    MaritimeCargoClaimsEngine, MaritimeLiabilityRegime, CarrierDefenseCategory,
    CharterpartyLaytimeEngine, LaytimeTerm, SeafarerMLCCompensationEngine,
    SeafarerRank, DisabilityDegree, MarinePilotageAndTowageEngine,
    TowageContractType, FlotillaCommandType,
)

console = Console()

cargoclaim_app = typer.Typer(name="cargoclaim", help="Carriage of Goods by Sea & Cargo Claims under VMC 2015 Arts. 145-174 & Hague-Visby.")
laytime_app = typer.Typer(name="laytime", help="Charterparty Laytime Calculation, Demurrage & Dispatch Performance Engine.")
seafarerwage_app = typer.Typer(name="seafarerwage", help="Seafarer Employment Agreement (SEA) & MLC 2006 Statutory Wage & Disability Suite.")
towagepilot_app = typer.Typer(name="towagepilot", help="Marine Pilotage Liability & Towage Contract Allocation under VMC 2015 Arts. 246-270.")


def _render_table(title: str, col1: str, col2: str, rows: list[tuple[str, str]]) -> None:
    table = Table(title=title)
    table.add_column(col1, style="cyan")
    table.add_column(col2, style="green")
    for k, v in rows:
        table.add_row(k, v)
    console.print(table)


@cargoclaim_app.command("assess")
def assess_cargo_claim(
    claim_id: str = typer.Option("CLM-2026-001", "--claim-id", help="Cargo claim reference"),
    cargo: str = typer.Option("ELECTRONICS_CONTAINER", "--cargo", help="Description of cargo"),
    packages: int = typer.Option(500, "--packages", help="Number of packages listed on Bill of Lading"),
    weight: float = typer.Option(15000.0, "--weight", help="Gross cargo weight in kg"),
    claimed_loss: float = typer.Option(600000.0, "--claimed-loss", help="Claimed cargo loss in USD"),
    regime: str = typer.Option("VIETNAM_MARITIME_CODE_2015", "--regime", help="Legal regime: VIETNAM_MARITIME_CODE_2015 | HAGUE_VISBY_RULES | HAMBURG_RULES"),
    defense: str = typer.Option("NONE", "--defense", help="Statutory carrier defense (e.g. NAUTICAL_FAULT_NAVIGATION_MANAGEMENT, PERILS_OF_THE_SEA, NONE)"),
    sdr_rate: float = typer.Option(1.35, "--sdr-rate", help="IMF SDR to USD conversion rate"),
    notice_days: int = typer.Option(0, "--notice-days", help="Days elapsed between delivery and notice of loss"),
    apparent: bool = typer.Option(True, "--apparent/--concealed", help="Whether damage was apparent or concealed"),
    days_since_delivery: int = typer.Option(30, "--days", help="Days elapsed since delivery for prescription audit"),
    due_diligence: bool = typer.Option(True, "--due-diligence/--no-due-diligence", help="Carrier exercised due diligence to make vessel seaworthy"),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format"),
):
    """Assess cargo loss claim under VMC 2015 Art. 152 dual ceiling and statutory defenses."""
    res = MaritimeCargoClaimsEngine.assess_cargo_claim(
        claim_id, cargo, packages, weight, claimed_loss, CarrierDefenseCategory[defense],
        MaritimeLiabilityRegime[regime], sdr_rate, notice_days, apparent, days_since_delivery, due_diligence,
    )
    if json_output:
        typer.echo(json.dumps(res.__dict__, indent=2))
        return
    _render_table(f"Cargo Claim Assessment: {claim_id}", "Metric", "Value", [
        ("Cargo Description", res.cargo_description),
        ("Claimed Loss", f"${res.claimed_loss_usd:,.2f}"),
        ("Package Limit Ceiling", f"${res.package_ceiling_usd:,.2f} ({res.number_of_packages} pkgs)"),
        ("Gross Weight Ceiling", f"${res.weight_ceiling_usd:,.2f} ({res.gross_weight_kg:,.1f} kg)"),
        ("Applicable Statutory Ceiling", f"${res.applicable_statutory_limit_usd:,.2f}"),
        ("Carrier Defense Invoked", res.carrier_defense.value),
        ("Carrier Defense Valid?", str(res.defense_valid)),
        ("1-Year Prescription Expired?", str(res.is_timebarred_1year_prescription)),
        ("Carrier Payout Liability", f"${res.carrier_payout_liability_usd:,.2f}"),
        ("Final Legal Verdict", res.verdict),
    ])


@laytime_app.command("calculate")
def calculate_laytime(
    charter_ref: str = typer.Option("CP-GENCON-2026", "--charter-ref", help="Charterparty reference code"),
    vessel: str = typer.Option("MV OCEAN FREIGHTER", "--vessel", help="Vessel name"),
    allowed_hours: float = typer.Option(72.0, "--allowed-hours", help="Total allowed laytime in hours"),
    nor_hour: int = typer.Option(10, "--nor-hour", help="Hour NOR tendered (0-23)"),
    nor_date: str = typer.Option("2026-10-01T10:00:00", "--nor-date", help="ISO timestamp of NOR tendering"),
    actual_hours: float = typer.Option(90.0, "--actual-hours", help="Total hours spent at berth"),
    weather_delay: float = typer.Option(6.0, "--weather-delay", help="Bad weather hours deducted (WWD)"),
    weekend_delay: float = typer.Option(0.0, "--weekend-delay", help="Weekend/holiday hours deducted (SHEX)"),
    term: str = typer.Option("WWD", "--term", help="Laytime terms: WWD | SHINC | SHEX"),
    demurrage_rate: float = typer.Option(15000.0, "--demurrage-rate", help="Daily demurrage rate in USD/day"),
    dispatch_rate: Optional[float] = typer.Option(None, "--dispatch-rate", help="Daily dispatch rate (default 50% demurrage)"),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format"),
):
    """Calculate charterparty laytime used, demurrage incurred, or dispatch earned."""
    res = CharterpartyLaytimeEngine.calculate_laytime(
        charter_ref, vessel, allowed_hours, nor_hour, nor_date, actual_hours,
        weather_delay, weekend_delay, LaytimeTerm[term], demurrage_rate, dispatch_rate,
    )
    if json_output:
        typer.echo(json.dumps(res.__dict__, indent=2))
        return
    _render_table(f"Laytime & Demurrage Audit: {charter_ref}", "Parameter", "Result", [
        ("Vessel Name", res.vessel_name), ("Laytime Terms", res.laytime_term.value),
        ("Allowed Laytime", f"{res.total_allowed_laytime_hours:.1f} hrs"),
        ("Counted Laytime Used", f"{res.laytime_used_hours:.1f} hrs"),
        ("Demurrage Hours", f"{res.demurrage_hours:.1f} hrs"),
        ("Time Saved Hours", f"{res.time_saved_hours:.1f} hrs"),
        ("Demurrage Payable", f"${res.demurrage_payable_usd:,.2f}"),
        ("Dispatch Receivable", f"${res.dispatch_receivable_usd:,.2f}"),
        ("Settlement Status", res.settlement_party), ("Summary Verdict", res.verdict),
    ])


@seafarerwage_app.command("audit")
def audit_seafarer_wages(
    name: str = typer.Option("NGUYEN VAN HAI", "--name", help="Seafarer full name"),
    rank: str = typer.Option("ABLE_SEAMAN", "--rank", help="Rank: MASTER | CHIEF_ENGINEER | ABLE_SEAMAN | CHIEF_COOK etc."),
    basic_wage: float = typer.Option(1800.0, "--basic-wage", help="Monthly basic wage in USD"),
    normal_ot: float = typer.Option(30.0, "--normal-ot", help="Normal overtime hours (150%)"),
    rest_ot: float = typer.Option(16.0, "--rest-ot", help="Rest day overtime hours (200%)"),
    holiday_ot: float = typer.Option(8.0, "--holiday-ot", help="Public holiday overtime hours (300%)"),
    months_service: float = typer.Option(6.0, "--service-months", help="Completed months of sea service"),
    medical_cost: float = typer.Option(0.0, "--med-cost", help="Medical treatment cost incurred in USD"),
    incapacity_months: float = typer.Option(0.0, "--incapacity-months", help="Months off duty due to medical condition"),
    disability: str = typer.Option("NONE", "--disability", help="Disability tier: NONE | TEMPORARY_PARTIAL | PERMANENT_PARTIAL_UNDER_50 | PERMANENT_SEVERE_50_TO_80 | PERMANENT_TOTAL_ABOVE_80 | DEATH_FATALITY"),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format"),
):
    """Audit seafarer wage, overtime tariffs and statutory disability compensation under MLC 2006."""
    rank_enum = SeafarerRank[rank]
    res = SeafarerMLCCompensationEngine.calculate_compensation(
        name, rank_enum, basic_wage, normal_ot, rest_ot, holiday_ot,
        months_service, medical_cost, incapacity_months, DisabilityDegree[disability],
    )
    if json_output:
        typer.echo(json.dumps(res.__dict__, indent=2))
        return
    _render_table(f"Seafarer Employment Audit: {name} ({rank_enum.value})", "Component", "Amount", [
        ("Basic Monthly Wage", f"${res.basic_monthly_wage_usd:,.2f}"),
        ("Monthly Wage with Overtime", f"${res.calculated_monthly_wage_usd:,.2f}"),
        ("Leave Days Accrued", f"{res.leave_days_accrued:.1f} days"),
        ("Paid Leave Allowance", f"${res.paid_leave_allowance_usd:,.2f}"),
        ("Medical Wage Maintenance", f"${res.medical_wage_maintenance_usd:,.2f}"),
        ("Disability Indemnity", f"${res.disability_compensation_usd:,.2f} ({res.disability_degree.value})"),
        ("Total Statutory Liability", f"${res.total_statutory_liability_usd:,.2f}"),
        ("MLC Status", res.mlc_compliance_status),
    ])


@towagepilot_app.command("assess")
def assess_towage_pilotage(
    operation_id: str = typer.Option("OPS-PILOT-001", "--op-id", help="Operation reference"),
    vessel: str = typer.Option("MV MEKONG CHALLENGER", "--vessel", help="Vessel name"),
    pilot_fee: float = typer.Option(3500.0, "--pilot-fee", help="Pilotage service fee collected in USD"),
    casualty_loss: float = typer.Option(250000.0, "--loss", help="Total marine casualty damages in USD"),
    pilot_error: bool = typer.Option(True, "--pilot-error/--no-pilot-error", help="Whether pilot navigational error is proven"),
    towage_type: str = typer.Option("PORT_ASSIST_BERTHING", "--tow-type", help="PORT_ASSIST_BERTHING | SEA_COASTAL_OCEAN_TOW"),
    command: str = typer.Option("TOWED_VESSEL_MASTER_COMMAND", "--command", help="Flotilla command authority: TOWED_VESSEL_MASTER_COMMAND | TUG_MASTER_COMMAND"),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format"),
):
    """Assess pilot statutory liability cap and towage flotilla command liability allocation."""
    res = MarinePilotageAndTowageEngine.evaluate_liability(
        operation_id, vessel, pilot_fee, casualty_loss, pilot_error,
        TowageContractType[towage_type], FlotillaCommandType[command],
    )
    if json_output:
        typer.echo(json.dumps(res.__dict__, indent=2))
        return
    _render_table(f"Pilotage & Towage Liability Allocation: {operation_id}", "Factor", "Apportionment", [
        ("Vessel Name", res.vessel_name),
        ("Total Marine Casualty Loss", f"${res.total_marine_casualty_loss_usd:,.2f}"),
        ("Pilot Error Proven?", str(res.pilot_error_proven)),
        ("Pilot Statutory Liability (Capped)", f"${res.statutory_pilot_liability_usd:,.2f}"),
        ("Master Navigation Liability", f"${res.master_navigation_liability_usd:,.2f}"),
        ("Flotilla Command Authority", res.command_authority.value),
        ("Tug Allocated Liability", f"${res.tug_allocated_liability_usd:,.2f}"),
        ("Towed Vessel Liability", f"${res.towed_vessel_allocated_liability_usd:,.2f}"),
        ("Summary Verdict", res.verdict),
    ])
