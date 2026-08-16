# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Public metering facade — C5 unit-economics constants + simple track() API.

Single import surface for callers that want:
  from src.services.metering import track, UNIT_ECON_CAC_VND, ...

Delegates to :class:`src.raas.credit_metering_middleware.CreditMeter` the
moment `track()` is actually called (lazy init), so importing this module
does not require an initialized RaaS DB.

Unit-economics constants come from the C5 plan and the existing
``docs/unit-economics-model.md``. They are shared by:
  - CLI `usage report -e` (JSON output)
  - Unit-economics test assertions (WORM-style — value is truth once)
  - Any future dashboard / stroke-prediction feed

Do not mutate these at runtime; they are file-level constants.
"""
from __future__ import annotations

from typing import Optional

# ---------------------------------------------------------------------------
# C5 canonical unit-economics (VND)
# ---------------------------------------------------------------------------
# These values are sourced from plans/260706-1243-phase-c-revenue/plan.md C5
# section and the docs/unit-economics-model.md model output.
# Treat as WORM — do not refactor into dicts/classes that drift silently.
# ---------------------------------------------------------------------------

UNIT_ECON_CAC_VND: int = 512_000   # ~512 USD → 512 000 VND @ 1 000 VND/USD
UNIT_ECON_LTV_VND: int = 2_048_000  # ~2 048 USD (LTV target ~4× CAC baseline)
UNIT_ECON_MRR_VND: int = 299_000   # Growth tier baseline (revenue anchor)

# Legacy USD aliases kept for backward-compat with existing reports
UNIT_ECON_CAC_USD: int = 512
UNIT_ECON_LTV_USD: int = 2_048
UNIT_ECON_MRR_USD: int = 299


# ---------------------------------------------------------------------------
# Module-level singletons (lazy-initialized)
# ---------------------------------------------------------------------------

_meter = None  # CreditMeter | None


def _get_meter():
    """Return (and cache) a CreditMeter instance."""
    global _meter
    if _meter is None:
        from src.raas.credit_metering_middleware import CreditMeter  # noqa: PLC0415
        _meter = CreditMeter()
    return _meter


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def track(
    command: str,
    tenant_id: Optional[str] = None,
    credits: int = 1,
    mission_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Record one usage event against the metering DB.

    Thin public face — the caller does not need to know about
    :class:`~src.raas.credit_metering_middleware.CreditMeter`. Returns the
    :class:`UsageEvent` as a plain dict so callers can persist the event id
    if they want idempotent downstream processing.

    :param command: Human-readable command/agent name (e.g. "cook", "plan").
    :param tenant_id: Tenant identifier. Defaults to ``RAAS_LICENSE_KEY`` env
      var so the common ``anonymous`` case (no env set) is handled uniformly.
    :param credits: Credits to log. Defaults to 1 for cheap commands; complex
      multi-step invocations should pass their actual cost up-front rather
      than calling ``track`` repeatedly.
    :param mission_id: Optional parent mission identifier for drill-down.
    :param metadata: Extra context stored for audit/debugging only; NOT used
      for billing tier resolution.
    :returns: ``UsageEvent``-shaped dict with ``id``, ``tenant_id``,
      ``task_type``, ``credits_used``, and ``timestamp``.
    :raises RuntimeError: On SQLite errors (never silent).

    Usage::

        from src.services.metering import track
        track("cook", credits=1)
    """
    meter = _get_meter()
    resolved_tenant = tenant_id or __import__("os").environ.get(
        "RAAS_LICENSE_KEY"
    )
    event = meter.record_usage(
        tenant_id=resolved_tenant or "",
        task_type=command,
        credits_used=credits,
        mission_id=mission_id,
    )
    out: dict = {
        "id": event.id,
        "tenant_id": event.tenant_id,
        "mission_id": event.mission_id,
        "task_type": event.task_type,
        "credits_used": event.credits_used,
        "timestamp": event.timestamp,
    }
    if metadata:
        out["metadata"] = metadata
    return out


def unit_economics() -> dict:
    """Return the canonical C5 unit-economics snapshot as a plain dict.

    Structured so ``mekong usage report -e --json`` can embed it verbatim.

    :returns: ``{"cacVnd", "ltvVnd", "mrrVnd", "method"}``

    Usage::

        from src.services.metering import unit_economics
        print(unit_economics())
    """
    return {
        "cacVnd": UNIT_ECON_CAC_VND,
        "ltvVnd": UNIT_ECON_LTV_VND,
        "mrrVnd": UNIT_ECON_MRR_VND,
        "method": "industry_average",
    }
