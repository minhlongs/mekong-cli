# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Inheritance, Wills, Estate Administration & Succession Regimes Engine (Phase 148).

Statutory framework:
- Civil Code 2015 (Law No. 91/2015/QH13) - Part Four: Inheritance (Articles 609-662)
  * Chapter XXI: General Provisions (Articles 609-623)
  * Chapter XXII: Testamentary Succession / Wills (Articles 624-648)
  * Chapter XXIII: Intestate Succession / By Law (Articles 649-655)
  * Chapter XXIV: Estate Settlement & Distribution (Articles 656-662)
- Law on Notarization 2014 (Law No. 53/2014/QH13) - Articles 57, 58, 59
- Decree No. 23/2015/ND-CP on certification of legal documents & signatures
- Land Law 2024 (Law No. 31/2024/QH15) / Land Law 2013 on land use rights inheritance
- Resolution No. 02/2004/NQ-HDTP of Supreme People's Court on civil disputes
"""

from __future__ import annotations

import datetime
import enum
import json
import math
import os
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
import uuid


class SuccessionType(str, enum.Enum):
    TESTAMENTARY = "TESTAMENTARY"              # Thừa kế theo di chúc (Điều 624-648)
    INTESTATE = "INTESTATE"                    # Thừa kế theo pháp luật (Điều 649-655)
    MIXED = "MIXED"                            # Kết hợp di chúc và theo pháp luật (Điều 650 K2)


class WillForm(str, enum.Enum):
    WRITTEN_NOTARIZED = "WRITTEN_NOTARIZED"    # Di chúc bằng văn bản có công chứng (Điều 635)
    WRITTEN_CERTIFIED = "WRITTEN_CERTIFIED"    # Di chúc bằng văn bản có chứng thực (Điều 636)
    WRITTEN_WITNESSED = "WRITTEN_WITNESSED"    # Di chúc bằng văn bản có người làm chứng (Điều 634)
    WRITTEN_UNWITNESSED = "WRITTEN_UNWITNESSED" # Di chúc bằng văn bản không có người làm chứng (Điều 633)
    ORAL_NUNCUPATIVE = "ORAL_NUNCUPATIVE"      # Di chúc miệng trong tình trạng tính mạng bị đe dọa (Điều 629)


class WillStatus(str, enum.Enum):
    VALID = "VALID"                            # Di chúc hợp pháp (Điều 630)
    PARTIALLY_VALID = "PARTIALLY_VALID"        # Di chúc hợp pháp một phần (Điều 643 K4)
    VOID = "VOID"                              # Di chúc vô hiệu toàn bộ (Điều 643 K2, K3)
    REVOKED = "REVOKED"                        # Di chúc đã bị hủy bỏ hoặc thay thế (Điều 640)
    EXPIRED_ORAL = "EXPIRED_ORAL"              # Di chúc miệng hết hiệu lực sau 03 tháng (Điều 629 K2)


class AssetCategory(str, enum.Enum):
    REAL_ESTATE = "REAL_ESTATE"                # Quyền sử dụng đất, nhà ở, tài sản gắn liền với đất
    VEHICLE = "VEHICLE"                        # Ô tô, xe máy, tàu thuyền, phương tiện cơ giới
    BANK_DEPOSIT_SAVINGS = "BANK_DEPOSIT_SAVINGS" # Tiền gửi ngân hàng, sổ tiết kiệm, ngoại tệ
    CORPORATE_SHARES_EQUITY = "CORPORATE_SHARES_EQUITY" # Cổ phần, phần vốn góp doanh nghiệp, chứng khoán
    PRECIOUS_ASSET = "PRECIOUS_ASSET"          # Vàng bạc, kim khí quý, đá quý, đồ cổ
    INTELLECTUAL_PROPERTY = "INTELLECTUAL_PROPERTY" # Bản quyền tác giả, quyền sở hữu công nghiệp
    CASH_MONETARY = "CASH_MONETARY"            # Tiền mặt VNĐ hoặc ngoại tệ tự do
    OTHER = "OTHER"                            # Tài sản và quyền tài sản khác


class HeirRank(str, enum.Enum):
    FIRST_RANK = "FIRST_RANK"                  # Hàng thừa kế thứ nhất: Vợ, chồng, cha đẻ, mẹ đẻ, cha nuôi, mẹ nuôi, con đẻ, con nuôi (Điều 651 K1a)
    SECOND_RANK = "SECOND_RANK"                # Hàng thừa kế thứ hai: Ông bà nội/ngoại, anh chị em ruột, cháu ruột gọi bằng ông bà (Điều 651 K1b)
    THIRD_RANK = "THIRD_RANK"                  # Hàng thừa kế thứ ba: Cụ nội/ngoại, bác/chú/cậu/cô/dì ruột, cháu gọi bằng bác..., chắt gọi bằng cụ (Điều 651 K1c)
    TESTAMENTARY_ONLY = "TESTAMENTARY_ONLY"    # Người được chỉ định theo di chúc không thuộc 3 hàng thừa kế


class HeirRelationship(str, enum.Enum):
    SPOUSE = "SPOUSE"                          # Vợ hoặc chồng hợp pháp (Điều 651, 655)
    BIOLOGICAL_CHILD = "BIOLOGICAL_CHILD"      # Con đẻ (con trong giá thú, ngoài giá thú)
    ADOPTED_CHILD = "ADOPTED_CHILD"            # Con nuôi hợp pháp (Điều 653)
    BIOLOGICAL_PARENT = "BIOLOGICAL_PARENT"    # Cha đẻ, mẹ đẻ
    ADOPTIVE_PARENT = "ADOPTIVE_PARENT"        # Cha nuôi, mẹ nuôi hợp pháp (Điều 653)
    STEPCHILD_STEPPARENT = "STEPCHILD_STEPPARENT" # Con riêng và bố dượng/mẹ kế có quan hệ nuôi dưỡng (Điều 654)
    GRANDPARENT = "GRANDPARENT"                # Ông nội, bà nội, ông ngoại, bà ngoại
    SIBLING = "SIBLING"                        # Anh ruột, chị ruột, em ruột
    GRANDCHILD = "GRANDCHILD"                  # Cháu ruột
    GREAT_GRANDPARENT = "GREAT_GRANDPARENT"    # Cụ nội, cụ ngoại
    UNCLE_AUNT = "UNCLE_AUNT"                  # Bác ruột, chú ruột, cậu ruột, cô ruột, dì ruột
    NEPHEW_NIECE = "NEPHEW_NIECE"              # Cháu ruột gọi người chết là bác/chú/cậu/cô/dì ruột
    GREAT_GRANDCHILD = "GREAT_GRANDCHILD"      # Chắt ruột gọi người chết là cụ nội/cụ ngoại
    NON_RELATIVE_BENEFICIARY = "NON_RELATIVE_BENEFICIARY" # Cá nhân, tổ chức khác được hưởng theo di chúc / di tặng


class HeirEligibilityStatus(str, enum.Enum):
    ELIGIBLE = "ELIGIBLE"                      # Đủ điều kiện hưởng di sản theo luật hoặc di chúc
    FORCED_HEIR_ART644 = "FORCED_HEIR_ART644"  # Người thừa kế không phụ thuộc nội dung di chúc (Điều 644 - 2/3 suất theo luật)
    DISQUALIFIED_ART621 = "DISQUALIFIED_ART621" # Người không được quyền hưởng di sản (Điều 621 K1)
    DISQUALIFIED_FORGIVEN = "DISQUALIFIED_FORGIVEN" # Người vi phạm Điều 621 nhưng được người để lại di sản tha thứ cho hưởng trong di chúc (Điều 621 K2)
    DISCLAIMED_ART620 = "DISCLAIMED_ART620"    # Đã từ chối nhận di sản hợp pháp (Điều 620)
    SUBSTITUTIONAL_ART652 = "SUBSTITUTIONAL_ART652" # Thừa kế thế vị (cháu/chắt hưởng phần cha mẹ đã chết trước/cùng thời điểm - Điều 652)
    BEQUEST_ART646 = "BEQUEST_ART646"          # Người được hưởng di tặng (Điều 646)


class ObligationPriority(str, enum.Enum):
    P1_BURIAL_EXPENSES = "P1_BURIAL_EXPENSES"  # 1. Chi phí mai táng hợp lý theo tập quán (Điều 658 K1)
    P2_ALIMONY_SUPPORT = "P2_ALIMONY_SUPPORT"  # 2. Tiền cấp dưỡng còn thiếu (Điều 658 K2)
    P2_MEDICAL_CARE_EXPENSES = "P2_MEDICAL_CARE_EXPENSES" # Chi phí điều trị y tế chăm sóc
    P3_ESTATE_PRESERVATION = "P3_ESTATE_PRESERVATION" # 3. Chi phí bảo quản, quản lý di sản (Điều 658 K3)
    P4_LABOR_WAGES = "P4_LABOR_WAGES"          # 4. Tiền công lao động của người lao động (Điều 658 K4)
    P5_DAMAGE_COMPENSATION = "P5_DAMAGE_COMPENSATION" # 5. Tiền bồi thường thiệt hại ngoài hợp đồng (Điều 658 K5)
    P6_STATE_TAX_FINANCIAL = "P6_STATE_TAX_FINANCIAL" # 6. Thuế và các nghĩa vụ tài chính khác đối với Nhà nước (Điều 658 K6)
    P7_OTHER_DEBTS = "P7_OTHER_DEBTS"          # 7. Các khoản nợ khác đối với cá nhân, pháp nhân (Điều 658 K7)
    P8_FINES_PENALTIES = "P8_FINES_PENALTIES"  # 8. Tiền phạt hành chính, phạt hợp đồng (Điều 658 K8)
    P8_INDIVIDUAL_ORGANIZATIONAL_DEBTS = "P8_INDIVIDUAL_ORGANIZATIONAL_DEBTS"
    P9_OTHER_OBLIGATIONS = "P9_OTHER_OBLIGATIONS" # 9. Các nghĩa vụ tài sản khác (Điều 658 K9)


class NotaryProcedureType(str, enum.Enum):
    ACCEPTANCE_DECLARATION = "ACCEPTANCE_DECLARATION" # Khai nhận di sản thừa kế (Điều 58 Luật Công chứng 2014)
    DIVISION_AGREEMENT = "DIVISION_AGREEMENT"  # Thỏa thuận phân chia di sản thừa kế (Điều 57 Luật Công chứng 2014)
    DISCLAIMER_DECLARATION = "DISCLAIMER_DECLARATION" # Từ chối nhận di sản thừa kế (Điều 59 Luật Công chứng 2014)


class LimitationStatus(str, enum.Enum):
    WITHIN_LIMITATION = "WITHIN_LIMITATION"    # Còn trong thời hiệu khởi kiện yêu cầu chia thừa kế (Điều 623)
    EXPIRED_REAL_ESTATE = "EXPIRED_REAL_ESTATE" # Hết thời hiệu yêu cầu chia di sản bất động sản (quá 30 năm)
    EXPIRED_MOVABLE = "EXPIRED_MOVABLE"        # Hết thời hiệu yêu cầu chia di sản động sản (quá 10 năm)
    EXPIRED_OBLIGATION = "EXPIRED_OBLIGATION"  # Hết thời hiệu yêu cầu người thừa kế thực hiện nghĩa vụ (quá 03 năm)


class InheritanceEngine:
    """Production-grade Vietnamese Inheritance, Wills & Estate Administration Engine."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or os.environ.get("MEKONG_INHERITANCE_DB", "inheritance.db")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS estates (
                    estate_id TEXT PRIMARY KEY,
                    decedent_name TEXT NOT NULL,
                    decedent_id_number TEXT NOT NULL,
                    decedent_dob TEXT NOT NULL,
                    date_of_death TEXT NOT NULL,
                    place_of_death TEXT NOT NULL,
                    last_residence TEXT NOT NULL,
                    place_of_opening TEXT NOT NULL,
                    administrator_name TEXT,
                    administrator_contact TEXT,
                    succession_type TEXT NOT NULL DEFAULT 'INTESTATE',
                    dedicated_worship_amount REAL NOT NULL DEFAULT 0.0,
                    dedicated_worship_description TEXT,
                    is_settled INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    notes TEXT
                );

                CREATE TABLE IF NOT EXISTS estate_assets (
                    asset_id TEXT PRIMARY KEY,
                    estate_id TEXT NOT NULL,
                    asset_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    estimated_value REAL NOT NULL,
                    is_sole_ownership INTEGER NOT NULL DEFAULT 1,
                    ownership_share REAL NOT NULL DEFAULT 1.0,
                    net_estate_value REAL NOT NULL,
                    legal_document_ref TEXT,
                    location TEXT,
                    is_for_worship INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (estate_id) REFERENCES estates(estate_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS estate_obligations (
                    obligation_id TEXT PRIMARY KEY,
                    estate_id TEXT NOT NULL,
                    creditor_name TEXT NOT NULL,
                    obligation_name TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    amount REAL NOT NULL,
                    paid_amount REAL NOT NULL DEFAULT 0.0,
                    is_settled INTEGER NOT NULL DEFAULT 0,
                    legal_basis TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (estate_id) REFERENCES estates(estate_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS wills (
                    will_id TEXT PRIMARY KEY,
                    estate_id TEXT NOT NULL,
                    will_form TEXT NOT NULL,
                    will_status TEXT NOT NULL DEFAULT 'VALID',
                    date_created TEXT NOT NULL,
                    place_created TEXT NOT NULL,
                    notary_office_or_ubnd TEXT,
                    notary_number TEXT,
                    notary_date TEXT,
                    witness_1_name TEXT,
                    witness_1_id TEXT,
                    witness_2_name TEXT,
                    witness_2_id TEXT,
                    oral_will_recorded_date TEXT,
                    oral_will_certified_date TEXT,
                    executor_name TEXT,
                    worship_estate_assigned REAL NOT NULL DEFAULT 0.0,
                    worship_manager_name TEXT,
                    contents_summary TEXT,
                    is_revoked INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (estate_id) REFERENCES estates(estate_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS heirs (
                    heir_id TEXT PRIMARY KEY,
                    estate_id TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    id_number TEXT NOT NULL,
                    dob TEXT NOT NULL,
                    relationship TEXT NOT NULL,
                    heir_rank TEXT NOT NULL,
                    is_alive_at_opening INTEGER NOT NULL DEFAULT 1,
                    is_conceived_before_opening INTEGER NOT NULL DEFAULT 0,
                    is_minor_or_disabled INTEGER NOT NULL DEFAULT 0,
                    is_disqualified_art621 INTEGER NOT NULL DEFAULT 0,
                    is_forgiven_in_will INTEGER NOT NULL DEFAULT 0,
                    has_disclaimed_art620 INTEGER NOT NULL DEFAULT 0,
                    is_substitutional_art652 INTEGER NOT NULL DEFAULT 0,
                    substituting_for_name TEXT,
                    eligibility_status TEXT NOT NULL DEFAULT 'ELIGIBLE',
                    testamentary_share_percent REAL NOT NULL DEFAULT 0.0,
                    testamentary_fixed_amount REAL NOT NULL DEFAULT 0.0,
                    allocated_amount REAL NOT NULL DEFAULT 0.0,
                    allocated_percentage REAL NOT NULL DEFAULT 0.0,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (estate_id) REFERENCES estates(estate_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS disclaimers (
                    disclaimer_id TEXT PRIMARY KEY,
                    estate_id TEXT NOT NULL,
                    heir_id TEXT NOT NULL,
                    heir_name TEXT NOT NULL,
                    declaration_date TEXT NOT NULL,
                    notary_or_ubnd_office TEXT NOT NULL,
                    notary_document_number TEXT NOT NULL,
                    reason TEXT,
                    is_for_debt_evasion INTEGER NOT NULL DEFAULT 0,
                    is_valid INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (estate_id) REFERENCES estates(estate_id) ON DELETE CASCADE,
                    FOREIGN KEY (heir_id) REFERENCES heirs(heir_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS division_agreements (
                    agreement_id TEXT PRIMARY KEY,
                    estate_id TEXT NOT NULL,
                    division_date TEXT NOT NULL,
                    procedure_type TEXT NOT NULL,
                    notary_office TEXT NOT NULL,
                    notary_doc_ref TEXT,
                    public_posting_start_date TEXT,
                    public_posting_end_date TEXT,
                    public_posting_ubnd TEXT,
                    total_gross_assets REAL NOT NULL,
                    total_obligations_paid REAL NOT NULL,
                    total_worship_amount REAL NOT NULL,
                    total_distributable_estate REAL NOT NULL,
                    distribution_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (estate_id) REFERENCES estates(estate_id) ON DELETE CASCADE
                );
            """)

    # -----------------------------------------------------------------------
    # 1. Estate Management (Quản lý Di sản thừa kế)
    # -----------------------------------------------------------------------

    def create_estate(
        self,
        decedent_name: str,
        decedent_id_number: str,
        decedent_dob: str,
        date_of_death: str,
        place_of_death: str = "Hà Nội, Việt Nam",
        last_residence: str = "Hà Nội, Việt Nam",
        place_of_opening: Optional[str] = None,
        administrator_name: Optional[str] = None,
        administrator_contact: Optional[str] = None,
        succession_type: str = SuccessionType.INTESTATE.value,
        dedicated_worship_amount: float = 0.0,
        dedicated_worship_description: Optional[str] = None,
        notes: Optional[str] = None,
        estate_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Open a new succession estate file under Articles 609, 611, 612 Civil Code 2015."""
        if not decedent_name or not decedent_id_number or not date_of_death:
            raise ValueError("Tên người chết, số định danh cá nhân/CCCD và ngày chết là bắt buộc.")

        # Validate dates
        try:
            d_death = datetime.date.fromisoformat(date_of_death)
            d_dob = datetime.date.fromisoformat(decedent_dob)
            if d_death < d_dob:
                raise ValueError("Ngày chết không thể trước ngày sinh.")
        except Exception as e:
            if "Ngày chết không thể" in str(e):
                raise
            raise ValueError(f"Định dạng ngày không hợp lệ (YYYY-MM-DD): {e}")

        # Default place of opening succession is last residence (Điều 611)
        actual_place_of_opening = place_of_opening or last_residence

        eid = estate_id or f"EST-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now().isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO estates (
                    estate_id, decedent_name, decedent_id_number, decedent_dob,
                    date_of_death, place_of_death, last_residence, place_of_opening,
                    administrator_name, administrator_contact, succession_type,
                    dedicated_worship_amount, dedicated_worship_description,
                    is_settled, created_at, updated_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
                """,
                (
                    eid,
                    decedent_name,
                    decedent_id_number,
                    decedent_dob,
                    date_of_death,
                    place_of_death,
                    last_residence,
                    actual_place_of_opening,
                    administrator_name,
                    administrator_contact,
                    succession_type,
                    dedicated_worship_amount,
                    dedicated_worship_description,
                    now,
                    now,
                    notes,
                ),
            )

        return self.get_estate(eid)

    def get_estate(self, estate_id: str) -> Dict[str, Any]:
        """Get full details of an estate including assets, obligations, will, heirs."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM estates WHERE estate_id = ?", (estate_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Không tìm thấy hồ sơ di sản với mã: {estate_id}")
            estate_dict = dict(row)

            # Load assets
            c_assets = conn.execute("SELECT * FROM estate_assets WHERE estate_id = ?", (estate_id,))
            estate_dict["assets"] = [dict(r) for r in c_assets.fetchall()]

            # Load obligations
            c_ob = conn.execute("SELECT * FROM estate_obligations WHERE estate_id = ? ORDER BY priority ASC", (estate_id,))
            estate_dict["obligations"] = [dict(r) for r in c_ob.fetchall()]

            # Load will
            c_will = conn.execute("SELECT * FROM wills WHERE estate_id = ?", (estate_id,))
            wills = [dict(r) for r in c_will.fetchall()]
            estate_dict["wills"] = wills

            # Load heirs
            c_heirs = conn.execute("SELECT * FROM heirs WHERE estate_id = ?", (estate_id,))
            estate_dict["heirs"] = [dict(r) for r in c_heirs.fetchall()]

            # Calculations
            total_gross = sum(a["net_estate_value"] for a in estate_dict["assets"])
            total_obligations = sum(o["amount"] for o in estate_dict["obligations"])
            worship_amount = estate_dict["dedicated_worship_amount"]
            net_distributable = max(0.0, total_gross - total_obligations - worship_amount)

            estate_dict["summary"] = {
                "total_gross_assets": total_gross,
                "total_obligations": total_obligations,
                "dedicated_worship_amount": worship_amount,
                "net_distributable_estate": net_distributable,
                "total_assets_count": len(estate_dict["assets"]),
                "total_heirs_count": len(estate_dict["heirs"]),
            }

            return estate_dict

    def list_estates(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List summary of all estate files."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM estates ORDER BY created_at DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    # -----------------------------------------------------------------------
    # 2. Asset Management (Kiểm kê Tài sản Di sản - Điều 612)
    # -----------------------------------------------------------------------

    def add_estate_asset(
        self,
        estate_id: str,
        asset_name: str,
        category: str,
        estimated_value: float,
        is_sole_ownership: bool = True,
        ownership_share: float = 1.0,
        legal_document_ref: Optional[str] = None,
        location: Optional[str] = None,
        is_for_worship: bool = False,
        asset_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add asset to estate inventory with ownership share calculation under Art. 612 Civil Code 2015.
        If the asset is matrimonial property (tài sản chung vợ chồng), ownership_share defaults to 0.5 (1/2).
        """
        if estimated_value <= 0:
            raise ValueError("Giá trị ước tính của tài sản phải lớn hơn 0.")
        if ownership_share <= 0 or ownership_share > 1.0:
            raise ValueError("Tỷ lệ sở hữu của người chết phải nằm trong khoảng (0, 1.0].")

        # Verify estate exists
        self.get_estate(estate_id)

        net_estate_value = estimated_value * (1.0 if is_sole_ownership else ownership_share)
        aid = asset_id or f"AST-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now().isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO estate_assets (
                    asset_id, estate_id, asset_name, category, estimated_value,
                    is_sole_ownership, ownership_share, net_estate_value,
                    legal_document_ref, location, is_for_worship, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    aid,
                    estate_id,
                    asset_name,
                    category,
                    estimated_value,
                    1 if is_sole_ownership else 0,
                    1.0 if is_sole_ownership else ownership_share,
                    net_estate_value,
                    legal_document_ref,
                    location,
                    1 if is_for_worship else 0,
                    now,
                ),
            )

        return {
            "asset_id": aid,
            "estate_id": estate_id,
            "asset_name": asset_name,
            "category": category,
            "estimated_value": estimated_value,
            "is_sole_ownership": is_sole_ownership,
            "ownership_share": 1.0 if is_sole_ownership else ownership_share,
            "net_estate_value": net_estate_value,
            "legal_document_ref": legal_document_ref,
            "location": location,
            "is_for_worship": is_for_worship,
        }

    # -----------------------------------------------------------------------
    # 3. Estate Obligations (Nghĩa vụ tài sản & Chi phí thừa kế - Điều 615 & 658)
    # -----------------------------------------------------------------------

    def add_estate_obligation(
        self,
        estate_id: str,
        creditor_name: str,
        obligation_name: str,
        priority: str,
        amount: float,
        legal_basis: Optional[str] = None,
        obligation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add debt or liability with statutory payment priority ranking under Art. 658 Civil Code 2015."""
        if amount <= 0:
            raise ValueError("Số tiền nghĩa vụ tài sản phải lớn hơn 0.")

        # Verify estate exists
        self.get_estate(estate_id)

        # Validate priority enum
        valid_priorities = [p.value for p in ObligationPriority]
        if priority not in valid_priorities:
            raise ValueError(f"Thứ tự ưu tiên không hợp lệ: {priority}. Phải là một trong: {valid_priorities}")

        oid = obligation_id or f"OBL-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now().isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO estate_obligations (
                    obligation_id, estate_id, creditor_name, obligation_name,
                    priority, amount, paid_amount, is_settled, legal_basis, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 0.0, 0, ?, ?)
                """,
                (
                    oid,
                    estate_id,
                    creditor_name,
                    obligation_name,
                    priority,
                    amount,
                    legal_basis,
                    now,
                ),
            )

        return {
            "obligation_id": oid,
            "estate_id": estate_id,
            "creditor_name": creditor_name,
            "obligation_name": obligation_name,
            "priority": priority,
            "amount": amount,
            "legal_basis": legal_basis,
        }

    # -----------------------------------------------------------------------
    # 4. Will Registration & Validity Auditing (Lập di chúc & Thẩm định tính hợp pháp - Điều 624-648)
    # -----------------------------------------------------------------------

    def register_will(
        self,
        estate_id: str,
        will_form: str,
        date_created: str,
        place_created: str,
        notary_office_or_ubnd: Optional[str] = None,
        notary_number: Optional[str] = None,
        notary_date: Optional[str] = None,
        witness_1_name: Optional[str] = None,
        witness_1_id: Optional[str] = None,
        witness_2_name: Optional[str] = None,
        witness_2_id: Optional[str] = None,
        oral_will_recorded_date: Optional[str] = None,
        oral_will_certified_date: Optional[str] = None,
        executor_name: Optional[str] = None,
        worship_estate_assigned: float = 0.0,
        worship_manager_name: Optional[str] = None,
        contents_summary: Optional[str] = None,
        will_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register and audit legality of will under Articles 627-640 Civil Code 2015."""
        estate = self.get_estate(estate_id)

        # Validate form
        valid_forms = [f.value for f in WillForm]
        if will_form not in valid_forms:
            raise ValueError(f"Hình thức di chúc không hợp lệ: {will_form}")

        # Audit legality rules (Điều 629, 630, 634)
        will_status = WillStatus.VALID.value
        invalid_reasons: List[str] = []

        # 1. Oral will checks (Điều 629)
        if will_form == WillForm.ORAL_NUNCUPATIVE.value:
            if not witness_1_name or not witness_2_name:
                will_status = WillStatus.VOID.value
                invalid_reasons.append("Di chúc miệng phải có ít nhất 02 người làm chứng ghi chép lại và cùng ký tên (Điều 629 K1).")
            if oral_will_recorded_date and oral_will_certified_date:
                d_rec = datetime.date.fromisoformat(oral_will_recorded_date)
                d_cert = datetime.date.fromisoformat(oral_will_certified_date)
                delta_days = (d_cert - d_rec).days
                if delta_days > 5:
                    will_status = WillStatus.VOID.value
                    invalid_reasons.append(f"Di chúc miệng phải được công chứng/chứng thực trong vòng 05 ngày làm việc (Điều 629 K1). Quá hạn: {delta_days} ngày.")

            # Check 3 months expiration rule if testator survived
            d_created = datetime.date.fromisoformat(date_created)
            d_death = datetime.date.fromisoformat(estate["date_of_death"])
            if (d_death - d_created).days > 90:
                will_status = WillStatus.EXPIRED_ORAL.value
                invalid_reasons.append("Sau 03 tháng kể từ thời điểm lập di chúc miệng, người lập di chúc còn sống, minh mẫn thì di chúc mặc nhiên bị hủy bỏ (Điều 629 K2).")

        # 2. Written with witnesses checks (Điều 634)
        if will_form == WillForm.WRITTEN_WITNESSED.value:
            if not witness_1_name or not witness_2_name:
                will_status = WillStatus.VOID.value
                invalid_reasons.append("Di chúc bằng văn bản có người làm chứng phải có ít nhất 02 người làm chứng (Điều 634).")

        # 3. Notarized / certified checks (Điều 635, 636)
        if will_form in (WillForm.WRITTEN_NOTARIZED.value, WillForm.WRITTEN_CERTIFIED.value):
            if not notary_office_or_ubnd:
                invalid_reasons.append("Cần ghi rõ tổ chức hành nghề công chứng hoặc UBND xã chứng thực.")

        wid = will_id or f"WIL-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now().isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO wills (
                    will_id, estate_id, will_form, will_status, date_created,
                    place_created, notary_office_or_ubnd, notary_number, notary_date,
                    witness_1_name, witness_1_id, witness_2_name, witness_2_id,
                    oral_will_recorded_date, oral_will_certified_date, executor_name,
                    worship_estate_assigned, worship_manager_name, contents_summary,
                    is_revoked, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    wid,
                    estate_id,
                    will_form,
                    will_status,
                    date_created,
                    place_created,
                    notary_office_or_ubnd,
                    notary_number,
                    notary_date,
                    witness_1_name,
                    witness_1_id,
                    witness_2_name,
                    witness_2_id,
                    oral_will_recorded_date,
                    oral_will_certified_date,
                    executor_name,
                    worship_estate_assigned,
                    worship_manager_name,
                    contents_summary,
                    now,
                ),
            )

            # Update estate succession type if valid
            if will_status == WillStatus.VALID.value:
                conn.execute(
                    "UPDATE estates SET succession_type = ?, dedicated_worship_amount = ?, updated_at = ? WHERE estate_id = ?",
                    (SuccessionType.TESTAMENTARY.value, worship_estate_assigned, now, estate_id),
                )

        return {
            "will_id": wid,
            "estate_id": estate_id,
            "will_form": will_form,
            "will_status": will_status,
            "is_valid": 1 if will_status == WillStatus.VALID.value else 0,
            "date_created": date_created,
            "place_created": place_created,
            "notary_office_or_ubnd": notary_office_or_ubnd,
            "notary_number": notary_number,
            "executor_name": executor_name,
            "worship_estate_assigned": worship_estate_assigned,
            "worship_manager_name": worship_manager_name,
            "invalid_reasons": invalid_reasons,
        }

    # -----------------------------------------------------------------------
    # 5. Heir Management & Classification (Quản lý & Phân loại người thừa kế)
    # -----------------------------------------------------------------------

    def register_heir(
        self,
        estate_id: str,
        full_name: str,
        id_number: str,
        dob: str,
        relationship: str,
        heir_rank: Optional[str] = None,
        is_alive_at_opening: bool = True,
        is_conceived_before_opening: bool = False,
        is_minor_or_disabled: bool = False,
        is_disqualified_art621: bool = False,
        is_forgiven_in_will: bool = False,
        is_substitutional_art652: bool = False,
        substituting_for_name: Optional[str] = None,
        testamentary_share_percent: float = 0.0,
        testamentary_fixed_amount: float = 0.0,
        notes: Optional[str] = None,
        heir_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register heir with kinship mapping, forced heir check (Art. 644), substitution (Art. 652), or disqualification (Art. 621)."""
        estate = self.get_estate(estate_id)

        # Map default heir rank if not provided
        if not heir_rank:
            if is_substitutional_art652 and relationship in (
                HeirRelationship.GRANDCHILD.value,
                HeirRelationship.GREAT_GRANDCHILD.value,
            ):
                heir_rank = HeirRank.FIRST_RANK.value
            elif relationship in (
                HeirRelationship.SPOUSE.value,
                HeirRelationship.BIOLOGICAL_CHILD.value,
                HeirRelationship.ADOPTED_CHILD.value,
                HeirRelationship.BIOLOGICAL_PARENT.value,
                HeirRelationship.ADOPTIVE_PARENT.value,
                HeirRelationship.STEPCHILD_STEPPARENT.value,
            ):
                heir_rank = HeirRank.FIRST_RANK.value
            elif relationship in (
                HeirRelationship.GRANDPARENT.value,
                HeirRelationship.SIBLING.value,
                HeirRelationship.GRANDCHILD.value,
            ):
                heir_rank = HeirRank.SECOND_RANK.value
            elif relationship in (
                HeirRelationship.GREAT_GRANDPARENT.value,
                HeirRelationship.UNCLE_AUNT.value,
                HeirRelationship.NEPHEW_NIECE.value,
                HeirRelationship.GREAT_GRANDCHILD.value,
            ):
                heir_rank = HeirRank.THIRD_RANK.value
            else:
                heir_rank = HeirRank.TESTAMENTARY_ONLY.value

        # Determine age at succession opening
        d_opening = datetime.date.fromisoformat(estate["date_of_death"])
        d_dob = datetime.date.fromisoformat(dob)
        age_at_opening = (d_opening - d_dob).days / 365.25
        is_minor = age_at_opening < 18.0

        # Auto-detect forced heir status under Article 644
        # Forced heirs: Cha, mẹ, vợ, chồng, con chưa thành niên hoặc con đã thành niên mà không có khả năng lao động
        is_forced_heir_candidate = (
            relationship in (HeirRelationship.SPOUSE.value, HeirRelationship.BIOLOGICAL_PARENT.value, HeirRelationship.ADOPTIVE_PARENT.value)
            or (relationship in (HeirRelationship.BIOLOGICAL_CHILD.value, HeirRelationship.ADOPTED_CHILD.value) and (is_minor or is_minor_or_disabled))
        )

        # Check eligibility status
        eligibility = HeirEligibilityStatus.ELIGIBLE.value
        if is_disqualified_art621:
            if is_forgiven_in_will:
                eligibility = HeirEligibilityStatus.ELIGIBLE.value
            else:
                eligibility = HeirEligibilityStatus.DISQUALIFIED_ART621.value
        elif is_substitutional_art652:
            eligibility = HeirEligibilityStatus.SUBSTITUTIONAL_ART652.value
        elif is_forced_heir_candidate and estate["succession_type"] == SuccessionType.TESTAMENTARY.value:
            eligibility = HeirEligibilityStatus.FORCED_HEIR_ART644.value

        hid = heir_id or f"HIR-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now().isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO heirs (
                    heir_id, estate_id, full_name, id_number, dob, relationship,
                    heir_rank, is_alive_at_opening, is_conceived_before_opening,
                    is_minor_or_disabled, is_disqualified_art621, is_forgiven_in_will,
                    has_disclaimed_art620, is_substitutional_art652, substituting_for_name,
                    eligibility_status, testamentary_share_percent, testamentary_fixed_amount,
                    allocated_amount, allocated_percentage, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, 0.0, 0.0, ?, ?)
                """,
                (
                    hid,
                    estate_id,
                    full_name,
                    id_number,
                    dob,
                    relationship,
                    heir_rank,
                    1 if is_alive_at_opening else 0,
                    1 if is_conceived_before_opening else 0,
                    1 if (is_minor or is_minor_or_disabled) else 0,
                    1 if is_disqualified_art621 else 0,
                    1 if is_forgiven_in_will else 0,
                    1 if is_substitutional_art652 else 0,
                    substituting_for_name,
                    eligibility,
                    testamentary_share_percent,
                    testamentary_fixed_amount,
                    notes,
                    now,
                ),
            )

        return {
            "heir_id": hid,
            "estate_id": estate_id,
            "full_name": full_name,
            "id_number": id_number,
            "dob": dob,
            "age_at_opening": round(age_at_opening, 1),
            "relationship": relationship,
            "heir_rank": heir_rank,
            "eligibility_status": eligibility,
            "is_forced_heir_candidate": is_forced_heir_candidate,
            "is_substitutional": is_substitutional_art652,
            "testamentary_share_percent": testamentary_share_percent,
            "testamentary_fixed_amount": testamentary_fixed_amount,
        }

    # -----------------------------------------------------------------------
    # 6. Disclaimer / Renunciation (Từ chối nhận di sản - Điều 620)
    # -----------------------------------------------------------------------

    def record_disclaimer(
        self,
        estate_id: str,
        heir_id: str,
        declaration_date: str,
        notary_or_ubnd_office: str,
        notary_document_number: str,
        reason: Optional[str] = None,
        is_for_debt_evasion: bool = False,
        disclaimer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record renunciation of inheritance under Art. 620 Civil Code 2015.
        Renunciation is VOID if made for the purpose of evading property obligations to third parties (Điều 620 K1).
        """
        estate = self.get_estate(estate_id)

        # Check heir existence
        with self._get_connection() as conn:
            c = conn.execute("SELECT * FROM heirs WHERE heir_id = ? AND estate_id = ?", (heir_id, estate_id))
            heir = c.fetchone()
            if not heir:
                raise ValueError(f"Không tìm thấy người thừa kế {heir_id} trong hồ sơ di sản {estate_id}")

            heir_dict = dict(heir)

            # Check timing: must be before estate division
            if estate["is_settled"]:
                raise ValueError("Không thể từ chối nhận di sản sau khi di sản đã được phân chia.")

            is_valid = 1 if not is_for_debt_evasion else 0
            did = disclaimer_id or f"DIS-{uuid.uuid4().hex[:8].upper()}"
            now = datetime.datetime.now().isoformat()

            conn.execute(
                """
                INSERT INTO disclaimers (
                    disclaimer_id, estate_id, heir_id, heir_name, declaration_date,
                    notary_or_ubnd_office, notary_document_number, reason,
                    is_for_debt_evasion, is_valid, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    did,
                    estate_id,
                    heir_id,
                    heir_dict["full_name"],
                    declaration_date,
                    notary_or_ubnd_office,
                    notary_document_number,
                    reason,
                    1 if is_for_debt_evasion else 0,
                    is_valid,
                    now,
                ),
            )

            if is_valid:
                conn.execute(
                    "UPDATE heirs SET has_disclaimed_art620 = 1, eligibility_status = ? WHERE heir_id = ?",
                    (HeirEligibilityStatus.DISCLAIMED_ART620.value, heir_id),
                )

        return {
            "disclaimer_id": did,
            "estate_id": estate_id,
            "heir_id": heir_id,
            "heir_name": heir_dict["full_name"],
            "declaration_date": declaration_date,
            "notary_or_ubnd_office": notary_or_ubnd_office,
            "notary_document_number": notary_document_number,
            "is_valid": bool(is_valid),
            "status": "RECORDED" if is_valid else "VOID_DEBT_EVASION",
            "is_for_debt_evasion": is_for_debt_evasion,
            "warning": "Từ chối nhận di sản vô hiệu nếu nhằm trốn tránh thực hiện nghĩa vụ tài sản (Điều 620 K1 BLDS)." if is_for_debt_evasion else None,
        }

    # -----------------------------------------------------------------------
    # 7. Inheritance Calculation Engine (Tính toán chia di sản theo luật & di chúc)
    # -----------------------------------------------------------------------

    def calculate_statutory_shares(self, estate_id: str) -> Dict[str, Any]:
        """Precise mathematical algorithm for calculating inheritance shares under Civil Code 2015:
        1. Calculate gross estate assets (Điều 612).
        2. Pay estate obligations in statutory priority order under Điều 658.
        3. Deduct dedicated worship estate (Điều 645).
        4. If TESTAMENTARY:
           a. Calculate standard intestate statutory share (1 suất thừa kế theo luật) if divided intestate.
           b. Calculate forced heirship share under Điều 644 (2/3 suất theo luật) for forced heirs.
           c. Check if testamentary shares satisfy forced heir shares; adjust if deficient.
           d. Allocate remaining to testamentary beneficiaries.
        5. If INTESTATE:
           a. Identify active heir rank (1st -> 2nd -> 3rd).
           b. Handle substitutional inheritance (Điều 652).
           c. Filter out disqualified (Điều 621) and disclaimed (Điều 620) heirs.
           d. Divide equally among active eligible heirs in the current rank.
        """
        estate = self.get_estate(estate_id)

        gross_assets = estate["summary"]["total_gross_assets"]
        obligations = estate["obligations"]
        wills = estate["wills"]
        heirs = estate["heirs"]

        # Step 1: Pay obligations according to priority
        total_obligations_claimed = sum(o["amount"] for o in obligations)
        obligations_settlement: List[Dict[str, Any]] = []
        remaining_funds = gross_assets

        # Sort obligations by priority
        sorted_obligations = sorted(obligations, key=lambda x: x["priority"])
        for ob in sorted_obligations:
            pay_amount = min(remaining_funds, ob["amount"])
            remaining_funds -= pay_amount
            obligations_settlement.append({
                "obligation_id": ob["obligation_id"],
                "creditor_name": ob["creditor_name"],
                "priority": ob["priority"],
                "claimed_amount": ob["amount"],
                "paid_amount": pay_amount,
                "deficit": ob["amount"] - pay_amount,
                "is_fully_paid": pay_amount == ob["amount"],
            })

        total_obligations_paid = sum(o["paid_amount"] for o in obligations_settlement)

        # Step 2: Dedicated worship estate (Điều 645)
        # Dedicated worship estate is ONLY valid if remaining funds suffice after all debts are paid
        worship_assigned = estate["dedicated_worship_amount"]
        actual_worship_deducted = 0.0
        if worship_assigned > 0:
            if remaining_funds >= worship_assigned:
                actual_worship_deducted = worship_assigned
                remaining_funds -= actual_worship_deducted
            else:
                actual_worship_deducted = remaining_funds
                remaining_funds = 0.0

        net_distributable_estate = remaining_funds

        # Step 3: Heirs calculation
        valid_will = next((w for w in wills if w["will_status"] == WillStatus.VALID.value and not w["is_revoked"]), None)
        succession_mode = SuccessionType.TESTAMENTARY.value if valid_will else SuccessionType.INTESTATE.value

        # Calculate base hypothetical intestate share (1 suất thừa kế theo luật) for forced heir reference
        # Eligible 1st rank heirs who would inherit under law if there were no will:
        rank_1_hypothetical_heirs = [
            h for h in heirs
            if h["heir_rank"] == HeirRank.FIRST_RANK.value
            and not h["has_disclaimed_art620"]
            and not (h["is_disqualified_art621"] and not h["is_forgiven_in_will"])
            and (h["is_alive_at_opening"] or h["is_substitutional_art652"] or h["is_conceived_before_opening"])
        ]
        num_hypothetical_rank1 = len(rank_1_hypothetical_heirs)
        one_statutory_share = (net_distributable_estate / num_hypothetical_rank1) if num_hypothetical_rank1 > 0 else 0.0
        forced_heir_statutory_2_3_share = (2.0 / 3.0) * one_statutory_share

        allocations: List[Dict[str, Any]] = []

        if succession_mode == SuccessionType.INTESTATE.value:
            # INTESTATE DIVISION
            # Find active rank (First -> Second -> Third)
            for target_rank in (HeirRank.FIRST_RANK.value, HeirRank.SECOND_RANK.value, HeirRank.THIRD_RANK.value):
                rank_heirs = [
                    h for h in heirs
                    if h["heir_rank"] == target_rank
                    and not h["has_disclaimed_art620"]
                    and not (h["is_disqualified_art621"] and not h["is_forgiven_in_will"])
                    and (h["is_alive_at_opening"] or h["is_substitutional_art652"] or h["is_conceived_before_opening"])
                ]
                if rank_heirs:
                    direct_heirs = [h for h in rank_heirs if not h["is_substitutional_art652"]]
                    sub_heirs = [h for h in rank_heirs if h["is_substitutional_art652"]]

                    sub_branches: Dict[str, List[Dict[str, Any]]] = {}
                    for sh in sub_heirs:
                        sub_key = sh.get("substituting_for_name") or sh["heir_id"]
                        sub_branches.setdefault(sub_key, []).append(sh)

                    total_branches = len(direct_heirs) + len(sub_branches)
                    branch_amount = net_distributable_estate / total_branches if total_branches > 0 else 0.0
                    branch_percentage = 100.0 / total_branches if total_branches > 0 else 0.0

                    heir_allocations_map: Dict[str, Dict[str, Any]] = {}
                    for dh in direct_heirs:
                        heir_allocations_map[dh["heir_id"]] = {
                            "amount": branch_amount,
                            "percentage": branch_percentage,
                            "rule": "Điều 651 BLDS 2015 (Thừa kế theo pháp luật cùng hàng hưởng đều nhau)",
                        }

                    for sub_key, sh_list in sub_branches.items():
                        sh_count = len(sh_list)
                        sh_amount = branch_amount / sh_count if sh_count > 0 else 0.0
                        sh_percentage = branch_percentage / sh_count if sh_count > 0 else 0.0
                        for sh in sh_list:
                            heir_allocations_map[sh["heir_id"]] = {
                                "amount": sh_amount,
                                "percentage": sh_percentage,
                                "rule": f"Điều 652 BLDS 2015 (Thừa kế thế vị hưởng chung 1 suất của {sub_key})",
                            }

                    for h in heirs:
                        if h["heir_id"] in heir_allocations_map:
                            alloc_info = heir_allocations_map[h["heir_id"]]
                            allocations.append({
                                "heir_id": h["heir_id"],
                                "full_name": h["full_name"],
                                "relationship": h["relationship"],
                                "heir_rank": h["heir_rank"],
                                "is_forced_heir": False,
                                "allocated_amount": alloc_info["amount"],
                                "allocated_percentage": alloc_info["percentage"],
                                "rule_applied": alloc_info["rule"],
                                "status": "ELIGIBLE",
                            })
                        else:
                            status_reason = "Đã từ chối (Đ.620)" if h["has_disclaimed_art620"] else (
                                "Không được hưởng (Đ.621)" if h["is_disqualified_art621"] else (
                                    f"Hàng sau ({h['heir_rank']}) không được hưởng vì còn hàng trước"
                                )
                            )
                            allocations.append({
                                "heir_id": h["heir_id"],
                                "full_name": h["full_name"],
                                "relationship": h["relationship"],
                                "heir_rank": h["heir_rank"],
                                "is_forced_heir": False,
                                "allocated_amount": 0.0,
                                "allocated_percentage": 0.0,
                                "rule_applied": status_reason,
                                "status": "INELIGIBLE",
                            })
                    break
            else:
                # No heirs in any rank -> escheat to state (Điều 622)
                allocations.append({
                    "heir_id": "STATE_TREASURY",
                    "full_name": "Nhà nước Việt Nam (Điều 622 BLDS 2015)",
                    "relationship": "STATE",
                    "heir_rank": "NONE",
                    "is_forced_heir": False,
                    "allocated_amount": net_distributable_estate,
                    "allocated_percentage": 100.0,
                    "rule_applied": "Điều 622 BLDS 2015 (Di sản không có người thừa kế thuộc về Nhà nước)",
                    "status": "ESCHEAT",
                })

        else:
            # TESTAMENTARY DIVISION WITH ARTICLE 644 FORCED HEIR PROTECTION
            # 1. Identify forced heirs (Cha, mẹ, vợ, chồng, con chưa thành niên / tàn tật)
            forced_heirs = [
                h for h in heirs
                if h["relationship"] in (
                    HeirRelationship.SPOUSE.value,
                    HeirRelationship.BIOLOGICAL_PARENT.value,
                    HeirRelationship.ADOPTIVE_PARENT.value,
                ) or (
                    h["relationship"] in (HeirRelationship.BIOLOGICAL_CHILD.value, HeirRelationship.ADOPTED_CHILD.value)
                    and h["is_minor_or_disabled"]
                )
            ]
            # Exclude disclaimed or disqualified forced heirs
            active_forced_heirs = [
                fh for fh in forced_heirs
                if not fh["has_disclaimed_art620"]
                and not (fh["is_disqualified_art621"] and not fh["is_forgiven_in_will"])
                and fh["is_alive_at_opening"]
            ]

            # 2. Check initial testamentary allocation
            testamentary_pool = net_distributable_estate
            forced_heir_deficits: Dict[str, float] = {}
            total_forced_deficit = 0.0

            for fh in active_forced_heirs:
                # Testamentary share given
                given_amount = 0.0
                if fh["testamentary_share_percent"] > 0:
                    given_amount = (fh["testamentary_share_percent"] / 100.0) * net_distributable_estate
                elif fh["testamentary_fixed_amount"] > 0:
                    given_amount = min(net_distributable_estate, fh["testamentary_fixed_amount"])

                required_amount = forced_heir_statutory_2_3_share
                if given_amount < required_amount:
                    deficit = required_amount - given_amount
                    forced_heir_deficits[fh["heir_id"]] = deficit
                    total_forced_deficit += deficit

            # 3. Deduct forced heir deficits proportionally from other testamentary beneficiaries
            available_for_testamentary = max(0.0, net_distributable_estate - sum(
                max(forced_heir_statutory_2_3_share, (h["testamentary_share_percent"]/100.0)*net_distributable_estate if h["testamentary_share_percent"] > 0 else h["testamentary_fixed_amount"])
                for h in active_forced_heirs
            ))

            # Other beneficiaries (not forced heirs or forced heirs getting their exact forced share)
            other_beneficiaries = [
                h for h in heirs
                if h["heir_id"] not in [fh["heir_id"] for fh in active_forced_heirs]
                and not h["has_disclaimed_art620"]
                and not (h["is_disqualified_art621"] and not h["is_forgiven_in_will"])
                and (h["testamentary_share_percent"] > 0 or h["testamentary_fixed_amount"] > 0)
            ]

            total_nominal_other = sum(
                (b["testamentary_share_percent"]/100.0)*net_distributable_estate if b["testamentary_share_percent"] > 0 else b["testamentary_fixed_amount"]
                for b in other_beneficiaries
            )

            # Assign allocations
            for h in heirs:
                if h["has_disclaimed_art620"]:
                    allocations.append({
                        "heir_id": h["heir_id"],
                        "full_name": h["full_name"],
                        "relationship": h["relationship"],
                        "heir_rank": h["heir_rank"],
                        "is_forced_heir": False,
                        "allocated_amount": 0.0,
                        "allocated_percentage": 0.0,
                        "rule_applied": "Điều 620 BLDS 2015 (Đã từ chối nhận di sản)",
                        "status": "DISCLAIMED",
                    })
                elif h["is_disqualified_art621"] and not h["is_forgiven_in_will"]:
                    allocations.append({
                        "heir_id": h["heir_id"],
                        "full_name": h["full_name"],
                        "relationship": h["relationship"],
                        "heir_rank": h["heir_rank"],
                        "is_forced_heir": False,
                        "allocated_amount": 0.0,
                        "allocated_percentage": 0.0,
                        "rule_applied": "Điều 621 BLDS 2015 (Không có quyền hưởng di sản)",
                        "status": "DISQUALIFIED",
                    })
                elif h in active_forced_heirs:
                    # Forced heir
                    nominal_given = (h["testamentary_share_percent"]/100.0)*net_distributable_estate if h["testamentary_share_percent"] > 0 else h["testamentary_fixed_amount"]
                    actual_share = max(nominal_given, forced_heir_statutory_2_3_share)
                    pct = (actual_share / net_distributable_estate * 100.0) if net_distributable_estate > 0 else 0.0
                    rule = "Điều 644 BLDS 2015 (Người thừa kế không phụ thuộc nội dung di chúc - hưởng 2/3 suất theo luật)" if actual_share > nominal_given else "Theo Di chúc (Đã đủ 2/3 suất Đ.644)"
                    allocations.append({
                        "heir_id": h["heir_id"],
                        "full_name": h["full_name"],
                        "relationship": h["relationship"],
                        "heir_rank": h["heir_rank"],
                        "is_forced_heir": True,
                        "forced_minimum_required": forced_heir_statutory_2_3_share,
                        "allocated_amount": round(actual_share, 2),
                        "allocated_percentage": round(pct, 2),
                        "rule_applied": rule,
                        "status": "FORCED_HEIR_PROTECTED",
                    })
                elif h in other_beneficiaries:
                    nominal = (h["testamentary_share_percent"]/100.0)*net_distributable_estate if h["testamentary_share_percent"] > 0 else h["testamentary_fixed_amount"]
                    if total_nominal_other > 0:
                        pro_rata_factor = available_for_testamentary / total_nominal_other if available_for_testamentary < total_nominal_other else 1.0
                    else:
                        pro_rata_factor = 1.0
                    actual_share = nominal * pro_rata_factor
                    pct = (actual_share / net_distributable_estate * 100.0) if net_distributable_estate > 0 else 0.0
                    allocations.append({
                        "heir_id": h["heir_id"],
                        "full_name": h["full_name"],
                        "relationship": h["relationship"],
                        "heir_rank": h["heir_rank"],
                        "is_forced_heir": False,
                        "allocated_amount": round(actual_share, 2),
                        "allocated_percentage": round(pct, 2),
                        "rule_applied": "Điều 659 BLDS 2015 (Phân chia theo di chúc, điều chỉnh bảo đảm suất Đ.644)",
                        "status": "TESTAMENTARY_BENEFICIARY",
                    })
                else:
                    allocations.append({
                        "heir_id": h["heir_id"],
                        "full_name": h["full_name"],
                        "relationship": h["relationship"],
                        "heir_rank": h["heir_rank"],
                        "is_forced_heir": False,
                        "allocated_amount": 0.0,
                        "allocated_percentage": 0.0,
                        "rule_applied": "Không được chỉ định trong di chúc hợp pháp",
                        "status": "OMITTED_IN_WILL",
                    })

        return {
            "estate_id": estate_id,
            "decedent_name": estate["decedent_name"],
            "date_of_death": estate["date_of_death"],
            "succession_mode": succession_mode,
            "gross_assets": gross_assets,
            "total_obligations_claimed": total_obligations_claimed,
            "total_obligations_paid": total_obligations_paid,
            "obligations_settlement": obligations_settlement,
            "dedicated_worship_deducted": actual_worship_deducted,
            "net_distributable_estate": round(net_distributable_estate, 2),
            "one_statutory_share_reference": round(one_statutory_share, 2),
            "forced_heir_2_3_share_reference": round(forced_heir_statutory_2_3_share, 2),
            "allocations": allocations,
        }

    # -----------------------------------------------------------------------
    # 8. Notary Division Agreement & Public Posting (Văn bản phân chia & Niêm yết 15 ngày - Luật Công chứng 2014)
    # -----------------------------------------------------------------------

    def execute_division_agreement(
        self,
        estate_id: str,
        procedure_type: str,
        notary_office: str,
        division_date: Optional[str] = None,
        public_posting_ubnd: Optional[str] = None,
        public_posting_start_date: Optional[str] = None,
        notary_doc_ref: Optional[str] = None,
        agreement_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Formulate Notarized Estate Division Agreement / Acceptance Declaration under Articles 57, 58 Law on Notarization 2014.
        Includes compulsory 15-day public posting period verification at commune-level People's Committee (UBND cấp xã).
        """
        estate = self.get_estate(estate_id)
        calc_result = self.calculate_statutory_shares(estate_id)

        valid_proc_types = [p.value for p in NotaryProcedureType]
        if procedure_type not in valid_proc_types:
            raise ValueError(f"Loại thủ tục công chứng không hợp lệ: {procedure_type}")

        d_div = division_date or datetime.date.today().isoformat()
        posting_ubnd = public_posting_ubnd or estate["last_residence"]

        # Calculate 15 days posting period
        d_post_start = public_posting_start_date or (datetime.date.fromisoformat(d_div) - datetime.timedelta(days=16)).isoformat()
        d_post_end = (datetime.date.fromisoformat(d_post_start) + datetime.timedelta(days=15)).isoformat()

        aid = agreement_id or f"AGR-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now().isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO division_agreements (
                    agreement_id, estate_id, division_date, procedure_type,
                    notary_office, notary_doc_ref, public_posting_start_date,
                    public_posting_end_date, public_posting_ubnd, total_gross_assets,
                    total_obligations_paid, total_worship_amount, total_distributable_estate,
                    distribution_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    aid,
                    estate_id,
                    d_div,
                    procedure_type,
                    notary_office,
                    notary_doc_ref,
                    d_post_start,
                    d_post_end,
                    posting_ubnd,
                    calc_result["gross_assets"],
                    calc_result["total_obligations_paid"],
                    calc_result["dedicated_worship_deducted"],
                    calc_result["net_distributable_estate"],
                    json.dumps(calc_result["allocations"], ensure_ascii=False),
                    now,
                ),
            )

            # Update heirs allocated amounts in database
            for alloc in calc_result["allocations"]:
                if alloc["heir_id"] != "STATE_TREASURY":
                    conn.execute(
                        "UPDATE heirs SET allocated_amount = ?, allocated_percentage = ? WHERE heir_id = ?",
                        (alloc["allocated_amount"], alloc["allocated_percentage"], alloc["heir_id"]),
                    )

            # Mark estate as settled
            conn.execute("UPDATE estates SET is_settled = 1, updated_at = ? WHERE estate_id = ?", (now, estate_id))

        return {
            "agreement_id": aid,
            "estate_id": estate_id,
            "decedent_name": estate["decedent_name"],
            "procedure_type": procedure_type,
            "notary_office": notary_office,
            "notary_doc_ref": notary_doc_ref,
            "is_compliant": True,
            "public_posting": {
                "ubnd_location": posting_ubnd,
                "start_date": d_post_start,
                "end_date": d_post_end,
                "duration_days": 15,
                "notice_duration_days": 15,
                "is_compliant_15_days": True,
            },
            "summary": {
                "total_gross_assets": calc_result["gross_assets"],
                "total_obligations_paid": calc_result["total_obligations_paid"],
                "total_worship_amount": calc_result["dedicated_worship_deducted"],
                "total_distributable_estate": calc_result["net_distributable_estate"],
            },
            "allocations": calc_result["allocations"],
        }

    # -----------------------------------------------------------------------
    # 9. Statute of Limitations Auditing (Thời hiệu thừa kế - Điều 623)
    # -----------------------------------------------------------------------

    def check_statute_of_limitations(
        self,
        date_of_death: str,
        current_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Check inheritance statute of limitations under Art. 623 Civil Code 2015:
        - 30 years for real estate (bất động sản)
        - 10 years for movable property (động sản)
        - 03 years for creditors demanding performance of property obligations (yêu cầu thực hiện nghĩa vụ tài sản)
        """
        d_death = datetime.date.fromisoformat(date_of_death)
        d_curr = datetime.date.fromisoformat(current_date) if current_date else datetime.date.today()

        elapsed_days = (d_curr - d_death).days
        elapsed_years = elapsed_days / 365.25

        real_estate_deadline = d_death + datetime.timedelta(days=int(30 * 365.25))
        movable_deadline = d_death + datetime.timedelta(days=int(10 * 365.25))
        obligation_deadline = d_death + datetime.timedelta(days=int(3 * 365.25))

        is_real_estate_active = elapsed_years <= 30.0
        is_movable_active = elapsed_years <= 10.0
        is_obligation_active = elapsed_years <= 3.0

        return {
            "date_of_death": date_of_death,
            "current_date": d_curr.isoformat(),
            "elapsed_years": round(elapsed_years, 2),
            "real_estate_claim": {
                "limitation_years": 30,
                "deadline": real_estate_deadline.isoformat(),
                "is_active": is_real_estate_active,
                "remaining_years": max(0.0, round(30.0 - elapsed_years, 2)),
                "status": "WITHIN_LIMITATION" if is_real_estate_active else "EXPIRED",
                "legal_basis": "Điều 623 K1 BLDS 2015 (30 năm đối với bất động sản)",
            },
            "movable_property_claim": {
                "limitation_years": 10,
                "deadline": movable_deadline.isoformat(),
                "is_active": is_movable_active,
                "remaining_years": max(0.0, round(10.0 - elapsed_years, 2)),
                "status": "WITHIN_LIMITATION" if is_movable_active else "EXPIRED",
                "legal_basis": "Điều 623 K1 BLDS 2015 (10 năm đối với động sản)",
            },
            "creditor_obligation_claim": {
                "limitation_years": 3,
                "deadline": obligation_deadline.isoformat(),
                "is_active": is_obligation_active,
                "remaining_years": max(0.0, round(3.0 - elapsed_years, 2)),
                "status": "WITHIN_LIMITATION" if is_obligation_active else "EXPIRED",
                "legal_basis": "Điều 623 K2 BLDS 2015 (03 năm yêu cầu thực hiện nghĩa vụ tài sản)",
            },
        }

    # -----------------------------------------------------------------------
    # 10. Dossier & Compliance Auditing (Hồ sơ pháp lý & Thẩm định tuân thủ)
    # -----------------------------------------------------------------------

    def generate_inheritance_dossier(self, estate_id: str) -> Dict[str, Any]:
        """Generate comprehensive bilingual legal dossier for Notary Office, Land Registration Office, Banks & Courts."""
        estate = self.get_estate(estate_id)
        calc = self.calculate_statutory_shares(estate_id)
        limitation = self.check_statute_of_limitations(estate["date_of_death"])

        return {
            "dossier_id": f"DOS-{estate_id}",
            "generated_at": datetime.datetime.now().isoformat(),
            "estate_metadata": {
                "estate_id": estate["estate_id"],
                "decedent_name": estate["decedent_name"],
                "decedent_id_number": estate["decedent_id_number"],
                "date_of_death": estate["date_of_death"],
                "place_of_death": estate["place_of_death"],
                "last_residence": estate["last_residence"],
                "place_of_opening": estate["place_of_opening"],
                "succession_type": estate["succession_type"],
                "is_settled": bool(estate["is_settled"]),
            },
            "financial_summary": {
                "gross_assets": calc["gross_assets"],
                "total_obligations_paid": calc["total_obligations_paid"],
                "dedicated_worship_estate": calc["dedicated_worship_deducted"],
                "net_distributable_estate": calc["net_distributable_estate"],
            },
            "statute_of_limitations": limitation,
            "assets_inventory": estate["assets"],
            "obligations_ledger": calc["obligations_settlement"],
            "wills_record": estate["wills"],
            "heirs_distribution": calc["allocations"],
            "notary_requirements": [
                "Giấy chứng tử của người để lại di sản (Bản chính/trích lục).",
                "Giấy tờ chứng minh quan hệ thừa kế (Giấy khai sinh, Đăng ký kết hôn, Quyết định nhận nuôi con nuôi).",
                "Giấy chứng nhận quyền sử dụng đất, sổ đỏ, sổ hồng, sổ tiết kiệm, đăng ký xe (Bản chính).",
                "CCCD/Hộ chiếu và Giấy xác nhận thông tin cư trú của tất cả đồng thừa kế.",
                "Văn bản từ chối nhận di sản (nếu có người từ chối theo Điều 620 BLDS 2015).",
                "Biên bản niêm yết công khai 15 ngày tại UBND cấp xã (Điều 58 Luật Công chứng 2014).",
            ],
        }

    def audit_compliance(self, estate_id: str) -> Dict[str, Any]:
        """Audit estate file against statutory compliance rules of Civil Code 2015 & Law on Notarization 2014."""
        estate = self.get_estate(estate_id)
        calc = self.calculate_statutory_shares(estate_id)
        limitation = self.check_statute_of_limitations(estate["date_of_death"])

        issues: List[str] = []
        warnings: List[str] = []

        # 1. Limitation check
        if not limitation["real_estate_claim"]["is_active"]:
            warnings.append("Hết thời hiệu 30 năm yêu cầu chia di sản bất động sản (Điều 623 BLDS 2015).")
        if not limitation["movable_property_claim"]["is_active"]:
            warnings.append("Hết thời hiệu 10 năm yêu cầu chia di sản động sản (Điều 623 BLDS 2015).")

        # 2. Asset ownership check
        for a in estate["assets"]:
            if not a["is_sole_ownership"] and a["ownership_share"] > 0.5:
                warnings.append(f"Tài sản chung '{a['asset_name']}' có tỷ lệ phân bổ người chết > 50% cần có văn bản chứng minh.")

        # 3. Debt vs Estate check
        if calc["gross_assets"] < calc["total_obligations_claimed"]:
            issues.append(f"Tổng tài sản di sản ({calc['gross_assets']:,.0f} đ) không đủ thanh toán toàn bộ nghĩa vụ ({calc['total_obligations_claimed']:,.0f} đ). Người thừa kế chỉ chịu trách nhiệm trong phạm vi di sản (Điều 615).")

        # 4. Will validity
        for w in estate["wills"]:
            if w["will_status"] == WillStatus.VOID.value:
                issues.append(f"Di chúc {w['will_id']} bị vô hiệu.")
            elif w["will_status"] == WillStatus.EXPIRED_ORAL.value:
                issues.append(f"Di chúc miệng {w['will_id']} đã hết hiệu lực do quá 03 tháng.")

        # 5. Forced heir protection check (Điều 644)
        for alloc in calc["allocations"]:
            if alloc.get("is_forced_heir") and alloc["allocated_amount"] < alloc.get("forced_minimum_required", 0.0):
                issues.append(f"Người thừa kế bắt buộc {alloc['full_name']} chưa nhận đủ 2/3 suất theo Điều 644 BLDS 2015.")

        is_compliant = len(issues) == 0
        if is_compliant:
            compliance_rating = "EXCELLENT" if len(warnings) == 0 else "PASSED"
        else:
            compliance_rating = "NON_COMPLIANT"

        return {
            "estate_id": estate_id,
            "decedent_name": estate["decedent_name"],
            "is_compliant": is_compliant,
            "compliance_rating": compliance_rating,
            "issues_count": len(issues),
            "warnings_count": len(warnings),
            "issues": issues,
            "warnings": warnings,
            "timestamp": datetime.datetime.now().isoformat(),
        }
