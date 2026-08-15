"""Mekong CLI 7 — doctor: gateway + model health checks.

OmniRoute ports: A1 breaker lockout state + B7 learned rate limits shown
per model; locked models are reported without a live ping.
"""

from __future__ import annotations

from .llm import LLMClient
from .models import all_models
from .resilience import breaker


def run_doctor(verbose: bool = False) -> tuple[int, list[dict]]:
    """Check gateway + every registered model. Returns (exit_code, results)."""
    client = LLMClient()
    results: list[dict] = []

    # Gateway ping
    try:
        ok, detail = client.ping("claude-fable-5")
        results.append({"check": "gateway", "status": "OK" if ok else "FAIL", "detail": detail})
    except Exception as e:
        results.append({"check": "gateway", "status": "FAIL", "detail": str(e)[:120]})

    # Per-model ping (skip live ping khi model đang locked — A1)
    for m in all_models():
        locked = breaker.is_locked(client.provider, m.id)
        if locked:
            remaining = breaker.remaining(client.provider, m.id)
            results.append(
                {
                    "check": m.id,
                    "status": "FAIL",
                    "detail": f"LOCKED (breaker) — {remaining:.0f}s còn lại",
                    "paid": m.paid,
                    "locked": True,
                }
            )
            continue
        try:
            ok, detail = client.ping(m.id)
            results.append(
                {
                    "check": m.id,
                    "status": "OK" if ok else "FAIL",
                    "detail": detail,
                    "paid": m.paid,
                    "locked": False,
                }
            )
        except Exception as e:
            results.append(
                {"check": m.id, "status": "FAIL", "detail": str(e)[:120], "locked": False}
            )

    # A1: lockout summary
    locked = breaker.locked_models()
    if locked:
        detail = ", ".join(
            f"{d['model']} ({d['remaining']:.0f}s)" for d in locked
        )
        results.append({"check": "breaker-lockouts", "status": "FAIL", "detail": detail})
    else:
        results.append({"check": "breaker-lockouts", "status": "OK", "detail": "no active lockouts"})

    # B7: learned rate limits
    limits = breaker.rate_limits()
    if limits:
        detail = "; ".join(
            f"{m}: remaining={e.get('remaining', '?')} reset_in={e.get('reset_in', '?')}s"
            for m, e in limits.items()
        )[:200]
        results.append({"check": "learned-rate-limits", "status": "OK", "detail": detail})
    else:
        results.append(
            {"check": "learned-rate-limits", "status": "OK", "detail": "chưa học được — cần 429/header"}
        )

    exit_code = 0 if all(r["status"] == "OK" for r in results) else 1
    return exit_code, results
