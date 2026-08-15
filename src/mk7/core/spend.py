"""Mekong CLI 7 — Spend tracking (OmniRoute A2).

Every LLM response is appended to <profile state dir>/spend.jsonl with a cost
estimate from a simple price table. burn_rate() feeds the analytics board and
the omni spend alert.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

# {model-key-prefix: {"in": $/1M tokens, "out": $/1M tokens}}
PRICE_TABLE: dict[str, dict[str, float]] = {
    "claude-opus-5": {"in": 15.0, "out": 75.0},
    "claude-opus-4": {"in": 3.0, "out": 15.0},     # sonnet-replacement model
    "claude-sonnet": {"in": 3.0, "out": 15.0},
    "claude-fable": {"in": 3.0, "out": 15.0},
    "claude-haiku": {"in": 1.0, "out": 5.0},
    "claude-opus": {"in": 15.0, "out": 75.0},      # generic opus fallback
    "deepseek": {"in": 0.3, "out": 1.2},
    "qwen3.8-max": {"in": 2.0, "out": 6.0},
    "gpt-oss": {"in": 0.0, "out": 0.0},            # free tier
    "nemotron": {"in": 0.0, "out": 0.0},           # free tier
}


def cost_estimate(model: str, input_tokens: int, output_tokens: int) -> float:
    low = model.strip().lower()
    for prefix, price in PRICE_TABLE.items():
        if low.startswith(prefix):
            return input_tokens * price["in"] / 1_000_000 + output_tokens * price["out"] / 1_000_000
    return 0.0


def _spend_file() -> Path:
    try:
        from .opc_loop import _state_dir

        return _state_dir() / "spend.jsonl"
    except Exception:  # noqa: BLE001
        return Path.home() / ".mekong" / "opc" / "spend.jsonl"


def record_spend(
    provider: str,
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    caller: str = "",
) -> dict:
    """Append one spend line. caller = session id / product hint (A2 join)."""
    entry = {
        "ts": time.time(),
        "provider": provider,
        "model": model,
        "input_tokens": int(input_tokens or 0),
        "output_tokens": int(output_tokens or 0),
        "cost_estimate": round(cost_estimate(model, input_tokens, output_tokens), 6),
        "caller": caller or "",
    }
    p = _spend_file()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass  # read-only state dir: spend tracking is best-effort
    return entry


def _entries(since: float = 0.0) -> list[dict]:
    p = _spend_file()
    if not p.exists():
        return []
    out: list[dict] = []
    try:
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("ts", 0) >= since:
                out.append(e)
    except OSError:
        return []
    return out


def burn_rate(hours: float = 24) -> float:
    """Tổng chi phí trong `hours` giờ gần nhất (USD)."""
    return round(sum(e.get("cost_estimate", 0.0) for e in _entries(since=time.time() - hours * 3600)), 4)


def spend_by_product(product: str, hours: float = 24 * 7) -> list[dict]:
    """Spend entries có caller hint khớp product (nối qua session/loop)."""
    since = time.time() - hours * 3600
    return [e for e in _entries(since=since) if product in (e.get("caller") or "")]


def spend_summary(hours: float = 24) -> dict:
    """{models: {model: stats}, totals} cho `hours` giờ gần nhất."""
    since = time.time() - hours * 3600
    models: dict[str, dict] = {}
    totals = {"calls": 0, "cost": 0.0, "input_tokens": 0, "output_tokens": 0}
    for e in _entries(since=since):
        model = e.get("model", "?")
        row = models.setdefault(model, {
            "calls": 0, "cost": 0.0, "input_tokens": 0, "output_tokens": 0,
        })
        row["calls"] += 1
        row["cost"] += e.get("cost_estimate", 0.0)
        row["input_tokens"] += e.get("input_tokens", 0)
        row["output_tokens"] += e.get("output_tokens", 0)
        totals["calls"] += 1
        totals["cost"] += e.get("cost_estimate", 0.0)
        totals["input_tokens"] += e.get("input_tokens", 0)
        totals["output_tokens"] += e.get("output_tokens", 0)
    for row in models.values():
        row["cost"] = round(row["cost"], 4)
    totals["cost"] = round(totals["cost"], 4)
    return {"models": models, "totals": totals}
