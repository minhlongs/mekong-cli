# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Financial audit trail for MCU billing — immutable log of all credit transactions."""
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class AuditEntry:
    """Immutable record of a single credit transaction."""

    timestamp: float
    tenant_id: str
    action: str  # "credit" | "debit" | "refund" | "adjustment"
    amount: float
    balance_before: float
    balance_after: float
    reason: str
    mission_id: Optional[str] = None
    idempotency_key: Optional[str] = None


class BillingAuditTrail:
    """
    Append-only financial audit log.

    Each tenant gets a separate JSONL file. Records are appended atomically.
    Supports balance reconciliation by replaying the full transaction history.
    """

    def __init__(self, log_dir: Optional[str] = None) -> None:
        self._dir = Path(
            log_dir
            or os.getenv(
                "BILLING_AUDIT_DIR",
                os.path.expanduser("~/.mekong/billing/audit"),
            )
        )
        self._dir.mkdir(parents=True, exist_ok=True)

    def record(self, entry: AuditEntry) -> str:
        """
        Record a billing event. Returns entry ID.

        Args:
            entry: AuditEntry dataclass with transaction details.

        Returns:
            Unique entry ID string.
        """
        entry_id = f"{int(entry.timestamp * 1000)}_{entry.tenant_id}_{entry.action}"
        log_file = self._dir / f"{entry.tenant_id}.jsonl"
        from src.core.file_lock import locked_append
        with locked_append(log_file) as f:
            f.write(json.dumps(asdict(entry)) + "\n")
        return entry_id

    def get_history(self, tenant_id: str, limit: int = 100) -> list[dict]:
        """
        Get recent audit entries for a tenant.

        Args:
            tenant_id: Tenant identifier.
            limit: Max entries to return (most recent).

        Returns:
            List of entry dicts, ordered oldest-first within the slice.
        """
        log_file = self._dir / f"{tenant_id}.jsonl"
        if not log_file.exists():
            return []
        raw = log_file.read_text().strip()
        if not raw:
            return []
        entries = [json.loads(line) for line in raw.split("\n") if line]
        return entries[-limit:]

    def get_balance_proof(self, tenant_id: str) -> dict:
        """
        Calculate balance from audit trail (reconciliation check).

        Replays all transactions to derive the expected balance.
        Use this to verify the live balance matches the audit log.

        Args:
            tenant_id: Tenant identifier.

        Returns:
            Dict with calculated_balance, entries_count, and last_entry.
        """
        history = self.get_history(tenant_id, limit=10_000)
        calculated = 0.0
        for entry in history:
            if entry["action"] in ("credit", "refund"):
                calculated += entry["amount"]
            elif entry["action"] in ("debit", "adjustment"):
                calculated -= entry["amount"]
        return {
            "tenant_id": tenant_id,
            "calculated_balance": round(calculated, 6),
            "entries_count": len(history),
            "last_entry": history[-1] if history else None,
        }


# Module-level singleton
_instance: Optional[BillingAuditTrail] = None


def get_audit_trail() -> BillingAuditTrail:
    """Singleton accessor for the default audit trail."""
    global _instance
    if _instance is None:
        _instance = BillingAuditTrail()
    return _instance


def reset_audit_trail() -> None:
    """Reset singleton (for testing)."""
    global _instance
    _instance = None


__all__ = [
    "AuditEntry",
    "BillingAuditTrail",
    "get_audit_trail",
    "reset_audit_trail",
]
