"""Cloud fallback — forward requests to Anthropic when routing decides CLOUD."""

from __future__ import annotations

import json
import logging
from typing import AsyncIterator, Callable

import httpx
from fastapi import HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from mekongd.config import MekongdConfig
from mekongd.schemas import MessagesRequest

log = logging.getLogger(__name__)

# Callback signature: (destination, tokens_in, tokens_out, model) → None
PersistFn = Callable[[str, int, int, str], None]


def _build_headers(cfg: MekongdConfig) -> dict:
    return {
        "x-api-key": cfg.anthropic_api_key or "",
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }


def _estimate_in(req: MessagesRequest) -> int:
    chars = len(req.get_system_text())
    for m in req.messages:
        if isinstance(m.content, str):
            chars += len(m.content)
        else:
            chars += sum(len(cb.text) for cb in m.content)
    return max(1, chars // 4)


async def forward(cfg: MekongdConfig, req: MessagesRequest, persist: PersistFn):
    """Forward to Anthropic. Preserves stream=true — pipes SSE bytes back."""
    if not cfg.anthropic_api_key:
        raise HTTPException(
            status_code=501,
            detail="Cloud fallback requested but ANTHROPIC_API_KEY not configured.",
        )
    url = f"{cfg.anthropic_fallback_url.rstrip('/')}/v1/messages"
    headers = _build_headers(cfg)
    body = req.model_dump(exclude_none=True)

    if not req.stream:
        return await _forward_json(url, headers, body, req, persist)

    return StreamingResponse(
        _sse_passthrough(url, headers, body, req, persist),
        media_type="text/event-stream",
    )


async def _forward_json(
    url: str, headers: dict, body: dict, req: MessagesRequest, persist: PersistFn
) -> JSONResponse:
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=30.0)) as client:
        resp = await client.post(url, headers=headers, json=body)
    try:
        data = resp.json() if resp.content else {}
    except ValueError:
        data = {
            "error": {
                "type": "proxy_parse_error",
                "message": (resp.text or "")[:500],
            }
        }
    usage = data.get("usage") or {}
    persist(
        "cloud",
        int(usage.get("input_tokens") or _estimate_in(req)),
        int(usage.get("output_tokens") or 0),
        req.model,
    )
    return JSONResponse(status_code=resp.status_code, content=data)


async def _sse_passthrough(
    url: str, headers: dict, body: dict, req: MessagesRequest, persist: PersistFn
) -> AsyncIterator[bytes]:
    """Stream raw SSE bytes from Anthropic → client. Parse usage from message_delta."""
    out_tokens = 0
    in_tokens = _estimate_in(req)
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10.0, read=600.0, write=30.0, pool=30.0)) as client:
        async with client.stream("POST", url, headers=headers, json=body) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data:") and "message_delta" in line:
                    out_tokens = _parse_delta_usage(line, out_tokens)
                yield (line + "\n").encode("utf-8")
            yield b"\n"
    persist("cloud", in_tokens, out_tokens, req.model)


def _parse_delta_usage(line: str, current: int) -> int:
    """Parse output_tokens from an Anthropic message_delta SSE line."""
    try:
        payload = line.split(":", 1)[1].strip()
        parsed = json.loads(payload)
        return int(parsed.get("usage", {}).get("output_tokens") or current)
    except (ValueError, KeyError):
        return current
