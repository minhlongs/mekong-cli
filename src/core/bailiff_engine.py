"""
Autonomous Vietnamese Bailiff, Evidence Protocol (Vi Bằng) & Civil Enforcement Suite.
Statutory Framework:
- Nghị định số 08/2020/NĐ-CP ngày 08/01/2020 của Chính phủ về tổ chức và hoạt động của Thừa phát lại
- Thông tư số 05/2020/TT-BTP ngày 28/08/2020 của Bộ Tư pháp quy định chi tiết Nghị định 08/2020/NĐ-CP
- Luật Thi hành án dân sự 2008 (sửa đổi, bổ sung 2014, Luật số 64/2014/QH13)
- Bộ luật Tố tụng dân sự 2015 (Giá trị chứng cứ của Vi bằng theo Điều 95; tống đạt văn bản tố tụng theo Chương X)

Strict Standard Library Only: Zero external HTTP, zero vendor SDKs.
"""

from __future__ import annotations

import os
import json
import sqlite3
import datetime
import uuid
from typing import Dict, Any, List, Optional

EVENT_CATEGORIES = {
    "PROPERTY_STATUS": "Ghi nhận hiện trạng nhà đất, công trình xây dựng, ranh giới tài sản",
    "TRANSACTION_DELIVERY": "Ghi nhận việc giao nhận tiền, giao nhận tài sản, bàn giao nhà xưởng",
    "INTERNET_IP_INFRINGEMENT": "Ghi nhận hành vi xâm phạm quyền tác giả, nhãn hiệu trên internet, mạng xã hội",
    "INHERITANCE_WILL": "Ghi nhận việc lập di chúc, phân chia di sản thừa kế, giao nhận tài sản thừa kế",
    "COMMERCIAL_DEFAULT": "Ghi nhận việc vi phạm hợp đồng kinh tế, chậm tiến độ, từ chối thực hiện nghĩa vụ",
    "CORPORATE_MEETING": "Ghi nhận cuộc họp Đại hội đồng cổ đông, Hội đồng quản trị, phiên hòa giải",
}

# Điều 37 Nghị định 08/2020/NĐ-CP: Các trường hợp không được lập vi bằng
PROHIBITED_KEYWORDS = [
    "chuyển nhượng quyền sử dụng đất không có giấy tờ",
    "mua bán nhà đất không có sổ đỏ",
    "thay thế công chứng mua bán đất",
    "bí mật đời tư trái phép",
    "bí mật nhà nước",
    "xâm phạm an ninh quốc gia",
    "xác nhận nội dung hợp đồng thay công chứng",
]


class BailiffEngine:
    """Core engine for Vietnamese Bailiff operations, Vi Bằng evidence protocols, and civil enforcement."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            db_path = os.path.join(base_dir, "bailiff.db")
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
                CREATE TABLE IF NOT EXISTS evidence_protocols (
                    protocol_id TEXT PRIMARY KEY,
                    bailiff_name TEXT NOT NULL,
                    office_name TEXT NOT NULL,
                    requester_name TEXT NOT NULL,
                    event_category TEXT NOT NULL,
                    event_description TEXT NOT NULL,
                    location TEXT NOT NULL,
                    media_attachments_count INTEGER NOT NULL,
                    doj_registered INTEGER NOT NULL,
                    is_valid INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS process_services (
                    service_id TEXT PRIMARY KEY,
                    court_or_agency TEXT NOT NULL,
                    recipient_name TEXT NOT NULL,
                    recipient_address TEXT NOT NULL,
                    document_title TEXT NOT NULL,
                    service_method TEXT NOT NULL,
                    service_fee_vnd REAL NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asset_verifications (
                    verification_id TEXT PRIMARY KEY,
                    debtor_name TEXT NOT NULL,
                    judgment_number TEXT NOT NULL,
                    bank_accounts_found INTEGER NOT NULL,
                    total_bank_balance_vnd REAL NOT NULL,
                    real_estate_found INTEGER NOT NULL,
                    vehicles_found INTEGER NOT NULL,
                    is_enforceable INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS civil_enforcements (
                    enforcement_id TEXT PRIMARY KEY,
                    debtor_name TEXT NOT NULL,
                    judgment_number TEXT NOT NULL,
                    judgment_amount_vnd REAL NOT NULL,
                    amount_collected_vnd REAL NOT NULL,
                    voluntary_compliance INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def create_evidence_protocol(
        self,
        requester_name: str,
        event_description: str,
        event_category: str = "PROPERTY_STATUS",
        location: str = "Số 15 Phố Tràng Tiền, Quận Hoàn Kiếm, Hà Nội",
        media_attachments_count: int = 5,
        bailiff_name: str = "Thừa phát lại Nguyễn Đức Toàn",
        office_name: str = "Văn phòng Thừa phát lại Ba Đình, Hà Nội",
        doj_registered: bool = True,
        registration_days_elapsed: int = 2,
    ) -> Dict[str, Any]:
        """
        Draft and register Evidence Protocol (Vi Bằng) under Decree 08/2020/NĐ-CP Articles 36-41.
        Vi bằng serves as legal proof/evidence before the Court under Article 36(3).
        Checks for prohibited statutory scopes under Article 37.
        Must be registered with Department of Justice within 3 working days (Article 39(4)).
        """
        protocol_id = f"BLF-VB-{uuid.uuid4().hex[:8].upper()}"
        violations = []
        desc_lower = event_description.lower()

        # Check prohibited scopes under Article 37
        for kw in PROHIBITED_KEYWORDS:
            if kw in desc_lower:
                violations.append(f"Hành vi thuộc diện cấm lập Vi bằng theo Điều 37 Nghị định 08/2020/NĐ-CP: '{kw}'")

        cat_upper = event_category.strip().upper()
        if cat_upper not in EVENT_CATEGORIES:
            violations.append(f"Danh mục sự kiện không hợp lệ: {', '.join(EVENT_CATEGORIES.keys())}")

        if not doj_registered:
            violations.append("Vi bằng chưa được gửi đăng ký tại Sở Tư pháp nơi đặt văn phòng (Điều 39 khoản 4)")

        if registration_days_elapsed > 3:
            violations.append(f"Quá thời hạn gửi đăng ký Sở Tư pháp ({registration_days_elapsed} ngày > 03 ngày làm việc theo Điều 39)")

        is_valid = len(violations) == 0
        status = "PROTOCOL_REGISTERED" if is_valid else "REJECTED_PROHIBITED_SCOPE"
        statutory_notes = (
            "Vi bằng đã vào sổ đăng ký Sở Tư pháp, có giá trị chứng cứ để Tòa án xem xét khi giải quyết vụ án (Điều 36)"
            if is_valid
            else "; ".join(violations)
        )

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO evidence_protocols (
                    protocol_id, bailiff_name, office_name, requester_name,
                    event_category, event_description, location, media_attachments_count,
                    doj_registered, is_valid, status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                protocol_id, bailiff_name.strip(), office_name.strip(), requester_name.strip(),
                cat_upper, event_description.strip(), location.strip(), media_attachments_count,
                1 if doj_registered else 0, 1 if is_valid else 0, status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "protocol_id": protocol_id,
            "bailiff_name": bailiff_name,
            "office_name": office_name,
            "requester_name": requester_name,
            "event_category": cat_upper,
            "category_name": EVENT_CATEGORIES.get(cat_upper, cat_upper),
            "event_description": event_description,
            "location": location,
            "media_attachments_count": media_attachments_count,
            "doj_registered": doj_registered,
            "registration_days_elapsed": registration_days_elapsed,
            "is_valid": is_valid,
            "status": status,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def serve_process_document(
        self,
        recipient_name: str,
        document_title: str,
        recipient_address: str = "Tổ dân phố 8, Phường Cống Vị, Ba Đình, Hà Nội",
        court_or_agency: str = "Tòa án nhân dân Thành phố Hà Nội",
        service_method: str = "DIRECT_DELIVERY",
        service_fee_vnd: float = 150000.0,
        recipient_present: bool = True,
    ) -> Dict[str, Any]:
        """
        Serve procedural document of Court, Procuracy, or Civil Judgment Enforcement Agency under Articles 32-35.
        Methods: DIRECT_DELIVERY, POSTAL_AFFIXED, AUTHORITY_ASSISTANCE.
        """
        service_id = f"BLF-SRV-{uuid.uuid4().hex[:8].upper()}"
        method_upper = service_method.strip().upper()

        if recipient_present and method_upper == "DIRECT_DELIVERY":
            status = "SERVED_SUCCESSFULLY"
            statutory_notes = "Đã tống đạt trực tiếp cho đương sự có ký nhận biên bản tống đạt theo Điều 33"
        elif method_upper == "POSTAL_AFFIXED":
            status = "SERVED_BY_POSTING"
            statutory_notes = "Đương sự vắng mặt, đã lập biên bản niêm yết công khai tại nơi cư trú và UBND xã/phường (Điều 34)"
        elif method_upper == "AUTHORITY_ASSISTANCE":
            status = "SERVED_VIA_AUTHORITY"
            statutory_notes = "Đã tống đạt qua người đại diện tổ dân phố hoặc người thân có thẩm quyền nhận thay (Điều 33)"
        else:
            status = "FAILED_ABSENT"
            statutory_notes = "Không gặp được đương sự, địa chỉ không rõ ràng hoặc đương sự từ chối nhận văn bản"

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO process_services (
                    service_id, court_or_agency, recipient_name, recipient_address,
                    document_title, service_method, service_fee_vnd, status,
                    statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                service_id, court_or_agency.strip(), recipient_name.strip(), recipient_address.strip(),
                document_title.strip(), method_upper, service_fee_vnd, status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "service_id": service_id,
            "court_or_agency": court_or_agency,
            "recipient_name": recipient_name,
            "recipient_address": recipient_address,
            "document_title": document_title,
            "service_method": method_upper,
            "service_fee_vnd": service_fee_vnd,
            "status": status,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def verify_asset_conditions(
        self,
        debtor_name: str,
        judgment_number: str = "Bản án số 45/2025/KDTM-ST",
        bank_accounts_found: int = 2,
        total_bank_balance_vnd: float = 350000000.0,
        real_estate_found: int = 1,
        vehicles_found: int = 1,
    ) -> Dict[str, Any]:
        """
        Verify debtor's financial and property conditions under Articles 43-50.
        Verifies accounts at commercial banks, land registry assets, and motor vehicles.
        """
        verification_id = f"BLF-VER-{uuid.uuid4().hex[:8].upper()}"
        is_enforceable = (total_bank_balance_vnd > 0) or (real_estate_found > 0) or (vehicles_found > 0)

        if is_enforceable:
            status = "CONDITIONS_CONFIRMED"
            statutory_notes = (
                f"Xác minh có điều kiện thi hành án: {bank_accounts_found} tài khoản ngân hàng "
                f"({total_bank_balance_vnd:,.0f} VND), {real_estate_found} bất động sản, {vehicles_found} phương tiện"
            )
        else:
            status = "INSOLVENT_NO_ASSETS"
            statutory_notes = "Chưa phát hiện tài sản hoặc thu nhập có thể kê biên; thuộc diện chưa có điều kiện thi hành án"

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO asset_verifications (
                    verification_id, debtor_name, judgment_number, bank_accounts_found,
                    total_bank_balance_vnd, real_estate_found, vehicles_found,
                    is_enforceable, status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                verification_id, debtor_name.strip(), judgment_number.strip(), bank_accounts_found,
                total_bank_balance_vnd, real_estate_found, vehicles_found,
                1 if is_enforceable else 0, status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "verification_id": verification_id,
            "debtor_name": debtor_name,
            "judgment_number": judgment_number,
            "bank_accounts_found": bank_accounts_found,
            "total_bank_balance_vnd": total_bank_balance_vnd,
            "real_estate_found": real_estate_found,
            "vehicles_found": vehicles_found,
            "is_enforceable": is_enforceable,
            "status": status,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def execute_civil_judgment(
        self,
        debtor_name: str,
        judgment_amount_vnd: float,
        judgment_number: str = "Quyết định số 12/2026/QĐST-DS",
        amount_collected_vnd: float = 0.0,
        voluntary_compliance: bool = True,
    ) -> Dict[str, Any]:
        """
        Organize enforcement of civil judgment under Articles 51-56.
        Bailiff directly receives voluntary payments or executes recovery.
        """
        enforcement_id = f"BLF-ENF-{uuid.uuid4().hex[:8].upper()}"

        if amount_collected_vnd >= judgment_amount_vnd:
            status = "FULLY_SATISFIED"
            statutory_notes = f"Đã thi hành xong toàn bộ số tiền {judgment_amount_vnd:,.0f} VND theo bản án"
        elif amount_collected_vnd > 0:
            status = "PARTIALLY_EXECUTED"
            statutory_notes = f"Đã thu hồi một phần {amount_collected_vnd:,.0f} / {judgment_amount_vnd:,.0f} VND"
        elif voluntary_compliance:
            status = "VOLUNTARY_NOTICE_ISSUED"
            statutory_notes = "Đã tống đạt quyết định thi hành án và ấn định thời hạn tự nguyện thi hành 10 ngày"
        else:
            status = "COERCION_PREPARED"
            statutory_notes = "Hết thời hạn tự nguyện, đã lập kế hoạch cưỡng chế kê biên tài sản phối hợp công an (Điều 54)"

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO civil_enforcements (
                    enforcement_id, debtor_name, judgment_number, judgment_amount_vnd,
                    amount_collected_vnd, voluntary_compliance, status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                enforcement_id, debtor_name.strip(), judgment_number.strip(), judgment_amount_vnd,
                amount_collected_vnd, 1 if voluntary_compliance else 0, status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "enforcement_id": enforcement_id,
            "debtor_name": debtor_name,
            "judgment_number": judgment_number,
            "judgment_amount_vnd": judgment_amount_vnd,
            "amount_collected_vnd": amount_collected_vnd,
            "voluntary_compliance": voluntary_compliance,
            "status": status,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def list_bailiff_records(self, category: str = "ALL", limit: int = 50) -> Dict[str, Any]:
        """List registered evidence protocols, process services, asset verifications, and civil enforcements."""
        cat_upper = category.strip().upper()
        results: Dict[str, Any] = {}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            if cat_upper in ["ALL", "PROTOCOLS", "VI_BANG"]:
                cursor.execute("SELECT * FROM evidence_protocols ORDER BY created_at DESC LIMIT ?", (limit,))
                results["evidence_protocols"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "SERVICES"]:
                cursor.execute("SELECT * FROM process_services ORDER BY created_at DESC LIMIT ?", (limit,))
                results["process_services"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "VERIFICATIONS"]:
                cursor.execute("SELECT * FROM asset_verifications ORDER BY created_at DESC LIMIT ?", (limit,))
                results["asset_verifications"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "ENFORCEMENTS"]:
                cursor.execute("SELECT * FROM civil_enforcements ORDER BY created_at DESC LIMIT ?", (limit,))
                results["civil_enforcements"] = [dict(row) for row in cursor.fetchall()]

        return results

    def get_bailiff_telemetry(self) -> Dict[str, Any]:
        """Aggregate national bailiff evidence protocols, service of process, and recovery volume."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN is_valid = 1 THEN 1 ELSE 0 END) FROM evidence_protocols")
            p_row = cursor.fetchone()
            total_protocols = p_row[0] or 0
            valid_protocols = p_row[1] or 0

            cursor.execute("SELECT COUNT(*), SUM(service_fee_vnd) FROM process_services")
            s_row = cursor.fetchone()
            total_services = s_row[0] or 0
            total_service_fees_vnd = s_row[1] or 0.0

            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN is_enforceable = 1 THEN 1 ELSE 0 END) FROM asset_verifications")
            v_row = cursor.fetchone()
            total_verifications = v_row[0] or 0
            enforceable_debtors = v_row[1] or 0

            cursor.execute("SELECT COUNT(*), SUM(judgment_amount_vnd), SUM(amount_collected_vnd) FROM civil_enforcements")
            e_row = cursor.fetchone()
            total_enforcements = e_row[0] or 0
            total_judgment_amount_vnd = e_row[1] or 0.0
            total_collected_amount_vnd = e_row[2] or 0.0

        return {
            "total_evidence_protocols": total_protocols,
            "valid_evidence_protocols": valid_protocols,
            "total_process_services": total_services,
            "total_service_fees_vnd": total_service_fees_vnd,
            "total_asset_verifications": total_verifications,
            "enforceable_debtors": enforceable_debtors,
            "total_civil_enforcements": total_enforcements,
            "total_judgment_amount_vnd": total_judgment_amount_vnd,
            "total_collected_amount_vnd": total_collected_amount_vnd,
            "database_path": self.db_path,
        }
