"""Unified Facade for Maritime Phases 403-406.

Integrates:
- Phase 403: Marine Bilge Water Separator & ODMCS (MARPOL Annex I Reg 14 & 31, MEPC.107(49))
- Phase 404: Marine Inert Gas System (IGS) & N2 Membrane Generator (SOLAS II-2 Reg 4.5.5, IMO FSS Ch.15)
- Phase 405: Stern Tube Bearing Lubrication & Bio-oil Sealing (US VGP 2013, DNV Pt.4 Ch.4)
- Phase 406: High-Pressure Water Mist Fire Extinguishing (SOLAS II-2 Reg 10, IMO MSC/Circ.1165)

Strictly zero mocks, < 200 LOC.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.core.maritime.phase_403_bilge_water_separator_odmcs import (
    BilgeOdmcsAssessment,
    BilgeOdmcsTelemetry,
    BilgeWaterSeparatorOdmcsEngine,
    OdmcsDischargeStatus,
)
from src.core.maritime.phase_404_inert_gas_n2_generator import (
    IgsOperatingState,
    InertGasN2Assessment,
    InertGasN2GeneratorEngine,
    InertGasN2Telemetry,
)
from src.core.maritime.phase_405_stern_tube_bio_lubrication import (
    LubricationRegime,
    SternTubeAssessment,
    SternTubeBioLubricationEngine,
    SternTubeTelemetry,
)
from src.core.maritime.phase_406_water_mist_fire_extinguishing import (
    WaterMistAssessment,
    WaterMistFireExtinguishingEngine,
    WaterMistTelemetry,
)


@dataclass(frozen=True)
class MaritimeBilgeInertgasSterntubeWatermistTelemetry:
    """Aggregated telemetry inputs across all four auxiliary systems."""
    bilge: BilgeOdmcsTelemetry = field(default_factory=BilgeOdmcsTelemetry)
    inert_gas: InertGasN2Telemetry = field(default_factory=InertGasN2Telemetry)
    stern_tube: SternTubeTelemetry = field(default_factory=SternTubeTelemetry)
    water_mist: WaterMistTelemetry = field(default_factory=WaterMistTelemetry)


@dataclass
class MaritimeBilgeInertgasSterntubeWatermistResult:
    """Consolidated assessment of the 4 maritime auxiliary environmental & safety systems."""
    bilge_assessment: BilgeOdmcsAssessment
    inert_gas_assessment: InertGasN2Assessment
    stern_tube_assessment: SternTubeAssessment
    water_mist_assessment: WaterMistAssessment
    overall_system_status: str
    aggregated_warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_system_status,
            "bilge_separator_odmcs": {
                "status": self.bilge_assessment.status.value,
                "stokes_rising_velocity_m_s": self.bilge_assessment.stokes_rising_velocity_m_s,
                "coalescence_retention_efficiency_pct": self.bilge_assessment.coalescence_retention_efficiency_pct,
                "discharge_liters_per_nm": self.bilge_assessment.discharge_liters_per_nautical_mile,
                "asd_trip_activated": self.bilge_assessment.asd_trip_activated,
                "audit_checksum": self.bilge_assessment.audit_entry.tamper_proof_checksum,
                "compliance_flags": self.bilge_assessment.compliance_flags,
            },
            "inert_gas_n2_generator": {
                "state": self.inert_gas_assessment.state.value,
                "oxygen_content_pct": self.inert_gas_assessment.oxygen_content_pct,
                "permeation_flux_ratio": self.inert_gas_assessment.permeation_flux_ratio,
                "deck_pressure_mmwg": self.inert_gas_assessment.deck_pressure_mmwg,
                "pv_breaker_tripped": self.inert_gas_assessment.pv_breaker_tripped,
                "atmospheric_venting_active": self.inert_gas_assessment.atmospheric_venting_active,
                "compliance_flags": self.inert_gas_assessment.compliance_flags,
            },
            "stern_tube_bio_lubrication": {
                "regime": self.stern_tube_assessment.regime.value,
                "sommerfeld_number": self.stern_tube_assessment.sommerfeld_number,
                "film_parameter_lambda": self.stern_tube_assessment.film_parameter_lambda,
                "differential_seal_pressure_bar": self.stern_tube_assessment.differential_seal_pressure_bar,
                "oil_overpressure_adequate": self.stern_tube_assessment.oil_overpressure_adequate,
                "eal_health_status": self.stern_tube_assessment.eal_health_status,
                "compliance_flags": self.stern_tube_assessment.compliance_flags,
            },
            "water_mist_fire_extinguishing": {
                "mode": self.water_mist_assessment.mode.value,
                "total_flow_rate_lpm": self.water_mist_assessment.total_flow_rate_lpm,
                "latent_cooling_capacity_kw": self.water_mist_assessment.latent_cooling_capacity_kw,
                "steam_volume_ratio_pct": self.water_mist_assessment.steam_volume_ratio_pct,
                "estimated_depleted_o2_pct": self.water_mist_assessment.estimated_depleted_o2_pct,
                "adequate_water_storage": self.water_mist_assessment.adequate_water_storage,
                "extinguishment_assured": self.water_mist_assessment.extinguishment_assured,
                "compliance_flags": self.water_mist_assessment.compliance_flags,
            },
            "total_warnings": len(self.aggregated_warnings),
            "warnings": self.aggregated_warnings,
        }


class MaritimeBilgeInertgasSterntubeWatermistEngine:
    """Master facade for Maritime Phases 403-406."""

    def __init__(self) -> None:
        self.bilge_engine = BilgeWaterSeparatorOdmcsEngine()
        self.inert_gas_engine = InertGasN2GeneratorEngine()
        self.stern_tube_engine = SternTubeBioLubricationEngine()
        self.water_mist_engine = WaterMistFireExtinguishingEngine()

    def evaluate(
        self,
        telemetry: MaritimeBilgeInertgasSterntubeWatermistTelemetry,
    ) -> MaritimeBilgeInertgasSterntubeWatermistResult:
        bilge_res = self.bilge_engine.evaluate(telemetry.bilge)
        inert_gas_res = self.inert_gas_engine.evaluate(telemetry.inert_gas)
        stern_tube_res = self.stern_tube_engine.evaluate(telemetry.stern_tube)
        water_mist_res = self.water_mist_engine.evaluate(telemetry.water_mist)

        warnings: List[str] = []
        warnings.extend([f"Phase 403 (Bilge): {w}" for w in bilge_res.warnings])
        warnings.extend([f"Phase 404 (Inert Gas): {w}" for w in inert_gas_res.warnings])
        warnings.extend([f"Phase 405 (Stern Tube): {w}" for w in stern_tube_res.warnings])
        warnings.extend([f"Phase 406 (Water Mist): {w}" for w in water_mist_res.warnings])

        # Overall Status Determination
        is_critical = (
            bilge_res.status == OdmcsDischargeStatus.LOCKED_OUT
            or inert_gas_res.state == IgsOperatingState.O2_SAFETY_TRIP_VENTING
            or stern_tube_res.regime == LubricationRegime.BOUNDARY_LUBRICATION
            or not water_mist_res.adequate_water_storage
        )

        is_warning = (
            bilge_res.status in (OdmcsDischargeStatus.ALARM_WARNING, OdmcsDischargeStatus.RECIRCULATING_TRIP)
            or inert_gas_res.state in (IgsOperatingState.O2_HIGH_ALARM, IgsOperatingState.PRESSURE_SURGE_RELIEF)
            or stern_tube_res.regime == LubricationRegime.MIXED_LUBRICATION
            or len(warnings) > 0
        )

        if is_critical:
            overall_status = "CRITICAL_ATTENTION_REQUIRED"
        elif is_warning:
            overall_status = "WARNING_OPERATIONAL"
        else:
            overall_status = "OPTIMAL_OPERATIONAL"

        return MaritimeBilgeInertgasSterntubeWatermistResult(
            bilge_assessment=bilge_res,
            inert_gas_assessment=inert_gas_res,
            stern_tube_assessment=stern_tube_res,
            water_mist_assessment=water_mist_res,
            overall_system_status=overall_status,
            aggregated_warnings=warnings,
        )
