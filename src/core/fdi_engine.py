# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Foreign Direct Investment (FDI) & SBV Capital Compliance Engine.

Implements statutory FDI market access checks, DICA capital accounts, and SBV compliance:
- Luật Đầu tư 2020 (Law No. 61/2020/QH14) & Nghị định 31/2021/NĐ-CP.
- WTO Commitments on Services, CPTPP, and EVFTA Schedule of Specific Commitments.
- Thông tư 06/2019/TT-NHNN: Quản lý ngoại hối đối với hoạt động đầu tư trực tiếp nước ngoài.
  Mọi dòng vốn góp, chuyển nhượng, giải ngân khoản vay và chuyển lợi nhuận bắt buộc qua DICA.
- Thông tư 186/2010/TT-BTC: Điều kiện và thủ tục chuyển lợi nhuận ra nước ngoài hợp pháp.
- Thông tư 12/2022/TT-NHNN: Điều kiện và thủ tục đăng ký khoản vay nước ngoài trung - dài hạn (> 1 năm).
- Lưu trữ SQLite WAL tại ``.mekong/fdi.db``.

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
# Market Access Dictionary under WTO & FTA Commitments
# ---------------------------------------------------------------------------

SECTOR_MARKET_ACCESS: dict[str, dict[str, typing.Any]] = {
    "IT_SOFTWARE": {
        "code": "IT_SOFTWARE",
        "vsic": "6201",
        "cpc": "CPC 842",
        "name": "Dịch vụ phần mềm & Trí tuệ nhân tạo (AI)",
        "max_fdi_ratio": 100.0,
        "access_status": "PERMITTED",
        "treaties": ["WTO", "CPTPP", "EVFTA"],
        "conditions": "Không hạn chế tỷ lệ sở hữu nhà đầu tư nước ngoài (100% FDI). Không yêu cầu liên doanh.",
    },
    "6201": {
        "code": "6201",
        "vsic": "6201",
        "cpc": "CPC 842",
        "name": "Lập trình máy vi tính & Phát triển AI",
        "max_fdi_ratio": 100.0,
        "access_status": "PERMITTED",
        "treaties": ["WTO", "CPTPP", "EVFTA"],
        "conditions": "Không hạn chế tỷ lệ sở hữu nhà đầu tư nước ngoài (100% FDI). Không yêu cầu liên doanh.",
    },
    "6202": {
        "code": "6202",
        "vsic": "6202",
        "cpc": "CPC 841",
        "name": "Tư vấn máy vi tính và quản trị hệ thống máy vi tính",
        "max_fdi_ratio": 100.0,
        "access_status": "PERMITTED",
        "treaties": ["WTO", "CPTPP", "EVFTA"],
        "conditions": "Được phép 100% vốn nước ngoài.",
    },
    "DATA_PROCESSING": {
        "code": "DATA_PROCESSING",
        "vsic": "6311",
        "cpc": "CPC 843",
        "name": "Xử lý dữ liệu & Lưu trữ đám mây (Cloud Hosting)",
        "max_fdi_ratio": 100.0,
        "access_status": "PERMITTED",
        "treaties": ["WTO", "CPTPP", "EVFTA"],
        "conditions": "Được phép thành lập doanh nghiệp 100% vốn nước ngoài. Tuân thủ Luật An ninh mạng 2018 về lưu trữ dữ liệu tại Việt Nam khi cung cấp dịch vụ công cộng.",
    },
    "6311": {
        "code": "6311",
        "vsic": "6311",
        "cpc": "CPC 843",
        "name": "Xử lý dữ liệu, cho thuê lưu trữ và các hoạt động liên quan",
        "max_fdi_ratio": 100.0,
        "access_status": "PERMITTED",
        "treaties": ["WTO", "CPTPP", "EVFTA"],
        "conditions": "Được phép 100% vốn nước ngoài. Tuân thủ Luật An ninh mạng 2018.",
    },
    "MANAGEMENT_CONSULTING": {
        "code": "MANAGEMENT_CONSULTING",
        "vsic": "7020",
        "cpc": "CPC 865",
        "name": "Tư vấn quản trị & Chuyển đổi số",
        "max_fdi_ratio": 100.0,
        "access_status": "PERMITTED",
        "treaties": ["WTO", "CPTPP", "EVFTA"],
        "conditions": "Được phép 100% vốn nước ngoài. Không bao gồm tư vấn pháp lý và kiểm toán tài chính.",
    },
    "7020": {
        "code": "7020",
        "vsic": "7020",
        "cpc": "CPC 865",
        "name": "Hoạt động tư vấn quản lý",
        "max_fdi_ratio": 100.0,
        "access_status": "PERMITTED",
        "treaties": ["WTO", "CPTPP", "EVFTA"],
        "conditions": "Được phép 100% vốn nước ngoài.",
    },
    "TELECOM_VALUE_ADDED": {
        "code": "TELECOM_VALUE_ADDED",
        "vsic": "6110",
        "cpc": "CPC 7523",
        "name": "Dịch vụ viễn thông giá trị gia tăng không có hạ tầng mạng",
        "max_fdi_ratio": 65.0,
        "access_status": "CONDITIONAL",
        "treaties": ["WTO", "CPTPP"],
        "conditions": "Tối đa 65% vốn nước ngoài đối với dịch vụ không có hạ tầng mạng (Non-facilities based). Cần giấy phép thiết lập mạng viễn thông từ Bộ TTTT.",
    },
    "LOGISTICS_FREIGHT": {
        "code": "LOGISTICS_FREIGHT",
        "vsic": "5229",
        "cpc": "CPC 748",
        "name": "Dịch vụ đại lý vận tải & Logistics",
        "max_fdi_ratio": 100.0,
        "access_status": "PERMITTED",
        "treaties": ["EVFTA", "CPTPP"],
        "conditions": "100% FDI theo lộ trình EVFTA và Nghị định 163/2017/NĐ-CP.",
    },
    "ADVERTISING": {
        "code": "ADVERTISING",
        "vsic": "7310",
        "cpc": "CPC 871",
        "name": "Dịch vụ quảng cáo & Tiếp thị số",
        "max_fdi_ratio": 100.0,
        "access_status": "PERMITTED",
        "treaties": ["WTO", "EVFTA"],
        "conditions": "Được phép 100% vốn FDI theo cam kết WTO và EVFTA.",
    },
    "6810": {
        "code": "6810",
        "vsic": "6810",
        "cpc": "CPC 821",
        "name": "Kinh doanh bất động sản, quyền sử dụng đất",
        "max_fdi_ratio": 50.0,
        "access_status": "CONDITIONAL",
        "treaties": ["WTO", "CPTPP"],
        "conditions": "Hạn chế tỷ lệ sở hữu nước ngoài theo Luật Kinh doanh Bất động sản 2023. Bắt buộc liên doanh.",
    },
    "8411": {
        "code": "8411",
        "vsic": "8411",
        "cpc": "CPC 911",
        "name": "Hoạt động quản lý nhà nước nói chung và kinh tế xã hội",
        "max_fdi_ratio": 0.0,
        "access_status": "PROHIBITED",
        "treaties": [],
        "conditions": "Lĩnh vực cấm tiếp cận thị trường đối với nhà đầu tư nước ngoài theo Điều 6 Luật Đầu tư 2020.",
    },
    "4651": {
        "code": "4651",
        "vsic": "4651",
        "cpc": "CPC 622",
        "name": "Bán buôn máy vi tính, thiết bị ngoại vi và phần mềm",
        "max_fdi_ratio": 100.0,
        "access_status": "PERMITTED",
        "treaties": ["WTO", "EVFTA"],
        "conditions": "Được phép 100% vốn nước ngoài.",
    },
}

MARKET_ACCESS_REGIME = SECTOR_MARKET_ACCESS
TREATIES: list[str] = ["WTO", "CPTPP", "EVFTA"]
EXCHANGE_RATE_USD_VND: float = 25_450.0  # Tỷ giá tham chiếu Ngân hàng Nhà nước


class FdiEngine:
    """Autonomous Foreign Direct Investment & SBV Capital Compliance Engine."""

    def __init__(self, db_path: typing.Optional[typing.Union[str, pathlib.Path]] = None) -> None:
        if db_path is not None:
            self.db_path = pathlib.Path(db_path)
        else:
            base_dir = pathlib.Path(os.environ.get("MEKONG_ROOT", "."))
            mekong_dir = base_dir / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "fdi.db"
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
                CREATE TABLE IF NOT EXISTS fdi_projects (
                    project_id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    investor_country TEXT NOT NULL,
                    sector_code TEXT NOT NULL,
                    capital_usd REAL NOT NULL,
                    capital_vnd REAL NOT NULL,
                    location TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS foreign_loans (
                    loan_id TEXT PRIMARY KEY,
                    borrower_name TEXT NOT NULL,
                    lender_name TEXT NOT NULL,
                    lender_country TEXT NOT NULL,
                    amount_usd REAL NOT NULL,
                    tenor_months INTEGER NOT NULL,
                    interest_rate REAL NOT NULL,
                    sbv_registration_required INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS profit_remittances (
                    remittance_id TEXT PRIMARY KEY,
                    company_name TEXT NOT NULL,
                    amount_usd REAL NOT NULL,
                    amount_vnd REAL NOT NULL,
                    tax_year INTEGER NOT NULL,
                    is_eligible INTEGER NOT NULL,
                    dica_bank TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_fdi_sector ON fdi_projects(sector_code);
                CREATE INDEX IF NOT EXISTS idx_loan_borrower ON foreign_loans(borrower_name);
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Market Access & Foreign Ownership Cap Evaluation
    # -----------------------------------------------------------------------

    def check_market_access(
        self,
        sector_code: str,
        foreign_ratio: float = 100.0,
    ) -> dict[str, typing.Any]:
        """Verify WTO & FTA market access conditions and foreign ownership limits."""
        res = self.evaluate_market_access(sector_code=sector_code, ownership_pct=foreign_ratio)
        if not res.get("ok"):
            return {
                "ok": False,
                "sector_code": sector_code,
                "error": res.get("error", f"Mã ngành không tồn tại trong biểu cam kết FDI: {sector_code}"),
                "available_sectors": list(SECTOR_MARKET_ACCESS.keys()),
            }

        verdict = (
            "CHẤP THUẬN (Tuân thủ trần sở hữu nước ngoài)"
            if res["is_compliant"]
            else f"TỪ CHỐI (Tỷ lệ {foreign_ratio}% vượt quá trần quy định {res['foreign_ownership_cap_pct']}%)"
        )

        return {
            "ok": True,
            "sector_code": res["sector_code"],
            "sector_name": res["sector_name"],
            "cpc_code": res.get("cpc_code", "CPC 842"),
            "requested_ratio": foreign_ratio,
            "max_allowed_ratio": res["foreign_ownership_cap_pct"],
            "is_compliant": res["is_compliant"],
            "verdict": verdict,
            "access_status": res["regime"],
            "treaties": res["applicable_treaties"],
            "conditions": res["conditions"],
            "regulatory_reference": "Nghị định 31/2021/NĐ-CP & Biểu cam kết WTO Việt Nam",
        }

    def evaluate_market_access(
        self,
        sector_code: str,
        investor_nationality: str = "US",
        ownership_pct: float = 100.0,
    ) -> dict[str, typing.Any]:
        """Evaluate market access, ownership cap, treaties, and conditional investment regulations."""
        sector_key = sector_code.strip().upper()
        sector_info = SECTOR_MARKET_ACCESS.get(sector_key)
        if not sector_info:
            sector_info = SECTOR_MARKET_ACCESS.get(sector_code.strip())

        if not sector_info:
            return {
                "ok": False,
                "sector_code": sector_code,
                "error": f"Mã phân ngành không tồn tại: {sector_code}",
                "available_sectors": list(SECTOR_MARKET_ACCESS.keys()),
            }

        max_ratio = float(sector_info["max_fdi_ratio"])
        regime = sector_info["access_status"]
        is_compliant = (ownership_pct <= max_ratio) and (regime != "PROHIBITED")

        warnings: list[str] = []
        if regime == "PROHIBITED":
            warnings.append(f"Sector {sector_code} is prohibited for foreign investment under Law on Investment 2020.")
        elif ownership_pct > max_ratio:
            warnings.append(f"Requested ownership {ownership_pct}% exceeds statutory cap {max_ratio}%.")

        return {
            "ok": True,
            "sector_code": sector_info["code"],
            "sector_name": sector_info["name"],
            "cpc_code": sector_info.get("cpc", "N/A"),
            "regime": regime,
            "foreign_ownership_cap_pct": max_ratio,
            "requested_ownership_pct": ownership_pct,
            "investor_nationality": investor_nationality,
            "is_compliant": is_compliant,
            "applicable_treaties": sector_info.get("treaties", []),
            "conditions": sector_info.get("conditions", ""),
            "warnings": warnings,
            "regulatory_reference": "Law on Investment 2020 & Decree 31/2021/ND-CP",
        }

    # -----------------------------------------------------------------------
    # Offshore Profit Remittance (Thông tư 186/2010/TT-BTC & TT 06/2019/TT-NHNN)
    # -----------------------------------------------------------------------

    def verify_profit_remittance(
        self,
        amount_usd: float = 0.0,
        tax_year: int = 2025,
        is_audited: bool = True,
        has_tax_clearance: bool = True,
        accumulated_loss_usd: float = 0.0,
        exchange_rate: float = EXCHANGE_RATE_USD_VND,
        company_name: str = "Doanh Nghiệp FDI",
        save: bool = True,
        *,
        fiscal_year: typing.Optional[int] = None,
        audited_profit_vnd: typing.Optional[float] = None,
        tax_cleared: typing.Optional[bool] = None,
        retained_reserve_pct: float = 5.0,
        dica_verified: bool = True,
        losses_carried_forward_vnd: float = 0.0,
    ) -> dict[str, typing.Any]:
        """Verify legal offshore profit remittance eligibility under Circular 186/2010/TT-BTC."""
        now = datetime.datetime.now(datetime.timezone.utc)
        remittance_id = f"REMIT-{uuid.uuid4().hex[:8].upper()}"

        actual_year = fiscal_year if fiscal_year is not None else tax_year
        actual_tax_cleared = tax_cleared if tax_cleared is not None else has_tax_clearance

        if audited_profit_vnd is not None and audited_profit_vnd > 0:
            actual_vnd = float(audited_profit_vnd)
            actual_usd = actual_vnd / exchange_rate
        else:
            actual_usd = float(amount_usd)
            actual_vnd = round(actual_usd * exchange_rate)

        actual_loss_vnd = float(losses_carried_forward_vnd) if losses_carried_forward_vnd > 0 else (accumulated_loss_usd * exchange_rate)

        deficiencies: list[str] = []
        if not is_audited:
            deficiencies.append("Chưa nộp Báo cáo tài chính năm đã được kiểm toán độc lập.")
        if not actual_tax_cleared:
            deficiencies.append("Chưa hoàn thành đầy đủ nghĩa vụ thuế (TNDN) và quyết toán thuế năm với cơ quan thuế quản lý trực tiếp.")
        if actual_loss_vnd > 0.0:
            deficiencies.append(f"Doanh nghiệp còn số lỗ lũy kế {actual_loss_vnd:,.0f} VND sau khi chuyển lỗ theo quy định pháp luật.")
        if not dica_verified:
            deficiencies.append("Chưa mở hoặc chưa xác thực Tài khoản vốn đầu tư trực tiếp (DICA) theo Thông tư 06/2019/TT-NHNN.")

        is_eligible = len(deficiencies) == 0

        # Statutory reserve deduction (e.g. 5% under Law on Enterprises 2020)
        legal_reserve_vnd = round(actual_vnd * (retained_reserve_pct / 100.0))
        net_distributable_vnd = max(0.0, actual_vnd - legal_reserve_vnd - actual_loss_vnd)
        eligible_remittance_vnd = net_distributable_vnd if is_eligible else 0.0
        eligible_remittance_usd = round(eligible_remittance_vnd / exchange_rate, 2)

        result = {
            "ok": True,
            "remittance_id": remittance_id,
            "company_name": company_name,
            "amount_usd": actual_usd,
            "amount_vnd": actual_vnd,
            "exchange_rate": exchange_rate,
            "tax_year": actual_year,
            "fiscal_year": actual_year,
            "audited_profit_vnd": actual_vnd,
            "legal_reserve_vnd": legal_reserve_vnd,
            "net_distributable_profit_vnd": net_distributable_vnd,
            "eligible_remittance_vnd": eligible_remittance_vnd,
            "eligible_remittance_usd": eligible_remittance_usd,
            "is_eligible": is_eligible,
            "deficiencies": deficiencies,
            "rejection_reasons": deficiencies,
            "statutory_rules": [
                "Bắt buộc chuyển tiền qua Tài khoản vốn đầu tư trực tiếp (DICA) theo Thông tư 06/2019/TT-NHNN.",
                "Gửi thông báo chuyển lợi nhuận ra nước ngoài tới Cơ quan thuế quản lý trực tiếp ít nhất 07 ngày làm việc trước khi thực hiện giao dịch.",
            ],
            "status": "APPROVED_FOR_REMITTANCE" if is_eligible else "REJECTED_DEFICIENT",
            "created_at": now.isoformat(),
        }

        if save and is_eligible:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO profit_remittances (
                        remittance_id, company_name, amount_usd, amount_vnd,
                        tax_year, is_eligible, dica_bank, status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        remittance_id,
                        company_name,
                        actual_usd,
                        actual_vnd,
                        actual_year,
                        1 if is_eligible else 0,
                        "MBBank (DICA Account)",
                        result["status"],
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Foreign Loan Evaluation (Thông tư 12/2022/TT-NHNN)
    # -----------------------------------------------------------------------

    def evaluate_foreign_loan(
        self,
        amount_usd: float = 0.0,
        tenor_months: int = 24,
        interest_rate_pct: float = 6.5,
        borrower_name: str = "Doanh Nghiệp FDI",
        lender_name: str = "Tổ chức tín dụng quốc tế",
        lender_country: str = "US",
        purpose: str = "Mở rộng sản xuất kinh doanh",
        save: bool = True,
        *,
        loan_amount: typing.Optional[float] = None,
        currency: str = "USD",
        tenure_months: typing.Optional[int] = None,
        project_capital_gap: float = 0.0,
    ) -> dict[str, typing.Any]:
        """Evaluate State Bank of Vietnam foreign loan registration requirements under TT 12/2022/TT-NHNN."""
        now = datetime.datetime.now(datetime.timezone.utc)
        loan_id = f"LOAN-{uuid.uuid4().hex[:8].upper()}"

        actual_months = tenure_months if tenure_months is not None else tenor_months
        if loan_amount is not None:
            actual_amount = float(loan_amount)
            actual_usd = actual_amount if currency.upper() == "USD" else round(actual_amount / EXCHANGE_RATE_USD_VND, 2)
        else:
            actual_usd = float(amount_usd)

        # Trung & dài hạn: > 12 tháng bắt buộc phải đăng ký với NHNN
        is_medium_long_term = actual_months > 12
        sbv_reg_required = is_medium_long_term

        # Check project capital gap: Loan limit <= (Total Investment - Charter Capital)
        conditions: list[str] = []
        is_compliant = True
        if project_capital_gap > 0.0 and actual_usd > project_capital_gap:
            is_compliant = False
            conditions.append(
                f"Foreign loan amount ({actual_usd:,.2f} {currency}) exceeds permitted project investment gap ({project_capital_gap:,.2f} {currency})."
            )

        # Reference interest cap warning (SOFR + spread)
        interest_status = "NORMAL" if interest_rate_pct <= 8.5 else "HIGH_SPREAD_ALERT"

        result = {
            "ok": True,
            "loan_id": loan_id,
            "borrower_name": borrower_name,
            "lender_name": lender_name,
            "lender_country": lender_country,
            "amount_usd": actual_usd,
            "amount_vnd": round(actual_usd * EXCHANGE_RATE_USD_VND),
            "currency": currency,
            "tenor_months": actual_months,
            "tenure_months": actual_months,
            "loan_category": "MEDIUM_LONG_TERM" if is_medium_long_term else "SHORT_TERM",
            "loan_type": "TRUNG VÀ DÀI HẠN" if is_medium_long_term else "NGẮN HẠN (Dưới 1 năm)",
            "interest_rate_pct": interest_rate_pct,
            "interest_status": interest_status,
            "sbv_registration_required": sbv_reg_required,
            "is_compliant": is_compliant,
            "conditions": conditions,
            "registration_timeline": (
                "Circular 12/2022/TT-NHNN: Bắt buộc đăng ký với NHNN trong vòng 30 ngày kể từ ngày ký thỏa thuận vay."
                if sbv_reg_required
                else "Khoản vay ngắn hạn: Miễn đăng ký trước, báo cáo định kỳ theo quý."
            ),
            "compliance_requirements": [
                "Đăng ký khoản vay với Ngân hàng Nhà nước Việt Nam (Cục Quản lý Ngoại hối) trước khi giải ngân vốn vay."
                if sbv_reg_required
                else "Khoản vay ngắn hạn không bắt buộc đăng ký trước, nhưng phải thực hiện báo cáo định kỳ theo quý.",
                "Giải ngân và trả nợ bắt buộc thực hiện qua Tài khoản vốn vay nước ngoài hoặc tài khoản DICA mở tại ngân hàng được phép.",
                "Báo cáo tình hình thực hiện khoản vay nước ngoài hàng quý trên Cổng thông tin điện tử NHNN.",
            ],
            "regulatory_framework": "Thông tư 12/2022/TT-NHNN & Circular 06/2019/TT-NHNN",
            "created_at": now.isoformat(),
        }

        if save and is_compliant:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO foreign_loans (
                        loan_id, borrower_name, lender_name, lender_country,
                        amount_usd, tenor_months, interest_rate,
                        sbv_registration_required, status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        loan_id,
                        borrower_name,
                        lender_name,
                        lender_country,
                        actual_usd,
                        actual_months,
                        interest_rate_pct,
                        1 if sbv_reg_required else 0,
                        "REGISTERED",
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Investment Registration Certificate (IRC) Dossier
    # -----------------------------------------------------------------------

    def generate_irc_dossier(
        self,
        project_name: str,
        capital_usd: float = 0.0,
        investor_country: str = "US",
        sector_code: str = "IT_SOFTWARE",
        location: str = "Khu Công Nghệ Cao Hòa Lạc, Hà Nội",
        save: bool = True,
        *,
        total_investment_vnd: typing.Optional[float] = None,
        investor_name: typing.Optional[str] = None,
        project_location: typing.Optional[str] = None,
    ) -> dict[str, typing.Any]:
        """Synthesize statutory Investment Project Proposal for IRC under Law on Investment 2020."""
        project_id = f"IRC-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        actual_location = project_location or location
        actual_investor = investor_name or f"Investor ({investor_country})"

        if total_investment_vnd is not None and total_investment_vnd > 0:
            actual_vnd = float(total_investment_vnd)
            actual_usd = round(actual_vnd / EXCHANGE_RATE_USD_VND, 2)
        else:
            actual_usd = float(capital_usd)
            actual_vnd = round(actual_usd * EXCHANGE_RATE_USD_VND)

        sector_key = sector_code.strip().upper()
        sector_info = SECTOR_MARKET_ACCESS.get(sector_key)
        if not sector_info:
            sector_info = SECTOR_MARKET_ACCESS.get(sector_code.strip(), SECTOR_MARKET_ACCESS["IT_SOFTWARE"])

        documents = [
            {
                "type": "APPLICATION_FORM",
                "title": "Văn bản đề nghị thực hiện dự án đầu tư (Mẫu A.I.1 Thông tư 03/2021/TT-BKHĐT)",
                "status": "READY",
            },
            {
                "type": "INVESTOR_STANDING",
                "title": f"Tài liệu tư cách pháp lý của nhà đầu tư {actual_investor} (Hợp pháp hóa lãnh sự)",
                "status": "READY",
            },
            {
                "type": "FINANCIAL_CAPACITY",
                "title": f"Báo cáo tài chính 02 năm gần nhất hoặc cam kết hỗ trợ tài chính của công ty mẹ ({investor_country})",
                "status": "VERIFIED",
            },
            {
                "type": "PROJECT_PROPOSAL",
                "title": f"Đề xuất dự án đầu tư công nghệ: {project_name}",
                "status": "APPROVED",
            },
            {
                "type": "SITE_RIGHTS",
                "title": f"Thỏa thuận nguyên tắc thuê mặt bằng / địa điểm thực hiện dự án tại {actual_location}",
                "status": "IN_ORDER",
            },
            {
                "type": "TECHNOLOGY_APPRAISAL",
                "title": "Giải trình về công nghệ sử dụng trong dự án đầu tư theo Điều 33 Luật Đầu tư 2020",
                "status": "VERIFIED",
            },
        ]

        dossier = {
            "ok": True,
            "project_id": project_id,
            "project_name": project_name,
            "investor_name": actual_investor,
            "investor_country": investor_country,
            "sector_code": sector_code,
            "sector_name": sector_info["name"],
            "capital_usd": actual_usd,
            "capital_vnd": actual_vnd,
            "total_investment_vnd": actual_vnd,
            "location": actual_location,
            "project_location": actual_location,
            "documents": documents,
            "required_documents_count": len(documents),
            "statutory_authority": "Sở Kế hoạch và Đầu tư / Ban Quản lý Khu công nghệ cao",
            "statutory_timeline": "15 ngày làm việc kể từ ngày nhận đủ hồ sơ hợp lệ (Điều 38 Luật Đầu tư 2020)",
            "created_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO fdi_projects (
                        project_id, project_name, investor_country, sector_code,
                        capital_usd, capital_vnd, location, status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project_id,
                        project_name,
                        investor_country,
                        sector_code,
                        actual_usd,
                        actual_vnd,
                        actual_location,
                        "ACTIVE",
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return dossier

    def list_irc_dossiers(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List registered FDI projects / IRC dossiers."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM fdi_projects ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated FDI projects, foreign loans, and remittance records."""
        with self._get_connection() as conn:
            proj_row = conn.execute(
                "SELECT COUNT(*) as cnt, COALESCE(SUM(capital_usd), 0) as sm FROM fdi_projects"
            ).fetchone()
            loan_row = conn.execute(
                "SELECT COUNT(*) as cnt, COALESCE(SUM(amount_usd), 0) as sm FROM foreign_loans"
            ).fetchone()
            remit_row = conn.execute(
                "SELECT COUNT(*) as cnt, COALESCE(SUM(amount_usd), 0) as sm FROM profit_remittances"
            ).fetchone()

        cnt = proj_row["cnt"] if proj_row else 0
        return {
            "ok": True,
            "status": "operational",
            "engine": "FDIEngine",
            "total_irc_dossiers": cnt,
            "regulatory_framework": "Luat Dau tu 2020 / TT 06/2019/TT-NHNN / TT 12/2022/TT-NHNN",
            "legal_framework": {
                "investment_law": "Law on Investment 2020 (Law No. 61/2020/QH14)",
                "decree": "Decree 31/2021/ND-CP",
                "circular_dica": "Circular 06/2019/TT-NHNN",
                "circular_loan": "Circular 12/2022/TT-NHNN",
                "circular_remittance": "Circular 186/2010/TT-BTC",
            },
            "reference_exchange_rate": EXCHANGE_RATE_USD_VND,
            "metrics": {
                "active_fdi_projects": cnt,
                "total_invested_capital_usd": proj_row["sm"] if proj_row else 0,
                "total_foreign_loans_registered": loan_row["cnt"] if loan_row else 0,
                "total_foreign_loans_usd": loan_row["sm"] if loan_row else 0,
                "total_profit_remittances": remit_row["cnt"] if remit_row else 0,
                "total_profit_remitted_usd": remit_row["sm"] if remit_row else 0,
                "supported_market_sectors": len(SECTOR_MARKET_ACCESS),
            },
            "database": str(self.db_path),
        }


FDIEngine = FdiEngine
