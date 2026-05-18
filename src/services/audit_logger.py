"""Admin audit log — flock-safe JSONL writer for auth events.

Writes to ~/.mekong/admin-audit.jsonl (or $MEKONG_CONFIG_DIR/admin-audit.jsonl).
PII policy: caller passes only scope, org, sub, endpoint — never raw token or
request body. File mode 0600 (founder-readable only).

Best-effort: IOError during write is logged to stderr but never raised so that
a full disk / permission error never blocks the auth path.
"""
from __future__ import annotations

import fcntl
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------- Path resolution ----------

def _audit_path() -> Path:
    """Resolve audit log path from env var or default ~/.mekong/."""
    base = os.getenv("MEKONG_CONFIG_DIR")
    if base:
        return Path(base) / "admin-audit.jsonl"
    return Path.home() / ".mekong" / "admin-audit.jsonl"


# ---------- Writer ----------

def audit_admin_action(scope: str, org: str, sub: str, endpoint: str) -> None:
    """Append one audit record for a successful admin auth.

    Args:
        scope:    JWT scope string (e.g. "founder", "cs", "legacy").
        org:      org_id from request (e.g. "acme", "default").
        sub:      JWT 'sub' claim — typically admin email.
        endpoint: request.url.path — no query string, strips PII from URL.

    Never raises. IOError → printed to stderr and swallowed.
    """
    record = {
        "event": "admin_auth",
        "timestamp_iso": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z",
        "scope": scope,
        "org": org,
        "sub": sub,
        "endpoint": endpoint,
    }
    path = _audit_path()
    try:
        _flock_append(path, record)
    except IOError as exc:
        print(f"[audit_logger] WARN: could not write audit log: {exc}", file=sys.stderr)


def _flock_append(path: Path, record: dict) -> None:
    """Open path in append mode, acquire exclusive flock, write one JSON line."""
    # Auto-create parent; parent (~/.mekong/) already exists from Phase 7
    path.parent.mkdir(parents=True, exist_ok=True)

    is_new = not path.exists()
    with path.open("a", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)

    # Enforce 0600 on first creation so only the founder UID can read it.
    if is_new:
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass  # best-effort; not a security blocker on shared filesystems


# ---------- Reader (for tail script + tests) ----------

def read_audit_lines(limit: int = 100) -> list[dict]:
    """Return the last *limit* valid JSON records from the audit log.

    Returns empty list if file is absent or unreadable (best-effort).
    """
    path = _audit_path()
    if not path.exists():
        return []
    try:
        raw_lines = path.read_text(encoding="utf-8").splitlines()
    except IOError:
        return []

    records: list[dict] = []
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return records[-limit:] if len(records) > limit else records
