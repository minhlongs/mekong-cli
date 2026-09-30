"""
Autonomous Vietnamese Property Auction, Distressed Asset Liquidation & Judicial Asset Disposal Suite.
Statutory Framework:
- Luật Đấu giá tài sản 2016 (Luật số 01/2016/QH14)
- Luật sửa đổi, bổ sung một số điều của Luật Đấu giá tài sản 2024 (Luật số 37/2024/QH15)
- Nghị định số 62/2017/NĐ-CP & Nghị định số 47/2023/NĐ-CP quy định chi tiết Luật Đấu giá tài sản
- Luật Quản lý, sử dụng tài sản công 2017 & Luật Đất đai 2024 (Điều kiện đấu giá QSDĐ)
- Luật Các tổ chức tín dụng 2024 & Nghị quyết 42/2017/QH14 (Xử lý nợ xấu, tài sản bảo đảm)
- Bộ luật Hình sự 2015 (Điều 218 về Tội vi phạm quy định về hoạt động bán đấu giá tài sản)

Strict Standard Library Only: Zero external HTTP, zero vendor SDKs.
"""

from __future__ import annotations

import os
import json
import sqlite3
import datetime
import uuid
import hashlib
from typing import Dict, Any, List, Optional

AUCTION_ASSET_TYPES = {
    "PUBLIC_PROPERTY": "Tài sản công nhà nước (xe công vụ, trụ sở, máy móc trang thiết bị)",
    "LAND_USE_RIGHT": "Quyền sử dụng đất (giao đất có thu tiền, cho thuê đất, dự án đầu tư)",
    "DISTRESSED_DEBT": "Tài sản bảo đảm xử lý nợ xấu ngân hàng thương mại và VAMC",
    "ENFORCEMENT_ASSET": "Tài sản kê biên thi hành án dân sự theo Luật THADS",
    "CONFISCATED_GOODS": "Tang vật, phương tiện vi phạm hành chính hoặc hình sự bị tịch thu",
    "MINING_SPECTRUM_VEHICLE": "Quyền khai thác khoáng sản, quyền sử dụng tần số vô tuyến điện, biển số xe ô tô",
}

AUCTION_FORMATS = {
    "ONLINE_PORTAL": "Đấu giá trực tuyến qua Cổng đấu giá tài sản quốc gia (National Property Auction Portal)",
    "DIRECT_VOTING": "Đấu giá bằng bỏ phiếu trực tiếp tại cuộc đấu giá",
    "INDIRECT_VOTING": "Đấu giá bằng bỏ phiếu gián tiếp qua đường bưu chính",
    "ORAL_BIDDING": "Đấu giá trực tiếp bằng lời nói tại cuộc đấu giá",
}


class AuctionEngine:
    """Core engine for Vietnamese Property Auction, Asset Liquidation and Anti-Collusion Auditing."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            db_path = os.path.join(base_dir, "auction.db")
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
                CREATE TABLE IF NOT EXISTS auctioneers (
                    auctioneer_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    certificate_no TEXT NOT NULL,
                    org_name TEXT NOT NULL,
                    issue_date TEXT NOT NULL,
                    is_practicing INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auction_assets (
                    asset_id TEXT PRIMARY KEY,
                    asset_name TEXT NOT NULL,
                    asset_type TEXT NOT NULL,
                    owner_agency TEXT NOT NULL,
                    starting_price_vnd REAL NOT NULL,
                    step_price_vnd REAL NOT NULL,
                    deposit_percent REAL NOT NULL,
                    deposit_amount_vnd REAL NOT NULL,
                    notice_days INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bidders (
                    bidder_id TEXT PRIMARY KEY,
                    asset_id TEXT NOT NULL,
                    bidder_name TEXT NOT NULL,
                    id_card_or_tax_code TEXT NOT NULL,
                    deposit_paid_vnd REAL NOT NULL,
                    is_eligible INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auction_sessions (
                    session_id TEXT PRIMARY KEY,
                    asset_id TEXT NOT NULL,
                    auctioneer_id TEXT NOT NULL,
                    auction_format TEXT NOT NULL,
                    winning_bidder_id TEXT NOT NULL,
                    winning_price_vnd REAL NOT NULL,
                    price_increase_vnd REAL NOT NULL,
                    signed_protocol INTEGER NOT NULL,
                    is_valid INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def register_auctioneer(
        self,
        full_name: str,
        certificate_no: str = "BTP-ĐGV-108/2021",
        org_name: str = "Công ty Đấu giá Hợp danh Mekong Law",
        issue_date: str = "2021-08-15",
        is_practicing: bool = True,
    ) -> Dict[str, Any]:
        """
        Register and verify professional Auctioneer qualification under Law on Property Auction Art 10 & 14.
        Mandatory requirement: Professional Auctioneer Certificate issued by Ministry of Justice (BTP).
        """
        auctioneer_id = f"AUC-{uuid.uuid4().hex[:8].upper()}"
        violations = []

        if not full_name.strip():
            violations.append("Thiếu họ và tên đấu giá viên")

        if not certificate_no.strip() or "BTP" not in certificate_no.upper():
            violations.append("Chứng chỉ hành nghề đấu giá phải do Bộ Tư pháp cấp (mã hiệu BTP theo quy định)")

        if not org_name.strip():
            violations.append("Đấu giá viên bắt buộc phải hành nghề tại một tổ chức hành nghề đấu giá tài sản")

        is_certified = len(violations) == 0 and is_practicing
        status = "CERTIFIED_PRACTICING" if is_certified else "PRACTICE_SUSPENDED_OR_INVALID"
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO auctioneers (
                    auctioneer_id, full_name, certificate_no, org_name,
                    issue_date, is_practicing, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                auctioneer_id, full_name.strip(), certificate_no.strip(), org_name.strip(),
                issue_date.strip(), 1 if is_practicing else 0, status, created_at
            ))
            conn.commit()

        return {
            "auctioneer_id": auctioneer_id,
            "full_name": full_name,
            "certificate_no": certificate_no,
            "org_name": org_name,
            "issue_date": issue_date,
            "is_practicing": is_practicing,
            "is_certified": is_certified,
            "status": status,
            "violations": violations,
            "created_at": created_at,
        }

    def register_auction_asset(
        self,
        asset_name: str,
        asset_type: str = "PUBLIC_PROPERTY",
        owner_agency: str = "UBND Thành phố Hà Nội",
        starting_price_vnd: float = 5000000000.0,
        step_price_vnd: float = 50000000.0,
        deposit_percent: float = 10.0,
        notice_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Register property for auction with mandatory statutory notice period and deposit bounds.
        Statutory Rules (Law 01/2016/QH14 & Law 37/2024/QH15):
        - General deposit: 5% to 20% of starting price (Art 39).
        - Project land use right deposit: 10% to 20% to prevent post-auction forfeiture (Law 37/2024/QH15).
        - Public notice days: Minimum 30 days for real estate / land; minimum 15 days for movable assets (Art 35).
        """
        asset_id = f"AST-{uuid.uuid4().hex[:8].upper()}"
        type_upper = asset_type.strip().upper()
        violations = []

        if type_upper not in AUCTION_ASSET_TYPES:
            violations.append(f"Loại tài sản đấu giá không hợp lệ: {', '.join(AUCTION_ASSET_TYPES.keys())}")

        if starting_price_vnd <= 0:
            violations.append("Giá khởi điểm của tài sản đấu giá phải lớn hơn 0 VND")

        # Statutory deposit percentage bounds (Điều 39 & Luật sửa đổi 2024)
        if type_upper == "LAND_USE_RIGHT":
            if deposit_percent < 10.0 or deposit_percent > 20.0:
                violations.append(
                    f"Tiền đặt trước đối với quyền sử dụng đất thực hiện dự án phải từ 10% đến 20% "
                    f"theo Luật sửa đổi 2024 (hiện tại: {deposit_percent}%)"
                )
        else:
            if deposit_percent < 5.0 or deposit_percent > 20.0:
                violations.append(
                    f"Tiền đặt trước phải từ 5% đến 20% giá khởi điểm theo Điều 39 Luật Đấu giá tài sản (hiện tại: {deposit_percent}%)"
                )

        # Minimum public notice period (Điều 35)
        is_real_estate = type_upper in ["LAND_USE_RIGHT", "PUBLIC_PROPERTY"]
        min_notice = 30 if is_real_estate else 15
        if notice_days < min_notice:
            violations.append(
                f"Thời hạn niêm yết, thông báo công khai ({notice_days} ngày) < tối thiểu {min_notice} ngày "
                f"theo Điều 35 Luật Đấu giá tài sản"
            )

        deposit_amount_vnd = starting_price_vnd * (deposit_percent / 100.0)
        is_valid = len(violations) == 0
        status = "ASSET_LISTED_FOR_AUCTION" if is_valid else "ASSET_REGISTRATION_INVALID"
        statutory_notes = (
            f"Tài sản đấu giá hợp chuẩn theo Luật Đấu giá tài sản; tiền đặt trước {deposit_percent}% "
            f"({deposit_amount_vnd:,.0f} VND), niêm yết công khai {notice_days} ngày."
            if is_valid
            else "; ".join(violations)
        )
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO auction_assets (
                    asset_id, asset_name, asset_type, owner_agency, starting_price_vnd,
                    step_price_vnd, deposit_percent, deposit_amount_vnd, notice_days,
                    status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                asset_id, asset_name.strip(), type_upper, owner_agency.strip(), starting_price_vnd,
                step_price_vnd, deposit_percent, deposit_amount_vnd, notice_days,
                status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "asset_id": asset_id,
            "asset_name": asset_name,
            "asset_type": type_upper,
            "asset_type_description": AUCTION_ASSET_TYPES.get(type_upper, type_upper),
            "owner_agency": owner_agency,
            "starting_price_vnd": starting_price_vnd,
            "step_price_vnd": step_price_vnd,
            "deposit_percent": deposit_percent,
            "deposit_amount_vnd": deposit_amount_vnd,
            "notice_days": notice_days,
            "is_valid": is_valid,
            "status": status,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def register_bidder(
        self,
        asset_id: str,
        bidder_name: str,
        id_card_or_tax_code: str,
        deposit_paid_vnd: float,
        has_prohibited_relation: bool = False,
    ) -> Dict[str, Any]:
        """
        Register a prospective bidder and verify deposit payment & statutory qualification under Art 38.
        Must have paid full deposit and not have prohibited relationship under Art 38(4).
        """
        bidder_id = f"BID-{uuid.uuid4().hex[:8].upper()}"
        violations = []

        # Retrieve asset deposit requirement
        required_deposit_vnd = 0.0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT deposit_amount_vnd FROM auction_assets WHERE asset_id = ?", (asset_id,))
            row = cursor.fetchone()
            if row:
                required_deposit_vnd = float(row[0])

        if deposit_paid_vnd < required_deposit_vnd:
            violations.append(
                f"Tiền đặt trước đã nộp ({deposit_paid_vnd:,.0f} VND) < mức yêu cầu ({required_deposit_vnd:,.0f} VND) "
                f"theo Điều 39 Luật Đấu giá tài sản"
            )

        if has_prohibited_relation:
            violations.append(
                "Người đăng ký thuộc đối tượng bị cấm tham gia đấu giá theo Khoản 4 Điều 38 "
                "(có quan hệ gia đình/lợi ích với người có thẩm quyền bán hoặc điều hành đấu giá)"
            )

        if not id_card_or_tax_code.strip():
            violations.append("Thiếu mã số thuế doanh nghiệp hoặc CCCD của người tham gia đấu giá")

        is_eligible = len(violations) == 0
        status = "BIDDER_QUALIFIED" if is_eligible else "BIDDER_DISQUALIFIED"
        statutory_notes = (
            "Đủ điều kiện tham gia trả giá tại cuộc đấu giá; tiền đặt trước đã phong tỏa tại ngân hàng."
            if is_eligible
            else "; ".join(violations)
        )
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO bidders (
                    bidder_id, asset_id, bidder_name, id_card_or_tax_code,
                    deposit_paid_vnd, is_eligible, status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bidder_id, asset_id.strip(), bidder_name.strip(), id_card_or_tax_code.strip(),
                deposit_paid_vnd, 1 if is_eligible else 0, status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "bidder_id": bidder_id,
            "asset_id": asset_id,
            "bidder_name": bidder_name,
            "id_card_or_tax_code": id_card_or_tax_code,
            "deposit_paid_vnd": deposit_paid_vnd,
            "required_deposit_vnd": required_deposit_vnd,
            "is_eligible": is_eligible,
            "status": status,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def conduct_auction_session(
        self,
        asset_id: str,
        auctioneer_id: str,
        winning_bidder_id: str,
        winning_price_vnd: float,
        auction_format: str = "ONLINE_PORTAL",
        signed_protocol: bool = True,
    ) -> Dict[str, Any]:
        """
        Record auction session result and formalize Auction Protocol under Art 44.
        Winning price must be >= starting price; protocol must be signed by all parties.
        """
        session_id = f"SES-{uuid.uuid4().hex[:8].upper()}"
        fmt_upper = auction_format.strip().upper()
        violations = []

        if fmt_upper not in AUCTION_FORMATS:
            violations.append(f"Hình thức đấu giá không hợp lệ: {', '.join(AUCTION_FORMATS.keys())}")

        starting_price_vnd = 0.0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT starting_price_vnd FROM auction_assets WHERE asset_id = ?", (asset_id,))
            row = cursor.fetchone()
            if row:
                starting_price_vnd = float(row[0])

        if winning_price_vnd < starting_price_vnd:
            violations.append(
                f"Giá trúng đấu giá ({winning_price_vnd:,.0f} VND) < Giá khởi điểm ({starting_price_vnd:,.0f} VND)"
            )

        if not signed_protocol:
            violations.append(
                "Biên bản đấu giá chưa được ký xác nhận đầy đủ theo Điều 44 Luật Đấu giá tài sản (Biên bản vô hiệu)"
            )

        price_increase_vnd = max(0.0, winning_price_vnd - starting_price_vnd)
        is_valid = len(violations) == 0
        status = "AUCTION_SUCCESS_CONTRACT_PENDING" if is_valid else "AUCTION_SESSION_INVALID"
        statutory_notes = (
            f"Cuộc đấu giá thành công hợp chuẩn theo Điều 44, 46 Luật Đấu giá tài sản; "
            f"chênh lệch tăng giá {price_increase_vnd:,.0f} VND; chuyển tiền đặt trước thành tiền đặt cọc."
            if is_valid
            else "; ".join(violations)
        )
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO auction_sessions (
                    session_id, asset_id, auctioneer_id, auction_format,
                    winning_bidder_id, winning_price_vnd, price_increase_vnd,
                    signed_protocol, is_valid, status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, asset_id.strip(), auctioneer_id.strip(), fmt_upper,
                winning_bidder_id.strip(), winning_price_vnd, price_increase_vnd,
                1 if signed_protocol else 0, 1 if is_valid else 0, status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "session_id": session_id,
            "asset_id": asset_id,
            "auctioneer_id": auctioneer_id,
            "auction_format": fmt_upper,
            "auction_format_description": AUCTION_FORMATS.get(fmt_upper, fmt_upper),
            "winning_bidder_id": winning_bidder_id,
            "winning_price_vnd": winning_price_vnd,
            "starting_price_vnd": starting_price_vnd,
            "price_increase_vnd": price_increase_vnd,
            "signed_protocol": signed_protocol,
            "is_valid": is_valid,
            "status": status,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def audit_collusion_risk(
        self,
        asset_id: str,
        bids: List[Dict[str, Any]],
        shared_network_ips: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Audit auction bidding pattern for collusion, bid-rigging or orchestrated forfeiture under Art 9 & Penal Code Art 218.
        Detects: identical bid values, single-round withdrawal clusters, shared IP origin.
        """
        audit_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"
        anomalies = []
        shared_network_ips = shared_network_ips or []

        if len(shared_network_ips) > 1 and len(set(shared_network_ips)) < len(shared_network_ips):
            anomalies.append("Phát hiện nhiều người tham gia trả giá từ cùng một địa chỉ IP / cùng mạng LAN nội bộ")

        # Bid value duplication check
        values = [b.get("amount_vnd", 0.0) for b in bids if "amount_vnd" in b]
        if len(values) > len(set(values)):
            anomalies.append("Phát hiện các mức giá trả trùng lặp bất thường giữa các đối thủ cạnh tranh độc lập")

        # Withdrawal / drop-off cluster
        withdrawn = [b for b in bids if b.get("withdrawn", False)]
        if len(bids) > 2 and (len(withdrawn) / len(bids)) >= 0.5:
            anomalies.append("Tỷ lệ người tham gia đồng loạt rút giá hoặc bỏ cuộc bất thường (nghi vấn dìm giá cho một bên trúng)")

        has_risk = len(anomalies) > 0
        risk_level = "HIGH_COLLUSION_RISK" if len(anomalies) >= 2 else ("MEDIUM_SUSPICION" if len(anomalies) == 1 else "LOW_NORMAL")
        recommendation = (
            "Chuyển hồ sơ sang Cơ quan Cảnh sát Điều tra xem xét dấu hiệu tội phạm theo Điều 218 Bộ luật Hình sự 2015."
            if has_risk
            else "Phiên đấu giá diễn ra cạnh tranh lành mạnh, không phát hiện dấu hiệu thông đồng dìm giá."
        )

        return {
            "audit_id": audit_id,
            "asset_id": asset_id,
            "total_bids_analyzed": len(bids),
            "has_collusion_risk": has_risk,
            "risk_level": risk_level,
            "anomalies": anomalies,
            "recommendation": recommendation,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    def list_auction_records(self, category: str = "ALL", limit: int = 50) -> Dict[str, Any]:
        """List registered auctioneers, assets, registered bidders, and auction sessions."""
        cat_upper = category.strip().upper()
        results: Dict[str, Any] = {}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            if cat_upper in ["ALL", "AUCTIONEERS"]:
                cursor.execute("SELECT * FROM auctioneers ORDER BY created_at DESC LIMIT ?", (limit,))
                results["auctioneers"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "ASSETS"]:
                cursor.execute("SELECT * FROM auction_assets ORDER BY created_at DESC LIMIT ?", (limit,))
                results["auction_assets"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "BIDDERS"]:
                cursor.execute("SELECT * FROM bidders ORDER BY created_at DESC LIMIT ?", (limit,))
                results["bidders"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "SESSIONS"]:
                cursor.execute("SELECT * FROM auction_sessions ORDER BY created_at DESC LIMIT ?", (limit,))
                results["auction_sessions"] = [dict(row) for row in cursor.fetchall()]

        return results

    def get_auction_telemetry(self) -> Dict[str, Any]:
        """Aggregate national property auction volume, winning value, and price increase metrics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN is_practicing = 1 THEN 1 ELSE 0 END) FROM auctioneers")
            a_row = cursor.fetchone()
            total_auctioneers = a_row[0] or 0
            practicing_auctioneers = a_row[1] or 0

            cursor.execute("SELECT COUNT(*), SUM(starting_price_vnd) FROM auction_assets")
            ast_row = cursor.fetchone()
            total_assets = ast_row[0] or 0
            total_starting_value_vnd = ast_row[1] or 0.0

            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN is_eligible = 1 THEN 1 ELSE 0 END) FROM bidders")
            b_row = cursor.fetchone()
            total_bidders = b_row[0] or 0
            eligible_bidders = b_row[1] or 0

            cursor.execute("""
                SELECT COUNT(*), SUM(winning_price_vnd), SUM(price_increase_vnd),
                       SUM(CASE WHEN is_valid = 1 THEN 1 ELSE 0 END)
                FROM auction_sessions
            """)
            s_row = cursor.fetchone()
            total_sessions = s_row[0] or 0
            total_winning_value_vnd = s_row[1] or 0.0
            total_price_increase_vnd = s_row[2] or 0.0
            successful_sessions = s_row[3] or 0

        success_rate_pct = (successful_sessions / total_sessions * 100.0) if total_sessions > 0 else 0.0

        return {
            "total_auctioneers": total_auctioneers,
            "practicing_auctioneers": practicing_auctioneers,
            "total_assets": total_assets,
            "total_starting_value_vnd": total_starting_value_vnd,
            "total_bidders": total_bidders,
            "eligible_bidders": eligible_bidders,
            "total_sessions": total_sessions,
            "successful_sessions": successful_sessions,
            "success_rate_pct": round(success_rate_pct, 2),
            "total_winning_value_vnd": total_winning_value_vnd,
            "total_price_increase_vnd": total_price_increase_vnd,
            "database_path": self.db_path,
        }
