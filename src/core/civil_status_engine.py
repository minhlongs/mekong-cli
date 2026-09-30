"""
Autonomous Vietnamese Civil Registration, Vital Statistics & Identification Registry Suite.
Statutory Framework:
- Luật Hộ tịch 2014 (Luật số 60/2014/QH13)
- Nghị định số 123/2015/NĐ-CP hướng dẫn thi hành một số điều của Luật Hộ tịch
- Thông tư số 04/2020/TT-BTP quy định chi tiết thi hành Luật Hộ tịch và Nghị định 123/2015/NĐ-CP
- Luật Hôn nhân và gia đình 2014 (Luật số 52/2014/QH13 - Điều kiện kết hôn Điều 8)
- Luật Căn cước 2023 (Luật số 26/2023/QH15 thay thế Luật Căn cước công dân 2014)
- Nghị định số 70/2024/NĐ-CP quy định chi tiết một số điều và biện pháp thi hành Luật Căn cước
- Đề án 06/CP: Phát triển ứng dụng dữ liệu về dân cư, định danh và xác thực điện tử (VNeID mức 2)

Strict Standard Library Only: Zero external HTTP, zero vendor SDKs.
"""

from __future__ import annotations

import os
import json
import sqlite3
import datetime
import uuid
from typing import Dict, Any, List, Optional

# Province codes for 12-digit National Personal Identification Number (Số định danh cá nhân)
PROVINCE_CODES = {
    "HÀ NỘI": "001",
    "HÀ GIANG": "002",
    "CAO BẰNG": "004",
    "BẮC KẠN": "006",
    "TUYÊN QUANG": "008",
    "LÀO CAI": "010",
    "ĐIỆN BIÊN": "011",
    "LAI CHÂU": "012",
    "SƠN LA": "014",
    "YÊN BÁI": "015",
    "HÒA BÌNH": "017",
    "THÁI NGUYÊN": "019",
    "LẠNG SƠN": "020",
    "QUẢNG NINH": "022",
    "BẮC GIANG": "024",
    "PHÚ THỌ": "025",
    "VĨNH PHÚC": "026",
    "BẮC NINH": "027",
    "HẢI DƯƠNG": "030",
    "HẢI PHÒNG": "031",
    "HƯNG YÊN": "033",
    "THÁI BÌNH": "034",
    "HÀ NAM": "035",
    "NAM ĐỊNH": "036",
    "NINH BÌNH": "037",
    "THANH HÓA": "038",
    "NGHỆ AN": "040",
    "HÀ TĨNH": "042",
    "QUẢNG BÌNH": "044",
    "QUẢNG TRỊ": "045",
    "THỪA THIÊN HUẾ": "046",
    "ĐÀ NẴNG": "048",
    "QUẢNG NAM": "049",
    "QUẢNG NGÃI": "051",
    "BÌNH ĐỊNH": "052",
    "PHÚ YÊN": "054",
    "KHÁNH HÒA": "056",
    "NINH THUẬN": "058",
    "BÌNH THUẬN": "060",
    "KON TUM": "062",
    "GIA LAI": "064",
    "ĐẮK LẮK": "066",
    "ĐẮK NÔNG": "067",
    "LÂM ĐỒNG": "068",
    "BÌNH PHƯỚC": "070",
    "TÂY NINH": "072",
    "BÌNH DƯƠNG": "074",
    "ĐỒNG NAI": "075",
    "BÀ RỊA - VŨNG TÀU": "077",
    "TP. HỒ CHÍ MINH": "079",
    "LONG AN": "080",
    "TIỀN GIANG": "082",
    "BẾN TRE": "083",
    "TRÀ VINH": "084",
    "VĨNH LONG": "086",
    "ĐỒNG THÁP": "087",
    "AN GIANG": "089",
    "KIÊN GIANG": "091",
    "CẦN THƠ": "092",
    "HẬU GIANG": "093",
    "SÓC TRĂNG": "094",
    "BẠC LIÊU": "095",
    "CÀ MAU": "096",
}


def compute_century_gender_code(birth_year: int, gender: str) -> str:
    """
    Century and Gender code for 12-digit Personal Identification Number:
    - 20th century (1900-1999): Male 0, Female 1
    - 21st century (2000-2099): Male 2, Female 3
    - 22nd century (2100-2199): Male 4, Female 5
    - 23rd century (2200-2299): Male 6, Female 7
    - 24th century (2300-2399): Male 8, Female 9
    """
    is_male = gender.strip().upper() in ["NAM", "MALE", "M"]
    if 1900 <= birth_year <= 1999:
        return "0" if is_male else "1"
    elif 2000 <= birth_year <= 2099:
        return "2" if is_male else "3"
    elif 2100 <= birth_year <= 2199:
        return "4" if is_male else "5"
    elif 2200 <= birth_year <= 2299:
        return "6" if is_male else "7"
    else:
        return "8" if is_male else "9"


class CivilStatusEngine:
    """Core engine for Vietnamese Civil Status Registration, Vital Statistics & Identification."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            db_path = os.path.join(base_dir, "civil_status.db")
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
                CREATE TABLE IF NOT EXISTS birth_registrations (
                    cert_id TEXT PRIMARY KEY,
                    personal_id TEXT UNIQUE NOT NULL,
                    child_name TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    date_of_birth TEXT NOT NULL,
                    birth_place TEXT NOT NULL,
                    province_code TEXT NOT NULL,
                    father_name TEXT,
                    mother_name TEXT NOT NULL,
                    registered_on_time INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS marriage_registrations (
                    cert_id TEXT PRIMARY KEY,
                    groom_name TEXT NOT NULL,
                    groom_dob TEXT NOT NULL,
                    groom_pid TEXT NOT NULL,
                    bride_name TEXT NOT NULL,
                    bride_dob TEXT NOT NULL,
                    bride_pid TEXT NOT NULL,
                    is_legal_age INTEGER NOT NULL,
                    single_status_verified INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS death_registrations (
                    cert_id TEXT PRIMARY KEY,
                    deceased_name TEXT NOT NULL,
                    personal_id TEXT NOT NULL,
                    date_of_death TEXT NOT NULL,
                    cause_of_death TEXT NOT NULL,
                    place_of_death TEXT NOT NULL,
                    death_notice_verified INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS identity_cards (
                    card_id TEXT PRIMARY KEY,
                    personal_id TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    date_of_birth TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    nationality TEXT NOT NULL,
                    has_iris_biometrics INTEGER NOT NULL,
                    has_fingerprints INTEGER NOT NULL,
                    has_facial_photo INTEGER NOT NULL,
                    vneid_level2_active INTEGER NOT NULL,
                    expiration_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS civil_extracts (
                    extract_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    source_cert_id TEXT NOT NULL,
                    applicant_name TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    issued_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def generate_personal_identification_number(
        self, province_name_or_code: str, birth_year: int, gender: str
    ) -> str:
        """
        Generate 12-digit National Personal Identification Number (Số định danh cá nhân):
        - 3 digits: Province/City code (Mã tỉnh/thành phố nơi đăng ký khai sinh)
        - 1 digit: Century & Gender code (Mã thế kỷ và giới tính)
        - 2 digits: Last two digits of birth year (Hai số cuối năm sinh)
        - 6 digits: Pseudo-random sequential unique index (Số ngẫu nhiên)
        """
        prov_upper = province_name_or_code.strip().upper()
        prov_code = PROVINCE_CODES.get(prov_upper, prov_upper if len(prov_upper) == 3 and prov_upper.isdigit() else "001")
        century_gender = compute_century_gender_code(birth_year, gender)
        year_str = f"{birth_year % 100:02d}"

        # 6 random digits based on uuid
        random_suffix = f"{int(uuid.uuid4().int % 1000000):06d}"
        return f"{prov_code}{century_gender}{year_str}{random_suffix}"

    def register_birth(
        self,
        child_name: str,
        date_of_birth: str,
        gender: str,
        mother_name: str,
        father_name: Optional[str] = None,
        birth_place: str = "Bệnh viện Phụ sản Hà Nội",
        province: str = "Hà Nội",
        hospital_birth_notice: bool = True,
        registration_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register birth and issue birth certificate under Law on Civil Status 2014 Article 13-16.
        Generates 12-digit personal identification number immediately upon birth registration.
        """
        cert_id = f"CS-BRT-{uuid.uuid4().hex[:8].upper()}"
        violations = []

        if not hospital_birth_notice:
            violations.append("Thiếu Giấy chứng sinh của cơ sở y tế hoặc văn bản xác nhận của người làm chứng (Điều 16)")

        try:
            dob_dt = datetime.datetime.strptime(date_of_birth, "%Y-%m-%d").date()
        except ValueError:
            dob_dt = datetime.date.today()

        if registration_date:
            try:
                reg_dt = datetime.datetime.strptime(registration_date, "%Y-%m-%d").date()
            except ValueError:
                reg_dt = datetime.date.today()
        else:
            reg_dt = datetime.date.today()

        days_elapsed = (reg_dt - dob_dt).days
        registered_on_time = days_elapsed <= 60  # On-time registration limit: 60 days (Article 15)

        if not registered_on_time:
            violations.append(f"Đăng ký khai sinh quá thời hạn 60 ngày ({days_elapsed} ngày) — thuộc diện đăng ký khai sinh quá hạn (Điều 15)")

        prov_upper = province.strip().upper()
        prov_code = PROVINCE_CODES.get(prov_upper, "001")
        personal_id = self.generate_personal_identification_number(prov_code, dob_dt.year, gender)

        is_registered = hospital_birth_notice  # Even if late, can still register if birth notice exists
        status = "BIRTH_REGISTERED" if is_registered else "REJECTED_MISSING_NOTICE"
        statutory_notes = (
            f"Đã cấp Giấy khai sinh và Số định danh cá nhân {personal_id} theo quy định của Luật Hộ tịch và Luật Căn cước"
            if is_registered
            else "; ".join(violations)
        )

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO birth_registrations (
                    cert_id, personal_id, child_name, gender, date_of_birth,
                    birth_place, province_code, father_name, mother_name,
                    registered_on_time, status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cert_id, personal_id, child_name.strip(), gender.upper(), date_of_birth,
                birth_place.strip(), prov_code, father_name.strip() if father_name else None,
                mother_name.strip(), 1 if registered_on_time else 0, status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "cert_id": cert_id,
            "personal_id": personal_id,
            "child_name": child_name.strip(),
            "gender": gender.upper(),
            "date_of_birth": date_of_birth,
            "birth_place": birth_place,
            "province_code": prov_code,
            "father_name": father_name,
            "mother_name": mother_name,
            "registered_on_time": registered_on_time,
            "status": status,
            "is_registered": is_registered,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def register_marriage(
        self,
        groom_name: str,
        groom_dob: str,
        groom_pid: str,
        bride_name: str,
        bride_dob: str,
        bride_pid: str,
        single_status_verified: bool = True,
        voluntary_consent: bool = True,
    ) -> Dict[str, Any]:
        """
        Register marriage and issue marriage certificate under Law on Civil Status 2014 & Law on Marriage and Family 2014.
        Requirements: Male >= 20 years old, Female >= 18 years old, single status confirmed, voluntary consent.
        """
        cert_id = f"CS-MAR-{uuid.uuid4().hex[:8].upper()}"
        violations = []
        today = datetime.date.today()

        try:
            g_dob = datetime.datetime.strptime(groom_dob, "%Y-%m-%d").date()
            groom_age = (today - g_dob).days // 365
        except ValueError:
            groom_age = 25

        try:
            b_dob = datetime.datetime.strptime(bride_dob, "%Y-%m-%d").date()
            bride_age = (today - b_dob).days // 365
        except ValueError:
            bride_age = 23

        is_legal_age = True
        if groom_age < 20:
            is_legal_age = False
            violations.append(f"Nam chưa đủ 20 tuổi ({groom_age} tuổi) - Vi phạm Điều 8 Luật Hôn nhân và gia đình")

        if bride_age < 18:
            is_legal_age = False
            violations.append(f"Nữ chưa đủ 18 tuổi ({bride_age} tuổi) - Vi phạm Điều 8 Luật Hôn nhân và gia đình")

        if not single_status_verified:
            violations.append("Chưa có Giấy xác nhận tình trạng hôn nhân hợp lệ của hai bên (Điều 18 Nghị định 123/2015)")

        if not voluntary_consent:
            violations.append("Kết hôn không trên cơ sở tự nguyện hoàn toàn (Điều 8 Luật Hôn nhân và gia đình)")

        is_approved = is_legal_age and single_status_verified and voluntary_consent
        status = "MARRIAGE_REGISTERED" if is_approved else "REJECTED_INADMISSIBLE"
        statutory_notes = (
            "Đã đăng ký kết hôn hợp pháp và cấp Giấy chứng nhận kết hôn theo Điều 17, 18 Luật Hộ tịch"
            if is_approved
            else "; ".join(violations)
        )

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO marriage_registrations (
                    cert_id, groom_name, groom_dob, groom_pid,
                    bride_name, bride_dob, bride_pid, is_legal_age,
                    single_status_verified, status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cert_id, groom_name.strip(), groom_dob, groom_pid.strip(),
                bride_name.strip(), bride_dob, bride_pid.strip(), 1 if is_legal_age else 0,
                1 if single_status_verified else 0, status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "cert_id": cert_id,
            "groom_name": groom_name.strip(),
            "groom_age": groom_age,
            "groom_pid": groom_pid.strip(),
            "bride_name": bride_name.strip(),
            "bride_age": bride_age,
            "bride_pid": bride_pid.strip(),
            "is_legal_age": is_legal_age,
            "single_status_verified": single_status_verified,
            "status": status,
            "is_approved": is_approved,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def register_death(
        self,
        deceased_name: str,
        personal_id: str,
        date_of_death: str,
        cause_of_death: str = "Bệnh lý tự nhiên",
        place_of_death: str = "Bệnh viện Bạch Mai, Hà Nội",
        death_notice_verified: bool = True,
        registration_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register death and revoke civil active status under Law on Civil Status 2014 Article 32-34.
        Must be registered within 15 days from the date of death.
        """
        cert_id = f"CS-DTH-{uuid.uuid4().hex[:8].upper()}"
        violations = []

        if not death_notice_verified:
            violations.append("Thiếu Giấy báo tử của cơ sở khám bệnh, chữa bệnh hoặc văn bản của cơ quan có thẩm quyền (Điều 34)")

        try:
            dod_dt = datetime.datetime.strptime(date_of_death, "%Y-%m-%d").date()
        except ValueError:
            dod_dt = datetime.date.today()

        if registration_date:
            try:
                reg_dt = datetime.datetime.strptime(registration_date, "%Y-%m-%d").date()
            except ValueError:
                reg_dt = datetime.date.today()
        else:
            reg_dt = datetime.date.today()

        days_elapsed = (reg_dt - dod_dt).days
        on_time = days_elapsed <= 15  # 15 days limit under Article 32

        if not on_time:
            violations.append(f"Đăng ký khai tử quá thời hạn 15 ngày ({days_elapsed} ngày)")

        is_registered = death_notice_verified
        status = "DEATH_REGISTERED" if is_registered else "REJECTED_MISSING_NOTICE"
        statutory_notes = (
            f"Đã đăng ký khai tử, cấp Trích lục khai tử và khóa trạng thái công dân {personal_id} trên CSDL Dân cư"
            if is_registered
            else "; ".join(violations)
        )

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO death_registrations (
                    cert_id, deceased_name, personal_id, date_of_death,
                    cause_of_death, place_of_death, death_notice_verified,
                    status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cert_id, deceased_name.strip(), personal_id.strip(), date_of_death,
                cause_of_death.strip(), place_of_death.strip(), 1 if death_notice_verified else 0,
                status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "cert_id": cert_id,
            "deceased_name": deceased_name.strip(),
            "personal_id": personal_id.strip(),
            "date_of_death": date_of_death,
            "cause_of_death": cause_of_death,
            "place_of_death": place_of_death,
            "on_time": on_time,
            "status": status,
            "is_registered": is_registered,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def issue_identity_card(
        self,
        full_name: str,
        date_of_birth: str,
        personal_id: str,
        gender: str = "NAM",
        nationality: str = "VIỆT NAM",
        has_iris_biometrics: bool = True,
        has_fingerprints: bool = True,
        has_facial_photo: bool = True,
    ) -> Dict[str, Any]:
        """
        Audit eligibility and issue National Identity Card under Law on Identification 2023 (Luật Căn cước số 26/2023/QH15).
        Captures iris biometrics (thu nhận mống mắt), 10 fingerprints, and facial image.
        Computes statutory expiration milestones (25, 40, 60 years old per Article 21).
        """
        card_id = f"CS-CID-{uuid.uuid4().hex[:8].upper()}"
        violations = []
        today = datetime.date.today()

        try:
            dob_dt = datetime.datetime.strptime(date_of_birth, "%Y-%m-%d").date()
            age = (today - dob_dt).days // 365
        except ValueError:
            age = 28
            dob_dt = datetime.date(today.year - 28, 1, 1)

        # Article 21: Card validity expiration dates
        # Age milestones: 25, 40, 60. Over 60: permanent validity.
        if age < 14:
            expiration_year = dob_dt.year + 14  # Valid until age 14
        elif age < 25:
            expiration_year = dob_dt.year + 25
        elif age < 40:
            expiration_year = dob_dt.year + 40
        elif age < 60:
            expiration_year = dob_dt.year + 60
        else:
            expiration_year = 9999  # Permanent validity over age 60

        expiration_date = f"{expiration_year}-{dob_dt.month:02d}-{dob_dt.day:02d}" if expiration_year != 9999 else "VÔ THỜI HẠN"

        if age >= 14:
            if not has_iris_biometrics:
                violations.append("Thiếu thông tin sinh trắc học mống mắt (bắt buộc thu nhận từ đủ 14 tuổi theo Điều 23 Luật Căn cước 2023)")
            if not has_fingerprints:
                violations.append("Thiếu vân tay lăn 10 ngón (Điều 23 Luật Căn cước 2023)")
            if not has_facial_photo:
                violations.append("Thiếu ảnh chân dung khuôn mặt kỹ thuật số (Điều 23)")

        is_eligible = len(violations) == 0
        vneid_level2_active = is_eligible and (age >= 14)
        status = "IDENTITY_CARD_ISSUED" if is_eligible else "REJECTED_BIOMETRICS_INCOMPLETE"
        statutory_notes = (
            f"Đã cấp Thẻ Căn cước công nghệ chip và kích hoạt tài khoản định danh điện tử VNeID Mức 2 (Thời hạn: {expiration_date})"
            if is_eligible
            else "; ".join(violations)
        )

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO identity_cards (
                    card_id, personal_id, full_name, date_of_birth, gender,
                    nationality, has_iris_biometrics, has_fingerprints,
                    has_facial_photo, vneid_level2_active, expiration_date,
                    status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                card_id, personal_id.strip(), full_name.strip(), date_of_birth, gender.upper(),
                nationality.upper(), 1 if has_iris_biometrics else 0, 1 if has_fingerprints else 0,
                1 if has_facial_photo else 0, 1 if vneid_level2_active else 0, expiration_date,
                status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "card_id": card_id,
            "personal_id": personal_id.strip(),
            "full_name": full_name.strip(),
            "age": age,
            "date_of_birth": date_of_birth,
            "gender": gender.upper(),
            "nationality": nationality.upper(),
            "has_iris_biometrics": has_iris_biometrics,
            "has_fingerprints": has_fingerprints,
            "has_facial_photo": has_facial_photo,
            "vneid_level2_active": vneid_level2_active,
            "expiration_date": expiration_date,
            "status": status,
            "is_eligible": is_eligible,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def issue_civil_extract(
        self,
        event_type: str,
        source_cert_id: str,
        applicant_name: str,
        purpose: str = "Bổ sung hồ sơ công chức / thủ tục bảo hiểm",
    ) -> Dict[str, Any]:
        """
        Issue official civil status extract (Trích lục hộ tịch) under Law on Civil Status 2014 Article 63.
        """
        extract_id = f"CS-EXT-{uuid.uuid4().hex[:8].upper()}"
        event_upper = event_type.strip().upper()
        today_str = datetime.date.today().isoformat()
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO civil_extracts (
                    extract_id, event_type, source_cert_id, applicant_name,
                    purpose, issued_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                extract_id, event_upper, source_cert_id.strip(), applicant_name.strip(),
                purpose.strip(), today_str, created_at
            ))
            conn.commit()

        return {
            "extract_id": extract_id,
            "event_type": event_upper,
            "source_cert_id": source_cert_id.strip(),
            "applicant_name": applicant_name.strip(),
            "purpose": purpose.strip(),
            "issued_date": today_str,
            "status": "EXTRACT_ISSUED",
            "statutory_notes": "Bản sao Trích lục hộ tịch có giá trị pháp lý chứng minh sự kiện hộ tịch (Điều 63)",
            "created_at": created_at,
        }

    def list_civil_records(self, category: str = "ALL", limit: int = 50) -> Dict[str, Any]:
        """List registered civil status and identification records."""
        cat_upper = category.strip().upper()
        results: Dict[str, Any] = {}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            if cat_upper in ["ALL", "BIRTH"]:
                cursor.execute("SELECT * FROM birth_registrations ORDER BY created_at DESC LIMIT ?", (limit,))
                results["births"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "MARRIAGE"]:
                cursor.execute("SELECT * FROM marriage_registrations ORDER BY created_at DESC LIMIT ?", (limit,))
                results["marriages"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "DEATH"]:
                cursor.execute("SELECT * FROM death_registrations ORDER BY created_at DESC LIMIT ?", (limit,))
                results["deaths"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "IDENTITY"]:
                cursor.execute("SELECT * FROM identity_cards ORDER BY created_at DESC LIMIT ?", (limit,))
                results["identity_cards"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "EXTRACT"]:
                cursor.execute("SELECT * FROM civil_extracts ORDER BY created_at DESC LIMIT ?", (limit,))
                results["extracts"] = [dict(row) for row in cursor.fetchall()]

        return results

    def get_civil_status_telemetry(self) -> Dict[str, Any]:
        """Aggregate national vital statistics and identity card issuance telemetry."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN registered_on_time = 1 THEN 1 ELSE 0 END) FROM birth_registrations")
            b_row = cursor.fetchone()
            total_births = b_row[0] or 0
            on_time_births = b_row[1] or 0

            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status = 'MARRIAGE_REGISTERED' THEN 1 ELSE 0 END) FROM marriage_registrations")
            m_row = cursor.fetchone()
            total_marriages = m_row[0] or 0
            approved_marriages = m_row[1] or 0

            cursor.execute("SELECT COUNT(*) FROM death_registrations")
            total_deaths = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN vneid_level2_active = 1 THEN 1 ELSE 0 END) FROM identity_cards")
            i_row = cursor.fetchone()
            total_cards = i_row[0] or 0
            active_vneid_level2 = i_row[1] or 0

            cursor.execute("SELECT COUNT(*) FROM civil_extracts")
            total_extracts = cursor.fetchone()[0] or 0

        natural_growth = total_births - total_deaths

        return {
            "total_birth_registrations": total_births,
            "on_time_birth_registrations": on_time_births,
            "total_marriage_registrations": total_marriages,
            "approved_marriages": approved_marriages,
            "total_death_registrations": total_deaths,
            "population_natural_growth": natural_growth,
            "total_identity_cards_issued": total_cards,
            "active_vneid_level2_users": active_vneid_level2,
            "total_civil_extracts_issued": total_extracts,
            "database_path": self.db_path,
        }
