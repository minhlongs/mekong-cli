"""Maritime IMDG Segregation, Container D&D, Tugboat Dispatch, and Ship Chandler Suite.

Phases 307-310 Simplest Viable Maritime Operational Suite.
- Phase 307: IMDG Class Segregation Matrix Engine (IMDG Code Table 7.2.4)
- Phase 308: Container Demurrage & Detention (D&D) Tiered Calculator
- Phase 309: Tugboat Quota & Dispatch Assigner (Rule-based LOA/GRT)
- Phase 310: Ship Chandler Provision Quotation & Margin Engine
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from typing import Any, Dict, List, Optional


# ==============================================================================
# Phase 307: IMDG Class Segregation Matrix Engine
# ==============================================================================

class ImdgClass(str, Enum):
    CLASS_1_1 = "1.1"  # Explosives (Mass explosion)
    CLASS_2_1 = "2.1"  # Flammable gases
    CLASS_2_3 = "2.3"  # Toxic gases
    CLASS_3 = "3"      # Flammable liquids
    CLASS_4_1 = "4.1"  # Flammable solids
    CLASS_5_1 = "5.1"  # Oxidizing substances
    CLASS_5_2 = "5.2"  # Organic peroxides
    CLASS_6_1 = "6.1"  # Toxic substances
    CLASS_7 = "7"      # Radioactive material
    CLASS_8 = "8"      # Corrosives
    CLASS_9 = "9"      # Miscellaneous dangerous substances


class SegregationLevel(int, Enum):
    NONE = 0                 # X - No restriction
    AWAY_FROM = 1            # 1 - "Away from" (min 3m or 1 container space)
    SEPARATED_FROM = 2       # 2 - "Separated from" (min 6m or 1 bulkhead)
    SEPARATED_BY_COMPARTMENT = 3  # 3 - "Separated by a complete compartment or hold"
    SEPARATED_LONGITUDINALLY = 4  # 4 - "Separated longitudinally by intervening compartment"


@dataclass
class ImdgCheckResult:
    class_a: str
    class_b: str
    segregation_level: int
    segregation_label: str
    is_compatible: bool
    remarks: str
    audit_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_a": self.class_a,
            "class_b": self.class_b,
            "segregation_level": self.segregation_level,
            "segregation_label": self.segregation_label,
            "is_compatible": self.is_compatible,
            "remarks": self.remarks,
            "audit_hash": self.audit_hash,
        }


class ImdgSegregationEngine:
    """General Segregation Table 7.2.4 Simplest Viable Engine."""

    # Predefined rules: tuple (ClassA, ClassB) -> SegregationLevel
    # Symmetric lookup
    SEGREGATION_RULES: Dict[tuple[str, str], SegregationLevel] = {
        # Explosives vs others
        ("1.1", "2.1"): SegregationLevel.SEPARATED_LONGITUDINALLY,
        ("1.1", "3"): SegregationLevel.SEPARATED_LONGITUDINALLY,
        ("1.1", "5.1"): SegregationLevel.SEPARATED_LONGITUDINALLY,
        ("1.1", "5.2"): SegregationLevel.SEPARATED_LONGITUDINALLY,
        ("1.1", "8"): SegregationLevel.SEPARATED_LONGITUDINALLY,
        # Flammable Liquid (3) vs Oxidizers / Peroxides
        ("3", "5.1"): SegregationLevel.SEPARATED_FROM,
        ("3", "5.2"): SegregationLevel.SEPARATED_BY_COMPARTMENT,
        ("3", "8"): SegregationLevel.AWAY_FROM,
        # Oxidizers (5.1) vs Corrosives (8)
        ("5.1", "8"): SegregationLevel.SEPARATED_FROM,
        # Flammable Solids (4.1) vs Oxidizers (5.1)
        ("4.1", "5.1"): SegregationLevel.SEPARATED_FROM,
        # Peroxides (5.2) vs Corrosives (8)
        ("5.2", "8"): SegregationLevel.SEPARATED_BY_COMPARTMENT,
    }

    LABELS = {
        0: "X - Không giới hạn phân cách",
        1: "1 - Phân cách 'Away from' (tối thiểu 3m)",
        2: "2 - Phân cách 'Separated from' (tối thiểu 6m hoặc 1 vách ngăn)",
        3: "3 - Phân cách 'Separated by complete compartment' (ngăn riêng biệt)",
        4: "4 - Phân cách 'Separated longitudinally' (cách xa theo chiều dọc khoang tàu)",
    }

    @classmethod
    def evaluate_segregation(
        cls, class_a: str, class_b: str, is_acid_base_conflict: bool = False
    ) -> ImdgCheckResult:
        c_a = class_a.strip()
        c_b = class_b.strip()

        # Check special exception: Acid vs Base in Class 8
        if (c_a == "8" and c_b == "8") and is_acid_base_conflict:
            level = SegregationLevel.AWAY_FROM
            remarks = "CẢNH BÁO: Xung đột Axít & Kiềm (Cùng Class 8). Bắt buộc phân cách 'Away from'."
        else:
            # Query rules (symmetric)
            level = cls.SEGREGATION_RULES.get((c_a, c_b))
            if level is None:
                level = cls.SEGREGATION_RULES.get((c_b, c_a), SegregationLevel.NONE)

            if level == SegregationLevel.NONE:
                remarks = f"Hai nhóm nguy hiểm {c_a} và {c_b} có thể xếp gần nhau (không yêu cầu khoảng cách đặc biệt)."
            else:
                remarks = f"Yêu cầu mức phân cách Cấp {level.value}: {cls.LABELS[level.value]}."

        raw = f"{c_a}|{c_b}|{level.value}|{is_acid_base_conflict}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return ImdgCheckResult(
            class_a=c_a,
            class_b=c_b,
            segregation_level=level.value,
            segregation_label=cls.LABELS[level.value],
            is_compatible=(level.value <= 1),
            remarks=remarks,
            audit_hash=token,
        )


# ==============================================================================
# Phase 308: Container Demurrage & Detention (D&D) Calculator
# ==============================================================================

class ContainerType(str, Enum):
    DRY_20GP = "DRY_20GP"
    DRY_40GP = "DRY_40GP"
    REEFER_20RF = "REEFER_20RF"
    REEFER_40HR = "REEFER_40HR"


@dataclass
class DndTierRate:
    from_day: int
    to_day: Optional[int]  # None = infinity
    rate_usd_per_day: float


@dataclass
class DndCalculationInput:
    container_no: str
    container_type: ContainerType
    free_days_allowed: int
    actual_days_used: int
    is_detention: bool = False  # False = Demurrage (Port), True = Detention (Customer)
    vat_rate: float = 0.08      # 8% standard VAT in Vietnam


@dataclass
class DndCalculationResult:
    container_no: str
    charge_type: str
    free_days_allowed: int
    actual_days_used: int
    overdue_days: int
    subtotal_usd: float
    vat_usd: float
    total_amount_usd: float
    remarks: str
    invoice_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "container_no": self.container_no,
            "charge_type": self.charge_type,
            "free_days_allowed": self.free_days_allowed,
            "actual_days_used": self.actual_days_used,
            "overdue_days": self.overdue_days,
            "subtotal_usd": round(self.subtotal_usd, 2),
            "vat_usd": round(self.vat_usd, 2),
            "total_amount_usd": round(self.total_amount_usd, 2),
            "remarks": self.remarks,
            "invoice_hash": self.invoice_hash,
        }


class ContainerDndEngine:
    """Tiered Demurrage & Detention Calculator."""

    DEFAULT_TIERS: Dict[ContainerType, List[DndTierRate]] = {
        ContainerType.DRY_20GP: [
            DndTierRate(from_day=1, to_day=7, rate_usd_per_day=15.0),
            DndTierRate(from_day=8, to_day=15, rate_usd_per_day=25.0),
            DndTierRate(from_day=16, to_day=None, rate_usd_per_day=40.0),
        ],
        ContainerType.DRY_40GP: [
            DndTierRate(from_day=1, to_day=7, rate_usd_per_day=25.0),
            DndTierRate(from_day=8, to_day=15, rate_usd_per_day=45.0),
            DndTierRate(from_day=16, to_day=None, rate_usd_per_day=70.0),
        ],
        ContainerType.REEFER_20RF: [
            DndTierRate(from_day=1, to_day=3, rate_usd_per_day=40.0),
            DndTierRate(from_day=4, to_day=7, rate_usd_per_day=70.0),
            DndTierRate(from_day=8, to_day=None, rate_usd_per_day=120.0),
        ],
        ContainerType.REEFER_40HR: [
            DndTierRate(from_day=1, to_day=3, rate_usd_per_day=60.0),
            DndTierRate(from_day=4, to_day=7, rate_usd_per_day=110.0),
            DndTierRate(from_day=8, to_day=None, rate_usd_per_day=180.0),
        ],
    }

    @classmethod
    def calculate_dnd(cls, req: DndCalculationInput) -> DndCalculationResult:
        overdue_days = max(req.actual_days_used - req.free_days_allowed, 0)
        charge_name = "DETENTION" if req.is_detention else "DEMURRAGE"

        if overdue_days == 0:
            return DndCalculationResult(
                container_no=req.container_no,
                charge_type=charge_name,
                free_days_allowed=req.free_days_allowed,
                actual_days_used=req.actual_days_used,
                overdue_days=0,
                subtotal_usd=0.0,
                vat_usd=0.0,
                total_amount_usd=0.0,
                remarks=f"Container trong thời hạn miễn phí (Free time {req.free_days_allowed} ngày). Không phát sinh phí.",
                invoice_hash=hashlib.sha256(f"{req.container_no}|0|0".encode("utf-8")).hexdigest(),
            )

        tiers = cls.DEFAULT_TIERS.get(req.container_type, cls.DEFAULT_TIERS[ContainerType.DRY_20GP])
        subtotal = 0.0

        for day in range(1, overdue_days + 1):
            day_rate = 0.0
            for tier in tiers:
                if tier.to_day is None:
                    if day >= tier.from_day:
                        day_rate = tier.rate_usd_per_day
                        break
                elif tier.from_day <= day <= tier.to_day:
                    day_rate = tier.rate_usd_per_day
                    break
            subtotal += day_rate

        vat_amount = subtotal * req.vat_rate
        total_amount = subtotal + vat_amount

        remarks = (f"Phát sinh {overdue_days} ngày quá hạn {charge_name}. "
                   f"Tiền cước: ${subtotal:,.2f} USD + Thuế GTGT ({req.vat_rate * 100:.0f}%): ${vat_amount:,.2f} USD.")

        raw = f"{req.container_no}|{overdue_days}|{total_amount:.2f}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return DndCalculationResult(
            container_no=req.container_no,
            charge_type=charge_name,
            free_days_allowed=req.free_days_allowed,
            actual_days_used=req.actual_days_used,
            overdue_days=overdue_days,
            subtotal_usd=subtotal,
            vat_usd=vat_amount,
            total_amount_usd=total_amount,
            remarks=remarks,
            invoice_hash=token,
        )


# ==============================================================================
# Phase 309: Tugboat Quota & Dispatch Assigner
# ==============================================================================

@dataclass
class TugboatAsset:
    tug_id: str
    tug_name: str
    bhp: int              # Brake Horsepower
    bollard_pull_mt: float
    is_idle: bool = True


@dataclass
class TugDispatchResult:
    vessel_name: str
    vessel_loa_m: float
    vessel_grt: float
    required_tug_count: int
    required_min_bhp: int
    is_dispatched: bool
    assigned_tugs: List[str]
    estimated_cost_vnd: float
    remarks: str
    dispatch_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vessel_name": self.vessel_name,
            "vessel_loa_m": self.vessel_loa_m,
            "vessel_grt": self.vessel_grt,
            "required_tug_count": self.required_tug_count,
            "required_min_bhp": self.required_min_bhp,
            "is_dispatched": self.is_dispatched,
            "assigned_tugs": self.assigned_tugs,
            "estimated_cost_vnd": round(self.estimated_cost_vnd, 2),
            "remarks": self.remarks,
            "dispatch_hash": self.dispatch_hash,
        }


class TugboatDispatchEngine:
    """Port Maritime Authority Quota & Simple FIFO Dispatcher."""

    @classmethod
    def evaluate_and_dispatch(
        cls,
        vessel_name: str,
        loa_m: float,
        grt: float,
        fleet: List[TugboatAsset]
    ) -> TugDispatchResult:
        # Vietnam Port Authority Maritime Quota by LOA
        if loa_m < 80.0:
            req_count = 0
            req_bhp = 0
            base_cost = 0.0
        elif loa_m < 115.0:
            req_count = 1
            req_bhp = 1000
            base_cost = 15_000_000.0  # 15M VND
        elif loa_m < 150.0:
            req_count = 2
            req_bhp = 2000
            base_cost = 35_000_000.0  # 35M VND
        elif loa_m < 200.0:
            req_count = 2
            req_bhp = 3200
            base_cost = 55_000_000.0  # 55M VND
        else:
            req_count = 3
            req_bhp = 4000
            base_cost = 85_000_000.0  # 85M VND

        # Find eligible idle tugs
        eligible_tugs = [t for t in fleet if t.is_idle and t.bhp >= req_bhp]
        assigned = []

        if len(eligible_tugs) >= req_count:
            is_dispatched = True
            assigned = [t.tug_name for t in eligible_tugs[:req_count]]
            remarks = (f"Định mức Cảng vụ: Cần {req_count} tàu lai (Tối thiểu {req_bhp} BHP). "
                       f"Đã điều động thành công: {', '.join(assigned)}.")
        else:
            is_dispatched = False
            remarks = (f"THIẾU TÀU LAI: Cảng vụ yêu cầu {req_count} tàu lai (>= {req_bhp} BHP) "
                       f"nhưng chỉ có {len(eligible_tugs)} tàu khả dụng trong đội tàu.")

        raw = f"{vessel_name}|{loa_m}|{req_count}|{is_dispatched}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return TugDispatchResult(
            vessel_name=vessel_name,
            vessel_loa_m=loa_m,
            vessel_grt=grt,
            required_tug_count=req_count,
            required_min_bhp=req_bhp,
            is_dispatched=is_dispatched,
            assigned_tugs=assigned,
            estimated_cost_vnd=base_cost,
            remarks=remarks,
            dispatch_hash=token,
        )


# ==============================================================================
# Phase 310: Ship Chandler Provision Quotation & Margin Engine
# ==============================================================================

@dataclass
class ChandlerItem:
    item_code: str        # IMPA / ISSA code
    description: str
    unit: str
    quantity: float
    unit_cost_usd: float


@dataclass
class ChandlerQuotationResult:
    rfq_id: str
    vessel_name: str
    total_cost_usd: float
    total_revenue_usd: float
    gross_profit_usd: float
    margin_percentage: float
    total_revenue_vnd: float
    exchange_rate: float
    launch_boat_fee_usd: float
    line_items_count: int
    remarks: str
    quote_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rfq_id": self.rfq_id,
            "vessel_name": self.vessel_name,
            "total_cost_usd": round(self.total_cost_usd, 2),
            "total_revenue_usd": round(self.total_revenue_usd, 2),
            "gross_profit_usd": round(self.gross_profit_usd, 2),
            "margin_percentage": round(self.margin_percentage, 2),
            "total_revenue_vnd": round(self.total_revenue_vnd, 0),
            "exchange_rate": self.exchange_rate,
            "launch_boat_fee_usd": round(self.launch_boat_fee_usd, 2),
            "line_items_count": self.line_items_count,
            "remarks": self.remarks,
            "quote_hash": self.quote_hash,
        }


class ShipChandlerEngine:
    """Multi-currency Provision Costing and Quotation Engine."""

    @classmethod
    def calculate_quotation(
        cls,
        rfq_id: str,
        vessel_name: str,
        items: List[ChandlerItem],
        markup_ratio: float = 0.25,        # 25% gross margin target
        launch_boat_fee_usd: float = 150.0, # Ca-nô vận chuyển ra phao neo
        exchange_rate_usd_vnd: float = 25400.0
    ) -> ChandlerQuotationResult:
        total_items_cost = sum(item.quantity * item.unit_cost_usd for item in items)
        total_cost = total_items_cost + launch_boat_fee_usd

        # Revenue = Cost / (1 - markup_ratio)
        total_revenue_usd = total_cost / max(1.0 - markup_ratio, 0.01)
        gross_profit_usd = total_revenue_usd - total_cost
        actual_margin_pct = (gross_profit_usd / total_revenue_usd) * 100.0

        total_revenue_vnd = total_revenue_usd * exchange_rate_usd_vnd

        remarks = (f"Báo giá cung ứng cho tàu {vessel_name} ({len(items)} mặt hàng). "
                   f"Giá vốn: ${total_cost:,.2f} USD | Doanh thu: ${total_revenue_usd:,.2f} USD "
                   f"({total_revenue_vnd:,.0f} VND) | Biên LN: {actual_margin_pct:.1f}%.")

        raw = f"{rfq_id}|{vessel_name}|{total_revenue_usd:.2f}|{total_revenue_vnd:.0f}"
        token = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return ChandlerQuotationResult(
            rfq_id=rfq_id,
            vessel_name=vessel_name,
            total_cost_usd=total_cost,
            total_revenue_usd=total_revenue_usd,
            gross_profit_usd=gross_profit_usd,
            margin_percentage=actual_margin_pct,
            total_revenue_vnd=total_revenue_vnd,
            exchange_rate=exchange_rate_usd_vnd,
            launch_boat_fee_usd=launch_boat_fee_usd,
            line_items_count=len(items),
            remarks=remarks,
            quote_hash=token,
        )
