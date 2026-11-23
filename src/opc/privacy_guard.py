"""VN Personal Data Protection (Law 91/2025/QH15, superseding Decree 13/2023/NĐ-CP) consent, DSAR erasure with accounting retention, PII redaction, and tenant DB guard."""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any, Final

from src.core.privacy_engine import PrivacyEngine
from src.opc.dsar_identity import (
    SubjectRef as SubjectRef,
    _field_matches_ref,
    extract_subject_redaction_tokens,
    json_blob_matches_subject,
    memo_matches_run_id,
    parse_dsar_subject,
)
from src.opc.dsar_redaction import (
    RedactionResult as RedactionResult,
    _expand_subject_tokens,
    _fold_vietnamese_ascii as _fold_vietnamese_ascii,
    _PII_PATTERNS as _PII_PATTERNS,
    _redact_memo_tokens,
    redact_vietnamese_pii as redact_vietnamese_pii,
)
from src.opc.verifier import MIN_EXTRACTION_CONFIDENCE, HaltForHumanError, compact_conversation_preserving_moim, verify_confidence_and_math

_TENANT_SLUG_RE: Final[re.Pattern[str]] = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{1,62}$")

class ConsentRequiredError(PermissionError):
    """Raised when VN Personal Data Protection (Law 91/2025/QH15) consent is missing or withdrawn."""


class TenantIsolationError(PermissionError):
    """Raised on invalid tenant slug or cross-tenant SQLite path traversal."""


def resolve_tenant_db_path(base_dir: str | Path, tenant_id: str, active_tenant_id: str | None = None) -> Path:
    """Resolve isolated {tenant_id}.db inside base_dir with strict slug & traversal checks."""
    slug = (tenant_id or "").strip()
    if not _TENANT_SLUG_RE.match(slug):
        raise TenantIsolationError(f"Invalid tenant_id '{tenant_id}' (rejected by slug policy).")
    if active_tenant_id is not None and active_tenant_id.strip() != slug:
        raise TenantIsolationError(f"Cross-tenant access denied: caller '{active_tenant_id}' requested '{slug}'.")
    root = Path(base_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    target = (root / f"{slug}.db").resolve()
    if target.parent != root:
        raise TenantIsolationError(f"Path traversal blocked for tenant_id '{tenant_id}'.")
    return target


class PilotPrivacyGuard:
    """VN PDPL (Law 91/2025/QH15, superseding Decree 13/2023/NĐ-CP) consent & DSAR erasure with accounting retention."""

    def __init__(self, privacy_db_path: str | Path, opc_db_path: str | Path | None = None) -> None:
        self.engine = PrivacyEngine(db_path=Path(privacy_db_path))
        self.opc_db_path = Path(opc_db_path) if opc_db_path is not None else None

    def record_subject_consent(self, subject_id: str, purpose: str = "zalo_lead_to_quote", consent_given: bool = True) -> dict[str, Any]:
        return self.engine.record_consent(subject_id.strip(), purpose, "Luật BVDLCN 91/2025/QH15 (thay thế NĐ 13/2023/NĐ-CP)", consent_given=consent_given)

    def has_active_consent(self, subject_id: str, purpose: str = "zalo_lead_to_quote") -> bool:
        with sqlite3.connect(str(self.engine.db_path), timeout=10.0) as conn:
            row = conn.execute(
                "SELECT consent_given, withdrawn_at FROM consent_log WHERE subject_id = ? AND purpose = ? ORDER BY recorded_at DESC LIMIT 1",
                (subject_id.strip(), purpose),
            ).fetchone()
        return bool(row and row[0] and row[1] is None)

    def require_consent(self, subject_id: str, purpose: str = "zalo_lead_to_quote") -> None:
        if not self.has_active_consent(subject_id, purpose=purpose):
            raise ConsentRequiredError(f"Active VN PDPL (Law 91/2025/QH15) consent required for '{subject_id}' ({purpose}).")

    def withdraw_subject_consent(self, subject_id: str, purpose: str = "zalo_lead_to_quote") -> dict[str, Any]:
        return self.engine.withdraw_consent(subject_id.strip(), purpose=purpose)

    def erase_subject_under_72h(
        self, subject_id: str, *, subject_type: str | None = None,
    ) -> dict[str, Any]:
        """Execute tenant-scoped DSAR RIGHT_TO_DELETE using exact structured identity matching, preserving financial legal holds."""
        ref = parse_dsar_subject(subject_id, subject_type=subject_type)
        opc_erased, consent_erased, financial_retained = 0, 0, 0
        run_ids: list[str] = []
        subject_tokens: set[str] = {ref.raw, ref.normalized}
        if self.opc_db_path is not None and self.opc_db_path.exists():
            with sqlite3.connect(str(self.opc_db_path), timeout=10.0) as conn:
                for rid, raw_inp, raw_act in conn.execute("SELECT run_id, proposal_input_json, action_payload_json FROM opc_runs").fetchall():
                    inp_match, parsed_inp = json_blob_matches_subject(raw_inp, ref)
                    if inp_match or json_blob_matches_subject(raw_act, ref)[0]:
                        run_ids.append(str(rid))
                        subject_tokens.update(extract_subject_redaction_tokens(parsed_inp, ref))
            # 1. Redact/purge VietQR FIRST so a crash before OPC commit never strands unredacted financial PII
            vqr_db = self.opc_db_path.parent / f"{self.opc_db_path.stem}_vietqr.db"
            if vqr_db.exists() and run_ids:
                ordered_tokens = _expand_subject_tokens(subject_tokens)
                with sqlite3.connect(str(vqr_db), timeout=10.0) as vconn:
                    qr_del = [
                        (qr_id,) for qr_id, memo in vconn.execute("SELECT qr_id, memo FROM qr_codes").fetchall()
                        if any(memo == f"OPC {rid}" or memo_matches_run_id(memo, rid) for rid in run_ids)
                    ]
                    if qr_del:
                        opc_erased += max(0, vconn.executemany("DELETE FROM qr_codes WHERE qr_id = ?", qr_del).rowcount)
                    tx_rows = {
                        str(tid): str(memo or "")
                        for tid, matched_oid, memo in vconn.execute("SELECT transaction_id, matched_order_id, memo FROM transactions").fetchall()
                        if matched_oid in run_ids or any(memo_matches_run_id(memo, rid) for rid in run_ids)
                    }
                    for tid, memo in tx_rows.items():
                        sanitized = _redact_memo_tokens(memo, ordered_tokens)
                        if sanitized != memo:
                            vconn.execute("UPDATE transactions SET memo = ? WHERE transaction_id = ?", (sanitized, tid))
                    financial_retained = len(tx_rows)
                    vconn.commit()
            # 2. Erase matched OPC rows + orphan rows in actions/checkpoints/journal/revocations atomically
            with sqlite3.connect(str(self.opc_db_path), timeout=10.0) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                tbls = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
                if run_ids:
                    rp = [(rid,) for rid in run_ids]
                    for sql in ("DELETE FROM opc_approvals WHERE run_id = ?", "DELETE FROM opc_actions WHERE run_id = ?", "DELETE FROM opc_runs WHERE run_id = ?"):
                        opc_erased += max(0, conn.executemany(sql, rp).rowcount)
                    for tbl, sql in (
                        ("opc_card_revocations", "DELETE FROM opc_card_revocations WHERE run_id = ?"),
                        ("opc_side_effect_journal", "DELETE FROM opc_side_effect_journal WHERE thread_id = ?"),
                        ("opc_graph_checkpoints", "DELETE FROM opc_graph_checkpoints WHERE thread_id = ?"),
                    ):
                        if tbl in tbls:
                            opc_erased += max(0, conn.executemany(sql, rp).rowcount)
                for tbl, sel_sql, del_sql in (
                    ("opc_actions", "SELECT idempotency_key, payload_json FROM opc_actions", "DELETE FROM opc_actions WHERE idempotency_key = ?"),
                    ("opc_graph_checkpoints", "SELECT thread_id, state_json FROM opc_graph_checkpoints", "DELETE FROM opc_graph_checkpoints WHERE thread_id = ?"),
                    ("opc_side_effect_journal", "SELECT idempotency_key, result_json FROM opc_side_effect_journal", "DELETE FROM opc_side_effect_journal WHERE idempotency_key = ?"),
                ):
                    if tbl in tbls:
                        orphans = [(str(r[0]),) for r in conn.execute(sel_sql).fetchall() if json_blob_matches_subject(r[1], ref)[0]]
                        if orphans:
                            opc_erased += max(0, conn.executemany(del_sql, orphans).rowcount)
                conn.commit()
        # 3. Record DSAR and purge tenant-scoped zalo/consent_log variants (never touching shared cross-tenant zalo.db)
        zalo_db = (self.opc_db_path.parent / f"{self.opc_db_path.stem}_zalo.db") if self.opc_db_path else (self.engine.db_path.parent / f"{self.engine.db_path.stem}_zalo.db")
        if zalo_db.is_file():
            with sqlite3.connect(str(zalo_db), timeout=10.0) as zconn:
                ztbls = {r[0] for r in zconn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
                uids = {str(u) for u, ph in (zconn.execute("SELECT user_id, phone FROM followers").fetchall() if "followers" in ztbls else []) if _field_matches_ref(u, ref) or _field_matches_ref(ph, ref)}
                uids |= {str(u) for (u,) in (zconn.execute("SELECT DISTINCT user_id FROM messages").fetchall() if "messages" in ztbls else []) if _field_matches_ref(u, ref)}
                if uids:
                    up = [(u,) for u in sorted(uids)]
                    if "followers" in ztbls:
                        opc_erased += max(0, zconn.executemany("DELETE FROM followers WHERE user_id = ?", up).rowcount)
                    if "messages" in ztbls:
                        opc_erased += max(0, zconn.executemany("DELETE FROM messages WHERE user_id = ?", up).rowcount)
                    zconn.commit()
        dsar = self.engine.handle_dsar_request("RIGHT_TO_DELETE", subject_id=ref.normalized, save=True, zalo_db_path=zalo_db, match_by_name=False)
        with sqlite3.connect(str(self.engine.db_path), timeout=10.0) as pconn:
            cid_del = [(str(cid),) for cid, sid in pconn.execute("SELECT consent_id, subject_id FROM consent_log").fetchall() if _field_matches_ref(sid, ref)]
            if cid_del:
                consent_erased = max(0, pconn.executemany("DELETE FROM consent_log WHERE consent_id = ?", cid_del).rowcount)
            prior_del = [(str(rid),) for rid, sid in pconn.execute("SELECT request_id, subject_id FROM dsar_requests WHERE request_id != ?", (dsar["request_id"],)).fetchall() if _field_matches_ref(sid, ref)]
            if prior_del:
                consent_erased += max(0, pconn.executemany("DELETE FROM dsar_requests WHERE request_id = ?", prior_del).rowcount)
            total_erased = int((dsar.get("erasure") or {}).get("total_erased", 0)) + opc_erased + consent_erased
            if total_erased > 0 and dsar.get("status") != "COMPLETED":
                dsar["status"] = "COMPLETED"
                pconn.execute("UPDATE dsar_requests SET status = 'COMPLETED' WHERE request_id = ?", (dsar["request_id"],))
            pconn.commit()
        dsar.update({
            "opc_rows_erased": opc_erased, "consent_rows_erased": consent_erased, "total_erased_combined": total_erased,
            "matched_subject_kind": ref.kind, "matched_run_ids": run_ids,
            "vietqr_financial_records_retained": financial_retained, "financial_legal_hold_preserved": True,
            "legal_review_required": True, "retention_policy_status": "PENDING_COUNSEL_DETERMINATION",
            "financial_retention_basis": "Law on Accounting 88/2015/QH13 Art. 41 & Tax Administration Law 38/2019/QH14 (PII redacted, ledger preserved; counsel sign-off required)",
            "legal_framework": "VN PDPL 91/2025/QH15 (superseding Decree 13/2023/NĐ-CP)",
        })
        return dsar


__all__ = [
    "MIN_EXTRACTION_CONFIDENCE", "ConsentRequiredError", "HaltForHumanError", "PilotPrivacyGuard", "RedactionResult",
    "TenantIsolationError", "compact_conversation_preserving_moim", "redact_vietnamese_pii", "resolve_tenant_db_path", "verify_confidence_and_math",
]
