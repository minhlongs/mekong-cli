"""
Vietnamese Public Investment, Capital Allocation, Feasibility & Medium-Term Planning Engine.
Governed by:
- Law on Public Investment 2019 (Law No. 39/2019/QH14, amended by Law No. 03/2022/QH15 and Law No. 29/2023/QH15)
- Decree No. 40/2020/ND-CP detailing the implementation of several articles of the Law on Public Investment
- Decree No. 99/2021/ND-CP on management, payment, and settlement of public investment capital
- Circular No. 12/2022/TT-BKHDT on guidelines for investment supervision and evaluation

Enforces standard-library-only pure Python constraints (zero external HTTP, zero vendor SDKs).
Uses SQLite WAL persistence at ~/.mekong/pubinvestment.db.
"""

import os
import json
import uuid
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class PublicInvestmentEngine:
    """
    Core engine for Vietnamese public investment projects, statutory classification
    (National Special, Group A, Group B, Group C) under Law 39/2019/QH14 Arts 6-10,
    medium-term & annual capital allocation plans (Arts 48-65), State Treasury
    disbursement tracking, and bottleneck resolution under Decree 40/2020/ND-CP.
    """

    SECTORS = {
        "TRANSPORT_ENERGY_INDUSTRY",
        "AGRICULTURE_IRRIGATION_URBAN",
        "HEALTH_EDUCATION_CULTURE",
        "OTHER_INFRASTRUCTURE",
    }

    CAPITAL_SOURCES = {
        "CENTRAL_BUDGET",       # Ngân sách trung ương
        "LOCAL_BUDGET",         # Ngân sách địa phương
        "ODA_CONCESSIONAL",     # Vốn ODA và vốn vay ưu đãi nước ngoài
        "GOVERNMENT_BONDS",     # Trái phiếu chính phủ
        "STATE_DEVELOPMENT",    # Vốn tín dụng đầu tư phát triển của Nhà nước
    }

    BOTTLENECK_TYPES = {
        "LAND_CLEARANCE",       # Giải phóng mặt bằng, bồi thường tái định cư
        "BIDDING_PROCEDURE",    # Thủ tục lựa chọn nhà thầu, khiếu nại đấu thầu
        "MATERIAL_PRICE_SPIKE", # Biến động giá vật liệu xây dựng
        "ODA_DONOR_APPROVAL",   # Thủ tục chấp thuận của nhà tài trợ nước ngoài
        "ENVIRONMENT_PERMIT",   # Thủ tục đánh giá tác động môi trường (ĐTM)
        "CONTRACTOR_CAPACITY",  # Năng lực thi công của nhà thầu yếu kém
    }

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            env_db = os.environ.get("MEKONG_PUBINVESTMENT_DB")
            if env_db:
                self.db_path = env_db
            else:
                base_dir = Path.home() / ".mekong"
                base_dir.mkdir(parents=True, exist_ok=True)
                self.db_path = str(base_dir / "pubinvestment.db")
        else:
            self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS investment_projects (
                    project_id TEXT PRIMARY KEY,
                    project_code TEXT NOT NULL UNIQUE,
                    project_name TEXT NOT NULL,
                    sector TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    total_investment_vnd REAL NOT NULL,
                    capital_source TEXT NOT NULL,
                    competent_authority TEXT NOT NULL,
                    managing_agency TEXT NOT NULL,
                    implementation_location TEXT NOT NULL,
                    start_year INTEGER NOT NULL,
                    end_year INTEGER NOT NULL,
                    resettlement_people INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'PROPOSAL',
                    approved_at TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS capital_plans (
                    plan_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    plan_type TEXT NOT NULL,
                    fiscal_year INTEGER NOT NULL,
                    period_span TEXT NOT NULL,
                    allocated_capital_vnd REAL NOT NULL,
                    priority_tier INTEGER NOT NULL DEFAULT 5,
                    approved_by TEXT NOT NULL,
                    decision_number TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES investment_projects(project_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS disbursement_records (
                    disbursement_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    fiscal_year INTEGER NOT NULL,
                    disbursed_amount_vnd REAL NOT NULL,
                    treasury_office TEXT NOT NULL,
                    payment_voucher_number TEXT NOT NULL,
                    recipient_contractor TEXT NOT NULL,
                    disbursed_at TEXT NOT NULL,
                    notes TEXT,
                    FOREIGN KEY (project_id) REFERENCES investment_projects(project_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS bottleneck_assessments (
                    assessment_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    bottleneck_type TEXT NOT NULL,
                    severity_level TEXT NOT NULL,
                    estimated_delay_months INTEGER NOT NULL,
                    mitigation_measures TEXT NOT NULL,
                    responsible_party TEXT NOT NULL,
                    reported_at TEXT NOT NULL,
                    resolved INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (project_id) REFERENCES investment_projects(project_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_proj_class ON investment_projects(classification);
                CREATE INDEX IF NOT EXISTS idx_proj_status ON investment_projects(status);
                CREATE INDEX IF NOT EXISTS idx_plan_proj ON capital_plans(project_id);
                CREATE INDEX IF NOT EXISTS idx_plan_year ON capital_plans(fiscal_year);
                CREATE INDEX IF NOT EXISTS idx_disb_proj ON disbursement_records(project_id);
                CREATE INDEX IF NOT EXISTS idx_disb_year ON disbursement_records(fiscal_year);
                CREATE INDEX IF NOT EXISTS idx_btn_proj ON bottleneck_assessments(project_id);
            """)

    # -------------------------------------------------------------------------
    # 1. Project Classification & Registration (Law 39/2019/QH14 Arts 6-10)
    # -------------------------------------------------------------------------
    @classmethod
    def classify_project(
        cls,
        sector: str,
        total_investment_vnd: float,
        resettlement_people: int = 0,
        is_nationally_sensitive: bool = False,
    ) -> Dict[str, Any]:
        """
        Determines statutory project classification (NATIONAL_SPECIAL, GROUP_A, GROUP_B, GROUP_C)
        and competent approving authority under Law 39/2019/QH14 Articles 6-10 and 17-18.
        """
        sec = sector.upper().strip()
        if sec not in cls.SECTORS:
            raise ValueError(f"Invalid sector '{sector}'. Allowed: {sorted(cls.SECTORS)}")
        if total_investment_vnd < 0:
            raise ValueError("Total investment capital cannot be negative.")
        if resettlement_people < 0:
            raise ValueError("Resettlement people count cannot be negative.")

        # Article 7: National Special Projects (Dự án quan trọng quốc gia)
        # Threshold: >= 10,000 billion VND (or 30,000B under recent amendments) or >= 20,000 people resettlement
        if total_investment_vnd >= 10_000_000_000_000 or resettlement_people >= 20_000 or is_nationally_sensitive:
            return {
                "ok": True,
                "classification": "NATIONAL_SPECIAL",
                "classification_name": "Dự án quan trọng quốc gia",
                "statutory_basis": "Luật Đầu tư công 2019 Điều 7",
                "competent_deciding_authority": "Quốc hội quyết định chủ trương đầu tư",
                "approving_authority": "Thủ tướng Chính phủ quyết định đầu tư",
                "study_type_required": "Báo cáo nghiên cứu tiền khả thi & Báo cáo nghiên cứu khả thi",
            }

        # Article 8: Group A Projects (Dự án nhóm A)
        group_a = False
        if sec == "TRANSPORT_ENERGY_INDUSTRY" and total_investment_vnd >= 2_300_000_000_000:
            group_a = True
        elif sec == "AGRICULTURE_IRRIGATION_URBAN" and total_investment_vnd >= 1_500_000_000_000:
            group_a = True
        elif sec == "HEALTH_EDUCATION_CULTURE" and total_investment_vnd >= 1_000_000_000_000:
            group_a = True
        elif sec == "OTHER_INFRASTRUCTURE" and total_investment_vnd >= 1_000_000_000_000:
            group_a = True

        if group_a:
            return {
                "ok": True,
                "classification": "GROUP_A",
                "classification_name": "Dự án nhóm A",
                "statutory_basis": "Luật Đầu tư công 2019 Điều 8",
                "competent_deciding_authority": "Thủ tướng Chính phủ quyết định chủ trương đầu tư",
                "approving_authority": "Bộ trưởng / Chủ tịch UBND cấp tỉnh quyết định đầu tư",
                "study_type_required": "Báo cáo nghiên cứu tiền khả thi",
            }

        # Article 9: Group B Projects (Dự án nhóm B)
        group_b = False
        if sec == "TRANSPORT_ENERGY_INDUSTRY" and 120_000_000_000 <= total_investment_vnd < 2_300_000_000_000:
            group_b = True
        elif sec == "AGRICULTURE_IRRIGATION_URBAN" and 80_000_000_000 <= total_investment_vnd < 1_500_000_000_000:
            group_b = True
        elif sec == "HEALTH_EDUCATION_CULTURE" and 60_000_000_000 <= total_investment_vnd < 1_000_000_000_000:
            group_b = True
        elif sec == "OTHER_INFRASTRUCTURE" and 45_000_000_000 <= total_investment_vnd < 1_000_000_000_000:
            group_b = True

        if group_b:
            return {
                "ok": True,
                "classification": "GROUP_B",
                "classification_name": "Dự án nhóm B",
                "statutory_basis": "Luật Đầu tư công 2019 Điều 9",
                "competent_deciding_authority": "HĐND cấp tỉnh / Bộ trưởng quyết định chủ trương đầu tư",
                "approving_authority": "Chủ tịch UBND cấp tỉnh / Bộ trưởng quyết định đầu tư",
                "study_type_required": "Báo cáo đề xuất chủ trương đầu tư",
            }

        # Article 10: Group C Projects (Dự án nhóm C)
        return {
            "ok": True,
            "classification": "GROUP_C",
            "classification_name": "Dự án nhóm C",
            "statutory_basis": "Luật Đầu tư công 2019 Điều 10",
            "competent_deciding_authority": "HĐND cấp tỉnh / UBND cấp huyện theo phân cấp",
            "approving_authority": "Chủ tịch UBND cấp tỉnh / Chủ tịch UBND cấp huyện",
            "study_type_required": "Báo cáo đề xuất chủ trương đầu tư",
        }

    def register_project(
        self,
        project_code: str,
        project_name: str,
        sector: str,
        total_investment_vnd: float,
        capital_source: str,
        managing_agency: str,
        implementation_location: str,
        start_year: int,
        end_year: int,
        resettlement_people: int = 0,
        is_nationally_sensitive: bool = False,
    ) -> Dict[str, Any]:
        """
        Registers a new public investment project and assigns statutory classification.
        """
        if not project_code or not project_code.strip():
            raise ValueError("Project code cannot be empty.")
        if not project_name or not project_name.strip():
            raise ValueError("Project name cannot be empty.")
        if not managing_agency or not managing_agency.strip():
            raise ValueError("Managing agency cannot be empty.")
        if not implementation_location or not implementation_location.strip():
            raise ValueError("Implementation location cannot be empty.")
        if start_year > end_year:
            raise ValueError("Start year cannot be after end year.")

        source = capital_source.upper().strip()
        if source not in self.CAPITAL_SOURCES:
            raise ValueError(f"Invalid capital source '{capital_source}'. Allowed: {sorted(self.CAPITAL_SOURCES)}")

        cls_info = self.classify_project(
            sector=sector,
            total_investment_vnd=total_investment_vnd,
            resettlement_people=resettlement_people,
            is_nationally_sensitive=is_nationally_sensitive,
        )

        project_id = f"PRJ-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO investment_projects (
                    project_id, project_code, project_name, sector, classification,
                    total_investment_vnd, capital_source, competent_authority,
                    managing_agency, implementation_location, start_year, end_year,
                    resettlement_people, status, approved_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    project_code.strip(),
                    project_name.strip(),
                    sector.upper().strip(),
                    cls_info["classification"],
                    float(total_investment_vnd),
                    source,
                    cls_info["competent_deciding_authority"],
                    managing_agency.strip(),
                    implementation_location.strip(),
                    start_year,
                    end_year,
                    resettlement_people,
                    "APPROVED",
                    now_iso,
                    now_iso,
                ),
            )

        return {
            "ok": True,
            "project_id": project_id,
            "project_code": project_code.strip(),
            "project_name": project_name.strip(),
            "sector": sector.upper().strip(),
            "classification": cls_info["classification"],
            "classification_name": cls_info["classification_name"],
            "total_investment_vnd": float(total_investment_vnd),
            "capital_source": source,
            "competent_authority": cls_info["competent_deciding_authority"],
            "managing_agency": managing_agency.strip(),
            "implementation_location": implementation_location.strip(),
            "duration": f"{start_year} - {end_year}",
            "resettlement_people": resettlement_people,
            "status": "APPROVED",
            "study_type_required": cls_info["study_type_required"],
            "created_at": now_iso,
        }

    # -------------------------------------------------------------------------
    # 2. Capital Allocation Plans (Law 39/2019/QH14 Arts 48-65)
    # -------------------------------------------------------------------------
    def allocate_capital_plan(
        self,
        project_id: str,
        plan_type: str,
        fiscal_year: int,
        allocated_capital_vnd: float,
        approved_by: str,
        decision_number: str,
        priority_tier: int = 5,
        period_span: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Allocates public investment capital under medium-term (5-year) or annual plans.
        Priority tiers (Law 39/2019/QH14 Art 51):
        1: Advance capital recovery (Thu hồi vốn ứng trước)
        2: Outstanding capital construction debt settlement (Thanh toán nợ đọng XDCB)
        3: ODA counterpart funds (Đối ứng vốn ODA)
        4: Transitional projects completed in period (Dự án chuyển tiếp)
        5: New start projects (Dự án khởi công mới)
        """
        p_type = plan_type.upper().strip()
        if p_type not in ("MEDIUM_TERM", "ANNUAL"):
            raise ValueError(f"Invalid plan type '{plan_type}'. Allowed: 'MEDIUM_TERM', 'ANNUAL'.")
        if allocated_capital_vnd <= 0:
            raise ValueError("Allocated capital must be greater than zero.")
        if not approved_by or not approved_by.strip():
            raise ValueError("Approving authority cannot be empty.")
        if not decision_number or not decision_number.strip():
            raise ValueError("Decision number cannot be empty.")
        if priority_tier not in (1, 2, 3, 4, 5):
            raise ValueError("Priority tier must be between 1 and 5 under Article 51.")

        with self._get_connection() as conn:
            proj = conn.execute("SELECT * FROM investment_projects WHERE project_id = ?", (project_id,)).fetchone()

        if not proj:
            raise KeyError(f"Public investment project '{project_id}' not found.")

        # Ensure cumulative allocation does not exceed total investment
        with self._get_connection() as conn:
            total_allocated = conn.execute(
                "SELECT COALESCE(SUM(allocated_capital_vnd), 0) FROM capital_plans WHERE project_id = ? AND plan_type = 'ANNUAL'",
                (project_id,),
            ).fetchone()[0]

        if p_type == "ANNUAL" and (total_allocated + allocated_capital_vnd) > proj["total_investment_vnd"]:
            raise ValueError(
                f"Cumulative annual allocation ({total_allocated + allocated_capital_vnd:,.0f} VND) "
                f"exceeds total project investment ({proj['total_investment_vnd']:,.0f} VND)."
            )

        span = period_span or (f"{fiscal_year - (fiscal_year % 5)}-{fiscal_year - (fiscal_year % 5) + 4}" if p_type == "MEDIUM_TERM" else str(fiscal_year))
        plan_id = f"PLN-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        tier_descriptions = {
            1: "Thu hồi các khoản vốn ứng trước (Bậc 1 Điều 51)",
            2: "Thanh toán nợ đọng xây dựng cơ bản (Bậc 2 Điều 51)",
            3: "Vốn đối ứng cho dự án ODA & vốn vay ưu đãi (Bậc 3 Điều 51)",
            4: "Dự án chuyển tiếp hoàn thành trong kỳ (Bậc 4 Điều 51)",
            5: "Dự án khởi công mới đáp ứng điều kiện (Bậc 5 Điều 51)",
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO capital_plans (
                    plan_id, project_id, plan_type, fiscal_year, period_span,
                    allocated_capital_vnd, priority_tier, approved_by,
                    decision_number, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_id,
                    project_id,
                    p_type,
                    fiscal_year,
                    span,
                    float(allocated_capital_vnd),
                    priority_tier,
                    approved_by.strip(),
                    decision_number.strip(),
                    now_iso,
                ),
            )

        return {
            "ok": True,
            "plan_id": plan_id,
            "project_id": project_id,
            "project_name": proj["project_name"],
            "plan_type": p_type,
            "fiscal_year": fiscal_year,
            "period_span": span,
            "allocated_capital_vnd": float(allocated_capital_vnd),
            "priority_tier": priority_tier,
            "priority_description": tier_descriptions[priority_tier],
            "approved_by": approved_by.strip(),
            "decision_number": decision_number.strip(),
            "created_at": now_iso,
        }

    # -------------------------------------------------------------------------
    # 3. State Treasury Disbursement (Decree 99/2021/ND-CP)
    # -------------------------------------------------------------------------
    def record_disbursement(
        self,
        project_id: str,
        fiscal_year: int,
        disbursed_amount_vnd: float,
        treasury_office: str,
        payment_voucher_number: str,
        recipient_contractor: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Records a capital disbursement payment voucher through the State Treasury.
        Computes the updated project disbursement rate and financial progress.
        """
        if disbursed_amount_vnd <= 0:
            raise ValueError("Disbursed amount must be greater than zero.")
        if not treasury_office or not treasury_office.strip():
            raise ValueError("State Treasury office cannot be empty.")
        if not payment_voucher_number or not payment_voucher_number.strip():
            raise ValueError("Payment voucher number cannot be empty.")
        if not recipient_contractor or not recipient_contractor.strip():
            raise ValueError("Recipient contractor cannot be empty.")

        with self._get_connection() as conn:
            proj = conn.execute("SELECT * FROM investment_projects WHERE project_id = ?", (project_id,)).fetchone()

        if not proj:
            raise KeyError(f"Public investment project '{project_id}' not found.")

        # Check total allocated annual capital for this fiscal year
        with self._get_connection() as conn:
            allocated_year = conn.execute(
                "SELECT COALESCE(SUM(allocated_capital_vnd), 0) FROM capital_plans WHERE project_id = ? AND fiscal_year = ? AND plan_type = 'ANNUAL'",
                (project_id, fiscal_year),
            ).fetchone()[0]

            disbursed_year = conn.execute(
                "SELECT COALESCE(SUM(disbursed_amount_vnd), 0) FROM disbursement_records WHERE project_id = ? AND fiscal_year = ?",
                (project_id, fiscal_year),
            ).fetchone()[0]

        if allocated_year > 0 and (disbursed_year + disbursed_amount_vnd) > allocated_year:
            raise ValueError(
                f"Total disbursement ({disbursed_year + disbursed_amount_vnd:,.0f} VND) "
                f"exceeds annual capital allocation ({allocated_year:,.0f} VND) for fiscal year {fiscal_year}."
            )

        disbursement_id = f"DIS-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO disbursement_records (
                    disbursement_id, project_id, fiscal_year, disbursed_amount_vnd,
                    treasury_office, payment_voucher_number, recipient_contractor,
                    disbursed_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    disbursement_id,
                    project_id,
                    fiscal_year,
                    float(disbursed_amount_vnd),
                    treasury_office.strip(),
                    payment_voucher_number.strip(),
                    recipient_contractor.strip(),
                    now_iso,
                    notes.strip() if notes else None,
                ),
            )

        new_total_disbursed = disbursed_year + disbursed_amount_vnd
        rate_pct = 0.0
        if allocated_year > 0:
            rate_pct = round((new_total_disbursed / allocated_year) * 100.0, 2)

        return {
            "ok": True,
            "disbursement_id": disbursement_id,
            "project_id": project_id,
            "project_name": proj["project_name"],
            "fiscal_year": fiscal_year,
            "disbursed_amount_vnd": float(disbursed_amount_vnd),
            "total_disbursed_year_vnd": new_total_disbursed,
            "allocated_capital_year_vnd": allocated_year,
            "disbursement_rate_pct": rate_pct,
            "treasury_office": treasury_office.strip(),
            "payment_voucher_number": payment_voucher_number.strip(),
            "recipient_contractor": recipient_contractor.strip(),
            "disbursed_at": now_iso,
        }

    # -------------------------------------------------------------------------
    # 4. Bottleneck Assessment & Risk Resolution (Decree 40/2020/ND-CP)
    # -------------------------------------------------------------------------
    def assess_bottleneck(
        self,
        project_id: str,
        bottleneck_type: str,
        severity_level: str,
        estimated_delay_months: int,
        mitigation_measures: str,
        responsible_party: str,
    ) -> Dict[str, Any]:
        """
        Records and analyzes a project execution bottleneck (e.g. land clearance, bidding).
        """
        btn = bottleneck_type.upper().strip()
        if btn not in self.BOTTLENECK_TYPES:
            raise ValueError(f"Invalid bottleneck type '{bottleneck_type}'. Allowed: {sorted(self.BOTTLENECK_TYPES)}")
        sev = severity_level.upper().strip()
        if sev not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            raise ValueError(f"Invalid severity level '{severity_level}'. Allowed: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'.")
        if estimated_delay_months < 0:
            raise ValueError("Estimated delay months cannot be negative.")
        if not mitigation_measures or not mitigation_measures.strip():
            raise ValueError("Mitigation measures cannot be empty.")
        if not responsible_party or not responsible_party.strip():
            raise ValueError("Responsible party cannot be empty.")

        with self._get_connection() as conn:
            proj = conn.execute("SELECT * FROM investment_projects WHERE project_id = ?", (project_id,)).fetchone()

        if not proj:
            raise KeyError(f"Public investment project '{project_id}' not found.")

        assessment_id = f"BTN-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO bottleneck_assessments (
                    assessment_id, project_id, bottleneck_type, severity_level,
                    estimated_delay_months, mitigation_measures, responsible_party,
                    reported_at, resolved
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    assessment_id,
                    project_id,
                    btn,
                    sev,
                    estimated_delay_months,
                    mitigation_measures.strip(),
                    responsible_party.strip(),
                    now_iso,
                ),
            )

        return {
            "ok": True,
            "assessment_id": assessment_id,
            "project_id": project_id,
            "project_name": proj["project_name"],
            "bottleneck_type": btn,
            "severity_level": sev,
            "estimated_delay_months": estimated_delay_months,
            "mitigation_measures": mitigation_measures.strip(),
            "responsible_party": responsible_party.strip(),
            "reported_at": now_iso,
            "resolved": False,
        }

    # -------------------------------------------------------------------------
    # 5. Queries and Telemetry
    # -------------------------------------------------------------------------
    def list_records(
        self,
        category: str = "all",
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Lists projects, capital allocation plans, disbursements, and bottlenecks.
        """
        cat = category.lower().strip()
        res: Dict[str, Any] = {"ok": True}
        with self._get_connection() as conn:
            if cat in ("all", "projects"):
                rows = conn.execute(
                    "SELECT project_id, project_code, project_name, sector, classification, total_investment_vnd, status, managing_agency FROM investment_projects ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["projects"] = [dict(r) for r in rows]

            if cat in ("all", "plans"):
                rows = conn.execute(
                    "SELECT plan_id, project_id, plan_type, fiscal_year, allocated_capital_vnd, priority_tier, decision_number FROM capital_plans ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["plans"] = [dict(r) for r in rows]

            if cat in ("all", "disbursements"):
                rows = conn.execute(
                    "SELECT disbursement_id, project_id, fiscal_year, disbursed_amount_vnd, treasury_office, payment_voucher_number, disbursed_at FROM disbursement_records ORDER BY disbursed_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["disbursements"] = [dict(r) for r in rows]

            if cat in ("all", "bottlenecks"):
                rows = conn.execute(
                    "SELECT assessment_id, project_id, bottleneck_type, severity_level, estimated_delay_months, resolved FROM bottleneck_assessments ORDER BY reported_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                res["bottlenecks"] = [dict(r) for r in rows]

        return res

    def get_telemetry_status(self) -> Dict[str, Any]:
        """
        Aggregates national public investment telemetry, disbursement velocity, and risk ratings.
        """
        with self._get_connection() as conn:
            total_projects = conn.execute("SELECT COUNT(*) FROM investment_projects").fetchone()[0]
            national_special = conn.execute("SELECT COUNT(*) FROM investment_projects WHERE classification = 'NATIONAL_SPECIAL'").fetchone()[0]
            group_a = conn.execute("SELECT COUNT(*) FROM investment_projects WHERE classification = 'GROUP_A'").fetchone()[0]
            group_b = conn.execute("SELECT COUNT(*) FROM investment_projects WHERE classification = 'GROUP_B'").fetchone()[0]
            group_c = conn.execute("SELECT COUNT(*) FROM investment_projects WHERE classification = 'GROUP_C'").fetchone()[0]
            total_committed_vnd = conn.execute("SELECT COALESCE(SUM(total_investment_vnd), 0) FROM investment_projects").fetchone()[0]

            total_allocated_vnd = conn.execute("SELECT COALESCE(SUM(allocated_capital_vnd), 0) FROM capital_plans WHERE plan_type = 'ANNUAL'").fetchone()[0]
            total_disbursed_vnd = conn.execute("SELECT COALESCE(SUM(disbursed_amount_vnd), 0) FROM disbursement_records").fetchone()[0]

            total_bottlenecks = conn.execute("SELECT COUNT(*) FROM bottleneck_assessments").fetchone()[0]
            critical_bottlenecks = conn.execute("SELECT COUNT(*) FROM bottleneck_assessments WHERE severity_level = 'CRITICAL' AND resolved = 0").fetchone()[0]

        disbursement_velocity_pct = 0.0
        if total_allocated_vnd > 0:
            disbursement_velocity_pct = round((total_disbursed_vnd / total_allocated_vnd) * 100.0, 2)

        return {
            "ok": True,
            "status": "HEALTHY",
            "regulatory_framework": {
                "law": "Luật Đầu tư công 2019 (Luật số 39/2019/QH14 & Luật số 29/2023/QH15)",
                "decree_guideline": "Nghị định số 40/2020/ND-CP",
                "decree_payment": "Nghị định số 99/2021/ND-CP",
            },
            "projects": {
                "total": total_projects,
                "national_special": national_special,
                "group_a": group_a,
                "group_b": group_b,
                "group_c": group_c,
                "total_committed_vnd": total_committed_vnd,
            },
            "capital_and_disbursement": {
                "total_annual_allocated_vnd": total_allocated_vnd,
                "total_disbursed_vnd": total_disbursed_vnd,
                "national_disbursement_rate_pct": disbursement_velocity_pct,
            },
            "bottlenecks": {
                "total_reported": total_bottlenecks,
                "critical_unresolved": critical_bottlenecks,
            },
        }
