"""
Vietnamese Advertising, Media & Digital Marketing Compliance Engine.
Pure Python standard library implementation adhering to tests/test_core_boundary.py.

Statutory Framework:
- Luật Quảng cáo 2012 (Luật số 16/2012/QH13):
  * Điều 8: Hành vi cấm trong quảng cáo (từ ngữ "nhất", "duy nhất", "tốt nhất", "số một", quảng cáo sai sự thật).
  * Điều 21, 22: Thời lượng quảng cáo phát thanh/truyền hình (<= 10% tổng thời lượng, <= 5% đối với truyền hình trả tiền, ngắt phim <= 2 lần, mỗi lần <= 5 phút).
- Nghị định số 181/2013/NĐ-CP: Hướng dẫn chi tiết Luật Quảng cáo, Giấy xác nhận nội dung quảng cáo (XNNDQC) cho sản phẩm đặc biệt.
- Nghị định số 70/2021/NĐ-CP: Quy định quảng cáo xuyên biên giới (Facebook, Google, TikTok, YouTube), hạn gỡ bỏ vi phạm trong 24 giờ.
- Nghị định số 38/2021/NĐ-CP & Nghị định số 129/2021/NĐ-CP: Xử phạt vi phạm hành chính trong hoạt động quảng cáo.
- QCVN 17:2018/BXD: Quy chuẩn kỹ thuật quốc gia về xây dựng và lắp đặt biển quảng cáo ngoài trời (OOH billboard).
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


class AdvertisingEngine:
    """Core engine for Vietnamese advertising compliance and verification."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            base_dir = os.path.join(os.getcwd(), ".mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "advertising.db")
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
                CREATE TABLE IF NOT EXISTS ad_content_approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    xnndqc_code TEXT UNIQUE NOT NULL,
                    product_name TEXT NOT NULL,
                    product_category TEXT NOT NULL,
                    applicant_name TEXT NOT NULL,
                    license_number TEXT NOT NULL,
                    issue_date TEXT NOT NULL,
                    valid_until TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ad_content_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    check_id TEXT UNIQUE NOT NULL,
                    content_preview TEXT NOT NULL,
                    product_type TEXT NOT NULL,
                    has_evidence INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    detected_prohibited_terms TEXT,
                    missing_disclaimers TEXT,
                    estimated_fine_min_vnd INTEGER NOT NULL,
                    estimated_fine_max_vnd INTEGER NOT NULL,
                    legal_basis TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS cross_border_takedowns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    takedown_id TEXT UNIQUE NOT NULL,
                    platform TEXT NOT NULL,
                    ad_id TEXT NOT NULL,
                    requester TEXT NOT NULL,
                    violation_type TEXT NOT NULL,
                    notice_timestamp TEXT NOT NULL,
                    resolved_timestamp TEXT,
                    status TEXT NOT NULL,
                    hours_elapsed REAL NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ooh_billboard_permits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    permit_id TEXT UNIQUE NOT NULL,
                    location_type TEXT NOT NULL,
                    structure_type TEXT NOT NULL,
                    area_sqm REAL NOT NULL,
                    height_m REAL NOT NULL,
                    clearance_m REAL NOT NULL,
                    duration_days INTEGER,
                    status TEXT NOT NULL,
                    deficiencies TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS broadcast_ad_slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slot_id TEXT UNIQUE NOT NULL,
                    channel_type TEXT NOT NULL,
                    program_duration_min REAL NOT NULL,
                    ad_duration_min REAL NOT NULL,
                    ad_ratio_pct REAL NOT NULL,
                    break_count INTEGER NOT NULL,
                    max_break_min REAL NOT NULL,
                    status TEXT NOT NULL,
                    excess_min REAL NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    # 1. Automated Ad Content Check (Luật Quảng cáo Điều 8, NĐ 38/2021/NĐ-CP)
    def check_ad_content(
        self,
        text: str,
        product_type: str = "general",
        has_evidence: bool = False,
    ) -> Dict[str, Any]:
        """Scans ad text for prohibited superlatives, absolute claims, and missing mandatory disclaimers."""
        text_lower = text.lower()
        prohibited_terms = [
            "tốt nhất",
            "nhất",
            "duy nhất",
            "số một",
            "số 1",
            "hàng đầu",
            "đỉnh cao nhất",
            "chữa khỏi hoàn toàn",
            "trị dứt điểm",
            "100% hiệu quả",
            "không tác dụng phụ",
        ]

        detected_terms = []
        for term in prohibited_terms:
            pattern = r"\b" + re.escape(term) + r"\b"
            if re.search(pattern, text_lower):
                detected_terms.append(term)

        missing_disclaimers = []
        prod_type_normalized = product_type.lower().strip()

        # Specific disclaimers per category
        if "supplement" in prod_type_normalized or "thực phẩm chức năng" in prod_type_normalized or "bảo vệ sức khỏe" in prod_type_normalized:
            required_phrase = "thực phẩm này không phải là thuốc và không có tác dụng thay thế thuốc chữa bệnh"
            if required_phrase not in text_lower:
                missing_disclaimers.append("Thiếu câu khuyến cáo bắt buộc: 'Thực phẩm này không phải là thuốc và không có tác dụng thay thế thuốc chữa bệnh'")

        elif "cosmetic" in prod_type_normalized or "mỹ phẩm" in prod_type_normalized:
            # Check for drug claims in cosmetics
            drug_claims = ["trị dứt điểm", "chữa khỏi", "đặc trị nám", "diệt vi khuẩn tận gốc"]
            for claim in drug_claims:
                if claim in text_lower:
                    detected_terms.append(f"quảng cáo mỹ phẩm có công dụng như thuốc: '{claim}'")

        elif "pharma" in prod_type_normalized or "thuốc" in prod_type_normalized:
            prescription_terms = ["thuốc kê đơn", "chỉ định của bác sĩ chuyên khoa", "kháng sinh đặc hiệu"]
            for pt in prescription_terms:
                if pt in text_lower:
                    detected_terms.append(f"nghi vấn quảng cáo thuốc kê đơn bị cấm: '{pt}'")

        # Determine compliance status and fine estimation under NĐ 38/2021/NĐ-CP
        is_compliant = True
        fine_min = 0
        fine_max = 0
        legal_basis = []

        # If superlatives found without official certification documents
        if detected_terms and not has_evidence:
            is_compliant = False
            fine_min += 10000000
            fine_max += 20000000
            legal_basis.append("Điều 34 Nghị định số 38/2021/NĐ-CP (sử dụng từ ngữ 'nhất', 'duy nhất', 'tốt nhất', 'số 1' không có tài liệu hợp pháp)")

        if missing_disclaimers:
            is_compliant = False
            fine_min += 10000000
            fine_max += 15000000
            legal_basis.append("Điều 52 Nghị định số 38/2021/NĐ-CP (thiếu khuyến cáo bắt buộc đối với thực phẩm chức năng/bảo vệ sức khỏe)")

        # Severe false claim fines
        if any(term in ["chữa khỏi hoàn toàn", "trị dứt điểm", "100% hiệu quả"] for term in detected_terms):
            is_compliant = False
            fine_min += 50000000
            fine_max += 70000000
            legal_basis.append("Điều 34 Khoản 5 Nghị định số 38/2021/NĐ-CP (quảng cáo sai sự thật hoặc gây nhầm lẫn công dụng)")

        if not is_compliant:
            status = "NON_COMPLIANT"
        elif detected_terms and has_evidence:
            status = "WARNING_REQUIRES_PROOF_VERIFICATION"
        else:
            status = "COMPLIANT"

        check_id = f"CHK-{hashlib.sha256(text.encode('utf-8')).hexdigest()[:10].upper()}"
        preview = text[:80] + ("..." if len(text) > 80 else "")

        result = {
            "check_id": check_id,
            "content_preview": preview,
            "product_type": product_type,
            "has_evidence": has_evidence,
            "status": status,
            "is_compliant": is_compliant,
            "detected_prohibited_terms": detected_terms,
            "missing_disclaimers": missing_disclaimers,
            "estimated_fine_min_vnd": fine_min,
            "estimated_fine_max_vnd": fine_max,
            "legal_basis": "; ".join(legal_basis) if legal_basis else "Luật Quảng cáo 2012 (Tuân thủ đầy đủ)",
            "created_at": datetime.datetime.now().isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO ad_content_checks
                (check_id, content_preview, product_type, has_evidence, status,
                 detected_prohibited_terms, missing_disclaimers, estimated_fine_min_vnd,
                 estimated_fine_max_vnd, legal_basis, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    check_id,
                    preview,
                    product_type,
                    1 if has_evidence else 0,
                    status,
                    json.dumps(detected_terms, ensure_ascii=False),
                    json.dumps(missing_disclaimers, ensure_ascii=False),
                    fine_min,
                    fine_max,
                    result["legal_basis"],
                    result["created_at"],
                ),
            )

        return result

    # 2. Register Special Content Approval (XNNDQC - NĐ 181/2013/NĐ-CP)
    def register_content_approval(
        self,
        product_name: str,
        product_category: str,
        applicant_name: str,
        license_number: str,
        validity_years: int = 2,
    ) -> Dict[str, Any]:
        """Registers and issues a Special Advertising Content Approval certificate (XNNDQC)."""
        valid_cats = ["pharmaceutical", "supplement", "cosmetic", "medical_device", "chemical"]
        cat_norm = product_category.lower().strip()
        matched_cat = next((c for c in valid_cats if c in cat_norm), "other")

        now = datetime.datetime.now()
        year = now.year
        seq_hash = hashlib.md5(f"{product_name}:{applicant_name}:{now.timestamp()}".encode("utf-8")).hexdigest()[:5].upper()
        xnndqc_code = f"XNNDQC-{year}-{seq_hash}"

        valid_until = (now + datetime.timedelta(days=validity_years * 365)).strftime("%Y-%m-%d")

        result = {
            "xnndqc_code": xnndqc_code,
            "product_name": product_name,
            "product_category": matched_cat,
            "applicant_name": applicant_name,
            "license_number": license_number,
            "issue_date": now.strftime("%Y-%m-%d"),
            "valid_until": valid_until,
            "status": "APPROVED",
            "statutory_authority": "Cục ATTP / Cục Quản lý Dược / Sở Y tế",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO ad_content_approvals
                (xnndqc_code, product_name, product_category, applicant_name,
                 license_number, issue_date, valid_until, status, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    xnndqc_code,
                    product_name,
                    matched_cat,
                    applicant_name,
                    license_number,
                    result["issue_date"],
                    valid_until,
                    "APPROVED",
                    json.dumps(result, ensure_ascii=False),
                    result["created_at"],
                ),
            )

        return result

    # 3. OOH Billboard & Banner Permit Verification (QCVN 17:2018/BXD & Luật Quảng cáo)
    def verify_ooh_billboard(
        self,
        location_type: str,
        area_sqm: float,
        height_m: float,
        clearance_m: float,
        duration_days: Optional[int] = None,
        structure_type: str = "billboard",
    ) -> Dict[str, Any]:
        """Validates outdoor billboard spatial zoning, dimensions, and banner duration."""
        deficiencies = []
        loc = location_type.lower().strip()
        struct = structure_type.lower().strip()

        # Dimension thresholds under QCVN 17:2018/BXD
        max_area = 120.0
        max_height = 15.0
        min_clearance = 5.0

        if loc in ["highway", "expressway", "quoc_lo"]:
            max_area = 120.0
            max_height = 15.0
            min_clearance = 5.0
        elif loc in ["urban_standalone", "do_thi_doc_lap"]:
            max_area = 40.0
            max_height = 10.0
            min_clearance = 4.0
        elif loc in ["urban_wall", "tuong_nha"]:
            max_area = 20.0
            max_height = 8.0
            min_clearance = 3.0
        elif struct == "banner" or loc in ["banner", "bang_ron"]:
            max_area = 10.0
            max_height = 2.0
            min_clearance = 3.5

        if area_sqm > max_area:
            deficiencies.append(f"Diện tích bảng ({area_sqm} m²) vượt quá giới hạn tối đa cho phép ({max_area} m²)")

        if height_m > max_height:
            deficiencies.append(f"Chiều cao bảng ({height_m} m) vượt quá giới hạn an toàn kết cấu ({max_height} m)")

        if clearance_m < min_clearance:
            deficiencies.append(f"Khoảng cách tĩnh không an toàn ({clearance_m} m) thấp hơn quy chuẩn ({min_clearance} m)")

        if struct == "banner" or loc in ["banner", "bang_ron"]:
            days = duration_days if duration_days is not None else 15
            if days > 15:
                deficiencies.append(f"Thời hạn treo băng-rôn ({days} ngày) vượt quá tối đa 15 ngày theo Điều 27 Luật Quảng cáo")

        approved = len(deficiencies) == 0
        permit_id = f"OOH-{hashlib.sha256(f'{loc}:{area_sqm}:{height_m}:{duration_days}'.encode('utf-8')).hexdigest()[:8].upper()}"

        result = {
            "permit_id": permit_id,
            "location_type": location_type,
            "structure_type": structure_type,
            "area_sqm": area_sqm,
            "max_allowed_area_sqm": max_area,
            "height_m": height_m,
            "max_allowed_height_m": max_height,
            "clearance_m": clearance_m,
            "min_required_clearance_m": min_clearance,
            "duration_days": duration_days,
            "status": "APPROVED" if approved else "REJECTED",
            "deficiencies": deficiencies,
            "created_at": datetime.datetime.now().isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO ooh_billboard_permits
                (permit_id, location_type, structure_type, area_sqm, height_m,
                 clearance_m, duration_days, status, deficiencies, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    permit_id,
                    location_type,
                    structure_type,
                    area_sqm,
                    height_m,
                    clearance_m,
                    duration_days,
                    result["status"],
                    json.dumps(deficiencies, ensure_ascii=False),
                    result["created_at"],
                ),
            )

        return result

    # 4. Cross-Border Ad Platform 24h Takedown Tracking (Nghị định số 70/2021/NĐ-CP)
    def track_cross_border_takedown(
        self,
        platform: str,
        ad_id: str,
        requester: str,
        violation_type: str,
        notice_timestamp: Optional[str] = None,
        resolved_timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Tracks the statutory 24-hour takedown requirement for cross-border digital ad platforms."""
        now = datetime.datetime.now()
        if notice_timestamp is None:
            notice_dt = now
            notice_str = notice_dt.isoformat()
        else:
            notice_str = notice_timestamp
            try:
                notice_dt = datetime.datetime.fromisoformat(notice_timestamp)
            except Exception:
                notice_dt = now

        if resolved_timestamp is not None:
            try:
                resolved_dt = datetime.datetime.fromisoformat(resolved_timestamp)
            except Exception:
                resolved_dt = now
            hours_elapsed = (resolved_dt - notice_dt).total_seconds() / 3600.0
            if hours_elapsed <= 24.0:
                status = "COMPLIANT_REMOVED_ON_TIME"
            else:
                status = "VIOLATION_TAKEDOWN_OVERDUE"
        else:
            hours_elapsed = (now - notice_dt).total_seconds() / 3600.0
            if hours_elapsed <= 24.0:
                status = "PENDING_WITHIN_24H"
            else:
                status = "VIOLATION_TAKEDOWN_OVERDUE"

        takedown_id = f"TD-{platform[:3].upper()}-{hashlib.md5(f'{ad_id}:{notice_str}'.encode('utf-8')).hexdigest()[:6].upper()}"

        result = {
            "takedown_id": takedown_id,
            "platform": platform,
            "ad_id": ad_id,
            "requester": requester,
            "violation_type": violation_type,
            "notice_timestamp": notice_str,
            "resolved_timestamp": resolved_timestamp,
            "hours_elapsed": round(hours_elapsed, 2),
            "deadline_hours": 24.0,
            "status": status,
            "sanction_risk": "Xử phạt hành chính 50M-70M VND và biện pháp ngăn chặn kỹ thuật" if "OVERDUE" in status else "None",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cross_border_takedowns
                (takedown_id, platform, ad_id, requester, violation_type,
                 notice_timestamp, resolved_timestamp, status, hours_elapsed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    takedown_id,
                    platform,
                    ad_id,
                    requester,
                    violation_type,
                    notice_str,
                    resolved_timestamp,
                    status,
                    hours_elapsed,
                    result["created_at"],
                ),
            )

        return result

    # 5. Broadcast Advertising Ratio Verification (Luật Quảng cáo Điều 22)
    def verify_broadcast_ratio(
        self,
        channel_type: str,
        program_duration_min: float,
        ad_duration_min: float,
        break_count: int = 1,
        max_break_min: float = 4.0,
    ) -> Dict[str, Any]:
        """Validates broadcast television and radio advertising slot ratios."""
        ad_ratio_pct = (ad_duration_min / program_duration_min * 100.0) if program_duration_min > 0 else 0.0
        ch = channel_type.lower().strip()

        # Under Law 16/2012/QH13:
        # Terrestrial / Free-to-Air: <= 10%
        # Pay TV: <= 5%
        # Film breaks: <= 2 breaks per film, each break <= 5 minutes
        max_allowed_pct = 5.0 if "pay" in ch or "tra_tien" in ch else 10.0
        deficiencies = []

        if ad_ratio_pct > max_allowed_pct:
            deficiencies.append(f"Thời lượng quảng cáo ({round(ad_ratio_pct, 1)}%) vượt quá mức cho phép ({max_allowed_pct}%)")

        if break_count > 2:
            deficiencies.append(f"Số lần ngắt để quảng cáo trong chương trình phim ({break_count} lần) vượt quá tối đa 02 lần")

        if max_break_min > 5.0:
            deficiencies.append(f"Thời lượng một lần ngắt quảng cáo ({max_break_min} phút) vượt quá tối đa 05 phút")

        compliant = len(deficiencies) == 0
        allowed_ad_min = program_duration_min * (max_allowed_pct / 100.0)
        excess_min = max(0.0, ad_duration_min - allowed_ad_min)

        slot_id = f"BC-{hashlib.md5(f'{channel_type}:{program_duration_min}:{ad_duration_min}:{break_count}'.encode('utf-8')).hexdigest()[:8].upper()}"

        result = {
            "slot_id": slot_id,
            "channel_type": channel_type,
            "program_duration_min": program_duration_min,
            "ad_duration_min": ad_duration_min,
            "ad_ratio_pct": round(ad_ratio_pct, 2),
            "max_allowed_ratio_pct": max_allowed_pct,
            "break_count": break_count,
            "max_break_min": max_break_min,
            "excess_min": round(excess_min, 2),
            "status": "COMPLIANT" if compliant else "NON_COMPLIANT",
            "deficiencies": deficiencies,
            "created_at": datetime.datetime.now().isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO broadcast_ad_slots
                (slot_id, channel_type, program_duration_min, ad_duration_min,
                 ad_ratio_pct, break_count, max_break_min, status, excess_min, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    slot_id,
                    channel_type,
                    program_duration_min,
                    ad_duration_min,
                    ad_ratio_pct,
                    break_count,
                    max_break_min,
                    result["status"],
                    excess_min,
                    result["created_at"],
                ),
            )

        return result

    # 6. List Records
    def list_records(self, category: str = "checks", limit: int = 20) -> List[Dict[str, Any]]:
        """Queries database records across advertising compliance domains."""
        cat = category.lower().strip()
        with self._get_connection() as conn:
            if cat in ["approvals", "xnndqc"]:
                cursor = conn.execute("SELECT * FROM ad_content_approvals ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["takedowns", "cross_border"]:
                cursor = conn.execute("SELECT * FROM cross_border_takedowns ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["billboards", "ooh", "permits"]:
                cursor = conn.execute("SELECT * FROM ooh_billboard_permits ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["broadcast", "slots"]:
                cursor = conn.execute("SELECT * FROM broadcast_ad_slots ORDER BY id DESC LIMIT ?", (limit,))
            else:
                cursor = conn.execute("SELECT * FROM ad_content_checks ORDER BY id DESC LIMIT ?", (limit,))

            return [dict(row) for row in cursor.fetchall()]

    # 7. Summary Status Telemetry
    def get_status(self) -> Dict[str, Any]:
        """Aggregates system-wide advertising compliance telemetry."""
        with self._get_connection() as conn:
            total_checks = conn.execute("SELECT COUNT(*) FROM ad_content_checks").fetchone()[0]
            non_compliant_checks = conn.execute("SELECT COUNT(*) FROM ad_content_checks WHERE status = 'NON_COMPLIANT'").fetchone()[0]
            total_approvals = conn.execute("SELECT COUNT(*) FROM ad_content_approvals").fetchone()[0]
            total_takedowns = conn.execute("SELECT COUNT(*) FROM cross_border_takedowns").fetchone()[0]
            overdue_takedowns = conn.execute("SELECT COUNT(*) FROM cross_border_takedowns WHERE status = 'VIOLATION_TAKEDOWN_OVERDUE'").fetchone()[0]
            total_permits = conn.execute("SELECT COUNT(*) FROM ooh_billboard_permits").fetchone()[0]
            total_broadcast = conn.execute("SELECT COUNT(*) FROM broadcast_ad_slots").fetchone()[0]

        compliance_rate_pct = round((1.0 - (non_compliant_checks / total_checks)) * 100.0, 1) if total_checks > 0 else 100.0

        return {
            "status": "HEALTHY",
            "total_content_checks": total_checks,
            "non_compliant_checks": non_compliant_checks,
            "compliance_rate_pct": compliance_rate_pct,
            "total_special_approvals_xnndqc": total_approvals,
            "total_cross_border_takedowns": total_takedowns,
            "overdue_cross_border_takedowns": overdue_takedowns,
            "total_ooh_billboard_permits": total_permits,
            "total_broadcast_slots_audited": total_broadcast,
            "timestamp": datetime.datetime.now().isoformat(),
        }
