"""Maritime Marine Insurance Subrogation, Casualty Investigation, Ship Saleform & Seafarer Repatriation Engine.

Phases 211-214:
- Phase 211: Marine Insurance Claims, Abandonment & Subrogation Rights (VMC 2015 Arts. 310-336, Insurance Business Law 2022, ITC Hulls 1983).
- Phase 212: Marine Casualties & Investigation Protocols (IMO Casualty Investigation Code Res. MSC.255(84), Circular 01/2020/TT-BGTVT).
- Phase 213: Ship Sale & Purchase (S&P), Escrow & Closing Protocol (BIMCO SALEFORM 2012 / SHIPSALE 22, VMC Arts. 29-36).
- Phase 214: Seafarer Repatriation & MLC 2006 Contingency Security (MLC 2006 Standard A2.5, Circular 22/2017/TT-BGTVT, VMC Arts. 64-66).

AST Zero-External-Dependency: Uses ONLY Python standard library (dataclasses, enum, math, typing, json, hashlib, re).
"""

from dataclasses import dataclass
from enum import Enum
from typing import List


# ===========================================================================
# Phase 211 Enums & Data Structures: Marine Insurance & Subrogation
# ===========================================================================

class MarineLossType(str, Enum):
    ACTUAL_TOTAL_LOSS = "ACTUAL_TOTAL_LOSS"
    CONSTRUCTIVE_TOTAL_LOSS = "CONSTRUCTIVE_TOTAL_LOSS"
    PARTIAL_DAMAGE_AVERAGE = "PARTIAL_DAMAGE_AVERAGE"
    GENERAL_AVERAGE_EXPENDITURE = "GENERAL_AVERAGE_EXPENDITURE"


class AbandonmentStatus(str, Enum):
    VALID_ACCEPTED = "VALID_ACCEPTED"
    VALID_DECLINED_PAYOUT_MAINTAINED = "VALID_DECLINED_PAYOUT_MAINTAINED"
    INVALID_REPAIR_BELOW_THRESHOLD = "INVALID_REPAIR_BELOW_THRESHOLD"
    UNTIMELY_TENDERED = "UNTIMELY_TENDERED"


@dataclass
class MarineInsuranceClaimResult:
    policy_id: str
    vessel_name: str
    insured_value_usd: float
    loss_type: MarineLossType
    estimated_repair_cost_usd: float
    salvage_value_usd: float
    ctl_threshold_ratio: float
    is_constructive_total_loss: bool
    abandonment_status: AbandonmentStatus
    indemnity_payable_usd: float
    deductible_applied_usd: float
    net_claim_payout_usd: float
    subrogation_rights_acquired: bool
    max_subrogation_recovery_usd: float
    insurer_salvage_title_acquired: bool
    statutory_articles: List[str]
    verdict: str


# ===========================================================================
# Phase 212 Enums & Data Structures: Marine Casualty Investigation
# ===========================================================================

class MarineCasualtySeverity(str, Enum):
    VERY_SERIOUS_MARINE_CASUALTY = "VERY_SERIOUS_MARINE_CASUALTY"  # Total loss, death, severe pollution
    SERIOUS_MARINE_CASUALTY = "SERIOUS_MARINE_CASUALTY"            # Fire, collision, grounding, structural immobilization
    LESS_SERIOUS_CASUALTY = "LESS_SERIOUS_CASUALTY"                # Minor contact, short tow
    MARINE_INCIDENT = "MARINE_INCIDENT"                            # Near miss, minor machinery failure


@dataclass
class MarineCasualtyInvestigationReport:
    incident_id: str
    vessel_name: str
    imo_number: str
    flag_state: str
    severity: MarineCasualtySeverity
    total_loss_of_ship: bool
    fatalities_count: int
    severe_pollution_occurred: bool
    structural_damage_severe: bool
    mandatory_safety_investigation_required: bool
    initial_report_deadline_hours: int
    preliminary_report_deadline_days: int
    final_safety_report_deadline_days: int
    vdr_preservation_mandatory: bool
    investigating_authority: str
    investigation_recommendations: List[str]
    statutory_governance: List[str]
    verdict: str


# ===========================================================================
# Phase 213 Enums & Data Structures: Ship Sale & Purchase (Saleform)
# ===========================================================================

class SaleformContractType(str, Enum):
    BIMCO_SALEFORM_2012 = "BIMCO_SALEFORM_2012"
    BIMCO_SHIPSALE_22 = "BIMCO_SHIPSALE_22"
    VIETNAMESE_DOMESTIC_SALE = "VIETNAMESE_DOMESTIC_SALE"


class InspectionOutcome(str, Enum):
    ACCEPTED_WITHOUT_CONDITION = "ACCEPTED_WITHOUT_CONDITION"
    CLASS_CONDITION_DEFECT_NOTED = "CLASS_CONDITION_DEFECT_NOTED"
    REJECTED_UNREPAIRED_DAMAGE = "REJECTED_UNREPAIRED_DAMAGE"


@dataclass
class ShipSaleformFinancialSummary:
    contract_ref: str
    vessel_name: str
    contract_price_usd: float
    deposit_percentage: float
    deposit_amount_usd: float
    escrow_agent_verified: bool
    inspection_outcome: InspectionOutcome
    underwater_defect_repair_deduction_usd: float
    bunkers_and_luboils_value_usd: float
    cancelling_date_breached: bool
    buyer_default_flag: bool
    seller_default_flag: bool
    balance_payable_on_delivery_usd: float
    escrow_deposit_forfeited_usd: float
    seller_liquidated_damages_usd: float
    legal_title_transfer_approved: bool
    closing_documents_verified: List[str]
    statutory_notes: List[str]
    verdict: str


# ===========================================================================
# Phase 214 Enums & Data Structures: Seafarer Repatriation & Contingency
# ===========================================================================

class RepatriationTrigger(str, Enum):
    EMPLOYMENT_CONTRACT_EXPIRY = "EMPLOYMENT_CONTRACT_EXPIRY"
    SHIPOWNER_INSOLVENCY_ABANDONMENT = "SHIPOWNER_INSOLVENCY_ABANDONMENT"
    VESSEL_UNSEAWORTHY_OR_ARRESTED = "VESSEL_UNSEAWORTHY_OR_ARRESTED"
    OCCUPATIONAL_INJURY_ILLNESS = "OCCUPATIONAL_INJURY_ILLNESS"
    WAR_OR_WARLIKE_ZONE_TERMINATION = "WAR_OR_WARLIKE_ZONE_TERMINATION"


@dataclass
class SeafarerRepatriationAssessment:
    case_ref: str
    vessel_name: str
    flag_state: str
    seafarer_count: int
    trigger_event: RepatriationTrigger
    compulsory_financial_security_valid: bool
    security_provider: str
    flight_tickets_total_usd: float
    sustenance_and_accommodation_usd: float
    medical_stabilization_usd: float
    outstanding_wages_covered_usd: float
    total_repatriation_liability_usd: float
    insurer_direct_guarantee_payout_usd: float
    vietnam_consular_contingency_advance_usd: float
    owner_recourse_liability_usd: float
    mlc_standard_compliance: str
    statutory_protections: List[str]
    verdict: str


# ===========================================================================
# 1. Marine Insurance Subrogation & Abandonment Engine (Phase 211)
# ===========================================================================

class MaritimeInsuranceSubrogationEngine:
    """Evaluates Marine Hull & Cargo insurance claims, Constructive Total Loss,

    Notice of Abandonment, and Insurer Subrogation Rights under VMC 2015 Arts. 310-336
    and Luật Kinh doanh bảo hiểm 2022.
    """

    DEFAULT_CTL_THRESHOLD = 0.80  # VMC Art. 320: CTL when repair costs exceed 80% or total insured value

    @staticmethod
    def assess_marine_claim(
        policy_id: str,
        vessel_name: str,
        insured_value_usd: float,
        actual_total_loss: bool,
        estimated_repair_cost_usd: float,
        salvage_value_usd: float = 0.0,
        policy_deductible_usd: float = 0.0,
        notice_of_abandonment_tendered: bool = False,
        abandonment_days_since_casualty: int = 30,
        abandonment_accepted_by_insurer: bool = False,
        ctl_threshold_ratio: float = DEFAULT_CTL_THRESHOLD,
    ) -> MarineInsuranceClaimResult:
        """Calculates claim indemnity, abandonment validity, and subrogation assignment."""
        statutory_articles = [
            "Vietnam Maritime Code 2015 Art. 310-316 (Marine Insurance Contracts)",
            "Vietnam Maritime Code 2015 Art. 320 (Constructive Total Loss & Notice of Abandonment)",
            "Vietnam Maritime Code 2015 Art. 324 (Insurer Subrogation Rights)",
            "Luật Kinh doanh bảo hiểm 2022 Art. 54 (Right of Subrogation / Thế quyền bồi thường)",
        ]

        if insured_value_usd <= 0:
            raise ValueError("Insured value must be strictly positive.")

        repair_ratio = estimated_repair_cost_usd / insured_value_usd
        is_ctl = (repair_ratio >= ctl_threshold_ratio) or (estimated_repair_cost_usd >= insured_value_usd)

        # Determine Loss Type
        if actual_total_loss:
            loss_type = MarineLossType.ACTUAL_TOTAL_LOSS
        elif is_ctl:
            loss_type = MarineLossType.CONSTRUCTIVE_TOTAL_LOSS
        else:
            loss_type = MarineLossType.PARTIAL_DAMAGE_AVERAGE

        # Evaluate Abandonment (VMC Art. 320: Tendered within 180 days from notice of casualty)
        if loss_type == MarineLossType.CONSTRUCTIVE_TOTAL_LOSS:
            if not notice_of_abandonment_tendered:
                abandonment_status = AbandonmentStatus.INVALID_REPAIR_BELOW_THRESHOLD
            elif abandonment_days_since_casualty > 180:
                abandonment_status = AbandonmentStatus.UNTIMELY_TENDERED
            elif abandonment_accepted_by_insurer:
                abandonment_status = AbandonmentStatus.VALID_ACCEPTED
            else:
                # Even if insurer declines abandonment, if CTL is proven, insurer must pay total loss
                abandonment_status = AbandonmentStatus.VALID_DECLINED_PAYOUT_MAINTAINED
        else:
            abandonment_status = AbandonmentStatus.INVALID_REPAIR_BELOW_THRESHOLD

        # Calculate Indemnity
        deductible_applied = min(policy_deductible_usd, insured_value_usd)
        if loss_type in (MarineLossType.ACTUAL_TOTAL_LOSS, MarineLossType.CONSTRUCTIVE_TOTAL_LOSS):
            # Total Loss pays full insured value (ITC Hulls 1983 / VMC Art. 320)
            indemnity_payable = insured_value_usd
            net_payout = max(0.0, indemnity_payable - deductible_applied)
            subrogation_acquired = True
            insurer_salvage_title = (abandonment_status == AbandonmentStatus.VALID_ACCEPTED)
        else:
            # Partial average pays repair cost minus deductible
            indemnity_payable = min(estimated_repair_cost_usd, insured_value_usd)
            net_payout = max(0.0, indemnity_payable - deductible_applied)
            subrogation_acquired = net_payout > 0
            insurer_salvage_title = False

        # Subrogation recovery can NEVER exceed indemnity paid to insured (VMC Art. 324)
        max_subrogation_recovery = net_payout

        verdict_parts = [f"Claim for {vessel_name} classified as {loss_type.value}."]
        if loss_type == MarineLossType.CONSTRUCTIVE_TOTAL_LOSS:
            verdict_parts.append(f"CTL verified ({repair_ratio:.1%} repair cost vs {ctl_threshold_ratio:.0%} threshold).")
            verdict_parts.append(f"Abandonment status: {abandonment_status.value}.")
        verdict_parts.append(f"Net payout: ${net_payout:,.2f} USD.")
        if subrogation_acquired:
            verdict_parts.append(f"Subrogation rights assigned up to ${max_subrogation_recovery:,.2f} USD.")

        return MarineInsuranceClaimResult(
            policy_id=policy_id,
            vessel_name=vessel_name,
            insured_value_usd=round(insured_value_usd, 2),
            loss_type=loss_type,
            estimated_repair_cost_usd=round(estimated_repair_cost_usd, 2),
            salvage_value_usd=round(salvage_value_usd, 2),
            ctl_threshold_ratio=ctl_threshold_ratio,
            is_constructive_total_loss=is_ctl,
            abandonment_status=abandonment_status,
            indemnity_payable_usd=round(indemnity_payable, 2),
            deductible_applied_usd=round(deductible_applied, 2),
            net_claim_payout_usd=round(net_payout, 2),
            subrogation_rights_acquired=subrogation_acquired,
            max_subrogation_recovery_usd=round(max_subrogation_recovery, 2),
            insurer_salvage_title_acquired=insurer_salvage_title,
            statutory_articles=statutory_articles,
            verdict=" ".join(verdict_parts),
        )


# ===========================================================================
# 2. Marine Casualty Investigation Protocols Engine (Phase 212)
# ===========================================================================

class MarineCasualtyInvestigationEngine:
    """Classifies marine casualties and computes investigation statutory timebars

    under IMO Casualty Investigation Code (Res. MSC.255(84)) and Circular 01/2020/TT-BGTVT.
    """

    @staticmethod
    def evaluate_casualty(
        incident_id: str,
        vessel_name: str,
        imo_number: str,
        flag_state: str,
        total_loss_of_ship: bool,
        fatalities_count: int,
        severe_pollution_occurred: bool,
        structural_damage_severe: bool,
        in_vietnam_internal_or_territorial_waters: bool = True,
    ) -> MarineCasualtyInvestigationReport:
        """Categorizes casualty severity and determines statutory inquiry timelines."""
        # Severity Determination under IMO Code Chapter 2 & Circular 01/2020/TT-BGTVT Art. 4
        if total_loss_of_ship or fatalities_count > 0 or severe_pollution_occurred:
            severity = MarineCasualtySeverity.VERY_SERIOUS_MARINE_CASUALTY
            mandatory_investigation = True
            initial_report_hours = 24
            preliminary_days = 30
            final_report_days = 60
            vdr_mandatory = True
        elif structural_damage_severe:
            severity = MarineCasualtySeverity.SERIOUS_MARINE_CASUALTY
            mandatory_investigation = True
            initial_report_hours = 24
            preliminary_days = 30
            final_report_days = 90
            vdr_mandatory = True
        else:
            severity = MarineCasualtySeverity.LESS_SERIOUS_CASUALTY
            mandatory_investigation = False
            initial_report_hours = 48
            preliminary_days = 45
            final_report_days = 120
            vdr_mandatory = False

        if in_vietnam_internal_or_territorial_waters:
            investigating_authority = "Vietnam Maritime Administration (Cục Hàng hải Việt Nam) & Local Port Authority (Cảng vụ Hàng hải)"
        else:
            investigating_authority = f"Lead Flag State ({flag_state}) with Vietnam as Substantially Interested State"

        recommendations = [
            "Impound and preserve Voyage Data Recorder (VDR / S-VDR) data capsule immediately.",
            "Record witness statements of Master, Officer of the Watch, and Duty Engineer.",
            "Inspect engine logbook, chart plotter records, and ECDIS voyage playback.",
        ]
        if severe_pollution_occurred:
            recommendations.append("Coordinate with MONRE and Marine Environment Protection agency for spill response documentation.")
        if fatalities_count > 0:
            recommendations.append("Formal coroner inquiry and notification to Flag State diplomatic mission under IMO Code.")

        statutory_governance = [
            "IMO Res. MSC.255(84) - Code of the International Standards and Recommended Practices for a Safety Investigation into a Marine Casualty",
            "Circular 01/2020/TT-BGTVT (Báo cáo và điều tra tai nạn hàng hải)",
            "Vietnam Maritime Code 2015 Arts. 115-124 (Tai nạn hàng hải và báo cáo)",
        ]

        verdict = (
            f"Casualty {incident_id} ({vessel_name}) classified as {severity.value}. "
            f"Mandatory safety inquiry: {'YES' if mandatory_investigation else 'DISCRETIONARY'}. "
            f"Initial notification due within {initial_report_hours} hours; "
            f"Safety report required within {final_report_days} days. "
            f"VDR preservation: {'MANDATORY' if vdr_mandatory else 'RECOMMENDED'}."
        )

        return MarineCasualtyInvestigationReport(
            incident_id=incident_id,
            vessel_name=vessel_name,
            imo_number=imo_number,
            flag_state=flag_state,
            severity=severity,
            total_loss_of_ship=total_loss_of_ship,
            fatalities_count=fatalities_count,
            severe_pollution_occurred=severe_pollution_occurred,
            structural_damage_severe=structural_damage_severe,
            mandatory_safety_investigation_required=mandatory_investigation,
            initial_report_deadline_hours=initial_report_hours,
            preliminary_report_deadline_days=preliminary_days,
            final_safety_report_deadline_days=final_report_days,
            vdr_preservation_mandatory=vdr_mandatory,
            investigating_authority=investigating_authority,
            investigation_recommendations=recommendations,
            statutory_governance=statutory_governance,
            verdict=verdict,
        )


# ===========================================================================
# 3. Ship Sale & Purchase (Saleform) Escrow & Closing Engine (Phase 213)
# ===========================================================================

class ShipSalePurchaseEscrowEngine:
    """Models BIMCO SALEFORM 2012 / SHIPSALE 22 transaction mechanics:

    10% deposit escrow, underwater inspection deductions, cancellation remedies,
    and documentary closing protocol under VMC 2015 Arts. 29-36.
    """

    @staticmethod
    def process_saleform_closing(
        contract_ref: str,
        vessel_name: str,
        contract_price_usd: float,
        deposit_percentage: float = 10.0,
        escrow_agent_verified: bool = True,
        inspection_outcome: InspectionOutcome = InspectionOutcome.ACCEPTED_WITHOUT_CONDITION,
        underwater_defect_repair_deduction_usd: float = 0.0,
        bunkers_and_luboils_value_usd: float = 0.0,
        cancelling_date_breached: bool = False,
        buyer_default: bool = False,
        seller_default: bool = False,
        contract_type: SaleformContractType = SaleformContractType.BIMCO_SALEFORM_2012,
    ) -> ShipSaleformFinancialSummary:
        """Calculates closing financial settlement, escrow forfeiture, or release."""
        if contract_price_usd <= 0:
            raise ValueError("Contract price must be positive.")

        deposit_amount = round(contract_price_usd * (deposit_percentage / 100.0), 2)

        closing_documents = [
            "Bill of Sale (Công chứng / Lãnh sự hợp pháp hóa)",
            "Certificate of Ownership & Encumbrance (Giấy chứng nhận sở hữu và không tranh chấp)",
            "Class Maintenance Certificate clean of recommendations",
            "Deletion Certificate / Undertaking from existing Flag Registry",
            "Commercial Invoice for Vessel and Remaining Bunkers/Lubes",
            "Protocol of Delivery and Acceptance (Biên bản bàn giao tàu)",
        ]

        statutory_notes = [
            "BIMCO SALEFORM 2012 Clause 2 & 3 (Deposit & Payment)",
            "BIMCO SALEFORM 2012 Clause 6 (Diver's Inspection / Drydocking)",
            "BIMCO SALEFORM 2012 Clause 14 (Seller's Default) & Clause 13 (Buyer's Default)",
            "Vietnam Maritime Code 2015 Arts. 29-36 (Hợp đồng mua bán tàu biển)",
        ]

        # Financial resolution logic
        if buyer_default:
            # Buyer fails to pay balance: Seller forfeits 10% deposit + right to damages (Cl. 13)
            balance_payable = 0.0
            deposit_forfeited = deposit_amount
            seller_damages = deposit_amount
            title_transferred = False
            verdict = f"BUYER DEFAULT: 10% deposit (${deposit_amount:,.2f}) forfeited to Seller. Delivery aborted."
        elif seller_default or cancelling_date_breached:
            # Seller fails to tender NOR by Cancelling Date: Buyer entitled to full deposit return + interest (Cl. 14)
            balance_payable = 0.0
            deposit_forfeited = 0.0
            seller_damages = round(deposit_amount * 0.05, 2)  # Simulated interest/expenses
            title_transferred = False
            verdict = (
                f"SELLER DEFAULT / CANCELLING DATE BREACH: Full deposit (${deposit_amount:,.2f}) "
                f"returned to Buyer with liquidated interest."
            )
        else:
            # Clean or conditioned delivery closing
            remaining_balance = contract_price_usd - deposit_amount
            net_closing_balance = (
                remaining_balance
                - underwater_defect_repair_deduction_usd
                + bunkers_and_luboils_value_usd
            )
            balance_payable = max(0.0, round(net_closing_balance, 2))
            deposit_forfeited = 0.0
            seller_damages = 0.0
            title_transferred = escrow_agent_verified

            verdict = (
                f"CLOSING APPROVED for {vessel_name}: Net balance payable at delivery: "
                f"${balance_payable:,.2f} USD (Price: ${contract_price_usd:,.2f}, "
                f"Deposit: ${deposit_amount:,.2f}, Defect Holdback: -${underwater_defect_repair_deduction_usd:,.2f}, "
                f"Bunkers/Lubes: +${bunkers_and_luboils_value_usd:,.2f})."
            )

        return ShipSaleformFinancialSummary(
            contract_ref=contract_ref,
            vessel_name=vessel_name,
            contract_price_usd=round(contract_price_usd, 2),
            deposit_percentage=deposit_percentage,
            deposit_amount_usd=deposit_amount,
            escrow_agent_verified=escrow_agent_verified,
            inspection_outcome=inspection_outcome,
            underwater_defect_repair_deduction_usd=round(underwater_defect_repair_deduction_usd, 2),
            bunkers_and_luboils_value_usd=round(bunkers_and_luboils_value_usd, 2),
            cancelling_date_breached=cancelling_date_breached,
            buyer_default_flag=buyer_default,
            seller_default_flag=seller_default,
            balance_payable_on_delivery_usd=balance_payable,
            escrow_deposit_forfeited_usd=deposit_forfeited,
            seller_liquidated_damages_usd=seller_damages,
            legal_title_transfer_approved=title_transferred,
            closing_documents_verified=closing_documents,
            statutory_notes=statutory_notes,
            verdict=verdict,
        )


# ===========================================================================
# 4. Seafarer Repatriation & Contingency Security Engine (Phase 214)
# ===========================================================================

class SeafarerRepatriationContingencyEngine:
    """Models MLC 2006 Standard A2.5 and Circular 22/2017/TT-BGTVT seafarer repatriation

    financial security, abandonment emergency relief, and shipowner recourse liability.
    """

    MAX_ABANDONMENT_WAGES_MONTHS = 4  # MLC 2006 2014 Amendments cap financial security at 4 months

    @staticmethod
    def assess_repatriation(
        case_ref: str,
        vessel_name: str,
        flag_state: str,
        seafarer_count: int,
        trigger_event: RepatriationTrigger,
        compulsory_financial_security_valid: bool,
        security_provider: str = "",
        flight_cost_per_seafarer_usd: float = 1200.0,
        sustenance_daily_usd: float = 50.0,
        stranded_days: int = 14,
        average_monthly_wage_usd: float = 2000.0,
        unpaid_wage_months: float = 2.0,
        emergency_medical_usd: float = 0.0,
    ) -> SeafarerRepatriationAssessment:
        """Audits repatriation costs and computes financial security payout."""
        if seafarer_count <= 0:
            raise ValueError("Seafarer count must be at least 1.")

        total_flights = round(seafarer_count * flight_cost_per_seafarer_usd, 2)
        total_sustenance = round(seafarer_count * sustenance_daily_usd * stranded_days, 2)

        # Under MLC 2006 Reg 2.5 / Standard A2.5.2, outstanding wages capped at 4 months
        capped_wage_months = min(unpaid_wage_months, SeafarerRepatriationContingencyEngine.MAX_ABANDONMENT_WAGES_MONTHS)
        total_wages = round(seafarer_count * average_monthly_wage_usd * capped_wage_months, 2)

        total_liability = round(
            total_flights + total_sustenance + total_wages + emergency_medical_usd, 2
        )

        if compulsory_financial_security_valid:
            insurer_payout = total_liability
            consular_advance = 0.0
            compliance = "COMPLIANT_WITH_MLC_2006_STANDARD_A2_5"
        else:
            # If financial security is missing or void, Flag State / Consular fund intervenes
            insurer_payout = 0.0
            consular_advance = total_liability
            compliance = "NON_COMPLIANT_SHIPOWNER_BREACH_CONSULAR_INTERVENTION"

        statutory_protections = [
            "MLC 2006 Regulation 2.5 & Standard A2.5 (Repatriation)",
            "MLC 2006 2014 Amendments Standard A2.5.2 (Financial Security for Abandonment)",
            "Circular 22/2017/TT-BGTVT (Hồi hương thuyền viên & Bảo đảm tài chính)",
            "Vietnam Maritime Code 2015 Arts. 64-66 (Nghĩa vụ và chi phí hồi hương thuyền viên)",
        ]

        verdict = (
            f"Repatriation Case {case_ref} ({vessel_name}): {seafarer_count} seafarers triggered by {trigger_event.value}. "
            f"Total cost: ${total_liability:,.2f} USD (Flights: ${total_flights:,.2f}, Sustenance: ${total_sustenance:,.2f}, "
            f"Wages [{capped_wage_months:.1f}mo]: ${total_wages:,.2f}). "
            f"Security status: {compliance}."
        )

        return SeafarerRepatriationAssessment(
            case_ref=case_ref,
            vessel_name=vessel_name,
            flag_state=flag_state,
            seafarer_count=seafarer_count,
            trigger_event=trigger_event,
            compulsory_financial_security_valid=compulsory_financial_security_valid,
            security_provider=security_provider,
            flight_tickets_total_usd=total_flights,
            sustenance_and_accommodation_usd=total_sustenance,
            medical_stabilization_usd=round(emergency_medical_usd, 2),
            outstanding_wages_covered_usd=total_wages,
            total_repatriation_liability_usd=total_liability,
            insurer_direct_guarantee_payout_usd=insurer_payout,
            vietnam_consular_contingency_advance_usd=consular_advance,
            owner_recourse_liability_usd=total_liability,
            mlc_standard_compliance=compliance,
            statutory_protections=statutory_protections,
            verdict=verdict,
        )
