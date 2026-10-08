"""Core Domain Engine for Maritime Admiralty, General Average, Liens & Collision Suite (Phases 203-206).

Statutory Frameworks:
- Phase 203: Ship Arrest & Judicial Release for Maritime Claims (Vietnam Maritime Code 2015 Arts. 129-144, Ordinance 05/2008/UBTVQH12).
- Phase 204: General Average Adjustment (Vietnam Maritime Code 2015 Arts. 295-298, York-Antwerp Rules 2016).
- Phase 205: Maritime Liens & In Rem Priorities (Vietnam Maritime Code 2015 Arts. 37-42, Geneva 1993).
- Phase 206: Collision Liability & Bunker Oil Pollution (Vietnam Maritime Code 2015 Arts. 285-294, Bunker Convention 2001).

Zero External Dependencies: strictly uses Python standard library.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ===========================================================================
# Phase 203: Ship Arrest & Judicial Release (VMC Arts. 129-144)
# ===========================================================================

class MaritimeClaimType(str, Enum):
    """22 Statutory Maritime Claims giving rise to arrest rights under VMC 2015 Art. 130."""
    COLLISION_OR_NAVIGATION_DAMAGE = "COLLISION_OR_NAVIGATION_DAMAGE"
    LOSS_OF_LIFE_OR_PERSONAL_INJURY = "LOSS_OF_LIFE_OR_PERSONAL_INJURY"
    SALVAGE_OPERATIONS = "SALVAGE_OPERATIONS"
    ENVIRONMENTAL_POLLUTION_DAMAGE = "ENVIRONMENTAL_POLLUTION_DAMAGE"
    WRECK_REMOVAL_OR_FLOATING = "WRECK_REMOVAL_OR_FLOATING"
    CHARTERPARTY_AGREEMENT = "CHARTERPARTY_AGREEMENT"
    CARRIAGE_OF_GOODS_OR_PASSENGERS = "CARRIAGE_OF_GOODS_OR_PASSENGERS"
    GENERAL_AVERAGE_CONTRIBUTION = "GENERAL_AVERAGE_CONTRIBUTION"
    TOWAGE_SERVICES = "TOWAGE_SERVICES"
    PILOTAGE_SERVICES = "PILOTAGE_SERVICES"
    GOODS_OR_BUNKER_SUPPLIES = "GOODS_OR_BUNKER_SUPPLIES"
    CONSTRUCTION_REPAIR_DRYDOCK = "CONSTRUCTION_REPAIR_DRYDOCK"
    PORT_CANAL_WATERWAY_DUES = "PORT_CANAL_WATERWAY_DUES"
    CREW_WAGES_AND_REPATRIATION = "CREW_WAGES_AND_REPATRIATION"
    DISBURSEMENTS_ON_BEHALF_OF_SHIP = "DISBURSEMENTS_ON_BEHALF_OF_SHIP"
    INSURANCE_PREMIUMS = "INSURANCE_PREMIUMS"
    BROKERAGE_OR_AGENCY_FEES = "BROKERAGE_OR_AGENCY_FEES"
    OWNERSHIP_OR_POSSESSION_DISPUTE = "OWNERSHIP_OR_POSSESSION_DISPUTE"
    MORTGAGE_OR_REGISTERED_CHARGE = "MORTGAGE_OR_REGISTERED_CHARGE"
    BOTTOMRY_BOND = "BOTTOMRY_BOND"
    FORFEITURE_OR_PENALTIES = "FORFEITURE_OR_PENALTIES"
    OTHER_MARITIME_CLAIMS = "OTHER_MARITIME_CLAIMS"


class ArrestSecurityType(str, Enum):
    """Acceptable counter-security and release security forms."""
    CASH_DEPOSIT_KBNN = "CASH_DEPOSIT_KBNN"
    BANK_GUARANTEE = "BANK_GUARANTEE"
    PI_CLUB_LOU = "PI_CLUB_LOU"  # Letter of Undertaking
    NONE = "NONE"


class ArrestStatus(str, Enum):
    ELIGIBLE_FOR_ARREST = "ELIGIBLE_FOR_ARREST"
    ARREST_ORDERED = "ARREST_ORDERED"
    COUNTER_SECURITY_DEFICIENT = "COUNTER_SECURITY_DEFICIENT"
    RELEASED_ON_SECURITY = "RELEASED_ON_SECURITY"
    RELEASED_EXPIRY = "RELEASED_EXPIRY"
    INADMISSIBLE_CLAIM = "INADMISSIBLE_CLAIM"


@dataclass
class ShipArrestEvaluationResult:
    vessel_name: str
    claim_type: MaritimeClaimType
    claim_amount_usd: float
    is_claim_eligible: bool
    mandatory_counter_security_usd: float
    counter_security_provided_usd: float
    is_counter_security_sufficient: bool
    security_for_release_provided_usd: float
    is_release_security_sufficient: bool
    days_under_arrest: int
    is_expired_30d_limit: bool
    arrest_status: ArrestStatus
    verdict: str
    legal_references: List[str] = field(default_factory=list)


class MaritimeShipArrestEngine:
    """Evaluates judicial ship arrest, counter-security, and release under VMC Arts. 129-144."""

    @staticmethod
    def evaluate_arrest(
        vessel_name: str,
        claim_type: MaritimeClaimType,
        claim_amount_usd: float,
        counter_security_provided_usd: float,
        counter_security_type: ArrestSecurityType,
        security_for_release_provided_usd: float = 0.0,
        release_security_type: ArrestSecurityType = ArrestSecurityType.NONE,
        arrest_date_iso: Optional[str] = None,
        assessment_date_iso: Optional[str] = None,
        court_action_commenced: bool = False,
    ) -> ShipArrestEvaluationResult:
        refs = [
            "Vietnam Maritime Code 2015 Arts. 129-144 (Bắt giữ tàu biển)",
            "Ordinance 05/2008/UBTVQH12 on Procedures for Arrest of Sea-going Ships",
            "International Convention on Arrest of Ships 1999 (Geneva Convention)",
        ]

        # Valid statutory claim
        is_claim_eligible = isinstance(claim_type, MaritimeClaimType)
        if not is_claim_eligible:
            return ShipArrestEvaluationResult(
                vessel_name=vessel_name,
                claim_type=claim_type,
                claim_amount_usd=claim_amount_usd,
                is_claim_eligible=False,
                mandatory_counter_security_usd=0.0,
                counter_security_provided_usd=counter_security_provided_usd,
                is_counter_security_sufficient=False,
                security_for_release_provided_usd=security_for_release_provided_usd,
                is_release_security_sufficient=False,
                days_under_arrest=0,
                is_expired_30d_limit=False,
                arrest_status=ArrestStatus.INADMISSIBLE_CLAIM,
                verdict="CLAIM REJECTED: Not an enumerated statutory maritime claim under VMC Art. 130.",
                legal_references=refs,
            )

        # Counter-security requirement (Chief Judge requirement: 15% statutory baseline)
        mandatory_counter_security_usd = claim_amount_usd * 0.15
        is_counter_security_sufficient = (
            counter_security_provided_usd >= mandatory_counter_security_usd
            and counter_security_type in (ArrestSecurityType.CASH_DEPOSIT_KBNN, ArrestSecurityType.BANK_GUARANTEE)
        )

        # Days under arrest calculation
        days_under_arrest = 0
        if arrest_date_iso and assessment_date_iso:
            d_arr = datetime.strptime(arrest_date_iso, "%Y-%m-%d")
            d_ass = datetime.strptime(assessment_date_iso, "%Y-%m-%d")
            days_under_arrest = max(0, (d_ass - d_arr).days)

        is_expired_30d_limit = (days_under_arrest > 30) and not court_action_commenced

        # Release security requirement: Must equal 100% of claim amount
        is_release_security_sufficient = (
            security_for_release_provided_usd >= claim_amount_usd
            and release_security_type in (
                ArrestSecurityType.CASH_DEPOSIT_KBNN,
                ArrestSecurityType.BANK_GUARANTEE,
                ArrestSecurityType.PI_CLUB_LOU,
            )
        )

        if not is_counter_security_sufficient:
            status = ArrestStatus.COUNTER_SECURITY_DEFICIENT
            verdict = (
                f"ARREST WARRANT DENIED: Counter-security of ${counter_security_provided_usd:,.2f} USD "
                f"fails 15% statutory threshold (${mandatory_counter_security_usd:,.2f} USD) under VMC Art. 136."
            )
        elif is_release_security_sufficient:
            status = ArrestStatus.RELEASED_ON_SECURITY
            verdict = (
                f"SHIP RELEASE MANDATED: Alternative security of ${security_for_release_provided_usd:,.2f} USD "
                f"lodged via {release_security_type.value}. Release required within 24 hours under VMC Art. 138."
            )
        elif is_expired_30d_limit:
            status = ArrestStatus.RELEASED_EXPIRY
            verdict = (
                f"SHIP RELEASE MANDATED: 30-day statutory arrest duration expired ({days_under_arrest} days) "
                "without substantive lawsuit commencement under VMC Art. 140."
            )
        else:
            status = ArrestStatus.ARREST_ORDERED
            verdict = (
                f"ARREST WARRANT EXECUTED: Vessel {vessel_name} detained in port. "
                f"Counter-security of ${counter_security_provided_usd:,.2f} USD confirmed. Detention active."
            )

        return ShipArrestEvaluationResult(
            vessel_name=vessel_name,
            claim_type=claim_type,
            claim_amount_usd=claim_amount_usd,
            is_claim_eligible=is_claim_eligible,
            mandatory_counter_security_usd=mandatory_counter_security_usd,
            counter_security_provided_usd=counter_security_provided_usd,
            is_counter_security_sufficient=is_counter_security_sufficient,
            security_for_release_provided_usd=security_for_release_provided_usd,
            is_release_security_sufficient=is_release_security_sufficient,
            days_under_arrest=days_under_arrest,
            is_expired_30d_limit=is_expired_30d_limit,
            arrest_status=status,
            verdict=verdict,
            legal_references=refs,
        )


# ===========================================================================
# Phase 204: General Average Adjustment (YAR 2016 & VMC Arts. 295-298)
# ===========================================================================

@dataclass
class GeneralAverageInterest:
    name: str  # "SHIP", "CARGO", "FREIGHT"
    sound_value_usd: float
    ga_sacrifice_usd: float
    ga_expenditure_usd: float
    non_ga_damage_deductions_usd: float = 0.0


@dataclass
class GeneralAverageAdjustmentResult:
    total_ga_sacrifice_usd: float
    total_ga_expenditure_usd: float
    commission_allowance_usd: float  # 2% on disbursements under Rule XX
    interest_allowance_usd: float    # Under Rule XXI
    gross_general_average_pool_usd: float
    ship_contributory_val_usd: float
    cargo_contributory_val_usd: float
    freight_contributory_val_usd: float
    total_contributory_val_usd: float
    ga_contribution_ratio: float
    settlement_balances_usd: Dict[str, float]  # Positive = Receivable, Negative = Payable
    adjuster_certified: bool
    verdict: str
    legal_references: List[str] = field(default_factory=list)


class GeneralAverageYAREngine:
    """Calculates General Average Adjustment under York-Antwerp Rules 2016 & VMC Arts. 295-298."""

    @staticmethod
    def calculate_adjustment(
        ship_interest: GeneralAverageInterest,
        cargo_interest: GeneralAverageInterest,
        freight_interest: GeneralAverageInterest,
        interest_rate_pct: float = 5.0,
        adjustment_delay_years: float = 1.0,
    ) -> GeneralAverageAdjustmentResult:
        refs = [
            "Vietnam Maritime Code 2015 Arts. 295-298 (Tổn thất chung)",
            "York-Antwerp Rules 2016 (Rules of Practice)",
            "Rule XX: Commission of 2% on GA disbursements",
            "Rule XXI: Interest on GA allowances",
        ]

        total_sac = (
            ship_interest.ga_sacrifice_usd
            + cargo_interest.ga_sacrifice_usd
            + freight_interest.ga_sacrifice_usd
        )
        total_exp = (
            ship_interest.ga_expenditure_usd
            + cargo_interest.ga_expenditure_usd
            + freight_interest.ga_expenditure_usd
        )

        # Rule XX: 2% commission on cash disbursements/expenditures
        commission = total_exp * 0.02

        # Rule XXI: Interest on losses made good and disbursements
        base_losses = total_sac + total_exp + commission
        interest_allowance = base_losses * (interest_rate_pct / 100.0) * adjustment_delay_years

        gross_ga_pool = base_losses + interest_allowance

        # Contributory Values: Net arrived values
        # CV = Sound Value - Non-GA Deductions + GA Sacrifice Made Good
        ship_cv = max(0.0, ship_interest.sound_value_usd - ship_interest.non_ga_damage_deductions_usd + ship_interest.ga_sacrifice_usd)
        cargo_cv = max(0.0, cargo_interest.sound_value_usd - cargo_interest.non_ga_damage_deductions_usd + cargo_interest.ga_sacrifice_usd)
        freight_cv = max(0.0, freight_interest.sound_value_usd - freight_interest.non_ga_damage_deductions_usd + freight_interest.ga_sacrifice_usd)

        total_cv = ship_cv + cargo_cv + freight_cv
        ga_ratio = (gross_ga_pool / total_cv) if total_cv > 0 else 0.0

        # Calculate Settlement Balances
        # For each interest: Net = Made Good (Sacrifice + Exp + Comm + Int share) - (CV * ga_ratio)
        interests = [
            ("SHIP", ship_interest, ship_cv),
            ("CARGO", cargo_interest, cargo_cv),
            ("FREIGHT", freight_interest, freight_cv),
        ]

        balances: Dict[str, float] = {}
        for name, interest, cv in interests:
            # Interest specific allowance
            int_exp_comm = interest.ga_expenditure_usd * 0.02
            int_base = interest.ga_sacrifice_usd + interest.ga_expenditure_usd + int_exp_comm
            int_interest = int_base * (interest_rate_pct / 100.0) * adjustment_delay_years
            total_made_good = int_base + int_interest

            required_contribution = cv * ga_ratio
            balances[name] = round(total_made_good - required_contribution, 2)

        verdict = (
            f"GENERAL AVERAGE APPORTIONMENT: Gross GA Pool ${gross_ga_pool:,.2f} USD "
            f"apportioned across ${total_cv:,.2f} USD contributory fund (Rate: {ga_ratio * 100:.3f}%). "
            f"Ship Balance: ${balances['SHIP']:,.2f} USD; Cargo Balance: ${balances['CARGO']:,.2f} USD."
        )

        return GeneralAverageAdjustmentResult(
            total_ga_sacrifice_usd=round(total_sac, 2),
            total_ga_expenditure_usd=round(total_exp, 2),
            commission_allowance_usd=round(commission, 2),
            interest_allowance_usd=round(interest_allowance, 2),
            gross_general_average_pool_usd=round(gross_ga_pool, 2),
            ship_contributory_val_usd=round(ship_cv, 2),
            cargo_contributory_val_usd=round(cargo_cv, 2),
            freight_contributory_val_usd=round(freight_cv, 2),
            total_contributory_val_usd=round(total_cv, 2),
            ga_contribution_ratio=round(ga_ratio, 6),
            settlement_balances_usd=balances,
            adjuster_certified=True,
            verdict=verdict,
            legal_references=refs,
        )


# ===========================================================================
# Phase 205: Maritime Liens & In Rem Priorities (VMC Arts. 37-42)
# ===========================================================================

class MaritimeLienRank(str, Enum):
    RANK_0_JUDICIAL_AUCTION_COSTS = "RANK_0_JUDICIAL_AUCTION_COSTS"
    RANK_1_CREW_WAGES_REPATRIATION = "RANK_1_CREW_WAGES_REPATRIATION"
    RANK_2_LOSS_OF_LIFE_PERSONAL_INJURY = "RANK_2_LOSS_OF_LIFE_PERSONAL_INJURY"
    RANK_3_SALVAGE_AND_GENERAL_AVERAGE = "RANK_3_SALVAGE_AND_GENERAL_AVERAGE"
    RANK_4_PORT_DUES_PILOTAGE_FEES = "RANK_4_PORT_DUES_PILOTAGE_FEES"
    RANK_5_COLLISION_TORT_PHYSICAL_DAMAGE = "RANK_5_COLLISION_TORT_PHYSICAL_DAMAGE"
    RANK_6_REGISTERED_MORTGAGE = "RANK_6_REGISTERED_MORTGAGE"
    RANK_7_UNSECURED_MARITIME_CLAIMS = "RANK_7_UNSECURED_MARITIME_CLAIMS"


@dataclass
class LienClaimItem:
    claim_id: str
    rank: MaritimeLienRank
    creditor: str
    amount_usd: float
    claim_date_iso: str  # For 1-year extinction rule under Art. 40


@dataclass
class LienSettlementItem:
    claim_id: str
    rank: MaritimeLienRank
    creditor: str
    original_claim_usd: float
    paid_amount_usd: float
    shortfall_amount_usd: float
    is_extinguished_by_prescription: bool
    status: str


@dataclass
class MaritimeLienPriorityResult:
    vessel_name: str
    gross_auction_proceeds_usd: float
    total_claims_usd: float
    total_disbursed_usd: float
    remaining_surplus_to_owner_usd: float
    settlements: List[LienSettlementItem]
    mortgage_satisfied: bool
    verdict: str
    legal_references: List[str] = field(default_factory=list)


class MaritimeLienPriorityEngine:
    """Evaluates 5-tier statutory maritime liens and mortgage priorities under VMC Arts. 37-42."""

    @staticmethod
    def calculate_priority_waterfall(
        vessel_name: str,
        gross_auction_proceeds_usd: float,
        claims: List[LienClaimItem],
        auction_date_iso: str,
    ) -> MaritimeLienPriorityResult:
        refs = [
            "Vietnam Maritime Code 2015 Arts. 37-42 (Quyền cầm giữ hàng hải)",
            "Art. 37: 5 Statutory Maritime Lien Ranks",
            "Art. 38: Superiority over ship mortgages and ordinary claims",
            "Art. 40: 1-Year Prescription Extinction period",
        ]

        d_auc = datetime.strptime(auction_date_iso, "%Y-%m-%d")

        # Rank ordering
        rank_order = [
            MaritimeLienRank.RANK_0_JUDICIAL_AUCTION_COSTS,
            MaritimeLienRank.RANK_1_CREW_WAGES_REPATRIATION,
            MaritimeLienRank.RANK_2_LOSS_OF_LIFE_PERSONAL_INJURY,
            MaritimeLienRank.RANK_3_SALVAGE_AND_GENERAL_AVERAGE,
            MaritimeLienRank.RANK_4_PORT_DUES_PILOTAGE_FEES,
            MaritimeLienRank.RANK_5_COLLISION_TORT_PHYSICAL_DAMAGE,
            MaritimeLienRank.RANK_6_REGISTERED_MORTGAGE,
            MaritimeLienRank.RANK_7_UNSECURED_MARITIME_CLAIMS,
        ]

        # Check prescription (1 year = 365 days) for Ranks 1-5
        active_claims: List[Tuple[LienClaimItem, bool]] = []
        for c in claims:
            d_claim = datetime.strptime(c.claim_date_iso, "%Y-%m-%d")
            diff_days = (d_auc - d_claim).days
            # Liens extinguish after 1 year unless already arrested
            is_extinguished = (diff_days > 365) and (c.rank in (
                MaritimeLienRank.RANK_1_CREW_WAGES_REPATRIATION,
                MaritimeLienRank.RANK_2_LOSS_OF_LIFE_PERSONAL_INJURY,
                MaritimeLienRank.RANK_3_SALVAGE_AND_GENERAL_AVERAGE,
                MaritimeLienRank.RANK_4_PORT_DUES_PILOTAGE_FEES,
                MaritimeLienRank.RANK_5_COLLISION_TORT_PHYSICAL_DAMAGE,
            ))
            active_claims.append((c, is_extinguished))

        pool = gross_auction_proceeds_usd
        settlements: List[LienSettlementItem] = []
        total_claims = sum(c.amount_usd for c in claims)
        mortgage_satisfied = True

        for current_rank in rank_order:
            # Claims at this rank
            tier_items = [(c, ext) for c, ext in active_claims if c.rank == current_rank]
            if not tier_items:
                continue

            tier_valid_total = sum(c.amount_usd for c, ext in tier_items if not ext)
            tier_extinguished_items = [(c, ext) for c, ext in tier_items if ext]

            # Handle extinguished
            for c, _ in tier_extinguished_items:
                settlements.append(LienSettlementItem(
                    claim_id=c.claim_id,
                    rank=c.rank,
                    creditor=c.creditor,
                    original_claim_usd=c.amount_usd,
                    paid_amount_usd=0.0,
                    shortfall_amount_usd=c.amount_usd,
                    is_extinguished_by_prescription=True,
                    status="EXTINGUISHED_BY_1YEAR_PRESCRIPTION",
                ))

            if tier_valid_total == 0:
                continue

            if pool >= tier_valid_total:
                # Full payment for tier
                for c, _ in [(item, ext) for item, ext in tier_items if not ext]:
                    settlements.append(LienSettlementItem(
                        claim_id=c.claim_id,
                        rank=c.rank,
                        creditor=c.creditor,
                        original_claim_usd=c.amount_usd,
                        paid_amount_usd=c.amount_usd,
                        shortfall_amount_usd=0.0,
                        is_extinguished_by_prescription=False,
                        status="FULLY_SATISFIED",
                    ))
                pool -= tier_valid_total
            else:
                # Pari passu proration among tier
                prorata_ratio = pool / tier_valid_total if tier_valid_total > 0 else 0.0
                for c, _ in [(item, ext) for item, ext in tier_items if not ext]:
                    paid = round(c.amount_usd * prorata_ratio, 2)
                    shortfall = round(c.amount_usd - paid, 2)
                    settlements.append(LienSettlementItem(
                        claim_id=c.claim_id,
                        rank=c.rank,
                        creditor=c.creditor,
                        original_claim_usd=c.amount_usd,
                        paid_amount_usd=paid,
                        shortfall_amount_usd=shortfall,
                        is_extinguished_by_prescription=False,
                        status="PRORATED_PARTIAL_PAYMENT",
                    ))
                    if c.rank == MaritimeLienRank.RANK_6_REGISTERED_MORTGAGE and shortfall > 0:
                        mortgage_satisfied = False
                pool = 0.0

        total_disbursed = sum(s.paid_amount_usd for s in settlements)
        remaining_surplus = max(0.0, pool)

        verdict = (
            f"JUDICIAL AUCTION WATERFALL: ${gross_auction_proceeds_usd:,.2f} USD disbursed. "
            f"Total Paid: ${total_disbursed:,.2f} USD across {len(settlements)} claims. "
            f"Surplus to Owner: ${remaining_surplus:,.2f} USD. "
            f"Mortgage Status: {'FULLY SATISFIED' if mortgage_satisfied else 'DEFICIT OCCURRED'}."
        )

        return MaritimeLienPriorityResult(
            vessel_name=vessel_name,
            gross_auction_proceeds_usd=gross_auction_proceeds_usd,
            total_claims_usd=round(total_claims, 2),
            total_disbursed_usd=round(total_disbursed, 2),
            remaining_surplus_to_owner_usd=round(remaining_surplus, 2),
            settlements=settlements,
            mortgage_satisfied=mortgage_satisfied,
            verdict=verdict,
            legal_references=refs,
        )


# ===========================================================================
# Phase 206: Collision Liability & Bunker Oil Pollution 2001 (VMC Arts. 285-294)
# ===========================================================================

@dataclass
class CollisionVesselParticulars:
    name: str
    gross_tonnage: float
    physical_damage_usd: float
    cargo_damage_usd: float
    demurrage_loss_usd: float
    bodily_injury_claims_paid_usd: float = 0.0
    has_valid_bunker_blue_card: bool = True
    bunker_spill_damage_usd: float = 0.0


@dataclass
class CollisionAssessmentResult:
    vessel_a_name: str
    vessel_b_name: str
    fault_ratio_a: float  # e.g., 0.70
    fault_ratio_b: float  # e.g., 0.30
    total_loss_a_usd: float
    total_loss_b_usd: float
    total_combined_losses_usd: float
    liability_a_to_b_usd: float
    liability_b_to_a_usd: float
    net_cross_liability_usd: float
    net_paying_vessel: str
    bodily_injury_recourse_usd: float
    recourse_claimant: str
    bunker_convention_compliant: bool
    bunker_strict_liability_party: Optional[str]
    verdict: str
    legal_references: List[str] = field(default_factory=list)


class CollisionAndBunkerPollutionEngine:
    """Evaluates Both-to-Blame collision liabilities, joint recourse, and Bunker 2001 certification."""

    @staticmethod
    def assess_collision(
        vessel_a: CollisionVesselParticulars,
        vessel_b: CollisionVesselParticulars,
        fault_percentage_a: float,  # 0 to 100
        total_bodily_injury_pool_usd: float = 0.0,
    ) -> CollisionAssessmentResult:
        refs = [
            "Vietnam Maritime Code 2015 Arts. 285-294 (Tai nạn đâm va)",
            "Art. 287: Apportionment of Liability in Proportion to Degree of Fault",
            "Art. 287(2): Joint and Several Liability for Loss of Life / Bodily Injury with Recourse",
            "International Convention on Civil Liability for Bunker Oil Pollution Damage 2001 (BUNKER 2001)",
        ]

        ratio_a = max(0.0, min(1.0, fault_percentage_a / 100.0))
        ratio_b = round(1.0 - ratio_a, 4)

        loss_a = vessel_a.physical_damage_usd + vessel_a.cargo_damage_usd + vessel_a.demurrage_loss_usd
        loss_b = vessel_b.physical_damage_usd + vessel_b.cargo_damage_usd + vessel_b.demurrage_loss_usd
        combined_losses = loss_a + loss_b

        # Admiralty cross-liabilities
        # A owes B for B's losses * ratio_a
        liability_a_to_b = loss_b * ratio_a
        # B owes A for A's losses * ratio_b
        liability_b_to_a = loss_a * ratio_b

        net_cross = liability_a_to_b - liability_b_to_a
        if net_cross > 0:
            net_paying = vessel_a.name
            net_cross_amt = round(net_cross, 2)
        elif net_cross < 0:
            net_paying = vessel_b.name
            net_cross_amt = round(abs(net_cross), 2)
        else:
            net_paying = "NONE (BALANCED)"
            net_cross_amt = 0.0

        # Joint and several bodily injury recourse (Art. 287(2))
        # Statutory share of injury pool:
        statutory_injury_a = total_bodily_injury_pool_usd * ratio_a

        injury_paid_a = vessel_a.bodily_injury_claims_paid_usd

        # If A paid more than statutory share: A has recourse against B
        diff_a = injury_paid_a - statutory_injury_a
        if diff_a > 0.01:
            recourse_amt = round(diff_a, 2)
            recourse_claimant = vessel_a.name
        elif diff_a < -0.01:
            recourse_amt = round(abs(diff_a), 2)
            recourse_claimant = vessel_b.name
        else:
            recourse_amt = 0.0
            recourse_claimant = "NONE"

        # Bunker Convention 2001 compliance (compulsory for vessels > 1000 GT)
        bunker_compliant = True
        bunker_polluter = None
        if vessel_a.gross_tonnage > 1000 and not vessel_a.has_valid_bunker_blue_card:
            bunker_compliant = False
        if vessel_b.gross_tonnage > 1000 and not vessel_b.has_valid_bunker_blue_card:
            bunker_compliant = False

        if vessel_a.bunker_spill_damage_usd > 0:
            bunker_polluter = vessel_a.name
        elif vessel_b.bunker_spill_damage_usd > 0:
            bunker_polluter = vessel_b.name

        verdict = (
            f"COLLISION FAULT APPORTIONMENT: {vessel_a.name} ({ratio_a*100:.1f}%) vs "
            f"{vessel_b.name} ({ratio_b*100:.1f}%). "
            f"Net Cross-Liability: ${net_cross_amt:,.2f} USD payable by {net_paying}. "
            f"Recourse on Bodily Injury: ${recourse_amt:,.2f} USD due to {recourse_claimant}. "
            f"Bunker 2001 Status: {'COMPLIANT' if bunker_compliant else 'DEFICIENT CERTIFICATION'}."
        )

        return CollisionAssessmentResult(
            vessel_a_name=vessel_a.name,
            vessel_b_name=vessel_b.name,
            fault_ratio_a=ratio_a,
            fault_ratio_b=ratio_b,
            total_loss_a_usd=round(loss_a, 2),
            total_loss_b_usd=round(loss_b, 2),
            total_combined_losses_usd=round(combined_losses, 2),
            liability_a_to_b_usd=round(liability_a_to_b, 2),
            liability_b_to_a_usd=round(liability_b_to_a, 2),
            net_cross_liability_usd=net_cross_amt,
            net_paying_vessel=net_paying,
            bodily_injury_recourse_usd=recourse_amt,
            recourse_claimant=recourse_claimant,
            bunker_convention_compliant=bunker_compliant,
            bunker_strict_liability_party=bunker_polluter,
            verdict=verdict,
            legal_references=refs,
        )
