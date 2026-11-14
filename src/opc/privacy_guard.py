"""Vietnamese PDPD (Decree 13/2023/NĐ-CP) consent, DSAR <72h erasure, PII redaction, and tenant DB guard."""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from src.core.privacy_engine import PrivacyEngine
from src.opc.verifier import (
    MIN_EXTRACTION_CONFIDENCE,
    HaltForHumanError,
    compact_conversation_preserving_moim,
    verify_confidence_and_math,
)

_TENANT_SLUG_RE: Final[re.Pattern[str]] = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{1,62}$")

_PII_PATTERNS: Final[tuple[tuple[str, re.Pattern[str]], ...]] = (
    ("PII_EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("PII_BANK_ACC", re.compile(r"(?i)(?:stk|tk|account|số\s*tài\s*khoản)[:\s#-]*(\d{8,16})\b")),
    ("PII_TAX_ID", re.compile(r"(?i)(?:mst|mã\s*số\s*thuế)[:\s#-]*(\d{10}(?:-\d{3})?)\b|\b\d{10}-\d{3}\b")),
    ("PII_CCCD", re.compile(r"(?i)(?:cccd|cmnd)[:\s#-]*(\d{9}|\d{12})\b|\b0\d{11}\b")),
    ("PII_PHONE", re.compile(r"(?:\+?84|0)[\s.-]?(?:2\d|3|5|7|8|9)(?:[\s.-]?\d){8}\b")),
)


class ConsentRequiredError(PermissionError):
    """Raised when Decree 13/2023/NĐ-CP data subject consent is missing or withdrawn."""


class TenantIsolationError(PermissionError):
    """Raised on invalid tenant slug or cross-tenant SQLite path traversal."""


@dataclass(frozen=True)
class RedactionResult:
    """Result of local Vietnamese PII tokenization before external LLM routing."""
    redacted_text: str
    token_map: dict[str, str]
    redacted_count: int


def redact_vietnamese_pii(text: str) -> RedactionResult:
    """Deterministically tokenize VN email, bank account, MST, CCCD/CMND, and phone strings."""
    token_map: dict[str, str] = {}
    working = text
    counter = 0
    for prefix, pattern in _PII_PATTERNS:
        def _sub(match: re.Match[str], pfx: str = prefix) -> str:
            nonlocal counter
            counter += 1
            tok = f"<{pfx}_{counter:02d}>"
            grp_val = next((g for g in match.groups() if g is not None), None)
            if grp_val is not None:
                token_map[tok] = grp_val
                return match.group(0).replace(grp_val, tok, 1)
            token_map[tok] = match.group(0)
            return tok

        working = pattern.sub(_sub, working)
    return RedactionResult(redacted_text=working, token_map=token_map, redacted_count=counter)


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
    """Decree 13/2023/NĐ-CP consent verification and <72h DSAR erasure across OPC + Privacy + VietQR DBs."""

    def __init__(self, privacy_db_path: str | Path, opc_db_path: str | Path | None = None) -> None:
        self.engine = PrivacyEngine(db_path=Path(privacy_db_path))
        self.opc_db_path = Path(opc_db_path) if opc_db_path is not None else None

    def record_subject_consent(self, subject_id: str, purpose: str = "zalo_lead_to_quote", consent_given: bool = True) -> dict[str, Any]:
        return self.engine.record_consent(subject_id.strip(), purpose, "Điều 11 Nghị định 13/2023/NĐ-CP", consent_given=consent_given)

    def has_active_consent(self, subject_id: str, purpose: str = "zalo_lead_to_quote") -> bool:
        with sqlite3.connect(str(self.engine.db_path), timeout=10.0) as conn:
            row = conn.execute(
                "SELECT consent_given, withdrawn_at FROM consent_log WHERE subject_id = ? AND purpose = ? ORDER BY recorded_at DESC LIMIT 1",
                (subject_id.strip(), purpose),
            ).fetchone()
        return bool(row and row[0] and row[1] is None)

    def require_consent(self, subject_id: str, purpose: str = "zalo_lead_to_quote") -> None:
        if not self.has_active_consent(subject_id, purpose=purpose):
            raise ConsentRequiredError(f"Active Decree 13/2023/NĐ-CP consent required for '{subject_id}' ({purpose}).")

    def withdraw_subject_consent(self, subject_id: str, purpose: str = "zalo_lead_to_quote") -> dict[str, Any]:
        return self.engine.withdraw_consent(subject_id.strip(), purpose=purpose)

    def erase_subject_under_72h(self, subject_id: str) -> dict[str, Any]:
        """Execute Article 9.5 RIGHT_TO_DELETE (<72h, deadline_days=3) safely with FK integrity."""
        clean_sub = (subject_id or "").strip()
        if len(clean_sub) < 3 or not any(ch.isalnum() for ch in clean_sub):
            raise ValueError(f"Invalid subject_id '{subject_id}' for DSAR erasure.")
        dsar = self.engine.handle_dsar_request("RIGHT_TO_DELETE", subject_id=clean_sub)
        opc_erased = 0
        escaped = clean_sub.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like_pat = f"%{escaped}%"
        run_ids: list[str] = []
        if self.opc_db_path is not None and self.opc_db_path.exists():
            with sqlite3.connect(str(self.opc_db_path), timeout=10.0) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                run_ids = [r[0] for r in conn.execute("SELECT run_id FROM opc_runs WHERE proposal_input_json LIKE ? ESCAPE '\\' OR action_payload_json LIKE ? ESCAPE '\\'", (like_pat, like_pat)).fetchall()]
                if run_ids:
                    ph = ",".join("?" * len(run_ids))
                    c0 = conn.execute(f"DELETE FROM opc_approvals WHERE run_id IN ({ph})", run_ids)
                    c1 = conn.execute(f"DELETE FROM opc_actions WHERE run_id IN ({ph})", run_ids)
                    c2 = conn.execute(f"DELETE FROM opc_runs WHERE run_id IN ({ph})", run_ids)
                    opc_erased += max(0, c0.rowcount) + max(0, c1.rowcount) + max(0, c2.rowcount)
                c3 = conn.execute("DELETE FROM opc_actions WHERE payload_json LIKE ? ESCAPE '\\'", (like_pat,))
                opc_erased += max(0, c3.rowcount)
                conn.commit()
            vqr_db = self.opc_db_path.parent / f"{self.opc_db_path.stem}_vietqr.db"
            if run_ids and vqr_db.exists():
                with sqlite3.connect(str(vqr_db), timeout=10.0) as vconn:
                    for rid in run_ids:
                        vconn.execute("DELETE FROM qr_codes WHERE memo LIKE ? ESCAPE '\\'", (f"%{rid}%",))
                    vconn.commit()
        total_erased = int((dsar.get("erasure") or {}).get("total_erased", 0)) + opc_erased
        if total_erased > 0 and dsar.get("status") != "COMPLETED":
            dsar["status"] = "COMPLETED"
            with sqlite3.connect(str(self.engine.db_path), timeout=10.0) as pconn:
                pconn.execute("UPDATE dsar_requests SET status = 'COMPLETED' WHERE request_id = ?", (dsar["request_id"],))
                pconn.commit()
        dsar["opc_rows_erased"] = opc_erased
        dsar["total_erased_combined"] = total_erased
        return dsar


__all__ = [
    "MIN_EXTRACTION_CONFIDENCE",
    "ConsentRequiredError",
    "HaltForHumanError",
    "PilotPrivacyGuard",
    "RedactionResult",
    "TenantIsolationError",
    "compact_conversation_preserving_moim",
    "redact_vietnamese_pii",
    "resolve_tenant_db_path",
    "verify_confidence_and_math",
]
