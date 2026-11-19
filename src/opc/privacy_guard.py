"""VN Personal Data Protection (Law 91/2025/QH15, superseding Decree 13/2023/NĐ-CP) consent, DSAR erasure with accounting retention, PII redaction, and tenant DB guard."""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Final

from src.core.privacy_engine import PrivacyEngine
from src.opc.dsar_redaction import (
    RedactionResult as RedactionResult,
    _escape_like,
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

    def erase_subject_under_72h(self, subject_id: str) -> dict[str, Any]:
        """Execute DSAR RIGHT_TO_DELETE (internal 72h operational target; statutory review required) preserving accounting records."""
        clean_sub = (subject_id or "").strip()
        if len(clean_sub) < 3 or not any(ch.isalnum() for ch in clean_sub):
            raise ValueError(f"Invalid subject_id '{subject_id}' for DSAR erasure.")
        dsar = self.engine.handle_dsar_request("RIGHT_TO_DELETE", subject_id=clean_sub)
        opc_erased = 0
        escaped = clean_sub.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like_pat = f"%{escaped}%"
        run_ids: list[str] = []
        subject_tokens: set[str] = {clean_sub}
        if self.opc_db_path is not None and self.opc_db_path.exists():
            with sqlite3.connect(str(self.opc_db_path), timeout=10.0) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                matched_runs = conn.execute("SELECT run_id, proposal_input_json FROM opc_runs WHERE proposal_input_json LIKE ? ESCAPE '\\' OR action_payload_json LIKE ? ESCAPE '\\'", (like_pat, like_pat)).fetchall()
                run_ids = [r[0] for r in matched_runs]
                for _, raw_inp in matched_runs:
                    inp = json.loads(raw_inp) if isinstance(raw_inp, str) and raw_inp.startswith("{") else {}
                    subject_tokens.update(
                        v for k in ("client_name", "sender_name", "sender_id", "client_contact")
                        if (raw := inp.get(k)) is not None and len(v := str(raw).strip()) >= 3
                    )
                if run_ids:
                    rows_param = [(rid,) for rid in run_ids]
                    c0 = conn.executemany("DELETE FROM opc_approvals WHERE run_id = ?", rows_param)
                    c1 = conn.executemany("DELETE FROM opc_actions WHERE run_id = ?", rows_param)
                    c2 = conn.executemany("DELETE FROM opc_runs WHERE run_id = ?", rows_param)
                    opc_erased += max(0, c0.rowcount) + max(0, c1.rowcount) + max(0, c2.rowcount)
                c3 = conn.execute("DELETE FROM opc_actions WHERE payload_json LIKE ? ESCAPE '\\'", (like_pat,))
                opc_erased += max(0, c3.rowcount)
                tbls = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
                if "opc_side_effect_journal" in tbls:
                    if run_ids:
                        opc_erased += max(0, conn.executemany("DELETE FROM opc_side_effect_journal WHERE thread_id = ?", [(r,) for r in run_ids]).rowcount)
                    opc_erased += max(0, conn.execute("DELETE FROM opc_side_effect_journal WHERE result_json LIKE ? ESCAPE '\\'", (like_pat,)).rowcount)
                if "opc_graph_checkpoints" in tbls:
                    if run_ids:
                        opc_erased += max(0, conn.executemany("DELETE FROM opc_graph_checkpoints WHERE thread_id = ?", [(r,) for r in run_ids]).rowcount)
                    opc_erased += max(0, conn.execute("DELETE FROM opc_graph_checkpoints WHERE state_json LIKE ? ESCAPE '\\'", (like_pat,)).rowcount)
                conn.commit()
            vqr_db = self.opc_db_path.parent / f"{self.opc_db_path.stem}_vietqr.db"
            financial_retained = 0
            if vqr_db.exists():
                ordered_tokens = _expand_subject_tokens(subject_tokens)
                with sqlite3.connect(str(vqr_db), timeout=10.0) as vconn:
                    for rid in run_ids:
                        rid_pat = f"%{_escape_like(rid)}%"
                        opc_erased += max(0, vconn.execute("DELETE FROM qr_codes WHERE memo = ? OR memo LIKE ? ESCAPE '\\'", (f"OPC {rid}", rid_pat)).rowcount)
                    opc_erased += max(0, vconn.execute("DELETE FROM qr_codes WHERE memo LIKE ? ESCAPE '\\'", (like_pat,)).rowcount)
                    tx_rows: dict[str, str] = {r[0]: str(r[1] or "") for r in vconn.execute("SELECT transaction_id, memo FROM transactions WHERE memo LIKE ? ESCAPE '\\'", (like_pat,)).fetchall()}
                    for rid in run_ids:
                        rid_pat = f"%{_escape_like(rid)}%"
                        for tid, memo in vconn.execute("SELECT transaction_id, memo FROM transactions WHERE matched_order_id = ? OR memo LIKE ? ESCAPE '\\'", (rid, rid_pat)).fetchall():
                            tx_rows[tid] = str(memo or "")
                    for tid, memo in tx_rows.items():
                        sanitized = _redact_memo_tokens(memo, ordered_tokens)
                        if sanitized != memo:
                            vconn.execute("UPDATE transactions SET memo = ? WHERE transaction_id = ?", (sanitized, tid))
                    financial_retained = len(tx_rows)
                    vconn.commit()
        else:
            financial_retained = 0
        total_erased = int((dsar.get("erasure") or {}).get("total_erased", 0)) + opc_erased
        if total_erased > 0 and dsar.get("status") != "COMPLETED":
            dsar["status"] = "COMPLETED"
            with sqlite3.connect(str(self.engine.db_path), timeout=10.0) as pconn:
                pconn.execute("UPDATE dsar_requests SET status = 'COMPLETED' WHERE request_id = ?", (dsar["request_id"],))
                pconn.commit()
        dsar.update({
            "opc_rows_erased": opc_erased, "total_erased_combined": total_erased,
            "vietqr_financial_records_retained": financial_retained, "legal_review_required": True,
            "financial_retention_basis": "Law on Accounting 88/2015/QH13 Art. 41 & Tax Administration Law 38/2019/QH14 (PII redacted, ledger preserved)",
            "legal_framework": "VN PDPL 91/2025/QH15 (superseding Decree 13/2023/NĐ-CP)",
        })
        return dsar


__all__ = [
    "MIN_EXTRACTION_CONFIDENCE", "ConsentRequiredError", "HaltForHumanError", "PilotPrivacyGuard", "RedactionResult",
    "TenantIsolationError", "compact_conversation_preserving_moim", "redact_vietnamese_pii", "resolve_tenant_db_path", "verify_confidence_and_math",
]
