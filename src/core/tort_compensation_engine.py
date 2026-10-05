# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Non-Contractual Civil Liability & Tort Compensation Suite (Phase 150).

Statutory framework:
- Civil Code 2015 (Bộ luật Dân sự số 91/2015/QH13) - Phần thứ ba, Chương XX: Trách nhiệm bồi thường thiệt hại ngoài hợp đồng (Điều 584–608)
- Resolution No. 02/2022/NQ-HDTP of the Supreme People's Court on guiding non-contractual tort damages
- Decree No. 73/2024/ND-CP on statutory base salary (Mức lương cơ sở: 2,340,000 VND/tháng from 2024-07-01)
- Civil Procedure Code 2015 (Bộ luật Tố tụng Dân sự số 92/2015/QH13) - Điều 147 & Pháp lệnh Án phí, lệ phí Tòa án
"""

from __future__ import annotations

import datetime
import enum
import json
import os
import sqlite3
import tempfile
from typing import Any, Dict, List, Optional, Tuple
import uuid


# Statutory Base Salary according to Decree 73/2024/ND-CP
BASE_SALARY_VND: float = 2_340_000.0

# Statutory Caps on Emotional Distress Compensation (Civil Code 2015)
CAP_MONTHS_HEALTH_DAMAGE: int = 50   # Điều 590.2: Tối đa 50 lần mức lương cơ sở (117,000,000 VND)
CAP_MONTHS_LIFE_DAMAGE: int = 100    # Điều 591.2: Tối đa 100 lần mức lương cơ sở (234,000,000 VND)
CAP_MONTHS_REPUTATION_DAMAGE: int = 10  # Điều 592.2: Tối đa 10 lần mức lương cơ sở (23,400,000 VND)
CAP_MONTHS_CORPSE_DAMAGE: int = 30   # Điều 606.2: Tối đa 30 lần mức lương cơ sở (70,200,000 VND)
CAP_MONTHS_GRAVE_DAMAGE: int = 10    # Điều 607.2: Tối đa 10 lần mức lương cơ sở (23,400,000 VND)

# Statutory limitation period (Điều 588 BLDS 2015): 3 years
STATUTE_LIMITATION_YEARS: int = 3


class DamageCategory(str, enum.Enum):
    HEALTH = "HEALTH"                        # Thiệt hại do sức khỏe bị xâm phạm (Điều 590)
    LIFE = "LIFE"                            # Thiệt hại do tính mạng bị xâm phạm (Điều 591)
    HONOR_REPUTATION = "HONOR_REPUTATION"    # Thiệt hại do danh dự, nhân phẩm, uy tín bị xâm phạm (Điều 592)
    PROPERTY = "PROPERTY"                    # Thiệt hại do tài sản bị xâm phạm (Điều 589)
    CORPSE = "CORPSE"                        # Thiệt hại do thi thể bị xâm phạm (Điều 606)
    GRAVE = "GRAVE"                          # Thiệt hại do mồ mả bị xâm phạm (Điều 607)


class LiabilityType(str, enum.Enum):
    FAULT_BASED = "FAULT_BASED"                              # Trách nhiệm do lỗi thông thường (Điều 584)
    HIGH_RISK_SOURCE = "HIGH_RISK_SOURCE"                    # Nguồn nguy hiểm cao độ - Trách nhiệm nghiêm ngặt (Điều 601)
    LEGAL_ENTITY = "LEGAL_ENTITY"                            # Pháp nhân bồi thường do hành vi của người của pháp nhân (Điều 597)
    EMPLOYER_APPRENTICE = "EMPLOYER_APPRENTICE"              # Cá nhân/pháp nhân bồi thường cho người làm công/học nghề (Điều 600)
    MINOR_UNDER_15 = "MINOR_UNDER_15"                        # Người dưới 15 tuổi gây thiệt hại (Điều 586.2, Điều 599)
    MINOR_15_TO_18 = "MINOR_15_TO_18"                        # Người từ 15 đến dưới 18 tuổi gây thiệt hại (Điều 586.2)
    INCAPACITATED_PERSON = "INCAPACITATED_PERSON"            # Người mất năng lực hành vi dân sự gây thiệt hại (Điều 586.3)
    ANIMAL_DAMAGE = "ANIMAL_DAMAGE"                          # Súc vật gây thiệt hại (Điều 603)
    TREE_DAMAGE = "TREE_DAMAGE"                              # Cây cối gãy đổ gây thiệt hại (Điều 604)
    CONSTRUCTION_DAMAGE = "CONSTRUCTION_DAMAGE"              # Nhà cửa, công trình xây dựng gây thiệt hại (Điều 605)
    POLLUTION_DAMAGE = "POLLUTION_DAMAGE"                    # Ô nhiễm môi trường gây thiệt hại (Điều 602)


class FaultType(str, enum.Enum):
    INTENTIONAL = "INTENTIONAL"                  # Lỗi cố ý
    GROSS_NEGLIGENCE = "GROSS_NEGLIGENCE"        # Lỗi vô ý nghiêm trọng
    SIMPLE_NEGLIGENCE = "SIMPLE_NEGLIGENCE"      # Lỗi vô ý thông thường
    NO_FAULT = "NO_FAULT"                        # Không có lỗi (chỉ áp dụng trách nhiệm nghiêm ngặt)
    VICTIM_SOLE_FAULT = "VICTIM_SOLE_FAULT"      # Hoàn toàn do lỗi của nạn nhân (Miễn trừ theo Điều 584.2, 601.3)
    VICTIM_PARTIAL_FAULT = "VICTIM_PARTIAL_FAULT"# Lỗi hỗn hợp (Trừ phần lỗi theo Điều 585.4)


class CaseStatus(str, enum.Enum):
    REGISTERED = "REGISTERED"
    ASSESSED = "ASSESSED"
    SETTLED = "SETTLED"
    LITIGATING = "LITIGATING"
    ENFORCED = "ENFORCED"
    CLOSED = "CLOSED"


class TortCompensationEngine:
    """Enterprise Engine for Vietnamese Non-Contractual Civil Liability & Tort Compensation Assessment."""

    def __init__(self, db_path: Optional[str] = None):
        self._memory_conn: Optional[sqlite3.Connection] = None
        if db_path:
            self.db_path = db_path
        elif os.getenv("MEKONG_TORT_DB"):
            self.db_path = os.getenv("MEKONG_TORT_DB")
        else:
            base_dir = os.path.expanduser("~/.mekong")
            try:
                os.makedirs(base_dir, exist_ok=True)
                test_path = os.path.join(base_dir, "tort.db")
                with sqlite3.connect(test_path) as test_conn:
                    test_conn.execute("SELECT 1;")
                self.db_path = test_path
            except Exception:
                tmp_dir = os.getenv("TMPDIR") or tempfile.gettempdir()
                self.db_path = os.path.join(tmp_dir, "mekong_tort.db")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self.db_path == ":memory:":
            if self._memory_conn is None:
                self._memory_conn = sqlite3.connect(":memory:")
                self._memory_conn.row_factory = sqlite3.Row
            return self._memory_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS tort_cases (
                    case_id TEXT PRIMARY KEY,
                    incident_date TEXT NOT NULL,
                    discovery_date TEXT NOT NULL,
                    incident_location TEXT NOT NULL,
                    damage_category TEXT NOT NULL,
                    liability_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS case_parties (
                    party_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    party_role TEXT NOT NULL, -- CLAIMANT, DEFENDANT, VICARIOUS_LIABLE, INSURER, DEPENDENT
                    full_name TEXT NOT NULL,
                    national_id TEXT,
                    date_of_birth TEXT,
                    phone TEXT,
                    address TEXT,
                    economic_capacity_level TEXT, -- EXCELLENT, AVERAGE, POOR, INSOLVENT
                    fault_percentage REAL DEFAULT 0.0,
                    is_direct_tortfeasor BOOLEAN DEFAULT 1,
                    FOREIGN KEY (case_id) REFERENCES tort_cases(case_id)
                );

                CREATE TABLE IF NOT EXISTS damage_claims (
                    claim_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    item_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount_claimed REAL NOT NULL,
                    amount_approved REAL NOT NULL,
                    is_statutory_capped BOOLEAN DEFAULT 0,
                    statutory_cap_amount REAL,
                    evidence_attached TEXT,
                    legal_basis TEXT NOT NULL,
                    FOREIGN KEY (case_id) REFERENCES tort_cases(case_id)
                );

                CREATE TABLE IF NOT EXISTS dependent_allowances (
                    allowance_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    dependent_name TEXT NOT NULL,
                    relationship TEXT NOT NULL,
                    date_of_birth TEXT,
                    monthly_allowance REAL NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    total_calculated REAL NOT NULL,
                    legal_basis TEXT NOT NULL,
                    FOREIGN KEY (case_id) REFERENCES tort_cases(case_id)
                );

                CREATE TABLE IF NOT EXISTS settlements (
                    settlement_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    settlement_date TEXT NOT NULL,
                    total_agreed_amount REAL NOT NULL,
                    payment_terms TEXT NOT NULL,
                    is_court_recognized BOOLEAN DEFAULT 0,
                    conciliator_name TEXT,
                    status TEXT NOT NULL,
                    FOREIGN KEY (case_id) REFERENCES tort_cases(case_id)
                );
            """)

    # -------------------------------------------------------------------------
    # 1. CASE MANAGEMENT & STATUTE OF LIMITATIONS
    # -------------------------------------------------------------------------

    def create_case(
        self,
        incident_date: str,
        incident_location: str,
        damage_category: str | DamageCategory,
        liability_type: str | LiabilityType,
        description: str,
        discovery_date: Optional[str] = None,
        case_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register a new non-contractual tort compensation case and verify statute of limitations."""
        cid = case_id or f"TC-{uuid.uuid4().hex[:8].upper()}"
        d_category = damage_category.value if isinstance(damage_category, DamageCategory) else damage_category
        l_type = liability_type.value if isinstance(liability_type, LiabilityType) else liability_type
        disc_date = discovery_date or incident_date
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Check statute of limitations (Điều 588 BLDS 2015: 03 years)
        limitation_check = self.check_statute_of_limitations(disc_date)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO tort_cases (
                    case_id, incident_date, discovery_date, incident_location,
                    damage_category, liability_type, status, description,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cid, incident_date, disc_date, incident_location,
                    d_category, l_type, CaseStatus.REGISTERED.value, description,
                    now_str, now_str,
                ),
            )

        return {
            "case_id": cid,
            "incident_date": incident_date,
            "discovery_date": disc_date,
            "incident_location": incident_location,
            "damage_category": d_category,
            "liability_type": l_type,
            "status": CaseStatus.REGISTERED.value,
            "description": description,
            "statute_of_limitations": limitation_check,
        }

    def check_statute_of_limitations(
        self,
        discovery_date_str: str,
        reference_date_str: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Assess the 3-year statute of limitations according to Article 588 Civil Code 2015."""
        try:
            disc_dt = datetime.datetime.fromisoformat(discovery_date_str.split("T")[0])
        except Exception:
            disc_dt = datetime.datetime.strptime(discovery_date_str, "%Y-%m-%d")

        ref_dt = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        if reference_date_str:
            try:
                ref_dt = datetime.datetime.fromisoformat(reference_date_str.split("T")[0])
            except Exception:
                ref_dt = datetime.datetime.strptime(reference_date_str, "%Y-%m-%d")

        expiry_dt = disc_dt + datetime.timedelta(days=365 * STATUTE_LIMITATION_YEARS + 1)
        days_remaining = (expiry_dt - ref_dt).days
        is_expired = days_remaining < 0

        return {
            "discovery_date": disc_dt.strftime("%Y-%m-%d"),
            "expiry_date": expiry_dt.strftime("%Y-%m-%d"),
            "reference_date": ref_dt.strftime("%Y-%m-%d"),
            "statute_years": STATUTE_LIMITATION_YEARS,
            "is_expired": is_expired,
            "days_remaining": max(0, days_remaining),
            "legal_basis": "Điều 588 BLDS 2015 (Thời hiệu khởi kiện yêu cầu bồi thường thiệt hại là 03 năm)",
            "admissibility_status": "EXPIRED_TIME_BARRED" if is_expired else "WITHIN_LIMITATION_PERIOD",
        }

    def add_party(
        self,
        case_id: str,
        party_role: str,
        full_name: str,
        national_id: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        economic_capacity_level: str = "AVERAGE",
        fault_percentage: float = 0.0,
        is_direct_tortfeasor: bool = True,
    ) -> Dict[str, Any]:
        """Add a litigant party (claimant, defendant, employer, guardian, insurer, dependent)."""
        pid = f"PT-{uuid.uuid4().hex[:8].upper()}"
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO case_parties (
                    party_id, case_id, party_role, full_name, national_id,
                    date_of_birth, phone, address, economic_capacity_level,
                    fault_percentage, is_direct_tortfeasor
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pid, case_id, party_role, full_name, national_id,
                    date_of_birth, phone, address, economic_capacity_level,
                    fault_percentage, 1 if is_direct_tortfeasor else 0,
                ),
            )
        return {
            "party_id": pid,
            "case_id": case_id,
            "party_role": party_role,
            "full_name": full_name,
            "national_id": national_id,
            "economic_capacity_level": economic_capacity_level,
            "fault_percentage": fault_percentage,
            "is_direct_tortfeasor": is_direct_tortfeasor,
        }

    # -------------------------------------------------------------------------
    # 2. STATUTORY DAMAGE CALCULATORS (ARTICLES 589 - 592 & NQ 02/2022)
    # -------------------------------------------------------------------------

    def calculate_health_damage(
        self,
        treatment_and_rehab_costs: float,
        lost_income_victim: float,
        caregiver_costs_and_lost_income: float,
        other_actual_expenses: float = 0.0,
        emotional_distress_agreed: Optional[float] = None,
        disability_percentage: float = 0.0,
        victim_fault_percentage: float = 0.0,
        defendant_economic_difficulty: bool = False,
        defendant_is_unintentional: bool = True,
    ) -> Dict[str, Any]:
        """Calculate damage caused by harm to health (Điều 590 BLDS 2015 & NQ 02/2022)."""
        actual_material_damage = (
            treatment_and_rehab_costs
            + lost_income_victim
            + caregiver_costs_and_lost_income
            + other_actual_expenses
        )

        statutory_cap_emotional = CAP_MONTHS_HEALTH_DAMAGE * BASE_SALARY_VND

        if emotional_distress_agreed is not None:
            emotional_distress = emotional_distress_agreed
            emotional_rule = "Thỏa thuận giữa các bên theo Điều 590.2 BLDS 2015"
        else:
            # If not agreed, calculate based on disability percentage up to 50 months base salary
            factor = min(1.0, max(0.2, disability_percentage / 100.0 if disability_percentage > 0 else 0.5))
            emotional_distress = statutory_cap_emotional * factor
            emotional_rule = f"Định lượng theo tỷ lệ thương tật ({disability_percentage}%) tối đa 50 tháng lương cơ sở (Đ.590.2)"

        total_gross_damage = actual_material_damage + emotional_distress

        # Apply Article 585.4 fault apportionment
        victim_fault_deduction = total_gross_damage * (victim_fault_percentage / 100.0)
        net_after_victim_fault = total_gross_damage - victim_fault_deduction

        # Apply Article 585.2 economic capacity reduction (lỗi vô ý & quá khả năng kinh tế)
        reduction_amount = 0.0
        reduction_rule = "Không áp dụng giảm trừ"
        if defendant_economic_difficulty and defendant_is_unintentional and victim_fault_percentage < 100.0:
            reduction_amount = net_after_victim_fault * 0.30  # Giảm 30% nếu vô ý & kinh tế quá khó khăn
            reduction_rule = "Điều 585.2 BLDS 2015 (Giảm mức bồi thường do lỗi vô ý và thiệt hại quá lớn so với khả năng kinh tế)"

        final_payable = max(0.0, net_after_victim_fault - reduction_amount)

        return {
            "damage_category": DamageCategory.HEALTH.value,
            "statutory_base_salary": BASE_SALARY_VND,
            "breakdown": {
                "treatment_and_rehab_costs": treatment_and_rehab_costs,
                "lost_income_victim": lost_income_victim,
                "caregiver_costs_and_lost_income": caregiver_costs_and_lost_income,
                "other_actual_expenses": other_actual_expenses,
                "total_material_damage": actual_material_damage,
                "emotional_distress": emotional_distress,
                "emotional_distress_cap": statutory_cap_emotional,
                "emotional_rule": emotional_rule,
            },
            "total_gross_damage": total_gross_damage,
            "victim_fault_percentage": victim_fault_percentage,
            "victim_fault_deduction": victim_fault_deduction,
            "net_after_victim_fault": net_after_victim_fault,
            "reduction_amount": reduction_amount,
            "reduction_rule": reduction_rule,
            "final_payable_compensation": final_payable,
            "legal_citations": [
                "Điều 584, 585, 590 Bộ luật Dân sự 2015",
                "Nghị quyết số 02/2022/NQ-HĐTP của Hội đồng Thẩm phán TANDTC",
                "Nghị định 73/2024/NĐ-CP (Mức lương cơ sở 2.340.000 VNĐ)",
            ],
        }

    def calculate_life_damage(
        self,
        pre_death_treatment_costs: float,
        reasonable_funeral_expenses: float,
        dependents: List[Dict[str, Any]],
        emotional_distress_agreed: Optional[float] = None,
        victim_fault_percentage: float = 0.0,
        defendant_economic_difficulty: bool = False,
        defendant_is_unintentional: bool = True,
    ) -> Dict[str, Any]:
        """Calculate damage caused by harm to life (Điều 591, 593 BLDS 2015 & NQ 02/2022)."""
        # Dependents calculation
        total_dependent_allowances = 0.0
        dependent_breakdowns = []

        for dep in dependents:
            dep_name = dep.get("full_name", "Thân nhân")
            rel = dep.get("relationship", "DEPENDENT")
            monthly = dep.get("monthly_allowance", BASE_SALARY_VND)
            # Duration in months (e.g., minor until 18, elderly parents estimated remaining life)
            duration_months = dep.get("duration_months", 120)
            total_dep = monthly * duration_months
            total_dependent_allowances += total_dep
            dependent_breakdowns.append({
                "full_name": dep_name,
                "relationship": rel,
                "monthly_allowance": monthly,
                "duration_months": duration_months,
                "total_allowance": total_dep,
                "rule": "Điều 591.1.c & Điều 593 BLDS 2015 (Nghĩa vụ cấp dưỡng cho người mà nạn nhân có nghĩa vụ cấp dưỡng)",
            })

        actual_material_damage = pre_death_treatment_costs + reasonable_funeral_expenses + total_dependent_allowances

        # Statutory cap on emotional distress: 100 months base salary (Điều 591.2)
        statutory_cap_emotional = CAP_MONTHS_LIFE_DAMAGE * BASE_SALARY_VND
        if emotional_distress_agreed is not None:
            emotional_distress = emotional_distress_agreed
            emotional_rule = "Thỏa thuận giữa các bên theo Điều 591.2 BLDS 2015"
        else:
            emotional_distress = statutory_cap_emotional
            emotional_rule = "Tối đa 100 lần mức lương cơ sở cho thân nhân thuộc hàng thừa kế thứ nhất (Đ.591.2 BLDS)"

        total_gross_damage = actual_material_damage + emotional_distress

        victim_fault_deduction = total_gross_damage * (victim_fault_percentage / 100.0)
        net_after_victim_fault = total_gross_damage - victim_fault_deduction

        reduction_amount = 0.0
        reduction_rule = "Không áp dụng giảm trừ"
        if defendant_economic_difficulty and defendant_is_unintentional and victim_fault_percentage < 100.0:
            reduction_amount = net_after_victim_fault * 0.25
            reduction_rule = "Điều 585.2 BLDS 2015 (Giảm trừ do lỗi vô ý và hoàn cảnh kinh tế đặc biệt khó khăn)"

        final_payable = max(0.0, net_after_victim_fault - reduction_amount)

        return {
            "damage_category": DamageCategory.LIFE.value,
            "statutory_base_salary": BASE_SALARY_VND,
            "breakdown": {
                "pre_death_treatment_costs": pre_death_treatment_costs,
                "reasonable_funeral_expenses": reasonable_funeral_expenses,
                "total_dependent_allowances": total_dependent_allowances,
                "dependents_detail": dependent_breakdowns,
                "total_material_damage": actual_material_damage,
                "emotional_distress": emotional_distress,
                "emotional_distress_cap": statutory_cap_emotional,
                "emotional_rule": emotional_rule,
            },
            "total_gross_damage": total_gross_damage,
            "victim_fault_percentage": victim_fault_percentage,
            "victim_fault_deduction": victim_fault_deduction,
            "net_after_victim_fault": net_after_victim_fault,
            "reduction_amount": reduction_amount,
            "reduction_rule": reduction_rule,
            "final_payable_compensation": final_payable,
            "legal_citations": [
                "Điều 584, 585, 591, 593 Bộ luật Dân sự 2015",
                "Nghị quyết số 02/2022/NQ-HĐTP của Hội đồng Thẩm phán TANDTC",
                "Nghị định 73/2024/NĐ-CP",
            ],
        }

    def calculate_property_damage(
        self,
        lost_or_destroyed_value: float,
        depreciation_or_repair_costs: float,
        lost_usufruct_and_earnings: float,
        mitigation_costs: float = 0.0,
        victim_fault_percentage: float = 0.0,
        defendant_economic_difficulty: bool = False,
        defendant_is_unintentional: bool = True,
    ) -> Dict[str, Any]:
        """Calculate damage caused by harm to property (Điều 589 BLDS 2015 & NQ 02/2022)."""
        actual_material_damage = (
            lost_or_destroyed_value
            + depreciation_or_repair_costs
            + lost_usufruct_and_earnings
            + mitigation_costs
        )

        total_gross_damage = actual_material_damage

        victim_fault_deduction = total_gross_damage * (victim_fault_percentage / 100.0)
        net_after_victim_fault = total_gross_damage - victim_fault_deduction

        reduction_amount = 0.0
        reduction_rule = "Không áp dụng giảm trừ"
        if defendant_economic_difficulty and defendant_is_unintentional and victim_fault_percentage < 100.0:
            reduction_amount = net_after_victim_fault * 0.35
            reduction_rule = "Điều 585.2 BLDS 2015 (Giảm bồi thường thiệt hại tài sản do lỗi vô ý và kinh tế khó khăn)"

        final_payable = max(0.0, net_after_victim_fault - reduction_amount)

        return {
            "damage_category": DamageCategory.PROPERTY.value,
            "breakdown": {
                "lost_or_destroyed_value": lost_or_destroyed_value,
                "depreciation_or_repair_costs": depreciation_or_repair_costs,
                "lost_usufruct_and_earnings": lost_usufruct_and_earnings,
                "mitigation_costs": mitigation_costs,
                "total_material_damage": actual_material_damage,
            },
            "total_gross_damage": total_gross_damage,
            "victim_fault_percentage": victim_fault_percentage,
            "victim_fault_deduction": victim_fault_deduction,
            "net_after_victim_fault": net_after_victim_fault,
            "reduction_amount": reduction_amount,
            "reduction_rule": reduction_rule,
            "final_payable_compensation": final_payable,
            "legal_citations": [
                "Điều 584, 585, 589 Bộ luật Dân sự 2015",
                "Nghị quyết số 02/2022/NQ-HĐTP của Hội đồng Thẩm phán TANDTC",
            ],
        }

    def calculate_reputation_honor_damage(
        self,
        remedy_and_rectification_costs: float,
        lost_or_reduced_income: float,
        other_actual_losses: float = 0.0,
        emotional_distress_agreed: Optional[float] = None,
        victim_fault_percentage: float = 0.0,
    ) -> Dict[str, Any]:
        """Calculate damage caused by infringement of honor, dignity, or reputation (Điều 592 BLDS 2015)."""
        actual_material_damage = remedy_and_rectification_costs + lost_or_reduced_income + other_actual_losses

        statutory_cap_emotional = CAP_MONTHS_REPUTATION_DAMAGE * BASE_SALARY_VND
        if emotional_distress_agreed is not None:
            emotional_distress = emotional_distress_agreed
            emotional_rule = "Thỏa thuận giữa các bên theo Điều 592.2 BLDS 2015"
        else:
            emotional_distress = statutory_cap_emotional
            emotional_rule = "Tối đa 10 lần mức lương cơ sở theo Điều 592.2 BLDS 2015"

        total_gross_damage = actual_material_damage + emotional_distress

        victim_fault_deduction = total_gross_damage * (victim_fault_percentage / 100.0)
        final_payable = max(0.0, total_gross_damage - victim_fault_deduction)

        return {
            "damage_category": DamageCategory.HONOR_REPUTATION.value,
            "statutory_base_salary": BASE_SALARY_VND,
            "breakdown": {
                "remedy_and_rectification_costs": remedy_and_rectification_costs,
                "lost_or_reduced_income": lost_or_reduced_income,
                "other_actual_losses": other_actual_losses,
                "total_material_damage": actual_material_damage,
                "emotional_distress": emotional_distress,
                "emotional_distress_cap": statutory_cap_emotional,
                "emotional_rule": emotional_rule,
            },
            "total_gross_damage": total_gross_damage,
            "victim_fault_percentage": victim_fault_percentage,
            "victim_fault_deduction": victim_fault_deduction,
            "final_payable_compensation": final_payable,
            "non_monetary_remedies": [
                "Buộc chấm dứt hành vi vi phạm (Điều 592 BLDS 2015)",
                "Buộc xin lỗi, cải chính công khai trên phương tiện thông tin đại chúng",
                "Gỡ bỏ thông tin sai sự thật trên nền tảng số / mạng xã hội",
            ],
            "legal_citations": [
                "Điều 34, 584, 585, 592 Bộ luật Dân sự 2015",
                "Nghị quyết số 02/2022/NQ-HĐTP của Hội đồng Thẩm phán TANDTC",
            ],
        }

    # -------------------------------------------------------------------------
    # 3. SPECIAL TORT LIABILITY DETERMINATION & RECOURSE (ARTICLES 596 - 605)
    # -------------------------------------------------------------------------

    def assess_special_liability(
        self,
        liability_type: str | LiabilityType,
        direct_tortfeasor_info: Dict[str, Any],
        responsible_party_info: Dict[str, Any],
        is_force_majeure: bool = False,
        is_victim_entirely_intentional: bool = False,
        is_unauthorized_possession: bool = False,
    ) -> Dict[str, Any]:
        """Assess special liability regime (Strict high-risk, vicarious legal entity, employer, minor, animals, trees)."""
        l_type = liability_type.value if isinstance(liability_type, LiabilityType) else liability_type

        is_exempt = False
        exemption_reason = ""
        primary_liable_party = responsible_party_info.get("full_name", "Bên chịu trách nhiệm")
        recourse_right = False
        recourse_explanation = ""

        if l_type == LiabilityType.HIGH_RISK_SOURCE.value:
            # Điều 601 BLDS 2015: Strict liability
            if is_victim_entirely_intentional:
                is_exempt = True
                exemption_reason = "Điều 601.3.a BLDS 2015 (Thiệt hại xảy ra hoàn toàn do lỗi cố ý của người bị thiệt hại)"
            elif is_force_majeure:
                is_exempt = True
                exemption_reason = "Điều 601.3.b BLDS 2015 (Thiệt hại xảy ra trong sự kiện bất khả kháng hoặc tình thế cấp thiết)"
            elif is_unauthorized_possession:
                primary_liable_party = direct_tortfeasor_info.get("full_name", "Người chiếm hữu trái pháp luật")
                exemption_reason = "Điều 601.4 BLDS 2015 (Người chiếm hữu, sử dụng trái pháp luật nguồn nguy hiểm cao độ phải bồi thường)"

            rule = "Điều 601 BLDS 2015 (Bồi thường thiệt hại do nguồn nguy hiểm cao độ gây ra - Trách nhiệm nghiêm ngặt)"

        elif l_type == LiabilityType.LEGAL_ENTITY.value:
            # Điều 597 BLDS 2015: Pháp nhân bồi thường, sau đó hoàn trả
            primary_liable_party = responsible_party_info.get("full_name", "Pháp nhân")
            recourse_right = True
            recourse_explanation = "Điều 597 BLDS 2015 (Pháp nhân có quyền yêu cầu người có lỗi hoàn trả khoản tiền đã bồi thường)"
            rule = "Điều 597 BLDS 2015 (Bồi thường thiệt hại do người của pháp nhân gây ra)"

        elif l_type == LiabilityType.EMPLOYER_APPRENTICE.value:
            # Điều 600 BLDS 2015: Người thuê mướn bồi thường, sau đó hoàn trả
            primary_liable_party = responsible_party_info.get("full_name", "Người sử dụng lao động")
            recourse_right = True
            recourse_explanation = "Điều 600 BLDS 2015 (Người sử dụng lao động có quyền yêu cầu người làm công/học nghề hoàn trả)"
            rule = "Điều 600 BLDS 2015 (Bồi thường thiệt hại do người làm công, người học nghề gây ra)"

        elif l_type == LiabilityType.MINOR_UNDER_15.value:
            # Điều 586.2 & Điều 599: Cha mẹ bồi thường toàn bộ (hoặc trường học/bệnh viện nếu trong thời gian quản lý)
            primary_liable_party = responsible_party_info.get("full_name", "Cha mẹ / Trường học / Bệnh viện")
            rule = "Điều 586.2, Điều 599 BLDS 2015 (Năng lực bồi thường của người dưới 15 tuổi)"

        elif l_type == LiabilityType.MINOR_15_TO_18.value:
            # Điều 586.2: Người từ 15 đến 18 bồi thường bằng tài sản riêng, cha mẹ bồi thường phần còn thiếu
            primary_liable_party = direct_tortfeasor_info.get("full_name", "Người từ đủ 15 đến dưới 18 tuổi")
            recourse_explanation = "Cha mẹ bồi thường phần còn thiếu nếu tài sản riêng của con không đủ (Điều 586.2)"
            rule = "Điều 586.2 BLDS 2015 (Năng lực bồi thường của người từ đủ 15 tuổi đến dưới 18 tuổi)"

        elif l_type == LiabilityType.ANIMAL_DAMAGE.value:
            # Điều 603: Chủ sở hữu súc vật bồi thường
            if is_victim_entirely_intentional:
                is_exempt = True
                exemption_reason = "Điều 603.1 BLDS 2015 (Người bị thiệt hại hoàn toàn có lỗi trong việc làm súc vật gây thiệt hại)"
            rule = "Điều 603 BLDS 2015 (Bồi thường thiệt hại do súc vật gây ra)"

        elif l_type == LiabilityType.TREE_DAMAGE.value:
            # Điều 604: Chủ sở hữu cây cối bồi thường
            if is_force_majeure:
                is_exempt = True
                exemption_reason = "Điều 604 BLDS 2015 (Sự kiện bất khả kháng như bão lũ bất thường vượt quá sức chịu đựng)"
            rule = "Điều 604 BLDS 2015 (Bồi thường thiệt hại do cây cối gây ra)"

        elif l_type == LiabilityType.CONSTRUCTION_DAMAGE.value:
            # Điều 605: Chủ sở hữu công trình xây dựng bồi thường
            rule = "Điều 605 BLDS 2015 (Bồi thường thiệt hại do nhà cửa, công trình xây dựng khác gây ra)"

        else:
            rule = "Điều 584 BLDS 2015 (Căn cứ phát sinh trách nhiệm bồi thường thiệt hại do lỗi)"

        return {
            "liability_type": l_type,
            "primary_liable_party": primary_liable_party,
            "is_exempt_from_liability": is_exempt,
            "exemption_reason": exemption_reason,
            "recourse_right_available": recourse_right,
            "recourse_explanation": recourse_explanation,
            "governing_rule": rule,
        }

    # -------------------------------------------------------------------------
    # 4. OUT-OF-COURT SETTLEMENT AGREEMENT (THỎA THUẬN HÒA GIẢI)
    # -------------------------------------------------------------------------

    def create_settlement_agreement(
        self,
        case_id: str,
        total_agreed_amount: float,
        payment_terms: str,
        conciliator_name: Optional[str] = None,
        is_court_recognized: bool = False,
    ) -> Dict[str, Any]:
        """Record an out-of-court dispute settlement agreement (Biên bản hòa giải thành)."""
        sid = f"SA-{uuid.uuid4().hex[:8].upper()}"
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO settlements (
                    settlement_id, case_id, settlement_date, total_agreed_amount,
                    payment_terms, is_court_recognized, conciliator_name, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sid, case_id, now_str, total_agreed_amount,
                    payment_terms, 1 if is_court_recognized else 0,
                    conciliator_name, "AGREED",
                ),
            )
            conn.execute(
                "UPDATE tort_cases SET status = ?, updated_at = ? WHERE case_id = ?",
                (CaseStatus.SETTLED.value, now_str, case_id),
            )

        return {
            "settlement_id": sid,
            "case_id": case_id,
            "settlement_date": now_str,
            "total_agreed_amount": total_agreed_amount,
            "payment_terms": payment_terms,
            "conciliator_name": conciliator_name,
            "is_court_recognized": is_court_recognized,
            "status": "AGREED",
            "enforceability_note": (
                "Văn bản hòa giải có giá trị bắt buộc thi hành; có thể yêu cầu Tòa án công nhận kết quả hòa giải thành ngoài Tòa án theo Chương XXXIII Bộ luật Tố tụng Dân sự 2015"
            ),
        }

    # -------------------------------------------------------------------------
    # 5. COMPREHENSIVE DOSSIER & COMPLIANCE AUDIT
    # -------------------------------------------------------------------------

    def generate_assessment_dossier(self, case_id: str) -> Dict[str, Any]:
        """Generate a complete legal assessment dossier with claim verification and statutory citations."""
        with self._get_connection() as conn:
            c_row = conn.execute("SELECT * FROM tort_cases WHERE case_id = ?", (case_id,)).fetchone()
            if not c_row:
                raise ValueError(f"Tort case '{case_id}' not found.")

            case_dict = dict(c_row)
            parties = [dict(r) for r in conn.execute("SELECT * FROM case_parties WHERE case_id = ?", (case_id,)).fetchall()]
            settlements = [dict(r) for r in conn.execute("SELECT * FROM settlements WHERE case_id = ?", (case_id,)).fetchall()]

        # Re-evaluate statute of limitations
        limitation_info = self.check_statute_of_limitations(case_dict["discovery_date"])

        return {
            "dossier_id": f"DOSSIER-{case_id}",
            "case_summary": case_dict,
            "parties": parties,
            "settlements": settlements,
            "statute_of_limitations": limitation_info,
            "statutory_parameters": {
                "base_salary_vnd": BASE_SALARY_VND,
                "decree_reference": "Nghị định số 73/2024/NĐ-CP",
                "health_distress_cap_vnd": CAP_MONTHS_HEALTH_DAMAGE * BASE_SALARY_VND,
                "life_distress_cap_vnd": CAP_MONTHS_LIFE_DAMAGE * BASE_SALARY_VND,
                "reputation_distress_cap_vnd": CAP_MONTHS_REPUTATION_DAMAGE * BASE_SALARY_VND,
            },
            "compliance_rating": "EXCELLENT" if not limitation_info["is_expired"] else "TIME_BARRED",
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
