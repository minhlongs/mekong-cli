"""Typer CLI Sub-apps for Maritime Insurance, Casualty, Ship Sale & Seafarer Repatriation (Phases 211-214).

Covers:
- Phase 211: Marine Insurance & Subrogation (maritimeins / baohiemhanghai)
- Phase 212: Marine Casualty Investigation (casualty / tainanhanghai)
- Phase 213: Ship Sale & Purchase Escrow (shipsale / muabantau)
- Phase 214: Seafarer Repatriation Contingency (repatriate / hoihuong)
"""

import json
from dataclasses import asdict
import typer
from rich.console import Console
from rich.table import Table

from src.core.maritime_insurance_casualty_sp_repatriation_engine import (
    MaritimeInsuranceSubrogationEngine,
    MarineCasualtyInvestigationEngine,
    ShipSalePurchaseEscrowEngine,
    InspectionOutcome,
    SaleformContractType,
    SeafarerRepatriationContingencyEngine,
    RepatriationTrigger,
)

console = Console()

# ---------------------------------------------------------------------------
# 1. Maritime Insurance Subrogation App (Phase 211)
# ---------------------------------------------------------------------------
maritimeins_app = typer.Typer(
    name="maritimeins",
    help="Marine Insurance Claims, Abandonment & Subrogation Rights under VMC Arts. 310-336.",
)


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
        policy_id=policy_id,
        vessel_name=vessel_name,
        insured_value_usd=insured_value,
        actual_total_loss=actual_total_loss,
        estimated_repair_cost_usd=repair_cost,
        salvage_value_usd=salvage_value,
        policy_deductible_usd=deductible,
        notice_of_abandonment_tendered=abandonment,
        abandonment_days_since_casualty=abandonment_days,
        abandonment_accepted_by_insurer=accepted_by_insurer,
    )

    if json_output:
        data = asdict(res)
        data["loss_type"] = res.loss_type.value
        data["abandonment_status"] = res.abandonment_status.value
        typer.echo(json.dumps(data, indent=2))
        return

    table = Table(title=f"Marine Insurance Claim Assessment: {vessel_name}")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Policy ID", res.policy_id)
    table.add_row("Insured Value", f"${res.insured_value_usd:,.2f} USD")
    table.add_row("Loss Classification", res.loss_type.value)
    table.add_row("Estimated Repair Cost", f"${res.estimated_repair_cost_usd:,.2f} USD")
    table.add_row("Constructive Total Loss (CTL)?", "YES" if res.is_constructive_total_loss else "NO")
    table.add_row("Notice of Abandonment", res.abandonment_status.value)
    table.add_row("Indemnity Payable", f"${res.indemnity_payable_usd:,.2f} USD")
    table.add_row("Deductible Applied", f"-${res.deductible_applied_usd:,.2f} USD")
    table.add_row("Net Claim Payout", f"${res.net_claim_payout_usd:,.2f} USD")
    table.add_row("Subrogation Rights Acquired", "YES" if res.subrogation_rights_acquired else "NO")
    table.add_row("Max Subrogation Recovery Cap", f"${res.max_subrogation_recovery_usd:,.2f} USD")
    table.add_row("Insurer Salvage Title", "YES" if res.insurer_salvage_title_acquired else "NO")
    console.print(table)
    console.print(f"[bold yellow]Verdict:[/bold yellow] {res.verdict}")


# ---------------------------------------------------------------------------
# 2. Marine Casualty Investigation App (Phase 212)
# ---------------------------------------------------------------------------
casualty_app = typer.Typer(
    name="casualty",
    help="Marine Casualty Investigation & Safety Reporting under IMO Res. MSC.255(84) & Circular 01/2020.",
)


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
        incident_id=incident_id,
        vessel_name=vessel_name,
        imo_number=imo_number,
        flag_state=flag_state,
        total_loss_of_ship=total_loss,
        fatalities_count=fatalities,
        severe_pollution_occurred=severe_pollution,
        structural_damage_severe=severe_damage,
        in_vietnam_internal_or_territorial_waters=in_vn_waters,
    )

    if json_output:
        data = asdict(rep)
        data["severity"] = rep.severity.value
        typer.echo(json.dumps(data, indent=2))
        return

    table = Table(title=f"Marine Casualty Investigation: {vessel_name} ({incident_id})")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("IMO Number / Flag", f"{rep.imo_number} ({rep.flag_state})")
    table.add_row("Casualty Severity", rep.severity.value)
    table.add_row("Mandatory Safety Investigation", "YES" if rep.mandatory_safety_investigation_required else "NO")
    table.add_row("Initial Notification Deadline", f"{rep.initial_report_deadline_hours} hours")
    table.add_row("Preliminary Report Deadline", f"{rep.preliminary_report_deadline_days} days")
    table.add_row("Final Safety Report Deadline", f"{rep.final_safety_report_deadline_days} days")
    table.add_row("VDR Preservation", "MANDATORY" if rep.vdr_preservation_mandatory else "OPTIONAL")
    table.add_row("Investigating Authority", rep.investigating_authority)
    console.print(table)
    console.print(f"[bold yellow]Verdict:[/bold yellow] {rep.verdict}")


# ---------------------------------------------------------------------------
# 3. Ship Sale & Purchase (Saleform) Escrow App (Phase 213)
# ---------------------------------------------------------------------------
shipsale_app = typer.Typer(
    name="shipsale",
    help="Ship Sale & Purchase Escrow & Closing Protocol under BIMCO SALEFORM 2012.",
)


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
        contract_ref=contract_ref,
        vessel_name=vessel_name,
        contract_price_usd=price,
        deposit_percentage=deposit_pct,
        escrow_agent_verified=escrow_verified,
        inspection_outcome=InspectionOutcome.ACCEPTED_WITHOUT_CONDITION,
        underwater_defect_repair_deduction_usd=defect_deduction,
        bunkers_and_luboils_value_usd=bunkers_value,
        cancelling_date_breached=cancelling_breach,
        buyer_default=buyer_default,
        seller_default=seller_default,
        contract_type=SaleformContractType.BIMCO_SALEFORM_2012,
    )

    if json_output:
        data = asdict(res)
        data["inspection_outcome"] = res.inspection_outcome.value
        typer.echo(json.dumps(data, indent=2))
        return

    table = Table(title=f"Ship Sale Closing Settlement: {vessel_name} ({contract_ref})")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Contract Price", f"${res.contract_price_usd:,.2f} USD")
    table.add_row("Escrow Deposit (10%)", f"${res.deposit_amount_usd:,.2f} USD")
    table.add_row("Defect Repair Holdback", f"-${res.underwater_defect_repair_deduction_usd:,.2f} USD")
    table.add_row("Bunkers & Luboils Value", f"+${res.bunkers_and_luboils_value_usd:,.2f} USD")
    table.add_row("Balance Payable on Delivery", f"${res.balance_payable_on_delivery_usd:,.2f} USD")
    table.add_row("Deposit Forfeited (Default)", f"${res.escrow_deposit_forfeited_usd:,.2f} USD")
    table.add_row("Title Transfer Approved", "YES" if res.legal_title_transfer_approved else "NO")
    console.print(table)
    console.print(f"[bold yellow]Verdict:[/bold yellow] {res.verdict}")


# ---------------------------------------------------------------------------
# 4. Seafarer Repatriation Contingency App (Phase 214)
# ---------------------------------------------------------------------------
repatriate_app = typer.Typer(
    name="repatriate",
    help="Seafarer Repatriation & MLC 2006 Standard A2.5 Financial Security Contingency Engine.",
)


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
    try:
        trigger_enum = RepatriationTrigger[trigger]
    except KeyError:
        trigger_enum = RepatriationTrigger.SHIPOWNER_INSOLVENCY_ABANDONMENT

    res = SeafarerRepatriationContingencyEngine.assess_repatriation(
        case_ref=case_ref,
        vessel_name=vessel_name,
        flag_state=flag_state,
        seafarer_count=seafarer_count,
        trigger_event=trigger_enum,
        compulsory_financial_security_valid=security_valid,
        security_provider=security_provider,
        flight_cost_per_seafarer_usd=flight_per_head,
        sustenance_daily_usd=sustenance_daily,
        stranded_days=stranded_days,
        average_monthly_wage_usd=wage_monthly,
        unpaid_wage_months=unpaid_months,
        emergency_medical_usd=emergency_med,
    )

    if json_output:
        data = asdict(res)
        data["trigger_event"] = res.trigger_event.value
        typer.echo(json.dumps(data, indent=2))
        return

    table = Table(title=f"Seafarer Repatriation Audit: {vessel_name} ({case_ref})")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Seafarer Count", str(res.seafarer_count))
    table.add_row("Trigger Event", res.trigger_event.value)
    table.add_row("Flight Tickets Total", f"${res.flight_tickets_total_usd:,.2f} USD")
    table.add_row("Sustenance & Lodging", f"${res.sustenance_and_accommodation_usd:,.2f} USD")
    table.add_row("Outstanding Wages Covered", f"${res.outstanding_wages_covered_usd:,.2f} USD")
    table.add_row("Emergency Medical", f"${res.medical_stabilization_usd:,.2f} USD")
    table.add_row("Total Repatriation Liability", f"${res.total_repatriation_liability_usd:,.2f} USD")
    table.add_row("Insurer P&I Direct Guarantee", f"${res.insurer_direct_guarantee_payout_usd:,.2f} USD")
    table.add_row("Consular Emergency Advance", f"${res.vietnam_consular_contingency_advance_usd:,.2f} USD")
    table.add_row("MLC Compliance Status", res.mlc_standard_compliance)
    console.print(table)
    console.print(f"[bold yellow]Verdict:[/bold yellow] {res.verdict}")
