"""Mekong CLI 7 — Provider breaker + cooldown-aware retry (OmniRoute A1).

Per (provider, model) lockout registry with Retry-After / "Resets in N"
awareness. Persisted to <profile state dir>/breaker.json so lockouts survive
restarts. Also hosts learned rate-limit info (B7).
"""

from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path

RETRY_BUDGET_MS = 60_000          # tổng thời gian chờ tối đa cho 1 request
BACKOFF_STEPS_S = (30, 60, 120)   # fallback exponential khi không có retry_after
DEFAULT_PROVIDER = "omniroute"

_RESET_IN_RE = re.compile(
    r"resets?\s+in\s+(\d+)\s+(day|days|hour|hours|minute|minutes|second|seconds)\b"
)
_RESET_AFTER_RE = re.compile(r"reset\s+(?:after|in)\s+(\d+(?:\.\d+)?)s?\b", re.IGNORECASE)
_RETRY_AFTER_RE = re.compile(r"retry[- ]?after\s*:?\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
_UNIT_S = {"day": 86400, "hour": 3600, "minute": 60, "second": 1}


def parse_retry_after_seconds(text: str | None) -> float | None:
    """Parse Retry-After / 'Resets in N units' / 'reset after Ns' -> seconds.

    Mirrors OmniRoute parseResetCountdownMs (providerErrorRules.ts): returns
    None when no recognizable phrase is present.
    """
    if not text:
        return None
    low = text.lower()
    m = _RESET_IN_RE.search(low)
    if m:
        return float(int(m.group(1)) * _UNIT_S[m.group(2).rstrip("s")])
    m = _RETRY_AFTER_RE.search(low)
    if m:
        return float(m.group(1))
    m = _RESET_AFTER_RE.search(low)
    if m:
        return float(m.group(1))
    return None


def _state_dir() -> Path:
    try:
        from .opc_loop import _state_dir as sd

        return sd()
    except Exception:  # noqa: BLE001
        return Path.home() / ".mekong" / "opc"


def _lock_key(provider: str, model: str) -> tuple[str, str]:
    return (provider, model.strip().lower())


class Breaker:
    """Lockout registry: record_failure/record_success/is_locked + persistence."""

    def __init__(self, path: Path | None = None):
        self.path = path or (_state_dir() / "breaker.json")
        self.lockouts: dict[tuple[str, str], float] = {}
        self.failures: dict[tuple[str, str], int] = {}
        self.learned_limits: dict[str, dict[str, float]] = {}
        self.reasons: dict[tuple[str, str], str] = {}
        self._mu = threading.Lock()
        self._load()

    # ── persistence ─────────────────────────────────────────

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text())
        except Exception:  # noqa: BLE001 — corrupt state never blocks startup
            return
        now = time.time()
        for key, until in (data.get("lockouts") or {}).items():
            provider, _, model = key.partition("::")
            if until > now:
                self.lockouts[(provider, model)] = float(until)
        for key, n in (data.get("failures") or {}).items():
            provider, _, model = key.partition("::")
            self.failures[(provider, model)] = int(n)
        self.learned_limits = data.get("learned_limits") or {}

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "lockouts": {f"{p}::{m}": u for (p, m), u in self.lockouts.items()},
                "failures": {f"{p}::{m}": n for (p, m), n in self.failures.items()},
                "learned_limits": self.learned_limits,
            }
            self.path.write_text(json.dumps(data, indent=2))
        except OSError:
            pass  # read-only state dir: in-memory breaker still works

    # ── core API ────────────────────────────────────────────

    def record_failure(
        self,
        provider: str,
        model: str,
        retry_after: float | None = None,
        reason: str = "",
    ) -> float:
        """Lock (provider, model). retry_after ưu tiên; fallback 30/60/120s.

        Returns the lockout duration in seconds.
        """
        key = _lock_key(provider, model)
        with self._mu:
            if retry_after is not None and retry_after > 0:
                until = time.time() + retry_after
            else:
                step = min(self.failures.get(key, 0), len(BACKOFF_STEPS_S) - 1)
                until = time.time() + BACKOFF_STEPS_S[step]
            self.lockouts[key] = until
            self.failures[key] = self.failures.get(key, 0) + 1
            if reason:
                self.reasons[key] = reason
            self._save()
            return until - time.time()

    def record_success(self, provider: str, model: str) -> None:
        key = _lock_key(provider, model)
        with self._mu:
            if key in self.lockouts:
                del self.lockouts[key]
            if key in self.failures:
                del self.failures[key]
            if key in self.reasons:
                del self.reasons[key]
            self._save()

    def is_locked(self, provider: str, model: str) -> bool:
        key = _lock_key(provider, model)
        until = self.lockouts.get(key, 0.0)
        if until <= time.time():
            if key in self.lockouts:  # lazy cleanup
                with self._mu:
                    self.lockouts.pop(key, None)
                    self.failures.pop(key, None)
                    self.reasons.pop(key, None)
                    self._save()
            return False
        return True

    def remaining(self, provider: str, model: str) -> float:
        until = self.lockouts.get(_lock_key(provider, model), 0.0)
        return max(0.0, until - time.time())

    def locked_models(self) -> list[dict]:
        now = time.time()
        out = []
        for (provider, model), until in self.lockouts.items():
            if until > now:
                out.append({
                    "provider": provider,
                    "model": model,
                    "until": round(until, 1),
                    "remaining": round(until - now, 1),
                    "reason": self.reasons.get((provider, model), ""),
                })
        return sorted(out, key=lambda d: d["remaining"])

    # ── B7: learned rate limits ─────────────────────────────

    def record_rate_limit(
        self, model: str, remaining: float | None = None, reset_in: float | None = None
    ) -> None:
        with self._mu:
            entry = dict(self.learned_limits.get(model.strip().lower(), {}))
            if remaining is not None:
                entry["remaining"] = float(remaining)
            if reset_in is not None:
                entry["reset_in"] = float(reset_in)
            entry["learned_at"] = time.time()
            self.learned_limits[model.strip().lower()] = entry
            self._save()

    def rate_limits(self) -> dict[str, dict[str, float]]:
        return {m: dict(e) for m, e in self.learned_limits.items()}

    def clear(self) -> None:
        with self._mu:
            self.lockouts.clear()
            self.failures.clear()
            self.reasons.clear()
            self.learned_limits.clear()
            self._save()


# module-level singleton used by llm.py / omni.py / doctor.py
breaker = Breaker()
