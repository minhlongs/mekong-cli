"""Currency-aware Decimal cost accounting with explicit FX provenance and fail-closed aggregation."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import time
from typing import Any, Literal, Sequence

from src.opc.models import UsageRecord, UsageStage


@dataclass(frozen=True)
class FxQuote:
    """Verified foreign-exchange quote with explicit source and freshness bounds."""
    base_currency: str
    quote_currency: str
    rate: Decimal
    source: str
    timestamp: int
    max_age_seconds: int = 86400
    confidence: str = "verified"


@dataclass(frozen=True)
class TypedCostEntry:
    """Typed single-event cost entry preserving original amount, currency, source, and FX provenance."""
    event_id: str
    original_amount: Decimal | None
    original_currency: str
    measurement_source: str
    provider: str
    model: str
    conversion_source: str | None
    fx_rate: Decimal | None
    fx_timestamp: int | None
    converted_amount: Decimal | None
    conversion_confidence: str
    missing_data_status: str


@dataclass(frozen=True)
class MultiCurrencyCostSummary:
    """Currency-safe cost aggregation that never silently adds distinct currencies or coerces unknown to zero."""
    measured_by_currency: dict[str, Decimal]
    estimated_by_currency: dict[str, Decimal]
    target_currency: str | None
    converted_measured_total: Decimal | None
    converted_estimated_total: Decimal | None
    has_unknown_costs: bool
    has_missing_currency: bool
    has_mixed_currencies: bool
    has_stale_or_missing_fx: bool
    status: Literal["COMPLETE_HOMOGENEOUS", "COMPLETE_CONVERTED", "SEPARATED_BY_CURRENCY", "INCOMPLETE_MISSING_DATA"]
    entries: tuple[TypedCostEntry, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "measured_by_currency": {k: str(v) for k, v in sorted(self.measured_by_currency.items())},
            "estimated_by_currency": {k: str(v) for k, v in sorted(self.estimated_by_currency.items())},
            "target_currency": self.target_currency,
            "converted_measured_total": str(self.converted_measured_total) if self.converted_measured_total is not None else None,
            "converted_estimated_total": str(self.converted_estimated_total) if self.converted_estimated_total is not None else None,
            "has_unknown_costs": self.has_unknown_costs,
            "has_missing_currency": self.has_missing_currency,
            "has_mixed_currencies": self.has_mixed_currencies,
            "has_stale_or_missing_fx": self.has_stale_or_missing_fx,
            "status": self.status,
            "entry_count": len(self.entries),
        }


def _parse_decimal(raw: str | None) -> Decimal | None:
    if raw is None or not str(raw).strip():
        return None
    try:
        val = Decimal(str(raw).strip())
        return val if val.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def _normalize_currency(raw: str | None) -> str:
    code = (raw or "").strip().upper()
    return code if (len(code) == 3 and code.isascii() and code.isalpha()) else ""


def _measurement_source(record: UsageRecord) -> str:
    if record.stage == UsageStage.ACTUAL:
        return "local_offline" if record.pricing_source == "local_offline" else "provider_billed"
    if record.stage == UsageStage.ESTIMATED:
        return "provider_estimated"
    if record.stage == UsageStage.RESERVED:
        return "reserved_policy"
    return "unknown"


def _find_fx_quote(src_ccy: str, dst_ccy: str, quotes: Sequence[FxQuote], now_s: int) -> tuple[FxQuote | None, str]:
    stale: FxQuote | None = None
    for q in quotes:
        if q.base_currency.strip().upper() != src_ccy or q.quote_currency.strip().upper() != dst_ccy:
            continue
        if not isinstance(q.rate, Decimal) or not q.rate.is_finite() or q.rate <= Decimal("0"):
            continue
        if not (q.source or "").strip() or q.confidence != "verified" or int(q.max_age_seconds) <= 0:
            continue
        age = now_s - int(q.timestamp)
        if age < -300 or age > int(q.max_age_seconds):
            stale = stale or q
            continue
        return q, "ok"
    return (stale, "stale_fx_rate") if stale is not None else (None, "missing_fx_rate")


def summarize_multicurrency_records(
    records: Sequence[UsageRecord], *, target_currency: str | None = None,
    fx_quotes: Sequence[FxQuote] | None = None, now: int | None = None,
) -> MultiCurrencyCostSummary:
    """Aggregate UsageRecords with strict Decimal arithmetic, currency separation, and FX provenance."""
    now_s = int(time.time()) if now is None else int(now)
    dst_ccy = (_normalize_currency(target_currency) or None) if target_currency is not None else None
    quotes = tuple(fx_quotes or ())
    measured: dict[str, Decimal] = {}
    estimated: dict[str, Decimal] = {}
    conv_measured, conv_estimated, has_measured, has_estimated = Decimal("0"), Decimal("0"), False, False
    has_unknown, has_missing_ccy, has_fx_issue = False, False, (target_currency is not None and dst_ccy is None)
    entries: list[TypedCostEntry] = []

    for rec in records:
        ccy = _normalize_currency(rec.currency)
        amt = None if rec.stage == UsageStage.UNKNOWN else _parse_decimal(rec.amount)
        src_kind = _measurement_source(rec)
        if not ccy:
            has_missing_ccy = True
            entries.append(TypedCostEntry(rec.event_id, amt, "", src_kind, rec.provider, rec.model, None, None, None, None, "missing_currency", "missing_currency"))
            continue
        if amt is None:
            has_unknown = True
            entries.append(TypedCostEntry(rec.event_id, None, ccy, src_kind, rec.provider, rec.model, None, None, None, None, "unavailable", "missing_amount"))
            continue

        conv_src, fx_rate, fx_ts, conv_amt, conv_conf, miss = None, None, None, None, "unavailable", "complete"
        if dst_ccy is not None:
            if ccy == dst_ccy:
                conv_src, fx_rate, fx_ts, conv_amt, conv_conf = "identity", Decimal("1"), now_s, amt, "exact_same_currency"
            else:
                q, q_state = _find_fx_quote(ccy, dst_ccy, quotes, now_s)
                if q is not None and q_state == "ok":
                    conv_src, fx_rate, fx_ts, conv_amt, conv_conf = q.source, q.rate, q.timestamp, amt * q.rate, q.confidence
                else:
                    has_fx_issue, conv_conf, miss = True, ("stale_fx" if q_state == "stale_fx_rate" else "unavailable"), q_state
        entries.append(TypedCostEntry(rec.event_id, amt, ccy, src_kind, rec.provider, rec.model, conv_src, fx_rate, fx_ts, conv_amt, conv_conf, miss))
        if rec.stage == UsageStage.ACTUAL:
            measured[ccy] = measured.get(ccy, Decimal("0")) + amt
            has_measured = True
            if conv_amt is not None:
                conv_measured += conv_amt
        elif rec.stage in (UsageStage.ESTIMATED, UsageStage.RESERVED):
            estimated[ccy] = estimated.get(ccy, Decimal("0")) + amt
            has_estimated = True
            if conv_amt is not None:
                conv_estimated += conv_amt

    all_ccys = set(measured.keys()) | set(estimated.keys())
    has_mixed = len(all_ccys) > 1
    can_convert = dst_ccy is not None and not has_unknown and not has_missing_ccy and not has_fx_issue
    out_conv_m = conv_measured if (can_convert and has_measured) else None
    out_conv_e = conv_estimated if (can_convert and has_estimated) else None

    if has_unknown or has_missing_ccy or (target_currency is not None and has_fx_issue):
        status: Literal["COMPLETE_HOMOGENEOUS", "COMPLETE_CONVERTED", "SEPARATED_BY_CURRENCY", "INCOMPLETE_MISSING_DATA"] = "INCOMPLETE_MISSING_DATA"
    elif dst_ccy is not None and (has_measured or has_estimated):
        status = "COMPLETE_CONVERTED"
    elif has_mixed:
        status = "SEPARATED_BY_CURRENCY"
    else:
        status = "COMPLETE_HOMOGENEOUS"

    return MultiCurrencyCostSummary(
        measured_by_currency=measured, estimated_by_currency=estimated, target_currency=dst_ccy,
        converted_measured_total=out_conv_m, converted_estimated_total=out_conv_e,
        has_unknown_costs=has_unknown, has_missing_currency=has_missing_ccy,
        has_mixed_currencies=has_mixed, has_stale_or_missing_fx=has_fx_issue,
        status=status, entries=tuple(entries),
    )
