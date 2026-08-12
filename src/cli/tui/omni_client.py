"""Async OmniRoute client with SSE streaming for the chat TUI."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

import httpx

from .chat_config import CHAT_PATH, resolve_base_url, resolve_token


@dataclass
class ChatChunk:
    """One SSE chunk from the gateway."""

    text: str = ""
    reasoning_text: str = ""
    actual_model: str = ""
    provider: str = ""
    usage: dict[str, Any] = field(default_factory=dict)
    done: bool = False


DeltaHandler = Callable[[ChatChunk], Awaitable[None]]

_CONNECT_TIMEOUT = 5.0
_FIRST_BYTE_TIMEOUT = 60.0
_TOTAL_TIMEOUT = 300.0


class OmniClient:
    """Minimal OpenAI-compatible chat client against OmniRoute."""

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = (base_url or resolve_base_url()).rstrip("/")
        self.token = token or resolve_token()
        self._transport = transport

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def stream_chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        on_delta: DeltaHandler,
    ) -> ChatChunk:
        """Stream a chat completion, invoking on_delta per chunk. Returns final chunk."""
        url = f"{self.base_url}{CHAT_PATH}"
        body = {"model": model, "messages": messages, "stream": True}
        timeout = httpx.Timeout(
            connect=_CONNECT_TIMEOUT,
            read=_FIRST_BYTE_TIMEOUT,
            write=30.0,
            pool=_TOTAL_TIMEOUT,
        )
        final = ChatChunk()
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                kwargs: dict[str, Any] = {"timeout": timeout}
                if self._transport is not None:
                    kwargs["transport"] = self._transport
                async with httpx.AsyncClient(**kwargs) as client:
                    async with client.stream(
                        "POST", url, headers=self._headers(), json=body
                    ) as resp:
                        if resp.status_code >= 400:
                            raw = await resp.aread()
                            raise httpx.HTTPStatusError(
                                f"HTTP {resp.status_code}: {raw.decode(errors='replace')[:400]}",
                                request=resp.request,
                                response=resp,
                            )
                        async for chunk in self._iter_sse(resp):
                            merged = self._merge(final, chunk)
                            final = merged
                            await on_delta(merged)
                return final
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as exc:
                last_error = exc
                if attempt == 0:
                    continue
                raise RuntimeError(
                    f"Cannot reach OmniRoute at {self.base_url}: {exc.__class__.__name__}"
                ) from exc
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(f"Gateway error: {exc}") from exc
        raise RuntimeError(f"Connection failed: {last_error}")

    async def complete(
        self, model: str, messages: list[dict[str, str]]
    ) -> ChatChunk:
        """Non-streaming completion (used by --raw before streaming lands)."""
        url = f"{self.base_url}{CHAT_PATH}"
        body = {"model": model, "messages": messages, "stream": False}
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=5.0)) as client:
            resp = await client.post(url, headers=self._headers(), json=body)
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Gateway error HTTP {resp.status_code}: {resp.text[:400]}"
                )
            data = resp.json()
        chunk = ChatChunk()
        chunk.actual_model = str(data.get("model", ""))
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        chunk.text = str(msg.get("content") or "")
        chunk.reasoning_text = str(msg.get("reasoning_content") or "")
        chunk.usage = data.get("usage") or {}
        chunk.done = True
        return chunk

    @staticmethod
    async def _iter_sse(resp: httpx.Response):
        """Yield parsed SSE data payloads, buffering partial JSON lines."""
        buffer = ""
        async for line in resp.aiter_lines():
            if not line or line.startswith(":"):
                continue
            if line.startswith("data:"):
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                buffer += payload
                try:
                    data = json.loads(buffer)
                except json.JSONDecodeError:
                    continue  # partial JSON; wait for next data line
                buffer = ""
                yield data

    @staticmethod
    def _merge(final: ChatChunk, raw: dict[str, Any]) -> ChatChunk:
        chunk = ChatChunk()
        chunk.actual_model = str(raw.get("model") or "") or final.actual_model
        provider = raw.get("provider")
        chunk.provider = str(provider) if provider else final.provider
        choices = raw.get("choices") or []
        if choices:
            delta = choices[0].get("delta") or {}
            if delta.get("content"):
                chunk.text = str(delta["content"])
            if delta.get("reasoning_content"):
                chunk.reasoning_text = str(delta["reasoning_content"])
            if delta.get("reasoning"):
                chunk.reasoning_text += str(delta["reasoning"])
            details = delta.get("reasoning_details") or []
            for item in details:
                if isinstance(item, dict) and item.get("text"):
                    chunk.reasoning_text += str(item["text"])
            if choices[0].get("finish_reason"):
                chunk.done = True
        usage = raw.get("usage")
        if usage:
            chunk.usage = usage
        if not chunk.actual_model and not chunk.text and not chunk.reasoning_text:
            chunk.done = final.done
        return chunk
