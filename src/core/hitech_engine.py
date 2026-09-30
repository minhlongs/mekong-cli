"""
Vietnamese High-Tech Enterprise, Science & Technology Parks & Tech Transfer Engine.
Pure Python standard library implementation adhering to tests/test_core_boundary.py.

Statutory Framework:
- Luật Công nghệ cao 2008 (Luật số 21/2008/QH12):
  * Tiêu chí công nhận Doanh nghiệp Công nghệ cao (Doanh nghiệp CNC) theo Quyết định số 10/2021/QĐ-TTg.
  * Tỷ lệ doanh thu từ sản phẩm CNC đạt tối thiểu 70% tổng doanh thu thuần.
  * Tỷ lệ chi tiêu nghiên cứu & phát triển (R&D) tại Việt Nam từ 0.5% đến 2.0% tùy quy mô vốn và lao động.
  * Tỷ lệ lao động có trình độ cao đẳng trở lên trực tiếp làm R&D đạt tối thiểu 5% (hoặc 1%-2.5% với DN quy mô lớn).
  * Chứng nhận hệ thống quản lý chất lượng đạt tiêu chuẩn ISO 9001.
  * Ưu đãi thuế TNDN: Thuế suất 10% trong 15 năm, miễn thuế 4 năm, giảm 50% trong 9 năm tiếp theo.
- Luật Chuyển giao công nghệ 2017 (Luật số 07/2017/QH14):
  * Phân loại công nghệ: Khuyến khích chuyển giao, Hạn chế chuyển giao, Cấm chuyển giao.
  * Đăng ký hợp đồng chuyển giao công nghệ bắt buộc (Điều 31): Chuyển giao từ nước ngoài vào VN, từ VN ra nước ngoài, hoặc có sử dụng vốn nhà nước.
  * Thẩm định giá công nghệ và giám định công nghệ dự án đầu tư theo Nghị định 76/2018/NĐ-CP.
- Nghị định số 10/2024/NĐ-CP (Khu công nghệ cao):
  * Tiêu chuẩn dự án đầu tư vào Khu công nghệ cao quốc gia (Hòa Lạc, TP.HCM, Đà Nẵng).
  * Suất vốn đầu tư tối thiểu: >= 100 tỷ VND/ha (hoặc >= 4 triệu USD/ha).
- Nghị định số 51/2019/NĐ-CP:
  * Xử phạt vi phạm hành chính trong hoạt động khoa học và công nghệ, chuyển giao công nghệ.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional


class HitechEngine:
    """Core engine for Vietnamese High-Tech Enterprise certification, Tech Transfer and Science Parks."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            base_dir = os.path.join(os.getcwd(), ".mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "hitech.db")
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
                CREATE TABLE IF NOT EXISTS hitech_enterprises (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    certificate_code TEXT UNIQUE NOT NULL,
                    company_name TEXT NOT NULL,
                    total_revenue_vnd REAL NOT NULL,
                    hitech_revenue_vnd REAL NOT NULL,
                    hitech_ratio_pct REAL NOT NULL,
                    rd_spending_vnd REAL NOT NULL,
                    rd_ratio_pct REAL NOT NULL,
                    total_employees INTEGER NOT NULL,
                    rd_employees INTEGER NOT NULL,
                    rd_employee_ratio_pct REAL NOT NULL,
                    has_iso9001 INTEGER NOT NULL,
                    enterprise_scale TEXT NOT NULL,
                    status TEXT NOT NULL,
                    is_qualified INTEGER NOT NULL,
                    deficiencies TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tech_transfer_contracts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    registration_code TEXT UNIQUE NOT NULL,
                    contract_title TEXT NOT NULL,
                    transferor TEXT NOT NULL,
                    transferee TEXT NOT NULL,
                    technology_name TEXT NOT NULL,
                    transfer_direction TEXT NOT NULL,
                    contract_value_usd REAL NOT NULL,
                    uses_state_capital INTEGER NOT NULL,
                    technology_category TEXT NOT NULL,
                    is_mandatory_registration INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    estimated_fine_vnd REAL NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS hitech_park_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_code TEXT UNIQUE NOT NULL,
                    project_name TEXT NOT NULL,
                    park_name TEXT NOT NULL,
                    land_area_ha REAL NOT NULL,
                    investment_capital_vnd REAL NOT NULL,
                    capital_per_ha_vnd REAL NOT NULL,
                    export_ratio_pct REAL NOT NULL,
                    commits_tech_transfer INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    is_approved INTEGER NOT NULL,
                    deficiencies TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tax_incentive_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    evaluation_code TEXT UNIQUE NOT NULL,
                    company_name TEXT NOT NULL,
                    operating_year INTEGER NOT NULL,
                    profit_before_tax_vnd REAL NOT NULL,
                    standard_tax_vnd REAL NOT NULL,
                    incentive_tax_vnd REAL NOT NULL,
                    tax_saved_vnd REAL NOT NULL,
                    applied_tax_rate_pct REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    # 1. Audit High-Tech Enterprise Certification (Quyết định số 10/2021/QĐ-TTg)
    def audit_hitech_enterprise(
        self,
        company_name: str,
        total_revenue_vnd: float,
        hitech_revenue_vnd: float,
        rd_spending_vnd: float,
        total_employees: int,
        rd_employees: int,
        has_iso9001: bool = True,
        enterprise_scale: str = "MEDIUM",
    ) -> Dict[str, Any]:
        """Audits enterprise eligibility for High-Tech Enterprise Certificate under Decision 10/2021/QD-TTg."""
        now = datetime.datetime.now()
        scale = enterprise_scale.upper().strip()
        deficiencies = []

        # Criterion 1: High-tech product revenue ratio >= 70%
        hitech_ratio = round((hitech_revenue_vnd / total_revenue_vnd) * 100.0, 2) if total_revenue_vnd > 0 else 0.0
        if hitech_ratio < 70.0:
            deficiencies.append(
                f"Tỷ lệ doanh thu sản phẩm công nghệ cao ({hitech_ratio}%) thấp hơn mức tối thiểu 70% theo Quyết định 10/2021/QĐ-TTg"
            )

        # Criterion 2: R&D spending ratio threshold based on scale
        rd_ratio = round((rd_spending_vnd / total_revenue_vnd) * 100.0, 2) if total_revenue_vnd > 0 else 0.0
        if scale in ["MICRO", "SMALL"]:
            min_rd = 2.0
        elif scale in ["MEGA", "LARGE_FDI"]:
            min_rd = 0.5
        else:  # MEDIUM or LARGE
            min_rd = 1.0

        if rd_ratio < min_rd:
            deficiencies.append(
                f"Tỷ lệ chi tiêu R&D tại Việt Nam ({rd_ratio}%) thấp hơn ngưỡng quy định ({min_rd}%) cho doanh nghiệp quy mô {scale}"
            )

        # Criterion 3: R&D employee ratio threshold
        rd_staff_ratio = round((rd_employees / total_employees) * 100.0, 2) if total_employees > 0 else 0.0
        min_rd_staff = 2.5 if scale in ["MEGA", "LARGE_FDI"] else 5.0

        if rd_staff_ratio < min_rd_staff:
            deficiencies.append(
                f"Tỷ lệ lao động làm việc trực tiếp về R&D ({rd_staff_ratio}%) thấp hơn mức tối thiểu {min_rd_staff}%"
            )

        # Criterion 4: Quality management certification
        if not has_iso9001:
            deficiencies.append("Doanh nghiệp chưa có Giấy chứng nhận hệ thống quản lý chất lượng đạt tiêu chuẩn ISO 9001 hoặc tương đương")

        is_qualified = len(deficiencies) == 0
        status = "QUALIFIED_HITECH_ENTERPRISE" if is_qualified else "DEFICIENT_CONDITIONS"
        seq = hashlib.md5(f"{company_name}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        cert_code = f"CNC-{now.year}-{seq}"

        tax_incentive_desc = (
            "Thuế suất TNDN ưu đãi 10% trong 15 năm; Miễn thuế 4 năm và Giảm 50% trong 9 năm tiếp theo; Miễn thuế nhập khẩu TSCĐ"
            if is_qualified
            else "Chưa đủ điều kiện hưởng gói ưu đãi thuế TNDN công nghệ cao"
        )

        result = {
            "certificate_code": cert_code,
            "company_name": company_name,
            "enterprise_scale": scale,
            "total_revenue_vnd": total_revenue_vnd,
            "hitech_revenue_vnd": hitech_revenue_vnd,
            "hitech_ratio_pct": hitech_ratio,
            "min_required_hitech_ratio_pct": 70.0,
            "rd_spending_vnd": rd_spending_vnd,
            "rd_ratio_pct": rd_ratio,
            "min_required_rd_ratio_pct": min_rd,
            "total_employees": total_employees,
            "rd_employees": rd_employees,
            "rd_employee_ratio_pct": rd_staff_ratio,
            "min_required_rd_staff_ratio_pct": min_rd_staff,
            "has_iso9001": has_iso9001,
            "is_qualified": is_qualified,
            "status": status,
            "tax_incentive_package": tax_incentive_desc,
            "deficiencies": deficiencies,
            "statutory_basis": "Điều 18 Luật Công nghệ cao 2008 & Quyết định số 10/2021/QĐ-TTg",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO hitech_enterprises
                (certificate_code, company_name, total_revenue_vnd, hitech_revenue_vnd,
                 hitech_ratio_pct, rd_spending_vnd, rd_ratio_pct, total_employees,
                 rd_employees, rd_employee_ratio_pct, has_iso9001, enterprise_scale,
                 status, is_qualified, deficiencies, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cert_code,
                    company_name,
                    total_revenue_vnd,
                    hitech_revenue_vnd,
                    hitech_ratio,
                    rd_spending_vnd,
                    rd_ratio,
                    total_employees,
                    rd_employees,
                    rd_staff_ratio,
                    1 if has_iso9001 else 0,
                    scale,
                    status,
                    1 if is_qualified else 0,
                    json.dumps(deficiencies, ensure_ascii=False),
                    result["created_at"],
                ),
            )

        return result

    # 2. Register Technology Transfer Contract (Luật Chuyển giao công nghệ 2017)
    def register_tech_transfer_contract(
        self,
        contract_title: str,
        transferor: str,
        transferee: str,
        technology_name: str,
        transfer_direction: str = "INWARD_FOREIGN",
        contract_value_usd: float = 500_000.0,
        uses_state_capital: bool = False,
        technology_category: str = "ENCOURAGED",
    ) -> Dict[str, Any]:
        """Registers technology transfer contract under Article 31 Law on Technology Transfer 2017."""
        now = datetime.datetime.now()
        direction = transfer_direction.upper().strip()
        category = technology_category.upper().strip()
        fine_vnd = 0.0

        # Statutory mandatory registration conditions (Art. 31 Law 07/2017)
        is_mandatory = (direction in ["INWARD_FOREIGN", "OUTWARD_FOREIGN"]) or uses_state_capital

        if category == "PROHIBITED":
            status = "PROHIBITED_TECHNOLOGY_ILLEGAL"
            fine_vnd = 90_000_000.0  # Decree 51/2019: 80-100M VND
            legal_status = "BỊ CẤM CHUYỂN GIAO: Hợp đồng vô hiệu, tịch thu tang vật và xử phạt vi phạm hành chính"
        elif is_mandatory:
            status = "REGISTERED_COMPLIANT"
            legal_status = "Đã đăng ký hợp lệ với Bộ KH&CN / Sở KH&CN theo Điều 31 Luật Chuyển giao công nghệ 2017"
        else:
            status = "VOLUNTARY_REGISTERED"
            legal_status = "Đăng ký tự nguyện đối với chuyển giao công nghệ nội địa không dùng vốn nhà nước"

        seq = hashlib.md5(f"{contract_title}:{transferor}:{transferee}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        reg_code = f"DKCG-{now.year}-{seq}"

        result = {
            "registration_code": reg_code,
            "contract_title": contract_title,
            "transferor": transferor,
            "transferee": transferee,
            "technology_name": technology_name,
            "transfer_direction": direction,
            "contract_value_usd": contract_value_usd,
            "uses_state_capital": uses_state_capital,
            "technology_category": category,
            "is_mandatory_registration": is_mandatory,
            "status": status,
            "is_approved": status != "PROHIBITED_TECHNOLOGY_ILLEGAL",
            "estimated_fine_vnd": fine_vnd,
            "legal_status": legal_status,
            "statutory_basis": "Điều 31 Luật Chuyển giao công nghệ 2017 & Nghị định 76/2018/NĐ-CP",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO tech_transfer_contracts
                (registration_code, contract_title, transferor, transferee, technology_name,
                 transfer_direction, contract_value_usd, uses_state_capital, technology_category,
                 is_mandatory_registration, status, estimated_fine_vnd, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reg_code,
                    contract_title,
                    transferor,
                    transferee,
                    technology_name,
                    direction,
                    contract_value_usd,
                    1 if uses_state_capital else 0,
                    category,
                    1 if is_mandatory else 0,
                    status,
                    fine_vnd,
                    result["created_at"],
                ),
            )

        return result

    # 3. Audit High-Tech Park Project (Nghị định 10/2024/NĐ-CP)
    def audit_hitech_park_project(
        self,
        project_name: str,
        park_name: str,
        land_area_ha: float,
        investment_capital_vnd: float,
        export_ratio_pct: float = 80.0,
        commits_tech_transfer: bool = True,
    ) -> Dict[str, Any]:
        """Audits project admission conditions in National High-Tech Parks under Decree 10/2024/ND-CP."""
        now = datetime.datetime.now()
        deficiencies = []

        # Min investment density: >= 100 billion VND/ha
        capital_per_ha = investment_capital_vnd / land_area_ha if land_area_ha > 0 else 0.0
        min_density = 100_000_000_000.0  # 100 Billion VND/ha

        if capital_per_ha < min_density:
            deficiencies.append(
                f"Suất vốn đầu tư ({capital_per_ha:,.0f} VND/ha) thấp hơn ngưỡng tối thiểu 100 tỷ VND/ha theo Nghị định 10/2024/NĐ-CP"
            )

        if not commits_tech_transfer:
            deficiencies.append("Dự án chưa cam kết lộ trình chuyển giao công nghệ cho doanh nghiệp hoặc viện nghiên cứu trong nước")

        is_approved = len(deficiencies) == 0
        status = "APPROVED_FOR_HITECH_PARK" if is_approved else "INSUFFICIENT_INVESTMENT_DENSITY"
        seq = hashlib.md5(f"{project_name}:{park_name}".encode("utf-8")).hexdigest()[:6].upper()
        proj_code = f"KCNC-{now.year}-{seq}"

        result = {
            "project_code": proj_code,
            "project_name": project_name,
            "park_name": park_name,
            "land_area_ha": land_area_ha,
            "investment_capital_vnd": investment_capital_vnd,
            "capital_per_ha_vnd": capital_per_ha,
            "min_required_capital_per_ha_vnd": min_density,
            "export_ratio_pct": export_ratio_pct,
            "commits_tech_transfer": commits_tech_transfer,
            "is_approved": is_approved,
            "status": status,
            "deficiencies": deficiencies,
            "statutory_basis": "Nghị định số 10/2024/NĐ-CP về Khu công nghệ cao",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO hitech_park_projects
                (project_code, project_name, park_name, land_area_ha, investment_capital_vnd,
                 capital_per_ha_vnd, export_ratio_pct, commits_tech_transfer, status,
                 is_approved, deficiencies, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proj_code,
                    project_name,
                    park_name,
                    land_area_ha,
                    investment_capital_vnd,
                    capital_per_ha,
                    export_ratio_pct,
                    1 if commits_tech_transfer else 0,
                    status,
                    1 if is_approved else 0,
                    json.dumps(deficiencies, ensure_ascii=False),
                    result["created_at"],
                ),
            )

        return result

    # 4. Calculate Tax Incentives for High-Tech Enterprise
    def calculate_tax_incentives(
        self,
        company_name: str,
        profit_before_tax_vnd: float,
        operating_year: int = 1,
        is_certified_hitech: bool = True,
    ) -> Dict[str, Any]:
        """Calculates Corporate Income Tax (CIT/TNDN) liability and statutory tax savings under hitech incentive regime."""
        standard_rate = 20.0
        standard_tax = profit_before_tax_vnd * (standard_rate / 100.0)

        if not is_certified_hitech or profit_before_tax_vnd <= 0:
            applied_rate = standard_rate
            incentive_tax = standard_tax
            status_desc = "Áp dụng mức thuế suất phổ thông 20% (Chưa có chứng nhận Doanh nghiệp CNC)"
        else:
            # Year 1-4: 100% Tax exemption (0%)
            if operating_year <= 4:
                applied_rate = 0.0
                incentive_tax = 0.0
                status_desc = f"Năm thứ {operating_year}: Được MIỄN 100% thuế TNDN (Giai đoạn miễn thuế 4 năm đầu)"
            # Year 5-13 (next 9 years): 50% reduction of 10% rate = 5%
            elif 5 <= operating_year <= 13:
                applied_rate = 5.0
                incentive_tax = profit_before_tax_vnd * (applied_rate / 100.0)
                status_desc = f"Năm thứ {operating_year}: Hưởng thuế suất ưu đãi 5% (Giảm 50% thuế suất ưu đãi 10% trong 9 năm tiếp theo)"
            # Year 14-15: 10% preferential rate
            elif 14 <= operating_year <= 15:
                applied_rate = 10.0
                incentive_tax = profit_before_tax_vnd * (applied_rate / 100.0)
                status_desc = f"Năm thứ {operating_year}: Hưởng thuế suất ưu đãi 10% (Giai đoạn cuối của thời hạn ưu đãi 15 năm)"
            else:
                applied_rate = standard_rate
                incentive_tax = standard_tax
                status_desc = f"Năm thứ {operating_year}: Đã hết thời hạn 15 năm ưu đãi, trở về mức phổ thông 20%"

        tax_saved = max(0.0, standard_tax - incentive_tax)
        now = datetime.datetime.now()
        seq = hashlib.md5(f"{company_name}:{operating_year}:{profit_before_tax_vnd}".encode("utf-8")).hexdigest()[:6].upper()
        eval_code = f"CIT-CNC-{now.year}-{seq}"

        result = {
            "evaluation_code": eval_code,
            "company_name": company_name,
            "operating_year": operating_year,
            "profit_before_tax_vnd": profit_before_tax_vnd,
            "standard_tax_rate_pct": standard_rate,
            "standard_tax_vnd": standard_tax,
            "applied_tax_rate_pct": applied_rate,
            "incentive_tax_vnd": incentive_tax,
            "tax_saved_vnd": tax_saved,
            "status": "INCENTIVE_APPLIED" if tax_saved > 0 else "STANDARD_TAX",
            "evaluation_summary": status_desc,
            "legal_basis": "Luật Thuế Thu nhập doanh nghiệp & Điều 18 Luật Công nghệ cao 2008",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO tax_incentive_evaluations
                (evaluation_code, company_name, operating_year, profit_before_tax_vnd,
                 standard_tax_vnd, incentive_tax_vnd, tax_saved_vnd, applied_tax_rate_pct,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    eval_code,
                    company_name,
                    operating_year,
                    profit_before_tax_vnd,
                    standard_tax,
                    incentive_tax,
                    tax_saved,
                    applied_rate,
                    result["status"],
                    result["created_at"],
                ),
            )

        return result

    # 5. List Records
    def list_records(self, category: str = "enterprises", limit: int = 20) -> List[Dict[str, Any]]:
        """Queries stored high-tech enterprises, tech transfer contracts, park projects, or tax evaluations."""
        cat = category.lower().strip()
        with self._get_connection() as conn:
            if cat in ["contracts", "transfers", "chuyen_giao"]:
                cursor = conn.execute("SELECT * FROM tech_transfer_contracts ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["parks", "projects", "kcnc"]:
                cursor = conn.execute("SELECT * FROM hitech_park_projects ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["taxes", "tax_incentives", "thue"]:
                cursor = conn.execute("SELECT * FROM tax_incentive_evaluations ORDER BY id DESC LIMIT ?", (limit,))
            else:
                cursor = conn.execute("SELECT * FROM hitech_enterprises ORDER BY id DESC LIMIT ?", (limit,))

            return [dict(row) for row in cursor.fetchall()]

    # 6. Telemetry & Summary Status
    def get_status(self) -> Dict[str, Any]:
        """Aggregates system-wide High-Tech, Tech Transfer, and Park telemetry."""
        with self._get_connection() as conn:
            total_enterprises = conn.execute("SELECT COUNT(*) FROM hitech_enterprises").fetchone()[0]
            qualified_enterprises = conn.execute("SELECT COUNT(*) FROM hitech_enterprises WHERE is_qualified = 1").fetchone()[0]
            total_contracts = conn.execute("SELECT COUNT(*) FROM tech_transfer_contracts").fetchone()[0]
            prohibited_contracts = conn.execute("SELECT COUNT(*) FROM tech_transfer_contracts WHERE status = 'PROHIBITED_TECHNOLOGY_ILLEGAL'").fetchone()[0]
            total_projects = conn.execute("SELECT COUNT(*) FROM hitech_park_projects").fetchone()[0]
            approved_projects = conn.execute("SELECT COUNT(*) FROM hitech_park_projects WHERE is_approved = 1").fetchone()[0]
            total_tax_evals = conn.execute("SELECT COUNT(*) FROM tax_incentive_evaluations").fetchone()[0]
            total_tax_savings = conn.execute("SELECT COALESCE(SUM(tax_saved_vnd), 0.0) FROM tax_incentive_evaluations").fetchone()[0]

        qualification_rate_pct = round((qualified_enterprises / total_enterprises) * 100.0, 1) if total_enterprises > 0 else 100.0

        return {
            "status": "HEALTHY",
            "statutory_law": "Luật Công nghệ cao 2008 (Luật 21/2008), Luật Chuyển giao công nghệ 2017 & Quyết định 10/2021/QĐ-TTg",
            "total_hitech_enterprises_audited": total_enterprises,
            "qualified_hitech_enterprises": qualified_enterprises,
            "enterprise_qualification_rate_pct": qualification_rate_pct,
            "total_tech_transfer_contracts": total_contracts,
            "prohibited_contracts_intercepted": prohibited_contracts,
            "total_hitech_park_projects": total_projects,
            "approved_hitech_park_projects": approved_projects,
            "total_tax_evaluations": total_tax_evals,
            "total_statutory_tax_saved_vnd": total_tax_savings,
            "timestamp": datetime.datetime.now().isoformat(),
        }
