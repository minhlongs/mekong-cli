"""
Vietnamese National Defense Industry, Security Export Controls & Industrial Mobilization Engine (Phase 100).
Implements statutory compliance under:
- Law on National Defense and Security Industry and Industrial Mobilization 2024 (Law 38/2024/QH15)
- Law on National Defense 2018 (Law 22/2018/QH14)
- Decrees on Strategic Dual-Use Technology and Security Export Controls (Hàng hóa lưỡng dụng & Giấy phép EUC)
- Regulations on Military Technical Standards (TCVN/QS & TCVN/AN).

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


# Statutory minimum strategic material stock days for industrial mobilization (Article 47 Law 38/2024/QH15)
STATUTORY_MIN_MOBILIZATION_STOCK_DAYS = 90

# Strategic dual-use items classification categories
STRATEGIC_DUAL_USE_CATEGORIES = {
    "DU_SEMI_MIL": "Linh kiện vi cơ điện tử bán dẫn & vi mạch cấp quân sự",
    "DU_TITANIUM_AERO": "Hợp kim Titan và sợi Carbon siêu nhẹ cấp hàng không - vũ trụ",
    "DU_CRYPTO_SEC": "Thiết bị mã hóa mật mã học và bảo mật truyền tin chuyên dụng",
    "DU_OPTICS_NIGHT": "Cảm biến quang điện tử hồng ngoại quan sát đêm và chỉ thị laser",
    "DU_UAV_AVIONICS": "Hệ thống điện tử hàng không (Avionics) và dẫn đường tự động UAV",
}


@dataclass
class DefenseFacilityLicense:
    license_id: str
    facility_name: str
    entity_type: str            # STATE_OWNED_DEFENSE_ENTERPRISE, DESIGNATED_PRIVATE_CONTRACTOR
    product_category: str       # WEAPONS_AMMUNITION, MILITARY_VEHICLES_UAV, CYBER_WARFARE_SYSTEMS, SPECIAL_EQUIPMENT
    state_secrets_clearance: str # TOP_SECRET, SECRET, CONFIDENTIAL
    personnel_security_cleared: bool
    perimeter_defense_and_pccc: bool
    hazardous_waste_clearance: bool
    is_approved: bool
    deficiencies: List[str]
    valid_until: str
    created_at: str


@dataclass
class DualUseExportControlRecord:
    control_id: str
    item_name: str
    dual_use_code: str
    quantity: int
    destination_country: str
    end_user_name: str
    has_valid_euc: bool
    no_retransfer_commitment: bool
    mod_export_permit_issued: bool
    compliance_status: str      # EXPORT_AUTHORIZED, RESTRICTED_HOLD, CRITICAL_VIOLATION_DENIED
    restrictions: List[str]
    created_at: str


@dataclass
class IndustrialMobilizationPlan:
    plan_id: str
    enterprise_name: str
    mobilization_capacity: str  # MILITARY_UNIFORM_BALLISTIC, EMERGENCY_MEDICAL_SUPPLIES, DRONE_AIRFRAME, RADAR_COMPONENTS
    reserved_production_lines: int
    strategic_material_stock_days: int
    annual_mobilization_drill_done: bool
    cyber_hardened_facility: bool
    readiness_rating: str       # COMBAT_READY, SATISFACTORY, INADEQUATE_STOCKPILE, DEFICIENT_DRILL
    is_ready: bool
    action_items: List[str]
    created_at: str


@dataclass
class MilitaryTechnicalStandardQA:
    qa_id: str
    equipment_name: str
    standard_code: str          # TCVN_QS_789, TCVN_AN_456, MIL_STD_VN_810
    temp_range_celsius: str     # e.g. "-10C to +55C"
    salt_fog_resistance_hours: int
    ecm_anti_jamming_resilience_db: float
    tolerance_error_pct: float
    is_compliant: bool
    test_verdict: str
    deviation_points: List[str]
    created_at: str


class DefenseEngine:
    """
    Vietnamese National Defense Industry, Security Export Controls & Industrial Mobilization Engine.
    Operates with pure Python standard library and SQLite WAL persistence.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path:
            self.db_path = db_path
        else:
            base_dir = Path.home() / ".mekong"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(base_dir / "defense.db")
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
                CREATE TABLE IF NOT EXISTS defense_facility_licenses (
                    license_id TEXT PRIMARY KEY,
                    facility_name TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    product_category TEXT NOT NULL,
                    state_secrets_clearance TEXT NOT NULL,
                    personnel_security_cleared INTEGER NOT NULL,
                    perimeter_defense_and_pccc INTEGER NOT NULL,
                    hazardous_waste_clearance INTEGER NOT NULL,
                    is_approved INTEGER NOT NULL,
                    deficiencies_json TEXT NOT NULL,
                    valid_until TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dual_use_export_controls (
                    control_id TEXT PRIMARY KEY,
                    item_name TEXT NOT NULL,
                    dual_use_code TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    destination_country TEXT NOT NULL,
                    end_user_name TEXT NOT NULL,
                    has_valid_euc INTEGER NOT NULL,
                    no_retransfer_commitment INTEGER NOT NULL,
                    mod_export_permit_issued INTEGER NOT NULL,
                    compliance_status TEXT NOT NULL,
                    restrictions_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS industrial_mobilization_plans (
                    plan_id TEXT PRIMARY KEY,
                    enterprise_name TEXT NOT NULL,
                    mobilization_capacity TEXT NOT NULL,
                    reserved_production_lines INTEGER NOT NULL,
                    strategic_material_stock_days INTEGER NOT NULL,
                    annual_mobilization_drill_done INTEGER NOT NULL,
                    cyber_hardened_facility INTEGER NOT NULL,
                    readiness_rating TEXT NOT NULL,
                    is_ready INTEGER NOT NULL,
                    action_items_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS military_technical_qas (
                    qa_id TEXT PRIMARY KEY,
                    equipment_name TEXT NOT NULL,
                    standard_code TEXT NOT NULL,
                    temp_range_celsius TEXT NOT NULL,
                    salt_fog_resistance_hours INTEGER NOT NULL,
                    ecm_anti_jamming_resilience_db REAL NOT NULL,
                    tolerance_error_pct REAL NOT NULL,
                    is_compliant INTEGER NOT NULL,
                    test_verdict TEXT NOT NULL,
                    deviation_points_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    def audit_facility_license(
        self,
        facility_name: str,
        entity_type: str = "STATE_OWNED_DEFENSE_ENTERPRISE",
        product_category: str = "MILITARY_VEHICLES_UAV",
        state_secrets_clearance: str = "TOP_SECRET",
        personnel_security_cleared: bool = True,
        perimeter_defense_and_pccc: bool = True,
        hazardous_waste_clearance: bool = True,
    ) -> Dict[str, Any]:
        """
        Audits defense and security production facility licensing conditions under Articles 19-21 Law 38/2024/QH15.
        """
        license_id = f"DEF-LIC-{uuid.uuid4().hex[:8].upper()}"
        deficiencies: List[str] = []

        ent = entity_type.upper()
        if ent not in ("STATE_OWNED_DEFENSE_ENTERPRISE", "DESIGNATED_PRIVATE_CONTRACTOR"):
            deficiencies.append(
                f"Loại hình doanh nghiệp '{entity_type}' không thuộc đối tượng nòng cốt hoặc được Bộ Quốc phòng chỉ định tham gia CNQP (Điều 19)."
            )

        if not personnel_security_cleared:
            deficiencies.append(
                "Người đứng đầu và cán bộ kỹ thuật chưa qua thẩm định tiêu chuẩn an ninh chính trị, lý lịch bí mật quân sự (Điều 20)."
            )

        if not perimeter_defense_and_pccc:
            deficiencies.append(
                "Hệ thống vọng gác bảo vệ vành đai và phương án phòng cháy chữa cháy nổ quân sự chưa đạt tiêu chuẩn TCVN/QS (Điều 20)."
            )

        if not hazardous_waste_clearance:
            deficiencies.append(
                "Chưa có giấy chứng nhận thẩm định xử lý chất thải độc hại quân sự, hóa chất thuốc phóng thuốc nổ theo quy định môi trường quốc phòng."
            )

        is_approved = len(deficiencies) == 0
        valid_until = (
            (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=5 * 365)).strftime("%Y-%m-%d")
            if is_approved
            else "N/A"
        )

        record = DefenseFacilityLicense(
            license_id=license_id,
            facility_name=facility_name,
            entity_type=ent,
            product_category=product_category,
            state_secrets_clearance=state_secrets_clearance.upper(),
            personnel_security_cleared=personnel_security_cleared,
            perimeter_defense_and_pccc=perimeter_defense_and_pccc,
            hazardous_waste_clearance=hazardous_waste_clearance,
            is_approved=is_approved,
            deficiencies=deficiencies,
            valid_until=valid_until,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO defense_facility_licenses
                (license_id, facility_name, entity_type, product_category, state_secrets_clearance,
                 personnel_security_cleared, perimeter_defense_and_pccc, hazardous_waste_clearance,
                 is_approved, deficiencies_json, valid_until, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.license_id,
                    record.facility_name,
                    record.entity_type,
                    record.product_category,
                    record.state_secrets_clearance,
                    1 if record.personnel_security_cleared else 0,
                    1 if record.perimeter_defense_and_pccc else 0,
                    1 if record.hazardous_waste_clearance else 0,
                    1 if record.is_approved else 0,
                    json.dumps(record.deficiencies, ensure_ascii=False),
                    record.valid_until,
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def verify_dual_use_export_control(
        self,
        item_name: str,
        dual_use_code: str = "DU_SEMI_MIL",
        quantity: int = 500,
        destination_country: str = "SINGAPORE",
        end_user_name: str = "TechDefense Corp",
        has_valid_euc: bool = True,
        no_retransfer_commitment: bool = True,
        mod_export_permit_issued: bool = True,
    ) -> Dict[str, Any]:
        """
        Verifies dual-use technologies and strategic goods export controls under Articles 28-30 Law 38/2024/QH15.
        """
        control_id = f"DUC-EXP-{uuid.uuid4().hex[:8].upper()}"
        restrictions: List[str] = []

        code = dual_use_code.upper()
        if code not in STRATEGIC_DUAL_USE_CATEGORIES:
            restrictions.append(
                f"Mã danh mục lưỡng dụng '{dual_use_code}' không hợp lệ hoặc chưa cập nhật danh mục kiểm soát chiến lược."
            )

        if not has_valid_euc:
            restrictions.append(
                "VI PHẠM BẮT BUỘC: Thiếu Giấy chứng nhận người sử dụng cuối (End-User Certificate - EUC) có xác nhận của cơ quan đại diện ngoại giao."
            )

        if not no_retransfer_commitment:
            restrictions.append(
                "VI PHẠM NGUY HIỂM: Thiếu văn bản cam kết không chuyển giao/tái xuất khẩu cho bên thứ ba hoặc vùng cấm vận quốc tế (Điều 29)."
            )

        if not mod_export_permit_issued:
            restrictions.append(
                "Chưa được Bộ Quốc phòng cấp Giấy phép xuất khẩu trang thiết bị kỹ thuật quân sự và công nghệ lưỡng dụng (Điều 30)."
            )

        if not has_valid_euc or not no_retransfer_commitment:
            compliance_status = "CRITICAL_VIOLATION_DENIED (Đình chỉ xuất khẩu khẩn cấp)"
        elif not mod_export_permit_issued or restrictions:
            compliance_status = "RESTRICTED_HOLD (Tạm giữ hồ sơ - Chờ bổ sung giấy phép Bộ Quốc phòng)"
        else:
            compliance_status = "EXPORT_AUTHORIZED (Đủ điều kiện xuất khẩu có kiểm soát)"

        record = DualUseExportControlRecord(
            control_id=control_id,
            item_name=item_name,
            dual_use_code=code,
            quantity=quantity,
            destination_country=destination_country,
            end_user_name=end_user_name,
            has_valid_euc=has_valid_euc,
            no_retransfer_commitment=no_retransfer_commitment,
            mod_export_permit_issued=mod_export_permit_issued,
            compliance_status=compliance_status,
            restrictions=restrictions,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO dual_use_export_controls
                (control_id, item_name, dual_use_code, quantity, destination_country, end_user_name,
                 has_valid_euc, no_retransfer_commitment, mod_export_permit_issued,
                 compliance_status, restrictions_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.control_id,
                    record.item_name,
                    record.dual_use_code,
                    record.quantity,
                    record.destination_country,
                    record.end_user_name,
                    1 if record.has_valid_euc else 0,
                    1 if record.no_retransfer_commitment else 0,
                    1 if record.mod_export_permit_issued else 0,
                    record.compliance_status,
                    json.dumps(record.restrictions, ensure_ascii=False),
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def evaluate_industrial_mobilization(
        self,
        enterprise_name: str,
        mobilization_capacity: str = "DRONE_AIRFRAME",
        reserved_production_lines: int = 2,
        strategic_material_stock_days: int = 120,
        annual_mobilization_drill_done: bool = True,
        cyber_hardened_facility: bool = True,
    ) -> Dict[str, Any]:
        """
        Evaluates enterprise industrial mobilization readiness plan under Articles 45-50 Law 38/2024/QH15.
        """
        plan_id = f"IMB-PLN-{uuid.uuid4().hex[:8].upper()}"
        action_items: List[str] = []

        if reserved_production_lines < 1:
            action_items.append("Bắt buộc duy trì tối thiểu 01 dây chuyền sản xuất dự phòng có khả năng chuyển đổi sang phục vụ quốc phòng.")

        if strategic_material_stock_days < STATUTORY_MIN_MOBILIZATION_STOCK_DAYS:
            action_items.append(
                f"Dự trữ vật tư chiến lược ({strategic_material_stock_days} ngày) chưa đạt mức tối thiểu {STATUTORY_MIN_MOBILIZATION_STOCK_DAYS} ngày theo quy định tại Điều 47."
            )

        if not annual_mobilization_drill_done:
            action_items.append(
                "Chưa tổ chức diễn tập thực binh chuyển trạng thái sẵn sàng động viên công nghiệp định kỳ hằng năm (Điều 49)."
            )

        if not cyber_hardened_facility:
            action_items.append(
                "Hệ thống điều khiển công nghiệp (SCADA/ICS) chưa được cô lập mạng nội bộ quân sự và bảo đảm an toàn thông tin cấp độ 4."
            )

        is_ready = len(action_items) == 0
        if is_ready:
            readiness_rating = "COMBAT_READY (Sẵn sàng động viên chiến đấu)"
        elif strategic_material_stock_days < STATUTORY_MIN_MOBILIZATION_STOCK_DAYS:
            readiness_rating = "INADEQUATE_STOCKPILE (Thiếu hụt dự trữ chiến lược)"
        elif not annual_mobilization_drill_done:
            readiness_rating = "DEFICIENT_DRILL (Chưa đạt chỉ tiêu diễn tập chuyển trạng thái)"
        else:
            readiness_rating = "SATISFACTORY (Đạt mức cơ bản - Cần hoàn thiện an ninh mạng)"

        record = IndustrialMobilizationPlan(
            plan_id=plan_id,
            enterprise_name=enterprise_name,
            mobilization_capacity=mobilization_capacity,
            reserved_production_lines=reserved_production_lines,
            strategic_material_stock_days=strategic_material_stock_days,
            annual_mobilization_drill_done=annual_mobilization_drill_done,
            cyber_hardened_facility=cyber_hardened_facility,
            readiness_rating=readiness_rating,
            is_ready=is_ready,
            action_items=action_items,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO industrial_mobilization_plans
                (plan_id, enterprise_name, mobilization_capacity, reserved_production_lines,
                 strategic_material_stock_days, annual_mobilization_drill_done,
                 cyber_hardened_facility, readiness_rating, is_ready, action_items_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.plan_id,
                    record.enterprise_name,
                    record.mobilization_capacity,
                    record.reserved_production_lines,
                    record.strategic_material_stock_days,
                    1 if record.annual_mobilization_drill_done else 0,
                    1 if record.cyber_hardened_facility else 0,
                    record.readiness_rating,
                    1 if record.is_ready else 0,
                    json.dumps(record.action_items, ensure_ascii=False),
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def test_military_technical_qa(
        self,
        equipment_name: str,
        standard_code: str = "TCVN_QS_789",
        temp_range_celsius: str = "-10C to +55C",
        salt_fog_resistance_hours: int = 120,
        ecm_anti_jamming_resilience_db: float = 35.0,
        tolerance_error_pct: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Assesses military technical standards and equipment QA testing under Article 25 Law 38/2024/QH15.
        """
        qa_id = f"MIL-QA-{uuid.uuid4().hex[:8].upper()}"
        deviation_points: List[str] = []

        if salt_fog_resistance_hours < 96:
            deviation_points.append(
                f"Thời gian chịu thử nghiệm sương muối biển ({salt_fog_resistance_hours}h) chưa đạt ngưỡng tối thiểu 96h cho trang bị môi trường nhiệt đới/hải đảo."
            )

        if ecm_anti_jamming_resilience_db < 30.0:
            deviation_points.append(
                f"Độ bền chống tác chiến điện tử ECM ({ecm_anti_jamming_resilience_db} dB) thấp hơn tiêu chuẩn 30.0 dB chống chế áp điện tử."
            )

        if tolerance_error_pct > 0.10:
            deviation_points.append(
                f"Dung sai cơ khí - điện tử ({tolerance_error_pct}%) vượt quá ngưỡng tối đa cho phép 0.10% của khí tài quân sự chính xác."
            )

        is_compliant = len(deviation_points) == 0
        if is_compliant:
            test_verdict = "PASSED_MILITARY_ACCEPTANCE (Nghiệm thu đạt chuẩn TCVN/QS)"
        else:
            test_verdict = "FAILED_SPECIFICATION_RETEST_REQUIRED (Không đạt chuẩn khí tài quân sự)"

        record = MilitaryTechnicalStandardQA(
            qa_id=qa_id,
            equipment_name=equipment_name,
            standard_code=standard_code,
            temp_range_celsius=temp_range_celsius,
            salt_fog_resistance_hours=salt_fog_resistance_hours,
            ecm_anti_jamming_resilience_db=ecm_anti_jamming_resilience_db,
            tolerance_error_pct=tolerance_error_pct,
            is_compliant=is_compliant,
            test_verdict=test_verdict,
            deviation_points=deviation_points,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO military_technical_qas
                (qa_id, equipment_name, standard_code, temp_range_celsius, salt_fog_resistance_hours,
                 ecm_anti_jamming_resilience_db, tolerance_error_pct, is_compliant,
                 test_verdict, deviation_points_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.qa_id,
                    record.equipment_name,
                    record.standard_code,
                    record.temp_range_celsius,
                    record.salt_fog_resistance_hours,
                    record.ecm_anti_jamming_resilience_db,
                    record.tolerance_error_pct,
                    1 if record.is_compliant else 0,
                    record.test_verdict,
                    json.dumps(record.deviation_points, ensure_ascii=False),
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def list_records(self, category: str = "all", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Lists stored defense records by category ('all', 'licenses', 'dual_use', 'mobilization', 'qa').
        """
        records: List[Dict[str, Any]] = []
        with self._get_connection() as conn:
            if category in ("all", "licenses"):
                rows = conn.execute(
                    "SELECT * FROM defense_facility_licenses ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "facility_license"
                    d["deficiencies"] = json.loads(d["deficiencies_json"])
                    records.append(d)
            if category in ("all", "dual_use"):
                rows = conn.execute(
                    "SELECT * FROM dual_use_export_controls ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "dual_use_control"
                    d["restrictions"] = json.loads(d["restrictions_json"])
                    records.append(d)
            if category in ("all", "mobilization"):
                rows = conn.execute(
                    "SELECT * FROM industrial_mobilization_plans ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "mobilization_plan"
                    d["action_items"] = json.loads(d["action_items_json"])
                    records.append(d)
            if category in ("all", "qa"):
                rows = conn.execute(
                    "SELECT * FROM military_technical_qas ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "technical_qa"
                    d["deviation_points"] = json.loads(d["deviation_points_json"])
                    records.append(d)
        return records

    def get_status(self) -> Dict[str, Any]:
        """
        Returns telemetry summary of defense facility licenses, dual-use exports, industrial mobilization, and technical QA.
        """
        with self._get_connection() as conn:
            lic_count = conn.execute("SELECT COUNT(*) FROM defense_facility_licenses").fetchone()[0]
            lic_approved = conn.execute(
                "SELECT COUNT(*) FROM defense_facility_licenses WHERE is_approved = 1"
            ).fetchone()[0]
            duc_count = conn.execute("SELECT COUNT(*) FROM dual_use_export_controls").fetchone()[0]
            duc_authorized = conn.execute(
                "SELECT COUNT(*) FROM dual_use_export_controls WHERE compliance_status LIKE 'EXPORT_AUTHORIZED%'"
            ).fetchone()[0]
            imb_count = conn.execute("SELECT COUNT(*) FROM industrial_mobilization_plans").fetchone()[0]
            imb_ready = conn.execute(
                "SELECT COUNT(*) FROM industrial_mobilization_plans WHERE is_ready = 1"
            ).fetchone()[0]
            qa_count = conn.execute("SELECT COUNT(*) FROM military_technical_qas").fetchone()[0]
            qa_passed = conn.execute(
                "SELECT COUNT(*) FROM military_technical_qas WHERE is_compliant = 1"
            ).fetchone()[0]

        return {
            "status": "operational",
            "regulatory_framework": "Law on National Defense and Security Industry and Industrial Mobilization 2024 (Law 38/2024/QH15)",
            "competent_authority": "Bộ Quốc phòng (Tổng cục Công nghiệp Quốc phòng & Cục Tác chiến)",
            "total_defense_facilities_audited": lic_count,
            "approved_defense_licenses": lic_approved,
            "total_dual_use_exports_screened": duc_count,
            "authorized_dual_use_shipments": duc_authorized,
            "industrial_mobilization_plans": imb_count,
            "combat_ready_mobilization_enterprises": imb_ready,
            "military_technical_qas_conducted": qa_count,
            "compliant_military_hardware": qa_passed,
            "db_path": self.db_path,
        }
