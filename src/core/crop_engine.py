"""
Vietnamese Crop Cultivation, Plant Protection, Pesticides & Agricultural Quarantine Engine.
Implements statutory compliance under:
- Law on Crop Production 2018 (Law 31/2018/QH14)
- Law on Plant Protection and Quarantine 2013 (Law 41/2013/QH13)
- Circular 21/2015/TT-BNNPTNT & Circular 09/2023/TT-BNNPTNT (Pesticide registration, active ingredients, MRL & PHI)
- Decision 3442/QD-BNN-BVTV & TCCS 774:2020/BVTV (Planting Area Code - PUC management)
- Decree 94/2019/ND-CP (Detailed regulations on crop seed circulation and farming standards)
- Decree 31/2023/ND-CP (Administrative penalties in crop production, plant quarantine and plant protection).

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


# Banned chemical active ingredients in Vietnamese Agriculture (Circular 09/2023/TT-BNNPTNT)
BANNED_PESTICIDE_ACTIVE_INGREDIENTS = {
    "PARAQUAT",
    "CHLORPYRIFOS_ETHYL",
    "CHLORPYRIFOS_METHYL",
    "GLYPHOSATE",
    "2,4-D",
    "CARBOFURAN",
    "ACEPHATE",
    "TRICHLORFON",
    "DICOFOL",
    "ENDRIN",
    "ALDRIN",
    "LINDANE",
}

# Statutory Pre-Harvest Intervals (PHI in days) and standard dosage limits for allowed ingredients
STATUTORY_ALLOWED_INGREDIENTS: Dict[str, Dict[str, Any]] = {
    "AZOXYSTROBIN": {"phi_days": 7, "max_dosage_l_ha": 0.8, "target_pest": "Fungicide / Đạo ôn, sương mai"},
    "ABAMECTIN": {"phi_days": 3, "max_dosage_l_ha": 0.5, "target_pest": "Insecticide / Sâu cuốn lá, bọ trĩ"},
    "EMAMECTIN_BENZOATE": {"phi_days": 3, "max_dosage_l_ha": 0.4, "target_pest": "Bio-insecticide / Sâu tơ, sâu đục quả"},
    "BACILLUS_THURINGIENSIS": {"phi_days": 1, "max_dosage_l_ha": 1.5, "target_pest": "Microbial / Chế phẩm sinh học BT"},
    "DIFENOCONAZOLE": {"phi_days": 14, "max_dosage_l_ha": 0.6, "target_pest": "Fungicide / Thán thư, gỉ sắt"},
    "SPINOSAD": {"phi_days": 3, "max_dosage_l_ha": 0.5, "target_pest": "Bio-insecticide / Bọ trĩ, sâu xanh"},
    "HEXACONAZOLE": {"phi_days": 14, "max_dosage_l_ha": 1.0, "target_pest": "Fungicide / Nấm hồng, lở cổ rễ"},
    "MANCOZEB": {"phi_days": 14, "max_dosage_l_ha": 2.5, "target_pest": "Fungicide / Mốc sương, đốm lá"},
    "COPPER_HYDROXIDE": {"phi_days": 7, "max_dosage_l_ha": 2.0, "target_pest": "Bactericide / Loét vi khuẩn"},
    "TRICHODERMA": {"phi_days": 0, "max_dosage_l_ha": 3.0, "target_pest": "Bio-fungicide / Nấm đối kháng Trichoderma"},
}

# Minimum area thresholds for Planting Area Codes (PUC in hectares)
MIN_PUC_HECTARES: Dict[str, float] = {
    "DURIAN_EXPORT": 10.0,
    "DRAGON_FRUIT": 10.0,
    "MANGO": 10.0,
    "BANANA_EXPORT": 15.0,
    "RICE_ST25": 20.0,
    "COFFEE_ROBUSTA": 10.0,
    "POMELO": 5.0,
    "SPECIALTY_FRUIT": 5.0,
}


@dataclass
class PlantingAreaCodeAudit:
    audit_id: str
    area_name: str
    crop_type: str
    province: str
    cultivated_hectares: float
    household_count: int
    has_digital_farming_log: bool
    uses_allowed_pesticides_only: bool
    has_pest_monitoring_system: bool
    target_market: str
    is_eligible: bool
    puc_code: Optional[str]
    deficiencies: List[str]
    created_at: str


@dataclass
class PesticideComplianceCheck:
    check_id: str
    crop_type: str
    active_ingredient: str
    dosage_liters_per_ha: float
    days_since_application: int
    intended_harvest_days: int
    is_banned: bool
    is_phi_breached: bool
    safety_status: str
    violations: List[str]
    recommendations: List[str]
    created_at: str


@dataclass
class PhytosanitaryCertificateInspection:
    certificate_id: str
    consignment_id: str
    commodity_name: str
    weight_metric_tons: float
    origin_province: str
    destination_country: str
    quarantine_pests_detected: List[str]
    treatment_method: str
    puc_verified: bool
    is_approved: bool
    inspection_result: str
    quarantine_actions: List[str]
    created_at: str


@dataclass
class PesticideStoreLicenseAudit:
    audit_id: str
    store_name: str
    owner_name: str
    province: str
    owner_has_practice_cert: bool
    distance_to_water_source_m: float
    has_ventilation_and_leak_basin: bool
    has_pccc_equipment: bool
    has_expired_or_counterfeit: bool
    is_eligible: bool
    deficiencies: List[str]
    validity_years: int
    created_at: str


class CropEngine:
    """
    Vietnamese Crop Cultivation, Plant Protection, Pesticides & Agricultural Quarantine Engine.
    Operates with pure Python standard library and SQLite WAL persistence.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path:
            self.db_path = db_path
        else:
            base_dir = Path.home() / ".mekong"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(base_dir / "crop.db")
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
                CREATE TABLE IF NOT EXISTS planting_area_code_audits (
                    audit_id TEXT PRIMARY KEY,
                    area_name TEXT NOT NULL,
                    crop_type TEXT NOT NULL,
                    province TEXT NOT NULL,
                    cultivated_hectares REAL NOT NULL,
                    household_count INTEGER NOT NULL,
                    has_digital_farming_log INTEGER NOT NULL,
                    uses_allowed_pesticides_only INTEGER NOT NULL,
                    has_pest_monitoring_system INTEGER NOT NULL,
                    target_market TEXT NOT NULL,
                    is_eligible INTEGER NOT NULL,
                    puc_code TEXT,
                    deficiencies_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pesticide_compliance_checks (
                    check_id TEXT PRIMARY KEY,
                    crop_type TEXT NOT NULL,
                    active_ingredient TEXT NOT NULL,
                    dosage_liters_per_ha REAL NOT NULL,
                    days_since_application INTEGER NOT NULL,
                    intended_harvest_days INTEGER NOT NULL,
                    is_banned INTEGER NOT NULL,
                    is_phi_breached INTEGER NOT NULL,
                    safety_status TEXT NOT NULL,
                    violations_json TEXT NOT NULL,
                    recommendations_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS phytosanitary_certificates (
                    certificate_id TEXT PRIMARY KEY,
                    consignment_id TEXT NOT NULL,
                    commodity_name TEXT NOT NULL,
                    weight_metric_tons REAL NOT NULL,
                    origin_province TEXT NOT NULL,
                    destination_country TEXT NOT NULL,
                    quarantine_pests_json TEXT NOT NULL,
                    treatment_method TEXT NOT NULL,
                    puc_verified INTEGER NOT NULL,
                    is_approved INTEGER NOT NULL,
                    inspection_result TEXT NOT NULL,
                    quarantine_actions_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pesticide_store_licenses (
                    audit_id TEXT PRIMARY KEY,
                    store_name TEXT NOT NULL,
                    owner_name TEXT NOT NULL,
                    province TEXT NOT NULL,
                    owner_has_practice_cert INTEGER NOT NULL,
                    distance_to_water_source_m REAL NOT NULL,
                    has_ventilation_and_leak_basin INTEGER NOT NULL,
                    has_pccc_equipment INTEGER NOT NULL,
                    has_expired_or_counterfeit INTEGER NOT NULL,
                    is_eligible INTEGER NOT NULL,
                    deficiencies_json TEXT NOT NULL,
                    validity_years INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    def audit_planting_area_code(
        self,
        area_name: str,
        crop_type: str = "DURIAN_EXPORT",
        province: str = "Đắk Lắk",
        cultivated_hectares: float = 12.5,
        household_count: int = 15,
        has_digital_farming_log: bool = True,
        uses_allowed_pesticides_only: bool = True,
        has_pest_monitoring_system: bool = True,
        target_market: str = "CHINA_GACC",
    ) -> Dict[str, Any]:
        """
        Audits eligibility for Planting Area Code (PUC / Mã số vùng trồng) under Law on Crop Production 2018 & TCCS 774:2020.
        """
        audit_id = f"PUC-AUD-{uuid.uuid4().hex[:8].upper()}"
        deficiencies: List[str] = []

        c_type = crop_type.upper()
        min_ha = MIN_PUC_HECTARES.get(c_type, 10.0)

        if cultivated_hectares < min_ha:
            deficiencies.append(
                f"Diện tích vùng trồng ({cultivated_hectares} ha) không đạt quy chuẩn tối thiểu {min_ha} ha đối với {c_type} (TCCS 774:2020/BVTV)."
            )

        if not has_digital_farming_log:
            deficiencies.append(
                "Chưa thiết lập hoặc ghi chép thiếu đầy đủ Nhật ký canh tác số (sử dụng phân bón, thuốc BVTV, thời gian thu hoạch)."
            )

        if not uses_allowed_pesticides_only:
            deficiencies.append(
                "Phát hiện hoặc nghi ngờ sử dụng hoạt chất BVTV ngoài danh mục được phép hoặc thuốc cấm theo Thông tư 09/2023/TT-BNNPTNT."
            )

        if not has_pest_monitoring_system:
            deficiencies.append(
                "Thiếu hệ thống bẫy bả và quy trình giám sát sinh vật gây hại thuộc đối tượng kiểm dịch của nước nhập khẩu."
            )

        is_eligible = len(deficiencies) == 0
        puc_code = None
        if is_eligible:
            # Generate official standard PUC: VN-[PROV]-[CROP]-[ID]
            prov_code = province[:3].upper().replace("Đ", "D")
            puc_code = f"VN-{prov_code}-{uuid.uuid4().hex[:5].upper()}"

        record = PlantingAreaCodeAudit(
            audit_id=audit_id,
            area_name=area_name,
            crop_type=c_type,
            province=province,
            cultivated_hectares=cultivated_hectares,
            household_count=household_count,
            has_digital_farming_log=has_digital_farming_log,
            uses_allowed_pesticides_only=uses_allowed_pesticides_only,
            has_pest_monitoring_system=has_pest_monitoring_system,
            target_market=target_market,
            is_eligible=is_eligible,
            puc_code=puc_code,
            deficiencies=deficiencies,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO planting_area_code_audits
                (audit_id, area_name, crop_type, province, cultivated_hectares, household_count,
                 has_digital_farming_log, uses_allowed_pesticides_only, has_pest_monitoring_system,
                 target_market, is_eligible, puc_code, deficiencies_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.audit_id,
                    record.area_name,
                    record.crop_type,
                    record.province,
                    record.cultivated_hectares,
                    record.household_count,
                    1 if record.has_digital_farming_log else 0,
                    1 if record.uses_allowed_pesticides_only else 0,
                    1 if record.has_pest_monitoring_system else 0,
                    record.target_market,
                    1 if record.is_eligible else 0,
                    record.puc_code,
                    json.dumps(record.deficiencies, ensure_ascii=False),
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def audit_pesticide_compliance(
        self,
        crop_type: str,
        active_ingredient: str,
        dosage_liters_per_ha: float = 0.5,
        days_since_application: int = 5,
        intended_harvest_days: int = 2,
    ) -> Dict[str, Any]:
        """
        Audits pesticide active ingredient legality, dosage, and Pre-Harvest Interval (PHI) under Circular 09/2023/TT-BNNPTNT.
        """
        check_id = f"PEST-CHK-{uuid.uuid4().hex[:8].upper()}"
        violations: List[str] = []
        recommendations: List[str] = []

        ingredient = active_ingredient.upper().strip()
        is_banned = ingredient in BANNED_PESTICIDE_ACTIVE_INGREDIENTS

        if is_banned:
            violations.append(
                f"HOẠT CHẤT CẤM: '{ingredient}' thuộc danh mục hóa chất BVTV BỊ CẤM SỬ DỤNG TẠI VIỆT NAM (Thông tư 09/2023/TT-BNNPTNT). Tịch thu và tiêu hủy nông sản."
            )
            recommendations.append(
                "Đình chỉ thu hoạch ngay lập tức, cách ly lô nông sản và chuyển hồ sơ sang Thanh tra Sở NN&PTNT để xử phạt hành chính theo Nghị định 31/2023/NĐ-CP."
            )
            safety_status = "CRITICAL_BANNED_SUBSTANCE (Sử dụng hoạt chất cấm tuyệt đối)"
            is_phi_breached = True
        else:
            allowed_info = STATUTORY_ALLOWED_INGREDIENTS.get(ingredient)
            if not allowed_info:
                # Active ingredient not in local database -> warning to check registry
                statutory_phi = 14
                max_dosage = 1.0
                recommendations.append(
                    f"Hoạt chất '{ingredient}' cần đối chiếu thêm với Danh mục thuốc BVTV được phép sử dụng hiện hành của Bộ NN&PTNT."
                )
            else:
                statutory_phi = allowed_info["phi_days"]
                max_dosage = allowed_info["max_dosage_l_ha"]

            if dosage_liters_per_ha > max_dosage:
                violations.append(
                    f"Liều lượng phun ({dosage_liters_per_ha} L/ha) vượt nồng độ hướng dẫn ({max_dosage} L/ha), tăng nguy cơ vượt ngưỡng dư lượng tối đa cho phép MRL."
                )

            total_days_before_harvest = days_since_application + intended_harvest_days
            is_phi_breached = total_days_before_harvest < statutory_phi

            if is_phi_breached:
                days_short = statutory_phi - total_days_before_harvest
                violations.append(
                    f"VI PHẠM THỜI GIAN CÁCH LY (PHI): Dự kiến thu hoạch sau {total_days_before_harvest} ngày, trong khi quy định bắt buộc cách ly tối thiểu {statutory_phi} ngày (thiếu {days_short} ngày)."
                )
                recommendations.append(
                    f"Hoãn thu hoạch tối thiểu thêm {days_short} ngày để hoạt chất phân giải an toàn dưới ngưỡng MRL trước khi đưa ra thị trường."
                )
                safety_status = "WARNING_PHI_BREACH (Vi phạm thời gian cách ly thu hoạch)"
            elif len(violations) > 0:
                safety_status = "WARNING_OVER_DOSAGE (Cảnh báo liều lượng cao)"
                recommendations.append(
                    "Theo dõi chặt chẽ và xét nghiệm kiểm tra nhanh dư lượng trước khi đóng thùng xuất khẩu."
                )
            else:
                safety_status = "SAFE_COMPLIANT (Đảm bảo an toàn dư lượng và thời gian cách ly)"
                recommendations.append(
                    "Đủ điều kiện thu hoạch và đóng gói theo tiêu chuẩn VietGAP/GlobalGAP."
                )

        record = PesticideComplianceCheck(
            check_id=check_id,
            crop_type=crop_type,
            active_ingredient=ingredient,
            dosage_liters_per_ha=dosage_liters_per_ha,
            days_since_application=days_since_application,
            intended_harvest_days=intended_harvest_days,
            is_banned=is_banned,
            is_phi_breached=is_phi_breached,
            safety_status=safety_status,
            violations=violations,
            recommendations=recommendations,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO pesticide_compliance_checks
                (check_id, crop_type, active_ingredient, dosage_liters_per_ha, days_since_application,
                 intended_harvest_days, is_banned, is_phi_breached, safety_status, violations_json,
                 recommendations_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.check_id,
                    record.crop_type,
                    record.active_ingredient,
                    record.dosage_liters_per_ha,
                    record.days_since_application,
                    record.intended_harvest_days,
                    1 if record.is_banned else 0,
                    1 if record.is_phi_breached else 0,
                    record.safety_status,
                    json.dumps(record.violations, ensure_ascii=False),
                    json.dumps(record.recommendations, ensure_ascii=False),
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def issue_phytosanitary_certificate(
        self,
        consignment_id: str,
        commodity_name: str,
        weight_metric_tons: float = 25.0,
        origin_province: str = "Tiền Giang",
        destination_country: str = "CHINA",
        quarantine_pests_detected: Optional[List[str]] = None,
        treatment_method: str = "VAPOR_HEAT_TREATMENT",
        puc_verified: bool = True,
    ) -> Dict[str, Any]:
        """
        Evaluates phytosanitary quarantine clearance and issues phytosanitary certificate under Law on Plant Protection and Quarantine 2013.
        """
        certificate_id = f"PHYTO-CERT-{uuid.uuid4().hex[:8].upper()}"
        quarantine_pests = quarantine_pests_detected or []
        quarantine_actions: List[str] = []

        dest = destination_country.upper()
        has_pests = len(quarantine_pests) > 0

        if not puc_verified:
            quarantine_actions.append(
                "Lô hàng xuất khẩu chưa được cấp hoặc chưa đối chiếu thành công Mã số vùng trồng (PUC) và Mã số cơ sở đóng gói (PHC)."
            )

        if has_pests:
            pests_str = ", ".join(quarantine_pests)
            quarantine_actions.append(
                f"PHÁT HIỆN SINH VẬT GÂY HẠI KIỂM DỊCH: {pests_str}. Từ chối cấp Giấy chứng nhận kiểm dịch thực vật xuất khẩu."
            )
            if "IRRADIATION" not in treatment_method.upper() and "FUMIGATION" not in treatment_method.upper():
                quarantine_actions.append(
                    "Yêu cầu xử lý chiếu xạ hoặc hun trùng diệt trừ sinh vật gây hại hoặc tiêu hủy/tái xuất lô hàng theo Điều 34 Luật BV&KDTV."
                )

        is_approved = not has_pests and puc_verified
        if is_approved:
            inspection_result = f"ĐẠT YÊU CẦU KIỂM DỊCH THỰC VẬT XUẤT KHẨU SANG {dest}"
            quarantine_actions.append(
                f"Đã hoàn thành kiểm tra cảm quan, giám định sinh học và xác nhận biện pháp xử lý {treatment_method}. Cấp Giấy chứng nhận Kiểm dịch thực vật (Mẫu Phytosanitary Certificate quốc tế)."
            )
        else:
            inspection_result = f"KHÔNG ĐẠT TIÊU CHUẨN KIỂM DỊCH XUẤT KHẨU SANG {dest}"

        record = PhytosanitaryCertificateInspection(
            certificate_id=certificate_id,
            consignment_id=consignment_id,
            commodity_name=commodity_name,
            weight_metric_tons=weight_metric_tons,
            origin_province=origin_province,
            destination_country=dest,
            quarantine_pests_detected=quarantine_pests,
            treatment_method=treatment_method,
            puc_verified=puc_verified,
            is_approved=is_approved,
            inspection_result=inspection_result,
            quarantine_actions=quarantine_actions,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO phytosanitary_certificates
                (certificate_id, consignment_id, commodity_name, weight_metric_tons, origin_province,
                 destination_country, quarantine_pests_json, treatment_method, puc_verified,
                 is_approved, inspection_result, quarantine_actions_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.certificate_id,
                    record.consignment_id,
                    record.commodity_name,
                    record.weight_metric_tons,
                    record.origin_province,
                    record.destination_country,
                    json.dumps(record.quarantine_pests_detected, ensure_ascii=False),
                    record.treatment_method,
                    1 if record.puc_verified else 0,
                    1 if record.is_approved else 0,
                    record.inspection_result,
                    json.dumps(record.quarantine_actions, ensure_ascii=False),
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def audit_pesticide_store_license(
        self,
        store_name: str,
        owner_name: str = "Nguyễn Văn Chủ",
        province: str = "Đồng Tháp",
        owner_has_practice_cert: bool = True,
        distance_to_water_source_m: float = 65.0,
        has_ventilation_and_leak_basin: bool = True,
        has_pccc_equipment: bool = True,
        has_expired_or_counterfeit: bool = False,
    ) -> Dict[str, Any]:
        """
        Audits eligibility for Pesticide Retail Store License under Article 63 Law on Plant Protection and Quarantine 2013.
        """
        audit_id = f"PEST-STR-{uuid.uuid4().hex[:8].upper()}"
        deficiencies: List[str] = []

        if not owner_has_practice_cert:
            deficiencies.append(
                "Người trực tiếp bán thuốc BVTV không có Chứng chỉ hành nghề buôn bán thuốc BVTV hoặc bằng cấp chuyên ngành nông lâm nghiệp (Khoản 1 Điều 63)."
            )

        if distance_to_water_source_m < 50.0:
            deficiencies.append(
                f"Khoảng cách từ cửa hàng đến nguồn nước ăn/trường học ({distance_to_water_source_m} m) vi phạm quy định an toàn tối thiểu 50 m."
            )

        if not has_ventilation_and_leak_basin:
            deficiencies.append(
                "Kho chứa thuốc thiếu hệ thống thông gió đạt chuẩn hoặc không có bờ ngăn gờ chống rò rỉ hóa chất khi đổ vỡ."
            )

        if not has_pccc_equipment:
            deficiencies.append(
                "Thiếu thiết bị phòng cháy chữa cháy chuyên dụng cho kho bảo quản hóa chất nông nghiệp."
            )

        if has_expired_or_counterfeit:
            deficiencies.append(
                "PHÁT HIỆN BUÔN BÁN THUỐC BVTV HẾT HẠN SỬ DỤNG, KHÔNG RÕ NGUỒN GỐC HOẶC THUỐC GIẢ (Vi phạm nghiêm trọng Nghị định 31/2023/NĐ-CP)."
            )

        is_eligible = len(deficiencies) == 0
        validity = 5 if is_eligible else 0  # 5-year statutory license for pesticide trading

        record = PesticideStoreLicenseAudit(
            audit_id=audit_id,
            store_name=store_name,
            owner_name=owner_name,
            province=province,
            owner_has_practice_cert=owner_has_practice_cert,
            distance_to_water_source_m=distance_to_water_source_m,
            has_ventilation_and_leak_basin=has_ventilation_and_leak_basin,
            has_pccc_equipment=has_pccc_equipment,
            has_expired_or_counterfeit=has_expired_or_counterfeit,
            is_eligible=is_eligible,
            deficiencies=deficiencies,
            validity_years=validity,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO pesticide_store_licenses
                (audit_id, store_name, owner_name, province, owner_has_practice_cert,
                 distance_to_water_source_m, has_ventilation_and_leak_basin, has_pccc_equipment,
                 has_expired_or_counterfeit, is_eligible, deficiencies_json, validity_years, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.audit_id,
                    record.store_name,
                    record.owner_name,
                    record.province,
                    1 if record.owner_has_practice_cert else 0,
                    record.distance_to_water_source_m,
                    1 if record.has_ventilation_and_leak_basin else 0,
                    1 if record.has_pccc_equipment else 0,
                    1 if record.has_expired_or_counterfeit else 0,
                    1 if record.is_eligible else 0,
                    json.dumps(record.deficiencies, ensure_ascii=False),
                    record.validity_years,
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def list_records(self, category: str = "all", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Lists stored records by category ('all', 'puc', 'pesticides', 'phyto', 'stores').
        """
        records: List[Dict[str, Any]] = []
        with self._get_connection() as conn:
            if category in ("all", "puc"):
                rows = conn.execute(
                    "SELECT * FROM planting_area_code_audits ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "planting_area_code"
                    d["deficiencies"] = json.loads(d["deficiencies_json"])
                    records.append(d)
            if category in ("all", "pesticides"):
                rows = conn.execute(
                    "SELECT * FROM pesticide_compliance_checks ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "pesticide_check"
                    d["violations"] = json.loads(d["violations_json"])
                    d["recommendations"] = json.loads(d["recommendations_json"])
                    records.append(d)
            if category in ("all", "phyto"):
                rows = conn.execute(
                    "SELECT * FROM phytosanitary_certificates ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "phytosanitary_certificate"
                    d["quarantine_pests_detected"] = json.loads(d["quarantine_pests_json"])
                    d["quarantine_actions"] = json.loads(d["quarantine_actions_json"])
                    records.append(d)
            if category in ("all", "stores"):
                rows = conn.execute(
                    "SELECT * FROM pesticide_store_licenses ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "pesticide_store_license"
                    d["deficiencies"] = json.loads(d["deficiencies_json"])
                    records.append(d)
        return records

    def get_status(self) -> Dict[str, Any]:
        """
        Returns telemetry summary of crop production, planting area codes, pesticide compliance, and export quarantine.
        """
        with self._get_connection() as conn:
            puc_count = conn.execute("SELECT COUNT(*) FROM planting_area_code_audits").fetchone()[0]
            puc_ok = conn.execute(
                "SELECT COUNT(*) FROM planting_area_code_audits WHERE is_eligible = 1"
            ).fetchone()[0]
            pest_count = conn.execute("SELECT COUNT(*) FROM pesticide_compliance_checks").fetchone()[0]
            phyto_count = conn.execute("SELECT COUNT(*) FROM phytosanitary_certificates").fetchone()[0]
            phyto_ok = conn.execute(
                "SELECT COUNT(*) FROM phytosanitary_certificates WHERE is_approved = 1"
            ).fetchone()[0]
            store_count = conn.execute("SELECT COUNT(*) FROM pesticide_store_licenses").fetchone()[0]
            store_ok = conn.execute(
                "SELECT COUNT(*) FROM pesticide_store_licenses WHERE is_eligible = 1"
            ).fetchone()[0]

        return {
            "status": "operational",
            "regulatory_framework": "Law on Crop Production 2018 (Law 31/2018/QH14), Law on Plant Protection and Quarantine 2013, Circular 09/2023/TT-BNNPTNT",
            "competent_authority": "Cục Bảo vệ thực vật & Cục Trồng trọt (Bộ NN&PTNT)",
            "total_puc_audits": puc_count,
            "approved_puc_codes": puc_ok,
            "total_pesticide_checks": pest_count,
            "total_phytosanitary_certificates": phyto_count,
            "approved_phytosanitary_certificates": phyto_ok,
            "total_pesticide_stores_audited": store_count,
            "licensed_pesticide_stores": store_ok,
            "db_path": self.db_path,
        }
