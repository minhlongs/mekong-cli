"""
Vietnamese Meteorology, Hydrology, Hydroelectric Reservoir Dam Safety & Natural Disaster Prevention Engine.
Implements statutory compliance under:
- Law on Natural Disaster Prevention and Control 2013 (Law 33/2013/QH13, amended by Law 60/2020/QH14)
- Law on Hydrometeorology 2015 (Law 90/2015/QH13)
- Decree 114/2018/ND-CP (Safety management of dams and water reservoirs)
- Decree 78/2021/ND-CP (Establishment and management of the Natural Disaster Prevention and Control Fund)
- Prime Minister Decision 18/2021/QD-TTg (Forecasting, warning and communication of natural disasters, disaster risk levels)
- Decree 03/2022/ND-CP (Administrative penalties in natural disaster prevention, irrigation, and dykes).

Pure Python standard-library-only engine with SQLite WAL persistence.
Compliant with tests/test_core_boundary.py AST invariant.
"""

from dataclasses import asdict, dataclass
import datetime
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
import uuid


# Statutory Dam Classifications under Decree 114/2018/ND-CP
DAM_CLASSES: Dict[str, Dict[str, Any]] = {
    "SPECIAL_IMPORTANT": {
        "class_name": "Đập, hồ chứa nước quan trọng đặc biệt",
        "description": "Dung tích toàn bộ >= 1 tỷ m3 hoặc hạ du là thành phố, khu đô thị trọng điểm quốc phòng, an ninh.",
        "inspection_cycle_years": 5,
        "monitoring_frequency": "Continuous Real-time Telemetry (SCADA)",
    },
    "LARGE": {
        "class_name": "Đập, hồ chứa nước lớn",
        "description": "Chiều cao đập >= 15m hoặc dung tích trữ từ 3 triệu m3 đến dưới 1 tỷ m3.",
        "inspection_cycle_years": 5,
        "monitoring_frequency": "Tự động đo mưa, mực nước, lưu lượng xả",
    },
    "MEDIUM": {
        "class_name": "Đập, hồ chứa nước vừa",
        "description": "Chiều cao đập từ 10m đến dưới 15m hoặc dung tích từ 500.000 m3 đến dưới 3 triệu m3.",
        "inspection_cycle_years": 7,
        "monitoring_frequency": "Đo đạc thủ công hoặc bán tự động định kỳ",
    },
    "SMALL": {
        "class_name": "Đập, hồ chứa nước nhỏ",
        "description": "Chiều cao đập dưới 10m và dung tích trữ dưới 500.000 m3.",
        "inspection_cycle_years": 10,
        "monitoring_frequency": "Kiểm tra hiện trường trước mùa mưa lũ",
    },
}

# Natural Disaster Risk Levels under Decision 18/2021/QD-TTg
DISASTER_RISK_LEVELS: Dict[int, Dict[str, Any]] = {
    1: {"name": "Cấp độ 1: Rủi ro thiên tai thấp (Nhỏ)", "color": "blue"},
    2: {"name": "Cấp độ 2: Rủi ro thiên tai trung bình", "color": "yellow"},
    3: {"name": "Cấp độ 3: Rủi ro thiên tai lớn (Nghiêm trọng)", "color": "orange"},
    4: {"name": "Cấp độ 4: Rủi ro thiên tai rất lớn (Đặc biệt nghiêm trọng)", "color": "red"},
    5: {"name": "Cấp độ 5: Thảm họa thiên tai quốc gia", "color": "purple"},
}


@dataclass
class ReservoirDamAudit:
    audit_id: str
    dam_name: str
    river_basin: str
    dam_height_m: float
    reservoir_capacity_m3: float
    downstream_population: int
    dam_classification: str
    is_safe: bool
    last_inspection_years_ago: int
    has_emergency_plan: bool
    automatic_monitoring: bool
    deficiencies: List[str]
    safety_rating: str
    created_at: str


@dataclass
class ReservoirFloodDischarge:
    discharge_id: str
    dam_name: str
    river_basin: str
    current_water_level_m: float
    flood_control_water_level_m: float
    inflow_rate_m3s: float
    discharge_rate_m3s: float
    advance_warning_hours: float
    siren_system_active: bool
    inter_reservoir_compliance: bool
    is_authorized: bool
    violations: List[str]
    alert_status: str
    created_at: str


@dataclass
class DisasterRiskAssessment:
    assessment_id: str
    event_name: str
    disaster_type: str
    affected_provinces_count: int
    wind_level_beaufort: int
    rainfall_24h_mm: float
    river_flood_level: int
    downstream_population_at_risk: int
    risk_level: int
    risk_level_name: str
    emergency_actions: List[str]
    created_at: str


@dataclass
class DisasterPreventionFundCalculation:
    calc_id: str
    enterprise_name: str
    total_capital_vnd: float
    employee_count: int
    enterprise_fee_vnd: float
    employee_fee_total_vnd: float
    total_contribution_vnd: float
    is_exempt: bool
    exemption_reason: Optional[str]
    created_at: str


class DisasterEngine:
    """
    Vietnamese Natural Disaster Prevention, Hydrology & Hydroelectric Reservoir Dam Safety Engine.
    Adheres strictly to pure Python standard library.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            mekong_dir = Path.home() / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(mekong_dir / "disaster.db")
        else:
            self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reservoir_dam_audits (
                    audit_id TEXT PRIMARY KEY,
                    dam_name TEXT NOT NULL,
                    river_basin TEXT NOT NULL,
                    dam_height_m REAL NOT NULL,
                    reservoir_capacity_m3 REAL NOT NULL,
                    downstream_population INTEGER NOT NULL,
                    dam_classification TEXT NOT NULL,
                    is_safe INTEGER NOT NULL,
                    last_inspection_years_ago INTEGER NOT NULL,
                    has_emergency_plan INTEGER NOT NULL,
                    automatic_monitoring INTEGER NOT NULL,
                    deficiencies_json TEXT NOT NULL,
                    safety_rating TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reservoir_flood_discharges (
                    discharge_id TEXT PRIMARY KEY,
                    dam_name TEXT NOT NULL,
                    river_basin TEXT NOT NULL,
                    current_water_level_m REAL NOT NULL,
                    flood_control_water_level_m REAL NOT NULL,
                    inflow_rate_m3s REAL NOT NULL,
                    discharge_rate_m3s REAL NOT NULL,
                    advance_warning_hours REAL NOT NULL,
                    siren_system_active INTEGER NOT NULL,
                    inter_reservoir_compliance INTEGER NOT NULL,
                    is_authorized INTEGER NOT NULL,
                    violations_json TEXT NOT NULL,
                    alert_status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS natural_disaster_risk_assessments (
                    assessment_id TEXT PRIMARY KEY,
                    event_name TEXT NOT NULL,
                    disaster_type TEXT NOT NULL,
                    affected_provinces_count INTEGER NOT NULL,
                    wind_level_beaufort INTEGER NOT NULL,
                    rainfall_24h_mm REAL NOT NULL,
                    river_flood_level INTEGER NOT NULL,
                    downstream_population_at_risk INTEGER NOT NULL,
                    risk_level INTEGER NOT NULL,
                    risk_level_name TEXT NOT NULL,
                    emergency_actions_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS disaster_prevention_fund_calculations (
                    calc_id TEXT PRIMARY KEY,
                    enterprise_name TEXT NOT NULL,
                    total_capital_vnd REAL NOT NULL,
                    employee_count INTEGER NOT NULL,
                    enterprise_fee_vnd REAL NOT NULL,
                    employee_fee_total_vnd REAL NOT NULL,
                    total_contribution_vnd REAL NOT NULL,
                    is_exempt INTEGER NOT NULL,
                    exemption_reason TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    def audit_reservoir_dam_safety(
        self,
        dam_name: str,
        river_basin: str = "Lưu vực Sông Hồng",
        dam_height_m: float = 85.0,
        reservoir_capacity_m3: float = 500_000_000.0,
        downstream_population: int = 50000,
        last_inspection_years_ago: int = 3,
        has_emergency_plan: bool = True,
        automatic_monitoring: bool = True,
    ) -> Dict[str, Any]:
        """
        Audits reservoir dam safety classification and operational compliance under Decree 114/2018/ND-CP.
        """
        audit_id = f"DAM-AUD-{uuid.uuid4().hex[:8].upper()}"
        deficiencies: List[str] = []

        # Determine classification
        if reservoir_capacity_m3 >= 1_000_000_000.0 or downstream_population >= 100_000:
            classification = "SPECIAL_IMPORTANT"
        elif dam_height_m >= 15.0 or (3_000_000.0 <= reservoir_capacity_m3 < 1_000_000_000.0):
            classification = "LARGE"
        elif (10.0 <= dam_height_m < 15.0) or (500_000.0 <= reservoir_capacity_m3 < 3_000_000.0):
            classification = "MEDIUM"
        else:
            classification = "SMALL"

        cycle_limit = DAM_CLASSES[classification]["inspection_cycle_years"]

        if last_inspection_years_ago > cycle_limit:
            deficiencies.append(
                f"Quá hạn kiểm định an toàn đập ({last_inspection_years_ago} năm > chu kỳ quy định {cycle_limit} năm theo Nghị định 114/2018/NĐ-CP)."
            )

        if not has_emergency_plan:
            deficiencies.append(
                "Chưa phê duyệt Phương án ứng phó với tình huống khẩn cấp cho vùng hạ du đập (Vi phạm Điều 23)."
            )

        if classification in ("SPECIAL_IMPORTANT", "LARGE") and not automatic_monitoring:
            deficiencies.append(
                "Đập lớn / đặc biệt quan trọng bắt buộc phải lắp đặt hệ thống quan trắc khí tượng thủy văn tự động và camera giám sát xả lũ."
            )

        is_safe = len(deficiencies) == 0
        if is_safe:
            safety_rating = "TIÊU CHUẨN AN TOÀN ĐẬP (APPROVED)"
        elif len(deficiencies) == 1:
            safety_rating = "CẢNH BÁO AN TOÀN - CẦN KHẮC PHỤC (WARNING)"
        else:
            safety_rating = "NGUY CƠ MẤT AN TOÀN ĐẬP CAO (UNSAFE)"

        record = ReservoirDamAudit(
            audit_id=audit_id,
            dam_name=dam_name,
            river_basin=river_basin,
            dam_height_m=dam_height_m,
            reservoir_capacity_m3=reservoir_capacity_m3,
            downstream_population=downstream_population,
            dam_classification=classification,
            is_safe=is_safe,
            last_inspection_years_ago=last_inspection_years_ago,
            has_emergency_plan=has_emergency_plan,
            automatic_monitoring=automatic_monitoring,
            deficiencies=deficiencies,
            safety_rating=safety_rating,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO reservoir_dam_audits
                (audit_id, dam_name, river_basin, dam_height_m, reservoir_capacity_m3,
                 downstream_population, dam_classification, is_safe, last_inspection_years_ago,
                 has_emergency_plan, automatic_monitoring, deficiencies_json, safety_rating, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.audit_id,
                    record.dam_name,
                    record.river_basin,
                    record.dam_height_m,
                    record.reservoir_capacity_m3,
                    record.downstream_population,
                    record.dam_classification,
                    1 if record.is_safe else 0,
                    record.last_inspection_years_ago,
                    1 if record.has_emergency_plan else 0,
                    1 if record.automatic_monitoring else 0,
                    json.dumps(record.deficiencies, ensure_ascii=False),
                    record.safety_rating,
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def simulate_reservoir_flood_discharge(
        self,
        dam_name: str,
        river_basin: str = "Lưu vực Sông Vu Gia - Thu Bồn",
        current_water_level_m: float = 115.5,
        flood_control_water_level_m: float = 114.0,
        inflow_rate_m3s: float = 2500.0,
        discharge_rate_m3s: float = 2200.0,
        advance_warning_hours: float = 4.5,
        siren_system_active: bool = True,
        inter_reservoir_compliance: bool = True,
    ) -> Dict[str, Any]:
        """
        Simulates and audits flood release operations under Inter-Reservoir Operating Procedures (Quy trình vận hành liên hồ chứa).
        Mandates:
        - Advance notification to downstream authorities >= 4.0 hours.
        - Operational audible siren and loudspeaker warning downstream.
        - Compliance with river basin inter-reservoir coordination orders.
        """
        discharge_id = f"FLD-DIS-{uuid.uuid4().hex[:8].upper()}"
        violations: List[str] = []

        if advance_warning_hours < 4.0:
            violations.append(
                f"Thời gian thông báo xả lũ ({advance_warning_hours} giờ) vi phạm quy định tối thiểu 04 giờ trước khi mở cửa xả (Nghị định 03/2022/NĐ-CP)."
            )

        if not siren_system_active:
            violations.append(
                "Chưa kích hoạt hệ thống còi báo động xả lũ và truyền thanh cảnh báo dân cư vùng hạ du."
            )

        if not inter_reservoir_compliance:
            violations.append(
                "Vi phạm lệnh vận hành điều tiết lũ của Ban Chỉ huy Phòng chống thiên tai lưu vực sông liên tỉnh."
            )

        if discharge_rate_m3s > (inflow_rate_m3s * 1.3) and current_water_level_m < flood_control_water_level_m:
            violations.append(
                "Lưu lượng xả vượt quá lưu lượng đến trong khi mực nước chưa đạt cao trình đón lũ (Xả lũ nhân tạo gây ngập hạ du)."
            )

        is_authorized = len(violations) == 0

        if not is_authorized:
            alert_status = "VIOLATION_EMERGENCY_HOLD (Vi phạm quy trình xả lũ - Đình chỉ hoặc xử phạt)"
        elif current_water_level_m > flood_control_water_level_m:
            alert_status = "AUTHORIZED_EMERGENCY_SPILLWAY (Được phép xả tràn khẩn cấp bảo đảm an toàn công trình)"
        else:
            alert_status = "AUTHORIZED_REGULAR_DISCHARGE (Vận hành điều tiết xả lũ hợp quy)"

        record = ReservoirFloodDischarge(
            discharge_id=discharge_id,
            dam_name=dam_name,
            river_basin=river_basin,
            current_water_level_m=current_water_level_m,
            flood_control_water_level_m=flood_control_water_level_m,
            inflow_rate_m3s=inflow_rate_m3s,
            discharge_rate_m3s=discharge_rate_m3s,
            advance_warning_hours=advance_warning_hours,
            siren_system_active=siren_system_active,
            inter_reservoir_compliance=inter_reservoir_compliance,
            is_authorized=is_authorized,
            violations=violations,
            alert_status=alert_status,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO reservoir_flood_discharges
                (discharge_id, dam_name, river_basin, current_water_level_m, flood_control_water_level_m,
                 inflow_rate_m3s, discharge_rate_m3s, advance_warning_hours, siren_system_active,
                 inter_reservoir_compliance, is_authorized, violations_json, alert_status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.discharge_id,
                    record.dam_name,
                    record.river_basin,
                    record.current_water_level_m,
                    record.flood_control_water_level_m,
                    record.inflow_rate_m3s,
                    record.discharge_rate_m3s,
                    record.advance_warning_hours,
                    1 if record.siren_system_active else 0,
                    1 if record.inter_reservoir_compliance else 0,
                    1 if record.is_authorized else 0,
                    json.dumps(record.violations, ensure_ascii=False),
                    record.alert_status,
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def assess_natural_disaster_risk(
        self,
        event_name: str,
        disaster_type: str = "TYPHOON",
        affected_provinces_count: int = 4,
        wind_level_beaufort: int = 12,
        rainfall_24h_mm: float = 350.0,
        river_flood_level: int = 3,
        downstream_population_at_risk: int = 120000,
    ) -> Dict[str, Any]:
        """
        Assesses natural disaster risk level (Levels 1 to 5) under Prime Minister Decision 18/2021/QD-TTg.
        Disaster types: TYPHOON, FLASH_FLOOD_LANDSLIDE, HISTORICAL_FLOOD, DROUGHT_SALTWATER, COLD_HEAT.
        """
        assessment_id = f"NAT-RSK-{uuid.uuid4().hex[:8].upper()}"

        d_type = disaster_type.upper()

        if wind_level_beaufort >= 16 or river_flood_level >= 4 or downstream_population_at_risk >= 300000:
            risk_level = 5  # Thảm họa quốc gia
        elif wind_level_beaufort >= 12 or rainfall_24h_mm >= 400.0 or river_flood_level == 3:
            risk_level = 4  # Rất lớn / Nghiêm trọng
        elif wind_level_beaufort >= 9 or rainfall_24h_mm >= 200.0 or river_flood_level == 2:
            risk_level = 3  # Lớn
        elif wind_level_beaufort >= 6 or rainfall_24h_mm >= 100.0 or river_flood_level == 1:
            risk_level = 2  # Trung bình
        else:
            risk_level = 1  # Nhỏ

        emergency_actions = [
            "Kích hoạt Ban Chỉ huy Phòng chống thiên tai & Tìm kiếm cứu nạn theo phương châm '4 tại chỗ'.",
            f"Di dời khẩn cấp {downstream_population_at_risk:,} người dân khỏi vùng trũng thấp, sạt lở nguy hiểm.",
            "Tổ chức cấm biển, kiểm đếm tàu thuyền, hướng dẫn neo đậu trú tránh an toàn.",
            "Hạ mực nước hồ chứa về cao trình đón lũ, vận hành trạm bơm tiêu úng bảo vệ lúa và hoa màu.",
        ]

        if risk_level >= 4:
            emergency_actions.insert(0, "BAN BỐ TÌNH TRẠNG KHẨN CẤP VỀ THIÊN TAI (CẤP THỦ TƯỚNG CHÍNH PHỦ).")

        level_info = DISASTER_RISK_LEVELS[risk_level]

        record = DisasterRiskAssessment(
            assessment_id=assessment_id,
            event_name=event_name,
            disaster_type=d_type,
            affected_provinces_count=affected_provinces_count,
            wind_level_beaufort=wind_level_beaufort,
            rainfall_24h_mm=rainfall_24h_mm,
            river_flood_level=river_flood_level,
            downstream_population_at_risk=downstream_population_at_risk,
            risk_level=risk_level,
            risk_level_name=level_info["name"],
            emergency_actions=emergency_actions,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO natural_disaster_risk_assessments
                (assessment_id, event_name, disaster_type, affected_provinces_count,
                 wind_level_beaufort, rainfall_24h_mm, river_flood_level, downstream_population_at_risk,
                 risk_level, risk_level_name, emergency_actions_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.assessment_id,
                    record.event_name,
                    record.disaster_type,
                    record.affected_provinces_count,
                    record.wind_level_beaufort,
                    record.rainfall_24h_mm,
                    record.river_flood_level,
                    record.downstream_population_at_risk,
                    record.risk_level,
                    record.risk_level_name,
                    json.dumps(record.emergency_actions, ensure_ascii=False),
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def calculate_disaster_prevention_fund(
        self,
        enterprise_name: str,
        total_capital_vnd: float = 20_000_000_000.0,
        employee_count: int = 50,
        is_exempt: bool = False,
        exemption_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculates mandatory Natural Disaster Prevention Fund contributions under Decree 78/2021/ND-CP.
        Mandates:
        - Enterprise rate: 0.02% (0.0002) of total assets/capital.
        - Enterprise cap: Min 500,000 VND, Max 100,000,000 VND (100M VND).
        - Employee rate: Standard statutory rate (approx 90,000 VND/person/year).
        """
        calc_id = f"FND-CAL-{uuid.uuid4().hex[:8].upper()}"

        if is_exempt:
            enterprise_fee = 0.0
            employee_fee_total = 0.0
            total_contrib = 0.0
            reason = exemption_reason or "Miễn đóng quỹ do doanh nghiệp bị thiệt hại bởi thiên tai dịch bệnh theo Điều 13."
        else:
            raw_enterprise_fee = total_capital_vnd * 0.0002
            enterprise_fee = max(500_000.0, min(100_000_000.0, raw_enterprise_fee))
            employee_fee_total = employee_count * 90_000.0
            total_contrib = enterprise_fee + employee_fee_total
            reason = None

        record = DisasterPreventionFundCalculation(
            calc_id=calc_id,
            enterprise_name=enterprise_name,
            total_capital_vnd=total_capital_vnd,
            employee_count=employee_count,
            enterprise_fee_vnd=enterprise_fee,
            employee_fee_total_vnd=employee_fee_total,
            total_contribution_vnd=total_contrib,
            is_exempt=is_exempt,
            exemption_reason=reason,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO disaster_prevention_fund_calculations
                (calc_id, enterprise_name, total_capital_vnd, employee_count, enterprise_fee_vnd,
                 employee_fee_total_vnd, total_contribution_vnd, is_exempt, exemption_reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.calc_id,
                    record.enterprise_name,
                    record.total_capital_vnd,
                    record.employee_count,
                    record.enterprise_fee_vnd,
                    record.employee_fee_total_vnd,
                    record.total_contribution_vnd,
                    1 if record.is_exempt else 0,
                    record.exemption_reason,
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def list_records(self, category: str = "all", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Lists stored records by category ('all', 'dams', 'discharges', 'risks', 'funds').
        """
        records: List[Dict[str, Any]] = []
        with self._get_connection() as conn:
            if category in ("all", "dams"):
                rows = conn.execute(
                    "SELECT * FROM reservoir_dam_audits ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "dam_audit"
                    d["deficiencies"] = json.loads(d["deficiencies_json"])
                    records.append(d)
            if category in ("all", "discharges"):
                rows = conn.execute(
                    "SELECT * FROM reservoir_flood_discharges ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "flood_discharge"
                    d["violations"] = json.loads(d["violations_json"])
                    records.append(d)
            if category in ("all", "risks"):
                rows = conn.execute(
                    "SELECT * FROM natural_disaster_risk_assessments ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "disaster_risk"
                    d["emergency_actions"] = json.loads(d["emergency_actions_json"])
                    records.append(d)
            if category in ("all", "funds"):
                rows = conn.execute(
                    "SELECT * FROM disaster_prevention_fund_calculations ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "fund_calculation"
                    records.append(d)
        return records

    def get_status(self) -> Dict[str, Any]:
        """
        Returns telemetry summary of dam safety, flood discharge simulations, disaster risks, and fund collections.
        """
        with self._get_connection() as conn:
            dam_count = conn.execute("SELECT COUNT(*) FROM reservoir_dam_audits").fetchone()[0]
            dam_safe = conn.execute(
                "SELECT COUNT(*) FROM reservoir_dam_audits WHERE is_safe = 1"
            ).fetchone()[0]
            fld_count = conn.execute("SELECT COUNT(*) FROM reservoir_flood_discharges").fetchone()[0]
            fld_auth = conn.execute(
                "SELECT COUNT(*) FROM reservoir_flood_discharges WHERE is_authorized = 1"
            ).fetchone()[0]
            rsk_count = conn.execute("SELECT COUNT(*) FROM natural_disaster_risk_assessments").fetchone()[0]
            fnd_total = conn.execute(
                "SELECT COALESCE(SUM(total_contribution_vnd), 0.0) FROM disaster_prevention_fund_calculations"
            ).fetchone()[0]

        return {
            "status": "operational",
            "regulatory_framework": "Law on Natural Disaster Prevention 2013/2020, Law on Hydrometeorology 2015, Decree 114/2018/ND-CP, Decree 78/2021/ND-CP",
            "coordinating_authority": "Ban Chỉ đạo Quốc gia về Phòng, chống thiên tai & Tổng cục Khí tượng Thủy văn",
            "total_reservoir_dams_audited": dam_count,
            "safe_reservoir_dams_count": dam_safe,
            "total_flood_discharges_monitored": fld_count,
            "compliant_flood_discharges": fld_auth,
            "disaster_risk_events_tracked": rsk_count,
            "total_disaster_fund_collected_vnd": fnd_total,
            "db_path": self.db_path,
        }
