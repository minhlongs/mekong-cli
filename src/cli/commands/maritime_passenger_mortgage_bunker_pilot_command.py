# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Typer CLI Sub-apps for Passenger Transport, Ship Mortgage, Bunkering & Pilotage Exemption (Phases 215-218)."""

import json
from dataclasses import asdict
import typer
from rich.console import Console
from rich.table import Table

from src.core.maritime_passenger_mortgage_bunker_pilot_engine import (
    BunkeringNavigationZone,
    ForeclosureClaimEntry,
    LuggageCategory,
    MarineBunkerFuelMarpolEngine,
    MaritimePassengerCarrierLiabilityEngine,
    MaritimePilotageExemptionEngine,
    MortgagePriorityTier,
    PassengerClaimItem,
    PassengerIncidentCategory,
    ScrubberType,
    ShipMortgageForeclosureAuctionEngine,
    VesselCargoRiskType,
)

console = Console()
passenger_app = typer.Typer(name="passenger", help="Maritime Passenger Transport Carrier Liability & Athens Convention 2002 under VMC Arts. 196-213.")
mortgage_app = typer.Typer(name="mortgage", help="Ship Mortgage Foreclosure & Judicial Sale Priority Waterfall under VMC Arts. 37-42.")
bunker_app = typer.Typer(name="bunker", help="Marine Bunkering BDN, MARPOL Annex VI LSFO Compliance & Scrubber Washwater Audit.")
pilotwaiver_app = typer.Typer(name="pilotwaiver", help="Marine Pilotage Exemption Certification & Navigation Safety under VMC Arts. 246-259.")


@passenger_app.command(name="assess")
def assess_passenger_liability(
    case_ref: str = typer.Option("PAX-2026-001", "--case-ref", help="Incident case reference"),
    vessel_name: str = typer.Option("MV MEKONG PRINCESS", "--vessel", help="Name of passenger vessel"),
    capacity: int = typer.Option(250, "--capacity", help="Licensed passenger carrying capacity"),
    incident_type: str = typer.Option("SHIPPING_INCIDENT", "--incident-type", help="SHIPPING_INCIDENT or NON_SHIPPING_INCIDENT"),
    injury_claim: float = typer.Option(350000.0, "--injury-claim", help="Claimed personal injury amount USD"),
    luggage_claim: float = typer.Option(2500.0, "--luggage-claim", help="Claimed luggage loss amount USD"),
    luggage_type: str = typer.Option("CABIN_LUGGAGE", "--luggage-type", help="CABIN_LUGGAGE, VEHICLE_AND_CARRIED, or OTHER_LUGGAGE"),
    pax_negligence: float = typer.Option(0.0, "--negligence-pct", help="Contributory negligence percentage (0-100)"),
    sdr_rate: float = typer.Option(1.33, "--sdr-rate", help="1 SDR to USD exchange rate"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON format"),
) -> None:
    """Evaluate passenger carrier liability caps, contributory negligence, and compulsory insurance."""
    cat_enum = PassengerIncidentCategory.__members__.get(incident_type, PassengerIncidentCategory.SHIPPING_INCIDENT)
    luggage_enum = LuggageCategory.__members__.get(luggage_type, LuggageCategory.CABIN_LUGGAGE)
    sample_claim = PassengerClaimItem("PAX-01", "Lead Passenger", injury_claim > 0, injury_claim, luggage_enum if luggage_claim > 0 else None, luggage_claim, pax_negligence)
    res = MaritimePassengerCarrierLiabilityEngine.evaluate_passenger_claims(case_ref=case_ref, vessel_name=vessel_name, licensed_passenger_capacity=capacity, incident_category=cat_enum, claims=[sample_claim], sdr_usd_rate=sdr_rate)
    if json_output:
        data = asdict(res)
        data["incident_category"] = res.incident_category.value
        typer.echo(json.dumps(data, indent=2))
        return
    table = Table(title=f"Passenger Carrier Liability Assessment: {vessel_name} ({case_ref})")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")
    for k, v in (("Licensed Pax Capacity", str(res.licensed_passenger_capacity)), ("Incident Classification", res.incident_category.value), ("Strict Liability Cap / Pax", f"${res.carrier_strict_liability_limit_per_pax_usd:,.2f} USD"), ("Total Claimed Amount", f"${res.total_claimed_usd:,.2f} USD"), ("Gross Payable (Athens Caps)", f"${res.gross_carrier_payable_usd:,.2f} USD"), ("Contributory Negligence Deduction", f"-${res.contributory_negligence_deductions_usd:,.2f} USD"), ("Net Carrier Payable", f"${res.net_carrier_liability_usd:,.2f} USD"), ("Compulsory Insurance Required", "YES" if res.compulsory_financial_security_required else "NO"), ("Compulsory Security Minimum", f"${res.compulsory_security_minimum_usd:,.2f} USD")):
        table.add_row(k, v)
    console.print(table)
    console.print(f"[bold yellow]Verdict:[/bold yellow] {res.verdict}")


@mortgage_app.command(name="auction")
def execute_auction_waterfall(
    auction_ref: str = typer.Option("AUC-2026-001", "--auction-ref", help="Judicial auction case reference"),
    vessel_name: str = typer.Option("MV OCEAN GIANT", "--vessel", help="Name of foreclosed vessel"),
    reserve_price: float = typer.Option(8000000.0, "--reserve-price", help="Court reserve auction price USD"),
    winning_bid: float = typer.Option(8500000.0, "--winning-bid", help="Actual winning auction bid USD"),
    court_costs: float = typer.Option(100000.0, "--court-costs", help="Judicial court & custody costs USD"),
    crew_wages_lien: float = typer.Option(300000.0, "--crew-lien", help="Crew unpaid wages & repatriation lien USD"),
    first_mortgage: float = typer.Option(5000000.0, "--first-mortgage", help="First registered mortgage USD"),
    second_mortgage: float = typer.Option(2000000.0, "--second-mortgage", help="Second registered mortgage USD"),
    unsecured_debt: float = typer.Option(2500000.0, "--unsecured", help="Trade suppliers unsecured claims USD"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON format"),
) -> None:
    """Execute statutory proceeds distribution waterfall and verify unencumbered title purge."""
    claims = [
        ForeclosureClaimEntry("Court Marshal Custody & Sale Costs", MortgagePriorityTier.TIER_0_COURT_AND_AUCTION_COSTS, court_costs),
        ForeclosureClaimEntry("Crew Statutory Wage Liens", MortgagePriorityTier.TIER_1_MARITIME_LIENS, crew_wages_lien, lien_age_days=60),
        ForeclosureClaimEntry("Bank Alpha 1st Preferred Mortgage", MortgagePriorityTier.TIER_3_REGISTERED_MORTGAGES, first_mortgage, mortgage_registration_order=1),
        ForeclosureClaimEntry("Bank Beta 2nd Mortgage", MortgagePriorityTier.TIER_3_REGISTERED_MORTGAGES, second_mortgage, mortgage_registration_order=2),
        ForeclosureClaimEntry("Bunker & Ship Chandlers Unsecured", MortgagePriorityTier.TIER_4_UNSECURED_CREDITORS, unsecured_debt),
    ]
    res = ShipMortgageForeclosureAuctionEngine.execute_foreclosure_distribution(auction_case_ref=auction_ref, vessel_name=vessel_name, reserve_price_usd=reserve_price, actual_winning_bid_usd=winning_bid, claims=claims)
    if json_output:
        data = asdict(res)
        for d in data["distributions"]:
            d["tier"] = d["tier"].value if hasattr(d["tier"], "value") else d["tier"]
        typer.echo(json.dumps(data, indent=2))
        return
    table = Table(title=f"Judicial Sale Priority Waterfall: {vessel_name} ({auction_ref})")
    table.add_column("Creditor / Tier", style="cyan")
    table.add_column("Claimed USD", justify="right")
    table.add_column("Payout USD", justify="right", style="green")
    table.add_column("Deficiency USD", justify="right", style="red")
    table.add_column("Recovery %", justify="right")
    for dist in res.distributions:
        tier_str = dist.tier.value if hasattr(dist.tier, "value") else str(dist.tier)
        table.add_row(f"{dist.creditor_name}\n({tier_str})", f"${dist.claimed_usd:,.2f}", f"${dist.payout_usd:,.2f}", f"${dist.deficiency_usd:,.2f}", f"{dist.satisfaction_rate_percent:.1f}%")
    console.print(table)
    console.print(f"[bold cyan]Total Winning Bid:[/bold cyan] ${res.actual_winning_bid_usd:,.2f} USD\n[bold green]Total Distributed:[/bold green] ${res.total_proceeds_distributed_usd:,.2f} USD\n[bold blue]Surplus Returned to Owner:[/bold blue] ${res.residual_surplus_to_owner_usd:,.2f} USD\n[bold yellow]Verdict:[/bold yellow] {res.verdict}")


@bunker_app.command(name="audit")
def audit_bunker_fuel(
    bdn_number: str = typer.Option("BDN-2026-088", "--bdn", help="Bunker Delivery Note serial number"),
    vessel_name: str = typer.Option("MV MEKONG SEAWAYS", "--vessel", help="Vessel name"),
    imo_number: str = typer.Option("9786543", "--imo", help="Vessel IMO number"),
    supplier: str = typer.Option("Petrolimex Marine Bunkering", "--supplier", help="Licensed bunker supplier name"),
    sulphur_content: float = typer.Option(0.48, "--sulphur", help="Fuel sulphur content percent (m/m)"),
    flashpoint: float = typer.Option(64.0, "--flashpoint", help="Fuel flashpoint degrees Celsius (min 60)"),
    zone: str = typer.Option("GLOBAL_HIGH_SEAS", "--zone", help="GLOBAL_HIGH_SEAS, EMISSION_CONTROL_AREA_ECA, or VIETNAMESE_INTERNAL_PORT_WATERS"),
    scrubber: str = typer.Option("NONE", "--scrubber", help="NONE, OPEN_LOOP, CLOSED_LOOP, or HYBRID"),
    scrubber_active: bool = typer.Option(False, "--scrubber-active", help="Whether scrubber is in operation"),
    washwater_ph: float = typer.Option(7.2, "--ph", help="Scrubber discharge washwater pH"),
    turbidity: float = typer.Option(8.0, "--turbidity", help="Scrubber washwater turbidity increase (NTU)"),
    sealed_sample: bool = typer.Option(True, "--sample-sealed", help="MARPOL representative sample sealed and signed"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON format"),
) -> None:
    """Audit Bunker Delivery Note and MARPOL Annex VI fuel oil quality limits."""
    zone_enum = BunkeringNavigationZone.__members__.get(zone, BunkeringNavigationZone.GLOBAL_HIGH_SEAS)
    scrubber_enum = ScrubberType.__members__.get(scrubber, ScrubberType.NONE)
    res = MarineBunkerFuelMarpolEngine.audit_bunkering_compliance(bdn_number=bdn_number, vessel_name=vessel_name, imo_number=imo_number, bunker_supplier_name=supplier, fuel_sulphur_content_percent=sulphur_content, fuel_flashpoint_celsius=flashpoint, navigation_zone=zone_enum, scrubber_installed=scrubber_enum, scrubber_active=scrubber_active, scrubber_washwater_ph=washwater_ph, scrubber_turbidity_ntu_increase=turbidity, marpol_sample_sealed=sealed_sample)
    if json_output:
        data = asdict(res)
        data["navigation_zone"] = res.navigation_zone.value
        data["scrubber_installed"] = res.scrubber_installed.value
        typer.echo(json.dumps(data, indent=2))
        return
    table = Table(title=f"Bunkering & MARPOL Annex VI Audit: {vessel_name} ({bdn_number})")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")
    for k, v in (("Bunker Supplier", res.bunker_supplier_name), ("Fuel Sulphur Content", f"{res.fuel_sulphur_content_percent:.2f}% m/m"), ("Flashpoint (SOLAS >= 60°C)", f"{res.fuel_flashpoint_celsius:.1f} °C"), ("Navigation Zone", res.navigation_zone.value), ("EGCS Scrubber Type", res.scrubber_installed.value), ("Washwater pH / Turbidity", f"pH {res.scrubber_washwater_ph:.1f} | {res.scrubber_turbidity_ntu_increase:.1f} NTU"), ("MARPOL Sample Sealed", "YES" if res.marpol_sample_sealed else "NO"), ("MARPOL Compliance Status", "COMPLIANT" if res.is_compliant else "NON-COMPLIANT")):
        table.add_row(k, v)
    console.print(table)
    console.print(f"[bold yellow]Verdict:[/bold yellow] {res.verdict}")


@pilotwaiver_app.command(name="check")
def check_pilotage_exemption(
    request_ref: str = typer.Option("EX-2026-001", "--ref", help="Exemption request reference"),
    vessel_name: str = typer.Option("MV COASTAL STAR", "--vessel", help="Vessel name"),
    gt: float = typer.Option(1800.0, "--gt", help="Gross tonnage (max 2,000 GT for exemption)"),
    loa: float = typer.Option(85.0, "--loa", help="Length overall meters"),
    draft: float = typer.Option(5.2, "--draft", help="Maximum draft meters"),
    flag_state: str = typer.Option("Vietnam", "--flag", help="Vessel flag state"),
    zone_name: str = typer.Option("Vung Tau - Thi Vai Channel", "--zone", help="Pilotage navigation zone"),
    captain: str = typer.Option("Capt. Nguyen Van Thang", "--captain", help="Vessel Master name"),
    past_transits: int = typer.Option(6, "--transits", help="Number of transits in past 12 months (min 4)"),
    has_infractions: bool = typer.Option(False, "--infractions", help="Safety infractions in past 12 months"),
    cargo_type: str = typer.Option("GENERAL_CARGO_OR_CONTAINER", "--cargo", help="GENERAL_CARGO_OR_CONTAINER, PASSENGER_FERRY, CRUDE_OIL_OR_CHEMICALS, or LPG_LNG_GAS_CARRIER"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON format"),
) -> None:
    """Assess vessel and captain eligibility for compulsory marine pilotage waiver."""
    cargo_enum = VesselCargoRiskType.__members__.get(cargo_type, VesselCargoRiskType.GENERAL_CARGO_OR_CONTAINER)
    res = MaritimePilotageExemptionEngine.evaluate_pilotage_exemption(request_ref=request_ref, vessel_name=vessel_name, gross_tonnage=gt, length_overall_meters=loa, draft_meters=draft, flag_state=flag_state, navigation_zone_name=zone_name, captain_name=captain, captain_past_transits_count_12mo=past_transits, has_safety_infractions_past_12mo=has_infractions, cargo_risk=cargo_enum)
    if json_output:
        data = asdict(res)
        data["cargo_risk"] = res.cargo_risk.value
        typer.echo(json.dumps(data, indent=2))
        return
    table = Table(title=f"Pilotage Exemption Assessment: {vessel_name} ({request_ref})")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")
    for k, v in (("Captain Name", res.captain_name), ("Navigation Zone", res.navigation_zone_name), ("Gross Tonnage (Cap: 2,000 GT)", f"{res.gross_tonnage:,.0f} GT"), ("LOA / Draft", f"{res.length_overall_meters:.1f}m / {res.draft_meters:.1f}m"), ("Transits in 12 Months", str(res.captain_past_transits_count_12mo)), ("Cargo Risk Profile", res.cargo_risk.value), ("Exemption Approved", "YES" if res.exemption_approved else "NO"), ("Mandatory Escort Tugs", str(res.mandatory_escort_tugs_count)), ("Statutory Pilotage Due %", f"{res.statutory_pilotage_due_percent:.0f}%")):
        table.add_row(k, v)
    console.print(table)
    console.print(f"[bold yellow]Verdict:[/bold yellow] {res.verdict}")
