# -*- coding: utf-8 -*-
"""Statutory Maritime Ship Agency, Salvage SCOPIC, Abandonment & Green Tug Engine.

Phases Covered:
- Phase 255: Maritime Ship Agency & Husbandry Disbursements Accounting (PDA/FDA)
  (Decree 160/2016/NĐ-CP, Decree 74/2023/NĐ-CP, VMC 2015 Arts. 154-165, Circular 39/2023/TT-BGTVT)
- Phase 256: Maritime Salvage Contracts & LOF 2024 / SCOPIC Clause Settlement
  (VMC 2015 Arts. 282-289, 1989 Salvage Convention, LOF 2024, SCOPIC 2020)
- Phase 257: Seafarer Repatriation & Abandonment Financial Security Guarantee
  (MLC 2006 Reg 2.5 & Standard A2.5.2, Circular 22/2017/TT-BYT, Decree 12/2022/NĐ-CP)
- Phase 258: Seaport Green Tug & Clean Energy Harbor Craft Transition Incentives
  (Decision 876/QĐ-TTg, Circular 39/2023/TT-BGTVT, IMO GHG Strategy 2023)

Architectural Invariant:
- Pure Python standard library only (zero external runtime dependencies).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


# ==============================================================================
# PHASE 255: MARITIME SHIP AGENCY & DISBURSEMENTS ACCOUNTING (PDA/FDA)
# ==============================================================================

class DisbursementCategory(str, Enum):
    """Statutory and commercial disbursement categories under Decree 160/2016 & Circular 39/2023."""
    PORT_DUES = "port_dues"
    PILOTAGE = "pilotage"
    TUGBOAT_SERVICES = "tugboat_services"
    MOORING_UNMOORING = "mooring_unmooring"
    WASTE_RECEPTION_PRF = "waste_reception_prf"
    CUSTOMS_IMMIGRATION_QUARANTINE = "customs_immigration_quarantine"
    HUSBANDRY_CREW = "husbandry_crew"
    BUNKER_SURVEY_TALLY = "bunker_survey_tally"
    MISCELLANEOUS_PORT_EXPENSES = "miscellaneous"


@dataclass(frozen=True)
class DisbursementItem:
    """Itemized port disbursement cost voucher."""
    item_id: str
    category: DisbursementCategory
    description: str
    estimated_usd: float
    actual_usd: float
    voucher_ref: str = ""
    is_disputed: bool = False


@dataclass(frozen=True)
class DisbursementAccountReport:
    """Proforma & Final Disbursement Account (PDA vs FDA) Reconciliation."""
    vessel_name: str
    call_id: str
    port_name: str
    gross_tonnage: float
    advance_deposit_received_usd: float
    total_estimated_pda_usd: float
    total_actual_fda_usd: float
    statutory_agency_fee_usd: float
    freight_commission_usd: float
    net_disbursement_total_usd: float
    balance_settlement_usd: float  # Positive = Refund to shipowner; Negative = Balance due from shipowner
    items: List[DisbursementItem] = field(default_factory=list)
    settlement_status: str = "BALANCED"
    remarks: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vessel_name": self.vessel_name,
            "call_id": self.call_id,
            "port_name": self.port_name,
            "gross_tonnage": self.gross_tonnage,
            "advance_deposit_received_usd": round(self.advance_deposit_received_usd, 2),
            "total_estimated_pda_usd": round(self.total_estimated_pda_usd, 2),
            "total_actual_fda_usd": round(self.total_actual_fda_usd, 2),
            "statutory_agency_fee_usd": round(self.statutory_agency_fee_usd, 2),
            "freight_commission_usd": round(self.freight_commission_usd, 2),
            "net_disbursement_total_usd": round(self.net_disbursement_total_usd, 2),
            "balance_settlement_usd": round(self.balance_settlement_usd, 2),
            "settlement_status": self.settlement_status,
            "items_count": len(self.items),
            "remarks": self.remarks,
        }


class ShipAgencyDisbursementEngine:
    """Phase 255: Reconciles PDA/FDA accounting and statutory agency fees."""

    @staticmethod
    def calculate_statutory_agency_fee(
        gross_tonnage: float,
        port_stay_days: int = 2,
        is_tanker_or_dangerous: bool = False,
    ) -> float:
        """Computes official statutory agency remuneration under Circular 39/2023 & industry tariff."""
        base_fee = 800.0  # Base fee up to 5,000 GT
        if gross_tonnage > 50000:
            base_fee = 2800.0
        elif gross_tonnage > 30000:
            base_fee = 2200.0
        elif gross_tonnage > 15000:
            base_fee = 1600.0
        elif gross_tonnage > 5000:
            base_fee = 1100.0

        # Port stay duration surcharge (days beyond standard 2 days)
        extra_days = max(0, port_stay_days - 2)
        duration_surcharge = extra_days * 150.0

        # Hazardous / tanker surcharge
        hazardous_multiplier = 1.20 if is_tanker_or_dangerous else 1.0

        return (base_fee + duration_surcharge) * hazardous_multiplier

    @classmethod
    def reconcile_pda_fda(
        cls,
        vessel_name: str,
        call_id: str,
        port_name: str,
        gross_tonnage: float,
        advance_deposit_received_usd: float,
        items: List[DisbursementItem],
        port_stay_days: int = 2,
        collected_freight_usd: float = 0.0,
        freight_commission_rate_pct: float = 1.25,
        is_tanker_or_dangerous: bool = False,
    ) -> DisbursementAccountReport:
        """Reconciles proforma against actual disbursements and determines final balance."""
        tot_est = sum(item.estimated_usd for item in items)
        tot_act = sum(item.actual_usd for item in items)

        agency_fee = cls.calculate_statutory_agency_fee(
            gross_tonnage=gross_tonnage,
            port_stay_days=port_stay_days,
            is_tanker_or_dangerous=is_tanker_or_dangerous,
        )

        freight_comm = collected_freight_usd * (freight_commission_rate_pct / 100.0)
        net_disbursements = tot_act + agency_fee + freight_comm
        balance = advance_deposit_received_usd - net_disbursements

        if balance > 0.01:
            status = "REFUND_TO_PRINCIPAL"
            remarks = f"Hoàn trả chủ tàu {balance:,.2f} USD tiền tạm ứng dư."
        elif balance < -0.01:
            status = "SUPPLEMENTARY_DUE_FROM_PRINCIPAL"
            remarks = f"Chủ tàu phải thanh toán bổ sung {-balance:,.2f} USD."
        else:
            status = "BALANCED"
            remarks = "Tài khoản giải ngân cân bằng hoàn toàn (0.00 USD)."

        return DisbursementAccountReport(
            vessel_name=vessel_name,
            call_id=call_id,
            port_name=port_name,
            gross_tonnage=gross_tonnage,
            advance_deposit_received_usd=advance_deposit_received_usd,
            total_estimated_pda_usd=tot_est,
            total_actual_fda_usd=tot_act,
            statutory_agency_fee_usd=agency_fee,
            freight_commission_usd=freight_comm,
            net_disbursement_total_usd=net_disbursements,
            balance_settlement_usd=balance,
            items=items,
            settlement_status=status,
            remarks=remarks,
        )


# ==============================================================================
# PHASE 256: MARITIME SALVAGE CONTRACTS & LOF 2024 / SCOPIC SETTLEMENT
# ==============================================================================

class SalvageContractRegime(str, Enum):
    """Salvage legal regimes under VMC 2015 Arts. 282-289 & LOF 2024."""
    LOF_ARTICLE_13_ONLY = "lof_article_13"
    SCOPIC_INVOKED = "scopic_invoked"
    ARTICLE_14_SPECIAL_COMPENSATION = "article_14_special_compensation"


@dataclass(frozen=True)
class SalvedPropertyValues:
    """Salved property valuation establishing the salvage award fund."""
    sound_ship_value_usd: float
    damage_repair_costs_usd: float
    cargo_cif_value_usd: float
    unpaid_freight_at_risk_usd: float

    @property
    def net_salved_fund_usd(self) -> float:
        net_ship = max(0.0, self.sound_ship_value_usd - self.damage_repair_costs_usd)
        return net_ship + self.cargo_cif_value_usd + self.unpaid_freight_at_risk_usd


@dataclass(frozen=True)
class SCOPICExpenseItem:
    """Itemized daily tariff calculation under SCOPIC 2020 rate book."""
    equipment_or_craft_name: str
    daily_tariff_rate_usd: float
    operating_days: float
    personnel_costs_usd: float = 0.0


@dataclass(frozen=True)
class SalvageSettlementResult:
    """Final remuneration settlement under Lloyd's Open Form (LOF) & SCOPIC."""
    regime: SalvageContractRegime
    net_salved_fund_usd: float
    article_13_assessed_award_usd: float
    scopic_costs_usd: float
    scopic_bonus_uplift_usd: float
    total_scopic_remuneration_usd: float
    article_13_discount_penalty_usd: float  # 25% discount if Art 13 > SCOPIC
    final_salvor_remuneration_usd: float
    property_underwriters_liability_usd: float
    pni_club_liability_usd: float
    is_environmental_protection_achieved: bool
    settlement_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "regime": self.regime.value,
            "net_salved_fund_usd": round(self.net_salved_fund_usd, 2),
            "article_13_assessed_award_usd": round(self.article_13_assessed_award_usd, 2),
            "scopic_costs_usd": round(self.scopic_costs_usd, 2),
            "scopic_bonus_uplift_usd": round(self.scopic_bonus_uplift_usd, 2),
            "total_scopic_remuneration_usd": round(self.total_scopic_remuneration_usd, 2),
            "article_13_discount_penalty_usd": round(self.article_13_discount_penalty_usd, 2),
            "final_salvor_remuneration_usd": round(self.final_salvor_remuneration_usd, 2),
            "property_underwriters_liability_usd": round(self.property_underwriters_liability_usd, 2),
            "pni_club_liability_usd": round(self.pni_club_liability_usd, 2),
            "is_environmental_protection_achieved": self.is_environmental_protection_achieved,
            "settlement_summary": self.settlement_summary,
        }


class MaritimeSalvageEngine:
    """Phase 256: Resolves LOF 2024 Art 13 awards and SCOPIC clause settlements."""

    @classmethod
    def calculate_salvage_settlement(
        cls,
        property_values: SalvedPropertyValues,
        assessed_art13_award_percentage: float,  # typically 5% - 25% of salved fund
        regime: SalvageContractRegime = SalvageContractRegime.SCOPIC_INVOKED,
        scopic_items: Optional[List[SCOPICExpenseItem]] = None,
        environmental_protection_achieved: bool = True,
    ) -> SalvageSettlementResult:
        """Determines final award, applying SCOPIC 25% bonus and 25% Art 13 penalty discount."""
        salved_fund = property_values.net_salved_fund_usd
        bounded_pct = min(100.0, max(0.0, assessed_art13_award_percentage))
        art13_award = salved_fund * (bounded_pct / 100.0)

        scopic_base = 0.0
        if scopic_items:
            for item in scopic_items:
                craft_cost = item.daily_tariff_rate_usd * item.operating_days
                scopic_base += craft_cost + item.personnel_costs_usd

        scopic_bonus = scopic_base * 0.25  # Standard SCOPIC 25% uplift
        total_scopic = scopic_base + scopic_bonus

        discount_penalty = 0.0
        if regime == SalvageContractRegime.SCOPIC_INVOKED:
            if art13_award > total_scopic:
                # Under Sub-clause 7 of SCOPIC: If Art 13 > SCOPIC, Art 13 is discounted by 25% of the excess
                excess = art13_award - total_scopic
                discount_penalty = excess * 0.25
                final_award = art13_award - discount_penalty
                prop_underwriters = final_award
                pni_liability = 0.0
                summary = (
                    f"Art 13 ({art13_award:,.2f}) > SCOPIC ({total_scopic:,.2f}). "
                    f"Áp dụng giảm trừ 25% chênh lệch ({discount_penalty:,.2f} USD). "
                    f"Bảo hiểm thân tàu/hàng chi trả {final_award:,.2f} USD."
                )
            else:
                # SCOPIC > Art 13: Salvor receives Art 13 from Property Underwriters + (SCOPIC - Art 13) from P&I Club
                final_award = total_scopic
                prop_underwriters = art13_award
                pni_liability = total_scopic - art13_award
                summary = (
                    f"SCOPIC ({total_scopic:,.2f}) > Art 13 ({art13_award:,.2f}). "
                    f"Bảo hiểm tài sản trả {prop_underwriters:,.2f} USD; "
                    f"Hội P&I chi trả phần chênh lệch cứu hộ môi trường {pni_liability:,.2f} USD."
                )
        elif regime == SalvageContractRegime.ARTICLE_14_SPECIAL_COMPENSATION:
            # Art 14: Salvor expenses plus up to 30% bonus (covered by P&I)
            art14_bonus = scopic_base * 0.30 if environmental_protection_achieved else 0.0
            total_art14 = scopic_base + art14_bonus
            final_award = max(art13_award, total_art14)
            prop_underwriters = art13_award
            pni_liability = max(0.0, total_art14 - art13_award)
            summary = f"Áp dụng Điều 14 Công ước Cứu hộ 1989. Tổng bồi hoàn: {final_award:,.2f} USD."
        else:
            # Traditional LOF Article 13 only
            final_award = art13_award
            prop_underwriters = art13_award
            pni_liability = 0.0
            summary = f"Cứu hộ thuần túy theo Điều 13 LOF. Thù lao cứu hộ: {final_award:,.2f} USD."

        return SalvageSettlementResult(
            regime=regime,
            net_salved_fund_usd=salved_fund,
            article_13_assessed_award_usd=art13_award,
            scopic_costs_usd=scopic_base,
            scopic_bonus_uplift_usd=scopic_bonus,
            total_scopic_remuneration_usd=total_scopic,
            article_13_discount_penalty_usd=discount_penalty,
            final_salvor_remuneration_usd=final_award,
            property_underwriters_liability_usd=prop_underwriters,
            pni_club_liability_usd=pni_liability,
            is_environmental_protection_achieved=environmental_protection_achieved,
            settlement_summary=summary,
        )


# ==============================================================================
# PHASE 257: SEAFARER REPATRIATION & ABANDONMENT FINANCIAL SECURITY GUARANTEE
# ==============================================================================

class AbandonmentTrigger(str, Enum):
    """Criteria qualifying for seafarer abandonment under MLC 2006 Standard A2.5.2."""
    UNPAID_WAGES_2_MONTHS = "unpaid_wages_2_months"
    FAILURE_TO_REPATRIATE = "failure_to_repatriate"
    LACK_OF_PROVISIONS_AND_SUPPORT = "lack_of_provisions_support"
    SEVERED_SHIPOWNER_TIES = "severed_shipowner_ties"


@dataclass(frozen=True)
class SeafarerAbandonmentClaim:
    """Individual seafarer claim under the financial security guarantee."""
    seafarer_name: str
    rank_or_role: str
    nationality: str
    monthly_basic_wage_usd: float
    months_unpaid: float
    actual_outstanding_wages_usd: float
    repatriation_home_country: str
    estimated_travel_cost_usd: float
    stranding_days_onboard: int = 14


@dataclass(frozen=True)
class AbandonmentSettlementReport:
    """MLC 2006 financial security insurer payout adjudication."""
    vessel_name: str
    imo_number: str
    guarantor_pni_insurer: str
    trigger: AbandonmentTrigger
    total_seafarers_stranded: int
    total_gross_wages_claimed_usd: float
    total_statutory_capped_wages_usd: float  # Capped at 4 months per MLC Standard A2.5.2
    total_repatriation_transit_costs_usd: float
    total_subsistence_allowance_usd: float  # Daily provisions/medical allowance
    total_guarantee_payout_usd: float
    shipowner_recourse_claim_usd: float  # Full subrogation against shipowner assets
    adjudication_verdict: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vessel_name": self.vessel_name,
            "imo_number": self.imo_number,
            "guarantor_pni_insurer": self.guarantor_pni_insurer,
            "trigger": self.trigger.value,
            "total_seafarers_stranded": self.total_seafarers_stranded,
            "total_gross_wages_claimed_usd": round(self.total_gross_wages_claimed_usd, 2),
            "total_statutory_capped_wages_usd": round(self.total_statutory_capped_wages_usd, 2),
            "total_repatriation_transit_costs_usd": round(self.total_repatriation_transit_costs_usd, 2),
            "total_subsistence_allowance_usd": round(self.total_subsistence_allowance_usd, 2),
            "total_guarantee_payout_usd": round(self.total_guarantee_payout_usd, 2),
            "shipowner_recourse_claim_usd": round(self.shipowner_recourse_claim_usd, 2),
            "adjudication_verdict": self.adjudication_verdict,
        }


class SeafarerAbandonmentEngine:
    """Phase 257: Adjudicates financial security payouts for abandoned seafarers."""

    DAILY_SUBSISTENCE_PER_SEAFARER_USD = 30.0  # Food, potable water, medical, comms

    @classmethod
    def adjudicate_abandonment(
        cls,
        vessel_name: str,
        imo_number: str,
        guarantor_pni_insurer: str,
        trigger: AbandonmentTrigger,
        claims: List[SeafarerAbandonmentClaim],
    ) -> AbandonmentSettlementReport:
        """Computes capped 4-month wages, flights, subsistence, and subrogation claims."""
        gross_wages = sum(c.actual_outstanding_wages_usd for c in claims)
        capped_wages = 0.0
        repat_transit = sum(c.estimated_travel_cost_usd for c in claims)
        subsistence = 0.0

        for claim in claims:
            # MLC 2006 Standard A2.5.2 Clause 2(a): Capped at max 4 months outstanding wages
            max_allowed_months = min(4.0, claim.months_unpaid)
            capped_seafarer_wages = claim.monthly_basic_wage_usd * max_allowed_months
            # Bound by actual claimed amount if less than formula
            capped_wages += min(claim.actual_outstanding_wages_usd, capped_seafarer_wages)

            # Daily subsistence during stranding
            subsistence += claim.stranding_days_onboard * cls.DAILY_SUBSISTENCE_PER_SEAFARER_USD

        total_payout = capped_wages + repat_transit + subsistence
        verdict = (
            f"CHẤP THUẬN KÍCH HOẠT BẢO ĐẢM TÀI CHÍNH MLC 2006: "
            f"Hội bảo lãnh chi trả khẩn cấp {total_payout:,.2f} USD cho {len(claims)} thuyền viên. "
            f"Lương nợ chốt trần 4 tháng ({capped_wages:,.2f} USD). "
            f"Kích hoạt quyền truy đòi thế quyền 100% đối với chủ tàu."
        )

        return AbandonmentSettlementReport(
            vessel_name=vessel_name,
            imo_number=imo_number,
            guarantor_pni_insurer=guarantor_pni_insurer,
            trigger=trigger,
            total_seafarers_stranded=len(claims),
            total_gross_wages_claimed_usd=gross_wages,
            total_statutory_capped_wages_usd=capped_wages,
            total_repatriation_transit_costs_usd=repat_transit,
            total_subsistence_allowance_usd=subsistence,
            total_guarantee_payout_usd=total_payout,
            shipowner_recourse_claim_usd=total_payout,
            adjudication_verdict=verdict,
        )


# ==============================================================================
# PHASE 258: SEAPORT GREEN TUG & CLEAN HARBOR CRAFT TRANSITION INCENTIVES
# ==============================================================================

class HarborCraftPropulsion(str, Enum):
    """Propulsion energy technologies for harbor craft transition."""
    CONVENTIONAL_DIESEL = "conventional_diesel"
    HYBRID_DIESEL_ELECTRIC = "hybrid_diesel_electric"
    PURE_BATTERY_ELECTRIC = "pure_battery_electric"
    GREEN_HYDROGEN_FUEL_CELL = "green_hydrogen_fc"
    GREEN_E_METHANOL = "green_e_methanol"


@dataclass(frozen=True)
class GreenHarborCraftMetrics:
    """Decarbonization, fuel savings, port tariff rebates, and simple payback."""
    craft_name: str
    propulsion: HarborCraftPropulsion
    bollard_pull_tonnes: float
    annual_operating_hours: float
    baseline_mgo_co2_tonnes_per_year: float
    abated_co2_tonnes_per_year: float
    abatement_ratio_pct: float
    annual_fuel_cost_savings_usd: float
    annual_green_tariff_rebate_usd: float  # Circular 39/2023 green port fee reduction
    annual_total_economic_benefit_usd: float
    capex_green_premium_usd: float
    simple_payback_years: float
    statutory_incentive_compliance: bool
    remarks: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "craft_name": self.craft_name,
            "propulsion": self.propulsion.value,
            "bollard_pull_tonnes": self.bollard_pull_tonnes,
            "annual_operating_hours": self.annual_operating_hours,
            "baseline_mgo_co2_tonnes_per_year": round(self.baseline_mgo_co2_tonnes_per_year, 2),
            "abated_co2_tonnes_per_year": round(self.abated_co2_tonnes_per_year, 2),
            "abatement_ratio_pct": round(self.abatement_ratio_pct, 2),
            "annual_fuel_cost_savings_usd": round(self.annual_fuel_cost_savings_usd, 2),
            "annual_green_tariff_rebate_usd": round(self.annual_green_tariff_rebate_usd, 2),
            "annual_total_economic_benefit_usd": round(self.annual_total_economic_benefit_usd, 2),
            "capex_green_premium_usd": round(self.capex_green_premium_usd, 2),
            "simple_payback_years": round(self.simple_payback_years, 2),
            "statutory_incentive_compliance": self.statutory_incentive_compliance,
            "remarks": self.remarks,
        }


class GreenHarborCraftEngine:
    """Phase 258: Evaluates green tugboat transition economics and Decision 876 incentives."""

    # IMO emission baseline constants
    MGO_EMISSION_FACTOR_CO2_PER_TONNE = 3.206
    SFOC_G_PER_KWH = 210.0  # Average specific fuel oil consumption
    MGO_PRICE_PER_TONNE_USD = 850.0

    @classmethod
    def evaluate_transition(
        cls,
        craft_name: str,
        bollard_pull_tonnes: float,
        propulsion: HarborCraftPropulsion,
        annual_operating_hours: float = 2500.0,
        average_power_kw: float = 1200.0,
        capex_green_premium_usd: float = 1500000.0,
        annual_port_dues_paid_usd: float = 80000.0,
    ) -> GreenHarborCraftMetrics:
        """Calculates emissions abatement, fuel savings, Circular 39 rebate, and payback period."""
        # Baseline annual MGO consumption (tonnes)
        total_kwh_per_year = average_power_kw * annual_operating_hours
        baseline_fuel_tonnes = (total_kwh_per_year * cls.SFOC_G_PER_KWH) / 1_000_000.0
        baseline_co2 = baseline_fuel_tonnes * cls.MGO_EMISSION_FACTOR_CO2_PER_TONNE
        baseline_fuel_cost = baseline_fuel_tonnes * cls.MGO_PRICE_PER_TONNE_USD

        # Abatement factors by clean energy propulsion
        abatement_map = {
            HarborCraftPropulsion.CONVENTIONAL_DIESEL: (0.0, 0.0),
            HarborCraftPropulsion.HYBRID_DIESEL_ELECTRIC: (0.22, 0.20),  # (CO2 abatement, Fuel savings)
            HarborCraftPropulsion.PURE_BATTERY_ELECTRIC: (0.80, 0.65),
            HarborCraftPropulsion.GREEN_HYDROGEN_FUEL_CELL: (0.95, 0.40),
            HarborCraftPropulsion.GREEN_E_METHANOL: (0.90, 0.35),
        }

        co2_ratio, fuel_save_ratio = abatement_map.get(propulsion, (0.0, 0.0))
        abated_co2 = baseline_co2 * co2_ratio
        fuel_savings = baseline_fuel_cost * fuel_save_ratio

        # Circular 39/2023 / Decision 876: Green harbor craft qualifying for port tariff rebates
        # Tiered rebate: Hybrid 10%, Electric/H2/Methanol 20%
        rebate_rate = 0.0
        if propulsion in (HarborCraftPropulsion.PURE_BATTERY_ELECTRIC, HarborCraftPropulsion.GREEN_HYDROGEN_FUEL_CELL, HarborCraftPropulsion.GREEN_E_METHANOL):
            rebate_rate = 0.20
        elif propulsion == HarborCraftPropulsion.HYBRID_DIESEL_ELECTRIC:
            rebate_rate = 0.10

        tariff_rebate = annual_port_dues_paid_usd * rebate_rate
        total_benefit = fuel_savings + tariff_rebate

        if total_benefit > 0.0:
            payback = capex_green_premium_usd / total_benefit
        else:
            payback = 99.9

        is_compliant = propulsion != HarborCraftPropulsion.CONVENTIONAL_DIESEL

        remarks = (
            f"Công nghệ {propulsion.value}: Giảm phát thải {abated_co2:,.1f} tấn CO2/năm ({co2_ratio*100:.1f}%). "
            f"Tổng lợi ích kinh tế: {total_benefit:,.2f} USD/năm (Thời gian hoàn vốn {payback:.1f} năm)."
        )

        return GreenHarborCraftMetrics(
            craft_name=craft_name,
            propulsion=propulsion,
            bollard_pull_tonnes=bollard_pull_tonnes,
            annual_operating_hours=annual_operating_hours,
            baseline_mgo_co2_tonnes_per_year=baseline_co2,
            abated_co2_tonnes_per_year=abated_co2,
            abatement_ratio_pct=co2_ratio * 100.0,
            annual_fuel_cost_savings_usd=fuel_savings,
            annual_green_tariff_rebate_usd=tariff_rebate,
            annual_total_economic_benefit_usd=total_benefit,
            capex_green_premium_usd=capex_green_premium_usd,
            simple_payback_years=payback,
            statutory_incentive_compliance=is_compliant,
            remarks=remarks,
        )
