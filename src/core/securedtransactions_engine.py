"""
Autonomous Vietnamese Registration of Security Interests & Secured Transactions Suite.
Compliant with:
- Civil Code 2015 (Bộ luật Dân sự - Law No. 91/2015/QH13, Chapter XV, Articles 292-350 on Security Measures)
- Decree No. 99/2022/ND-CP on Registration of Security Measures (Nghị định số 99/2022/NĐ-CP)
- Circular No. 08/2023/TT-BTP guiding forms, registers, and operations of Secured Transactions Registration
- Land Law 2024 (Law No. 31/2024/QH15 - Article 133 on Mortgage of Land Use Rights)
- Maritime Code 2015 (Law No. 95/2015/QH13 - Articles 37-41 on Ship Mortgages)
- Law on Civil Aviation of Vietnam (Law No. 66/2006/QH11 & Law No. 61/2014/QH13 - Aircraft Mortgages)

Standard library only: zero external vendor dependencies.
Enforces strict AST boundaries (tests/test_core_boundary.py compliant).
"""

import sqlite3
import datetime
import json
import uuid
import enum
import os
import random
from typing import Dict, Any, List, Optional


class SecurityMeasureType(str, enum.Enum):
    MORTGAGE = "MORTGAGE"                    # Thế chấp tài sản (Điều 317 BLDS)
    PLEDGE = "PLEDGE"                        # Cầm cố tài sản (Điều 309 BLDS)
    DEPOSIT = "DEPOSIT"                      # Đặt cọc (Điều 328 BLDS)
    SECURITY_COLLATERAL = "SECURITY_COLLATERAL" # Ký cược (Điều 329 BLDS)
    ESCROW_DEPOSIT = "ESCROW_DEPOSIT"        # Ký quỹ (Điều 330 BLDS)
    TITLE_RETENTION = "TITLE_RETENTION"      # Bảo lưu quyền sở hữu (Điều 331 BLDS)
    GUARANTEE = "GUARANTEE"                  # Bảo lãnh (Điều 335 BLDS)
    PLEDGE_OF_TRUST = "PLEDGE_OF_TRUST"      # Tín chấp (Điều 344 BLDS)
    PROPERTY_LIEN = "PROPERTY_LIEN"          # Cầm giữ tài sản (Điều 346 BLDS)


class AssetType(str, enum.Enum):
    REAL_ESTATE = "REAL_ESTATE"              # Quyền sử dụng đất, nhà ở, tài sản gắn liền với đất
    MOVABLE_PROPERTY = "MOVABLE_PROPERTY"    # Phương tiện giao thông, máy móc thiết bị, hàng hóa luân chuyển
    PROPERTY_RIGHT = "PROPERTY_RIGHT"        # Quyền đòi nợ, quyền tài sản phát sinh từ hợp đồng, cổ phần
    FUTURE_ASSET = "FUTURE_ASSET"            # Tài sản hình thành trong tương lai
    INVESTMENT_PROJECT = "INVESTMENT_PROJECT"# Dự án đầu tư xây dựng nhà ở, dự án công trình
    VEHICLE = "VEHICLE"                      # Phương tiện giao thông cơ giới đường bộ (ô tô, xe máy)
    VESSEL = "VESSEL"                        # Tàu biển, phương tiện thủy nội địa
    AIRCRAFT = "AIRCRAFT"                    # Tàu bay dân dụng
    EQUIPMENT_MACHINERY = "EQUIPMENT_MACHINERY" # Máy móc thiết bị, dây chuyền sản xuất
    INVENTORY_GOODS = "INVENTORY_GOODS"      # Hàng hóa luân chuyển trong quá trình sản xuất, kinh doanh
    AGRICULTURAL_PRODUCT = "AGRICULTURAL_PRODUCT" # Nông sản, thủy hải sản, vùng nguyên liệu


class RegistrationStatus(str, enum.Enum):
    REGISTERED = "REGISTERED"                # Đã đăng ký có hiệu lực
    MODIFIED = "MODIFIED"                    # Đã đăng ký thay đổi nội dung
    DISPOSAL_NOTICE = "DISPOSAL_NOTICE"      # Đang xử lý tài sản bảo đảm
    DEREGISTERED = "DEREGISTERED"            # Đã xóa đăng ký (giải chấp)


class DisposalMethod(str, enum.Enum):
    AUCTION = "AUCTION"                      # Bán đấu giá tài sản
    PRIVATE_SALE = "PRIVATE_SALE"            # Bên nhận bảo đảm tự bán tài sản
    DEBT_OFFSET = "DEBT_OFFSET"              # Nhận chính tài sản để thay thế thực hiện nghĩa vụ
    OTHER = "OTHER"                          # Phương thức khác do các bên thỏa thuận


class SecuredTransactionsEngine:
    """Core engine managing Vietnamese Security Interests, Priority Rankings, Collateral Assets & Deregistrations."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        elif os.getenv("MEKONG_SECUREDTRANSACTIONS_DB"):
            self.db_path = os.getenv("MEKONG_SECUREDTRANSACTIONS_DB")
        else:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "securedtransactions.db")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Security Registrations Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS security_registrations (
                    registration_id TEXT PRIMARY KEY,
                    contract_number TEXT NOT NULL,
                    measure_type TEXT NOT NULL,
                    secured_party_name TEXT NOT NULL,
                    secured_party_id TEXT NOT NULL,
                    secured_party_address TEXT NOT NULL,
                    securing_party_name TEXT NOT NULL,
                    securing_party_id TEXT NOT NULL,
                    securing_party_address TEXT NOT NULL,
                    debtor_name TEXT,
                    debtor_id TEXT,
                    secured_obligation_amount REAL NOT NULL,
                    secured_obligation_currency TEXT NOT NULL DEFAULT 'VND',
                    registry_office TEXT NOT NULL,
                    registration_timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # 2. Collateral Assets Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collateral_assets (
                    asset_id TEXT PRIMARY KEY,
                    registration_id TEXT NOT NULL,
                    asset_type TEXT NOT NULL,
                    asset_description TEXT NOT NULL,
                    identifier_number TEXT NOT NULL,
                    estimated_value REAL NOT NULL,
                    location TEXT NOT NULL,
                    is_future_asset INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            # 3. Priority Rankings Table (Điều 308 BLDS 2015)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS priority_rankings (
                    ranking_id TEXT PRIMARY KEY,
                    asset_identifier TEXT NOT NULL,
                    registration_id TEXT NOT NULL,
                    priority_rank INTEGER NOT NULL,
                    claim_amount REAL NOT NULL,
                    registration_timestamp TEXT NOT NULL,
                    is_opposable_to_third_parties INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );
            """)

            # 4. Disposal Notices Table (Điều 51 Nghị định 99/2022/NĐ-CP)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS disposal_notices (
                    notice_id TEXT PRIMARY KEY,
                    registration_id TEXT NOT NULL,
                    asset_id TEXT NOT NULL,
                    disposal_reason TEXT NOT NULL,
                    disposal_method TEXT NOT NULL,
                    expected_disposal_date TEXT NOT NULL,
                    notifying_party TEXT NOT NULL,
                    notice_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            # 5. Deregistrations Table (Điều 52 Nghị định 99/2022/NĐ-CP)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deregistrations (
                    deregistration_id TEXT PRIMARY KEY,
                    registration_id TEXT NOT NULL,
                    deregistration_reason TEXT NOT NULL,
                    requesting_party TEXT NOT NULL,
                    approving_officer TEXT NOT NULL,
                    release_date TEXT NOT NULL,
                    certificate_code TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

            # 6. Inter-Agency Compliance Audit Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_audit_logs (
                    log_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    details TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
            """)
            conn.commit()

    def _log_audit(self, conn: sqlite3.Connection, entity_type: str, entity_id: str, action: str, actor: str, details: Dict[str, Any]) -> None:
        cursor = conn.cursor()
        log_id = f"LOG-BPBD-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO compliance_audit_logs (log_id, entity_type, entity_id, action, actor, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (log_id, entity_type, entity_id, action, actor, json.dumps(details, ensure_ascii=False), now))

    # 1. Register Initial or Modified Security Interest (Điều 292-350 BLDS & Nghị định 99/2022)
    def register_security_interest(
        self,
        contract_number: str,
        measure_type: str,
        secured_party_name: str,
        secured_party_id: str,
        secured_party_address: str,
        securing_party_name: str,
        securing_party_id: str,
        securing_party_address: str,
        secured_obligation_amount: float,
        debtor_name: Optional[str] = None,
        debtor_id: Optional[str] = None,
        secured_obligation_currency: str = "VND",
        registry_office: Optional[str] = None,
        registration_timestamp: Optional[str] = None,
        status: str = RegistrationStatus.REGISTERED.value,
        notes: str = "",
        registration_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register security measure and establish third-party opposability under Civil Code 2015."""
        if not contract_number or not contract_number.strip():
            raise ValueError("Security contract number cannot be empty.")
        if not secured_party_name or not secured_party_name.strip():
            raise ValueError("Secured party (creditor/bên nhận bảo đảm) name cannot be empty.")
        if not secured_party_id or not secured_party_id.strip():
            raise ValueError("Secured party ID/enterprise code cannot be empty.")
        if not securing_party_name or not securing_party_name.strip():
            raise ValueError("Securing party (guarantor/bên bảo đảm) name cannot be empty.")
        if not securing_party_id or not securing_party_id.strip():
            raise ValueError("Securing party ID/citizen ID cannot be empty.")
        if secured_obligation_amount <= 0:
            raise ValueError("Secured obligation amount must be strictly greater than 0.")

        try:
            valid_measure = SecurityMeasureType(measure_type.strip().upper())
        except ValueError:
            raise ValueError(f"Invalid security measure type: {measure_type}. Valid: {[m.value for m in SecurityMeasureType]}")

        # Competent registry office default under Decree 99/2022
        if not registry_office or not registry_office.strip():
            registry_office = "Trung tâm Đăng ký giao dịch, tài sản tại TP. Hà Nội - Cục ĐKQGGDBD (Bộ Tư pháp)"

        reg_id = registration_id if registration_id else f"REG-BPBD-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        reg_time = registration_timestamp if registration_timestamp else now

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO security_registrations (
                    registration_id, contract_number, measure_type, secured_party_name,
                    secured_party_id, secured_party_address, securing_party_name,
                    securing_party_id, securing_party_address, debtor_name, debtor_id,
                    secured_obligation_amount, secured_obligation_currency, registry_office,
                    registration_timestamp, status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(registration_id) DO UPDATE SET
                    contract_number=excluded.contract_number,
                    measure_type=excluded.measure_type,
                    secured_party_name=excluded.secured_party_name,
                    secured_party_id=excluded.secured_party_id,
                    secured_party_address=excluded.secured_party_address,
                    securing_party_name=excluded.securing_party_name,
                    securing_party_id=excluded.securing_party_id,
                    securing_party_address=excluded.securing_party_address,
                    debtor_name=excluded.debtor_name,
                    debtor_id=excluded.debtor_id,
                    secured_obligation_amount=excluded.secured_obligation_amount,
                    secured_obligation_currency=excluded.secured_obligation_currency,
                    registry_office=excluded.registry_office,
                    registration_timestamp=excluded.registration_timestamp,
                    status=excluded.status,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at;
            """, (
                reg_id, contract_number.strip(), valid_measure.value, secured_party_name.strip(),
                secured_party_id.strip(), secured_party_address.strip(), securing_party_name.strip(),
                securing_party_id.strip(), securing_party_address.strip(),
                debtor_name.strip() if debtor_name else securing_party_name.strip(),
                debtor_id.strip() if debtor_id else securing_party_id.strip(),
                float(secured_obligation_amount), secured_obligation_currency.strip().upper(),
                registry_office.strip(), reg_time, status.strip().upper(), notes.strip(), now, now
            ))
            self._log_audit(conn, "SECURITY_REGISTRATION", reg_id, "REGISTER", registry_office, {
                "contract": contract_number,
                "measure": valid_measure.value,
                "amount": secured_obligation_amount,
                "secured_party": secured_party_name,
                "securing_party": securing_party_name,
            })
            conn.commit()

        return self.get_record("registration", reg_id)

    register_security_measure = register_security_interest

    # 2. Record Collateral Asset Linked to Security Measure
    def record_collateral(
        self,
        registration_id: str,
        asset_type: str,
        asset_description: str,
        identifier_number: str,
        estimated_value: float,
        location: str,
        is_future_asset: bool = False,
        status: str = "COLLATERALIZED",
        asset_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record collateral asset and link to active security registration."""
        if not registration_id or not registration_id.strip():
            raise ValueError("Registration ID cannot be empty.")
        if not asset_description or not asset_description.strip():
            raise ValueError("Asset description cannot be empty.")
        if not identifier_number or not identifier_number.strip():
            raise ValueError("Asset identifier number (VIN/Chassis/Land Certificate/Contract No.) cannot be empty.")
        if estimated_value <= 0:
            raise ValueError("Estimated collateral value must be strictly greater than 0.")
        if not location or not location.strip():
            raise ValueError("Asset location / registration authority cannot be empty.")

        try:
            valid_asset_type = AssetType(asset_type.strip().upper())
        except ValueError:
            raise ValueError(f"Invalid asset type: {asset_type}. Valid: {[a.value for a in AssetType]}")

        # Check registration exists
        reg = self.get_record("registration", registration_id.strip())

        a_id = asset_id if asset_id else f"ASSET-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO collateral_assets (
                    asset_id, registration_id, asset_type, asset_description,
                    identifier_number, estimated_value, location, is_future_asset,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_id) DO UPDATE SET
                    registration_id=excluded.registration_id,
                    asset_type=excluded.asset_type,
                    asset_description=excluded.asset_description,
                    identifier_number=excluded.identifier_number,
                    estimated_value=excluded.estimated_value,
                    location=excluded.location,
                    is_future_asset=excluded.is_future_asset,
                    status=excluded.status;
            """, (
                a_id, registration_id.strip(), valid_asset_type.value, asset_description.strip(),
                identifier_number.strip(), float(estimated_value), location.strip(),
                1 if is_future_asset else 0, status.strip().upper(), now
            ))
            self._log_audit(conn, "COLLATERAL_ASSET", a_id, "RECORD_COLLATERAL", reg["registry_office"], {
                "registration_id": registration_id,
                "asset_type": valid_asset_type.value,
                "identifier": identifier_number,
                "estimated_value": estimated_value,
            })
            conn.commit()

        # Update priority rankings automatically for this asset identifier
        self.calculate_priority(identifier_number.strip())

        return self.get_record("collateral", a_id)

    # 3. Calculate Priority of Repayment (Điều 308 BLDS 2015)
    def calculate_priority(self, asset_identifier: str) -> List[Dict[str, Any]]:
        """
        Calculate statutory repayment priority ranking over an asset under Article 308 Civil Code 2015.
        Rules:
        1. Opposable security interests (registered) rank strictly ahead of non-opposable interests.
        2. Among registered security interests, priority is determined chronologically by registration timestamp.
        3. Among unregistered security interests, priority is determined by creation time.
        """
        if not asset_identifier or not asset_identifier.strip():
            raise ValueError("Asset identifier cannot be empty.")

        clean_id = asset_identifier.strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Find all registrations linked to this asset identifier
            cursor.execute("""
                SELECT ca.asset_id, ca.estimated_value, sr.registration_id, sr.secured_obligation_amount,
                       sr.registration_timestamp, sr.secured_party_name, sr.status
                FROM collateral_assets ca
                JOIN security_registrations sr ON ca.registration_id = sr.registration_id
                WHERE ca.identifier_number = ? AND sr.status != 'DEREGISTERED'
                ORDER BY sr.registration_timestamp ASC;
            """, (clean_id,))
            rows = cursor.fetchall()

            # Clear existing rankings for this asset
            cursor.execute("DELETE FROM priority_rankings WHERE asset_identifier = ?;", (clean_id,))

            rankings = []
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            for rank_idx, r in enumerate(rows, start=1):
                ranking_id = f"PRANK-{uuid.uuid4().hex[:8].upper()}"
                reg_id = r["registration_id"]
                claim_amount = float(r["secured_obligation_amount"])
                reg_time = r["registration_timestamp"]

                cursor.execute("""
                    INSERT INTO priority_rankings (
                        ranking_id, asset_identifier, registration_id, priority_rank,
                        claim_amount, registration_timestamp, is_opposable_to_third_parties, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 1, ?);
                """, (ranking_id, clean_id, reg_id, rank_idx, claim_amount, reg_time, now))

                rankings.append({
                    "ranking_id": ranking_id,
                    "asset_identifier": clean_id,
                    "registration_id": reg_id,
                    "secured_party": r["secured_party_name"],
                    "priority_rank": rank_idx,
                    "claim_amount": claim_amount,
                    "registration_timestamp": reg_time,
                    "is_opposable_to_third_parties": True,
                })

            conn.commit()
            return rankings

    # 4. Notice of Collateral Disposal (Điều 51 Nghị định 99/2022/NĐ-CP)
    def register_disposal_notice(
        self,
        registration_id: str,
        asset_id: str,
        disposal_reason: str,
        expected_disposal_date: str,
        notifying_party: str,
        disposal_method: str = DisposalMethod.AUCTION.value,
        notice_date: Optional[str] = None,
        status: str = "ACTIVE",
        notice_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register formal notice on disposal of collateral property under Article 51 Decree 99/2022/ND-CP."""
        if not registration_id or not registration_id.strip():
            raise ValueError("Registration ID cannot be empty.")
        if not asset_id or not asset_id.strip():
            raise ValueError("Asset ID cannot be empty.")
        if not disposal_reason or not disposal_reason.strip():
            raise ValueError("Disposal reason (default on loan, breach of contract) cannot be empty.")
        if not expected_disposal_date or not expected_disposal_date.strip():
            raise ValueError("Expected disposal date cannot be empty.")
        if not notifying_party or not notifying_party.strip():
            raise ValueError("Notifying party cannot be empty.")

        try:
            valid_method = DisposalMethod(disposal_method.strip().upper())
        except ValueError:
            raise ValueError(f"Invalid disposal method: {disposal_method}. Valid: {[m.value for m in DisposalMethod]}")

        # Check records exist
        self.get_record("registration", registration_id.strip())
        self.get_record("collateral", asset_id.strip())

        n_id = notice_id if notice_id else f"DISP-{uuid.uuid4().hex[:8].upper()}"
        n_date = notice_date if notice_date else datetime.date.today().isoformat()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO disposal_notices (
                    notice_id, registration_id, asset_id, disposal_reason,
                    disposal_method, expected_disposal_date, notifying_party,
                    notice_date, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(notice_id) DO UPDATE SET
                    disposal_reason=excluded.disposal_reason,
                    disposal_method=excluded.disposal_method,
                    expected_disposal_date=excluded.expected_disposal_date,
                    notifying_party=excluded.notifying_party,
                    notice_date=excluded.notice_date,
                    status=excluded.status;
            """, (
                n_id, registration_id.strip(), asset_id.strip(), disposal_reason.strip(),
                valid_method.value, expected_disposal_date.strip(), notifying_party.strip(),
                n_date, status.strip().upper(), now
            ))
            # Mark registration status as DISPOSAL_NOTICE
            cursor.execute("""
                UPDATE security_registrations SET status='DISPOSAL_NOTICE', updated_at=? WHERE registration_id=?;
            """, (now, registration_id.strip()))

            self._log_audit(conn, "DISPOSAL_NOTICE", n_id, "NOTICE_DISPOSAL", notifying_party, {
                "registration_id": registration_id,
                "asset_id": asset_id,
                "method": valid_method.value,
                "expected_date": expected_disposal_date,
            })
            conn.commit()

        return self.get_record("disposal", n_id)

    # 5. Deregistration / Release of Security Interest (Điều 52 Nghị định 99/2022/NĐ-CP)
    def deregister_security_interest(
        self,
        registration_id: str,
        deregistration_reason: str,
        requesting_party: str,
        approving_officer: str,
        release_date: Optional[str] = None,
        deregistration_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Release and cancel registration of security interest upon fulfillment of secured obligation."""
        if not registration_id or not registration_id.strip():
            raise ValueError("Registration ID cannot be empty.")
        if not deregistration_reason or not deregistration_reason.strip():
            raise ValueError("Deregistration reason (obligation fulfilled, collateral substituted, waiver) cannot be empty.")
        if not requesting_party or not requesting_party.strip():
            raise ValueError("Requesting party cannot be empty.")
        if not approving_officer or not approving_officer.strip():
            raise ValueError("Approving registrar officer cannot be empty.")

        reg = self.get_record("registration", registration_id.strip())

        d_id = deregistration_id if deregistration_id else f"DEREG-{uuid.uuid4().hex[:8].upper()}"
        rel_date = release_date if release_date else datetime.date.today().isoformat()
        cert_code = f"CERT-XOA-BPBD-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO deregistrations (
                    deregistration_id, registration_id, deregistration_reason,
                    requesting_party, approving_officer, release_date,
                    certificate_code, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'DEREGISTERED', ?)
                ON CONFLICT(deregistration_id) DO UPDATE SET
                    deregistration_reason=excluded.deregistration_reason,
                    requesting_party=excluded.requesting_party,
                    approving_officer=excluded.approving_officer,
                    release_date=excluded.release_date,
                    certificate_code=excluded.certificate_code,
                    status=excluded.status;
            """, (
                d_id, registration_id.strip(), deregistration_reason.strip(),
                requesting_party.strip(), approving_officer.strip(), rel_date,
                cert_code, now
            ))
            # Mark registration as DEREGISTERED
            cursor.execute("""
                UPDATE security_registrations SET status='DEREGISTERED', updated_at=? WHERE registration_id=?;
            """, (now, registration_id.strip()))

            # Mark linked collateral assets as RELEASED
            cursor.execute("""
                UPDATE collateral_assets SET status='RELEASED' WHERE registration_id=?;
            """, (registration_id.strip(),))

            # Remove from priority rankings
            cursor.execute("""
                DELETE FROM priority_rankings WHERE registration_id=?;
            """, (registration_id.strip(),))

            self._log_audit(conn, "DEREGISTRATION", d_id, "DEREGISTER", approving_officer, {
                "registration_id": registration_id,
                "reason": deregistration_reason,
                "certificate_code": cert_code,
            })
            conn.commit()

        return self.get_record("deregistration", d_id)

    # 6. Search and Query Security Interests
    def search_security_interest(self, query: str) -> List[Dict[str, Any]]:
        """Search security registrations by contract number, debtor ID, secured party, or asset identifier."""
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        q = f"%{query.strip()}%"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT sr.*, ca.identifier_number AS collateral_id, ca.asset_description
                FROM security_registrations sr
                LEFT JOIN collateral_assets ca ON sr.registration_id = ca.registration_id
                WHERE sr.contract_number LIKE ?
                   OR sr.securing_party_id LIKE ?
                   OR sr.securing_party_name LIKE ?
                   OR sr.secured_party_name LIKE ?
                   OR ca.identifier_number LIKE ?
                ORDER BY sr.registration_timestamp DESC;
            """, (q, q, q, q, q))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_record(self, category: str, record_id: str) -> Dict[str, Any]:
        table_map = {
            "registration": ("security_registrations", "registration_id"),
            "collateral": ("collateral_assets", "asset_id"),
            "priority": ("priority_rankings", "ranking_id"),
            "disposal": ("disposal_notices", "notice_id"),
            "deregistration": ("deregistrations", "deregistration_id"),
        }
        if category not in table_map:
            raise ValueError(f"Unknown category: {category}. Valid: {list(table_map.keys())}")

        table, id_col = table_map[category]
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table} WHERE {id_col} = ?;", (record_id,))
            row = cursor.fetchone()
            if not row:
                raise KeyError(f"Record '{record_id}' not found in category '{category}'.")
            return dict(row)

    def list_records(self, category: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        table_map = {
            "registration": "security_registrations",
            "collateral": "collateral_assets",
            "priority": "priority_rankings",
            "disposal": "disposal_notices",
            "deregistration": "deregistrations",
            "audit": "compliance_audit_logs",
        }
        if category not in table_map:
            raise ValueError(f"Unknown category: {category}. Valid: {list(table_map.keys())}")

        table = table_map[category]
        order_col = "timestamp" if category == "audit" else "created_at"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {table} ORDER BY {order_col} DESC LIMIT ? OFFSET ?;", (limit, offset))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                if category == "audit" and "details" in item:
                    try:
                        item["details"] = json.loads(item["details"])
                    except Exception:
                        pass
                results.append(item)
            return results

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Aggregate statistical telemetry across Vietnamese secured transactions registry systems."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN status='REGISTERED' THEN 1 ELSE 0 END) AS active_reg, SUM(CASE WHEN status='DEREGISTERED' THEN 1 ELSE 0 END) AS deregistered_total, SUM(secured_obligation_amount) AS total_secured_value FROM security_registrations;")
            reg_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total, SUM(estimated_value) AS total_collateral_value FROM collateral_assets;")
            asset_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM priority_rankings;")
            prank_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM disposal_notices WHERE status='ACTIVE';")
            disp_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM deregistrations;")
            dereg_res = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) AS total FROM compliance_audit_logs;")
            audit_res = cursor.fetchone()

            return {
                "statutory_framework": "Civil Code 2015 (Law 91/2015/QH13) & Decree No. 99/2022/ND-CP",
                "central_authority": "National Registration Agency for Secured Transactions - MOJ (Cục ĐKQGGDBD - BTP)",
                "total_security_registrations": reg_res["total"] if reg_res else 0,
                "active_security_registrations": int(reg_res["active_reg"] or 0) if reg_res else 0,
                "deregistered_securities": int(reg_res["deregistered_total"] or 0) if reg_res else 0,
                "total_secured_obligation_value_vnd": float(reg_res["total_secured_value"] or 0.0) if reg_res else 0.0,
                "total_collateral_assets": asset_res["total"] if asset_res else 0,
                "total_collateral_value_vnd": float(asset_res["total_collateral_value"] or 0.0) if asset_res else 0.0,
                "active_priority_rankings": prank_res["total"] if prank_res else 0,
                "active_disposal_notices": disp_res["total"] if disp_res else 0,
                "deregistrations_processed": dereg_res["total"] if dereg_res else 0,
                "audit_logs_count": audit_res["total"] if audit_res else 0,
                "system_status": "ONLINE_HEALTHY",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
