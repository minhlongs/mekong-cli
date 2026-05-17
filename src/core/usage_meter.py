"""
Usage Meter — log events + decrement credits for VN pilot users.

Side effects:
- Appends 1 line/call to ~/.mekong/usage_events.jsonl (read by scripts/pilot-metrics.py)
- Decrements ~/.mekong/pilot_credits.json (managed by scripts/pilot-onboard.py)

User identity: MEKONG_USER_ID env var. Fallback: "anonymous" (no credit gating).

Cost lookup: factory/contracts/pricing.json::vn_services (Phase 4 of VN Hub).

Public API:
    track(command, success=True, duration_ms=0) → raises InsufficientCreditsError
    balance(user_id=None) → int

Why a top-level function (not class): single global side-effect target; class
adds no value for stateless file appends and would invite premature caching.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".mekong"
EVENTS_FILE = CONFIG_DIR / "usage_events.jsonl"
CREDITS_FILE = CONFIG_DIR / "pilot_credits.json"
PRICING_FILE = Path(__file__).resolve().parents[2] / "factory" / "contracts" / "pricing.json"

DEFAULT_COST = 1
ANONYMOUS_USER = "anonymous"


class InsufficientCreditsError(RuntimeError):
    """Raised when a pilot user has fewer credits than the command requires.

    Mirrors HTTP 402 semantics from the gateway — gives callers a clear
    error type to catch and surface a user-friendly upgrade prompt.
    """

    def __init__(self, user_id: str, command: str, cost: int, balance: int) -> None:
        self.user_id = user_id
        self.command = command
        self.cost = cost
        self.balance = balance
        super().__init__(
            f"Hết credits — '{command}' cần {cost} nhưng số dư = {balance}. "
            f"Nâng gói tại https://mekongmind.com/vn/bang-gia"
        )


@dataclass(frozen=True)
class TrackResult:
    command: str
    user_id: str
    cost: int
    balance_after: int
    success: bool
    duration_ms: int


@lru_cache(maxsize=1)
def _load_costs() -> dict[str, int]:
    """Cost table keyed by command name. Cached — pricing changes need restart."""
    try:
        data = json.loads(PRICING_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    table: dict[str, int] = {}
    for entry in data.get("vn_services", []):
        cmd = entry.get("command")
        if cmd:
            table[cmd] = int(entry.get("credits", DEFAULT_COST))
    return table


def _command_cost(command: str) -> int:
    """Cost for `command`. Falls back to DEFAULT_COST. Sub-command (eg
    'ke-toan invoice') uses the base command's cost so we don't have to
    enumerate every flag combo in pricing.json."""
    table = _load_costs()
    if command in table:
        return table[command]
    base = command.split()[0] if " " in command else command
    return table.get(base, DEFAULT_COST)


def _current_user() -> str:
    return os.getenv("MEKONG_USER_ID", "").strip() or ANONYMOUS_USER


def _load_balances() -> dict[str, int]:
    if not CREDITS_FILE.exists():
        return {}
    try:
        return json.loads(CREDITS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_balances(balances: dict[str, int]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CREDITS_FILE.write_text(
        json.dumps(balances, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _append_event(record: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with EVENTS_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def balance(user_id: Optional[str] = None) -> int:
    """Current credit balance for `user_id` (or env user). Anonymous returns 0."""
    uid = user_id or _current_user()
    if uid == ANONYMOUS_USER:
        return 0
    return int(_load_balances().get(uid, 0))


def track(command: str, *, success: bool = True, duration_ms: int = 0,
          cost_override: Optional[int] = None) -> TrackResult:
    """Log a command execution + decrement credits.

    Raises InsufficientCreditsError if the registered user has < cost credits.
    Anonymous users (no MEKONG_USER_ID) skip credit gating but still log
    events so usage analytics work for local dev.
    """
    uid = _current_user()
    cost = cost_override if cost_override is not None else _command_cost(command)

    if uid != ANONYMOUS_USER:
        balances = _load_balances()
        current = int(balances.get(uid, 0))
        if current < cost:
            _append_event({
                "user_id": uid,
                "command": command,
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "success": False,
                "duration_ms": duration_ms,
                "cost": cost,
                "error": "insufficient_credits",
            })
            raise InsufficientCreditsError(uid, command, cost, current)
        balances[uid] = current - cost
        _save_balances(balances)
        balance_after = balances[uid]
    else:
        balance_after = 0  # anonymous mode — no balance tracked

    _append_event({
        "user_id": uid,
        "command": command,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "success": success,
        "duration_ms": duration_ms,
        "cost": cost,
    })

    return TrackResult(
        command=command,
        user_id=uid,
        cost=cost,
        balance_after=balance_after,
        success=success,
        duration_ms=duration_ms,
    )


class Stopwatch:
    """Context manager that calls track() on exit with the elapsed duration.

    Usage:
        with Stopwatch("ke-toan invoice"):
            ... do work ...
    """

    def __init__(self, command: str) -> None:
        self.command = command
        self._t0: float = 0.0
        self._exc_seen: bool = False

    def __enter__(self) -> "Stopwatch":
        self._t0 = time.monotonic()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._exc_seen = exc_type is not None
        duration_ms = int((time.monotonic() - self._t0) * 1000)
        try:
            track(self.command, success=not self._exc_seen, duration_ms=duration_ms)
        except InsufficientCreditsError:
            # Don't shadow the user's original exception (if any).
            if not self._exc_seen:
                raise
