"""Maritime MLC, Bunkering, Shore Power, and Customs VASSCM Suite (Phases 303-306)."""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Dict, List


class CrewRole(str, Enum):
    CAPTAIN = "CAPTAIN"
    OFFICER = "OFFICER"
    RATING = "RATING"
    PASSENGER = "PASSENGER"


@dataclass
class CrewMember:
    crew_id: str
    full_name: str
    role: CrewRole
    nationality: str
    medical_fitness_expiry: str  # YYYY-MM-DD
    contract_active: bool


@dataclass
class CrewClearanceResult:
    vessel_name: str
    is_cleared: bool
    total_crew: int
    unfit_crew_ids: List[str]
    remarks: str
    clearance_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vessel_name": self.vessel_name, "is_cleared": self.is_cleared,
            "total_crew": self.total_crew, "unfit_crew_ids": self.unfit_crew_ids,
            "remarks": self.remarks, "clearance_hash": self.clearance_hash,
        }


class MlcCrewEngine:
    """Simplest Viable Crew Clearance based on IMO FAL Form 5 & Medical Fitness."""

    @classmethod
    def evaluate_clearance(cls, vessel_name: str, crew_list: List[CrewMember], current_date: str) -> CrewClearanceResult:
        unfit_crew = [c.crew_id for c in crew_list if not c.contract_active or c.medical_fitness_expiry < current_date]
        is_cleared = len(unfit_crew) == 0
        if is_cleared:
            remarks = "Toàn bộ thuyền viên hợp lệ (Hợp đồng & Y tế). Cấp phép IMO FAL Form 5."
        else:
            remarks = f"CẢNH BÁO: Phát hiện {len(unfit_crew)} thuyền viên hết hạn hợp đồng hoặc chứng nhận y tế."
        raw = f"{vessel_name}|{is_cleared}|{len(crew_list)}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return CrewClearanceResult(vessel_name, is_cleared, len(crew_list), unfit_crew, remarks, token)


@dataclass
class BdnInput:
    bdn_id: str
    vessel_name: str
    fuel_type: str
    volume_cubic_meters: float
    density_kg_m3: float
    temperature_celsius: float
    env_tax_rate_vnd_per_mt: float = 1000.0


@dataclass
class BunkeringResult:
    bdn_id: str
    metric_tons: float
    env_tax_vnd: float
    remarks: str
    audit_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bdn_id": self.bdn_id, "metric_tons": round(self.metric_tons, 2),
            "env_tax_vnd": round(self.env_tax_vnd, 2), "remarks": self.remarks, "audit_hash": self.audit_hash,
        }


class BunkeringEngine:
    """Calculates Metric Tons from BDN volume and applies Tax based on ASTM concepts."""

    @classmethod
    def calculate_bunker_delivery(cls, bdn: BdnInput) -> BunkeringResult:
        vcf = 1.0 - (bdn.temperature_celsius - 15.0) * 0.00064
        metric_tons = (bdn.volume_cubic_meters * vcf * bdn.density_kg_m3) / 1000.0
        env_tax = metric_tons * bdn.env_tax_rate_vnd_per_mt
        remarks = f"VCF: {vcf:.4f}. Tổng {metric_tons:.2f} MT dầu. Thuế BVMT: {env_tax:,.0f} VND."
        raw = f"{bdn.bdn_id}|{metric_tons:.2f}|{env_tax:.2f}"
        return BunkeringResult(bdn.bdn_id, metric_tons, env_tax, remarks, hashlib.sha256(raw.encode("utf-8")).hexdigest())


@dataclass
class ShorePowerConnection:
    connection_id: str
    vessel_name: str
    kwh_start: float
    kwh_stop: float
    rate_usd_per_kwh: float
    connection_fee_usd: float = 50.0


@dataclass
class ShorePowerResult:
    connection_id: str
    total_kwh: float
    energy_cost_usd: float
    total_invoice_usd: float
    remarks: str
    billing_hash: str


class ShorePowerEngine:
    """Calculates Shore Power (Cold Ironing) consumption and cost."""

    @classmethod
    def calculate_billing(cls, conn: ShorePowerConnection) -> ShorePowerResult:
        total_kwh = max(conn.kwh_stop - conn.kwh_start, 0.0)
        energy_cost = total_kwh * conn.rate_usd_per_kwh
        total_usd = energy_cost + conn.connection_fee_usd
        remarks = f"Tiêu thụ {total_kwh:.1f} kWh. Phí kết nối cố định: ${conn.connection_fee_usd:.2f}."
        raw = f"{conn.connection_id}|{total_kwh:.1f}|{total_usd:.2f}"
        return ShorePowerResult(
            conn.connection_id, total_kwh, energy_cost, total_usd, remarks,
            hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        )


@dataclass
class ManifestItem:
    bill_of_lading: str
    container_no: str
    seal_no: str
    gross_weight_kg: float
    hs_code: str


@dataclass
class VasscmPayloadResult:
    vessel_name: str
    json_payload: str
    total_containers: int
    is_valid: bool
    remarks: str


class CustomsVasscmEngine:
    """Converts internal manifest to VASSCM JSON schema without implementing full EDIFACT."""

    @classmethod
    def generate_vasscm_payload(cls, vessel_name: str, voyage_no: str, port_code: str, items: List[ManifestItem]) -> VasscmPayloadResult:
        if not items:
            return VasscmPayloadResult(vessel_name, "{}", 0, False, "Manifest rỗng, không thể truyền VASSCM.")
        containers = [
            {"BL": i.bill_of_lading, "ContainerNumber": i.container_no, "Seal": i.seal_no, "WeightKg": i.gross_weight_kg, "HSCode": i.hs_code}
            for i in items
        ]
        payload = {"Declaration": {"Vessel": vessel_name, "Voyage": voyage_no, "PortOfDischarge": port_code, "Containers": containers}}
        remarks = f"Đã sinh payload VASSCM (JSON) cho {len(items)} containers. Bỏ qua EDIFACT phức tạp."
        return VasscmPayloadResult(vessel_name, json.dumps(payload, ensure_ascii=False), len(items), True, remarks)
