"""
Autonomous Vietnamese Physical Training, Sports, Professional Athletics & Anti-Doping Engine.
Statutory Framework:
- Luật Thể dục, Thể thao 2006 (sửa đổi, bổ sung 2018 số 26/2018/QH14)
- Nghị định số 36/2019/NĐ-CP hướng dẫn thi hành một số điều của Luật Thể dục, Thể thao
- Thông tư số 17/2019/TT-BVHTTDL về kiểm tra phòng chống Doping trong hoạt động thể thao
- Thông tư số 04/2019/TT-BVHTTDL ban hành danh mục hoạt động thể thao bắt buộc có người hướng dẫn tập luyện
  và hoạt động thể thao mạo hiểm
- WADA World Anti-Doping Code 2021 & VADC (Trung tâm Doping và Y học Thể thao Việt Nam)

Strict Standard Library Only: Zero external HTTP, zero vendor SDKs.
"""

import os
import json
import sqlite3
import datetime
import uuid
from typing import Dict, Any, List, Optional

WADA_PROHIBITED_CLASSES = {
    "S0": "Non-approved substances (Chất chưa được phê chuẩn)",
    "S1": "Anabolic agents (Chất đồng hóa - Steroids)",
    "S2": "Peptide hormones & growth factors (EPO, HGH)",
    "S3": "Beta-2 agonists (Chất chủ vận beta-2)",
    "S4": "Hormone & metabolic modulators (Bộ điều hòa hormone và chuyển hóa)",
    "S5": "Diuretics & masking agents (Thuốc lợi tiểu và chất che giấu)",
    "S6": "Stimulants (Chất kích thích - Amphetamine, Cocaine)",
    "S7": "Narcotics (Chất gây nghiện - Morphine, Oxycodone)",
    "S8": "Cannabinoids (Chất chuyển hóa cần sa)",
    "S9": "Glucocorticoids (Glucocorticoid kháng viêm dạng tiêm/uống)",
    "M1": "Manipulation of blood & blood components (Thao túng máu/doping máu)",
    "M2": "Chemical & physical manipulation (Thao tác hóa học/vật lý)",
    "M3": "Gene & cell doping (Doping gen và tế bào)",
}

EXTREME_SPORT_TYPES = [
    "PARAGLIDING",      # Dù lượn
    "HANG_GLIDING",     # Diều bay
    "ROCK_CLIMBING",    # Leo núi thể thao mạo hiểm
    "SCUBA_DIVING",     # Lặn biển có khí thở
    "OFF_ROAD_MOTOR",   # Đua mô tô/ô tô địa hình mạo hiểm
    "BUNGEE_JUMPING",   # Nhảy bungee
    "WHITE_WATER_RAFT", # Vượt thác nước ghềnh bằng xuồng cao su
]

class SportsEngine:
    """Core engine for Vietnamese Physical Training, Sports, Professional Athletics & Anti-Doping."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            db_path = os.path.join(base_dir, "sports.db")
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
                CREATE TABLE IF NOT EXISTS athlete_contracts (
                    contract_id TEXT PRIMARY KEY,
                    athlete_name TEXT NOT NULL,
                    sport TEXT NOT NULL,
                    club_name TEXT NOT NULL,
                    contract_type TEXT NOT NULL,
                    salary_vnd REAL NOT NULL,
                    duration_months INTEGER NOT NULL,
                    insurance_covered INTEGER NOT NULL,
                    training_fee_vnd REAL NOT NULL,
                    transfer_fee_vnd REAL NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS doping_tests (
                    test_id TEXT PRIMARY KEY,
                    athlete_name TEXT NOT NULL,
                    sport TEXT NOT NULL,
                    sample_type TEXT NOT NULL,
                    collection_date TEXT NOT NULL,
                    substance_detected TEXT,
                    wada_class TEXT,
                    has_tue INTEGER NOT NULL,
                    tue_approved INTEGER NOT NULL,
                    result TEXT NOT NULL,
                    sanction_months INTEGER NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS extreme_sports_permits (
                    permit_id TEXT PRIMARY KEY,
                    facility_name TEXT NOT NULL,
                    sport_type TEXT NOT NULL,
                    certified_coach INTEGER NOT NULL,
                    rescue_certified INTEGER NOT NULL,
                    equipment_inspected INTEGER NOT NULL,
                    medical_plan INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    violations_json TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tournament_sanctions (
                    sanction_id TEXT PRIMARY KEY,
                    tournament_name TEXT NOT NULL,
                    sport TEXT NOT NULL,
                    scale TEXT NOT NULL,
                    organizer TEXT NOT NULL,
                    venue_name TEXT NOT NULL,
                    lighting_lux REAL NOT NULL,
                    medical_team INTEGER NOT NULL,
                    emergency_exits INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def contract_athlete(
        self,
        athlete_name: str,
        sport: str,
        club_name: str,
        contract_type: str = "PROFESSIONAL",
        salary_vnd: float = 30000000.0,
        duration_months: int = 24,
        insurance_covered: bool = True,
        training_fee_vnd: float = 0.0,
        transfer_fee_vnd: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Register and validate a professional athlete contract or transfer under Law on Sports Article 32 & 33.
        """
        contract_id = f"ATH-CTR-{uuid.uuid4().hex[:8].upper()}"
        violations = []

        if not athlete_name or not athlete_name.strip():
            violations.append("Họ tên vận động viên không được để trống")

        if not club_name or not club_name.strip():
            violations.append("Tên câu lạc bộ/đơn vị sử dụng VĐV không được để trống")

        if duration_months < 6:
            violations.append("Hợp đồng VĐV chuyên nghiệp tối thiểu phải từ 06 tháng theo quy định (Điều 32)")

        if salary_vnd < 5000000.0:
            violations.append("Mức lương VĐV chuyên nghiệp không được thấp hơn mức lương tối thiểu vùng quy định")

        if not insurance_covered:
            violations.append("Bắt buộc tham gia bảo hiểm tai nạn lao động, bệnh nghề nghiệp và BHYT cho VĐV (Điều 32 Khoản 2)")

        if contract_type.upper() == "TRANSFER":
            if transfer_fee_vnd < 0:
                violations.append("Phí chuyển nhượng không hợp lệ")

        is_compliant = len(violations) == 0
        status = "APPROVED" if is_compliant else "REJECTED"
        statutory_notes = "Tuân thủ Điều 32, 33 Luật Thể dục, Thể thao 2018" if is_compliant else "; ".join(violations)

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO athlete_contracts (
                    contract_id, athlete_name, sport, club_name, contract_type,
                    salary_vnd, duration_months, insurance_covered, training_fee_vnd,
                    transfer_fee_vnd, status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contract_id, athlete_name.strip(), sport.strip().upper(), club_name.strip(),
                contract_type.upper(), salary_vnd, duration_months, 1 if insurance_covered else 0,
                training_fee_vnd, transfer_fee_vnd, status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "contract_id": contract_id,
            "athlete_name": athlete_name,
            "sport": sport.upper(),
            "club_name": club_name,
            "contract_type": contract_type.upper(),
            "salary_vnd": salary_vnd,
            "duration_months": duration_months,
            "insurance_covered": insurance_covered,
            "training_fee_vnd": training_fee_vnd,
            "transfer_fee_vnd": transfer_fee_vnd,
            "status": status,
            "is_compliant": is_compliant,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def test_doping(
        self,
        athlete_name: str,
        sport: str,
        sample_type: str = "URINE",
        substance_detected: Optional[str] = None,
        wada_class: Optional[str] = None,
        has_tue: bool = False,
        tue_approved: bool = False,
        collection_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process anti-doping sample test and evaluate sanctions under Circular 17/2019/TT-BVHTTDL & WADA Code 2021.
        """
        test_id = f"DOP-{uuid.uuid4().hex[:8].upper()}"
        if not collection_date:
            collection_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

        wada_class_upper = wada_class.upper().strip() if wada_class else None
        substance = substance_detected.strip() if substance_detected else None

        sanction_months = 0
        violations = []
        is_adverse = False

        if substance and substance != "NONE":
            is_adverse = True
            if not wada_class_upper or wada_class_upper not in WADA_PROHIBITED_CLASSES:
                violations.append("Nhóm chất cấm phải thuộc Danh mục WADA (S0–S9, M1–M3)")
            
            if has_tue and tue_approved:
                # Legitimate medical therapeutic use exemption
                result = "TUE_EXEMPTION"
                sanction_months = 0
                statutory_notes = f"Phát hiện chất {substance} ({wada_class_upper}) nhưng được miễn trừ điều trị y tế TUE hợp lệ"
            else:
                result = "ADVERSE_ANALYTICAL_FINDING" # Mẫu vi phạm (Dương tính)
                # Determine standard WADA sanction
                if wada_class_upper in ["S1", "S2", "M1", "M2", "M3"]:
                    sanction_months = 48  # 4 years for non-specified substances/methods (Anabolic/Peptides/Blood)
                elif wada_class_upper in ["S6", "S7", "S8", "S9"]:
                    sanction_months = 24  # 2 years standard for specified stimulants/cannabinoids
                else:
                    sanction_months = 24
                statutory_notes = f"DƯƠNG TÍNH chất cấm {substance} thuộc nhóm {wada_class_upper}. Đình chỉ thi đấu {sanction_months} tháng theo WADA Code & Thông tư 17/2019"
        else:
            result = "NEGATIVE"
            statutory_notes = "Mẫu thử âm tính với tất cả chất cấm trong danh mục WADA 2021"

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO doping_tests (
                    test_id, athlete_name, sport, sample_type, collection_date,
                    substance_detected, wada_class, has_tue, tue_approved,
                    result, sanction_months, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_id, athlete_name.strip(), sport.strip().upper(), sample_type.upper(),
                collection_date, substance, wada_class_upper, 1 if has_tue else 0,
                1 if tue_approved else 0, result, sanction_months, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "test_id": test_id,
            "athlete_name": athlete_name,
            "sport": sport.upper(),
            "sample_type": sample_type.upper(),
            "collection_date": collection_date,
            "substance_detected": substance,
            "wada_class": wada_class_upper,
            "wada_class_description": WADA_PROHIBITED_CLASSES.get(wada_class_upper, "N/A"),
            "has_tue": has_tue,
            "tue_approved": tue_approved,
            "result": result,
            "is_adverse": is_adverse,
            "sanction_months": sanction_months,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def license_extreme_sport(
        self,
        facility_name: str,
        sport_type: str,
        certified_coach: bool = True,
        rescue_certified: bool = True,
        equipment_inspected: bool = True,
        medical_plan: bool = True,
    ) -> Dict[str, Any]:
        """
        Audit safety conditions and license extreme/high-risk sports facilities under Circular 04/2019/TT-BVHTTDL.
        """
        permit_id = f"EXT-SP-{uuid.uuid4().hex[:8].upper()}"
        violations = []
        sport_type_upper = sport_type.strip().upper()

        if not facility_name or not facility_name.strip():
            violations.append("Tên cơ sở hoạt động thể thao mạo hiểm không được để trống")

        if sport_type_upper not in EXTREME_SPORT_TYPES:
            violations.append(f"Môn thể thao mạo hiểm phải thuộc danh mục quy định: {', '.join(EXTREME_SPORT_TYPES)}")

        if not certified_coach:
            violations.append("Bắt buộc phải có Huấn luyện viên/Hướng dẫn viên có chứng chỉ chuyên môn hợp lệ (Điều 4 Thông tư 04/2019)")

        if not rescue_certified:
            violations.append("Bắt buộc phải có nhân viên cứu hộ đạt chuẩn được cấp chứng nhận cứu nạn, cứu hộ thường trực")

        if not equipment_inspected:
            violations.append("Trang thiết bị chuyên dùng (dây, dù, bình dưỡng khí, cáp an toàn) bắt buộc phải có tem kiểm định an toàn định kỳ")

        if not medical_plan:
            violations.append("Bắt buộc có túi sơ cứu y tế chuyên dụng và phương án phối hợp chuyển viện cấp cứu khẩn cấp")

        is_approved = len(violations) == 0
        status = "LICENSED" if is_approved else "REJECTED"
        violations_json = json.dumps(violations, ensure_ascii=False)
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO extreme_sports_permits (
                    permit_id, facility_name, sport_type, certified_coach,
                    rescue_certified, equipment_inspected, medical_plan,
                    status, violations_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                permit_id, facility_name.strip(), sport_type_upper,
                1 if certified_coach else 0, 1 if rescue_certified else 0,
                1 if equipment_inspected else 0, 1 if medical_plan else 0,
                status, violations_json, created_at
            ))
            conn.commit()

        return {
            "permit_id": permit_id,
            "facility_name": facility_name,
            "sport_type": sport_type_upper,
            "certified_coach": certified_coach,
            "rescue_certified": rescue_certified,
            "equipment_inspected": equipment_inspected,
            "medical_plan": medical_plan,
            "status": status,
            "is_approved": is_approved,
            "violations": violations,
            "created_at": created_at,
        }

    def sanction_tournament(
        self,
        tournament_name: str,
        sport: str,
        scale: str = "NATIONAL",
        organizer: str = "Liên đoàn Thể thao Việt Nam",
        venue_name: str = "Sân vận động Quốc gia Mỹ Đình",
        lighting_lux: float = 1200.0,
        medical_team: bool = True,
        emergency_exits: bool = True,
    ) -> Dict[str, Any]:
        """
        Evaluate tournament organization conditions and technical standards under Law on Sports Article 37 & 38.
        """
        sanction_id = f"TOURN-{uuid.uuid4().hex[:8].upper()}"
        violations = []
        scale_upper = scale.strip().upper()

        if not tournament_name or not tournament_name.strip():
            violations.append("Tên giải thi đấu thể thao không được để trống")

        if lighting_lux < 500.0:
            violations.append("Hệ thống chiếu sáng thi đấu thể thao tối thiểu phải đạt 500 lux (1200+ lux đối với truyền hình trực tiếp)")

        if not medical_team:
            violations.append("Bắt buộc phải bố trí đội ngũ y bác sĩ và xe cấp cứu túc trực trong suốt thời gian thi đấu")

        if not emergency_exits:
            violations.append("Địa điểm thi đấu bắt buộc phải có đầy đủ lối thoát nạn khẩn cấp và phương án phân luồng khán giả")

        is_approved = len(violations) == 0
        status = "SANCTIONED" if is_approved else "REJECTED"
        statutory_notes = "Đạt tiêu chuẩn tổ chức thi đấu theo Điều 37, 38 Luật Thể dục, Thể thao" if is_approved else "; ".join(violations)
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tournament_sanctions (
                    sanction_id, tournament_name, sport, scale, organizer,
                    venue_name, lighting_lux, medical_team, emergency_exits,
                    status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sanction_id, tournament_name.strip(), sport.strip().upper(), scale_upper,
                organizer.strip(), venue_name.strip(), lighting_lux,
                1 if medical_team else 0, 1 if emergency_exits else 0,
                status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "sanction_id": sanction_id,
            "tournament_name": tournament_name,
            "sport": sport.upper(),
            "scale": scale_upper,
            "organizer": organizer,
            "venue_name": venue_name,
            "lighting_lux": lighting_lux,
            "medical_team": medical_team,
            "emergency_exits": emergency_exits,
            "status": status,
            "is_approved": is_approved,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def list_sports_records(self, category: str = "ALL", limit: int = 50) -> Dict[str, Any]:
        """List registered sports contracts, anti-doping tests, extreme permits, and tournaments."""
        cat_upper = category.strip().upper()
        results: Dict[str, Any] = {}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            if cat_upper in ["ALL", "CONTRACTS"]:
                cursor.execute("SELECT * FROM athlete_contracts ORDER BY created_at DESC LIMIT ?", (limit,))
                results["contracts"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "DOPING"]:
                cursor.execute("SELECT * FROM doping_tests ORDER BY created_at DESC LIMIT ?", (limit,))
                results["doping_tests"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "EXTREME"]:
                cursor.execute("SELECT * FROM extreme_sports_permits ORDER BY created_at DESC LIMIT ?", (limit,))
                results["extreme_permits"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "TOURNAMENTS"]:
                cursor.execute("SELECT * FROM tournament_sanctions ORDER BY created_at DESC LIMIT ?", (limit,))
                results["tournaments"] = [dict(row) for row in cursor.fetchall()]

        return results

    def get_sports_telemetry(self) -> Dict[str, Any]:
        """Aggregate national sports, athletic contracts, anti-doping, and extreme sports telemetry."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status = 'APPROVED' THEN 1 ELSE 0 END), SUM(salary_vnd) FROM athlete_contracts")
            c_row = cursor.fetchone()
            total_contracts = c_row[0] or 0
            approved_contracts = c_row[1] or 0
            total_salary_pool = c_row[2] or 0.0

            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN result = 'ADVERSE_ANALYTICAL_FINDING' THEN 1 ELSE 0 END), SUM(CASE WHEN result = 'TUE_EXEMPTION' THEN 1 ELSE 0 END) FROM doping_tests")
            d_row = cursor.fetchone()
            total_doping_tests = d_row[0] or 0
            positive_doping_cases = d_row[1] or 0
            tue_exemptions = d_row[2] or 0

            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status = 'LICENSED' THEN 1 ELSE 0 END) FROM extreme_sports_permits")
            e_row = cursor.fetchone()
            total_extreme_permits = e_row[0] or 0
            licensed_extreme_facilities = e_row[1] or 0

            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status = 'SANCTIONED' THEN 1 ELSE 0 END) FROM tournament_sanctions")
            t_row = cursor.fetchone()
            total_tournaments = t_row[0] or 0
            sanctioned_tournaments = t_row[1] or 0

        clean_doping_rate = round(((total_doping_tests - positive_doping_cases) / total_doping_tests * 100.0), 2) if total_doping_tests > 0 else 100.0

        return {
            "total_contracts": total_contracts,
            "approved_contracts": approved_contracts,
            "total_salary_pool_vnd": total_salary_pool,
            "total_doping_tests": total_doping_tests,
            "positive_doping_cases": positive_doping_cases,
            "tue_exemptions": tue_exemptions,
            "clean_doping_rate_pct": clean_doping_rate,
            "total_extreme_permits": total_extreme_permits,
            "licensed_extreme_facilities": licensed_extreme_facilities,
            "total_tournaments": total_tournaments,
            "sanctioned_tournaments": sanctioned_tournaments,
            "database_path": self.db_path,
        }
