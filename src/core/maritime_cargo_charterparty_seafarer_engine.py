"""Maritime Cargo Claims, Charterparty Laytime, Seaman Employment & Pilotage/Towage Suite (Phases 207-210).

Statutory references:
- Phase 207: Vietnam Maritime Code 2015 (VMC 2015) Arts. 145-174, Hague-Visby Rules 1968, Hamburg Rules 1978.
  - Art. 152 dual statutory ceiling: 666.67 SDR/package or 2.0 SDR/kg gross weight (Hague-Visby baseline) vs. 835 SDR/pkg or 2.5 SDR/kg (Hamburg).
  - Art. 151 17 statutory carrier exemptions (nautical fault, fire, perils of the sea, act of God, latent defect).
  - Art. 154 notice of loss timebars (apparent: on delivery; non-apparent: 3 consecutive days; Hague-Visby 7 days; Hamburg 15 days).
  - Art. 169 1-year prescription timebar.
- Phase 208: Charterparty Demurrage, Dispatch & Laytime Performance.
  - Laytime allowed calculation (SHINC, SHEX, Weather Working Days - WWD).
  - Notice of Readiness (NOR) tendering and laytime commencement windows (13:00 if tendered before 12:00, 08:00 next working day if tendered afternoon).
  - Continuous demurrage ("Once on demurrage, always on demurrage").
  - Dispatch calculation (standard 50% demurrage rate on laytime saved).
- Phase 209: Seafarer Employment Agreement (SEA) & MLC 2006 Statutory Wage/Disability.
  - VMC 2015 Arts. 56-68, Maritime Labour Convention 2006 (MLC 2006) Title 2.
  - Statutory basic wage, overtime allowance (150% normal, 200% rest days, 300% holidays), paid annual leave (minimum 2.5 calendar days per month).
  - Full sick wage maintenance and medical expenses during treatment.
  - Permanent disability & death indemnity scale under VMC Art. 63 / statutory CBA standards.
- Phase 210: Marine Pilotage Liability & Towage Contract Allocation.
  - VMC 2015 Arts. 246-259: Marine pilot as advisor to Master, Master retains navigation command.
  - VMC Art. 253: Pilotage organization liability capped at the pilotage service fee collected for the transit.
  - VMC Arts. 260-270: Sea towage vs. Port assist towage; command of flotilla determines primary liability.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# ===========================================================================
# Phase 207: Cargo Claims & Bill of Lading Engine Enums & Models
# ===========================================================================

class MaritimeLiabilityRegime(str, Enum):
    VIETNAM_MARITIME_CODE_2015 = "VIETNAM_MARITIME_CODE_2015"
    HAGUE_VISBY_RULES = "HAGUE_VISBY_RULES"
    HAMBURG_RULES = "HAMBURG_RULES"


class CarrierDefenseCategory(str, Enum):
    NAUTICAL_FAULT_NAVIGATION_MANAGEMENT = "NAUTICAL_FAULT_NAVIGATION_MANAGEMENT"  # Art 151(2)(a)
    FIRE_WITHOUT_ACTUAL_FAULT_OR_PRIVITY = "FIRE_WITHOUT_ACTUAL_FAULT_OR_PRIVITY"  # Art 151(2)(b)
    PERILS_OF_THE_SEA = "PERILS_OF_THE_SEA"                                        # Art 151(2)(c)
    ACT_OF_GOD = "ACT_OF_GOD"                                                      # Art 151(2)(d)
    ACT_OF_WAR_OR_HOSTILITIES = "ACT_OF_WAR_OR_HOSTILITIES"                        # Art 151(2)(e)
    PUBLIC_ENEMIES_OR_PIRACY = "PUBLIC_ENEMIES_OR_PIRACY"                          # Art 151(2)(f)
    ARREST_OR_RESTRAINT_OF_PRINCES = "ARREST_OR_RESTRAINT_OF_PRINCES"              # Art 151(2)(g)
    QUARANTINE_RESTRICTIONS = "QUARANTINE_RESTRICTIONS"                            # Art 151(2)(h)
    STRIKES_OR_LOCKOUTS = "STRIKES_OR_LOCKOUTS"                                    # Art 151(2)(i)
    SAVING_LIFE_OR_PROPERTY_AT_SEA = "SAVING_LIFE_OR_PROPERTY_AT_SEA"              # Art 151(2)(j)
    INHERENT_VICE_OF_GOODS = "INHERENT_VICE_OF_GOODS"                              # Art 151(2)(k)
    INSUFFICIENCY_OF_PACKING_OR_MARKING = "INSUFFICIENCY_OF_PACKING_OR_MARKING"    # Art 151(2)(l)
    LATENT_DEFECTS_NOT_DISCOVERABLE_BY_DUE_DILIGENCE = "LATENT_DEFECTS"            # Art 151(2)(m)
    SHIPPER_OR_OWNER_FAULT = "SHIPPER_OR_OWNER_FAULT"                              # Art 151(2)(n)
    NONE = "NONE"


@dataclass
class CargoClaimAssessment:
    claim_id: str
    regime: MaritimeLiabilityRegime
    cargo_description: str
    number_of_packages: int
    gross_weight_kg: float
    claimed_loss_usd: float
    sdr_to_usd_rate: float
    statutory_package_limit_sdr: float
    statutory_kg_limit_sdr: float
    package_ceiling_usd: float
    weight_ceiling_usd: float
    applicable_statutory_limit_usd: float
    carrier_defense: CarrierDefenseCategory
    defense_valid: bool
    is_timebarred_notice: bool
    is_timebarred_1year_prescription: bool
    admissible_claim_amount_usd: float
    carrier_payout_liability_usd: float
    verdict: str
    notes: List[str] = field(default_factory=list)


# ===========================================================================
# Phase 208: Charterparty Laytime, Demurrage & Dispatch Models
# ===========================================================================

class LaytimeTerm(str, Enum):
    SHINC = "SHINC"  # Sundays and Holidays Included
    SHEX = "SHEX"    # Sundays and Holidays Excluded
    WWD = "WWD"      # Weather Working Days (excludes bad weather)


@dataclass
class LaytimeDemurrageResult:
    charter_ref: str
    vessel_name: str
    laytime_term: LaytimeTerm
    total_allowed_laytime_hours: float
    nor_tendered_iso: str
    laytime_commenced_iso: str
    laytime_used_hours: float
    time_saved_hours: float
    demurrage_hours: float
    demurrage_rate_per_day_usd: float
    dispatch_rate_per_day_usd: float
    demurrage_payable_usd: float
    dispatch_receivable_usd: float
    net_charter_settlement_usd: float  # Positive = Demurrage payable by Charterer; Negative = Dispatch payable by Owner
    settlement_party: str
    verdict: str


# ===========================================================================
# Phase 209: Seafarer Employment Agreement (SEA) & MLC 2006 Models
# ===========================================================================

class SeafarerRank(str, Enum):
    MASTER = "MASTER"
    CHIEF_ENGINEER = "CHIEF_ENGINEER"
    CHIEF_OFFICER = "CHIEF_OFFICER"
    SECOND_ENGINEER = "SECOND_ENGINEER"
    DECK_OFFICER = "DECK_OFFICER"
    ENGINE_OFFICER = "ENGINE_OFFICER"
    ABLE_SEAMAN = "ABLE_SEAMAN"
    ORDINARY_SEAMAN = "ORDINARY_SEAMAN"
    MOTORMAN_OILER = "MOTORMAN_OILER"
    CHIEF_COOK = "CHIEF_COOK"


class DisabilityDegree(str, Enum):
    TEMPORARY_PARTIAL = "TEMPORARY_PARTIAL"
    PERMANENT_PARTIAL_UNDER_50 = "PERMANENT_PARTIAL_UNDER_50"
    PERMANENT_SEVERE_50_TO_80 = "PERMANENT_SEVERE_50_TO_80"
    PERMANENT_TOTAL_ABOVE_80 = "PERMANENT_TOTAL_ABOVE_80"
    DEATH_FATALITY = "DEATH_FATALITY"
    NONE = "NONE"


@dataclass
class SeafarerCompensationAssessment:
    seafarer_name: str
    rank: SeafarerRank
    basic_monthly_wage_usd: float
    normal_overtime_hours: float
    rest_day_overtime_hours: float
    holiday_overtime_hours: float
    calculated_monthly_wage_usd: float
    leave_days_accrued: float
    paid_leave_allowance_usd: float
    medical_treatment_cost_usd: float
    medical_wage_maintenance_usd: float
    disability_degree: DisabilityDegree
    disability_compensation_usd: float
    total_statutory_liability_usd: float
    mlc_compliance_status: str
    verdict: str


# ===========================================================================
# Phase 210: Marine Pilotage Liability & Towage Contract Allocation Models
# ===========================================================================

class TowageContractType(str, Enum):
    PORT_ASSIST_BERTHING = "PORT_ASSIST_BERTHING"      # Usually under Master/Pilot command
    SEA_COASTAL_OCEAN_TOW = "SEA_COASTAL_OCEAN_TOW"    # Usually Tug Master command


class FlotillaCommandType(str, Enum):
    TUG_MASTER_COMMAND = "TUG_MASTER_COMMAND"
    TOWED_VESSEL_MASTER_COMMAND = "TOWED_VESSEL_MASTER_COMMAND"


@dataclass
class PilotageAndTowageAssessment:
    operation_id: str
    vessel_name: str
    pilotage_fee_collected_usd: float
    total_marine_casualty_loss_usd: float
    pilot_error_proven: bool
    statutory_pilot_liability_usd: float
    master_navigation_liability_usd: float
    towage_type: TowageContractType
    command_authority: FlotillaCommandType
    tug_allocated_liability_usd: float
    towed_vessel_allocated_liability_usd: float
    verdict: str
    applicable_articles: List[str] = field(default_factory=list)


# ===========================================================================
# Core Engines Implementation
# ===========================================================================

class MaritimeCargoClaimsEngine:
    """Carriage of Goods by Sea & Cargo Claims under VMC 2015 & Conventions."""

    @staticmethod
    def assess_cargo_claim(
        claim_id: str,
        cargo_description: str,
        number_of_packages: int,
        gross_weight_kg: float,
        claimed_loss_usd: float,
        carrier_defense: CarrierDefenseCategory = CarrierDefenseCategory.NONE,
        regime: MaritimeLiabilityRegime = MaritimeLiabilityRegime.VIETNAM_MARITIME_CODE_2015,
        sdr_to_usd_rate: float = 1.35,
        notice_days_after_delivery: int = 0,
        apparent_damage: bool = True,
        days_since_delivery: int = 30,
        due_diligence_seaworthy: bool = True,
    ) -> CargoClaimAssessment:
        notes: List[str] = []

        # 1. Statutory package & gross weight limits
        if regime in (MaritimeLiabilityRegime.VIETNAM_MARITIME_CODE_2015, MaritimeLiabilityRegime.HAGUE_VISBY_RULES):
            pkg_limit_sdr = 666.67
            kg_limit_sdr = 2.0
            notes.append("VMC Art. 152 / Hague-Visby: 666.67 SDR/pkg or 2.0 SDR/kg gross weight.")
        else:  # HAMBURG_RULES
            pkg_limit_sdr = 835.0
            kg_limit_sdr = 2.5
            notes.append("Hamburg Rules Art. 6: 835.0 SDR/pkg or 2.5 SDR/kg gross weight.")

        package_ceiling_usd = round(number_of_packages * pkg_limit_sdr * sdr_to_usd_rate, 2)
        weight_ceiling_usd = round(gross_weight_kg * kg_limit_sdr * sdr_to_usd_rate, 2)
        applicable_statutory_limit_usd = max(package_ceiling_usd, weight_ceiling_usd)

        # 2. Timebar Checks
        # Notice of loss timebar
        is_timebarred_notice = False
        if regime == MaritimeLiabilityRegime.VIETNAM_MARITIME_CODE_2015:
            # Art. 154: Apparent -> at delivery (0 days). Non-apparent -> 3 days.
            if apparent_damage and notice_days_after_delivery > 0:
                is_timebarred_notice = True
                notes.append("Art. 154 notice timebar: Apparent damage must be notified upon delivery.")
            elif not apparent_damage and notice_days_after_delivery > 3:
                is_timebarred_notice = True
                notes.append("Art. 154 notice timebar: Non-apparent damage notice exceeded 3 consecutive days.")
        elif regime == MaritimeLiabilityRegime.HAGUE_VISBY_RULES:
            if not apparent_damage and notice_days_after_delivery > 7:
                is_timebarred_notice = True
                notes.append("Hague-Visby Art. III(6): Non-apparent damage notice exceeded 7 days.")
        else:  # Hamburg
            if not apparent_damage and notice_days_after_delivery > 15:
                is_timebarred_notice = True
                notes.append("Hamburg Rules Art. 19: Non-apparent damage notice exceeded 15 days.")

        # 1-year prescription under Art. 169
        is_timebarred_1year_prescription = False
        if days_since_delivery > 365:
            is_timebarred_1year_prescription = True
            notes.append("VMC Art. 169 / Hague-Visby Art. III(6): Extinguished by 1-year statutory limitation.")

        # 3. Carrier Defenses
        defense_valid = False
        if carrier_defense != CarrierDefenseCategory.NONE:
            if not due_diligence_seaworthy:
                defense_valid = False
                notes.append("Carrier defense OVERRIDDEN: Carrier failed due diligence to make vessel seaworthy (Art. 150).")
            else:
                defense_valid = True
                notes.append(f"Carrier defense ACCEPTED: Exempt from liability under Art. 151 ({carrier_defense.value}).")

        # 4. Liability Payout Determination
        if is_timebarred_1year_prescription:
            admissible_claim_amount_usd = 0.0
            carrier_payout_liability_usd = 0.0
            verdict = "CLAIM EXTINGUISHED: 1-Year Maritime Prescription Timebar (Art. 169)"
        elif defense_valid:
            admissible_claim_amount_usd = claimed_loss_usd
            carrier_payout_liability_usd = 0.0
            verdict = f"CARRIER EXEMPT: Valid Defense under Art. 151 ({carrier_defense.name})"
        elif is_timebarred_notice:
            # Presumption of good delivery shifted, burden of proof on cargo owner; if admitted, limited
            admissible_claim_amount_usd = min(claimed_loss_usd, applicable_statutory_limit_usd)
            carrier_payout_liability_usd = admissible_claim_amount_usd
            verdict = "BURDEN SHIFTED: Notice of Loss Delayed; Liability Capped by Statutory Ceiling"
        else:
            admissible_claim_amount_usd = min(claimed_loss_usd, applicable_statutory_limit_usd)
            carrier_payout_liability_usd = admissible_claim_amount_usd
            verdict = "CARRIER LIABLE: Cargo Claim Admissible Subject to Statutory Dual Ceiling"

        return CargoClaimAssessment(
            claim_id=claim_id,
            regime=regime,
            cargo_description=cargo_description,
            number_of_packages=number_of_packages,
            gross_weight_kg=gross_weight_kg,
            claimed_loss_usd=claimed_loss_usd,
            sdr_to_usd_rate=sdr_to_usd_rate,
            statutory_package_limit_sdr=pkg_limit_sdr,
            statutory_kg_limit_sdr=kg_limit_sdr,
            package_ceiling_usd=package_ceiling_usd,
            weight_ceiling_usd=weight_ceiling_usd,
            applicable_statutory_limit_usd=applicable_statutory_limit_usd,
            carrier_defense=carrier_defense,
            defense_valid=defense_valid,
            is_timebarred_notice=is_timebarred_notice,
            is_timebarred_1year_prescription=is_timebarred_1year_prescription,
            admissible_claim_amount_usd=admissible_claim_amount_usd,
            carrier_payout_liability_usd=carrier_payout_liability_usd,
            verdict=verdict,
            notes=notes,
        )


class CharterpartyLaytimeEngine:
    """Laytime Calculation, Demurrage & Dispatch Performance Engine."""

    @staticmethod
    def calculate_laytime(
        charter_ref: str,
        vessel_name: str,
        total_allowed_laytime_hours: float,
        nor_tendered_hour: int,  # 0 to 23
        nor_tendered_iso: str,
        actual_working_hours: float,
        weather_delay_hours: float = 0.0,
        weekend_holiday_delay_hours: float = 0.0,
        laytime_term: LaytimeTerm = LaytimeTerm.WWD,
        demurrage_rate_per_day_usd: float = 12000.0,
        dispatch_rate_per_day_usd: Optional[float] = None,
    ) -> LaytimeDemurrageResult:
        if dispatch_rate_per_day_usd is None:
            # Statutory and industry standard: Dispatch = 50% Demurrage
            dispatch_rate_per_day_usd = round(demurrage_rate_per_day_usd * 0.5, 2)

        # NOR commencement rule:
        # If tendered <= 12:00, laytime commences at 13:00 same day
        # If tendered > 12:00, laytime commences at 08:00 next business day
        if nor_tendered_hour <= 12:
            commencement_note = f"{nor_tendered_iso[:10]} 13:00"
        else:
            commencement_note = f"{nor_tendered_iso[:10]} +1D 08:00"

        # Calculate counted laytime used:
        # Base hours spent
        base_hours = actual_working_hours

        # Under WWD, weather downtime is deducted from laytime counting
        # Under SHEX, weekend/holiday hours are deducted unless already on demurrage
        if laytime_term == LaytimeTerm.WWD:
            laytime_used_hours = max(0.0, base_hours - weather_delay_hours - weekend_holiday_delay_hours)
        elif laytime_term == LaytimeTerm.SHEX:
            laytime_used_hours = max(0.0, base_hours - weekend_holiday_delay_hours)
        else:  # SHINC
            laytime_used_hours = base_hours

        demurrage_hours = 0.0
        time_saved_hours = 0.0
        demurrage_payable_usd = 0.0
        dispatch_receivable_usd = 0.0

        if laytime_used_hours > total_allowed_laytime_hours:
            # Demurrage incurred
            demurrage_hours = round(laytime_used_hours - total_allowed_laytime_hours, 2)
            demurrage_days = demurrage_hours / 24.0
            demurrage_payable_usd = round(demurrage_days * demurrage_rate_per_day_usd, 2)
            net_charter_settlement_usd = demurrage_payable_usd
            settlement_party = "CHARTERER_OWES_DEMURRAGE"
            verdict = f"DEMURRAGE INCURRED: Charterer owes {demurrage_payable_usd:,.2f} USD ({demurrage_hours:.1f} hrs)"
        else:
            # Dispatch earned
            time_saved_hours = round(total_allowed_laytime_hours - laytime_used_hours, 2)
            dispatch_days = time_saved_hours / 24.0
            dispatch_receivable_usd = round(dispatch_days * dispatch_rate_per_day_usd, 2)
            net_charter_settlement_usd = -dispatch_receivable_usd
            settlement_party = "OWNER_OWES_DISPATCH"
            verdict = f"DISPATCH EARNED: Owner owes Charterer {dispatch_receivable_usd:,.2f} USD ({time_saved_hours:.1f} hrs saved)"

        return LaytimeDemurrageResult(
            charter_ref=charter_ref,
            vessel_name=vessel_name,
            laytime_term=laytime_term,
            total_allowed_laytime_hours=total_allowed_laytime_hours,
            nor_tendered_iso=nor_tendered_iso,
            laytime_commenced_iso=commencement_note,
            laytime_used_hours=round(laytime_used_hours, 2),
            time_saved_hours=time_saved_hours,
            demurrage_hours=demurrage_hours,
            demurrage_rate_per_day_usd=demurrage_rate_per_day_usd,
            dispatch_rate_per_day_usd=dispatch_rate_per_day_usd,
            demurrage_payable_usd=demurrage_payable_usd,
            dispatch_receivable_usd=dispatch_receivable_usd,
            net_charter_settlement_usd=net_charter_settlement_usd,
            settlement_party=settlement_party,
            verdict=verdict,
        )


class SeafarerMLCCompensationEngine:
    """Seafarer Wage, Overtime & Statutory Disability under VMC 2015 & MLC 2006."""

    @staticmethod
    def calculate_compensation(
        seafarer_name: str,
        rank: SeafarerRank,
        basic_monthly_wage_usd: float,
        normal_overtime_hours: float = 0.0,
        rest_day_overtime_hours: float = 0.0,
        holiday_overtime_hours: float = 0.0,
        months_of_service: float = 1.0,
        medical_treatment_cost_usd: float = 0.0,
        incapacity_months_during_treatment: float = 0.0,
        disability_degree: DisabilityDegree = DisabilityDegree.NONE,
    ) -> SeafarerCompensationAssessment:
        # Standard MLC working hours baseline: 8 hours/day, 48 hours/week (~208 hours/month)
        hourly_basic_rate = basic_monthly_wage_usd / 208.0

        # Overtime rates under VN Labor Code & Maritime practice:
        # Normal day OT: 150% (1.5x)
        # Rest day OT: 200% (2.0x)
        # Holiday OT: 300% (3.0x)
        normal_ot_pay = normal_overtime_hours * hourly_basic_rate * 1.5
        rest_ot_pay = rest_day_overtime_hours * hourly_basic_rate * 2.0
        holiday_ot_pay = holiday_overtime_hours * hourly_basic_rate * 3.0
        total_ot_pay = round(normal_ot_pay + rest_ot_pay + holiday_ot_pay, 2)

        calculated_monthly_wage_usd = round(basic_monthly_wage_usd + total_ot_pay, 2)

        # Paid Annual Leave (MLC Reg 2.4: min 2.5 calendar days per month of employment)
        leave_days_accrued = round(months_of_service * 2.5, 1)
        daily_basic_rate = basic_monthly_wage_usd / 30.0
        paid_leave_allowance_usd = round(leave_days_accrued * daily_basic_rate, 2)

        # Full wage maintenance during medical treatment (MLC Standard A4.2 / VMC Art. 63)
        # Up to maximum statutory ceiling (typically 12-16 weeks or 4 months full pay)
        capped_treatment_months = min(incapacity_months_during_treatment, 4.0)
        medical_wage_maintenance_usd = round(capped_treatment_months * basic_monthly_wage_usd, 2)

        # Statutory Disability & Fatality Indemnity under VMC Art. 63 & CBA:
        # - Temporary Partial: 2x monthly wage
        # - Permanent Partial < 50%: 12x monthly wage
        # - Permanent Severe 50%-80%: 24x monthly wage
        # - Permanent Total > 80%: 36x monthly wage
        # - Death / Fatality: 36x monthly wage (baseline CBA statutory minimum)
        disability_multipliers = {
            DisabilityDegree.TEMPORARY_PARTIAL: 2.0,
            DisabilityDegree.PERMANENT_PARTIAL_UNDER_50: 12.0,
            DisabilityDegree.PERMANENT_SEVERE_50_TO_80: 24.0,
            DisabilityDegree.PERMANENT_TOTAL_ABOVE_80: 36.0,
            DisabilityDegree.DEATH_FATALITY: 36.0,
            DisabilityDegree.NONE: 0.0,
        }
        multiplier = disability_multipliers[disability_degree]
        disability_compensation_usd = round(multiplier * basic_monthly_wage_usd, 2)

        total_statutory_liability_usd = round(
            calculated_monthly_wage_usd
            + paid_leave_allowance_usd
            + medical_treatment_cost_usd
            + medical_wage_maintenance_usd
            + disability_compensation_usd,
            2,
        )

        mlc_compliance_status = "COMPLIANT_WITH_MLC_2006_AND_VMC_2015"
        verdict = (
            f"SEAFARER REMUNERATION & INDEMNITY: Total Statutory Liability {total_statutory_liability_usd:,.2f} USD "
            f"(Basic/OT: {calculated_monthly_wage_usd:,.2f}, Disability: {disability_compensation_usd:,.2f})"
        )

        return SeafarerCompensationAssessment(
            seafarer_name=seafarer_name,
            rank=rank,
            basic_monthly_wage_usd=basic_monthly_wage_usd,
            normal_overtime_hours=normal_overtime_hours,
            rest_day_overtime_hours=rest_day_overtime_hours,
            holiday_overtime_hours=holiday_overtime_hours,
            calculated_monthly_wage_usd=calculated_monthly_wage_usd,
            leave_days_accrued=leave_days_accrued,
            paid_leave_allowance_usd=paid_leave_allowance_usd,
            medical_treatment_cost_usd=medical_treatment_cost_usd,
            medical_wage_maintenance_usd=medical_wage_maintenance_usd,
            disability_degree=disability_degree,
            disability_compensation_usd=disability_compensation_usd,
            total_statutory_liability_usd=total_statutory_liability_usd,
            mlc_compliance_status=mlc_compliance_status,
            verdict=verdict,
        )


class MarinePilotageAndTowageEngine:
    """Pilotage Liability & Maritime Towage Allocation under VMC 2015 Arts. 246-270."""

    @staticmethod
    def evaluate_liability(
        operation_id: str,
        vessel_name: str,
        pilotage_fee_collected_usd: float,
        total_marine_casualty_loss_usd: float,
        pilot_error_proven: bool = False,
        towage_type: TowageContractType = TowageContractType.PORT_ASSIST_BERTHING,
        command_authority: FlotillaCommandType = FlotillaCommandType.TOWED_VESSEL_MASTER_COMMAND,
    ) -> PilotageAndTowageAssessment:
        applicable_articles: List[str] = []

        # 1. Pilotage Liability:
        # VMC Art. 248: Pilot acts as navigational adviser; does not relieve Master of command.
        # VMC Art. 253: Pilotage organization liability is capped at the pilotage fee collected.
        applicable_articles.append("VMC Art. 248: Master remains in command of vessel navigation.")
        applicable_articles.append("VMC Art. 253: Pilotage entity liability strictly capped at service fee collected.")

        if pilot_error_proven:
            statutory_pilot_liability_usd = min(pilotage_fee_collected_usd, total_marine_casualty_loss_usd)
            master_navigation_liability_usd = round(total_marine_casualty_loss_usd - statutory_pilot_liability_usd, 2)
            pilot_verdict = f"Pilot error proven; liability capped at fee ({statutory_pilot_liability_usd:,.2f} USD). Master bears residual."
        else:
            statutory_pilot_liability_usd = 0.0
            master_navigation_liability_usd = total_marine_casualty_loss_usd
            pilot_verdict = "No pilot error; Master and Shipowner bear 100% navigation liability."

        # 2. Towage Allocation:
        # VMC Art. 263: Command of flotilla determines liability for casualty:
        # - If under towed vessel's Master: Towed vessel owner bears liability.
        # - If under Tug Master: Tugboat owner bears liability.
        applicable_articles.append("VMC Art. 263: Flotilla command authority dictates towage casualty apportionment.")

        if command_authority == FlotillaCommandType.TOWED_VESSEL_MASTER_COMMAND:
            towed_vessel_allocated_liability_usd = total_marine_casualty_loss_usd
            tug_allocated_liability_usd = 0.0
            tow_verdict = "Command was with Towed Vessel Master -> Towed vessel bears 100% towage liability."
        else:  # TUG_MASTER_COMMAND
            tug_allocated_liability_usd = total_marine_casualty_loss_usd
            towed_vessel_allocated_liability_usd = 0.0
            tow_verdict = "Command was with Tugboat Master -> Tugboat owner bears 100% towage liability."

        verdict = f"{pilot_verdict} | {tow_verdict}"

        return PilotageAndTowageAssessment(
            operation_id=operation_id,
            vessel_name=vessel_name,
            pilotage_fee_collected_usd=pilotage_fee_collected_usd,
            total_marine_casualty_loss_usd=total_marine_casualty_loss_usd,
            pilot_error_proven=pilot_error_proven,
            statutory_pilot_liability_usd=statutory_pilot_liability_usd,
            master_navigation_liability_usd=master_navigation_liability_usd,
            towage_type=towage_type,
            command_authority=command_authority,
            tug_allocated_liability_usd=tug_allocated_liability_usd,
            towed_vessel_allocated_liability_usd=towed_vessel_allocated_liability_usd,
            verdict=verdict,
            applicable_articles=applicable_articles,
        )
