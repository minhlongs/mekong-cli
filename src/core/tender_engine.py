# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Public Procurement, National E-GP Electronic Tender & Bid Evaluation Engine.

Implements Vietnamese statutory procurement, bidding dossiers & E-GP evaluation:
- Luật Đấu thầu 2023 (Luật số 22/2023/QH15) có hiệu lực từ 01/01/2024:
  * Điều 20: Đấu thầu rộng rãi (Open Bidding) — phương thức mặc định.
  * Điều 23: Chỉ định thầu (Direct Contracting) — các gói dịch vụ tư vấn ≤ 500 triệu VND;
    hàng hóa, xây lắp, phi tư vấn ≤ 1 tỷ VND.
  * Điều 24: Chào hàng cạnh tranh (Competitive Quotation) — gói hàng hóa, dịch vụ thông dụng ≤ 5 tỷ VND.
  * Điều 14: Biện pháp bảo đảm dự thầu (Bid Security / Bid Bond: 1% - 3% giá gói thầu).
  * Điều 16: Các hành vi bị nghiêm cấm trong hoạt động đấu thầu (thông thầu, chuyển nhượng thầu trái phép).
- Nghị định 24/2024/NĐ-CP: Quy định chi tiết một số điều và biện pháp thi hành Luật Đấu thầu:
  * Quy trình 4 bước đánh giá E-HSDT: Tính hợp lệ -> Năng lực & kinh nghiệm -> Kỹ thuật -> Tài chính.
  * Tiêu chí doanh thu bình quân 3 năm tối thiểu 1.5x giá gói thầu; hợp đồng tương tự ≥ 70% giá gói thầu.
- Thông tư 06/2024/TT-BKHĐT: Mẫu E-HSMT trên Hệ thống mạng đấu thầu quốc gia (National E-GP).
- Lưu trữ SQLite WAL tại ``.mekong/tenders.db``.

Pure Python standard-library-only implementation adhering strictly to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import datetime
import json
import os
import pathlib
import sqlite3
import typing
import uuid

# ---------------------------------------------------------------------------
# Procurement Framework & Threshold Constants (Luật Đấu thầu 2023)
# ---------------------------------------------------------------------------

DIRECT_CONTRACTING_CAPS_VND: dict[str, float] = {
    "CONSULTING": 500_000_000.0,       # Dịch vụ tư vấn <= 500 triệu đồng
    "GOODS": 1_000_000_000.0,           # Hàng hóa <= 1 tỷ đồng
    "WORKS": 1_000_000_000.0,           # Xây lắp <= 1 tỷ đồng
    "NON_CONSULTING": 1_000_000_000.0,  # Dịch vụ phi tư vấn <= 1 tỷ đồng
}

COMPETITIVE_QUOTATION_CAP_VND: float = 5_000_000_000.0  # Chào hàng cạnh tranh <= 5 tỷ đồng


class TenderEngine:
    """Autonomous Public Procurement, National E-GP Electronic Tender & Bid Evaluation Engine."""

    def __init__(self, db_path: typing.Optional[typing.Union[str, pathlib.Path]] = None) -> None:
        if db_path is not None:
            self.db_path = pathlib.Path(db_path)
        else:
            base_dir = pathlib.Path(os.environ.get("MEKONG_ROOT", "."))
            mekong_dir = base_dir / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "tenders.db"
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tenders (
                    tender_id TEXT PRIMARY KEY,
                    package_number TEXT NOT NULL UNIQUE,
                    package_name TEXT NOT NULL,
                    procuring_entity TEXT NOT NULL,
                    package_type TEXT NOT NULL,
                    budget_vnd REAL NOT NULL,
                    procurement_method TEXT NOT NULL,
                    bid_security_vnd REAL NOT NULL,
                    submission_deadline TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS bids (
                    bid_id TEXT PRIMARY KEY,
                    tender_id TEXT NOT NULL,
                    bidder_name TEXT NOT NULL,
                    bidder_tax_id TEXT NOT NULL,
                    bid_price_vnd REAL NOT NULL,
                    revenue_3yr_avg_vnd REAL NOT NULL,
                    similar_contract_val_vnd REAL NOT NULL,
                    tech_score REAL NOT NULL,
                    has_valid_security INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (tender_id) REFERENCES tenders(tender_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS bid_evaluations (
                    eval_id TEXT PRIMARY KEY,
                    tender_id TEXT NOT NULL,
                    bid_id TEXT NOT NULL,
                    is_eligible INTEGER NOT NULL,
                    is_capable INTEGER NOT NULL,
                    is_tech_passed INTEGER NOT NULL,
                    financial_rank INTEGER NOT NULL,
                    savings_rate_pct REAL NOT NULL,
                    evaluation_summary TEXT NOT NULL,
                    evaluated_at TEXT NOT NULL,
                    FOREIGN KEY (tender_id) REFERENCES tenders(tender_id) ON DELETE CASCADE,
                    FOREIGN KEY (bid_id) REFERENCES bids(bid_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_tenders_status ON tenders(status);
                CREATE INDEX IF NOT EXISTS idx_bids_tender ON bids(tender_id);
                CREATE INDEX IF NOT EXISTS idx_evals_tender ON bid_evaluations(tender_id);
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Procurement Method Advisory (Điều 20, 23, 24 Luật Đấu thầu 2023)
    # -----------------------------------------------------------------------

    def evaluate_procurement_method(
        self,
        package_type: str,
        budget_vnd: float,
        is_urgent: bool = False,
        is_proprietary_tech: bool = False,
    ) -> dict[str, typing.Any]:
        """Determine legal procurement method and legal thresholds under Bidding Law 2023."""
        clean_type = package_type.upper().strip()
        if clean_type not in DIRECT_CONTRACTING_CAPS_VND:
            clean_type = "GOODS"

        direct_cap = DIRECT_CONTRACTING_CAPS_VND[clean_type]

        if is_urgent:
            method = "DIRECT_CONTRACTING"
            reason = "Chỉ định thầu rút gọn do tính chất cấp bách / phục vụ phòng chống thiên tai, dịch bệnh (Điều 23.1.a)."
            article = "Điều 23.1.a Luật Đấu thầu 2023"
        elif is_proprietary_tech:
            method = "DIRECT_CONTRACTING"
            reason = "Chỉ định thầu do yêu cầu tính tương thích công nghệ độc quyền hoặc sở hữu trí tuệ duy nhất (Điều 23.1.c)."
            article = "Điều 23.1.c Luật Đấu thầu 2023"
        elif budget_vnd <= direct_cap:
            method = "DIRECT_CONTRACTING"
            reason = f"Giá gói thầu ({budget_vnd:,.0f} VND) nằm trong hạn mức chỉ định thầu quy định (<= {direct_cap:,.0f} VND)."
            article = "Điều 23.1.m Luật Đấu thầu 2023"
        elif budget_vnd <= COMPETITIVE_QUOTATION_CAP_VND and clean_type in ("GOODS", "NON_CONSULTING", "WORKS"):
            method = "COMPETITIVE_QUOTATION"
            reason = f"Giá gói thầu ({budget_vnd:,.0f} VND) đủ điều kiện Chào hàng cạnh tranh (<= 5 tỷ VND) theo quy định."
            article = "Điều 24 Luật Đấu thầu 2023"
        else:
            method = "OPEN_BIDDING"
            reason = "Áp dụng hình thức Đấu thầu rộng rãi công khai qua Mạng đấu thầu quốc gia (E-GP)."
            article = "Điều 20 Luật Đấu thầu 2023 (Nguyên tắc cạnh tranh mặc định)"

        # Calculate standard bid security (Bảo đảm dự thầu)
        bid_sec_pct = 1.5 if budget_vnd <= 10_000_000_000.0 else 2.0
        bid_security_vnd = round(budget_vnd * (bid_sec_pct / 100.0))

        return {
            "ok": True,
            "package_type": clean_type,
            "budget_vnd": budget_vnd,
            "recommended_method": method,
            "statutory_justification": reason,
            "governing_article": article,
            "direct_contracting_cap_vnd": direct_cap,
            "bid_security_required": method in ("OPEN_BIDDING", "COMPETITIVE_QUOTATION"),
            "bid_security_rate_pct": bid_sec_pct if method in ("OPEN_BIDDING", "COMPETITIVE_QUOTATION") else 0.0,
            "bid_security_estimated_vnd": bid_security_vnd if method in ("OPEN_BIDDING", "COMPETITIVE_QUOTATION") else 0.0,
        }

    # -----------------------------------------------------------------------
    # E-HSMT Tender Package Creation
    # -----------------------------------------------------------------------

    def create_tender(
        self,
        package_name: str,
        procuring_entity: str,
        budget_vnd: float,
        package_type: str = "GOODS",
        procurement_method: typing.Optional[str] = None,
        submission_days: int = 15,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Synthesize and publish an electronic tender dossier (E-HSMT) on National E-GP."""
        tender_id = f"TD-{uuid.uuid4().hex[:8].upper()}"
        year = datetime.datetime.now().year
        package_number = f"EGP-{year}-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)
        deadline = now + datetime.timedelta(days=submission_days)

        clean_type = package_type.upper().strip()
        if not procurement_method:
            adv = self.evaluate_procurement_method(package_type=clean_type, budget_vnd=budget_vnd)
            method = adv["recommended_method"]
            bid_sec_vnd = adv["bid_security_estimated_vnd"]
        else:
            method = procurement_method.upper().strip()
            bid_sec_vnd = round(budget_vnd * 0.015) if method != "DIRECT_CONTRACTING" else 0.0

        record = {
            "ok": True,
            "tender_id": tender_id,
            "package_number": package_number,
            "package_name": package_name,
            "procuring_entity": procuring_entity,
            "package_type": clean_type,
            "budget_vnd": budget_vnd,
            "procurement_method": method,
            "bid_security_vnd": bid_sec_vnd,
            "submission_deadline": deadline.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "status": "PUBLISHED",
            "egp_system": "Hệ thống Mạng Đấu thầu Quốc gia (muasamcong.mpi.gov.vn)",
            "statutory_criteria": {
                "min_3yr_avg_revenue_vnd": round(budget_vnd * 1.5),
                "min_similar_contract_val_vnd": round(budget_vnd * 0.7),
                "min_tech_score": 70.0,
            },
            "created_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO tenders (
                        tender_id, package_number, package_name, procuring_entity,
                        package_type, budget_vnd, procurement_method, bid_security_vnd,
                        submission_deadline, status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tender_id,
                        package_number,
                        package_name,
                        procuring_entity,
                        clean_type,
                        budget_vnd,
                        method,
                        bid_sec_vnd,
                        deadline.strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "PUBLISHED",
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return record

    # -----------------------------------------------------------------------
    # Bid Submission & 4-Step E-HSDT Evaluation (Nghị định 24/2024/NĐ-CP)
    # -----------------------------------------------------------------------

    def evaluate_bid(
        self,
        tender_id: str,
        bidder_name: str,
        bid_price_vnd: float,
        bidder_tax_id: str = "0101234567",
        revenue_3yr_avg_vnd: float = 0.0,
        similar_contract_val_vnd: float = 0.0,
        tech_score: float = 85.0,
        has_valid_security: bool = True,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Execute statutory 4-step E-HSDT bid evaluation under Decree 24/2024/ND-CP."""
        with self._get_connection() as conn:
            tender_row = conn.execute("SELECT * FROM tenders WHERE tender_id = ? OR package_number = ?", (tender_id, tender_id)).fetchone()
            if not tender_row:
                return {
                    "ok": False,
                    "error": f"Không tìm thấy gói thầu với mã định danh: '{tender_id}'",
                }
            t_dict = dict(tender_row)

        budget_vnd = t_dict["budget_vnd"]
        req_revenue = budget_vnd * 1.5
        req_similar = budget_vnd * 0.7

        # Step 1: Eligibility check (Tính hợp lệ)
        # Bid price must not exceed budget by default without adjustments; valid security required if method is Open/Competitive
        needs_sec = t_dict["procurement_method"] in ("OPEN_BIDDING", "COMPETITIVE_QUOTATION")
        is_eligible = (not needs_sec or has_valid_security) and bid_price_vnd > 0

        # Step 2: Capacity & Experience evaluation (Năng lực & kinh nghiệm)
        # Revenue >= 1.5x budget, Similar contract >= 0.7x budget
        is_capable = (revenue_3yr_avg_vnd >= req_revenue) and (similar_contract_val_vnd >= req_similar)

        # Step 3: Technical evaluation (Kỹ thuật)
        # Min technical score is 70.0
        is_tech_passed = tech_score >= 70.0

        # Step 4: Financial evaluation & Ranking
        # Savings rate = ((Budget - BidPrice) / Budget) * 100%
        if budget_vnd > 0:
            savings_pct = round(((budget_vnd - bid_price_vnd) / budget_vnd) * 100.0, 2)
        else:
            savings_pct = 0.0

        overall_qualified = is_eligible and is_capable and is_tech_passed and (bid_price_vnd <= budget_vnd)

        bid_id = f"BID-{uuid.uuid4().hex[:8].upper()}"
        eval_id = f"EV-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        eval_summary = []
        if not is_eligible:
            eval_summary.append("Không đạt tính hợp lệ (Thiếu bảo lãnh dự thầu hoặc hồ sơ vi phạm điều cấm).")
        if not is_capable:
            eval_summary.append(f"Không đạt năng lực (Yêu cầu doanh thu >= {req_revenue:,.0f} VND hoặc HĐ tương tự >= {req_similar:,.0f} VND).")
        if not is_tech_passed:
            eval_summary.append(f"Không đạt yêu cầu kỹ thuật (Điểm kỹ thuật {tech_score}/100 < 70 điểm sàn).")
        if bid_price_vnd > budget_vnd:
            eval_summary.append(f"Giá dự thầu ({bid_price_vnd:,.0f} VND) vượt giá gói thầu ({budget_vnd:,.0f} VND).")
        if overall_qualified:
            eval_summary.append(f"Đạt cả 4 bước đánh giá. Tỷ lệ tiết kiệm cho ngân sách nhà nước: {savings_pct}%.")

        result = {
            "ok": True,
            "eval_id": eval_id,
            "bid_id": bid_id,
            "tender_id": t_dict["tender_id"],
            "package_name": t_dict["package_name"],
            "bidder_name": bidder_name,
            "bidder_tax_id": bidder_tax_id,
            "bid_price_vnd": bid_price_vnd,
            "budget_vnd": budget_vnd,
            "savings_rate_pct": savings_pct,
            "step_1_eligibility": is_eligible,
            "step_2_capacity": is_capable,
            "step_3_technical": is_tech_passed,
            "step_4_financial": bid_price_vnd <= budget_vnd,
            "overall_qualified": overall_qualified,
            "recommendation": "ĐỀ NGHỊ TRÚNG THẦU" if overall_qualified else "LOẠI HỒ SƠ DỰ THẦU",
            "evaluation_notes": "; ".join(eval_summary),
            "evaluated_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO bids (
                        bid_id, tender_id, bidder_name, bidder_tax_id, bid_price_vnd,
                        revenue_3yr_avg_vnd, similar_contract_val_vnd, tech_score,
                        has_valid_security, status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        bid_id,
                        t_dict["tender_id"],
                        bidder_name,
                        bidder_tax_id,
                        bid_price_vnd,
                        revenue_3yr_avg_vnd,
                        similar_contract_val_vnd,
                        tech_score,
                        1 if has_valid_security else 0,
                        "QUALIFIED" if overall_qualified else "DISQUALIFIED",
                        now.isoformat(),
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO bid_evaluations (
                        eval_id, tender_id, bid_id, is_eligible, is_capable,
                        is_tech_passed, financial_rank, savings_rate_pct,
                        evaluation_summary, evaluated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        eval_id,
                        t_dict["tender_id"],
                        bid_id,
                        1 if is_eligible else 0,
                        1 if is_capable else 0,
                        1 if is_tech_passed else 0,
                        1 if overall_qualified else 99,
                        savings_pct,
                        result["evaluation_notes"],
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Bid Collusion & Integrity Scanner (Điều 16 Luật Đấu thầu 2023)
    # -----------------------------------------------------------------------

    def detect_bid_collusion(self, tender_id: str) -> dict[str, typing.Any]:
        """Scan submitted bids for anti-competitive collusion or abnormal price patterns under Article 16."""
        with self._get_connection() as conn:
            tender_row = conn.execute("SELECT * FROM tenders WHERE tender_id = ? OR package_number = ?", (tender_id, tender_id)).fetchone()
            if not tender_row:
                return {
                    "ok": False,
                    "error": f"Không tìm thấy gói thầu với mã: '{tender_id}'",
                }
            t_dict = dict(tender_row)

            bids = conn.execute("SELECT * FROM bids WHERE tender_id = ?", (t_dict["tender_id"],)).fetchall()
            bids_list = [dict(b) for b in bids]

        red_flags: list[dict[str, typing.Any]] = []
        collusion_risk = "LOW"
        risk_score = 0

        if len(bids_list) >= 2:
            prices = [b["bid_price_vnd"] for b in bids_list]
            # Check price clustering: prices differing by less than 0.5%
            prices_sorted = sorted(prices)
            for i in range(len(prices_sorted) - 1):
                diff_pct = abs(prices_sorted[i + 1] - prices_sorted[i]) / prices_sorted[i] * 100.0
                if diff_pct < 0.3:
                    risk_score += 45
                    red_flags.append({
                        "type": "PRICE_CLUSTERING",
                        "severity": "CRITICAL",
                        "description": f"Chênh lệch giá giữa các nhà thầu ({diff_pct:.2f}%) sát nhau bất thường, có dấu hiệu thông thầu phân chia thị phần.",
                        "statutory_basis": "Điều 16.3 Luật Đấu thầu 2023 (Các hành vi thông thầu bị cấm).",
                    })

            # Check duplicate or similar tax IDs / entities
            tax_ids = [b["bidder_tax_id"] for b in bids_list]
            if len(tax_ids) != len(set(tax_ids)):
                risk_score += 50
                red_flags.append({
                    "type": "AFFILIATE_COLLUSION",
                    "severity": "CRITICAL",
                    "description": "Phát hiện nhiều hồ sơ dự thầu có cùng mã số thuế hoặc thuộc cùng tập đoàn mẹ con dự cùng 01 gói thầu.",
                    "statutory_basis": "Điều 6.2 Luật Đấu thầu 2023 (Quy định về bảo đảm cạnh tranh trong đấu thầu).",
                })

        if risk_score >= 50:
            collusion_risk = "HIGH"
        elif risk_score >= 25:
            collusion_risk = "MEDIUM"

        return {
            "ok": True,
            "tender_id": t_dict["tender_id"],
            "package_name": t_dict["package_name"],
            "total_bids_scanned": len(bids_list),
            "collusion_risk": collusion_risk,
            "risk_score": risk_score,
            "red_flags_count": len(red_flags),
            "red_flags": red_flags,
            "legal_conclusion": (
                "Phát hiện dấu hiệu vi phạm điều cấm về thông thầu theo Điều 16 Luật Đấu thầu 2023. Kiến nghị kiểm tra tính độc lập."
                if collusion_risk == "HIGH"
                else "Các hồ sơ dự thầu đáp ứng tính cạnh tranh và độc lập theo quy định."
            ),
        }

    # -----------------------------------------------------------------------
    # Portfolio & Status
    # -----------------------------------------------------------------------

    def list_tenders(self, status: typing.Optional[str] = None, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List registered tender packages and active biddings."""
        with self._get_connection() as conn:
            if status and status.upper() != "ALL":
                rows = conn.execute(
                    "SELECT * FROM tenders WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status.upper(), limit),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM tenders ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated public procurement metrics, total budget, and savings."""
        with self._get_connection() as conn:
            t_row = conn.execute("SELECT COUNT(*) as c, COALESCE(SUM(budget_vnd), 0) as sm FROM tenders").fetchone()
            b_row = conn.execute("SELECT COUNT(*) as c FROM bids").fetchone()
            q_row = conn.execute("SELECT COUNT(*) as c FROM bids WHERE status = 'QUALIFIED'").fetchone()
            avg_sav = conn.execute("SELECT COALESCE(AVG(savings_rate_pct), 0) as a FROM bid_evaluations").fetchone()

        return {
            "ok": True,
            "status": "operational",
            "engine": "TenderEngine",
            "regulatory_framework": "Luật Đấu thầu 2023 (Luật số 22/2023/QH15) & Nghị định 24/2024/NĐ-CP",
            "national_egp_system": "Hệ thống Mạng Đấu thầu Quốc gia (muasamcong.mpi.gov.vn)",
            "metrics": {
                "total_tenders": t_row["c"] if t_row else 0,
                "total_budget_vnd": t_row["sm"] if t_row else 0.0,
                "total_bids_submitted": b_row["c"] if b_row else 0,
                "qualified_bids": q_row["c"] if q_row else 0,
                "average_savings_rate_pct": round(avg_sav["a"], 2) if avg_sav else 0.0,
            },
            "database": str(self.db_path),
        }
