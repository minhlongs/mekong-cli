# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""SQLite WAL Evidence Store & Two-Tier Gate Evaluation Engine.

Provides persistent, atomic storage for:
- ``cli_runs``: Command execution runs, inputs, outputs, timestamps, exit codes.
- ``execution_receipts``: Signed Tier 1 receipts with input/output SHA256 hashes.
- ``company_milestone_gates``: Tier 2 L0–L5 enterprise milestone gates.
- ``cfo_double_entry_ledger``: Immutable double-entry financial audit journal.

Adheres strictly to ``tests/test_core_boundary.py`` (standard library only).
"""

from __future__ import annotations

import datetime
import json
import pathlib
import sqlite3
import typing

DEFAULT_EVIDENCE_DB = pathlib.Path(".mekong") / "cli_promise_evidence.db"

# Canonical L0–L5 Company Milestone Gate Definitions
CANONICAL_GATES: list[dict[str, typing.Any]] = [
    {
        "gate_id": "company-blueprint",
        "layer_id": "L0",
        "name": "Ý Chí Sáng Lập & Bản Thiết Kế Doanh Nghiệp (L0)",
        "department_id": "ceo-command",
        "owner_agent": "planner",
        "required_evidence_type": "FOUNDER_INTENT_BLUEPRINT",
        "description": "Bản thiết kế công ty 1 người và bộ quy tắc phân quyền điều hành.",
    },
    {
        "gate_id": "offer-validated",
        "layer_id": "L1",
        "name": "Xác Thực Thị Trường & Đóng Gói Offer (L1)",
        "department_id": "product-strategy",
        "owner_agent": "business-analyst",
        "required_evidence_type": "MARKET_ICP_OFFER_CONTRACT",
        "description": "Chân dung ICP, định giá dịch vụ và phân tích rào cản đối thủ.",
    },
    {
        "gate_id": "mvp-live",
        "layer_id": "L2",
        "name": "Nhà Máy Kỹ Thuật Sản Xuất Live (L2)",
        "department_id": "engineering-factory",
        "owner_agent": "fullstack-developer",
        "required_evidence_type": "PRODUCTION_BUILD_VERIFICATION",
        "description": "Mã nguồn sản xuất Next.js, API backend và kiểm toán tuân thủ.",
    },
    {
        "gate_id": "first-revenue",
        "layer_id": "L3",
        "name": "Dòng Doanh Thu Lặp Lại & Quyết Toán Thuế (L3)",
        "department_id": "sales-revenue",
        "owner_agent": "business-analyst",
        "required_evidence_type": "RECONCILED_BANKING_TRANSACTION",
        "description": "Doanh thu thực tế, hóa đơn TT78, sổ sách kế toán và quyết toán thuế.",
    },
    {
        "gate_id": "fulfillment-stable",
        "layer_id": "L4",
        "name": "Bàn Giao & Vận Hành Chuyên Ngành (L4)",
        "department_id": "customer-success",
        "owner_agent": "project-manager",
        "required_evidence_type": "CLIENT_DELIVERY_ACCEPTANCE",
        "description": "Nghiệm thu bàn giao nghiệp vụ, CSKH Zalo OA và retention.",
    },
    {
        "gate_id": "scale-ready",
        "layer_id": "L5",
        "name": "Kho Tri Thức & Sẵn Sàng Nhân Bản (L5)",
        "department_id": "knowledge-memory",
        "owner_agent": "docs-manager",
        "required_evidence_type": "ENTERPRISE_SOP_CLONE_SYNC",
        "description": "Đóng gói toàn bộ SOP, sổ cái và kiến trúc hướng mốc $1M ARR.",
    },
]


class CliEvidenceStore:
    """SQLite WAL storage for command executions, signed receipts, and company gates."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        if db_path is None:
            base_dir = pathlib.Path(".mekong")
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = base_dir / "cli_promise_evidence.db"
        else:
            self.db_path = pathlib.Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cli_runs (
                    run_id TEXT PRIMARY KEY,
                    command_id TEXT NOT NULL,
                    cluster TEXT NOT NULL,
                    department_id TEXT NOT NULL,
                    layer_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_payload TEXT NOT NULL,
                    output_payload TEXT NOT NULL,
                    error_message TEXT,
                    duration_ms INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_receipts (
                    receipt_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    command_id TEXT NOT NULL,
                    department_id TEXT NOT NULL,
                    layer_id TEXT NOT NULL,
                    input_sha256 TEXT NOT NULL,
                    output_sha256 TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES cli_runs(run_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS company_milestone_gates (
                    gate_id TEXT PRIMARY KEY,
                    layer_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    department_id TEXT NOT NULL,
                    owner_agent TEXT NOT NULL,
                    status TEXT NOT NULL,
                    evidence_ref TEXT,
                    reconciled_transaction_id TEXT,
                    unlocked_at TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cfo_double_entry_ledger (
                    journal_id TEXT PRIMARY KEY,
                    run_id TEXT,
                    account_code TEXT NOT NULL,
                    account_name TEXT NOT NULL,
                    debit_amount INTEGER NOT NULL DEFAULT 0,
                    credit_amount INTEGER NOT NULL DEFAULT 0,
                    memo TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

            # Seed default canonical gates if not present
            cursor = conn.execute("SELECT COUNT(*) AS cnt FROM company_milestone_gates")
            if cursor.fetchone()["cnt"] == 0:
                now = datetime.datetime.now(datetime.timezone.utc).isoformat()
                for g in CANONICAL_GATES:
                    conn.execute(
                        """
                        INSERT INTO company_milestone_gates
                        (gate_id, layer_id, name, department_id, owner_agent, status, evidence_ref, reconciled_transaction_id, unlocked_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            g["gate_id"],
                            g["layer_id"],
                            g["name"],
                            g["department_id"],
                            g["owner_agent"],
                            "LOCKED",  # Tier 2 gates start LOCKED until externally verified
                            None,
                            None,
                            None,
                            now,
                        ),
                    )
                conn.commit()

    def record_run(
        self,
        run_id: str,
        command_id: str,
        cluster: str,
        department_id: str,
        layer_id: str,
        status: str,
        input_payload: dict[str, typing.Any],
        output_payload: dict[str, typing.Any],
        error_message: str | None = None,
        duration_ms: int = 0,
    ) -> None:
        """Record a single command execution into cli_runs."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cli_runs
                (run_id, command_id, cluster, department_id, layer_id, status, input_payload, output_payload, error_message, duration_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    command_id,
                    cluster,
                    department_id,
                    layer_id,
                    status,
                    json.dumps(input_payload, ensure_ascii=False),
                    json.dumps(output_payload, ensure_ascii=False),
                    error_message,
                    duration_ms,
                    now,
                ),
            )
            conn.commit()

    def record_receipt(self, receipt: dict[str, typing.Any]) -> None:
        """Store a signed CommandExecutionReceipt."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        receipt_id = f"RCPT-{receipt['run_id']}"
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO execution_receipts
                (receipt_id, run_id, command_id, department_id, layer_id, input_sha256, output_sha256, signature, receipt_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt_id,
                    receipt["run_id"],
                    receipt["command_id"],
                    receipt["department_id"],
                    receipt["layer_id"],
                    receipt["input_sha256"],
                    receipt["output_sha256"],
                    receipt["signature"],
                    json.dumps(receipt, ensure_ascii=False),
                    now,
                ),
            )
            conn.commit()

    def get_run(self, run_id: str) -> dict[str, typing.Any] | None:
        """Retrieve run details and attached receipt by run_id."""
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM cli_runs WHERE run_id = ?", (run_id,))
            row = cur.fetchone()
            if not row:
                return None
            res = dict(row)
            res["input_payload"] = json.loads(res["input_payload"])
            res["output_payload"] = json.loads(res["output_payload"])

            rcpt_cur = conn.execute("SELECT * FROM execution_receipts WHERE run_id = ?", (run_id,))
            rcpt_row = rcpt_cur.fetchone()
            if rcpt_row:
                res["receipt"] = json.loads(rcpt_row["receipt_json"])
            else:
                res["receipt"] = None
            return res

    def list_gates(self) -> list[dict[str, typing.Any]]:
        """List all company milestone gates and current lock status."""
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM company_milestone_gates ORDER BY layer_id ASC")
            return [dict(r) for r in cur.fetchall()]

    def unlock_gate_with_reconciliation(
        self,
        gate_id: str,
        transaction_id: str,
        evidence_ref: str,
    ) -> bool:
        """Unlock a Tier 2 Company Milestone Gate with external reconciliation proof."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                UPDATE company_milestone_gates
                SET status = 'SEALED_VERIFIED',
                    reconciled_transaction_id = ?,
                    evidence_ref = ?,
                    unlocked_at = ?,
                    updated_at = ?
                WHERE gate_id = ?
                """,
                (transaction_id, evidence_ref, now, now, gate_id),
            )
            conn.commit()
            return cur.rowcount > 0

    def record_journal_entry(
        self,
        journal_id: str,
        run_id: str | None,
        account_code: str,
        account_name: str,
        debit: int,
        credit: int,
        memo: str,
    ) -> None:
        """Add line to double-entry financial audit journal."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO cfo_double_entry_ledger
                (journal_id, run_id, account_code, account_name, debit_amount, credit_amount, memo, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (journal_id, run_id, account_code, account_name, debit, credit, memo, now),
            )
            conn.commit()
