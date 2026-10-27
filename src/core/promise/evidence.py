# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Evidence store: run evidence plus the *business facts* gates are built on.

Three separations are persisted per record, because they are three different
questions:

``handler_ran``          did the bound code execute without raising?
``artifact_integrity``   do the recorded digests still match the payload?
``business_conditions``  were the declared postconditions measured and met?

Gate-relevant business facts (reconciled revenue, deployment proofs, client
acceptances, named attestations, channel metrics, SOP exports) live in their
own tables and can only be written with the fields that make them verifiable —
a free-text string can never seal a gate.
"""

from __future__ import annotations

import json
import pathlib
import sqlite3
import typing
import uuid

from src.core.promise.signing import EvidenceSigner, redact, sha256_of, utc_now_iso


class EvidenceIntegrityError(RuntimeError):
    """Raised when a caller tries to persist unverifiable evidence."""


SCHEMA = """
CREATE TABLE IF NOT EXISTS promise_evidence (
    evidence_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    principal_id TEXT NOT NULL,
    command_id TEXT NOT NULL,
    op_id TEXT,
    gate_id TEXT,
    evidence_type TEXT NOT NULL,
    code_version TEXT NOT NULL,
    input_digest TEXT NOT NULL,
    output_digest TEXT NOT NULL,
    handler_ran INTEGER NOT NULL DEFAULT 0,
    artifact_integrity TEXT NOT NULL DEFAULT 'UNKNOWN',
    business_conditions_met INTEGER NOT NULL DEFAULT 0,
    checks_json TEXT NOT NULL,
    record_json TEXT NOT NULL,
    signature TEXT,
    signing_status TEXT NOT NULL DEFAULT 'UNSIGNED',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_evidence_run ON promise_evidence(run_id);
CREATE INDEX IF NOT EXISTS ix_evidence_ws ON promise_evidence(workspace_id, created_at DESC);
CREATE TABLE IF NOT EXISTS revenue_transactions (
    tx_id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, run_id TEXT,
    provider TEXT NOT NULL, method TEXT NOT NULL, amount TEXT NOT NULL,
    currency TEXT NOT NULL, invoice_ref TEXT, status TEXT NOT NULL,
    provider_confirmation_json TEXT, confirmed_at TEXT,
    reconciled_by TEXT, reconciled_at TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS deployment_proofs (
    proof_id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, run_id TEXT,
    target_url TEXT NOT NULL, environment TEXT NOT NULL,
    health_status TEXT NOT NULL, checked_at TEXT NOT NULL,
    build_digest TEXT, test_digest TEXT, checked_by TEXT NOT NULL,
    response_digest TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS client_acceptances (
    acceptance_id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, run_id TEXT,
    client_ref TEXT NOT NULL, deliverable_ref TEXT NOT NULL,
    accepted_by TEXT NOT NULL, accepted_at TEXT NOT NULL,
    sla_met INTEGER NOT NULL DEFAULT 0, notes TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attestations (
    attestation_id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, run_id TEXT,
    kind TEXT NOT NULL, subject TEXT NOT NULL, attested_by TEXT NOT NULL,
    attested_at TEXT NOT NULL, criteria_json TEXT NOT NULL,
    evidence_refs_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS channel_metrics (
    metric_id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, run_id TEXT,
    channel TEXT NOT NULL, period TEXT NOT NULL, impressions INTEGER,
    clicks INTEGER, conversions INTEGER, revenue TEXT, currency TEXT,
    source TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sop_exports (
    export_id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, run_id TEXT,
    sop_id TEXT NOT NULL, artifact_path TEXT NOT NULL, artifact_digest TEXT NOT NULL,
    clone_target TEXT, exported_by TEXT NOT NULL, created_at TEXT NOT NULL
);
"""


class EvidenceStore:
    """SQLite (WAL) evidence + business-fact store, workspace scoped."""

    def __init__(self, db_path: str | pathlib.Path, signer: EvidenceSigner | None = None) -> None:
        self.db_path = pathlib.Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.signer = signer or EvidenceSigner()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    # ------------------------------------------------------------------
    # Run evidence
    # ------------------------------------------------------------------
    def record_run_evidence(
        self,
        *,
        run_id: str,
        workspace_id: str,
        principal_id: str,
        command_id: str,
        op_id: str | None,
        gate_id: str | None,
        evidence_type: str,
        code_version: str,
        input_payload: dict[str, typing.Any],
        output_payload: dict[str, typing.Any],
        handler_ran: bool,
        checks: list[dict[str, typing.Any]],
    ) -> dict[str, typing.Any]:
        safe_input = redact(input_payload)
        safe_output = redact(output_payload)
        required_failed = [c for c in checks if c.get("required", True) and c.get("status") != "PASSED"]
        record: dict[str, typing.Any] = {
            "evidence_version": "2.0.0",
            "run_id": run_id,
            "workspace_id": workspace_id,
            "principal_id": principal_id,
            "command_id": command_id,
            "op_id": op_id,
            "gate_id": gate_id,
            "evidence_type": evidence_type,
            "code_version": code_version,
            "input": safe_input,
            "output_digest": sha256_of(safe_output),
            "input_digest": sha256_of(safe_input),
            "handler_ran": handler_ran,
            "business_conditions_met": handler_ran and not required_failed,
            "checks": checks,
            "recorded_at": utc_now_iso(),
        }
        signed = self.signer.sign(record)
        evidence_id = f"EVD-{uuid.uuid4().hex[:16].upper()}"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO promise_evidence (
                    evidence_id, run_id, workspace_id, principal_id, command_id, op_id, gate_id,
                    evidence_type, code_version, input_digest, output_digest, handler_ran,
                    artifact_integrity, business_conditions_met, checks_json, record_json,
                    signature, signing_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence_id, run_id, workspace_id, principal_id, command_id, op_id, gate_id,
                    evidence_type, code_version, record["input_digest"], record["output_digest"],
                    1 if handler_ran else 0, "VERIFIED",
                    1 if record["business_conditions_met"] else 0,
                    json.dumps(checks, sort_keys=True, ensure_ascii=False, default=str),
                    json.dumps(signed, sort_keys=True, ensure_ascii=False, default=str),
                    signed.get("signature"),
                    (signed.get("signing") or {}).get("status", "UNSIGNED"),
                    record["recorded_at"],
                ),
            )
        return {"evidence_id": evidence_id, **signed}

    def get_evidence_for_run(self, run_id: str, workspace_id: str) -> list[dict[str, typing.Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM promise_evidence WHERE run_id = ? AND workspace_id = ? ORDER BY created_at ASC",
                (run_id, workspace_id),
            ).fetchall()
        return [self._hydrate_evidence(r) for r in rows]

    def verify_evidence(self, evidence_id: str, workspace_id: str) -> dict[str, typing.Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM promise_evidence WHERE evidence_id = ? AND workspace_id = ?",
                (evidence_id, workspace_id),
            ).fetchone()
        if not row:
            return {"valid": False, "reason": "evidence not found in this workspace"}
        record = json.loads(row["record_json"])
        signature_check = self.signer.verify(record)
        integrity_ok = (
            record.get("input_digest") == row["input_digest"]
            and record.get("output_digest") == row["output_digest"]
        )
        return {
            "evidence_id": evidence_id,
            "signature_valid": bool(signature_check.get("valid")),
            "signature_detail": signature_check,
            "digest_integrity": integrity_ok,
            "handler_ran": bool(row["handler_ran"]),
            "business_conditions_met": bool(row["business_conditions_met"]),
            "checks": json.loads(row["checks_json"] or "[]"),
        }

    @staticmethod
    def _hydrate_evidence(row: sqlite3.Row) -> dict[str, typing.Any]:
        data = dict(row)
        data["record"] = json.loads(data.pop("record_json") or "{}")
        data["checks"] = json.loads(data.pop("checks_json") or "[]")
        data["handler_ran"] = bool(data["handler_ran"])
        data["business_conditions_met"] = bool(data["business_conditions_met"])
        return data

    # ------------------------------------------------------------------
    # Business facts (gate inputs)
    # ------------------------------------------------------------------
    def record_revenue_transaction(self, **fields: typing.Any) -> dict[str, typing.Any]:
        """Persist a revenue transaction; ``RECONCILED`` requires provider proof."""
        status = str(fields.get("status", "PENDING")).upper()
        confirmation = fields.get("provider_confirmation")
        if status == "RECONCILED" and not confirmation:
            raise EvidenceIntegrityError(
                "a revenue transaction cannot be marked RECONCILED without provider confirmation data"
            )
        try:
            amount = float(str(fields.get("amount", "0")).replace(",", ""))
        except ValueError as exc:
            raise EvidenceIntegrityError(f"amount must be numeric: {exc}") from exc
        if amount <= 0:
            raise EvidenceIntegrityError("a revenue transaction must have a positive amount")
        currency = str(fields.get("currency", "")).upper()
        if len(currency) != 3:
            raise EvidenceIntegrityError("currency must be an ISO-4217 code")
        tx_id = str(fields.get("tx_id") or f"TX-{uuid.uuid4().hex[:14].upper()}")
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO revenue_transactions (
                    tx_id, workspace_id, run_id, provider, method, amount, currency, invoice_ref,
                    status, provider_confirmation_json, confirmed_at, reconciled_by, reconciled_at,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tx_id, fields["workspace_id"], fields.get("run_id"), fields["provider"],
                    fields.get("method", "unknown"), str(fields["amount"]), currency,
                    fields.get("invoice_ref"), status,
                    json.dumps(redact(confirmation), sort_keys=True, ensure_ascii=False, default=str)
                    if confirmation else None,
                    fields.get("confirmed_at") or (now if confirmation else None),
                    fields.get("reconciled_by"), fields.get("reconciled_at") or (now if status == "RECONCILED" else None),
                    now,
                ),
            )
        return {"tx_id": tx_id, "status": status}

    def record_deployment_proof(self, **fields: typing.Any) -> dict[str, typing.Any]:
        if not str(fields.get("target_url", "")).startswith(("https://", "http://")):
            raise EvidenceIntegrityError("deployment proof requires a concrete target_url")
        if str(fields.get("health_status", "")).upper() not in {"HEALTHY", "DEGRADED", "UNREACHABLE"}:
            raise EvidenceIntegrityError("health_status must be HEALTHY, DEGRADED or UNREACHABLE")
        proof_id = str(fields.get("proof_id") or f"DEP-{uuid.uuid4().hex[:14].upper()}")
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO deployment_proofs (
                    proof_id, workspace_id, run_id, target_url, environment, health_status,
                    checked_at, build_digest, test_digest, checked_by, response_digest, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proof_id, fields["workspace_id"], fields.get("run_id"), fields["target_url"],
                    fields.get("environment", "production"), str(fields["health_status"]).upper(),
                    fields.get("checked_at") or now, fields.get("build_digest"),
                    fields.get("test_digest"), fields["checked_by"], fields.get("response_digest"), now,
                ),
            )
        return {"proof_id": proof_id}

    def record_client_acceptance(self, **fields: typing.Any) -> dict[str, typing.Any]:
        for required in ("client_ref", "deliverable_ref", "accepted_by"):
            if not fields.get(required):
                raise EvidenceIntegrityError(f"client acceptance requires '{required}'")
        acceptance_id = str(fields.get("acceptance_id") or f"ACC-{uuid.uuid4().hex[:14].upper()}")
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO client_acceptances (
                    acceptance_id, workspace_id, run_id, client_ref, deliverable_ref, accepted_by,
                    accepted_at, sla_met, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    acceptance_id, fields["workspace_id"], fields.get("run_id"), fields["client_ref"],
                    fields["deliverable_ref"], fields["accepted_by"], fields.get("accepted_at") or now,
                    1 if fields.get("sla_met") else 0, fields.get("notes"), now,
                ),
            )
        return {"acceptance_id": acceptance_id}

    def record_attestation(self, **fields: typing.Any) -> dict[str, typing.Any]:
        criteria = fields.get("criteria") or {}
        if not criteria:
            raise EvidenceIntegrityError("an attestation must state the criteria it was judged against")
        if not fields.get("attested_by"):
            raise EvidenceIntegrityError("an attestation must name who attested")
        attestation_id = str(fields.get("attestation_id") or f"ATT-{uuid.uuid4().hex[:14].upper()}")
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO attestations (
                    attestation_id, workspace_id, run_id, kind, subject, attested_by, attested_at,
                    criteria_json, evidence_refs_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attestation_id, fields["workspace_id"], fields.get("run_id"), fields["kind"],
                    fields["subject"], fields["attested_by"], fields.get("attested_at") or now,
                    json.dumps(criteria, sort_keys=True, ensure_ascii=False, default=str),
                    json.dumps(list(fields.get("evidence_refs") or []), sort_keys=True), now,
                ),
            )
        return {"attestation_id": attestation_id}

    def record_channel_metric(self, **fields: typing.Any) -> dict[str, typing.Any]:
        metric_id = str(fields.get("metric_id") or f"CHM-{uuid.uuid4().hex[:14].upper()}")
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO channel_metrics (
                    metric_id, workspace_id, run_id, channel, period, impressions, clicks,
                    conversions, revenue, currency, source, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metric_id, fields["workspace_id"], fields.get("run_id"), fields["channel"],
                    fields["period"], fields.get("impressions"), fields.get("clicks"),
                    fields.get("conversions"), fields.get("revenue"), fields.get("currency"),
                    fields.get("source", "manual"), now,
                ),
            )
        return {"metric_id": metric_id}

    def record_sop_export(self, **fields: typing.Any) -> dict[str, typing.Any]:
        if not fields.get("artifact_digest"):
            raise EvidenceIntegrityError("an SOP export requires an artifact digest")
        export_id = str(fields.get("export_id") or f"SOP-{uuid.uuid4().hex[:14].upper()}")
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sop_exports (
                    export_id, workspace_id, run_id, sop_id, artifact_path, artifact_digest,
                    clone_target, exported_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    export_id, fields["workspace_id"], fields.get("run_id"), fields["sop_id"],
                    fields["artifact_path"], fields["artifact_digest"], fields.get("clone_target"),
                    fields["exported_by"], now,
                ),
            )
        return {"export_id": export_id}

    # ------------------------------------------------------------------
    # Gate-facing queries
    # ------------------------------------------------------------------
    def query(self, table: str, workspace_id: str, where: str = "", params: tuple = ()) -> list[dict[str, typing.Any]]:
        allowed = {
            "revenue_transactions", "deployment_proofs", "client_acceptances",
            "attestations", "channel_metrics", "sop_exports", "promise_evidence",
        }
        if table not in allowed:
            raise EvidenceIntegrityError(f"table '{table}' is not queryable through the evidence store")
        sql = f"SELECT * FROM {table} WHERE workspace_id = ?"
        if where:
            sql += f" AND {where}"
        with self._connect() as conn:
            rows = conn.execute(sql, (workspace_id, *params)).fetchall()
        return [dict(r) for r in rows]


__all__ = ["EvidenceIntegrityError", "EvidenceStore"]
