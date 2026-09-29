"""
Vietnamese Cinema, Film Production, Age Classification & Censorship Engine.
Pure Python standard library implementation adhering to tests/test_core_boundary.py.

Statutory Framework:
- Luật Điện ảnh 2022 (Luật số 05/2022/QH15):
  * Điều 9: Các hành vi bị nghiêm cấm trong hoạt động điện ảnh (xuyên tạc lịch sử, vi phạm chủ quyền lãnh thổ, kích động bạo lực, khiêu dâm).
  * Điều 13, 14: Điều kiện sản xuất phim và cung cấp dịch vụ quay phim cho đối tác nước ngoài tại Việt Nam.
  * Điều 19: Phổ biến phim trên không gian mạng (OTT VOD), tự phân loại, hiển thị cảnh báo và hạn gỡ bỏ trong 24 giờ.
- Thông tư số 05/2023/TT-BVHTTDL:
  * 06 mức phân loại độ tuổi quốc gia: P (mọi độ tuổi), K (dưới 13 có người giám hộ), T13 (13+), T16 (16+), T18 (18+), C (cấm phổ biến).
  * 07 tiêu chí đánh giá mức phân loại: Chủ đề; Bạo lực; Khỏa thân/tình dục; Ma túy/chất kích thích; Kinh dị; Ngôn từ tục tĩu; Hành vi nguy hiểm.
- Nghị định số 131/2022/NĐ-CP:
  * Quy định chi tiết thi hành Luật Điện ảnh: Tỷ lệ suất chiếu phim Việt Nam tại rạp (>= 10% tổng số suất chiếu, ưu tiên khung giờ vàng 18:00 - 22:00); tỷ lệ thời lượng phát sóng phim Việt Nam trên truyền hình (>= 30%).
- Nghị định số 38/2021/NĐ-CP & Nghị định số 128/2022/NĐ-CP: Xử phạt vi phạm hành chính trong lĩnh vực điện ảnh.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import math
import os
import re
import sqlite3
from typing import Any, Dict, List, Optional


class CinemaEngine:
    """Core engine for Vietnamese cinema regulation, age classification, and censorship."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            base_dir = os.path.join(os.getcwd(), ".mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "cinema.db")
        else:
            self.db_path = db_path
            parent = os.path.dirname(db_path)
            if parent:
                os.makedirs(parent, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS film_classifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    classification_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    rating TEXT NOT NULL,
                    rating_description TEXT NOT NULL,
                    violence_level INTEGER NOT NULL,
                    nudity_level INTEGER NOT NULL,
                    horror_level INTEGER NOT NULL,
                    profanity_level INTEGER NOT NULL,
                    sovereign_violation INTEGER NOT NULL,
                    warning_tags TEXT NOT NULL,
                    is_prohibited INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS film_censorship_permits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    permit_code TEXT UNIQUE NOT NULL,
                    film_title TEXT NOT NULL,
                    producer_name TEXT NOT NULL,
                    rating TEXT NOT NULL,
                    duration_min INTEGER NOT NULL,
                    country_of_origin TEXT NOT NULL,
                    director TEXT NOT NULL,
                    status TEXT NOT NULL,
                    issue_date TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS cinema_screen_quotas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_id TEXT UNIQUE NOT NULL,
                    cinema_name TEXT NOT NULL,
                    total_screenings INTEGER NOT NULL,
                    vn_screenings INTEGER NOT NULL,
                    vn_ratio_pct REAL NOT NULL,
                    prime_time_total INTEGER NOT NULL,
                    prime_time_vn INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    deficiencies TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ott_film_compliance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id TEXT UNIQUE NOT NULL,
                    platform TEXT NOT NULL,
                    film_id TEXT NOT NULL,
                    film_title TEXT NOT NULL,
                    rating TEXT NOT NULL,
                    has_warning_banner INTEGER NOT NULL,
                    sovereign_clean INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    sanction_risk TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ott_film_takedowns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    takedown_id TEXT UNIQUE NOT NULL,
                    platform TEXT NOT NULL,
                    film_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    notice_timestamp TEXT NOT NULL,
                    resolved_timestamp TEXT,
                    hours_elapsed REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    # 1. Film Age Classification & Censorship Evaluation (Thông tư 05/2023/TT-BVHTTDL)
    def classify_film(
        self,
        title: str,
        violence_level: int = 0,
        nudity_level: int = 0,
        horror_level: int = 0,
        profanity_level: int = 0,
        drug_substance: int = 0,
        dangerous_acts: int = 0,
        sovereign_violation: bool = False,
    ) -> Dict[str, Any]:
        """Evaluates film content across 7 statutory criteria and determines the age rating under Circular 05/2023."""
        # Levels range from 0 (none) to 5 (extreme / prohibited)
        warning_tags = []
        is_prohibited = False

        # Check Article 9 Law 05/2022/QH15: Absolute prohibition on sovereign violations (nine-dash line, distortion of history)
        if sovereign_violation:
            is_prohibited = True
            rating = "C"
            rating_desc = "Phim bị cấm phổ biến (Vi phạm chủ quyền lãnh thổ, an ninh quốc gia theo Điều 9 Luật Điện ảnh 2022)"
            warning_tags.append("VI PHẠM CHỦ QUYỀN LÃNH THỔ / BỊ CẤM PHỔ BIẾN")
        else:
            max_intensity = max(violence_level, nudity_level, horror_level, profanity_level, drug_substance, dangerous_acts)

            if max_intensity >= 5:
                # Level 5 in any harmful criterion leads to prohibition or severe cut requirement
                rating = "C"
                rating_desc = "Phim bị cấm phổ biến (Nội dung bạo lực cực đoan, khiêu dâm hoặc kích động tệ nạn vượt ngưỡng cho phép)"
                warning_tags.append("Nội dung vượt ngưỡng phân loại / Cấm phổ biến")
                is_prohibited = True
            elif max_intensity == 4:
                rating = "T18"
                rating_desc = "Phim được phép phổ biến đến người xem từ đủ 18 tuổi trở lên (18+)"
            elif max_intensity == 3:
                rating = "T16"
                rating_desc = "Phim được phép phổ biến đến người xem từ đủ 16 tuổi trở lên (16+)"
            elif max_intensity == 2:
                rating = "T13"
                rating_desc = "Phim được phép phổ biến đến người xem từ đủ 13 tuổi trở lên (13+)"
            elif max_intensity == 1:
                rating = "K"
                rating_desc = "Phim được phép phổ biến đến người xem dưới 13 tuổi với điều kiện xem cùng cha, mẹ hoặc người giám hộ"
            else:
                rating = "P"
                rating_desc = "Phim được phép phổ biến đến người xem ở mọi độ tuổi"

            # Add warning tags based on criteria presence
            if violence_level >= 2:
                warning_tags.append(f"Cảnh báo bạo lực (Mức {violence_level}/5)")
            if nudity_level >= 2:
                warning_tags.append(f"Cảnh báo nội dung nhạy cảm / tình dục (Mức {nudity_level}/5)")
            if horror_level >= 2:
                warning_tags.append(f"Cảnh báo kinh dị / giật gân (Mức {horror_level}/5)")
            if profanity_level >= 2:
                warning_tags.append(f"Cảnh báo ngôn từ thô tục (Mức {profanity_level}/5)")
            if drug_substance >= 2:
                warning_tags.append(f"Cảnh báo chất kích thích / ma túy (Mức {drug_substance}/5)")
            if dangerous_acts >= 2:
                warning_tags.append(f"Cảnh báo hành vi nguy hiểm dễ bắt chước (Mức {dangerous_acts}/5)")

        classification_id = f"CLS-{hashlib.sha256(f'{title}:{rating}:{datetime.datetime.now().isoformat()}'.encode('utf-8')).hexdigest()[:8].upper()}"

        display_rule = (
            f"Bắt buộc hiển thị biểu tượng chữ '{rating}' ở góc màn hình và cảnh báo: {'; '.join(warning_tags)}"
            if rating != "P" and not is_prohibited
            else ("Không được phép chiếu dưới mọi hình thức" if is_prohibited else "Phù hợp mọi lứa tuổi, không yêu cầu cảnh báo đặc biệt")
        )

        result = {
            "classification_id": classification_id,
            "title": title,
            "rating": rating,
            "rating_description": rating_desc,
            "is_prohibited": is_prohibited,
            "criteria_scores": {
                "violence": violence_level,
                "nudity": nudity_level,
                "horror": horror_level,
                "profanity": profanity_level,
                "drug_substance": drug_substance,
                "dangerous_acts": dangerous_acts,
                "sovereign_violation": sovereign_violation,
            },
            "warning_tags": warning_tags,
            "display_requirement": display_rule,
            "legal_basis": "Thông tư số 05/2023/TT-BVHTTDL & Điều 9 Luật Điện ảnh 2022",
            "created_at": datetime.datetime.now().isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO film_classifications
                (classification_id, title, rating, rating_description, violence_level,
                 nudity_level, horror_level, profanity_level, sovereign_violation,
                 warning_tags, is_prohibited, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    classification_id,
                    title,
                    rating,
                    rating_desc,
                    violence_level,
                    nudity_level,
                    horror_level,
                    profanity_level,
                    1 if sovereign_violation else 0,
                    json.dumps(warning_tags, ensure_ascii=False),
                    1 if is_prohibited else 0,
                    result["created_at"],
                ),
            )

        return result

    # 2. Issue Distribution Permit (GPHPP - Giấy phép phổ biến phim)
    def issue_distribution_permit(
        self,
        film_title: str,
        producer_name: str,
        rating: str,
        duration_min: int,
        country_of_origin: str = "Việt Nam",
        director: str = "Đạo diễn Mekong",
    ) -> Dict[str, Any]:
        """Issues an official Film Distribution Permit (GPHPP) if the film is not banned."""
        rate = rating.upper().strip()
        if rate == "C":
            raise ValueError(f"Không thể cấp Giấy phép phổ biến phim cho tác phẩm bị xếp hạng 'C' (Bị cấm phổ biến): {film_title}")

        now = datetime.datetime.now()
        year = now.year
        seq = hashlib.md5(f"{film_title}:{producer_name}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        permit_code = f"GPHPP-{year}-{seq}"

        result = {
            "permit_code": permit_code,
            "film_title": film_title,
            "producer_name": producer_name,
            "rating": rate,
            "duration_min": duration_min,
            "country_of_origin": country_of_origin,
            "director": director,
            "issuing_authority": "Cục Điện ảnh - Bộ Văn hóa, Thể thao và Du lịch",
            "status": "ISSUED",
            "issue_date": now.strftime("%Y-%m-%d"),
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO film_censorship_permits
                (permit_code, film_title, producer_name, rating, duration_min,
                 country_of_origin, director, status, issue_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    permit_code,
                    film_title,
                    producer_name,
                    rate,
                    duration_min,
                    country_of_origin,
                    director,
                    "ISSUED",
                    result["issue_date"],
                    result["created_at"],
                ),
            )

        return result

    # 3. Cinema Theater Screen Quota Audit (Nghị định 131/2022/NĐ-CP Điều 9)
    def audit_cinema_screen_quota(
        self,
        cinema_name: str,
        total_screenings: int,
        vn_screenings: int,
        prime_time_total: int = 0,
        prime_time_vn: int = 0,
    ) -> Dict[str, Any]:
        """Audits compliance with statutory quota for Vietnamese film screenings at cinema complexes (>= 10%)."""
        if total_screenings <= 0:
            raise ValueError("Tổng số suất chiếu phải lớn hơn 0")

        vn_ratio_pct = (vn_screenings / total_screenings) * 100.0
        deficiencies = []

        # Under Decree 131/2022/NĐ-CP Article 9: Vietnamese film ratio >= 10%
        if vn_ratio_pct < 10.0:
            deficiencies.append(f"Tỷ lệ suất chiếu phim Việt Nam ({round(vn_ratio_pct, 1)}%) thấp hơn hạn ngạch tối thiểu 10% theo Điều 9 Nghị định 131/2022/NĐ-CP")

        if prime_time_total > 0:
            prime_ratio_pct = (prime_time_vn / prime_time_total) * 100.0
            if prime_ratio_pct < 10.0:
                deficiencies.append(f"Tỷ lệ suất chiếu khung giờ vàng 18h-22h cho phim Việt ({round(prime_ratio_pct, 1)}%) thấp hơn quy định ưu tiên")

        compliant = len(deficiencies) == 0
        min_required_vn = math.ceil(total_screenings * 0.10)
        shortfall = max(0, min_required_vn - vn_screenings)

        audit_id = f"QTA-{hashlib.md5(f'{cinema_name}:{total_screenings}:{vn_screenings}'.encode('utf-8')).hexdigest()[:8].upper()}"

        result = {
            "audit_id": audit_id,
            "cinema_name": cinema_name,
            "total_screenings": total_screenings,
            "vn_screenings": vn_screenings,
            "vn_ratio_pct": round(vn_ratio_pct, 2),
            "min_required_ratio_pct": 10.0,
            "shortfall_screenings": shortfall,
            "prime_time_total": prime_time_total,
            "prime_time_vn": prime_time_vn,
            "status": "COMPLIANT" if compliant else "NON_COMPLIANT",
            "deficiencies": deficiencies,
            "created_at": datetime.datetime.now().isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cinema_screen_quotas
                (audit_id, cinema_name, total_screenings, vn_screenings, vn_ratio_pct,
                 prime_time_total, prime_time_vn, status, deficiencies, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    cinema_name,
                    total_screenings,
                    vn_screenings,
                    round(vn_ratio_pct, 2),
                    prime_time_total,
                    prime_time_vn,
                    result["status"],
                    json.dumps(deficiencies, ensure_ascii=False),
                    result["created_at"],
                ),
            )

        return result

    # 4. OTT Streaming Compliance & Warning Verification (Điều 19 Luật Điện ảnh 2022)
    def verify_ott_film_compliance(
        self,
        platform: str,
        film_id: str,
        film_title: str,
        rating: str,
        has_warning_banner: bool = True,
        sovereign_clean: bool = True,
    ) -> Dict[str, Any]:
        """Audits OTT VOD film streaming self-classification, warning display, and territorial integrity."""
        rate = rating.upper().strip()
        non_compliant_reasons = []

        if not sovereign_clean or rate == "C":
            non_compliant_reasons.append("Phim vi phạm chủ quyền lãnh thổ hoặc thuộc diện cấm phổ biến theo Điều 9 Luật Điện ảnh 2022")

        if rate in ["K", "T13", "T16", "T18"] and not has_warning_banner:
            non_compliant_reasons.append(f"Phim có mức phân loại {rate} nhưng không hiển thị thông điệp cảnh báo nội dung nhạy cảm theo quy định Thông tư 05/2023")

        is_compliant = len(non_compliant_reasons) == 0
        status = "COMPLIANT" if is_compliant else "NON_COMPLIANT"

        sanction = "None"
        if not sovereign_clean or rate == "C":
            sanction = "Xử phạt 80M - 100M VND, yêu cầu gỡ bỏ ngay lập tức và thu hồi quyền cung cấp dịch vụ"
        elif not has_warning_banner:
            sanction = "Xử phạt 40M - 50M VND đối với hành vi không hiển thị cảnh báo theo Nghị định 38/2021"

        record_id = f"OTT-{platform[:3].upper()}-{hashlib.md5(f'{film_id}:{rate}'.encode('utf-8')).hexdigest()[:6].upper()}"

        result = {
            "record_id": record_id,
            "platform": platform,
            "film_id": film_id,
            "film_title": film_title,
            "rating": rate,
            "has_warning_banner": has_warning_banner,
            "sovereign_clean": sovereign_clean,
            "status": status,
            "deficiencies": non_compliant_reasons,
            "sanction_risk": sanction,
            "created_at": datetime.datetime.now().isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO ott_film_compliance
                (record_id, platform, film_id, film_title, rating,
                 has_warning_banner, sovereign_clean, status, sanction_risk, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    platform,
                    film_id,
                    film_title,
                    rate,
                    1 if has_warning_banner else 0,
                    1 if sovereign_clean else 0,
                    status,
                    sanction,
                    result["created_at"],
                ),
            )

        return result

    # 5. Track OTT 24h Takedown Requirement
    def track_ott_takedown(
        self,
        platform: str,
        film_id: str,
        reason: str,
        notice_timestamp: Optional[str] = None,
        resolved_timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Tracks the 24-hour statutory takedown deadline for online streaming services under Article 19 Law 05/2022."""
        now = datetime.datetime.now()
        notice_str = notice_timestamp or now.isoformat()
        try:
            notice_dt = datetime.datetime.fromisoformat(notice_str)
        except Exception:
            notice_dt = now

        if resolved_timestamp is not None:
            try:
                resolved_dt = datetime.datetime.fromisoformat(resolved_timestamp)
            except Exception:
                resolved_dt = now
            hours_elapsed = (resolved_dt - notice_dt).total_seconds() / 3600.0
            status = "COMPLIANT_REMOVED_ON_TIME" if hours_elapsed <= 24.0 else "VIOLATION_TAKEDOWN_OVERDUE"
        else:
            hours_elapsed = (now - notice_dt).total_seconds() / 3600.0
            status = "PENDING_WITHIN_24H" if hours_elapsed <= 24.0 else "VIOLATION_TAKEDOWN_OVERDUE"

        takedown_id = f"TD-FILM-{hashlib.md5(f'{platform}:{film_id}:{notice_str}'.encode('utf-8')).hexdigest()[:6].upper()}"

        result = {
            "takedown_id": takedown_id,
            "platform": platform,
            "film_id": film_id,
            "reason": reason,
            "notice_timestamp": notice_str,
            "resolved_timestamp": resolved_timestamp,
            "hours_elapsed": round(hours_elapsed, 2),
            "deadline_hours": 24.0,
            "status": status,
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO ott_film_takedowns
                (takedown_id, platform, film_id, reason, notice_timestamp,
                 resolved_timestamp, hours_elapsed, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    takedown_id,
                    platform,
                    film_id,
                    reason,
                    notice_str,
                    resolved_timestamp,
                    hours_elapsed,
                    status,
                    result["created_at"],
                ),
            )

        return result

    # 6. List Records
    def list_records(self, category: str = "classifications", limit: int = 20) -> List[Dict[str, Any]]:
        """Queries database records across cinema regulation domains."""
        cat = category.lower().strip()
        with self._get_connection() as conn:
            if cat in ["permits", "gphpp"]:
                cursor = conn.execute("SELECT * FROM film_censorship_permits ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["quotas", "screens", "cinemas"]:
                cursor = conn.execute("SELECT * FROM cinema_screen_quotas ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["ott", "streaming"]:
                cursor = conn.execute("SELECT * FROM ott_film_compliance ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["takedowns"]:
                cursor = conn.execute("SELECT * FROM ott_film_takedowns ORDER BY id DESC LIMIT ?", (limit,))
            else:
                cursor = conn.execute("SELECT * FROM film_classifications ORDER BY id DESC LIMIT ?", (limit,))

            return [dict(row) for row in cursor.fetchall()]

    # 7. Summary Status Telemetry
    def get_status(self) -> Dict[str, Any]:
        """Aggregates system-wide cinema, age rating and quota compliance telemetry."""
        with self._get_connection() as conn:
            total_classified = conn.execute("SELECT COUNT(*) FROM film_classifications").fetchone()[0]
            banned_films = conn.execute("SELECT COUNT(*) FROM film_classifications WHERE rating = 'C'").fetchone()[0]
            total_permits = conn.execute("SELECT COUNT(*) FROM film_censorship_permits").fetchone()[0]
            total_quotas = conn.execute("SELECT COUNT(*) FROM cinema_screen_quotas").fetchone()[0]
            non_compliant_quotas = conn.execute("SELECT COUNT(*) FROM cinema_screen_quotas WHERE status = 'NON_COMPLIANT'").fetchone()[0]
            total_ott = conn.execute("SELECT COUNT(*) FROM ott_film_compliance").fetchone()[0]
            ott_violations = conn.execute("SELECT COUNT(*) FROM ott_film_compliance WHERE status = 'NON_COMPLIANT'").fetchone()[0]
            total_takedowns = conn.execute("SELECT COUNT(*) FROM ott_film_takedowns").fetchone()[0]

        quota_compliance_pct = round((1.0 - (non_compliant_quotas / total_quotas)) * 100.0, 1) if total_quotas > 0 else 100.0

        return {
            "status": "HEALTHY",
            "statutory_law": "Luật Điện ảnh 2022 (Luật số 05/2022/QH15) & Thông tư 05/2023/TT-BVHTTDL",
            "total_films_classified": total_classified,
            "banned_films_count": banned_films,
            "total_distribution_permits_gphpp": total_permits,
            "total_cinema_quota_audits": total_quotas,
            "quota_compliance_rate_pct": quota_compliance_pct,
            "total_ott_films_audited": total_ott,
            "ott_violations_count": ott_violations,
            "total_ott_takedowns": total_takedowns,
            "timestamp": datetime.datetime.now().isoformat(),
        }
