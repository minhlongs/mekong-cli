"""Forest → mekongd signal emission (Giai đoạn 3.2.A).

Closes Pillar 3 (Feedback Loop) at the multi-tenant layer: every finished job
becomes a `good`/`bad` signal at mekongd, so operator dashboards see signal
volume from both single-founder (agent-core direct) and multi-user (forest)
traffic.

Best-effort — signal transport failures never fail the user's job. Gated by
``FOREST_SIGNALS_ENABLED`` (default: on); disable with ``FOREST_SIGNALS_ENABLED=0``.
"""

from __future__ import annotations

import logging
import os

import httpx

log = logging.getLogger("agent_forest.worker.signals")

_DEFAULT_MEKONGD_URL = "http://127.0.0.1:8765"
_DEFAULT_TIMEOUT = 3.0


def is_enabled() -> bool:
    raw = os.getenv("FOREST_SIGNALS_ENABLED")
    if raw is None:
        return True
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _mekongd_url() -> str:
    return os.getenv("MEKONGD_URL", _DEFAULT_MEKONGD_URL).rstrip("/")


def build_note(user_id: str, job_id: str, error: str | None = None) -> str:
    """Compact, model-friendly provenance string for the signal note.

    Keeps PII out (user_id is opaque); short-circuits error length so signal
    rows stay bounded.
    """
    base = f"forest/{user_id}/{job_id}"
    if error:
        tail = error.strip().replace("\n", " ")[:160]
        return f"{base}: {tail}"
    return base


def _post_signal(
    kind: str,
    note: str,
    *,
    model: str = "",
    base_url: str | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
) -> bool:
    """Low-level POST to mekongd /v1/signals. Returns True on 2xx.

    Never raises — transport errors are logged and swallowed so a broken
    mekongd never blocks worker throughput or user requests.
    """
    if not is_enabled():
        return False
    payload: dict = {"kind": kind, "note": note}
    if model:
        payload["model"] = model
    url = f"{(base_url or _mekongd_url()).rstrip('/')}/v1/signals"
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload)
        return 200 <= resp.status_code < 300
    except Exception as exc:  # noqa: BLE001 — best-effort
        log.warning("signal emit failed: %s", exc)
        return False


def emit(
    status: str,
    user_id: str,
    job_id: str,
    *,
    error: str | None = None,
    model: str = "",
    base_url: str | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
) -> bool:
    """Worker-side auto-emission (Giai đoạn 3.2.A)."""
    kind = "good" if status == "completed" else "bad"
    note = build_note(user_id, job_id, error if kind == "bad" else None)
    return _post_signal(kind, note, model=model, base_url=base_url, timeout=timeout)


def emit_user_feedback(
    rating: str,
    user_id: str,
    job_id: str,
    *,
    note: str | None = None,
    base_url: str | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
) -> bool:
    """User-driven feedback (Giai đoạn 3.2.B).

    The rating maps directly to signal kind. ``note`` is appended to the
    standard provenance prefix with ``#user`` so operator dashboards can
    distinguish auto- vs user-emitted signals.
    """
    if rating not in ("good", "bad"):
        raise ValueError(f"rating must be 'good' or 'bad', got {rating!r}")
    base = f"forest/{user_id}/{job_id}#user"
    if note:
        tail = note.strip().replace("\n", " ")[:160]
        full_note = f"{base}: {tail}"
    else:
        full_note = base
    return _post_signal(rating, full_note, base_url=base_url, timeout=timeout)
