"""FastAPI proxy exposing Anthropic-compat /v1/messages with routing + stats."""

from __future__ import annotations

import logging
import uuid
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from sse_starlette.sse import EventSourceResponse

from mekongd import __version__
from mekongd.cloud import forward as cloud_forward
from mekongd.config import MekongdConfig, load_config
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
    aggregate_signals,
    aggregate_stats,
    estimate_savings,
    record_route,
    record_signal,
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
    s = aggregate_stats(cfg.stats_db_path)
    lines = [
        "# HELP mekongd_requests_total Total /v1/messages requests by destination",
        "# TYPE mekongd_requests_total counter",
        f'mekongd_requests_total{{destination="local"}} {s.local_requests}',
        f'mekongd_requests_total{{destination="cloud"}} {s.cloud_requests}',
        "# HELP mekongd_tokens_in_total Total input tokens accepted",
        "# TYPE mekongd_tokens_in_total counter",
        f"mekongd_tokens_in_total {s.total_tokens_in}",
        "# HELP mekongd_tokens_out_total Total output tokens produced",
        "# TYPE mekongd_tokens_out_total counter",
        f"mekongd_tokens_out_total {s.total_tokens_out}",
        "# HELP mekongd_cost_saved_usd_total Estimated USD saved by local routing",
        "# TYPE mekongd_cost_saved_usd_total counter",
        f"mekongd_cost_saved_usd_total {s.total_cost_saved_usd:.6f}",
        "# HELP mekongd_local_ratio Share of requests routed to local runtime (0..1)",
        "# TYPE mekongd_local_ratio gauge",
        f"mekongd_local_ratio {s.local_pct / 100:.6f}",
    ]
    sigs = aggregate_signals(cfg.stats_db_path)
    good, bad = sigs.get("good", 0), sigs.get("bad", 0)
    total = good + bad
    ratio = good / total if total else 0.0
    lines.extend(
        [
            "# HELP mekongd_signals_total Operator feedback signals by kind (Pillar 3)",
            "# TYPE mekongd_signals_total counter",
            f'mekongd_signals_total{{kind="good"}} {good}',
            f'mekongd_signals_total{{kind="bad"}} {bad}',
            "# HELP mekongd_signals_ratio Share of good signals (0..1, 0 when no signals)",
            "# TYPE mekongd_signals_ratio gauge",
            f"mekongd_signals_ratio {ratio:.6f}",
        ]
    )
    return "\n".join(lines) + "\n"


@app.post("/v1/messages")
async def messages(req: MessagesRequest):
    cfg, runtime, router = _get_deps()
    decision = router.decide(req)
    log.info("route: %s (%s)", decision.destination, decision.reason)
    message_id = f"msg_{uuid.uuid4().hex[:16]}"

    if decision.destination == "cloud":
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
    ok = record_signal(cfg.stats_db_path, req.kind, req.note)
    return {"accepted": ok, "kind": req.kind}


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
    saved = (
        estimate_savings(
            in_tok, out_tok, cfg.cloud_input_usd_per_mtok, cfg.cloud_output_usd_per_mtok
        )
        if destination == "local"
        else 0.0
    )
    record_route(
        cfg.stats_db_path,
        "POST /v1/messages",
        in_tok,
        out_tok,
        destination,  # type: ignore[arg-type]
        saved,
        model,
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
