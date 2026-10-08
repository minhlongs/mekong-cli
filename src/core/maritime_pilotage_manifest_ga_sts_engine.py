"""Maritime Pilotage Exemption, e-Manifest MLETR, General Average & STS Transshipment Engine.

Phases 235-238:
- Phase 235: Compulsory Maritime Pilotage Zones & Statutory Exemption Licensing (VMC 2015 Arts. 246-258, Decree 58/2017/NĐ-CP, Circular 39/2023/TT-BGTVT)
- Phase 236: Seaport Cargo Manifest Delivery, Electronic Bill of Lading (e-B/L) & Customs Tally Reconciliation (Decree 58/2017, Decree 59/2018, Circular 39/2018/TT-BTC, UNCITRAL MLETR)
- Phase 237: Marine Hull General Average (GA) Security, Lloyd's Average Bond & Contributory Values (VMC 2015 Arts. 290-302, York-Antwerp Rules 2016)
- Phase 238: Seaport Ship-to-Ship (STS) Transfer Operations & Offshore Petroleum Transshipment Safety (Decree 58/2017 Arts. 95-98, MARPOL Annex I Ch. 8, OCIMF/CDI)

Zero-external-dependency invariant: purely Python standard library.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import hashlib


# ===========================================================================
# Phase 235: Compulsory Maritime Pilotage Zones & Exemption Licensing
# ===========================================================================

class PilotageZoneType(str, Enum):
    COMPULSORY_INSHORE = "compulsory_inshore"
    COMPULSORY_ESTUARY = "compulsory_estuary"
    OPTIONAL_ANCHORAGE = "optional_anchorage"


class VesselTradeClass(str, Enum):
    INTERNATIONAL = "international"
    DOMESTIC = "domestic"


@dataclass
class PilotageExemptionCheckResult:
    is_exempt: bool
    requires_pilot: bool
    exemption_reason: str
    statutory_notes: List[str] = field(default_factory=list)


@dataclass
class PilotageTariffCalculation:
    base_tariff: float
    wait_hours: float
    standby_detention_fee: float
    cancellation_penalty: float
    total_tariff: float
    currency: str
    audit_hash: str


class MaritimePilotageEngine:
    """Evaluates pilotage zone compliance, master exemption licensing, and tariffs."""

    @staticmethod
    def check_pilotage_exemption(
        gross_tonnage: float,
        trade_class: VesselTradeClass,
        is_hazardous_bulk: bool = False,
        master_has_exemption_cert: bool = False,
        port_calls_last_12m: int = 0,
        zone_type: PilotageZoneType = PilotageZoneType.COMPULSORY_INSHORE,
    ) -> PilotageExemptionCheckResult:
        """Evaluate statutory pilotage exemption under VMC 2015 Art. 248 & Decree 58/2017."""
        notes = []

        if zone_type == PilotageZoneType.OPTIONAL_ANCHORAGE:
            return PilotageExemptionCheckResult(
                is_exempt=True,
                requires_pilot=False,
                exemption_reason="Optional pilotage zone (anchorage or non-compulsory fairway).",
                statutory_notes=["Pilotage is advisory/optional upon request of Master."],
            )

        # International vessels are strictly mandated to employ pilots
        if trade_class == VesselTradeClass.INTERNATIONAL:
            return PilotageExemptionCheckResult(
                is_exempt=False,
                requires_pilot=True,
                exemption_reason="International flag vessels must employ compulsory maritime pilots.",
                statutory_notes=["VMC 2015 Art. 248: All international vessels require certified pilots."],
            )

        # Domestic vessels carrying hazardous bulk
        if is_hazardous_bulk:
            return PilotageExemptionCheckResult(
                is_exempt=False,
                requires_pilot=True,
                exemption_reason="Vessels carrying dangerous goods/oil in bulk cannot be granted exemption.",
                statutory_notes=["Decree 58/2017: Mandatory pilotage for bulk hazardous cargo."],
            )

        # Domestic vessel under 2,000 GT
        if gross_tonnage < 2000.0:
            return PilotageExemptionCheckResult(
                is_exempt=True,
                requires_pilot=False,
                exemption_reason="Domestic vessel under 2,000 GT naturally exempt in designated channels.",
                statutory_notes=["VMC 2015 Art. 248 Clause 2: Domestic vessels < 2,000 GT exempt."],
            )

        # Domestic vessel >= 2,000 GT requires exemption certificate + minimum 10 calls in 12 months
        if master_has_exemption_cert and port_calls_last_12m >= 10:
            notes.append(f"Master certified for fairway with {port_calls_last_12m} calls in past 12 months.")
            return PilotageExemptionCheckResult(
                is_exempt=True,
                requires_pilot=False,
                exemption_reason="Master holds valid Pilotage Exemption Certificate with >= 10 port calls.",
                statutory_notes=notes,
            )

        if not master_has_exemption_cert:
            notes.append("Master lacks certified Fairway Pilotage Exemption Certificate.")
        if port_calls_last_12m < 10:
            notes.append(f"Insufficient port calls in past 12m ({port_calls_last_12m} < 10 required).")

        return PilotageExemptionCheckResult(
            is_exempt=False,
            requires_pilot=True,
            exemption_reason="Domestic vessel >= 2,000 GT without qualifying master exemption credentials.",
            statutory_notes=notes,
        )

    @staticmethod
    def calculate_pilotage_tariff(
        gross_tonnage: float,
        trade_class: VesselTradeClass,
        distance_nautical_miles: float = 10.0,
        idle_wait_hours: float = 0.0,
        cancellation_notice_hours: Optional[float] = None,
    ) -> PilotageTariffCalculation:
        """Calculate pilotage dues, standby detention, and cancellation penalties (Circular 39/2023)."""
        dist = max(distance_nautical_miles, 1.0)
        gt = max(gross_tonnage, 100.0)

        # Rates per GT-NM
        if trade_class == VesselTradeClass.INTERNATIONAL:
            currency = "USD"
            rate_per_gt_nm = 0.0035
            base_turn_min = 150.0
            wait_rate_per_hour = 20.0
        else:
            currency = "VND"
            rate_per_gt_nm = 30.0
            base_turn_min = 1000000.0
            wait_rate_per_hour = 300000.0

        calculated_base = gt * dist * rate_per_gt_nm
        base_tariff = max(calculated_base, base_turn_min)

        # Standby detention fee: first 1.0h is free of charge
        billable_wait_hours = max(0.0, idle_wait_hours - 1.0)
        standby_detention_fee = billable_wait_hours * wait_rate_per_hour

        # Cancellation fee: if cancelled < 2.0h before scheduled boarding, 100% of base minimum applies
        cancellation_penalty = 0.0
        if cancellation_notice_hours is not None and cancellation_notice_hours < 2.0:
            cancellation_penalty = base_turn_min

        total_tariff = base_tariff + standby_detention_fee + cancellation_penalty

        hasher = hashlib.sha256()
        payload = f"{gt}:{trade_class.value}:{dist}:{total_tariff}:{currency}"
        hasher.update(payload.encode("utf-8"))
        audit_hash = hasher.hexdigest()[:16]

        return PilotageTariffCalculation(
            base_tariff=round(base_tariff, 2),
            wait_hours=round(idle_wait_hours, 2),
            standby_detention_fee=round(standby_detention_fee, 2),
            cancellation_penalty=round(cancellation_penalty, 2),
            total_tariff=round(total_tariff, 2),
            currency=currency,
            audit_hash=audit_hash,
        )


# ===========================================================================
# Phase 236: Seaport Cargo Manifest Delivery & e-B/L MLETR Reconciliation
# ===========================================================================

class ManifestSubmissionStatus(str, Enum):
    ON_TIME = "on_time"
    LATE_SUBMISSION = "late_submission"
    NON_COMPLIANT = "non_compliant"


class CargoDiscrepancyType(str, Enum):
    MATCH = "match"
    SHORTAGE = "shortage"
    OVERAGE = "overage"


@dataclass
class AdvanceManifestCheckResult:
    is_compliant: bool
    status: ManifestSubmissionStatus
    hours_prior: float
    required_hours: float
    statutory_notes: List[str] = field(default_factory=list)


@dataclass
class TallyReconciliationResult:
    is_matched: bool
    manifest_qty: float
    tally_qty: float
    discrepancy_qty: float
    discrepancy_pct: float
    discrepancy_type: CargoDiscrepancyType
    requires_customs_amendment: bool
    statutory_warning: Optional[str] = None


@dataclass
class MLETRControlRecord:
    bl_number: str
    carrier: str
    shipper: str
    consignee: str
    current_holder: str
    is_valid_transfer: bool
    mletr_token: str
    previous_hash: str


class CargoManifestMletrEngine:
    """e-Manifest advance submission, tally reconciliation, and MLETR e-B/L governance."""

    @staticmethod
    def check_advance_manifest(
        hours_before_arrival: float,
        is_short_sea_shipping: bool = False,
    ) -> AdvanceManifestCheckResult:
        """Validate advance electronic cargo manifest timeline under Decree 58/2017 & Decree 59/2018."""
        # Standard international voyage requires >= 24h; short sea (< 500 NM) allows >= 12h
        required_hours = 12.0 if is_short_sea_shipping else 24.0
        notes = []

        if hours_before_arrival >= required_hours:
            status = ManifestSubmissionStatus.ON_TIME
            is_compliant = True
            notes.append(f"Manifest submitted {hours_before_arrival:.1f}h prior to ETA (>= {required_hours:.1f}h).")
        elif hours_before_arrival > 0:
            status = ManifestSubmissionStatus.LATE_SUBMISSION
            is_compliant = False
            notes.append(
                f"Late submission: {hours_before_arrival:.1f}h prior to ETA. "
                f"Statutory minimum is {required_hours:.1f}h. Subject to customs administrative penalty."
            )
        else:
            status = ManifestSubmissionStatus.NON_COMPLIANT
            is_compliant = False
            notes.append("Manifest submitted after arrival or missing. Critical border customs violation.")

        return AdvanceManifestCheckResult(
            is_compliant=is_compliant,
            status=status,
            hours_prior=hours_before_arrival,
            required_hours=required_hours,
            statutory_notes=notes,
        )

    @staticmethod
    def reconcile_manifest_vs_tally(
        manifest_qty: float,
        tally_qty: float,
        customs_tolerance_pct: float = 0.5,
    ) -> TallyReconciliationResult:
        """Reconcile discharged tally cargo against manifested quantities (Circular 39/2018/TT-BTC)."""
        discrepancy_qty = round(tally_qty - manifest_qty, 3)

        if manifest_qty <= 0:
            return TallyReconciliationResult(
                is_matched=False,
                manifest_qty=manifest_qty,
                tally_qty=tally_qty,
                discrepancy_qty=discrepancy_qty,
                discrepancy_pct=100.0,
                discrepancy_type=CargoDiscrepancyType.OVERAGE,
                requires_customs_amendment=True,
                statutory_warning="Zero or negative manifested cargo quantity.",
            )

        discrepancy_pct = round(abs(discrepancy_qty) / manifest_qty * 100.0, 3)

        if abs(discrepancy_qty) < 1e-4:
            disc_type = CargoDiscrepancyType.MATCH
        elif discrepancy_qty < 0:
            disc_type = CargoDiscrepancyType.SHORTAGE
        else:
            disc_type = CargoDiscrepancyType.OVERAGE

        # Threshold for formal customs amendment (typically 0.5%)
        requires_amendment = discrepancy_pct > customs_tolerance_pct
        warning = None
        if requires_amendment:
            warning = (
                f"Discrepancy of {discrepancy_pct:.2f}% exceeds {customs_tolerance_pct}% allowance. "
                "Carrier/agent must file e-Manifest amendment under Circular 39/2018/TT-BTC."
            )

        return TallyReconciliationResult(
            is_matched=not requires_amendment,
            manifest_qty=manifest_qty,
            tally_qty=tally_qty,
            discrepancy_qty=discrepancy_qty,
            discrepancy_pct=discrepancy_pct,
            discrepancy_type=disc_type,
            requires_customs_amendment=requires_amendment,
            statutory_warning=warning,
        )

    @staticmethod
    def issue_or_transfer_mletr_ebl(
        bl_number: str,
        carrier: str,
        shipper: str,
        consignee: str,
        new_holder: str,
        previous_token: str = "0" * 64,
    ) -> MLETRControlRecord:
        """Generate singular cryptographic electronic Bill of Lading token under UNCITRAL MLETR."""
        payload = f"{bl_number}:{carrier}:{shipper}:{consignee}:{new_holder}:{previous_token}"
        token = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        is_valid = len(new_holder.strip()) > 0 and len(bl_number.strip()) > 0

        return MLETRControlRecord(
            bl_number=bl_number,
            carrier=carrier,
            shipper=shipper,
            consignee=consignee,
            current_holder=new_holder,
            is_valid_transfer=is_valid,
            mletr_token=token,
            previous_hash=previous_token,
        )


# ===========================================================================
# Phase 237: Marine Hull General Average (GA) Security & Adjusting
# ===========================================================================

@dataclass
class ContributoryValues:
    ship_value: float
    cargo_value: float
    freight_value: float
    total_contributory_value: float


@dataclass
class GAAdjustmentResult:
    total_ga_sacrifice_expenditure: float
    total_contributory_value: float
    ga_rate_pct: float
    ship_contribution: float
    cargo_contribution: float
    freight_contribution: float
    cash_deposit_required: float
    commission_allowance: float
    interest_allowance: float
    adjustment_hash: str


class GeneralAverageAdjustingEngine:
    """Computes York-Antwerp Rules 2016 and VMC 2015 General Average adjustment and security deposits."""

    @staticmethod
    def calculate_contributory_values(
        ship_sound_value: float,
        ship_non_ga_damage: float,
        cargo_cif_value: float,
        cargo_damage_loss: float,
        cargo_landing_charges: float,
        freight_at_risk: float,
        freight_post_ga_expenses: float,
    ) -> ContributoryValues:
        """Calculate net contributory values of ship, cargo, and freight at common destination."""
        cv_ship = max(0.0, ship_sound_value - ship_non_ga_damage)
        cv_cargo = max(0.0, cargo_cif_value - cargo_damage_loss - cargo_landing_charges)
        cv_freight = max(0.0, freight_at_risk - freight_post_ga_expenses)
        cv_total = cv_ship + cv_cargo + cv_freight

        return ContributoryValues(
            ship_value=round(cv_ship, 2),
            cargo_value=round(cv_cargo, 2),
            freight_value=round(cv_freight, 2),
            total_contributory_value=round(cv_total, 2),
        )

    @staticmethod
    def adjust_general_average(
        ga_sacrifices: float,
        ga_cash_disbursements: float,
        contributory_values: ContributoryValues,
        adjustment_days: int = 180,
    ) -> GAAdjustmentResult:
        """Applies York-Antwerp Rules 2016 Rule XX (2% commission) and Rule XXI (7% p.a. interest)."""
        # Rule XX: 2% commission on cash disbursements (other than crew wages/maintenance)
        commission = ga_cash_disbursements * 0.02

        # Rule XXI: 7% per annum interest on expenditure, sacrifices, and allowances until adjustment date
        base_subject_to_interest = ga_sacrifices + ga_cash_disbursements + commission
        interest = base_subject_to_interest * 0.07 * (adjustment_days / 365.0)

        total_ga_claim = base_subject_to_interest + interest

        total_cv = contributory_values.total_contributory_value
        if total_cv <= 0:
            ga_rate = 0.0
            ship_contrib = 0.0
            cargo_contrib = 0.0
            freight_contrib = 0.0
        else:
            ga_rate = (total_ga_claim / total_cv) * 100.0
            ship_contrib = contributory_values.ship_value * (ga_rate / 100.0)
            cargo_contrib = contributory_values.cargo_value * (ga_rate / 100.0)
            freight_contrib = contributory_values.freight_value * (ga_rate / 100.0)

        # Average Guarantee Cash Deposit: typically cargo's expected contribution + 15% safety margin
        cash_deposit = cargo_contrib * 1.15

        hasher = hashlib.sha256()
        payload = f"{total_ga_claim}:{total_cv}:{ga_rate}:{cash_deposit}"
        hasher.update(payload.encode("utf-8"))
        adj_hash = hasher.hexdigest()[:16]

        return GAAdjustmentResult(
            total_ga_sacrifice_expenditure=round(total_ga_claim, 2),
            total_contributory_value=round(total_cv, 2),
            ga_rate_pct=round(ga_rate, 4),
            ship_contribution=round(ship_contrib, 2),
            cargo_contribution=round(cargo_contrib, 2),
            freight_contribution=round(freight_contrib, 2),
            cash_deposit_required=round(cash_deposit, 2),
            commission_allowance=round(commission, 2),
            interest_allowance=round(interest, 2),
            adjustment_hash=adj_hash,
        )


# ===========================================================================
# Phase 238: Seaport Ship-to-Ship (STS) Transfer & Offshore Petroleum Safety
# ===========================================================================

@dataclass
class STSKineticEnergyResult:
    berthing_energy_kNm: float
    virtual_mass_tonnes: float
    fender_standoff_meters: float
    is_fender_adequate: bool


@dataclass
class STSSafetyEvaluation:
    is_safe_to_operate: bool
    weather_abort: bool
    inert_gas_safe: bool
    electrical_bonding_safe: bool
    boom_circumference_adequate: bool
    violations: List[str] = field(default_factory=list)
    sts_clearance_hash: str = ""


class ShipToShipTransferEngine:
    """Evaluates offshore Ship-to-Ship (STS) transfer kinetic berthing energy and MARPOL safety envelope."""

    @staticmethod
    def calculate_berthing_energy(
        displacement_tonnes: float,
        draft_meters: float,
        beam_meters: float,
        approach_velocity_mps: float = 0.15,
        eccentricity_coef: float = 0.5,
        softness_coef: float = 0.9,
        configuration_coef: float = 0.9,
        fender_rated_energy_kNm: float = 350.0,
        fender_standoff_distance_meters: float = 3.5,
    ) -> STSKineticEnergyResult:
        """Calculate hydrodynamic virtual mass and fender absorption energy (PIANC / OCIMF guidelines)."""
        disp = max(displacement_tonnes, 100.0)
        draft = max(draft_meters, 1.0)
        beam = max(beam_meters, 1.0)
        v = max(approach_velocity_mps, 0.01)

        # Hydrodynamic added mass coefficient Cm = 1 + 2 * (D / B)
        cm = 1.0 + (2.0 * draft / beam)
        virtual_mass = disp * cm

        # Berthing kinetic energy E = 0.5 * M * v^2 * Ce * Cs * Cc
        energy_kNm = 0.5 * virtual_mass * (v ** 2) * eccentricity_coef * softness_coef * configuration_coef

        # Adequate if fender rated absorption >= berthing energy and standoff >= 3.0m
        is_adequate = (energy_kNm <= fender_rated_energy_kNm) and (fender_standoff_distance_meters >= 3.0)

        return STSKineticEnergyResult(
            berthing_energy_kNm=round(energy_kNm, 2),
            virtual_mass_tonnes=round(virtual_mass, 2),
            fender_standoff_meters=round(fender_standoff_distance_meters, 2),
            is_fender_adequate=is_adequate,
        )

    @staticmethod
    def evaluate_sts_safety(
        wind_speed_mps: float,
        significant_wave_height_meters: float,
        lightning_distance_nm: Optional[float] = None,
        inert_gas_oxygen_pct: float = 5.0,
        bonding_resistance_ohms: float = 500.0,
        oil_boom_circumference_meters: float = 400.0,
        vessel_a_loa_meters: float = 180.0,
        vessel_b_loa_meters: float = 120.0,
    ) -> STSSafetyEvaluation:
        """Evaluate meteorological abort limits, vapor inert gas, and secondary boom containment."""
        violations = []
        weather_abort = False

        # 1. Weather abort limits (Beaufort 6 / 12 m/s, Wave 1.5m, Lightning within 5.0 NM)
        if wind_speed_mps > 12.0:
            weather_abort = True
            violations.append(f"Wind speed {wind_speed_mps} m/s exceeds statutory STS limit of 12.0 m/s.")

        if significant_wave_height_meters > 1.5:
            weather_abort = True
            violations.append(
                f"Significant wave height {significant_wave_height_meters}m exceeds statutory limit of 1.5m."
            )

        if lightning_distance_nm is not None and lightning_distance_nm <= 5.0:
            weather_abort = True
            violations.append(
                f"Thunderstorm/lightning detected at {lightning_distance_nm} NM (<= 5.0 NM safety buffer)."
            )

        # 2. Inert gas safety (O2 <= 8.0% by volume)
        inert_gas_safe = inert_gas_oxygen_pct <= 8.0
        if not inert_gas_safe:
            violations.append(
                f"Inert gas oxygen content {inert_gas_oxygen_pct}% exceeds 8.0% explosive limit."
            )

        # 3. Grounding & electrical bonding continuity (Resistance <= 1,000,000 Ohms)
        electrical_bonding_safe = bonding_resistance_ohms <= 1000000.0
        if not electrical_bonding_safe:
            violations.append(
                f"Electrical bonding resistance {bonding_resistance_ohms} Ohms exceeds 1,000,000 Ohm threshold."
            )

        # 4. Secondary containment oil boom circumference (>= 1.5 * max(LOA_A, LOA_B))
        max_loa = max(vessel_a_loa_meters, vessel_b_loa_meters)
        min_boom = 1.5 * max_loa
        boom_adequate = oil_boom_circumference_meters >= min_boom
        if not boom_adequate:
            violations.append(
                f"Oil boom circumference {oil_boom_circumference_meters}m is below required {min_boom}m."
            )

        is_safe = (not weather_abort) and inert_gas_safe and electrical_bonding_safe and boom_adequate

        token_raw = f"{wind_speed_mps}:{significant_wave_height_meters}:{inert_gas_oxygen_pct}:{is_safe}"
        clearance_hash = hashlib.sha256(token_raw.encode("utf-8")).hexdigest()[:16]

        return STSSafetyEvaluation(
            is_safe_to_operate=is_safe,
            weather_abort=weather_abort,
            inert_gas_safe=inert_gas_safe,
            electrical_bonding_safe=electrical_bonding_safe,
            boom_circumference_adequate=boom_adequate,
            violations=violations,
            sts_clearance_hash=clearance_hash,
        )
