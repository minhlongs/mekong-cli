"""Typer CLI Sub-apps for Maritime Insurance, Casualty, Ship Sale & Seafarer Repatriation (Phases 211-214)."""

import json
from dataclasses import asdict
import typer
from rich.console import Console
from rich.table import Table

from src.core.maritime_insurance_casualty_sp_repatriation_engine import (
    MaritimeInsuranceSubrogationEngine, MarineCasualtyInvestigationEngine,
    ShipSalePurchaseEscrowEngine, InspectionOutcome, SaleformContractType,
    SeafarerRepatriationContingencyEngine, RepatriationTrigger,
)

console = Console()

maritimeins_app = typer.Typer(name="maritimeins", help="Marine Insurance Claims, Abandonment & Subrogation Rights under VMC Arts. 310-336.")
casualty_app = typer.Typer(name="casualty", help="Marine Casualty Investigation & Safety Reporting under IMO Res. MSC.255(84) & Circular 01/2020.")
shipsale_app = typer.Typer(name="shipsale", help="Ship Sale & Purchase Escrow & Closing Protocol under BIMCO SALEFORM 2012.")
repatriate_app = typer.Typer(name="repatriate", help="Seafarer Repatriation & MLC 2006 Standard A2.5 Financial Security Contingency Engine.")


def _print_result(title: str, rows: list[tuple[str, str]], verdict: str) -> None:
    table = Table(title=title)
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")
    for k, v in rows:
        table.add_row(k, v)
    console.print(table)
    console.print(f"[bold yellow]Verdict:[/bold yellow] {verdict}")


@maritimeins_app.command(name="assess")
def assess_marine_insurance(
    policy_id: str = typer.Option("POL-HULL-01", "--policy-id", help="Marine insurance policy reference"),
    vessel_name: str = typer.Option("MV PACIFIC OCEAN", "--vessel", help="Name of insured vessel"),
    insured_value: float = typer.Option(5000000.0, "--insured-val", help="Agreed insured value in USD"),
    repair_cost: float = typer.Option(4200000.0, "--repair-cost", help="Estimated casualty repair cost USD"),
    actual_total_loss: bool = typer.Option(False, "--total-loss", help="Whether vessel is physically destroyed/sunk"),
    salvage_value: float = typer.Option(200000.0, "--salvage-val", help="Estimated salvage value in USD"),
    deductible: float = typer.Option(50000.0, "--deductible", help="Policy deductible in USD"),
    abandonment: bool = typer.Option(True, "--abandonment", help="Whether Notice of Abandonment was tendered"),
    abandonment_days: int = typer.Option(30, "--abandonment-days", help="Days elapsed since casualty"),
    accepted_by_insurer: bool = typer.Option(False, "--accepted", help="Whether insurer accepted abandonment"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON format"),
):
    """Assess Marine Hull insurance claim, Constructive Total Loss, and subrogation assignment."""
    res = MaritimeInsuranceSubrogationEngine.assess_marine_claim(
        policy_id, vessel_name, insured_value, actual_total_loss, repair_cost,
        salvage_value, deductible, abandonment, abandonment_days, accepted_by_insurer,
    )
    if json_output:
        typer.echo(json.dumps({**asdict(res), "loss_type": res.loss_type.value, "abandonment_status": res.abandonment_status.value}, indent=2))
        return
    _print_result(f"Marine Insurance Claim Assessment: {vessel_name}", [
        ("Policy ID", res.policy_id), ("Insured Value", f"${res.insured_value_usd:,.2f} USD"),
        ("Loss Classification", res.loss_type.value), ("Estimated Repair Cost", f"${res.estimated_repair_cost_usd:,.2f} USD"),
        ("Constructive Total Loss (CTL)?", "YES" if res.is_constructive_total_loss else "NO"),
        ("Notice of Abandonment", res.abandonment_status.value), ("Indemnity Payable", f"${res.indemnity_payable_usd:,.2f} USD"),
        ("Deductible Applied", f"-${res.deductible_applied_usd:,.2f} USD"), ("Net Claim Payout", f"${res.net_claim_payout_usd:,.2f} USD"),
        ("Subrogation Rights Acquired", "YES" if res.subrogation_rights_acquired else "NO"),
        ("Max Subrogation Recovery Cap", f"${res.max_subrogation_recovery_usd:,.2f} USD"),
        ("Insurer Salvage Title", "YES" if res.insurer_salvage_title_acquired else "NO"),
    ], res.verdict)


@casualty_app.command(name="investigate")
def investigate_marine_casualty(
    incident_id: str = typer.Option("CAS-2026-001", "--id", help="Marine casualty incident reference"),
    vessel_name: str = typer.Option("MV MEKONG PHOENIX", "--vessel", help="Vessel name"),
    imo_number: str = typer.Option("9876543", "--imo", help="Vessel IMO number"),
    flag_state: str = typer.Option("Vietnam", "--flag", help="Flag state of vessel"),
    total_loss: bool = typer.Option(False, "--total-loss", help="Whether vessel was totally lost/sunk"),
    fatalities: int = typer.Option(0, "--fatalities", help="Number of lives lost"),
    severe_pollution: bool = typer.Option(False, "--severe-pollution", help="Whether severe pollution occurred"),
    severe_damage: bool = typer.Option(True, "--severe-damage", help="Structural immobilizing damage"),
    in_vn_waters: bool = typer.Option(True, "--in-vn-waters", help="Casualty within VN maritime zone"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON format"),
):
    """Classify marine casualty severity and calculate statutory investigation deadlines."""
    rep = MarineCasualtyInvestigationEngine.evaluate_casualty(
        incident_id, vessel_name, imo_number, flag_state, total_loss, fatalities, severe_pollution, severe_damage, in_vn_waters,
    )
    if json_output:
        typer.echo(json.dumps({**asdict(rep), "severity": rep.severity.value}, indent=2))
        return
    _print_result(f"Marine Casualty Investigation: {vessel_name} ({incident_id})", [
        ("IMO Number / Flag", f"{rep.imo_number} ({rep.flag_state})"), ("Casualty Severity", rep.severity.value),
        ("Mandatory Safety Investigation", "YES" if rep.mandatory_safety_investigation_required else "NO"),
        ("Initial Notification Deadline", f"{rep.initial_report_deadline_hours} hours"),
        ("Preliminary Report Deadline", f"{rep.preliminary_report_deadline_days} days"),
        ("Final Safety Report Deadline", f"{rep.final_safety_report_deadline_days} days"),
        ("VDR Preservation", "MANDATORY" if rep.vdr_preservation_mandatory else "OPTIONAL"),
        ("Investigating Authority", rep.investigating_authority),
    ], rep.verdict)


@shipsale_app.command(name="closing")
def closing_ship_saleform(
    contract_ref: str = typer.Option("MOA-2026-SALE-01", "--contract-ref", help="MOA Contract reference"),
    vessel_name: str = typer.Option("MV SOUTHERN STAR", "--vessel", help="Vessel name"),
    price: float = typer.Option(12000000.0, "--price", help="Total agreed purchase price in USD"),
    deposit_pct: float = typer.Option(10.0, "--deposit-pct", help="Deposit escrow percentage (usually 10%)"),
    escrow_verified: bool = typer.Option(True, "--escrow-verified", help="Escrow account verified"),
    defect_deduction: float = typer.Option(150000.0, "--defect-deduction", help="Underwater diver defect repair deduction USD"),
    bunkers_value: float = typer.Option(220000.0, "--bunkers-val", help="Value of remaining bunkers and lubes USD"),
    cancelling_breach: bool = typer.Option(False, "--cancelling-breach", help="NOR tendered after Cancelling Date"),
    buyer_default: bool = typer.Option(False, "--buyer-default", help="Buyer default on payment"),
    seller_default: bool = typer.Option(False, "--seller-default", help="Seller default on delivery"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON format"),
):
    """Compute financial closing balance, deposit escrow status, and documentary title transfer."""
    res = ShipSalePurchaseEscrowEngine.process_saleform_closing(
        contract_ref, vessel_name, price, deposit_pct, escrow_verified,
        InspectionOutcome.ACCEPTED_WITHOUT_CONDITION, defect_deduction, bunkers_value,
        cancelling_breach, buyer_default, seller_default, SaleformContractType.BIMCO_SALEFORM_2012,
    )
    if json_output:
        typer.echo(json.dumps({**asdict(res), "inspection_outcome": res.inspection_outcome.value}, indent=2))
        return
    _print_result(f"Ship Sale Closing Settlement: {vessel_name} ({contract_ref})", [
        ("Contract Price", f"${res.contract_price_usd:,.2f} USD"), ("Escrow Deposit (10%)", f"${res.deposit_amount_usd:,.2f} USD"),
        ("Defect Repair Holdback", f"-${res.underwater_defect_repair_deduction_usd:,.2f} USD"),
        ("Bunkers & Luboils Value", f"+${res.bunkers_and_luboils_value_usd:,.2f} USD"),
        ("Balance Payable on Delivery", f"${res.balance_payable_on_delivery_usd:,.2f} USD"),
        ("Deposit Forfeited (Default)", f"${res.escrow_deposit_forfeited_usd:,.2f} USD"),
        ("Title Transfer Approved", "YES" if res.legal_title_transfer_approved else "NO"),
    ], res.verdict)


@repatriate_app.command(name="audit")
def audit_seafarer_repatriation(
    case_ref: str = typer.Option("REP-2026-01", "--case-ref", help="Repatriation case reference"),
    vessel_name: str = typer.Option("MV MEKONG TRADER", "--vessel", help="Vessel name"),
    flag_state: str = typer.Option("Vietnam", "--flag", help="Vessel flag state"),
    seafarer_count: int = typer.Option(18, "--seafarers", help="Number of seafarers to be repatriated"),
    trigger: str = typer.Option("SHIPOWNER_INSOLVENCY_ABANDONMENT", "--trigger", help="Repatriation trigger reason"),
    security_valid: bool = typer.Option(True, "--security-valid", help="Compulsory MLC financial security certificate valid"),
    security_provider: str = typer.Option("West of England P&I Club", "--provider", help="Security provider / P&I Club"),
    flight_per_head: float = typer.Option(1200.0, "--flight-cost", help="Airfare ticket per seafarer USD"),
    sustenance_daily: float = typer.Option(60.0, "--daily-food", help="Daily food & accommodation per head USD"),
    stranded_days: int = typer.Option(10, "--days", help="Number of stranded days prior to departure"),
    wage_monthly: float = typer.Option(2200.0, "--monthly-wage", help="Average monthly wage per seafarer USD"),
    unpaid_months: float = typer.Option(3.0, "--unpaid-months", help="Unpaid back wage months (max 4mo MLC cap)"),
    emergency_med: float = typer.Option(5000.0, "--medical", help="Emergency medical stabilization costs USD"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON format"),
):
    """Audit seafarer repatriation expenses, financial security guarantee, and owner recourse liability."""
    trigger_enum = RepatriationTrigger.__members__.get(trigger, RepatriationTrigger.SHIPOWNER_INSOLVENCY_ABANDONMENT)
    res = SeafarerRepatriationContingencyEngine.assess_repatriation(
        case_ref, vessel_name, flag_state, seafarer_count, trigger_enum, security_valid,
        security_provider, flight_per_head, sustenance_daily, stranded_days, wage_monthly, unpaid_months, emergency_med,
    )
    if json_output:
        typer.echo(json.dumps({**asdict(res), "trigger_event": res.trigger_event.value}, indent=2))
        return
    _print_result(f"Seafarer Repatriation Audit: {vessel_name} ({case_ref})", [
        ("Seafarer Count", str(res.seafarer_count)), ("Trigger Event", res.trigger_event.value),
        ("Flight Tickets Total", f"${res.flight_tickets_total_usd:,.2f} USD"),
        ("Sustenance & Lodging", f"${res.sustenance_and_accommodation_usd:,.2f} USD"),
        ("Outstanding Wages Covered", f"${res.outstanding_wages_covered_usd:,.2f} USD"),
        ("Emergency Medical", f"${res.medical_stabilization_usd:,.2f} USD"),
        ("Total Repatriation Liability", f"${res.total_repatriation_liability_usd:,.2f} USD"),
        ("Insurer P&I Direct Guarantee", f"${res.insurer_direct_guarantee_payout_usd:,.2f} USD"),
        ("Consular Emergency Advance", f"${res.vietnam_consular_contingency_advance_usd:,.2f} USD"),
        ("MLC Compliance Status", res.mlc_standard_compliance),
    ], res.verdict)
