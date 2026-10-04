# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Guardianship, Custodianship & Ward Protection Suite (Phase 148).

Statutory framework:
- Civil Code 2015 (Luật Dân sự số 91/2015/QH13) - Chương III Mục 4: Giám hộ (Điều 46–63)
- Law on Civil Status 2014 (Luật Hộ tịch số 60/2014/QH13) - Điều 19–21 & 39–41
- Decree No. 126/2014/ND-CP detailing provisions on family and civil relations
- Decree No. 82/2020/ND-CP on administrative penalties in judicial assistance and civil status
"""

from __future__ import annotations

import datetime
import enum
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional
import uuid


class WardCategory(str, enum.Enum):
    MINOR_NO_PARENTS = "MINOR_NO_PARENTS"                        # Người chưa thành niên mồ côi cả cha lẫn mẹ (Điều 47.1.a)
    MINOR_PARENTS_INCAPABLE = "MINOR_PARENTS_INCAPABLE"          # Chưa thành niên mà cha mẹ mất năng lực/bị hạn chế quyền (Điều 47.1.b)
    INCAPACITATED_ADULT = "INCAPACITATED_ADULT"                  # Người mất năng lực hành vi dân sự (Điều 47.2 & Điều 22)
    COGNITIVE_DIFFICULTY = "COGNITIVE_DIFFICULTY"                # Người có khó khăn trong nhận thức, làm chủ hành vi (Điều 47.3 & Điều 23)


class GuardianshipType(str, enum.Enum):
    NATURAL = "NATURAL"                                          # Giám hộ đương nhiên (Điều 52 & 53)
    APPOINTED_COMMUNE = "APPOINTED_COMMUNE"                      # Giám hộ cử bởi UBND cấp xã (Điều 54)
    DESIGNATED_COURT = "DESIGNATED_COURT"                        # Giám hộ chỉ định bởi Tòa án (Điều 54)
    CHOSEN = "CHOSEN"                                            # Người giám hộ do cha mẹ hoặc cá nhân lựa chọn (Điều 48.2)


class GuardianRelationship(str, enum.Enum):
    SPOUSE = "SPOUSE"                                            # Vợ hoặc chồng (Điều 53.1)
    PARENT = "PARENT"                                            # Cha hoặc mẹ (Điều 53.2)
    ELDER_SIBLING = "ELDER_SIBLING"                              # Anh ruột hoặc chị ruột (Điều 52.1 & 53.3)
    ADULT_CHILD = "ADULT_CHILD"                                  # Con thành niên (Điều 53.3)
    GRANDPARENT = "GRANDPARENT"                                  # Ông nội, bà nội, ông ngoại, bà ngoại (Điều 52.2)
    UNCLE_AUNT = "UNCLE_AUNT"                                    # Bác ruột, chú ruột, cậu ruột, cô ruột, dì ruột (Điều 52.3)
    COMMUNE_UBND = "COMMUNE_UBND"                                # UBND cấp xã làm người giám hộ (Điều 49)
    OTHER = "OTHER"                                              # Cá nhân, tổ chức khác được cử hoặc chỉ định


class GuardianshipStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"                                            # Đang thực hiện quyền và nghĩa vụ giám hộ
    CHANGED = "CHANGED"                                          # Đã thay đổi người giám hộ (Điều 60)
    TERMINATED = "TERMINATED"                                    # Đã chấm dứt việc giám hộ (Điều 62)


class AssetCategory(str, enum.Enum):
    REAL_ESTATE = "REAL_ESTATE"                                  # Quyền sử dụng đất, nhà ở, tài sản gắn liền với đất
    VEHICLE = "VEHICLE"                                          # Ô tô, xe máy, phương tiện vận tải
    BANK_DEPOSIT = "BANK_DEPOSIT"                                # Tiền gửi ngân hàng, sổ tiết kiệm, ngoại tệ
    LIVESTOCK = "LIVESTOCK"                                      # Gia súc, gia cầm, trang trại nuôi trồng
    OTHER = "OTHER"                                              # Tài sản khác của người được giám hộ


class TransactionType(str, enum.Enum):
    SALE = "SALE"                                                # Bán tài sản phục vụ nhu cầu thiết yếu của người được giám hộ
    LEASE = "LEASE"                                              # Cho thuê tài sản tạo nguồn thu cho người được giám hộ
    EXPENSE_CARE = "EXPENSE_CARE"                                # Chi phí nuôi dưỡng, sinh hoạt thiết yếu
    EXPENSE_EDUCATION = "EXPENSE_EDUCATION"                      # Chi phí học tập, đào tạo
    TREATMENT = "TREATMENT"                                      # Chi phí khám chữa bệnh, chăm sóc sức khỏe
    INVESTMENT = "INVESTMENT"                                    # Đầu tư an toàn bảo toàn vốn
    GIFT = "GIFT"                                                # Tặng cho (bị nghiêm cấm theo Điều 59.3)


class TerminationGrounds(str, enum.Enum):
    WARD_ATTAINED_MAJORITY = "WARD_ATTAINED_MAJORITY"            # Người được giám hộ đã thành niên (Điều 62.1)
    WARD_REGAINED_CAPACITY = "WARD_REGAINED_CAPACITY"            # Người được giám hộ đã hồi phục năng lực hành vi (Điều 62.2)
    WARD_DECEASED = "WARD_DECEASED"                              # Người được giám hộ chết (Điều 62.3)
    PARENTS_RESUMED_RIGHTS = "PARENTS_RESUMED_RIGHTS"            # Cha, mẹ người được giám hộ đã có đủ điều kiện thực hiện quyền (Điều 62.4)
    WARD_ADOPTED = "WARD_ADOPTED"                                # Người được giám hộ được nhận làm con nuôi (Điều 62.5)


MAJOR_TRANSACTION_THRESHOLD_VND = 50_000_000.0  # Ngưỡng giao dịch lớn cần sự đồng ý của người giám sát (50 triệu VND)
INITIAL_INVENTORY_DAYS_LIMIT = 10               # Thời hạn kiểm kê ban đầu: 10 ngày kể từ ngày giám hộ (Điều 59.1)
HANDOVER_MONTHS_LIMIT = 3                       # Thời hạn thanh toán, chuyển giao tài sản: 3 tháng kể từ ngày chấm dứt (Điều 63)


class GuardianshipEngine:
    """Core autonomous engine managing Vietnamese Guardianship, Custodianship & Ward Protection."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        elif os.getenv("MEKONG_GUARDIANSHIP_DB"):
            self.db_path = os.getenv("MEKONG_GUARDIANSHIP_DB")
        else:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "guardianship.db")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Guardianship Registrations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS guardianship_registrations (
                    registration_id TEXT PRIMARY KEY,
                    certificate_code TEXT NOT NULL UNIQUE,
                    ward_name TEXT NOT NULL,
                    ward_dob TEXT NOT NULL,
                    ward_id_number TEXT NOT NULL,
                    ward_address TEXT NOT NULL,
                    ward_category TEXT NOT NULL,
                    guardian_name TEXT NOT NULL,
                    guardian_dob TEXT NOT NULL,
                    guardian_id_number TEXT NOT NULL,
                    guardian_address TEXT NOT NULL,
                    guardian_phone TEXT NOT NULL,
                    guardian_relationship TEXT NOT NULL,
                    guardianship_type TEXT NOT NULL,
                    commune_ubnd TEXT NOT NULL,
                    district TEXT NOT NULL,
                    province TEXT NOT NULL,
                    registration_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    notes TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # 2. Guardianship Supervisors (Article 51)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS guardianship_supervisors (
                    supervisor_id TEXT PRIMARY KEY,
                    registration_id TEXT NOT NULL,
                    supervisor_name TEXT NOT NULL,
                    supervisor_dob TEXT NOT NULL,
                    supervisor_id_number TEXT NOT NULL,
                    supervisor_address TEXT NOT NULL,
                    supervisor_relationship TEXT NOT NULL,
                    appointing_authority TEXT NOT NULL,
                    registered_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (registration_id) REFERENCES guardianship_registrations(registration_id) ON DELETE CASCADE
                );
            """)

            # 3. Ward Assets (Article 59)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ward_assets (
                    asset_id TEXT PRIMARY KEY,
                    registration_id TEXT NOT NULL,
                    asset_name TEXT NOT NULL,
                    asset_category TEXT NOT NULL,
                    estimated_value_vnd REAL NOT NULL DEFAULT 0.0,
                    identifier TEXT NOT NULL,
                    inventory_date TEXT NOT NULL,
                    days_from_registration INTEGER NOT NULL DEFAULT 0,
                    is_verified_by_supervisor INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'HELD',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (registration_id) REFERENCES guardianship_registrations(registration_id) ON DELETE CASCADE
                );
            """)

            # 4. Asset Transactions (Article 59)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asset_transactions (
                    transaction_id TEXT PRIMARY KEY,
                    registration_id TEXT NOT NULL,
                    asset_id TEXT,
                    transaction_type TEXT NOT NULL,
                    amount_vnd REAL NOT NULL,
                    purpose TEXT NOT NULL,
                    is_major_transaction INTEGER NOT NULL DEFAULT 0,
                    supervisor_consent INTEGER NOT NULL DEFAULT 0,
                    transaction_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'APPROVED',
                    notes TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (registration_id) REFERENCES guardianship_registrations(registration_id) ON DELETE CASCADE
                );
            """)

            # 5. Guardianship Changes & Termination (Articles 60, 62, 63)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS guardianship_changes (
                    change_id TEXT PRIMARY KEY,
                    registration_id TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    grounds TEXT NOT NULL,
                    effective_date TEXT NOT NULL,
                    handover_deadline TEXT NOT NULL,
                    is_handover_completed INTEGER NOT NULL DEFAULT 0,
                    handover_notes TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (registration_id) REFERENCES guardianship_registrations(registration_id) ON DELETE CASCADE
                );
            """)

            # 6. Compliance Audit Logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_audit_logs (
                    log_id TEXT PRIMARY KEY,
                    registration_id TEXT,
                    action_type TEXT NOT NULL,
                    performed_by TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
            """)

            conn.commit()

    def _log_audit(
        self,
        conn: sqlite3.Connection,
        action_type: str,
        performed_by: str,
        details: Dict[str, Any],
        registration_id: Optional[str] = None,
    ) -> None:
        log_id = f"LOG-GH-{uuid.uuid4().hex[:10].upper()}"
        now_iso = datetime.datetime.now().isoformat()
        conn.execute(
            """
            INSERT INTO compliance_audit_logs (
                log_id, registration_id, action_type, performed_by, details_json, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                log_id,
                registration_id,
                action_type,
                performed_by,
                json.dumps(details, ensure_ascii=False),
                now_iso,
            ),
        )

    # ── Guardian Eligibility Validation (Article 48) ───────────────────

    @staticmethod
    def _calculate_age(dob_str: str, on_date: Optional[datetime.date] = None) -> int:
        if on_date is None:
            on_date = datetime.date.today()
        dob = datetime.date.fromisoformat(dob_str.strip())
        age = on_date.year - dob.year - ((on_date.month, on_date.day) < (dob.month, dob.day))
        return age

    def validate_guardian_eligibility(
        self,
        name: str,
        dob: str,
        has_full_capacity: bool = True,
        has_conviction_against_life_property: bool = False,
        parental_rights_restricted: bool = False,
        reference_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate statutory eligibility of an individual to serve as guardian under Article 48 Civil Code 2015."""
        ref_date = datetime.date.fromisoformat(reference_date) if reference_date else datetime.date.today()
        age = self._calculate_age(dob, ref_date)

        # Condition 1: Must be at least 18 years old
        if age < 18:
            raise ValueError(
                f"Guardian '{name}' is {age} years old. Under Article 48(1) Civil Code 2015, "
                f"an individual must be at least 18 years of age to be a guardian."
            )

        # Condition 2: Must have full civil act capacity
        if not has_full_capacity:
            raise ValueError(
                f"Guardian '{name}' lacks full civil act capacity. Disqualified under Article 48(1) Civil Code 2015."
            )

        # Condition 3: Not convicted of intentional crimes against life, health, dignity, or property
        if has_conviction_against_life_property:
            raise ValueError(
                f"Guardian '{name}' has a criminal record or is prosecuted for intentional crimes against "
                f"life, health, dignity, or property. Disqualified under Article 48(3) Civil Code 2015."
            )

        # Condition 4: Parental rights not restricted
        if parental_rights_restricted:
            raise ValueError(
                f"Guardian '{name}' has parental rights restricted by a court. Disqualified under Article 48(4) Civil Code 2015."
            )

        return {
            "eligible": True,
            "guardian_name": name,
            "age": age,
            "has_full_capacity": has_full_capacity,
            "no_disqualifying_crimes": not has_conviction_against_life_property,
            "parental_rights_intact": not parental_rights_restricted,
            "statutory_basis": "Điều 48 Bộ luật Dân sự 2015",
        }

    # ── Natural Guardian Hierarchy Resolution (Articles 52 & 53) ───────

    def resolve_natural_guardian_ranking(
        self,
        ward_category: str | WardCategory,
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Rank eligible natural guardian candidates according to Article 52 (minors) or Article 53 (incapacitated adults)."""
        cat = WardCategory(ward_category) if isinstance(ward_category, str) else ward_category
        ranked = []

        # Order weights: lower rank number = higher statutory priority
        priority_minor = {
            GuardianRelationship.ELDER_SIBLING.value: 1,
            GuardianRelationship.GRANDPARENT.value: 2,
            GuardianRelationship.UNCLE_AUNT.value: 3,
        }
        priority_adult = {
            GuardianRelationship.SPOUSE.value: 1,
            GuardianRelationship.PARENT.value: 2,
            GuardianRelationship.ADULT_CHILD.value: 3,
            GuardianRelationship.ELDER_SIBLING.value: 4,
        }

        priority_map = priority_minor if cat in (WardCategory.MINOR_NO_PARENTS, WardCategory.MINOR_PARENTS_INCAPABLE) else priority_adult

        for cand in candidates:
            rel = str(cand.get("relationship", GuardianRelationship.OTHER.value))
            rank = priority_map.get(rel, 99)
            cand_copy = dict(cand)
            cand_copy["statutory_priority_rank"] = rank
            ranked.append(cand_copy)

        ranked.sort(key=lambda x: (x["statutory_priority_rank"], -x.get("age", 0)))
        return ranked

    # ── Registration Operations ────────────────────────────────────────

    def register_guardianship(
        self,
        ward_name: str,
        ward_dob: str,
        ward_id_number: str,
        ward_address: str,
        ward_category: str | WardCategory,
        guardian_name: str,
        guardian_dob: str,
        guardian_id_number: str,
        guardian_address: str,
        guardian_phone: str,
        guardian_relationship: str | GuardianRelationship,
        guardianship_type: str | GuardianshipType = GuardianshipType.NATURAL,
        commune_ubnd: str = "UBND Xã Đa Kao",
        district: str = "Quận 1",
        province: str = "Thành phố Hồ Chí Minh",
        registration_date: Optional[str] = None,
        notes: str = "",
        registration_id: Optional[str] = None,
        has_full_capacity: bool = True,
        has_conviction_against_life_property: bool = False,
        parental_rights_restricted: bool = False,
    ) -> Dict[str, Any]:
        """Register legal guardianship under Civil Code 2015 & Law on Civil Status 2014."""
        now_dt = datetime.datetime.now()
        now_iso = now_dt.isoformat()
        reg_date = registration_date or now_dt.date().isoformat()

        # Validate guardian statutory eligibility
        self.validate_guardian_eligibility(
            name=guardian_name,
            dob=guardian_dob,
            has_full_capacity=has_full_capacity,
            has_conviction_against_life_property=has_conviction_against_life_property,
            parental_rights_restricted=parental_rights_restricted,
            reference_date=reg_date,
        )

        reg_id = registration_id or f"GH-{uuid.uuid4().hex[:8].upper()}"
        year_str = reg_date.split("-")[0] if "-" in reg_date else str(now_dt.year)
        cert_code = f"CERT-GH-{year_str}-{uuid.uuid4().hex[:6].upper()}"

        w_cat = WardCategory(ward_category).value if isinstance(ward_category, str) else ward_category.value
        g_rel = GuardianRelationship(guardian_relationship).value if isinstance(guardian_relationship, str) else guardian_relationship.value
        g_type = GuardianshipType(guardianship_type).value if isinstance(guardianship_type, str) else guardianship_type.value

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO guardianship_registrations (
                    registration_id, certificate_code, ward_name, ward_dob, ward_id_number,
                    ward_address, ward_category, guardian_name, guardian_dob, guardian_id_number,
                    guardian_address, guardian_phone, guardian_relationship, guardianship_type,
                    commune_ubnd, district, province, registration_date, status, notes,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?)
                """,
                (
                    reg_id, cert_code, ward_name.strip(), ward_dob.strip(), ward_id_number.strip(),
                    ward_address.strip(), w_cat, guardian_name.strip(), guardian_dob.strip(),
                    guardian_id_number.strip(), guardian_address.strip(), guardian_phone.strip(),
                    g_rel, g_type, commune_ubnd.strip(), district.strip(), province.strip(),
                    reg_date, notes.strip(), now_iso, now_iso,
                ),
            )

            self._log_audit(
                conn=conn,
                action_type="REGISTER_GUARDIANSHIP",
                performed_by=f"UBND_{commune_ubnd}",
                details={
                    "registration_id": reg_id,
                    "certificate_code": cert_code,
                    "ward": ward_name,
                    "guardian": guardian_name,
                    "category": w_cat,
                    "type": g_type,
                },
                registration_id=reg_id,
            )
            conn.commit()

        return self.get_guardianship(reg_id)

    def get_guardianship(self, registration_id: str) -> Dict[str, Any]:
        """Retrieve complete guardianship record by registration ID or certificate code."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM guardianship_registrations
                WHERE registration_id = ? OR certificate_code = ?
                """,
                (registration_id, registration_id),
            )
            row = cursor.fetchone()
            if not row:
                raise KeyError(f"Guardianship record '{registration_id}' not found.")

            reg_dict = dict(row)

            # Fetch supervisor
            cursor.execute(
                "SELECT * FROM guardianship_supervisors WHERE registration_id = ? AND status = 'ACTIVE'",
                (reg_dict["registration_id"],),
            )
            supervisor_row = cursor.fetchone()
            reg_dict["supervisor"] = dict(supervisor_row) if supervisor_row else None

            # Fetch assets
            cursor.execute(
                "SELECT * FROM ward_assets WHERE registration_id = ?",
                (reg_dict["registration_id"],),
            )
            reg_dict["assets"] = [dict(r) for r in cursor.fetchall()]

            # Fetch recent transactions
            cursor.execute(
                "SELECT * FROM asset_transactions WHERE registration_id = ? ORDER BY created_at DESC LIMIT 20",
                (reg_dict["registration_id"],),
            )
            reg_dict["transactions"] = [dict(r) for r in cursor.fetchall()]

            # Fetch changes/termination
            cursor.execute(
                "SELECT * FROM guardianship_changes WHERE registration_id = ?",
                (reg_dict["registration_id"],),
            )
            reg_dict["changes"] = [dict(r) for r in cursor.fetchall()]

            return reg_dict

    # ── Supervisor Management (Article 51) ─────────────────────────────

    def register_supervisor(
        self,
        registration_id: str,
        supervisor_name: str,
        supervisor_dob: str,
        supervisor_id_number: str,
        supervisor_address: str,
        supervisor_relationship: str = "CLOSE_RELATIVE",
        appointing_authority: str = "UBND Cấp Xã",
        registered_date: Optional[str] = None,
        supervisor_id: Optional[str] = None,
        has_full_capacity: bool = True,
    ) -> Dict[str, Any]:
        """Register supervisor of guardianship under Article 51 Civil Code 2015."""
        if not has_full_capacity:
            raise ValueError(
                f"Supervisor '{supervisor_name}' must possess full civil act capacity under Article 51(2) Civil Code 2015."
            )

        now_dt = datetime.datetime.now()
        now_iso = now_dt.isoformat()
        reg_date = registered_date or now_dt.date().isoformat()
        sup_id = supervisor_id or f"SUP-{uuid.uuid4().hex[:8].upper()}"

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Verify registration exists
            cursor.execute("SELECT registration_id, ward_name FROM guardianship_registrations WHERE registration_id = ?", (registration_id,))
            guard = cursor.fetchone()
            if not guard:
                raise KeyError(f"Guardianship record '{registration_id}' not found.")

            # Deactivate any prior active supervisor
            cursor.execute(
                "UPDATE guardianship_supervisors SET status = 'REPLACED' WHERE registration_id = ? AND status = 'ACTIVE'",
                (registration_id,),
            )

            cursor.execute(
                """
                INSERT INTO guardianship_supervisors (
                    supervisor_id, registration_id, supervisor_name, supervisor_dob, supervisor_id_number,
                    supervisor_address, supervisor_relationship, appointing_authority, registered_date,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
                """,
                (
                    sup_id, registration_id, supervisor_name.strip(), supervisor_dob.strip(),
                    supervisor_id_number.strip(), supervisor_address.strip(),
                    supervisor_relationship.strip(), appointing_authority.strip(),
                    reg_date, now_iso,
                ),
            )

            self._log_audit(
                conn=conn,
                action_type="REGISTER_SUPERVISOR",
                performed_by=appointing_authority,
                details={
                    "supervisor_id": sup_id,
                    "supervisor_name": supervisor_name,
                    "registration_id": registration_id,
                    "statutory_basis": "Điều 51 Bộ luật Dân sự 2015",
                },
                registration_id=registration_id,
            )
            conn.commit()

        return {
            "ok": True,
            "supervisor_id": sup_id,
            "registration_id": registration_id,
            "supervisor_name": supervisor_name,
            "appointing_authority": appointing_authority,
            "status": "ACTIVE",
            "statutory_role": "Giám sát việc giám hộ (Điều 51 BLDS 2015)",
        }

    # ── Asset Inventory Management (Article 59) ────────────────────────

    def record_asset_inventory(
        self,
        registration_id: str,
        asset_name: str,
        asset_category: str | AssetCategory,
        estimated_value_vnd: float,
        identifier: str,
        inventory_date: Optional[str] = None,
        is_verified_by_supervisor: bool = True,
        asset_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record ward asset inventory within statutory 10-day period under Article 59(1) Civil Code 2015."""
        now_dt = datetime.datetime.now()
        now_iso = now_dt.isoformat()
        inv_date_str = inventory_date or now_dt.date().isoformat()
        inv_date = datetime.date.fromisoformat(inv_date_str)

        ast_id = asset_id or f"AST-{uuid.uuid4().hex[:8].upper()}"
        cat_val = AssetCategory(asset_category).value if isinstance(asset_category, str) else asset_category.value

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT registration_date FROM guardianship_registrations WHERE registration_id = ?",
                (registration_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise KeyError(f"Guardianship record '{registration_id}' not found.")

            reg_date = datetime.date.fromisoformat(row["registration_date"])
            days_from_reg = (inv_date - reg_date).days

            # Statutory check: within 10 days of establishing guardianship
            if days_from_reg > INITIAL_INVENTORY_DAYS_LIMIT:
                compliance_warning = (
                    f"Warning: Initial inventory conducted {days_from_reg} days after registration, "
                    f"exceeding 10-day deadline under Article 59(1) Civil Code 2015."
                )
            else:
                compliance_warning = "Compliant with 10-day initial inventory statutory requirement."

            cursor.execute(
                """
                INSERT INTO ward_assets (
                    asset_id, registration_id, asset_name, asset_category, estimated_value_vnd,
                    identifier, inventory_date, days_from_registration, is_verified_by_supervisor,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'HELD', ?)
                """,
                (
                    ast_id, registration_id, asset_name.strip(), cat_val, float(estimated_value_vnd),
                    identifier.strip(), inv_date_str, max(0, days_from_reg),
                    1 if is_verified_by_supervisor else 0, now_iso,
                ),
            )

            self._log_audit(
                conn=conn,
                action_type="INVENTORY_ASSET",
                performed_by="GUARDIAN",
                details={
                    "asset_id": ast_id,
                    "asset_name": asset_name,
                    "category": cat_val,
                    "value_vnd": float(estimated_value_vnd),
                    "days_from_registration": days_from_reg,
                    "compliance": compliance_warning,
                },
                registration_id=registration_id,
            )
            conn.commit()

        return {
            "ok": True,
            "asset_id": ast_id,
            "registration_id": registration_id,
            "asset_name": asset_name,
            "category": cat_val,
            "estimated_value_vnd": float(estimated_value_vnd),
            "days_from_registration": days_from_reg,
            "is_verified_by_supervisor": is_verified_by_supervisor,
            "compliance_note": compliance_warning,
        }

    # ── Asset Transaction Safeguards (Article 59) ──────────────────────

    def record_asset_transaction(
        self,
        registration_id: str,
        transaction_type: str | TransactionType,
        amount_vnd: float,
        purpose: str,
        asset_id: Optional[str] = None,
        supervisor_consent: bool = False,
        is_major_transaction: Optional[bool] = None,
        transaction_date: Optional[str] = None,
        notes: str = "",
        transaction_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record transaction on ward's assets, enforcing strict safeguards under Article 59 Civil Code 2015."""
        tx_type_enum = TransactionType(transaction_type) if isinstance(transaction_type, str) else transaction_type

        # Safeguard 1: Zero-tolerance prohibition on gifts / donations of ward's assets (Article 59(3))
        if tx_type_enum == TransactionType.GIFT:
            raise ValueError(
                "Article 59(3) Civil Code 2015 strictly prohibits donating or gifting ward's assets "
                "('Không được đem tài sản của người được giám hộ tặng cho người khác')."
            )

        amt = float(amount_vnd)
        if amt < 0:
            raise ValueError("Transaction amount must be non-negative.")

        # Determine if major transaction
        is_major = is_major_transaction if is_major_transaction is not None else (amt >= MAJOR_TRANSACTION_THRESHOLD_VND or tx_type_enum == TransactionType.SALE)

        # Safeguard 2: Major transactions require supervisor consent (Article 59(2))
        if is_major and not supervisor_consent:
            raise ValueError(
                f"Major asset transaction ({amt:,.0f} VND / {tx_type_enum.value}) requires supervisor consent "
                f"under Article 59(2) Civil Code 2015. Consent flag is missing or false."
            )

        now_dt = datetime.datetime.now()
        now_iso = now_dt.isoformat()
        tx_date = transaction_date or now_dt.date().isoformat()
        t_id = transaction_id or f"TX-{uuid.uuid4().hex[:8].upper()}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM guardianship_registrations WHERE registration_id = ?", (registration_id,))
            guard = cursor.fetchone()
            if not guard:
                raise KeyError(f"Guardianship record '{registration_id}' not found.")
            if guard["status"] != "ACTIVE":
                raise ValueError(f"Cannot record transaction for guardianship in '{guard['status']}' state.")

            # If asset_id given, check asset exists
            if asset_id:
                cursor.execute("SELECT asset_name, status FROM ward_assets WHERE asset_id = ?", (asset_id,))
                ast = cursor.fetchone()
                if not ast:
                    raise KeyError(f"Asset '{asset_id}' not found.")
                if tx_type_enum == TransactionType.SALE:
                    cursor.execute("UPDATE ward_assets SET status = 'DISPOSED' WHERE asset_id = ?", (asset_id,))

            cursor.execute(
                """
                INSERT INTO asset_transactions (
                    transaction_id, registration_id, asset_id, transaction_type, amount_vnd,
                    purpose, is_major_transaction, supervisor_consent, transaction_date,
                    status, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'APPROVED', ?, ?)
                """,
                (
                    t_id, registration_id, asset_id, tx_type_enum.value, amt,
                    purpose.strip(), 1 if is_major else 0, 1 if supervisor_consent else 0,
                    tx_date, notes.strip(), now_iso,
                ),
            )

            self._log_audit(
                conn=conn,
                action_type="ASSET_TRANSACTION",
                performed_by="GUARDIAN",
                details={
                    "transaction_id": t_id,
                    "type": tx_type_enum.value,
                    "amount_vnd": amt,
                    "is_major": is_major,
                    "supervisor_consent": supervisor_consent,
                    "purpose": purpose,
                },
                registration_id=registration_id,
            )
            conn.commit()

        return {
            "ok": True,
            "transaction_id": t_id,
            "registration_id": registration_id,
            "asset_id": asset_id,
            "transaction_type": tx_type_enum.value,
            "amount_vnd": amt,
            "is_major_transaction": is_major,
            "supervisor_consent": supervisor_consent,
            "status": "APPROVED",
            "statutory_basis": "Điều 59 Bộ luật Dân sự 2015",
        }

    # ── Termination & Handover Protocol (Articles 62 & 63) ─────────────

    def terminate_guardianship(
        self,
        registration_id: str,
        grounds: str | TerminationGrounds,
        effective_date: Optional[str] = None,
        handover_notes: str = "",
        is_handover_completed: bool = False,
        change_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Terminate legal guardianship and trigger 3-month statutory handover settlement under Articles 62 & 63 Civil Code 2015."""
        grounds_val = TerminationGrounds(grounds).value if isinstance(grounds, str) else grounds.value

        now_dt = datetime.datetime.now()
        now_iso = now_dt.isoformat()
        eff_date_str = effective_date or now_dt.date().isoformat()
        eff_date = datetime.date.fromisoformat(eff_date_str)

        # Handover deadline: exactly 3 months (approx 90 days) under Article 63(1)
        # We calculate 90 days from effective termination date
        handover_deadline = (eff_date + datetime.timedelta(days=90)).isoformat()
        c_id = change_id or f"CHG-{uuid.uuid4().hex[:8].upper()}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM guardianship_registrations WHERE registration_id = ?", (registration_id,))
            guard = cursor.fetchone()
            if not guard:
                raise KeyError(f"Guardianship record '{registration_id}' not found.")

            # Update guardianship status
            cursor.execute(
                "UPDATE guardianship_registrations SET status = 'TERMINATED', updated_at = ? WHERE registration_id = ?",
                (now_iso, registration_id),
            )

            # Insert into changes/termination table
            cursor.execute(
                """
                INSERT INTO guardianship_changes (
                    change_id, registration_id, change_type, grounds, effective_date,
                    handover_deadline, is_handover_completed, handover_notes, created_at
                ) VALUES (?, ?, 'TERMINATION', ?, ?, ?, ?, ?, ?)
                """,
                (
                    c_id, registration_id, grounds_val, eff_date_str, handover_deadline,
                    1 if is_handover_completed else 0, handover_notes.strip(), now_iso,
                ),
            )

            self._log_audit(
                conn=conn,
                action_type="TERMINATE_GUARDIANSHIP",
                performed_by="COMMUNE_UBND_OR_COURT",
                details={
                    "change_id": c_id,
                    "registration_id": registration_id,
                    "grounds": grounds_val,
                    "effective_date": eff_date_str,
                    "handover_deadline": handover_deadline,
                    "handover_completed": is_handover_completed,
                    "statutory_basis": "Điều 62 & Điều 63 Bộ luật Dân sự 2015",
                },
                registration_id=registration_id,
            )
            conn.commit()

        return {
            "ok": True,
            "change_id": c_id,
            "registration_id": registration_id,
            "status": "TERMINATED",
            "grounds": grounds_val,
            "effective_date": eff_date_str,
            "handover_deadline": handover_deadline,
            "is_handover_completed": is_handover_completed,
            "statutory_timeline": "3 tháng thanh toán tài sản có người giám sát chứng kiến (Điều 63 BLDS 2015)",
        }

    # ── Query & Telemetry Operations ───────────────────────────────────

    def search_records(self, query: str = "", limit: int = 50) -> List[Dict[str, Any]]:
        """Search guardianship registrations by name, ID number, certificate code, or address."""
        q = f"%{query.strip().lower()}%"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM guardianship_registrations
                WHERE LOWER(ward_name) LIKE ?
                   OR LOWER(guardian_name) LIKE ?
                   OR LOWER(ward_id_number) LIKE ?
                   OR LOWER(guardian_id_number) LIKE ?
                   OR LOWER(certificate_code) LIKE ?
                   OR LOWER(commune_ubnd) LIKE ?
                ORDER BY created_at DESC LIMIT ?
                """,
                (q, q, q, q, q, q, limit),
            )
            return [dict(r) for r in cursor.fetchall()]

    def list_registrations(
        self,
        status: Optional[str] = None,
        ward_category: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List registered guardianship cases with optional filtering."""
        sql = "SELECT * FROM guardianship_registrations WHERE 1=1"
        params: List[Any] = []
        if status:
            sql += " AND status = ?"
            params.append(status.strip().upper())
        if ward_category:
            sql += " AND ward_category = ?"
            params.append(ward_category.strip().upper())
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(r) for r in cursor.fetchall()]

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Aggregate national guardianship protection telemetry and asset safety metrics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) AS total FROM guardianship_registrations")
            total_cases = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS active FROM guardianship_registrations WHERE status = 'ACTIVE'")
            active_cases = cursor.fetchone()["active"]

            cursor.execute("SELECT COUNT(*) AS terminated FROM guardianship_registrations WHERE status = 'TERMINATED'")
            terminated_cases = cursor.fetchone()["terminated"]

            cursor.execute(
                "SELECT COUNT(*) AS minors FROM guardianship_registrations WHERE ward_category IN ('MINOR_NO_PARENTS', 'MINOR_PARENTS_INCAPABLE')"
            )
            minor_wards = cursor.fetchone()["minors"]

            cursor.execute(
                "SELECT COUNT(*) AS adults FROM guardianship_registrations WHERE ward_category IN ('INCAPACITATED_ADULT', 'COGNITIVE_DIFFICULTY')"
            )
            adult_wards = cursor.fetchone()["adults"]

            cursor.execute("SELECT COUNT(*) AS supervisors FROM guardianship_supervisors WHERE status = 'ACTIVE'")
            active_supervisors = cursor.fetchone()["supervisors"]

            cursor.execute("SELECT COALESCE(SUM(estimated_value_vnd), 0.0) AS total_val, COUNT(*) AS asset_count FROM ward_assets")
            ast_row = cursor.fetchone()
            total_asset_value_vnd = ast_row["total_val"]
            total_assets = ast_row["asset_count"]

            cursor.execute("SELECT COUNT(*) AS tx_count, COALESCE(SUM(amount_vnd), 0.0) AS total_tx FROM asset_transactions")
            tx_row = cursor.fetchone()
            total_transactions = tx_row["tx_count"]
            total_tx_amount_vnd = tx_row["total_tx"]

            cursor.execute("SELECT COUNT(*) AS logs FROM compliance_audit_logs")
            audit_logs = cursor.fetchone()["logs"]

            supervisor_coverage_pct = round((active_supervisors / active_cases * 100.0), 2) if active_cases > 0 else 100.0

            return {
                "total_guardianship_cases": total_cases,
                "active_cases": active_cases,
                "terminated_cases": terminated_cases,
                "minor_wards_protected": minor_wards,
                "adult_incapacitated_wards": adult_wards,
                "active_supervisors": active_supervisors,
                "supervisor_coverage_pct": supervisor_coverage_pct,
                "total_managed_assets_count": total_assets,
                "total_managed_assets_vnd": total_asset_value_vnd,
                "total_transactions_count": total_transactions,
                "total_transactions_amount_vnd": total_tx_amount_vnd,
                "compliance_audit_logs": audit_logs,
                "statutory_framework": "Bộ luật Dân sự 2015 (Điều 46-63) & Luật Hộ tịch 2014",
            }
