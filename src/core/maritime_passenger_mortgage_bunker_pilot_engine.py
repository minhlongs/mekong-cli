"""Maritime Suite (Phases 215-218) Core Engine.

AST Zero-External-Dependency Invariant:
This module relies EXCLUSIVELY on Python Standard Library modules
(dataclasses, datetime, enum, math, typing, json, hashlib, re).

Statutory Frameworks:
- Phase 215: Maritime Passenger Transport & Athens Convention 2002 Liability
  (Vietnam Maritime Code 2015 Arts. 196-213, Athens Convention 2002 Protocol)
- Phase 216: Ship Mortgage Foreclosure & Judicial Sale Auction Waterfall
  (Vietnam Maritime Code 2015 Arts. 37-42, Decree 171/2016/ND-CP, Law on Property Auction 2016)
- Phase 217: Marine Bunkering & MARPOL Annex VI Low-Sulphur Fuel Oil (LSFO) / Scrubber Compliance
  (MARPOL 73/78 Annex VI Reg. 14 & 18, Circular 40/2020/TT-BGTVT, Res. MEPC.340(77))
- Phase 218: Maritime Pilotage Exemption & Safety Navigational Zone
  (Vietnam Maritime Code 2015 Arts. 246-259, Circular 50/2020/TT-BGTVT, Circular 39/2023/TT-BGTVT)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# ===========================================================================
# 1. Phase 215: Maritime Passenger Transport & Athens Convention 2002
# ===========================================================================

class PassengerIncidentCategory(str, Enum):
    """Classification of maritime passenger incidents under Athens 2002 & VMC 2015."""
    SHIPPING_INCIDENT = "SHIPPING_INCIDENT"  # Shipwreck, capsizing, collision, stranding, explosion, fire
    NON_SHIPPING_INCIDENT = "NON_SHIPPING_INCIDENT"  # Slip and fall, onboard medical, personal assault, etc.


class LuggageCategory(str, Enum):
    """Luggage categories with distinct liability caps under Athens 2002 Art. 8."""
    CABIN_LUGGAGE = "CABIN_LUGGAGE"  # In cabin or passenger possession (2,250 SDR limit)
    VEHICLE_AND_CARRIED = "VEHICLE_AND_CARRIED"  # Vehicles including luggage inside/on vehicle (12,700 SDR limit)
    OTHER_LUGGAGE = "OTHER_LUGGAGE"  # Checked luggage in hold (3,375 SDR limit)


@dataclass
class PassengerClaimItem:
    """Individual passenger injury, death, or property loss claim."""
    passenger_id: str
    passenger_name: str
    death_or_personal_injury: bool
    claimed_injury_amount_usd: float = 0.0
    luggage_category: Optional[LuggageCategory] = None
    claimed_luggage_amount_usd: float = 0.0
    contributory_negligence_percentage: float = 0.0  # Passenger fault reduction (0 - 100%)
    notice_of_luggage_damage_days: int = 0  # Days elapsed before notice of luggage loss


@dataclass
class PassengerLiabilityAssessmentResult:
    """Assessment of passenger carrier liability, statutory caps, and compulsory insurance."""
    case_ref: str
    vessel_name: str
    licensed_passenger_capacity: int
    incident_category: PassengerIncidentCategory
    sdr_usd_exchange_rate: float
    total_claims_count: int
    total_claimed_usd: float
    carrier_strict_liability_limit_per_pax_usd: float
    carrier_fault_liability_limit_per_pax_usd: float
    cabin_luggage_limit_per_pax_usd: float
    vehicle_luggage_limit_per_vehicle_usd: float
    other_luggage_limit_per_pax_usd: float
    gross_carrier_payable_usd: float
    contributory_negligence_deductions_usd: float
    net_carrier_liability_usd: float
    compulsory_financial_security_required: bool
    compulsory_security_minimum_usd: float
    carrier_exonerated: bool
    timebar_prescribed: bool
    verdict: str
    statutory_citations: List[str] = field(default_factory=list)


class MaritimePassengerCarrierLiabilityEngine:
    """Evaluates passenger carrier liability under VMC 2015 Arts. 196-213 & Athens 2002."""

    # Athens Convention 2002 Statutory SDR limits
    STRICT_LIABILITY_INJURY_CAP_SDR = 250_000.0  # Per passenger (Tier 1 strict liability)
    FAULT_LIABILITY_INJURY_CAP_SDR = 400_000.0   # Per passenger (Tier 2 fault ceiling)
    CABIN_LUGGAGE_CAP_SDR = 2_250.0             # Per passenger
    VEHICLE_LUGGAGE_CAP_SDR = 12_700.0          # Per vehicle
    OTHER_LUGGAGE_CAP_SDR = 3_375.0             # Per passenger

    DEFAULT_SDR_USD_RATE = 1.33                 # Baseline 1 SDR = 1.33 USD

    @classmethod
    def evaluate_passenger_claims(
        cls,
        case_ref: str,
        vessel_name: str,
        licensed_passenger_capacity: int,
        incident_category: PassengerIncidentCategory,
        claims: List[PassengerClaimItem],
        sdr_usd_rate: float = DEFAULT_SDR_USD_RATE,
        carrier_proven_faultless_above_strict: bool = False,
        war_or_natural_catastrophe_defense: bool = False,
        days_since_disembarkation: int = 30,
    ) -> PassengerLiabilityAssessmentResult:
        """Calculate carrier liability limits, deductions, and compulsory insurance compliance."""
        citations = [
            "Vietnam Maritime Code 2015 Arts. 196-213",
            "Athens Convention 2002 Protocol (Carriage of Passengers and their Luggage by Sea)",
            "Circular 22/2017/TT-BGTVT (Passenger vessel mandatory financial security)",
        ]

        # Statutory timebar under VMC 2015 Art. 212 is 2 years (730 days)
        timebar_prescribed = days_since_disembarkation > 730

        strict_cap_usd = cls.STRICT_LIABILITY_INJURY_CAP_SDR * sdr_usd_rate
        fault_cap_usd = cls.FAULT_LIABILITY_INJURY_CAP_SDR * sdr_usd_rate
        cabin_cap_usd = cls.CABIN_LUGGAGE_CAP_SDR * sdr_usd_rate
        vehicle_cap_usd = cls.VEHICLE_LUGGAGE_CAP_SDR * sdr_usd_rate
        other_cap_usd = cls.OTHER_LUGGAGE_CAP_SDR * sdr_usd_rate

        # Compulsory financial security is mandatory for vessels licensed > 12 passengers
        compulsory_security_required = licensed_passenger_capacity > 12
        compulsory_security_min_usd = (
            licensed_passenger_capacity * strict_cap_usd if compulsory_security_required else 0.0
        )

        # Carrier exoneration defense under Athens Art. 3(1) (act of war, civil strife, natural catastrophe)
        if war_or_natural_catastrophe_defense and incident_category == PassengerIncidentCategory.SHIPPING_INCIDENT:
            carrier_exonerated = True
        else:
            carrier_exonerated = False

        total_claimed_usd = 0.0
        gross_payable_usd = 0.0
        total_contributory_deductions = 0.0

        if not timebar_prescribed and not carrier_exonerated:
            for item in claims:
                pax_claimed = item.claimed_injury_amount_usd + item.claimed_luggage_amount_usd
                total_claimed_usd += pax_claimed

                # Personal injury / death assessment
                injury_payable = 0.0
                if item.death_or_personal_injury and item.claimed_injury_amount_usd > 0:
                    if incident_category == PassengerIncidentCategory.SHIPPING_INCIDENT:
                        # Tier 1 strict liability up to 250k SDR
                        tier1 = min(item.claimed_injury_amount_usd, strict_cap_usd)
                        # Tier 2 up to 400k SDR unless carrier proves no fault
                        if item.claimed_injury_amount_usd > strict_cap_usd:
                            if not carrier_proven_faultless_above_strict:
                                tier2 = min(item.claimed_injury_amount_usd - strict_cap_usd, fault_cap_usd - strict_cap_usd)
                            else:
                                tier2 = 0.0
                        else:
                            tier2 = 0.0
                        injury_payable = tier1 + tier2
                    else:
                        # Non-shipping incident: fault-based, up to 400k SDR
                        if not carrier_proven_faultless_above_strict:
                            injury_payable = min(item.claimed_injury_amount_usd, fault_cap_usd)
                        else:
                            injury_payable = 0.0

                # Luggage assessment
                luggage_payable = 0.0
                if item.luggage_category and item.claimed_luggage_amount_usd > 0:
                    # Notice of damage timebar (VMC Art. 210: cabin immediate/disembarkation, other 15 days)
                    luggage_timebarred = False
                    if item.luggage_category == LuggageCategory.CABIN_LUGGAGE and item.notice_of_luggage_damage_days > 1:
                        luggage_timebarred = True
                    elif item.notice_of_luggage_damage_days > 15:
                        luggage_timebarred = True

                    if not luggage_timebarred:
                        if item.luggage_category == LuggageCategory.CABIN_LUGGAGE:
                            luggage_payable = min(item.claimed_luggage_amount_usd, cabin_cap_usd)
                        elif item.luggage_category == LuggageCategory.VEHICLE_AND_CARRIED:
                            luggage_payable = min(item.claimed_luggage_amount_usd, vehicle_cap_usd)
                        else:
                            luggage_payable = min(item.claimed_luggage_amount_usd, other_cap_usd)

                pax_gross = injury_payable + luggage_payable
                gross_payable_usd += pax_gross

                # Contributory negligence deduction (Athens Art. 6 & VMC Art. 206)
                negligence_pct = max(0.0, min(100.0, item.contributory_negligence_percentage))
                deduction = pax_gross * (negligence_pct / 100.0)
                total_contributory_deductions += deduction
        else:
            total_claimed_usd = sum(c.claimed_injury_amount_usd + c.claimed_luggage_amount_usd for c in claims)

        net_carrier_liability_usd = max(0.0, gross_payable_usd - total_contributory_deductions)

        # Verdict assembly
        if timebar_prescribed:
            verdict = "CLAIMS_TIMEBARRED: Action is barred by 2-year statutory limitation period under VMC Art. 212."
        elif carrier_exonerated:
            verdict = "CARRIER_EXONERATED: Incident caused solely by force majeure / war hostilities under Athens Art. 3."
        else:
            verdict = (
                f"LIABILITY_ESTABLISHED: Net carrier payable ${net_carrier_liability_usd:,.2f} USD "
                f"across {len(claims)} passengers under Athens 2002 statutory caps."
            )

        return PassengerLiabilityAssessmentResult(
            case_ref=case_ref,
            vessel_name=vessel_name,
            licensed_passenger_capacity=licensed_passenger_capacity,
            incident_category=incident_category,
            sdr_usd_exchange_rate=sdr_usd_rate,
            total_claims_count=len(claims),
            total_claimed_usd=round(total_claimed_usd, 2),
            carrier_strict_liability_limit_per_pax_usd=round(strict_cap_usd, 2),
            carrier_fault_liability_limit_per_pax_usd=round(fault_cap_usd, 2),
            cabin_luggage_limit_per_pax_usd=round(cabin_cap_usd, 2),
            vehicle_luggage_limit_per_vehicle_usd=round(vehicle_cap_usd, 2),
            other_luggage_limit_per_pax_usd=round(other_cap_usd, 2),
            gross_carrier_payable_usd=round(gross_payable_usd, 2),
            contributory_negligence_deductions_usd=round(total_contributory_deductions, 2),
            net_carrier_liability_usd=round(net_carrier_liability_usd, 2),
            compulsory_financial_security_required=compulsory_security_required,
            compulsory_security_minimum_usd=round(compulsory_security_min_usd, 2),
            carrier_exonerated=carrier_exonerated,
            timebar_prescribed=timebar_prescribed,
            verdict=verdict,
            statutory_citations=citations,
        )


# ===========================================================================
# 2. Phase 216: Ship Mortgage Foreclosure & Judicial Sale Auction
# ===========================================================================

class MortgagePriorityTier(str, Enum):
    """Statutory distribution tiers for ship foreclosure proceeds under VMC Arts. 37-42."""
    TIER_0_COURT_AND_AUCTION_COSTS = "TIER_0_COURT_AND_AUCTION_COSTS"
    TIER_1_MARITIME_LIENS = "TIER_1_MARITIME_LIENS"
    TIER_2_POSSESSORY_REPAIRER_LIEN = "TIER_2_POSSESSORY_REPAIRER_LIEN"
    TIER_3_REGISTERED_MORTGAGES = "TIER_3_REGISTERED_MORTGAGES"
    TIER_4_UNSECURED_CREDITORS = "TIER_4_UNSECURED_CREDITORS"


@dataclass
class ForeclosureClaimEntry:
    """Individual creditor claim against ship foreclosure proceeds."""
    creditor_name: str
    tier: MortgagePriorityTier
    claim_amount_usd: float
    mortgage_registration_order: int = 0  # 1 for first-ranking, 2 for second, etc.
    lien_age_days: int = 0  # To evaluate 1-year maritime lien expiration under VMC Art. 40


@dataclass
class ForeclosurePayoutDistribution:
    """Allocated payout per creditor."""
    creditor_name: str
    tier: MortgagePriorityTier
    claimed_usd: float
    payout_usd: float
    deficiency_usd: float
    satisfaction_rate_percent: float


@dataclass
class JudicialAuctionSummary:
    """Outcome of judicial auction and proceeds distribution waterfall."""
    auction_case_ref: str
    vessel_name: str
    reserve_price_usd: float
    actual_winning_bid_usd: float
    auction_deposit_required_usd: float
    auction_successful: bool
    total_claims_admitted_usd: float
    total_proceeds_distributed_usd: float
    residual_surplus_to_owner_usd: float
    distributions: List[ForeclosurePayoutDistribution]
    title_purged_of_encumbrances: bool
    verdict: str
    statutory_citations: List[str] = field(default_factory=list)


class ShipMortgageForeclosureAuctionEngine:
    """Executes statutory priority waterfall under VMC 2015 Arts. 37-42 and Law on Property Auction 2016."""

    STANDARD_AUCTION_DEPOSIT_PERCENT = 10.0  # 10% statutory deposit baseline (range 5-20%)

    @classmethod
    def execute_foreclosure_distribution(
        cls,
        auction_case_ref: str,
        vessel_name: str,
        reserve_price_usd: float,
        actual_winning_bid_usd: float,
        claims: List[ForeclosureClaimEntry],
        deposit_percent: float = STANDARD_AUCTION_DEPOSIT_PERCENT,
        auction_held_successfully: bool = True,
    ) -> JudicialAuctionSummary:
        """Process auction proceeds and allocate to claims in strict order of priority."""
        citations = [
            "Vietnam Maritime Code 2015 Arts. 37-42 (Maritime Liens, Mortgages, and Judicial Sale)",
            "Decree 171/2016/ND-CP (Registration and Mortgages of Ships)",
            "Law on Property Auction 2016 Arts. 39 & 56 (Auction Deposits and Settlement)",
        ]

        deposit_usd = reserve_price_usd * (deposit_percent / 100.0)

        if not auction_held_successfully or actual_winning_bid_usd < reserve_price_usd:
            return JudicialAuctionSummary(
                auction_case_ref=auction_case_ref,
                vessel_name=vessel_name,
                reserve_price_usd=round(reserve_price_usd, 2),
                actual_winning_bid_usd=round(actual_winning_bid_usd, 2),
                auction_deposit_required_usd=round(deposit_usd, 2),
                auction_successful=False,
                total_claims_admitted_usd=0.0,
                total_proceeds_distributed_usd=0.0,
                residual_surplus_to_owner_usd=0.0,
                distributions=[],
                title_purged_of_encumbrances=False,
                verdict="AUCTION_FAILED: Winning bid did not meet reserve price or auction aborted.",
                statutory_citations=citations,
            )

        # Filter and organize claims
        valid_claims: List[ForeclosureClaimEntry] = []
        for c in claims:
            # Maritime liens expire after 1 year (365 days) from inception under VMC Art. 40
            if c.tier == MortgagePriorityTier.TIER_1_MARITIME_LIENS and c.lien_age_days > 365:
                # Expired maritime lien drops to unsecured creditor
                valid_claims.append(
                    ForeclosureClaimEntry(
                        creditor_name=f"{c.creditor_name} (Lien Extinguished -> Unsecured)",
                        tier=MortgagePriorityTier.TIER_4_UNSECURED_CREDITORS,
                        claim_amount_usd=c.claim_amount_usd,
                        mortgage_registration_order=0,
                        lien_age_days=c.lien_age_days,
                    )
                )
            else:
                valid_claims.append(c)

        # Distribute waterfall
        remaining_proceeds = actual_winning_bid_usd
        distributions: List[ForeclosurePayoutDistribution] = []

        # Sequential tier settlement
        tier_sequence = [
            MortgagePriorityTier.TIER_0_COURT_AND_AUCTION_COSTS,
            MortgagePriorityTier.TIER_1_MARITIME_LIENS,
            MortgagePriorityTier.TIER_2_POSSESSORY_REPAIRER_LIEN,
            MortgagePriorityTier.TIER_3_REGISTERED_MORTGAGES,
            MortgagePriorityTier.TIER_4_UNSECURED_CREDITORS,
        ]

        for current_tier in tier_sequence:
            tier_claims = [c for c in valid_claims if c.tier == current_tier]
            if not tier_claims:
                continue

            if current_tier == MortgagePriorityTier.TIER_3_REGISTERED_MORTGAGES:
                # Mortgages are satisfied chronologically by registration timestamp/order
                tier_claims.sort(key=lambda x: x.mortgage_registration_order)
                for m_claim in tier_claims:
                    allocated = min(remaining_proceeds, m_claim.claim_amount_usd)
                    deficiency = m_claim.claim_amount_usd - allocated
                    sat_rate = (allocated / m_claim.claim_amount_usd * 100.0) if m_claim.claim_amount_usd > 0 else 100.0
                    remaining_proceeds -= allocated
                    distributions.append(
                        ForeclosurePayoutDistribution(
                            creditor_name=m_claim.creditor_name,
                            tier=m_claim.tier,
                            claimed_usd=round(m_claim.claim_amount_usd, 2),
                            payout_usd=round(allocated, 2),
                            deficiency_usd=round(deficiency, 2),
                            satisfaction_rate_percent=round(sat_rate, 2),
                        )
                    )
            else:
                # Other tiers satisfy pari passu if proceeds are insufficient
                tier_total = sum(c.claim_amount_usd for c in tier_claims)
                if remaining_proceeds >= tier_total:
                    # Fully paid
                    for c in tier_claims:
                        distributions.append(
                            ForeclosurePayoutDistribution(
                                creditor_name=c.creditor_name,
                                tier=c.tier,
                                claimed_usd=round(c.claim_amount_usd, 2),
                                payout_usd=round(c.claim_amount_usd, 2),
                                deficiency_usd=0.0,
                                satisfaction_rate_percent=100.0,
                            )
                        )
                    remaining_proceeds -= tier_total
                else:
                    # Prorated pari passu
                    proration_ratio = (remaining_proceeds / tier_total) if tier_total > 0 else 0.0
                    for c in tier_claims:
                        payout = c.claim_amount_usd * proration_ratio
                        deficiency = c.claim_amount_usd - payout
                        distributions.append(
                            ForeclosurePayoutDistribution(
                                creditor_name=c.creditor_name,
                                tier=c.tier,
                                claimed_usd=round(c.claim_amount_usd, 2),
                                payout_usd=round(payout, 2),
                                deficiency_usd=round(deficiency, 2),
                                satisfaction_rate_percent=round(proration_ratio * 100.0, 2),
                            )
                        )
                    remaining_proceeds = 0.0

        total_distributed = actual_winning_bid_usd - remaining_proceeds
        total_admitted = sum(c.claim_amount_usd for c in valid_claims)

        verdict = (
            f"AUCTION_CLOSED: Proceeds ${actual_winning_bid_usd:,.2f} distributed across "
            f"{len(distributions)} claimants. Purchaser receives unencumbered title under VMC Art. 42."
        )

        return JudicialAuctionSummary(
            auction_case_ref=auction_case_ref,
            vessel_name=vessel_name,
            reserve_price_usd=round(reserve_price_usd, 2),
            actual_winning_bid_usd=round(actual_winning_bid_usd, 2),
            auction_deposit_required_usd=round(deposit_usd, 2),
            auction_successful=True,
            total_claims_admitted_usd=round(total_admitted, 2),
            total_proceeds_distributed_usd=round(total_distributed, 2),
            residual_surplus_to_owner_usd=round(remaining_proceeds, 2),
            distributions=distributions,
            title_purged_of_encumbrances=True,
            verdict=verdict,
            statutory_citations=citations,
        )


# ===========================================================================
# 3. Phase 217: Marine Bunkering & MARPOL Annex VI Low-Sulphur Compliance
# ===========================================================================

class ScrubberType(str, Enum):
    """Exhaust Gas Cleaning System (EGCS) configuration."""
    NONE = "NONE"
    OPEN_LOOP = "OPEN_LOOP"
    CLOSED_LOOP = "CLOSED_LOOP"
    HYBRID = "HYBRID"


class BunkeringNavigationZone(str, Enum):
    """Geographical zones with differing sulphur ceilings."""
    GLOBAL_HIGH_SEAS = "GLOBAL_HIGH_SEAS"  # 0.50% m/m global cap
    EMISSION_CONTROL_AREA_ECA = "EMISSION_CONTROL_AREA_ECA"  # 0.10% m/m ECA cap
    VIETNAMESE_INTERNAL_PORT_WATERS = "VIETNAMESE_INTERNAL_PORT_WATERS"  # Scrubber discharge restrictions


@dataclass
class BunkerBdnComplianceReport:
    """Audit report for bunker delivery note and MARPOL Annex VI compliance."""
    bdn_number: str
    vessel_name: str
    imo_number: str
    bunker_supplier_name: str
    fuel_sulphur_content_percent: float
    fuel_flashpoint_celsius: float
    navigation_zone: BunkeringNavigationZone
    scrubber_installed: ScrubberType
    scrubber_active: bool
    scrubber_washwater_ph: float
    scrubber_turbidity_ntu_increase: float
    bdn_retention_years: float
    marpol_sample_sealed: bool
    fonar_submitted: bool
    is_compliant: bool
    action_required: str
    verdict: str
    statutory_citations: List[str] = field(default_factory=list)


class MarineBunkerFuelMarpolEngine:
    """Validates bunker fuel oil, BDN records, and scrubber emissions under MARPOL Annex VI."""

    GLOBAL_SULPHUR_CAP_PERCENT = 0.50  # MARPOL Annex VI Reg. 14.1
    ECA_SULPHUR_CAP_PERCENT = 0.10     # MARPOL Annex VI Reg. 14.4
    MIN_FLASHPOINT_SOLAS_CELSIUS = 60.0  # SOLAS Ch. II-2 Reg. 4.2.1
    MIN_BDN_RETENTION_YEARS = 3.0       # MARPOL Annex VI Reg. 18.6
    MIN_SCRUBBER_DISCHARGE_PH = 6.5     # Res. MEPC.340(77)
    MAX_SCRUBBER_TURBIDITY_NTU = 25.0   # Res. MEPC.340(77)

    @classmethod
    def audit_bunkering_compliance(
        cls,
        bdn_number: str,
        vessel_name: str,
        imo_number: str,
        bunker_supplier_name: str,
        fuel_sulphur_content_percent: float,
        fuel_flashpoint_celsius: float,
        navigation_zone: BunkeringNavigationZone = BunkeringNavigationZone.GLOBAL_HIGH_SEAS,
        scrubber_installed: ScrubberType = ScrubberType.NONE,
        scrubber_active: bool = False,
        scrubber_washwater_ph: float = 7.0,
        scrubber_turbidity_ntu_increase: float = 10.0,
        bdn_retention_years: float = 3.0,
        marpol_sample_sealed: bool = True,
        fonar_submitted: bool = False,
    ) -> BunkerBdnComplianceReport:
        """Verify fuel sulphur limit, flashpoint safety, and scrubber washwater compliance."""
        citations = [
            "MARPOL 73/78 Annex VI Reg. 14 (Sulphur Oxides & PM) and Reg. 18 (Fuel Oil Quality)",
            "IMO Res. MEPC.340(77) (2021 Guidelines for Exhaust Gas Cleaning Systems)",
            "Circular 40/2020/TT-BGTVT (Maritime Environmental Protection & Fuel Inspection)",
            "SOLAS 1974 Ch. II-2 Reg. 4.2.1 (Minimum Flashpoint Safety Standard)",
        ]

        deficiencies: List[str] = []

        # 1. Flashpoint safety check (SOLAS 60°C min)
        if fuel_flashpoint_celsius < cls.MIN_FLASHPOINT_SOLAS_CELSIUS:
            deficiencies.append(
                f"FLASHPOINT_FIRE_HAZARD: Fuel flashpoint {fuel_flashpoint_celsius}°C is below SOLAS 60.0°C minimum."
            )

        # 2. BDN & Sample integrity check
        if bdn_retention_years < cls.MIN_BDN_RETENTION_YEARS:
            deficiencies.append("BDN_RETENTION_DEFICIENCY: BDN must be preserved onboard for at least 3 years.")
        if not marpol_sample_sealed:
            deficiencies.append("SAMPLE_SEAL_MISSING: MARPOL representative sample was not sealed and signed.")

        # 3. Sulphur ceiling evaluation
        statutory_cap = (
            cls.ECA_SULPHUR_CAP_PERCENT
            if navigation_zone == BunkeringNavigationZone.EMISSION_CONTROL_AREA_ECA
            else cls.GLOBAL_SULPHUR_CAP_PERCENT
        )

        scrubber_equivalent_valid = False
        if scrubber_installed != ScrubberType.NONE and scrubber_active:
            # Check washwater discharge parameters under MEPC.340(77)
            if navigation_zone == BunkeringNavigationZone.VIETNAMESE_INTERNAL_PORT_WATERS:
                if scrubber_installed == ScrubberType.OPEN_LOOP:
                    deficiencies.append(
                        "OPEN_LOOP_PORT_BAN: Open-loop scrubber discharge prohibited in internal port waters."
                    )
                else:
                    # Closed-loop or hybrid in zero-discharge mode is allowed
                    scrubber_equivalent_valid = True
            else:
                # High seas or ECA: check pH and turbidity
                if scrubber_washwater_ph < cls.MIN_SCRUBBER_DISCHARGE_PH:
                    deficiencies.append(
                        f"WASHWATER_ACIDIC: Scrubber discharge pH {scrubber_washwater_ph} < {cls.MIN_SCRUBBER_DISCHARGE_PH} threshold."
                    )
                elif scrubber_turbidity_ntu_increase > cls.MAX_SCRUBBER_TURBIDITY_NTU:
                    deficiencies.append(
                        f"TURBIDITY_EXCESS: Washwater turbidity increase {scrubber_turbidity_ntu_increase} NTU exceeds 25 NTU limit."
                    )
                else:
                    scrubber_equivalent_valid = True

        if fuel_sulphur_content_percent > statutory_cap and not scrubber_equivalent_valid:
            if not fonar_submitted:
                deficiencies.append(
                    f"EXCESS_SULPHUR: Fuel sulphur {fuel_sulphur_content_percent:.2f}% exceeds {statutory_cap:.2f}% cap without valid scrubber or FONAR."
                )

        is_compliant = len(deficiencies) == 0

        if is_compliant:
            action_required = "NONE: All MARPOL Annex VI fuel oil and environmental criteria verified."
            verdict = "COMPLIANT: Bunker Delivery Note and fuel parameters comply fully with statutory limits."
        else:
            action_required = "CORRECTIVE_ACTION: " + "; ".join(deficiencies)
            verdict = (
                f"NON_COMPLIANT: Vessel detected with {len(deficiencies)} MARPOL Annex VI deficiencies. "
                "Subject to PSC detention or bunker debunkering order."
            )

        return BunkerBdnComplianceReport(
            bdn_number=bdn_number,
            vessel_name=vessel_name,
            imo_number=imo_number,
            bunker_supplier_name=bunker_supplier_name,
            fuel_sulphur_content_percent=fuel_sulphur_content_percent,
            fuel_flashpoint_celsius=fuel_flashpoint_celsius,
            navigation_zone=navigation_zone,
            scrubber_installed=scrubber_installed,
            scrubber_active=scrubber_active,
            scrubber_washwater_ph=scrubber_washwater_ph,
            scrubber_turbidity_ntu_increase=scrubber_turbidity_ntu_increase,
            bdn_retention_years=bdn_retention_years,
            marpol_sample_sealed=marpol_sample_sealed,
            fonar_submitted=fonar_submitted,
            is_compliant=is_compliant,
            action_required=action_required,
            verdict=verdict,
            statutory_citations=citations,
        )


# ===========================================================================
# 4. Phase 218: Maritime Pilotage Exemption & Safety Navigational Zone
# ===========================================================================

class VesselCargoRiskType(str, Enum):
    """Cargo hazard classification impacting pilotage exemption eligibility."""
    GENERAL_CARGO_OR_CONTAINER = "GENERAL_CARGO_OR_CONTAINER"
    PASSENGER_FERRY = "PASSENGER_FERRY"
    CRUDE_OIL_OR_CHEMICALS = "CRUDE_OIL_OR_CHEMICALS"  # Exemption strictly barred
    LPG_LNG_GAS_CARRIER = "LPG_LNG_GAS_CARRIER"  # Exemption strictly barred


@dataclass
class PilotageExemptionAssessment:
    """Eligibility report for compulsory pilotage exemption in Vietnamese navigation zones."""
    request_ref: str
    vessel_name: str
    gross_tonnage: float
    length_overall_meters: float
    draft_meters: float
    flag_state: str
    navigation_zone_name: str
    captain_name: str
    captain_past_transits_count_12mo: int
    has_safety_infractions_past_12mo: bool
    cargo_risk: VesselCargoRiskType
    exemption_approved: bool
    disqualification_reasons: List[str]
    mandatory_escort_tugs_count: int
    statutory_pilotage_due_percent: float
    verdict: str
    statutory_citations: List[str] = field(default_factory=list)


class MaritimePilotageExemptionEngine:
    """Assesses compulsory pilotage exemption under VMC Arts. 246-259 & Circular 50/2020/TT-BGTVT."""

    MAX_EXEMPTION_GROSS_TONNAGE = 2_000.0  # Baseline statutory GT ceiling for captain exemption
    MIN_LOCAL_TRANSITS_12MO = 4            # Minimum 4 round trips (or 8 transits) under pilot oversight

    @classmethod
    def evaluate_pilotage_exemption(
        cls,
        request_ref: str,
        vessel_name: str,
        gross_tonnage: float,
        length_overall_meters: float,
        draft_meters: float,
        flag_state: str,
        navigation_zone_name: str,
        captain_name: str,
        captain_past_transits_count_12mo: int,
        has_safety_infractions_past_12mo: bool,
        cargo_risk: VesselCargoRiskType = VesselCargoRiskType.GENERAL_CARGO_OR_CONTAINER,
    ) -> PilotageExemptionAssessment:
        """Determine if captain qualifies for pilotage waiver and calculate escort requirements."""
        citations = [
            "Vietnam Maritime Code 2015 Arts. 246-259 (Marine Pilotage)",
            "Circular 50/2020/TT-BGTVT (Marine Pilotage Zones & Exemption Certificates)",
            "Circular 39/2023/TT-BGTVT (Maritime Safety Dues and Pilotage Tariffs)",
        ]

        disqualifications: List[str] = []

        # 1. Dangerous cargo prohibition
        if cargo_risk in (VesselCargoRiskType.CRUDE_OIL_OR_CHEMICALS, VesselCargoRiskType.LPG_LNG_GAS_CARRIER):
            disqualifications.append(
                f"HAZARDOUS_CARGO: Ships carrying {cargo_risk.value} are prohibited from pilotage exemption."
            )

        # 2. Tonnage ceiling check
        if gross_tonnage > cls.MAX_EXEMPTION_GROSS_TONNAGE:
            disqualifications.append(
                f"TONNAGE_EXCEEDED: Vessel GT {gross_tonnage:,.0f} exceeds maximum exemption limit of {cls.MAX_EXEMPTION_GROSS_TONNAGE:,.0f} GT."
            )

        # 3. Transits experience in the navigation zone
        if captain_past_transits_count_12mo < cls.MIN_LOCAL_TRANSITS_12MO:
            disqualifications.append(
                f"INSUFFICIENT_TRANSITS: Captain has completed {captain_past_transits_count_12mo} transits in past 12mo "
                f"(minimum required: {cls.MIN_LOCAL_TRANSITS_12MO})."
            )

        # 4. Navigational safety history
        if has_safety_infractions_past_12mo:
            disqualifications.append(
                "SAFETY_RECORD_BLEMISHED: Captain or vessel incurred maritime navigational infractions in the past 12 months."
            )

        exemption_approved = len(disqualifications) == 0

        # Mandatory tug escort rules based on vessel dimensions under Circular 50/2020
        if length_overall_meters >= 150.0 or draft_meters >= 9.5:
            mandatory_tugs = 2
        elif length_overall_meters >= 95.0 or draft_meters >= 6.5:
            mandatory_tugs = 1
        else:
            mandatory_tugs = 0

        # Statutory due reduction (exempt vessels still pay 10% administrative safety dues under Circular 39/2023)
        statutory_due_percent = 10.0 if exemption_approved else 100.0

        if exemption_approved:
            verdict = (
                f"EXEMPTION_GRANTED: Captain {captain_name} is certified for solo navigation in {navigation_zone_name}. "
                f"Subject to {statutory_due_percent}% statutory safety monitoring fee."
            )
        else:
            verdict = (
                f"EXEMPTION_DENIED: Compulsory marine pilot required due to: {'; '.join(disqualifications)}."
            )

        return PilotageExemptionAssessment(
            request_ref=request_ref,
            vessel_name=vessel_name,
            gross_tonnage=gross_tonnage,
            length_overall_meters=length_overall_meters,
            draft_meters=draft_meters,
            flag_state=flag_state,
            navigation_zone_name=navigation_zone_name,
            captain_name=captain_name,
            captain_past_transits_count_12mo=captain_past_transits_count_12mo,
            has_safety_infractions_past_12mo=has_safety_infractions_past_12mo,
            cargo_risk=cargo_risk,
            exemption_approved=exemption_approved,
            disqualification_reasons=disqualifications,
            mandatory_escort_tugs_count=mandatory_tugs,
            statutory_pilotage_due_percent=statutory_due_percent,
            verdict=verdict,
            statutory_citations=citations,
        )
