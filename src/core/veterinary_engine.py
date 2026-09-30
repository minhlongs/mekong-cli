"""
Autonomous Vietnamese Veterinary Medicine, Animal Disease Surveillance & Livestock Quarantine Engine.
Statutory Framework:
- Luật Thú y 2015 (Luật số 79/2015/QH13)
- Nghị định số 35/2016/NĐ-CP & Nghị định số 123/2018/NĐ-CP sửa đổi, bổ sung
- Thông tư số 07/2016/TT-BNNPTNT về phòng, chống dịch bệnh động vật trên cạn
- Thông tư số 25/2016/TT-BNNPTNT & Thông tư số 04/2024/TT-BNNPTNT về kiểm dịch động vật
- Thông tư số 09/2016/TT-BNNPTNT về kiểm soát giết mổ và vệ sinh thú y
- Thông tư số 13/2016/TT-BNNPTNT về quản lý thuốc thú y và tiêu chuẩn GMP-WHO

Strict Standard Library Only: Zero external HTTP, zero vendor SDKs.
"""

import os
import json
import sqlite3
import datetime
import uuid
from typing import Dict, Any, List, Optional

DANGEROUS_ANIMAL_DISEASES = {
    "ASF": "African Swine Fever (Dịch tả lợn Châu Phi)",
    "H5N1": "Highly Pathogenic Avian Influenza (Cúm gia cầm độc lực cao A/H5N1)",
    "H5N6": "Avian Influenza (Cúm gia cầm A/H5N6)",
    "FMD": "Foot-and-Mouth Disease (Bệnh Lở mồm long móng)",
    "PRRS": "Porcine Reproductive and Respiratory Syndrome (Hội chứng tai xanh)",
    "RABIES": "Rabies (Bệnh Dại động vật)",
    "ANTHRAX": "Anthrax (Bệnh Nhiệt thán)",
    "LSD": "Lumpy Skin Disease (Bệnh Viêm da nổi cục trên trâu bò)",
}

PROHIBITED_VET_SUBSTANCES = [
    "SALBUTAMOL",
    "CLENBUTEROL",
    "RACTOPAMINE",
    "CHLORAMPHENICOL",
    "NITROFURAN",
    "DIMETRIDAZOLE",
    "MALACHITE_GREEN",
]

class VeterinaryEngine:
    """Core engine for Vietnamese Veterinary Medicine, Epizootic Surveillance & Quarantine."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            db_path = os.path.join(base_dir, "veterinary.db")
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quarantine_certificates (
                    cert_id TEXT PRIMARY KEY,
                    shipment_type TEXT NOT NULL,
                    animal_species TEXT NOT NULL,
                    quantity_head INTEGER NOT NULL,
                    origin_province TEXT NOT NULL,
                    destination_province TEXT NOT NULL,
                    safe_zone INTEGER NOT NULL,
                    tested_negative INTEGER NOT NULL,
                    disinfected INTEGER NOT NULL,
                    lead_sealed INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS disease_outbreaks (
                    outbreak_id TEXT PRIMARY KEY,
                    disease_name TEXT NOT NULL,
                    species TEXT NOT NULL,
                    location_province TEXT NOT NULL,
                    radius_km REAL NOT NULL,
                    culled_count INTEGER NOT NULL,
                    cull_method TEXT NOT NULL,
                    ring_vaccination INTEGER NOT NULL,
                    quarantine_post_active INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS slaughter_inspections (
                    inspection_id TEXT PRIMARY KEY,
                    abattoir_name TEXT NOT NULL,
                    species TEXT NOT NULL,
                    batch_size INTEGER NOT NULL,
                    antemortem_healthy INTEGER NOT NULL,
                    postmortem_passed INTEGER NOT NULL,
                    water_injected INTEGER NOT NULL,
                    stamp_issued INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    violations_json TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS medicine_facilities (
                    facility_id TEXT PRIMARY KEY,
                    facility_name TEXT NOT NULL,
                    license_type TEXT NOT NULL,
                    chief_vet_licensed INTEGER NOT NULL,
                    gmp_certified INTEGER NOT NULL,
                    has_prohibited_substances INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    violations_json TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def quarantine_shipment(
        self,
        shipment_type: str,
        animal_species: str,
        quantity_head: int,
        origin_province: str,
        destination_province: str,
        safe_zone: bool = True,
        tested_negative: bool = True,
        disinfected: bool = True,
        lead_sealed: bool = True,
    ) -> Dict[str, Any]:
        """
        Issue or validate Veterinary Quarantine Certificate under Law on Veterinary Medicine Articles 37-45.
        """
        cert_id = f"VET-QC-{uuid.uuid4().hex[:8].upper()}"
        violations = []

        if quantity_head <= 0:
            violations.append("Số lượng động vật/sản phẩm động vật phải lớn hơn 0")

        if not safe_zone:
            violations.append("Động vật xuất phát từ vùng chưa được công nhận an toàn dịch bệnh (yêu cầu giám sát bổ sung)")

        if not tested_negative:
            violations.append("Bắt buộc phải có phiếu xét nghiệm âm tính với các bệnh truyền nhiễm nguy hiểm (Điều 38)")

        if not disinfected:
            violations.append("Phương tiện vận chuyển chuyên dùng chưa được tiêu độc, khử trùng trước khi bốc dỡ")

        if not lead_sealed:
            violations.append("Phương tiện vận chuyển phải được niêm phong kẹp chì kiểm dịch thú y hợp lệ")

        is_approved = len(violations) == 0
        status = "CERTIFIED" if is_approved else "REJECTED"
        statutory_notes = "Đủ điều kiện cấp Giấy chứng nhận kiểm dịch vận chuyển nội địa/liên tỉnh" if is_approved else "; ".join(violations)
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO quarantine_certificates (
                    cert_id, shipment_type, animal_species, quantity_head,
                    origin_province, destination_province, safe_zone,
                    tested_negative, disinfected, lead_sealed,
                    status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cert_id, shipment_type.upper(), animal_species.upper(), quantity_head,
                origin_province.strip(), destination_province.strip(),
                1 if safe_zone else 0, 1 if tested_negative else 0,
                1 if disinfected else 0, 1 if lead_sealed else 0,
                status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "cert_id": cert_id,
            "shipment_type": shipment_type.upper(),
            "animal_species": animal_species.upper(),
            "quantity_head": quantity_head,
            "origin_province": origin_province,
            "destination_province": destination_province,
            "safe_zone": safe_zone,
            "tested_negative": tested_negative,
            "disinfected": disinfected,
            "lead_sealed": lead_sealed,
            "status": status,
            "is_approved": is_approved,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def declare_outbreak(
        self,
        disease_name: str,
        species: str,
        location_province: str,
        culled_count: int,
        cull_method: str = "DEEP_BURIAL",
        radius_km: float = 3.0,
        ring_vaccination: bool = True,
        quarantine_post_active: bool = True,
    ) -> Dict[str, Any]:
        """
        Record animal disease outbreak and enforce emergency containment under Law on Veterinary Medicine Articles 15-26.
        """
        outbreak_id = f"EPI-OUT-{uuid.uuid4().hex[:8].upper()}"
        violations = []
        disease_code = disease_name.strip().upper()

        if culled_count < 0:
            violations.append("Số lượng tiêu hủy không hợp lệ")

        if radius_km < 3.0:
            violations.append("Bán kính vùng dịch tối thiểu phải từ 3.0 km theo quy định phòng chống dịch khẩn cấp")

        if not ring_vaccination:
            violations.append("Bắt buộc tổ chức tiêm phòng bao vây trong vùng đệm kiểm soát dịch (Thông tư 07/2016)")

        if not quarantine_post_active:
            violations.append("Bắt buộc lập chốt kiểm dịch tạm thời 24/7 kiểm soát người và phương tiện ra vào ổ dịch")

        is_controlled = len(violations) == 0
        status = "CONTAINMENT_ACTIVE" if is_controlled else "NON_COMPLIANT_RESPONSE"
        disease_desc = DANGEROUS_ANIMAL_DISEASES.get(disease_code, disease_code)
        statutory_notes = f"Thiết lập kiểm soát khẩn cấp dịch bệnh {disease_desc}" if is_controlled else "; ".join(violations)
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO disease_outbreaks (
                    outbreak_id, disease_name, species, location_province,
                    radius_km, culled_count, cull_method, ring_vaccination,
                    quarantine_post_active, status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                outbreak_id, disease_code, species.upper(), location_province.strip(),
                radius_km, culled_count, cull_method.upper(),
                1 if ring_vaccination else 0, 1 if quarantine_post_active else 0,
                status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "outbreak_id": outbreak_id,
            "disease_name": disease_code,
            "disease_description": disease_desc,
            "species": species.upper(),
            "location_province": location_province,
            "radius_km": radius_km,
            "culled_count": culled_count,
            "cull_method": cull_method.upper(),
            "ring_vaccination": ring_vaccination,
            "quarantine_post_active": quarantine_post_active,
            "status": status,
            "is_controlled": is_controlled,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def inspect_slaughter(
        self,
        abattoir_name: str,
        species: str,
        batch_size: int,
        antemortem_healthy: bool = True,
        postmortem_passed: bool = True,
        water_injected: bool = False,
    ) -> Dict[str, Any]:
        """
        Inspect abattoir slaughterhouse and stamp meat under Law on Veterinary Medicine Articles 64-70.
        """
        inspection_id = f"SLAUGHT-{uuid.uuid4().hex[:8].upper()}"
        violations = []

        if batch_size <= 0:
            violations.append("Quy mô lô giết mổ phải lớn hơn 0")

        if not antemortem_healthy:
            violations.append("Nghiêm cấm giết mổ động vật có triệu chứng bệnh lâm sàng hoặc không rõ nguồn gốc")

        if not postmortem_passed:
            violations.append("Thân thịt không đạt tiêu chuẩn cảm quan/vi sinh sau giết mổ (phát hiện gạo lợn, áp xe, tụ huyết)")

        if water_injected:
            violations.append("HÀNH VI NGHIÊM CẤM: Bơm nước, tạp chất hoặc hóa chất vào động vật trước/sau giết mổ (Điều 65)")

        is_passed = len(violations) == 0
        status = "PASSED_STAMPED" if is_passed else "REJECTED_DISPOSAL"
        stamp_issued = is_passed
        violations_json = json.dumps(violations, ensure_ascii=False)
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO slaughter_inspections (
                    inspection_id, abattoir_name, species, batch_size,
                    antemortem_healthy, postmortem_passed, water_injected,
                    stamp_issued, status, violations_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                inspection_id, abattoir_name.strip(), species.upper(), batch_size,
                1 if antemortem_healthy else 0, 1 if postmortem_passed else 0,
                1 if water_injected else 0, 1 if stamp_issued else 0,
                status, violations_json, created_at
            ))
            conn.commit()

        return {
            "inspection_id": inspection_id,
            "abattoir_name": abattoir_name,
            "species": species.upper(),
            "batch_size": batch_size,
            "antemortem_healthy": antemortem_healthy,
            "postmortem_passed": postmortem_passed,
            "water_injected": water_injected,
            "stamp_issued": stamp_issued,
            "status": status,
            "is_passed": is_passed,
            "violations": violations,
            "created_at": created_at,
        }

    def certify_medicine_facility(
        self,
        facility_name: str,
        license_type: str = "MANUFACTURE",
        chief_vet_licensed: bool = True,
        gmp_certified: bool = True,
        has_prohibited_substances: bool = False,
    ) -> Dict[str, Any]:
        """
        Audit veterinary medicine manufacturing or trading facility under Law on Veterinary Medicine Articles 77-107.
        """
        facility_id = f"VET-MED-{uuid.uuid4().hex[:8].upper()}"
        violations = []

        if not facility_name or not facility_name.strip():
            violations.append("Tên cơ sở sản xuất/kinh doanh thuốc thú y không được để trống")

        if not chief_vet_licensed:
            violations.append("Người quản lý chuyên môn bắt buộc phải có Chứng chỉ hành nghề thú y hợp lệ (Điều 107)")

        if license_type.upper() == "MANUFACTURE" and not gmp_certified:
            violations.append("Cơ sở sản xuất thuốc thú y bắt buộc phải đạt chuẩn thực hành tốt sản xuất thuốc thú y GMP-WHO (Điều 90)")

        if has_prohibited_substances:
            violations.append(f"HÀNH VI NGHIÊM CẤM: Tàng trữ, sản xuất, sử dụng chất cấm trong chăn nuôi thú y ({', '.join(PROHIBITED_VET_SUBSTANCES[:3])})")

        is_certified = len(violations) == 0
        status = "CERTIFIED" if is_certified else "REJECTED"
        violations_json = json.dumps(violations, ensure_ascii=False)
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO medicine_facilities (
                    facility_id, facility_name, license_type, chief_vet_licensed,
                    gmp_certified, has_prohibited_substances, status,
                    violations_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                facility_id, facility_name.strip(), license_type.upper(),
                1 if chief_vet_licensed else 0, 1 if gmp_certified else 0,
                1 if has_prohibited_substances else 0, status,
                violations_json, created_at
            ))
            conn.commit()

        return {
            "facility_id": facility_id,
            "facility_name": facility_name,
            "license_type": license_type.upper(),
            "chief_vet_licensed": chief_vet_licensed,
            "gmp_certified": gmp_certified,
            "has_prohibited_substances": has_prohibited_substances,
            "status": status,
            "is_certified": is_certified,
            "violations": violations,
            "created_at": created_at,
        }

    def list_veterinary_records(self, category: str = "ALL", limit: int = 50) -> Dict[str, Any]:
        """List registered veterinary certificates, disease outbreaks, slaughter inspections, and medicine facilities."""
        cat_upper = category.strip().upper()
        results: Dict[str, Any] = {}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            if cat_upper in ["ALL", "QUARANTINE"]:
                cursor.execute("SELECT * FROM quarantine_certificates ORDER BY created_at DESC LIMIT ?", (limit,))
                results["quarantine"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "OUTBREAKS"]:
                cursor.execute("SELECT * FROM disease_outbreaks ORDER BY created_at DESC LIMIT ?", (limit,))
                results["outbreaks"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "SLAUGHTER"]:
                cursor.execute("SELECT * FROM slaughter_inspections ORDER BY created_at DESC LIMIT ?", (limit,))
                results["slaughter"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "MEDICINE"]:
                cursor.execute("SELECT * FROM medicine_facilities ORDER BY created_at DESC LIMIT ?", (limit,))
                results["medicine"] = [dict(row) for row in cursor.fetchall()]

        return results

    def get_veterinary_telemetry(self) -> Dict[str, Any]:
        """Aggregate national veterinary disease surveillance, quarantine, and slaughterhouse hygiene metrics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status = 'CERTIFIED' THEN 1 ELSE 0 END), SUM(quantity_head) FROM quarantine_certificates")
            q_row = cursor.fetchone()
            total_quarantine = q_row[0] or 0
            approved_quarantine = q_row[1] or 0
            total_quarantined_animals = q_row[2] or 0

            cursor.execute("SELECT COUNT(*), SUM(culled_count) FROM disease_outbreaks")
            o_row = cursor.fetchone()
            total_outbreaks = o_row[0] or 0
            total_culled_animals = o_row[1] or 0

            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN stamp_issued = 1 THEN 1 ELSE 0 END), SUM(batch_size) FROM slaughter_inspections")
            s_row = cursor.fetchone()
            total_slaughter_batches = s_row[0] or 0
            passed_slaughter_batches = s_row[1] or 0
            total_slaughtered_animals = s_row[2] or 0

            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status = 'CERTIFIED' THEN 1 ELSE 0 END) FROM medicine_facilities")
            m_row = cursor.fetchone()
            total_medicine_facilities = m_row[0] or 0
            certified_gmp_facilities = m_row[1] or 0

        slaughter_pass_rate = round((passed_slaughter_batches / total_slaughter_batches * 100.0), 2) if total_slaughter_batches > 0 else 100.0

        return {
            "total_quarantine_certs": total_quarantine,
            "approved_quarantine_certs": approved_quarantine,
            "total_quarantined_animals": total_quarantined_animals,
            "total_outbreaks_recorded": total_outbreaks,
            "total_culled_animals": total_culled_animals,
            "total_slaughter_inspections": total_slaughter_batches,
            "passed_slaughter_batches": passed_slaughter_batches,
            "total_slaughtered_animals": total_slaughtered_animals,
            "slaughter_pass_rate_pct": slaughter_pass_rate,
            "total_medicine_facilities": total_medicine_facilities,
            "certified_gmp_facilities": certified_gmp_facilities,
            "database_path": self.db_path,
        }
