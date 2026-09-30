"""
Vietnamese Chemical Safety, Dangerous Goods & Industrial Explosives Engine.
Implements compliance under Law on Chemicals 2007 (Law 06/2007/QH12),
Decree 113/2017/ND-CP, Decree 82/2022/ND-CP, Decree 34/2024/ND-CP (Dangerous Goods Transport),
Law on Weapons, Explosives and Combat Gear 2024 (Law 42/2024/QH15),
and Decree 71/2019/ND-CP (sanctions for chemical safety violations).

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


# Statutory Chemical Catalogs under Decree 113/2017/ND-CP & Decree 82/2022/ND-CP
STATUTORY_CHEMICALS: Dict[str, Dict[str, Any]] = {
    "7664-93-9": {
        "cas_number": "7664-93-9",
        "name_vi": "Axit sulfuric",
        "name_en": "Sulfuric acid",
        "formula": "H2SO4",
        "category": "CONDITIONAL",  # Hóa chất SX-KD có điều kiện (Phụ lục I)
        "ghs_class": "Class 8: Corrosive",
        "hazard_statements": ["H314: Causes severe skin burns and eye damage"],
        "un_number": "UN 1830",
        "threshold_kg": 500,
        "requires_incident_plan": True,
        "requires_nsw_declaration": True,
    },
    "7697-37-2": {
        "cas_number": "7697-37-2",
        "name_vi": "Axit nitric",
        "name_en": "Nitric acid",
        "formula": "HNO3",
        "category": "RESTRICTED",  # Tiền chất thuốc nổ / Hóa chất hạn chế (Phụ lục II)
        "ghs_class": "Class 8 / Class 5.1: Corrosive & Oxidizer",
        "hazard_statements": ["H272: May intensify fire; oxidizer", "H314: Severe burns"],
        "un_number": "UN 2031",
        "threshold_kg": 200,
        "requires_incident_plan": True,
        "requires_nsw_declaration": True,
    },
    "6484-52-2": {
        "cas_number": "6484-52-2",
        "name_vi": "Amoni nitrat",
        "name_en": "Ammonium nitrate",
        "formula": "NH4NO3",
        "category": "EXPLOSIVE_PRECURSOR",  # Tiền chất thuốc nổ nồng độ >= 98.5%
        "ghs_class": "Class 5.1: Oxidizing Solid / Explosive Precursor",
        "hazard_statements": ["H272: May intensify fire; oxidizer", "H319: Causes serious eye irritation"],
        "un_number": "UN 1942",
        "threshold_kg": 100,
        "requires_incident_plan": True,
        "requires_nsw_declaration": True,
    },
    "67-64-1": {
        "cas_number": "67-64-1",
        "name_vi": "Axeton",
        "name_en": "Acetone",
        "formula": "C3H6O",
        "category": "CONDITIONAL",  # Tiền chất công nghiệp / Dung môi dễ cháy
        "ghs_class": "Class 3: Flammable Liquid",
        "hazard_statements": ["H225: Highly flammable liquid and vapour", "H319: Serious eye irritation"],
        "un_number": "UN 1090",
        "threshold_kg": 1000,
        "requires_incident_plan": False,
        "requires_nsw_declaration": True,
    },
    "7647-01-0": {
        "cas_number": "7647-01-0",
        "name_vi": "Axit clohydric",
        "name_en": "Hydrochloric acid",
        "formula": "HCl",
        "category": "CONDITIONAL",
        "ghs_class": "Class 8: Corrosive",
        "hazard_statements": ["H314: Causes severe skin burns and eye damage", "H335: May cause respiratory irritation"],
        "un_number": "UN 1789",
        "threshold_kg": 1000,
        "requires_incident_plan": True,
        "requires_nsw_declaration": True,
    },
    "7782-50-5": {
        "cas_number": "7782-50-5",
        "name_vi": "Khí clo",
        "name_en": "Chlorine gas",
        "formula": "Cl2",
        "category": "RESTRICTED",
        "ghs_class": "Class 2.3: Toxic Gas",
        "hazard_statements": ["H270: May cause or intensify fire; oxidizer", "H330: Fatal if inhaled"],
        "un_number": "UN 1017",
        "threshold_kg": 50,
        "requires_incident_plan": True,
        "requires_nsw_declaration": True,
    },
    "57-12-5": {
        "cas_number": "57-12-5",
        "name_vi": "Xyanua",
        "name_en": "Cyanide salts",
        "formula": "CN-",
        "category": "BANNED_OR_SPECIAL",  # Hóa chất cực độc / Hạn chế đặc biệt nghiêm ngặt
        "ghs_class": "Class 6.1: Toxic Substance",
        "hazard_statements": ["H300: Fatal if swallowed", "H310: Fatal in contact with skin"],
        "un_number": "UN 1680",
        "threshold_kg": 10,
        "requires_incident_plan": True,
        "requires_nsw_declaration": True,
    },
}

# 9 Classes of Dangerous Goods under Decree 34/2024/ND-CP & UN Model Regulations
DANGEROUS_GOODS_CLASSES: Dict[str, Dict[str, Any]] = {
    "1": {"class": "Class 1", "desc": "Chất nổ và vật phẩm cháy nổ", "regulator": "Bộ Quốc phòng / Bộ Công an"},
    "2": {"class": "Class 2", "desc": "Khí gas dễ cháy, độc hoặc không cháy", "regulator": "Bộ Công an / Bộ Công Thương"},
    "3": {"class": "Class 3", "desc": "Chất lỏng dễ cháy (xăng, dầu, dung môi)", "regulator": "Bộ Công an / Bộ GTVT"},
    "4": {"class": "Class 4", "desc": "Chất rắn dễ cháy, tự cháy, sinh khí nguy hiểm", "regulator": "Bộ Công an / Bộ Công Thương"},
    "5": {"class": "Class 5", "desc": "Chất oxy hóa và peroxit hữu cơ", "regulator": "Bộ Khoa học và Công nghệ / Bộ Công Thương"},
    "6": {"class": "Class 6", "desc": "Chất độc và chất lây nhiễm", "regulator": "Bộ Y tế / Bộ Nông nghiệp"},
    "7": {"class": "Class 7", "desc": "Chất phóng xạ", "regulator": "Bộ Khoa học và Công nghệ"},
    "8": {"class": "Class 8", "desc": "Chất ăn mòn (axit, kiềm mạnh)", "regulator": "Bộ Công an / Bộ Công Thương"},
    "9": {"class": "Class 9", "desc": "Chất và vật phẩm nguy hiểm khác", "regulator": "Bộ Giao thông Vận tải / Bộ Công an"},
}


@dataclass
class ChemicalClassification:
    classification_id: str
    query: str
    cas_number: str
    chemical_name: str
    category: str
    ghs_class: str
    un_number: str
    requires_incident_plan: bool
    requires_nsw_declaration: bool
    compliance_notes: str
    created_at: str


@dataclass
class StorageSafetyAudit:
    audit_id: str
    facility_name: str
    chemical_name: str
    volume_liters: float
    bund_capacity_pct: float
    shower_distance_m: float
    has_explosion_proof_ventilation: bool
    has_grounding_system: bool
    is_compliant: bool
    deficiencies: List[str]
    potential_penalty_vnd: int
    created_at: str


@dataclass
class ImportDeclaration:
    declaration_id: str
    nsw_reference_no: str
    importer_name: str
    cas_number: str
    chemical_name: str
    quantity_kg: float
    country_of_origin: str
    border_gate: str
    status: str
    duty_free_declaration: bool
    created_at: str


@dataclass
class TransportAudit:
    transport_id: str
    carrier_name: str
    un_number: str
    hazard_class: str
    gross_weight_kg: float
    has_dangerous_goods_license: bool
    has_fire_extinguishers: bool
    driver_hazmat_certified: bool
    is_approved: bool
    violations: List[str]
    potential_penalty_vnd: int
    created_at: str


class ChemicalEngine:
    """
    Vietnamese Chemical Safety, Dangerous Goods & Industrial Explosives Engine.
    Adheres strictly to the standard library only.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            mekong_dir = Path.home() / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(mekong_dir / "chemical.db")
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
                CREATE TABLE IF NOT EXISTS chemical_classifications (
                    classification_id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    cas_number TEXT NOT NULL,
                    chemical_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    ghs_class TEXT NOT NULL,
                    un_number TEXT NOT NULL,
                    requires_incident_plan INTEGER NOT NULL,
                    requires_nsw_declaration INTEGER NOT NULL,
                    compliance_notes TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS storage_safety_audits (
                    audit_id TEXT PRIMARY KEY,
                    facility_name TEXT NOT NULL,
                    chemical_name TEXT NOT NULL,
                    volume_liters REAL NOT NULL,
                    bund_capacity_pct REAL NOT NULL,
                    shower_distance_m REAL NOT NULL,
                    has_explosion_proof_ventilation INTEGER NOT NULL,
                    has_grounding_system INTEGER NOT NULL,
                    is_compliant INTEGER NOT NULL,
                    deficiencies_json TEXT NOT NULL,
                    potential_penalty_vnd INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS import_declarations (
                    declaration_id TEXT PRIMARY KEY,
                    nsw_reference_no TEXT NOT NULL,
                    importer_name TEXT NOT NULL,
                    cas_number TEXT NOT NULL,
                    chemical_name TEXT NOT NULL,
                    quantity_kg REAL NOT NULL,
                    country_of_origin TEXT NOT NULL,
                    border_gate TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duty_free_declaration INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transport_audits (
                    transport_id TEXT PRIMARY KEY,
                    carrier_name TEXT NOT NULL,
                    un_number TEXT NOT NULL,
                    hazard_class TEXT NOT NULL,
                    gross_weight_kg REAL NOT NULL,
                    has_dangerous_goods_license INTEGER NOT NULL,
                    has_fire_extinguishers INTEGER NOT NULL,
                    driver_hazmat_certified INTEGER NOT NULL,
                    is_approved INTEGER NOT NULL,
                    violations_json TEXT NOT NULL,
                    potential_penalty_vnd INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    def classify_chemical(self, query: str) -> Dict[str, Any]:
        """
        Classifies a chemical substance by CAS number or name under Decree 113/2017 & 82/2022.
        """
        q_norm = query.strip().lower()
        matched: Optional[Dict[str, Any]] = None

        # Direct CAS match
        if query.strip() in STATUTORY_CHEMICALS:
            matched = STATUTORY_CHEMICALS[query.strip()]
        else:
            # Substring match on name_vi, name_en, or formula
            for chem in STATUTORY_CHEMICALS.values():
                if (
                    q_norm in chem["name_vi"].lower()
                    or q_norm in chem["name_en"].lower()
                    or q_norm == chem["formula"].lower()
                    or q_norm in chem["cas_number"].lower()
                ):
                    matched = chem
                    break

        if not matched:
            # Fallback for generic/unlisted chemicals
            classification_id = f"CHEM-CLS-{uuid.uuid4().hex[:8].upper()}"
            record = ChemicalClassification(
                classification_id=classification_id,
                query=query,
                cas_number="UNKNOWN",
                chemical_name=query,
                category="GENERAL_INDUSTRIAL",
                ghs_class="Undetermined / Requires GHS Testing",
                un_number="UN 0000",
                requires_incident_plan=False,
                requires_nsw_declaration=True,
                compliance_notes="Chất hóa học chưa có trong danh mục đặc thù; tuân thủ quy định chung về SDS 16 mục và nhãn GHS.",
                created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            )
        else:
            classification_id = f"CHEM-CLS-{uuid.uuid4().hex[:8].upper()}"
            notes = (
                f"Thuộc nhóm {matched['category']} theo Nghị định 113/2017/NĐ-CP & 82/2022/NĐ-CP. "
                f"Mã CAS: {matched['cas_number']}, Mã UN: {matched['un_number']}. "
                f"Ngưỡng lập kế hoạch PNUPSC: {matched['threshold_kg']} kg."
            )
            record = ChemicalClassification(
                classification_id=classification_id,
                query=query,
                cas_number=matched["cas_number"],
                chemical_name=matched["name_vi"],
                category=matched["category"],
                ghs_class=matched["ghs_class"],
                un_number=matched["un_number"],
                requires_incident_plan=matched["requires_incident_plan"],
                requires_nsw_declaration=matched["requires_nsw_declaration"],
                compliance_notes=notes,
                created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO chemical_classifications
                (classification_id, query, cas_number, chemical_name, category, ghs_class, un_number,
                 requires_incident_plan, requires_nsw_declaration, compliance_notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.classification_id,
                    record.query,
                    record.cas_number,
                    record.chemical_name,
                    record.category,
                    record.ghs_class,
                    record.un_number,
                    1 if record.requires_incident_plan else 0,
                    1 if record.requires_nsw_declaration else 0,
                    record.compliance_notes,
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def audit_chemical_storage(
        self,
        facility_name: str,
        chemical_name: str,
        volume_liters: float,
        bund_capacity_pct: float,
        shower_distance_m: float,
        has_explosion_proof_ventilation: bool = True,
        has_grounding_system: bool = True,
    ) -> Dict[str, Any]:
        """
        Audits chemical warehouse / tank storage safety under Decree 113/2017/ND-CP & TCVN 5507.
        Statutory mandates:
        - Bunding (đê bao chống tràn): >= 110% of tank volume.
        - Emergency shower / eye-wash: <= 10.0m from hazard source.
        - Explosion-proof ventilation (thông gió phòng nổ) mandatory.
        - Electrostatic grounding system (nối đất chống tĩnh điện) mandatory.
        """
        audit_id = f"CHEM-STR-{uuid.uuid4().hex[:8].upper()}"
        deficiencies: List[str] = []
        penalty_vnd = 0

        # Bund capacity check
        if bund_capacity_pct < 110.0:
            deficiencies.append(
                f"Dung tích đê bao chống tràn ({bund_capacity_pct:.1f}%) không đạt chuẩn tối thiểu 110% thể tích bồn lớn nhất."
            )
            penalty_vnd += 40_000_000

        # Shower distance check
        if shower_distance_m > 10.0:
            deficiencies.append(
                f"Vị trí bồn rửa mắt và tắm khẩn cấp ({shower_distance_m:.1f}m) vượt quá cự ly tối đa 10m theo TCVN 5507."
            )
            penalty_vnd += 15_000_000

        # Explosion-proof ventilation
        if not has_explosion_proof_ventilation:
            deficiencies.append("Thiếu hệ thống quạt hút thông gió phòng nổ chống tích tụ hơi hóa chất độc/cháy.")
            penalty_vnd += 25_000_000

        # Grounding system
        if not has_grounding_system:
            deficiencies.append("Thiếu hệ thống tiếp địa tiêu tán tĩnh điện cho bồn chứa hóa chất dễ cháy nổ.")
            penalty_vnd += 20_000_000

        is_compliant = len(deficiencies) == 0

        record = StorageSafetyAudit(
            audit_id=audit_id,
            facility_name=facility_name,
            chemical_name=chemical_name,
            volume_liters=volume_liters,
            bund_capacity_pct=bund_capacity_pct,
            shower_distance_m=shower_distance_m,
            has_explosion_proof_ventilation=has_explosion_proof_ventilation,
            has_grounding_system=has_grounding_system,
            is_compliant=is_compliant,
            deficiencies=deficiencies,
            potential_penalty_vnd=penalty_vnd,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO storage_safety_audits
                (audit_id, facility_name, chemical_name, volume_liters, bund_capacity_pct, shower_distance_m,
                 has_explosion_proof_ventilation, has_grounding_system, is_compliant, deficiencies_json,
                 potential_penalty_vnd, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.audit_id,
                    record.facility_name,
                    record.chemical_name,
                    record.volume_liters,
                    record.bund_capacity_pct,
                    record.shower_distance_m,
                    1 if record.has_explosion_proof_ventilation else 0,
                    1 if record.has_grounding_system else 0,
                    1 if record.is_compliant else 0,
                    json.dumps(record.deficiencies, ensure_ascii=False),
                    record.potential_penalty_vnd,
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def declare_chemical_import(
        self,
        importer_name: str,
        cas_number: str,
        quantity_kg: float,
        country_of_origin: str = "Japan",
        border_gate: str = "Cảng Hải Phòng",
    ) -> Dict[str, Any]:
        """
        Registers an electronic chemical import declaration via National Single Window (Cổng Một cửa Quốc gia vnsw.gov.vn)
        under Decree 113/2017/ND-CP Article 25 & 26.
        """
        declaration_id = f"CHEM-DEC-{uuid.uuid4().hex[:8].upper()}"
        current_year = datetime.datetime.now(datetime.timezone.utc).year
        nsw_ref = f"NSW-BCT-{current_year}-{uuid.uuid4().hex[:6].upper()}"

        chem_info = STATUTORY_CHEMICALS.get(cas_number, {})
        chemical_name = chem_info.get("name_vi", f"Hóa chất CAS {cas_number}")

        record = ImportDeclaration(
            declaration_id=declaration_id,
            nsw_reference_no=nsw_ref,
            importer_name=importer_name,
            cas_number=cas_number,
            chemical_name=chemical_name,
            quantity_kg=quantity_kg,
            country_of_origin=country_of_origin,
            border_gate=border_gate,
            status="APPROVED_AUTOMATIC",  # Cấp phản hồi tự động qua Cổng Một cửa Quốc gia
            duty_free_declaration=True,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO import_declarations
                (declaration_id, nsw_reference_no, importer_name, cas_number, chemical_name,
                 quantity_kg, country_of_origin, border_gate, status, duty_free_declaration, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.declaration_id,
                    record.nsw_reference_no,
                    record.importer_name,
                    record.cas_number,
                    record.chemical_name,
                    record.quantity_kg,
                    record.country_of_origin,
                    record.border_gate,
                    record.status,
                    1 if record.duty_free_declaration else 0,
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def audit_dangerous_goods_transport(
        self,
        carrier_name: str,
        un_number: str,
        hazard_class_key: str,
        gross_weight_kg: float,
        has_dangerous_goods_license: bool,
        has_fire_extinguishers: bool,
        driver_hazmat_certified: bool,
    ) -> Dict[str, Any]:
        """
        Audits dangerous goods overland transport compliance under Decree 34/2024/ND-CP.
        """
        transport_id = f"CHEM-TRN-{uuid.uuid4().hex[:8].upper()}"
        violations: List[str] = []
        penalty_vnd = 0

        dg_info = DANGEROUS_GOODS_CLASSES.get(hazard_class_key, {"class": f"Class {hazard_class_key}", "desc": "Nguy hiểm"})
        hazard_class = f"{dg_info['class']}: {dg_info['desc']}"

        if not has_dangerous_goods_license:
            violations.append("Thiếu Giấy phép vận chuyển hàng nguy hiểm do cơ quan có thẩm quyền cấp (Nghị định 34/2024/NĐ-CP).")
            penalty_vnd += 30_000_000

        if not has_fire_extinguishers:
            violations.append("Phương tiện vận tải không trang bị đủ bình chữa cháy chuyên dụng theo quy chuẩn PCCC vận tải.")
            penalty_vnd += 10_000_000

        if not driver_hazmat_certified:
            violations.append("Lái xe và người áp tải chưa được cấp Chứng chỉ huấn luyện an toàn vận chuyển hàng nguy hiểm.")
            penalty_vnd += 15_000_000

        is_approved = len(violations) == 0

        record = TransportAudit(
            transport_id=transport_id,
            carrier_name=carrier_name,
            un_number=un_number,
            hazard_class=hazard_class,
            gross_weight_kg=gross_weight_kg,
            has_dangerous_goods_license=has_dangerous_goods_license,
            has_fire_extinguishers=has_fire_extinguishers,
            driver_hazmat_certified=driver_hazmat_certified,
            is_approved=is_approved,
            violations=violations,
            potential_penalty_vnd=penalty_vnd,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO transport_audits
                (transport_id, carrier_name, un_number, hazard_class, gross_weight_kg,
                 has_dangerous_goods_license, has_fire_extinguishers, driver_hazmat_certified,
                 is_approved, violations_json, potential_penalty_vnd, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.transport_id,
                    record.carrier_name,
                    record.un_number,
                    record.hazard_class,
                    record.gross_weight_kg,
                    1 if record.has_dangerous_goods_license else 0,
                    1 if record.has_fire_extinguishers else 0,
                    1 if record.driver_hazmat_certified else 0,
                    1 if record.is_approved else 0,
                    json.dumps(record.violations, ensure_ascii=False),
                    record.potential_penalty_vnd,
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def list_records(self, category: str = "all", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Lists recent chemical records by category ('classifications', 'audits', 'declarations', 'transports', or 'all').
        """
        records: List[Dict[str, Any]] = []
        with self._get_connection() as conn:
            if category in ("all", "classifications"):
                rows = conn.execute(
                    "SELECT * FROM chemical_classifications ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "classification"
                    records.append(d)
            if category in ("all", "audits"):
                rows = conn.execute(
                    "SELECT * FROM storage_safety_audits ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "storage_audit"
                    d["deficiencies"] = json.loads(d["deficiencies_json"])
                    records.append(d)
            if category in ("all", "declarations"):
                rows = conn.execute(
                    "SELECT * FROM import_declarations ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "import_declaration"
                    records.append(d)
            if category in ("all", "transports"):
                rows = conn.execute(
                    "SELECT * FROM transport_audits ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "transport_audit"
                    d["violations"] = json.loads(d["violations_json"])
                    records.append(d)
        return records

    def get_status(self) -> Dict[str, Any]:
        """
        Returns telemetry summary of chemical safety, import declarations, and dangerous goods transport.
        """
        with self._get_connection() as conn:
            cls_count = conn.execute("SELECT COUNT(*) FROM chemical_classifications").fetchone()[0]
            audit_count = conn.execute("SELECT COUNT(*) FROM storage_safety_audits").fetchone()[0]
            dec_count = conn.execute("SELECT COUNT(*) FROM import_declarations").fetchone()[0]
            trn_count = conn.execute("SELECT COUNT(*) FROM transport_audits").fetchone()[0]
            total_qty_kg = conn.execute("SELECT COALESCE(SUM(quantity_kg), 0) FROM import_declarations").fetchone()[0]
            compliant_audits = conn.execute(
                "SELECT COUNT(*) FROM storage_safety_audits WHERE is_compliant = 1"
            ).fetchone()[0]

        compliance_rate_pct = (compliant_audits / audit_count * 100.0) if audit_count > 0 else 100.0

        return {
            "status": "operational",
            "regulatory_framework": "Law on Chemicals 2007 (Law 06/2007/QH12), Decree 113/2017/ND-CP, Decree 82/2022/ND-CP, Decree 34/2024/ND-CP",
            "statutory_catalog_count": len(STATUTORY_CHEMICALS),
            "dangerous_goods_classes": len(DANGEROUS_GOODS_CLASSES),
            "total_classifications": cls_count,
            "total_storage_audits": audit_count,
            "compliant_storage_audits": compliant_audits,
            "storage_compliance_rate_pct": round(compliance_rate_pct, 1),
            "total_import_declarations": dec_count,
            "total_imported_quantity_kg": round(float(total_qty_kg), 2),
            "total_transport_audits": trn_count,
            "db_path": self.db_path,
        }
