"""
Autonomous Vietnamese Maritime Court, Admiralty Jurisdiction, Vessel Arrest, Maritime Liens & General Average Suite.
Statutory Framework:
- Bộ luật Hàng hải Việt Nam 2015 (Luật số 95/2015/QH13)
- Pháp lệnh Thủ tục bắt giữ tàu biển 2008 (Pháp lệnh số 05/2008/PL-UBTVQH12)
- Quy tắc York-Antwerp 2016 (YAR 2016) về Phân bổ Tổn thất chung (General Average)
- Quy tắc quốc tế phòng ngừa đâm va tàu thuyền trên biển (COLREGS 1972)
- Công ước quốc tế về cứu hộ hàng hải 1989 (London Salvage Convention 1989)

Strict Standard Library Only: Zero external HTTP, zero vendor SDKs.
"""

from __future__ import annotations

import os
import json
import sqlite3
import datetime
import uuid
import math
from typing import Dict, Any, List, Optional

# Căn cứ Khoản 1 Điều 11 Pháp lệnh số 05/2008/PL-UBTVQH12 & Điều 41 Bộ luật Hàng hải 2015
MARITIME_CLAIM_TYPES = {
    "CREW_WAGES": "Tiền lương, chi phí hồi hương, tiền đóng BHXH của thuyền viên (Điều 41.1)",
    "PERSONAL_INJURY": "Bồi thường tổn thất tính mạng, thương tích của thuyền viên hoặc hành khách (Điều 41.2)",
    "SALVAGE_REWARD": "Tiền công cứu hộ hàng hải và bồi hoàn đặc biệt (Điều 41.3 & Điều 292)",
    "PORT_NAVIGATION_DUES": "Phí luồng hàng hải, hoa tiêu, cầu bến neo đậu và phí cảng biển (Điều 41.4)",
    "COLLISION_DAMAGE": "Tổn thất vật chất trực tiếp do đâm va hoặc tai nạn hàng hải (Điều 41.5 & Điều 286)",
    "CARGO_DAMAGE": "Mất mát, hư hỏng hàng hóa hoặc hành lý vận chuyển theo vận đơn (Điều 11.e Pháp lệnh 05/2008)",
    "CHARTER_DISPUTE": "Tranh chấp hợp đồng thuê tàu định hạn, thuê tàu chuyến hoặc thuê tàu trần (Điều 11.c Pháp lệnh 05/2008)",
    "GENERAL_AVERAGE_CONTRIBUTION": "Đóng góp tổn thất chung của chủ tàu, chủ hàng (Điều 11.g Pháp lệnh 05/2008 & Điều 300)",
}

# Thứ tự ưu tiên Quyền cầm giữ hàng hải (Maritime Liens) theo Khoản 1 Điều 41 Bộ luật Hàng hải 2015
MARITIME_LIEN_PRIORITY = {
    "CREW_WAGES": 1,
    "PERSONAL_INJURY": 2,
    "SALVAGE_REWARD": 3,
    "PORT_NAVIGATION_DUES": 4,
    "COLLISION_DAMAGE": 5,
}

VESSEL_TYPES = {
    "CONTAINER": "Tàu chuyên dụng chở container bách hóa",
    "BULK_CARRIER": "Tàu hàng rời chuyên chở quặng, than đá, ngũ cốc",
    "OIL_TANKER": "Tàu chở dầu thô và sản phẩm dầu mỏ lỏng",
    "CHEMICAL_GAS_CARRIER": "Tàu chở hóa chất lỏng hoặc khí hóa lỏng (LPG/LNG)",
    "GENERAL_CARGO": "Tàu chở hàng bách hóa tổng hợp",
}


class AdmiraltyEngine:
    """Core engine for Vietnamese Admiralty Jurisdiction, Vessel Arrest, Maritime Liens & General Average."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            db_path = os.path.join(base_dir, "admiralty.db")
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
                CREATE TABLE IF NOT EXISTS vessels (
                    vessel_id TEXT PRIMARY KEY,
                    imo_number TEXT UNIQUE NOT NULL,
                    vessel_name TEXT NOT NULL,
                    flag_state TEXT NOT NULL,
                    gross_tonnage REAL NOT NULL,
                    deadweight_dwt REAL NOT NULL,
                    vessel_type TEXT NOT NULL,
                    registered_owner TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vessel_arrests (
                    arrest_id TEXT PRIMARY KEY,
                    vessel_imo TEXT NOT NULL,
                    vessel_name TEXT NOT NULL,
                    applicant_name TEXT NOT NULL,
                    claim_type TEXT NOT NULL,
                    claim_amount_usd REAL NOT NULL,
                    counter_security_usd REAL NOT NULL,
                    counter_security_ratio_pct REAL NOT NULL,
                    court_name TEXT NOT NULL,
                    port_location TEXT NOT NULL,
                    is_counter_security_sufficient INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS maritime_liens (
                    lien_id TEXT PRIMARY KEY,
                    vessel_imo TEXT NOT NULL,
                    claimant_name TEXT NOT NULL,
                    lien_category TEXT NOT NULL,
                    priority_rank INTEGER NOT NULL,
                    claim_amount_usd REAL NOT NULL,
                    incident_date TEXT NOT NULL,
                    days_elapsed INTEGER NOT NULL,
                    is_time_barred INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collision_assessments (
                    collision_id TEXT PRIMARY KEY,
                    vessel_a_imo TEXT NOT NULL,
                    vessel_b_imo TEXT NOT NULL,
                    collision_date TEXT NOT NULL,
                    colregs_violation TEXT NOT NULL,
                    fault_ratio_a_pct REAL NOT NULL,
                    fault_ratio_b_pct REAL NOT NULL,
                    damage_vessel_a_usd REAL NOT NULL,
                    damage_vessel_b_usd REAL NOT NULL,
                    liability_a_usd REAL NOT NULL,
                    liability_b_usd REAL NOT NULL,
                    net_settlement_payer TEXT NOT NULL,
                    net_settlement_usd REAL NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS general_average_adjustments (
                    ga_id TEXT PRIMARY KEY,
                    vessel_imo TEXT NOT NULL,
                    incident_date TEXT NOT NULL,
                    ga_sacrifice_usd REAL NOT NULL,
                    ga_expenditure_usd REAL NOT NULL,
                    total_ga_loss_usd REAL NOT NULL,
                    vessel_value_usd REAL NOT NULL,
                    cargo_value_usd REAL NOT NULL,
                    freight_value_usd REAL NOT NULL,
                    total_contributory_value_usd REAL NOT NULL,
                    ga_contribution_rate_pct REAL NOT NULL,
                    vessel_contribution_usd REAL NOT NULL,
                    cargo_contribution_usd REAL NOT NULL,
                    freight_contribution_usd REAL NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def register_vessel(
        self,
        imo_number: str,
        vessel_name: str,
        flag_state: str = "VIETNAM",
        gross_tonnage: float = 12500.0,
        deadweight_dwt: float = 18000.0,
        vessel_type: str = "CONTAINER",
        registered_owner: str = "Tổng công ty Hàng hải Việt Nam (VIMC)",
    ) -> Dict[str, Any]:
        """
        Register a commercial vessel into Admiralty Registry under Chapter II Vietnam Maritime Code 2015.
        Validates IMO number format and tonnage invariants.
        """
        vessel_id = f"VES-{uuid.uuid4().hex[:8].upper()}"
        imo_clean = imo_number.strip().upper().replace("IMO", "").replace(" ", "").replace("-", "")
        type_upper = vessel_type.strip().upper()
        violations = []

        if not imo_clean.isdigit() or len(imo_clean) != 7:
            violations.append(f"Mã số IMO không hợp chuẩn: Phải bao gồm đúng 7 chữ số (nhận được: {imo_number})")

        if not vessel_name.strip():
            violations.append("Thiếu tên đăng ký của tàu biển")

        if gross_tonnage <= 0 or deadweight_dwt <= 0:
            violations.append("Dung tích toàn phần (GT) và trọng tải toàn phần (DWT) phải lớn hơn 0")

        if type_upper not in VESSEL_TYPES:
            violations.append(f"Loại tàu biển không hợp lệ: {', '.join(VESSEL_TYPES.keys())}")

        is_valid = len(violations) == 0
        status = "VESSEL_REGISTERED" if is_valid else "REGISTRATION_DEFICIENT"
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        if is_valid:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO vessels (
                        vessel_id, imo_number, vessel_name, flag_state,
                        gross_tonnage, deadweight_dwt, vessel_type, registered_owner, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    vessel_id, f"IMO{imo_clean}", vessel_name.strip(), flag_state.strip().upper(),
                    gross_tonnage, deadweight_dwt, type_upper, registered_owner.strip(), created_at
                ))
                conn.commit()

        return {
            "vessel_id": vessel_id,
            "imo_number": f"IMO{imo_clean}" if imo_clean.isdigit() and len(imo_clean) == 7 else imo_number,
            "vessel_name": vessel_name,
            "flag_state": flag_state.upper(),
            "gross_tonnage": gross_tonnage,
            "deadweight_dwt": deadweight_dwt,
            "vessel_type": type_upper,
            "vessel_type_description": VESSEL_TYPES.get(type_upper, type_upper),
            "registered_owner": registered_owner,
            "is_valid": is_valid,
            "status": status,
            "violations": violations,
            "created_at": created_at,
        }

    def petition_vessel_arrest(
        self,
        vessel_imo: str,
        applicant_name: str,
        claim_type: str = "CREW_WAGES",
        claim_amount_usd: float = 120000.0,
        counter_security_usd: float = 24000.0,
        court_name: str = "Tòa án nhân dân Thành phố Hải Phòng",
        port_location: str = "Khu bến cảng Lạch Huyện",
    ) -> Dict[str, Any]:
        """
        Record petition for vessel arrest under Ordinance 05/2008/PL-UBTVQH12.
        Enforces Article 14 mandatory financial counter-security:
        Applicant must provide security deposit or bank guarantee of at least 15% of claim value
        to cover potential damages in case of wrongful arrest.
        """
        arrest_id = f"ARR-{uuid.uuid4().hex[:8].upper()}"
        claim_upper = claim_type.strip().upper()
        violations = []

        if claim_upper not in MARITIME_CLAIM_TYPES:
            violations.append(f"Loại khiếu nại hàng hải không thuộc thẩm quyền bắt giữ tàu biển: {', '.join(MARITIME_CLAIM_TYPES.keys())}")

        if claim_amount_usd <= 0:
            violations.append("Giá trị khiếu nại hàng hải phải lớn hơn 0 USD")

        if not applicant_name.strip():
            violations.append("Thiếu tên người yêu cầu bắt giữ tàu biển")

        # Statutory Counter-Security requirement under Ordinance 05/2008 Art 14:
        # Minimum 15% of claim value required as counter-security
        counter_ratio = round((counter_security_usd / claim_amount_usd) * 100.0, 2) if claim_amount_usd > 0 else 0.0
        is_counter_security_sufficient = counter_ratio >= 15.0

        if not is_counter_security_sufficient:
            violations.append(
                f"Biện pháp bảo đảm tài chính không đủ điều kiện thụ lý: {counter_security_usd:,.0f} USD ({counter_ratio}%) "
                f"< tối thiểu 15% giá trị khiếu nại ({claim_amount_usd * 0.15:,.0f} USD) "
                f"theo Điều 14 Pháp lệnh Bắt giữ tàu biển 2008"
            )

        is_warrant_granted = len(violations) == 0
        status = "ARREST_WARRANT_ISSUED" if is_warrant_granted else "ARREST_PETITION_REJECTED"
        statutory_notes = (
            f"TAND ban hành Quyết định bắt giữ tàu biển để bảo đảm giải quyết khiếu nại hàng hải; "
            f"thời hạn bắt giữ tối đa 30 ngày theo Điều 15 Pháp lệnh 05/2008; "
            f"đã ký quỹ bảo đảm tài chính {counter_security_usd:,.0f} USD ({counter_ratio}%)."
            if is_warrant_granted
            else "; ".join(violations)
        )
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Find vessel name if registered
        vessel_name = "Tàu biển đang neo đậu"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT vessel_name FROM vessels WHERE imo_number = ?", (vessel_imo.strip(),))
            row = cursor.fetchone()
            if row:
                vessel_name = row["vessel_name"]

            cursor.execute("""
                INSERT INTO vessel_arrests (
                    arrest_id, vessel_imo, vessel_name, applicant_name,
                    claim_type, claim_amount_usd, counter_security_usd,
                    counter_security_ratio_pct, court_name, port_location,
                    is_counter_security_sufficient, status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                arrest_id, vessel_imo.strip(), vessel_name, applicant_name.strip(),
                claim_upper, claim_amount_usd, counter_security_usd,
                counter_ratio, court_name.strip(), port_location.strip(),
                1 if is_counter_security_sufficient else 0, status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "arrest_id": arrest_id,
            "vessel_imo": vessel_imo,
            "vessel_name": vessel_name,
            "applicant_name": applicant_name,
            "claim_type": claim_upper,
            "claim_type_description": MARITIME_CLAIM_TYPES.get(claim_upper, claim_upper),
            "claim_amount_usd": claim_amount_usd,
            "counter_security_usd": counter_security_usd,
            "counter_security_ratio_pct": counter_ratio,
            "is_counter_security_sufficient": is_counter_security_sufficient,
            "court_name": court_name,
            "port_location": port_location,
            "status": status,
            "is_warrant_granted": is_warrant_granted,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def evaluate_maritime_lien(
        self,
        vessel_imo: str,
        claimant_name: str,
        lien_category: str = "CREW_WAGES",
        claim_amount_usd: float = 45000.0,
        incident_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate and rank statutory Maritime Lien (Quyền cầm giữ hàng hải) under Article 41 Vietnam Maritime Code 2015.
        Validates priority tier (Rank 1 to 5) and 1-year statutory limitation period (Thời hiệu 01 năm theo Điều 42).
        Maritime liens take precedence over ship mortgages!
        """
        lien_id = f"MLN-{uuid.uuid4().hex[:8].upper()}"
        cat_upper = lien_category.strip().upper()
        violations = []

        if cat_upper not in MARITIME_LIEN_PRIORITY:
            violations.append(f"Danh mục khiếu nại không được hưởng quyền cầm giữ hàng hải luật định: {', '.join(MARITIME_LIEN_PRIORITY.keys())}")

        if claim_amount_usd <= 0:
            violations.append("Giá trị quyền cầm giữ hàng hải phải lớn hơn 0 USD")

        priority_rank = MARITIME_LIEN_PRIORITY.get(cat_upper, 99)

        # 1-year limitation period check under Article 42
        now = datetime.datetime.now(datetime.timezone.utc)
        if incident_date:
            try:
                dt_incident = datetime.datetime.fromisoformat(incident_date)
                if dt_incident.tzinfo is None:
                    dt_incident = dt_incident.replace(tzinfo=datetime.timezone.utc)
                days_elapsed = (now - dt_incident).days
            except Exception:
                days_elapsed = 30
                incident_date = now.strftime("%Y-%m-%d")
        else:
            days_elapsed = 30
            incident_date = now.strftime("%Y-%m-%d")

        # Statutory limitation period under Article 42: 01 year (365 days)
        is_time_barred = days_elapsed > 365
        if is_time_barred:
            violations.append(
                f"Quyền cầm giữ hàng hải đã hết thời hiệu khởi kiện ({days_elapsed} ngày) "
                f"> 01 năm (365 ngày) theo quy định tại Điều 42 Bộ luật Hàng hải 2015"
            )

        is_valid = len(violations) == 0
        status = "LIEN_ENFORCEABLE_VALID" if is_valid else "LIEN_EXTINGUISHED_OR_INVALID"
        statutory_notes = (
            f"Quyền cầm giữ hàng hải hợp chuẩn Điều 41 Bộ luật Hàng hải 2015; "
            f"Hạng ưu tiên thanh toán: BẬC {priority_rank} (Ưu tiên thanh toán trước thế chấp tàu biển); "
            f"Thời hiệu còn hiệu lực: {365 - days_elapsed} ngày."
            if is_valid
            else "; ".join(violations)
        )
        created_at = now.isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO maritime_liens (
                    lien_id, vessel_imo, claimant_name, lien_category,
                    priority_rank, claim_amount_usd, incident_date,
                    days_elapsed, is_time_barred, status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lien_id, vessel_imo.strip(), claimant_name.strip(), cat_upper,
                priority_rank, claim_amount_usd, incident_date,
                days_elapsed, 1 if is_time_barred else 0, status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "lien_id": lien_id,
            "vessel_imo": vessel_imo,
            "claimant_name": claimant_name,
            "lien_category": cat_upper,
            "lien_category_description": MARITIME_CLAIM_TYPES.get(cat_upper, cat_upper),
            "priority_rank": priority_rank,
            "claim_amount_usd": claim_amount_usd,
            "incident_date": incident_date,
            "days_elapsed": days_elapsed,
            "is_time_barred": is_time_barred,
            "is_valid": is_valid,
            "status": status,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def apportion_collision_liability(
        self,
        vessel_a_imo: str,
        vessel_b_imo: str,
        collision_date: str,
        colregs_violation: str = "RULE_15_CROSSING_GIVE_WAY_FAILED",
        fault_ratio_a_pct: float = 70.0,
        damage_vessel_a_usd: float = 250000.0,
        damage_vessel_b_usd: float = 600000.0,
    ) -> Dict[str, Any]:
        """
        Apportion collision liability and calculate net damages settlement under Chapter X (Articles 286-291)
        Vietnam Maritime Code 2015 & COLREGS 1972.
        - Article 288: Fault apportionment liability principle:
          Each ship pays damages in proportion to its degree of fault.
          Total damages = Damage A + Damage B.
          Liability A = Total damages * Fault Ratio A.
          Liability B = Total damages * Fault Ratio B.
          Net settlement = Absolute difference between actual damage and apportioned liability.
        """
        collision_id = f"COL-{uuid.uuid4().hex[:8].upper()}"
        violations = []

        if fault_ratio_a_pct < 0.0 or fault_ratio_a_pct > 100.0:
            violations.append("Tỷ lệ lỗi của tàu A phải nằm trong khoảng từ 0.0% đến 100.0%")

        fault_ratio_b_pct = round(100.0 - fault_ratio_a_pct, 2)
        total_damages_usd = damage_vessel_a_usd + damage_vessel_b_usd

        # Apportioned liabilities under Article 288
        liability_a_usd = round(total_damages_usd * (fault_ratio_a_pct / 100.0), 2)
        liability_b_usd = round(total_damages_usd * (fault_ratio_b_pct / 100.0), 2)

        # Net payment calculation
        # Vessel A suffered damage_a, owes liability_a.
        # Net balance A = liability_a - damage_a
        # If liability_a > damage_a, Vessel A must pay (liability_a - damage_a) to Vessel B.
        net_diff = liability_a_usd - damage_vessel_a_usd
        if net_diff > 0:
            net_settlement_payer = f"VESSEL_A ({vessel_a_imo})"
            net_settlement_usd = round(net_diff, 2)
        elif net_diff < 0:
            net_settlement_payer = f"VESSEL_B ({vessel_b_imo})"
            net_settlement_usd = round(abs(net_diff), 2)
        else:
            net_settlement_payer = "NONE_BALANCED"
            net_settlement_usd = 0.0

        is_valid = len(violations) == 0
        status = "COLLISION_SETTLEMENT_ADOPTED" if is_valid else "COLLISION_APPORTIONMENT_INVALID"
        statutory_notes = (
            f"Phân định trách nhiệm đâm va theo Điều 288 Bộ luật Hàng hải 2015 & COLREGS 1972 ({colregs_violation}); "
            f"Tỷ lệ lỗi: Tàu A ({fault_ratio_a_pct}%) vs Tàu B ({fault_ratio_b_pct}%); "
            f"Tổng thiệt hại: {total_damages_usd:,.0f} USD; Bên bồi thường ròng: {net_settlement_payer} ({net_settlement_usd:,.0f} USD)."
            if is_valid
            else "; ".join(violations)
        )
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO collision_assessments (
                    collision_id, vessel_a_imo, vessel_b_imo, collision_date,
                    colregs_violation, fault_ratio_a_pct, fault_ratio_b_pct,
                    damage_vessel_a_usd, damage_vessel_b_usd, liability_a_usd,
                    liability_b_usd, net_settlement_payer, net_settlement_usd,
                    status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                collision_id, vessel_a_imo.strip(), vessel_b_imo.strip(), collision_date.strip(),
                colregs_violation.strip(), fault_ratio_a_pct, fault_ratio_b_pct,
                damage_vessel_a_usd, damage_vessel_b_usd, liability_a_usd,
                liability_b_usd, net_settlement_payer, net_settlement_usd,
                status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "collision_id": collision_id,
            "vessel_a_imo": vessel_a_imo,
            "vessel_b_imo": vessel_b_imo,
            "collision_date": collision_date,
            "colregs_violation": colregs_violation,
            "fault_ratio_a_pct": fault_ratio_a_pct,
            "fault_ratio_b_pct": fault_ratio_b_pct,
            "damage_vessel_a_usd": damage_vessel_a_usd,
            "damage_vessel_b_usd": damage_vessel_b_usd,
            "total_damages_usd": total_damages_usd,
            "liability_a_usd": liability_a_usd,
            "liability_b_usd": liability_b_usd,
            "net_settlement_payer": net_settlement_payer,
            "net_settlement_usd": net_settlement_usd,
            "is_valid": is_valid,
            "status": status,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def adjust_general_average(
        self,
        vessel_imo: str,
        incident_date: str,
        ga_sacrifice_usd: float = 300000.0,
        ga_expenditure_usd: float = 150000.0,
        vessel_value_usd: float = 12000000.0,
        cargo_value_usd: float = 16000000.0,
        freight_value_usd: float = 2000000.0,
    ) -> Dict[str, Any]:
        """
        Adjust General Average (Tổn thất chung) under Chapter XII (Articles 300-307)
        Vietnam Maritime Code 2015 & York-Antwerp Rules 2016 (YAR 2016).
        Calculates:
        - Total GA Loss = GA Sacrifice + GA Expenditure.
        - Total Contributory Value = Vessel Value + Cargo Value + Freight at risk.
        - GA Contribution Rate % = (Total GA Loss / Total Contributory Value) * 100%.
        - Proportionate contributions of Vessel, Cargo, and Freight.
        """
        ga_id = f"GAV-{uuid.uuid4().hex[:8].upper()}"
        violations = []

        total_ga_loss_usd = ga_sacrifice_usd + ga_expenditure_usd
        total_contributory_value_usd = vessel_value_usd + cargo_value_usd + freight_value_usd

        if total_ga_loss_usd <= 0:
            violations.append("Tổng tổn thất và chi phí tổn thất chung (GA Loss) phải lớn hơn 0 USD")

        if total_contributory_value_usd <= 0:
            violations.append("Tổng giá trị chịu phân bổ tổn thất chung (Contributory Value) phải lớn hơn 0 USD")

        if total_contributory_value_usd > 0:
            ga_rate_pct = round((total_ga_loss_usd / total_contributory_value_usd) * 100.0, 4)
        else:
            ga_rate_pct = 0.0

        vessel_contribution_usd = round(vessel_value_usd * (ga_rate_pct / 100.0), 2)
        cargo_contribution_usd = round(cargo_value_usd * (ga_rate_pct / 100.0), 2)
        freight_contribution_usd = round(freight_value_usd * (ga_rate_pct / 100.0), 2)

        is_valid = len(violations) == 0
        status = "GENERAL_AVERAGE_ADJUSTED" if is_valid else "GA_ADJUSTMENT_INVALID"
        statutory_notes = (
            f"Bản tính toán phân bổ tổn thất chung hợp chuẩn Điều 300-307 Bộ luật Hàng hải & YAR 2016; "
            f"Tỷ lệ đóng góp TTC: {ga_rate_pct}%; "
            f"Tàu biển đóng góp: {vessel_contribution_usd:,.0f} USD; "
            f"Chủ hàng đóng góp: {cargo_contribution_usd:,.0f} USD; "
            f"Cước phí đóng góp: {freight_contribution_usd:,.0f} USD."
            if is_valid
            else "; ".join(violations)
        )
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO general_average_adjustments (
                    ga_id, vessel_imo, incident_date, ga_sacrifice_usd,
                    ga_expenditure_usd, total_ga_loss_usd, vessel_value_usd,
                    cargo_value_usd, freight_value_usd, total_contributory_value_usd,
                    ga_contribution_rate_pct, vessel_contribution_usd,
                    cargo_contribution_usd, freight_contribution_usd,
                    status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ga_id, vessel_imo.strip(), incident_date.strip(), ga_sacrifice_usd,
                ga_expenditure_usd, total_ga_loss_usd, vessel_value_usd,
                cargo_value_usd, freight_value_usd, total_contributory_value_usd,
                ga_rate_pct, vessel_contribution_usd, cargo_contribution_usd, freight_contribution_usd,
                status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "ga_id": ga_id,
            "vessel_imo": vessel_imo,
            "incident_date": incident_date,
            "ga_sacrifice_usd": ga_sacrifice_usd,
            "ga_expenditure_usd": ga_expenditure_usd,
            "total_ga_loss_usd": total_ga_loss_usd,
            "vessel_value_usd": vessel_value_usd,
            "cargo_value_usd": cargo_value_usd,
            "freight_value_usd": freight_value_usd,
            "total_contributory_value_usd": total_contributory_value_usd,
            "ga_contribution_rate_pct": ga_rate_pct,
            "vessel_contribution_usd": vessel_contribution_usd,
            "cargo_contribution_usd": cargo_contribution_usd,
            "freight_contribution_usd": freight_contribution_usd,
            "is_valid": is_valid,
            "status": status,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def list_admiralty_records(self, category: str = "ALL", limit: int = 50) -> Dict[str, Any]:
        """List registered vessels, vessel arrest warrants, maritime liens, collision assessments, and GA adjustments."""
        cat_upper = category.strip().upper()
        results: Dict[str, Any] = {}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            if cat_upper in ["ALL", "VESSELS"]:
                cursor.execute("SELECT * FROM vessels ORDER BY created_at DESC LIMIT ?", (limit,))
                results["vessels"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "ARRESTS"]:
                cursor.execute("SELECT * FROM vessel_arrests ORDER BY created_at DESC LIMIT ?", (limit,))
                results["vessel_arrests"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "LIENS"]:
                cursor.execute("SELECT * FROM maritime_liens ORDER BY priority_rank ASC, created_at DESC LIMIT ?", (limit,))
                results["maritime_liens"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "COLLISIONS"]:
                cursor.execute("SELECT * FROM collision_assessments ORDER BY created_at DESC LIMIT ?", (limit,))
                results["collision_assessments"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "GA", "GENERAL_AVERAGE"]:
                cursor.execute("SELECT * FROM general_average_adjustments ORDER BY created_at DESC LIMIT ?", (limit,))
                results["general_average_adjustments"] = [dict(row) for row in cursor.fetchall()]

        return results

    def get_admiralty_telemetry(self) -> Dict[str, Any]:
        """Aggregate national admiralty jurisdiction, maritime arrest, and maritime claims telemetry."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(gross_tonnage), SUM(deadweight_dwt) FROM vessels")
            v_row = cursor.fetchone()
            total_vessels = v_row[0] or 0
            total_gross_tonnage = v_row[1] or 0.0
            total_deadweight_dwt = v_row[2] or 0.0

            cursor.execute("""
                SELECT COUNT(*),
                       SUM(claim_amount_usd),
                       SUM(counter_security_usd),
                       SUM(CASE WHEN is_counter_security_sufficient = 1 THEN 1 ELSE 0 END)
                FROM vessel_arrests
            """)
            a_row = cursor.fetchone()
            total_arrest_petitions = a_row[0] or 0
            total_arrest_claims_usd = a_row[1] or 0.0
            total_counter_security_usd = a_row[2] or 0.0
            warrants_granted = a_row[3] or 0

            cursor.execute("""
                SELECT COUNT(*),
                       SUM(claim_amount_usd),
                       SUM(CASE WHEN is_time_barred = 0 THEN 1 ELSE 0 END)
                FROM maritime_liens
            """)
            l_row = cursor.fetchone()
            total_maritime_liens = l_row[0] or 0
            total_liens_amount_usd = l_row[1] or 0.0
            active_enforceable_liens = l_row[2] or 0

            cursor.execute("""
                SELECT COUNT(*),
                       SUM(damage_vessel_a_usd + damage_vessel_b_usd),
                       SUM(net_settlement_usd)
                FROM collision_assessments
            """)
            c_row = cursor.fetchone()
            total_collisions = c_row[0] or 0
            total_collision_damages_usd = c_row[1] or 0.0
            total_net_settlement_usd = c_row[2] or 0.0

            cursor.execute("""
                SELECT COUNT(*),
                       SUM(total_ga_loss_usd),
                       SUM(total_contributory_value_usd)
                FROM general_average_adjustments
            """)
            g_row = cursor.fetchone()
            total_ga_adjustments = g_row[0] or 0
            total_ga_loss_usd = g_row[1] or 0.0
            total_ga_contributory_usd = g_row[2] or 0.0

        return {
            "total_vessels": total_vessels,
            "total_gross_tonnage": total_gross_tonnage,
            "total_deadweight_dwt": total_deadweight_dwt,
            "total_arrest_petitions": total_arrest_petitions,
            "warrants_granted": warrants_granted,
            "total_arrest_claims_usd": total_arrest_claims_usd,
            "total_counter_security_usd": total_counter_security_usd,
            "total_maritime_liens": total_maritime_liens,
            "active_enforceable_liens": active_enforceable_liens,
            "total_liens_amount_usd": total_liens_amount_usd,
            "total_collisions": total_collisions,
            "total_collision_damages_usd": total_collision_damages_usd,
            "total_net_settlement_usd": total_net_settlement_usd,
            "total_ga_adjustments": total_ga_adjustments,
            "total_ga_loss_usd": total_ga_loss_usd,
            "total_ga_contributory_usd": total_ga_contributory_usd,
            "compliance_framework": "Bộ luật Hàng hải Việt Nam 2015 & Pháp lệnh 05/2008/PL-UBTVQH12",
            "statutory_min_counter_security_pct": 15.0,
            "database_path": self.db_path,
        }
