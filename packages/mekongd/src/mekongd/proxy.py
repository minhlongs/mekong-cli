"""FastAPI proxy exposing Anthropic-compat /v1/messages with routing + stats."""

from __future__ import annotations

import logging
import uuid
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from sse_starlette.sse import EventSourceResponse

from mekongd import __version__
from mekongd.cloud import forward as cloud_forward
from mekongd.config import MekongdConfig, load_config
from mekongd.metrics_exposition import build_metrics_body
from mekongd.router import Router
from mekongd.runtime import BaseRuntime, get_runtime
from mekongd.schemas import (
    ContentBlock,
    ContentBlockDelta,
    ContentBlockDeltaEvent,
    ContentBlockStartEvent,
    ContentBlockStopEvent,
    MessageDeltaEvent,
    MessageDeltaPayload,
    MessageDeltaUsage,
    MessageStartEvent,
    MessageStopEvent,
    MessagesRequest,
    MessagesResponse,
    SignalRequest,
    Usage,
)
from mekongd.stats import (
    aggregate_signals_by_model,
    cloud_cost_by_model,
    estimate_savings,
    list_recent_signals,
    record_route,
    record_signal,
    today_cloud_spent_usd,
)

log = logging.getLogger(__name__)
app = FastAPI(title="mekongd", version=__version__)

_config: MekongdConfig | None = None
_runtime: BaseRuntime | None = None
_router: Router | None = None


def _get_deps() -> tuple[MekongdConfig, BaseRuntime, Router]:
    global _config, _runtime, _router
    if _config is None:
        _config = load_config()
    if _runtime is None:
        _runtime = get_runtime(_config)
    if _router is None:
        _router = Router(_config.policy)
    return _config, _runtime, _router


def set_runtime(runtime: BaseRuntime, config: MekongdConfig | None = None) -> None:
    """Test hook — inject runtime + optional config; rebuilds router."""
    global _runtime, _config, _router
    _runtime = runtime
    if config is not None:
        _config = config
        _router = Router(config.policy)


@app.get("/healthz")
async def healthz():
    _, runtime, _ = _get_deps()
    return {"status": "ok", "runtime": runtime.name, "version": __version__}


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    """Prometheus text-format exposition — aggregated from stats sqlite."""
    cfg, _, _ = _get_deps()
    return build_metrics_body(cfg)


@app.post("/v1/messages")
async def messages(req: MessagesRequest):
    cfg, runtime, router = _get_deps()
    decision = router.decide(req)
    log.info("route: %s (%s)", decision.destination, decision.reason)
    message_id = f"msg_{uuid.uuid4().hex[:16]}"

    if decision.destination == "cloud":
        _enforce_cloud_budget(cfg)
        return await cloud_forward(cfg, req, _make_persist(cfg))

    if not req.stream:
        text = await runtime.generate(req)
        in_tok, out_tok = _estimate_in(req), max(1, len(text) // 4)
        _persist(cfg, "local", in_tok, out_tok, req.model)
        return MessagesResponse(
            id=message_id,
            model=req.model,
            content=[ContentBlock(type="text", text=text)],
            usage=Usage(input_tokens=in_tok, output_tokens=out_tok),
        )

    return EventSourceResponse(_stream_local(cfg, runtime, req, message_id))


@app.post("/v1/signals", status_code=202)
async def signals(req: SignalRequest):
    """Pillar 3 — operator feedback loop. Persists one signal, returns 202."""
    cfg, _, _ = _get_deps()
    ok = record_signal(cfg.stats_db_path, req.kind, req.note, req.model)
    return {"accepted": ok, "kind": req.kind}


@app.get("/v1/signals/breakdown")
async def signals_breakdown(
    hours: int | None = None, source: str | None = None
):
    """Operator diagnostic — good/bad counts grouped by model.

    hours: optional window filter (e.g. ?hours=24). Legacy rows bucket under ''.
    source: ``user`` or ``auto`` — filter by note origin (``#user`` marker
            set by agent-forest user-feedback endpoint). Unknown values fall
            back to no filter.
    """
    cfg, _, _ = _get_deps()
    effective = source if source in ("user", "auto") else None
    return {
        "by_model": aggregate_signals_by_model(
            cfg.stats_db_path, hours, source=effective
        )
    }


@app.get("/v1/cost/by-model")
async def cost_by_model(hours: int | None = None):
    """Operator diagnostic — cloud spend grouped by model.

    hours: optional window filter (e.g. ?hours=168 for last week).
    Returns only models with non-zero cost.
    """
    cfg, _, _ = _get_deps()
    return {"by_model": cloud_cost_by_model(cfg.stats_db_path, hours)}


@app.get("/v1/signals/recent")
async def signals_recent(limit: int = 20):
    """Operator review — last N signals (newest first) with notes."""
    cfg, _, _ = _get_deps()
    return {"signals": list_recent_signals(cfg.stats_db_path, limit)}


async def _stream_local(
    cfg: MekongdConfig,
    runtime: BaseRuntime,
    req: MessagesRequest,
    message_id: str,
) -> AsyncIterator[dict]:
    in_tok = _estimate_in(req)
    start_msg = MessagesResponse(
        id=message_id,
        model=req.model,
        content=[],
        usage=Usage(input_tokens=in_tok, output_tokens=0),
    )
    yield _sse(MessageStartEvent(message=start_msg))
    yield _sse(ContentBlockStartEvent(content_block=ContentBlock(type="text", text="")))
    out_chars = 0
    async for chunk in runtime.stream(req):
        out_chars += len(chunk)
        yield _sse(ContentBlockDeltaEvent(delta=ContentBlockDelta(text=chunk)))
    yield _sse(ContentBlockStopEvent())
    out_tok = max(1, out_chars // 4)
    yield _sse(
        MessageDeltaEvent(
            delta=MessageDeltaPayload(stop_reason="end_turn"),
            usage=MessageDeltaUsage(output_tokens=out_tok),
        )
    )
    yield _sse(MessageStopEvent())
    _persist(cfg, "local", in_tok, out_tok, req.model)


def _enforce_cloud_budget(cfg: MekongdConfig) -> None:
    """Raise 402 if today's cloud spend has reached cfg.cloud_daily_budget_usd."""
    budget = cfg.cloud_daily_budget_usd
    if budget is None or budget <= 0:
        return
    spent = today_cloud_spent_usd(cfg.stats_db_path)
    if spent >= budget:
        raise HTTPException(
            status_code=402,
            detail=(
                f"Cloud daily budget reached: spent ${spent:.2f} "
                f">= cap ${budget:.2f}. Route locally or raise MEKONGD_CLOUD_DAILY_BUDGET_USD."
            ),
        )


def _make_persist(cfg: MekongdConfig):
    """Closure adapter — matches cloud.PersistFn signature."""

    def _fn(destination: str, in_tok: int, out_tok: int, model: str) -> None:
        _persist(cfg, destination, in_tok, out_tok, model)

    return _fn


def _persist(
    cfg: MekongdConfig,
    destination: str,
    in_tok: int,
    out_tok: int,
    model: str,
) -> None:
    estimate = estimate_savings(
        in_tok, out_tok, cfg.cloud_input_usd_per_mtok, cfg.cloud_output_usd_per_mtok
    )
    saved = estimate if destination == "local" else 0.0
    cost = estimate if destination == "cloud" else 0.0
    record_route(
        cfg.stats_db_path,
        "POST /v1/messages",
        in_tok,
        out_tok,
        destination,  # type: ignore[arg-type]
        saved,
        model,
        cost,
    )


def _sse(event) -> dict:
    return {"event": event.type, "data": event.model_dump_json()}


def _estimate_in(req: MessagesRequest) -> int:
    chars = len(req.system or "")
    for m in req.messages:
        if isinstance(m.content, str):
            chars += len(m.content)
        else:
            chars += sum(len(cb.text) for cb in m.content)
    return max(1, chars // 4)
