"""CLI Commands for Maritime Admiralty, General Average, Liens & Collision (Phases 203-206).

Typer Apps:
- mekong shiparrest / battau (Phase 203: Ship Arrest & Judicial Release)
- mekong genaverage / tonthatchung (Phase 204: General Average Adjustment under YAR 2016)
- mekong lienpriority / hangcamgiu (Phase 205: Maritime Liens & In Rem Priorities)
- mekong collision / damva (Phase 206: Collision Liability & Bunker Oil Pollution 2001)
"""

import dataclasses
import enum
import json
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from src.core.maritime_admiralty_ga_collision_engine import (
    MaritimeShipArrestEngine,
    MaritimeClaimType,
    ArrestSecurityType,
    GeneralAverageYAREngine,
    GeneralAverageInterest,
    MaritimeLienPriorityEngine,
    MaritimeLienRank,
    LienClaimItem,
    CollisionAndBunkerPollutionEngine,
    CollisionVesselParticulars,
)

console = Console()

shiparrest_app = typer.Typer(
    name="shiparrest",
    help="Phase 203: Ship Arrest & Judicial Release for Maritime Claims (VMC Arts. 129-144).",
    no_args_is_help=True,
)

genaverage_app = typer.Typer(
    name="genaverage",
    help="Phase 204: General Average Adjustment under York-Antwerp Rules 2016 (VMC Arts. 295-298).",
    no_args_is_help=True,
)

lienpriority_app = typer.Typer(
    name="lienpriority",
    help="Phase 205: Maritime Liens 5-Tier Statutory Waterfall & Mortgages (VMC Arts. 37-42).",
    no_args_is_help=True,
)

collision_app = typer.Typer(
    name="collision",
    help="Phase 206: Both-to-Blame Collision Apportionment & Bunker Oil Pollution (VMC Arts. 285-294).",
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
# Phase 203: Ship Arrest Commands
# ---------------------------------------------------------------------------

@shiparrest_app.command("audit")
def audit_ship_arrest(
    vessel: str = typer.Option("MV EASTERN TRADER", "--vessel", help="Vessel name under arrest warrant"),
    claim_type: str = typer.Option("COLLISION_OR_NAVIGATION_DAMAGE", "--claim-type", help="Maritime claim category under Art. 130"),
    amount: float = typer.Option(1000000.0, "--amount", help="Claim amount in USD"),
    counter_sec: float = typer.Option(150000.0, "--counter-sec", help="Counter-security provided by claimant in USD"),
    counter_type: str = typer.Option("BANK_GUARANTEE", "--counter-type", help="CASH_DEPOSIT_KBNN or BANK_GUARANTEE"),
    release_sec: float = typer.Option(0.0, "--release-sec", help="Security provided by shipowner for release in USD"),
    release_type: str = typer.Option("NONE", "--release-type", help="PI_CLUB_LOU, BANK_GUARANTEE, CASH_DEPOSIT_KBNN, NONE"),
    arrest_date: Optional[str] = typer.Option("2026-09-01", "--arrest-date", help="Date arrest order issued (YYYY-MM-DD)"),
    assess_date: Optional[str] = typer.Option("2026-09-15", "--assess-date", help="Assessment date (YYYY-MM-DD)"),
    court_action: bool = typer.Option(False, "--court-action/--no-court-action", help="Substantive court lawsuit filed within 30d"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Audit statutory ship arrest conditions, counter-security, and release rights under VMC Arts. 129-144."""
    ctype = MaritimeClaimType(claim_type)
    csec_type = ArrestSecurityType(counter_type)
    rsec_type = ArrestSecurityType(release_type)

    res = MaritimeShipArrestEngine.evaluate_arrest(
        vessel_name=vessel,
        claim_type=ctype,
        claim_amount_usd=amount,
        counter_security_provided_usd=counter_sec,
        counter_security_type=csec_type,
        security_for_release_provided_usd=release_sec,
        release_security_type=rsec_type,
        arrest_date_iso=arrest_date,
        assessment_date_iso=assess_date,
        court_action_commenced=court_action,
    )

    if json_out:
        _dump_json(res)
        return

    table = Table(title=f"Judicial Ship Arrest Audit: {res.vessel_name}")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Maritime Claim Category", res.claim_type.value)
    table.add_row("Principal Claim Quantum", f"${res.claim_amount_usd:,.2f} USD")
    table.add_row("Mandatory Counter-Security (15%)", f"${res.mandatory_counter_security_usd:,.2f} USD")
    table.add_row("Counter-Security Lodged", f"${res.counter_security_provided_usd:,.2f} USD")
    table.add_row("Counter-Security Sufficient", "[green]YES[/green]" if res.is_counter_security_sufficient else "[red]NO[/red]")
    table.add_row("Release Security Lodged", f"${res.security_for_release_provided_usd:,.2f} USD")
    table.add_row("Days Under Arrest", f"{res.days_under_arrest} days")
    table.add_row("30-Day Period Expired", "[red]EXPIRED[/red]" if res.is_expired_30d_limit else "[green]VALID[/green]")
    table.add_row("Admiralty Status", f"[yellow]{res.arrest_status.value}[/yellow]")
    table.add_row("Court Verdict", res.verdict)

    console.print(table)


# ---------------------------------------------------------------------------
# Phase 204: General Average Adjustment Commands
# ---------------------------------------------------------------------------

@genaverage_app.command("adjust")
def adjust_general_average(
    ship_sound: float = typer.Option(10000000.0, "--ship-sound", help="Sound value of ship in USD"),
    ship_sac: float = typer.Option(500000.0, "--ship-sac", help="Ship sacrifices made in USD"),
    ship_exp: float = typer.Option(250000.0, "--ship-exp", help="Port of refuge & salvage expenses incurred by ship in USD"),
    cargo_sound: float = typer.Option(5000000.0, "--cargo-sound", help="Invoice/CIF value of cargo in USD"),
    cargo_sac: float = typer.Option(300000.0, "--cargo-sac", help="Cargo jettisoned/sacrificed in USD"),
    freight_sound: float = typer.Option(500000.0, "--freight-sound", help="Gross freight at risk in USD"),
    rate: float = typer.Option(5.0, "--interest-rate", help="Annual interest rate percentage under Rule XXI"),
    delay: float = typer.Option(1.0, "--delay-years", help="Adjustment timeline delay in years"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Adjust General Average pool, contributions, and settlement balances under York-Antwerp Rules 2016."""
    ship_int = GeneralAverageInterest(
        name="SHIP",
        sound_value_usd=ship_sound,
        ga_sacrifice_usd=ship_sac,
        ga_expenditure_usd=ship_exp,
    )
    cargo_int = GeneralAverageInterest(
        name="CARGO",
        sound_value_usd=cargo_sound,
        ga_sacrifice_usd=cargo_sac,
        ga_expenditure_usd=0.0,
    )
    freight_int = GeneralAverageInterest(
        name="FREIGHT",
        sound_value_usd=freight_sound,
        ga_sacrifice_usd=0.0,
        ga_expenditure_usd=0.0,
    )

    res = GeneralAverageYAREngine.calculate_adjustment(
        ship_interest=ship_int,
        cargo_interest=cargo_int,
        freight_interest=freight_int,
        interest_rate_pct=rate,
        adjustment_delay_years=delay,
    )

    if json_out:
        _dump_json(res)
        return

    table = Table(title="York-Antwerp Rules 2016 General Average Adjustment Statement")
    table.add_column("Component", style="cyan")
    table.add_column("USD Amount", style="white")

    table.add_row("Total GA Sacrifices", f"${res.total_ga_sacrifice_usd:,.2f}")
    table.add_row("Total GA Expenditures", f"${res.total_ga_expenditure_usd:,.2f}")
    table.add_row("Rule XX Commission (2%)", f"${res.commission_allowance_usd:,.2f}")
    table.add_row("Rule XXI Interest Allowance", f"${res.interest_allowance_usd:,.2f}")
    table.add_row("Gross General Average Pool", f"[red]${res.gross_general_average_pool_usd:,.2f}[/red]")
    table.add_row("Total Contributory Values", f"${res.total_contributory_val_usd:,.2f}")
    table.add_row("General Average Ratio", f"[green]{res.ga_contribution_ratio * 100:.4f}%[/green]")
    table.add_row("Ship Net Settlement", f"${res.settlement_balances_usd['SHIP']:,.2f}")
    table.add_row("Cargo Net Settlement", f"${res.settlement_balances_usd['CARGO']:,.2f}")
    table.add_row("Freight Net Settlement", f"${res.settlement_balances_usd['FREIGHT']:,.2f}")
    table.add_row("Adjuster Verdict", res.verdict)

    console.print(table)


# ---------------------------------------------------------------------------
# Phase 205: Maritime Liens Priority Waterfall Commands
# ---------------------------------------------------------------------------

@lienpriority_app.command("waterfall")
def calculate_lien_waterfall(
    vessel: str = typer.Option("MV PACIFIC CARRIER", "--vessel", help="Auctioned vessel name"),
    auction_proceeds: float = typer.Option(3000000.0, "--proceeds", help="Gross judicial auction proceeds in USD"),
    auction_date: str = typer.Option("2026-10-01", "--auction-date", help="Judicial sale date (YYYY-MM-DD)"),
    court_costs: float = typer.Option(100000.0, "--court-costs", help="Judicial court & sale costs (USD)"),
    crew_wages: float = typer.Option(250000.0, "--crew-wages", help="Crew wages and repatriation (Rank 1) in USD"),
    personal_injury: float = typer.Option(400000.0, "--injury", help="Loss of life and bodily injury (Rank 2) in USD"),
    salvage: float = typer.Option(500000.0, "--salvage", help="Salvage reward & GA contribution (Rank 3) in USD"),
    port_dues: float = typer.Option(150000.0, "--port-dues", help="Port dues & pilotage (Rank 4) in USD"),
    collision_tort: float = typer.Option(300000.0, "--tort", help="Physical tort/collision damage (Rank 5) in USD"),
    mortgage: float = typer.Option(1500000.0, "--mortgage", help="Registered ship mortgage in USD"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Calculate 5-tier statutory maritime liens and mortgage distribution waterfall under VMC Arts. 37-42."""
    claims = [
        LienClaimItem("C-00", MaritimeLienRank.RANK_0_JUDICIAL_AUCTION_COSTS, "Maritime Court Sheriff", court_costs, "2026-09-25"),
        LienClaimItem("C-01", MaritimeLienRank.RANK_1_CREW_WAGES_REPATRIATION, "Officers & Crew Members", crew_wages, "2026-07-01"),
        LienClaimItem("C-02", MaritimeLienRank.RANK_2_LOSS_OF_LIFE_PERSONAL_INJURY, "Injured Stevedores & Seafarers", personal_injury, "2026-05-15"),
        LienClaimItem("C-03", MaritimeLienRank.RANK_3_SALVAGE_AND_GENERAL_AVERAGE, "Nippon Salvage Co", salvage, "2026-06-20"),
        LienClaimItem("C-04", MaritimeLienRank.RANK_4_PORT_DUES_PILOTAGE_FEES, "Vung Tau Port Authority", port_dues, "2026-08-10"),
        LienClaimItem("C-05", MaritimeLienRank.RANK_5_COLLISION_TORT_PHYSICAL_DAMAGE, "Wharf Facility Owner", collision_tort, "2026-04-01"),
        LienClaimItem("C-06", MaritimeLienRank.RANK_6_REGISTERED_MORTGAGE, "Vietcombank Maritime Finance", mortgage, "2024-01-01"),
    ]

    res = MaritimeLienPriorityEngine.calculate_priority_waterfall(
        vessel_name=vessel,
        gross_auction_proceeds_usd=auction_proceeds,
        claims=claims,
        auction_date_iso=auction_date,
    )

    if json_out:
        _dump_json(res)
        return

    table = Table(title=f"Maritime Liens Statutory Waterfall Audit: {res.vessel_name}")
    table.add_column("Claim ID", style="cyan")
    table.add_column("Rank & Creditor", style="white")
    table.add_column("Claim Amount", style="white")
    table.add_column("Disbursed", style="green")
    table.add_column("Shortfall", style="red")
    table.add_column("Status", style="yellow")

    for s in res.settlements:
        table.add_row(
            s.claim_id,
            f"{s.rank.value}\n({s.creditor})",
            f"${s.original_claim_usd:,.2f}",
            f"${s.paid_amount_usd:,.2f}",
            f"${s.shortfall_amount_usd:,.2f}",
            s.status,
        )

    table.add_section()
    table.add_row("TOTALS", "Auction Pool Disbursed", f"${res.total_claims_usd:,.2f}", f"${res.total_disbursed_usd:,.2f}", f"${res.total_claims_usd - res.total_disbursed_usd:,.2f}", f"Surplus: ${res.remaining_surplus_to_owner_usd:,.2f}")

    console.print(table)


# ---------------------------------------------------------------------------
# Phase 206: Collision & Bunker Pollution Commands
# ---------------------------------------------------------------------------

@collision_app.command("assess")
def assess_collision(
    vessel_a: str = typer.Option("MV VIET DRAGON", "--vessel-a", help="First colliding vessel name"),
    gt_a: float = typer.Option(12000.0, "--gt-a", help="Gross tonnage of Vessel A"),
    damage_a: float = typer.Option(800000.0, "--damage-a", help="Vessel A physical hull damage in USD"),
    cargo_a: float = typer.Option(200000.0, "--cargo-a", help="Vessel A cargo damage in USD"),
    demurrage_a: float = typer.Option(50000.0, "--demurrage-a", help="Vessel A loss of use / demurrage in USD"),
    vessel_b: str = typer.Option("MV NORDIC TRADER", "--vessel-b", help="Second colliding vessel name"),
    gt_b: float = typer.Option(18000.0, "--gt-b", help="Gross tonnage of Vessel B"),
    damage_b: float = typer.Option(500000.0, "--damage-b", help="Vessel B physical hull damage in USD"),
    cargo_b: float = typer.Option(100000.0, "--cargo-b", help="Vessel B cargo damage in USD"),
    demurrage_b: float = typer.Option(40000.0, "--demurrage-b", help="Vessel B loss of use in USD"),
    fault_a: float = typer.Option(70.0, "--fault-a", help="Fault percentage of Vessel A (0-100)"),
    injury_pool: float = typer.Option(300000.0, "--injury-pool", help="Total third-party bodily injury pool in USD"),
    injury_paid_a: float = typer.Option(300000.0, "--injury-paid-a", help="Injury compensation settled by Vessel A in USD"),
    bunker_card_a: bool = typer.Option(True, "--blue-card-a/--no-blue-card-a", help="Vessel A has Bunker 2001 Blue Card"),
    bunker_card_b: bool = typer.Option(True, "--blue-card-b/--no-blue-card-b", help="Vessel B has Bunker 2001 Blue Card"),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Assess collision cross-liabilities, bodily injury recourse, and Bunker 2001 compliance."""
    p_a = CollisionVesselParticulars(
        name=vessel_a,
        gross_tonnage=gt_a,
        physical_damage_usd=damage_a,
        cargo_damage_usd=cargo_a,
        demurrage_loss_usd=demurrage_a,
        bodily_injury_claims_paid_usd=injury_paid_a,
        has_valid_bunker_blue_card=bunker_card_a,
    )
    p_b = CollisionVesselParticulars(
        name=vessel_b,
        gross_tonnage=gt_b,
        physical_damage_usd=damage_b,
        cargo_damage_usd=cargo_b,
        demurrage_loss_usd=demurrage_b,
        bodily_injury_claims_paid_usd=0.0,
        has_valid_bunker_blue_card=bunker_card_b,
    )

    res = CollisionAndBunkerPollutionEngine.assess_collision(
        vessel_a=p_a,
        vessel_b=p_b,
        fault_percentage_a=fault_a,
        total_bodily_injury_pool_usd=injury_pool,
    )

    if json_out:
        _dump_json(res)
        return

    table = Table(title=f"Maritime Collision & Bunker Pollution Assessment: {res.vessel_a_name} vs {res.vessel_b_name}")
    table.add_column("Category", style="cyan")
    table.add_column("Finding", style="white")

    table.add_row("Fault Apportionment", f"{res.vessel_a_name}: {res.fault_ratio_a*100:.1f}% | {res.vessel_b_name}: {res.fault_ratio_b*100:.1f}%")
    table.add_row("Total Losses", f"{res.vessel_a_name}: ${res.total_loss_a_usd:,.2f} | {res.vessel_b_name}: ${res.total_loss_b_usd:,.2f}")
    table.add_row("Admiralty Cross-Liability", f"{res.vessel_a_name} owes: ${res.liability_a_to_b_usd:,.2f} | {res.vessel_b_name} owes: ${res.liability_b_to_a_usd:,.2f}")
    table.add_row("Net Payable", f"[red]${res.net_cross_liability_usd:,.2f} USD[/red] payable by [yellow]{res.net_paying_vessel}[/yellow]")
    table.add_row("Bodily Injury Recourse", f"[green]${res.bodily_injury_recourse_usd:,.2f} USD[/green] claimable by [cyan]{res.recourse_claimant}[/cyan]")
    table.add_row("Bunker 2001 Certification", "[green]COMPLIANT[/green]" if res.bunker_convention_compliant else "[red]DEFICIENT[/red]")
    table.add_row("Admiralty Verdict", res.verdict)

    console.print(table)
