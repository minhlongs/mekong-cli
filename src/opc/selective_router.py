"""Profile 4 Selective AI Router with Field-Level source_span Provenance & Fail-Closed Budget."""
from __future__ import annotations

import json
import os
import re
import time
import unicodedata
import urllib.error
import urllib.request
import uuid
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable, Final

from src.opc.models import UsageRecord, UsageStage
from src.opc.usage import UsageLedger

_STOP_TOKENS: Final[frozenset[str]] = frozenset({"tich", "hop", "dich", "thiet", "giai", "phap", "goi", "lam"})
_QTY_UNIT_RE: Final[re.Pattern[str]] = re.compile(r"(?i)\b(\d+)\s*(giờ|gio|h|thùng|thung|gói|goi|cái|cai|bộ|bo|tháng|thang|ngày|ngay|kg)\b")
_QTY_PREFIX_RE: Final[re.Pattern[str]] = re.compile(r"(?i)(?:(?<=\s)|^)(?:x|sl:?|số\s*lượng:?)\s*(\d+)\b")


@dataclass(frozen=True)
class FieldCitation:
    """Character-exact provenance span anchoring an extracted field to customer input."""
    field_name: str
    value: Any
    source_quote: str
    start_char: int
    end_char: int


@dataclass(frozen=True)
class SelectiveRouteResult:
    """Structured outcome from SelectiveRouter across deterministic, local, or cloud tiers."""
    mode: str
    provider: str
    model: str
    extracted: dict[str, Any]
    citations: tuple[FieldCitation, ...]
    confidence: float
    latency_ms: float
    unknown_cost: bool


def _fold_with_offsets(text: str) -> tuple[str, list[int]]:
    chars, starts = [], []
    for idx, ch in enumerate(text):
        if unicodedata.combining(ch):
            continue
        base = "d" if ch in ("đ", "Đ") else unicodedata.normalize("NFD", ch)[0].lower()
        chars.append(" " if base in ("_", "-") else base)
        starts.append(idx)
    starts.append(len(text))
    return "".join(chars), starts


def extract_deterministic_citations(message_text: str, service_catalog: Mapping[str, Decimal]) -> tuple[dict[str, Any], tuple[FieldCitation, ...], float]:
    """Deterministically extract services, quantities/hours, and notes with exact char spans."""
    folded, offsets = _fold_with_offsets(message_text)
    citations: list[FieldCitation] = []
    matched_services: list[str] = []
    for svc_key in service_catalog:
        phrase = _fold_with_offsets(svc_key)[0].strip()
        for needle in [phrase] + [tok for tok in phrase.split() if len(tok) >= 4 and tok not in _STOP_TOKENS]:
            if needle and (m := re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", folded)) is not None:
                s, e = offsets[m.start()], offsets[m.end()]
                matched_services.append(svc_key)
                citations.append(FieldCitation("requested_services", svc_key, message_text[s:e], s, e))
                break

    qty_val, qty_field = None, "quantity"
    if (mu := _QTY_UNIT_RE.search(message_text)) is not None:
        s, e, qty_val = mu.span(0)[0], mu.span(0)[1], int(mu.group(1))
        qty_field = "estimated_hours" if mu.group(2).lower() in ("giờ", "gio", "h") else "quantity"
        citations.append(FieldCitation(qty_field, qty_val, message_text[s:e], s, e))
    elif (mp := _QTY_PREFIX_RE.search(message_text)) is not None:
        s, e, qty_val = mp.span(0)[0], mp.span(0)[1], int(mp.group(1))
        citations.append(FieldCitation("quantity", qty_val, message_text[s:e], s, e))

    if stripped := message_text.strip():
        ns, ne = len(message_text) - len(message_text.lstrip()), len(message_text.rstrip())
        citations.append(FieldCitation("customer_notes", message_text[ns:ne], message_text[ns:ne], ns, ne))

    extracted: dict[str, Any] = {"requested_services": tuple(matched_services), "customer_notes": stripped}
    if qty_val is not None:
        extracted[qty_field] = qty_val
        extracted.setdefault("estimated_hours", qty_val)
    conf = 0.95 if (matched_services and qty_val is not None) else (0.60 if (matched_services or qty_val is not None) else 0.25)
    return extracted, tuple(citations), conf


def _anchor_citations(message_text: str, raw_citations: Any, fallback: tuple[FieldCitation, ...]) -> tuple[FieldCitation, ...]:
    if not isinstance(raw_citations, (list, tuple)):
        return fallback
    anchored = list(fallback)
    for item in raw_citations:
        if not isinstance(item, Mapping) or not (quote := str(item.get("source_quote", ""))):
            continue
        s, e = int(item.get("start_char", -1)), int(item.get("end_char", -1))
        if s < 0 or e > len(message_text) or message_text[s:e] != quote:
            if (pos := message_text.find(quote)) < 0:
                continue
            s, e = pos, pos + len(quote)
        anchored.append(FieldCitation(str(item.get("field_name", "extracted")), item.get("value"), quote, s, e))
    return tuple(anchored)


class SelectiveRouter:
    """3-Tier Router: Deterministic Python -> Local MLX/LiteLLM (<1500ms) -> Cloud Fallback."""

    def __init__(
        self, usage_ledger: UsageLedger, service_catalog: Mapping[str, Decimal] | None = None, *,
        local_endpoint: str | None = None, local_model: str = "local-qwen-14b-mlx", cloud_model: str = "gemini-2.5-flash",
        timeout_ms: int = 1500, min_confidence: float = 0.85, fail_closed_budget_enforcement: bool = True,
        estimated_call_budget: str = "50.00", hard_budget_limit: str | None = None, currency: str = "VND",
        local_transport: Callable[[str, dict[str, str], bytes, float], tuple[int, bytes]] | None = None,
        cloud_fallback_fn: Callable[[str, Mapping[str, Decimal]], dict[str, Any]] | None = None,
    ) -> None:
        self.usage_ledger, self.service_catalog = usage_ledger, service_catalog or {}
        self.local_endpoint = local_endpoint if local_endpoint is not None else (os.getenv("MLX_BASE_URL") or os.getenv("LITELLM_BASE_URL"))
        self.local_model, self.cloud_model, self.timeout_ms, self.min_confidence = local_model, cloud_model, int(timeout_ms), float(min_confidence)
        self.fail_closed_budget_enforcement, self.estimated_call_budget = fail_closed_budget_enforcement, estimated_call_budget
        self.hard_budget_limit, self.currency, self._local_transport, self.cloud_fallback_fn = hard_budget_limit, currency, local_transport, cloud_fallback_fn

    def _post_json(self, url: str, body: bytes, timeout_s: float) -> tuple[int, bytes]:
        if self._local_transport is not None:
            return self._local_transport(url, {"Content-Type": "application/json"}, body, timeout_s)
        if not url.lower().startswith(("http://", "https://")):
            raise urllib.error.URLError(f"Unsupported endpoint scheme: {url}")
        with urllib.request.urlopen(urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST"), timeout=timeout_s) as resp:  # noqa: S310
            return int(resp.status), resp.read()

    def _record_llm_usage(self, run_id: str, provider: str, model: str, resp: Mapping[str, Any]) -> bool:
        usage, now, eid = resp.get("usage"), int(time.time()), f"use_{uuid.uuid4().hex[:12]}"
        if isinstance(usage, Mapping) and usage.get("cost") is not None and usage.get("total_tokens") is not None:
            self.usage_ledger.record_usage(UsageRecord(eid, run_id, 1, UsageStage.ACTUAL, provider, model, int(usage["total_tokens"]), "0.00", str(usage["cost"]), self.currency, "owner", "provider_usage", now))
            return False
        tok = int(usage["total_tokens"]) if isinstance(usage, Mapping) and usage.get("total_tokens") is not None else None
        self.usage_ledger.record_usage(UsageRecord(eid, run_id, 1, UsageStage.UNKNOWN, provider, model, tok, None, None, self.currency, "owner", "UNKNOWN_COST_EVENT", now))
        return True

    def route(self, message_text: str, *, run_id: str = "run_router", service_catalog: Mapping[str, Decimal] | None = None, hard_budget_limit: str | None = None) -> SelectiveRouteResult:
        t0 = time.monotonic()
        catalog = service_catalog if service_catalog is not None else self.service_catalog
        det_ext, det_cits, det_conf = extract_deterministic_citations(message_text, catalog)
        if det_conf >= self.min_confidence:
            return SelectiveRouteResult("deterministic", "deterministic_python", "rule_extractor_v1", det_ext, det_cits, det_conf, (time.monotonic() - t0) * 1000.0, False)
        if self.local_endpoint:
            deadline_s = max(0.05, (self.timeout_ms * 0.92) / 1000.0)
            req_bytes = json.dumps({"model": self.local_model, "messages": [{"role": "user", "content": message_text}]}).encode("utf-8")
            pool = ThreadPoolExecutor(max_workers=1)
            try:
                status, raw = pool.submit(self._post_json, self.local_endpoint, req_bytes, deadline_s).result(timeout=deadline_s)
                if 200 <= status < 300:
                    parsed = json.loads(raw.decode("utf-8"))
                    unk = self._record_llm_usage(run_id, "local_openai_compat", self.local_model, parsed)
                    return SelectiveRouteResult("local_llm", "local_openai_compat", self.local_model, dict(parsed.get("extracted") or det_ext), _anchor_citations(message_text, parsed.get("citations"), det_cits), float(parsed.get("confidence", 0.88)), (time.monotonic() - t0) * 1000.0, unk)
            except (FuturesTimeoutError, TimeoutError, urllib.error.URLError, OSError, ValueError):
                pass
            finally:
                pool.shutdown(wait=False, cancel_futures=True)
        reserved = self.usage_ledger.reserve_budget(f"res_{uuid.uuid4().hex[:12]}", run_id, self.estimated_call_budget, self.currency, "owner", int(time.time()), hard_budget_limit if hard_budget_limit is not None else self.hard_budget_limit)
        if self.fail_closed_budget_enforcement and not reserved:
            raise PermissionError("Budget reservation failed (fail-closed)")
        if self.cloud_fallback_fn is None:
            return SelectiveRouteResult("low_confidence_halt", "deterministic_python", "rule_extractor_v1", det_ext, det_cits, det_conf, (time.monotonic() - t0) * 1000.0, False)
        cloud_resp = self.cloud_fallback_fn(message_text, catalog)
        unk = self._record_llm_usage(run_id, "cloud_fallback", str(cloud_resp.get("model", self.cloud_model)), cloud_resp)
        return SelectiveRouteResult("cloud_fallback", "cloud_fallback", str(cloud_resp.get("model", self.cloud_model)), dict(cloud_resp.get("extracted") or det_ext), _anchor_citations(message_text, cloud_resp.get("citations"), det_cits), float(cloud_resp.get("confidence", 0.90)), (time.monotonic() - t0) * 1000.0, unk)
