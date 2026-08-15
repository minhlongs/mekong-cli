"""Mekong CLI — core LLM client.

OpenAI-compatible chat completions through the OmniRoute gateway.
All models resolve through the gateway (fable/sonnet/opus/haiku/strategist).

OmniRoute essence ports:
- A1: provider breaker + cooldown-aware retry (respect Retry-After / "Resets
  in N", total wait capped by RETRY_BUDGET_MS per request).
- A3: stream throughput watchdog (non-streaming variant): two-tier request
  watchdog — stall detection + hard timeout.
- B4: model-family fallback when the requested model is breaker-locked.
- B5: session affinity pin — pinned model wins while alive; 429 unpins.
- B7: learned rate limits recorded from error bodies / response headers.
"""

from __future__ import annotations

import json
import os
import socket
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from .models import fallback_chain, resolve_or_fallback
from .resilience import (RETRY_BUDGET_MS, Breaker, breaker as default_breaker,
                         parse_retry_after_seconds)

DEFAULT_BASE_URL = "http://192.168.1.231:20128"
DEFAULT_TOKEN = "sk-b9eb30e8d08b6389-bdc6e3-a980fe1f"

# A3: watchdog tiers (non-streaming)
WATCHDOG_STALL_S = 60      # không có response trong 60s đầu → stall
WATCHDOG_HARD_S = 300      # timeout cứng tuyệt đối

# bounded log của stall/hard-timeout alerts (B7/A3 — hiển thị trong doctor)
STALL_ALERTS: list[str] = []
_MAX_ALERTS = 20


def _stall_alert(msg: str) -> None:
    STALL_ALERTS.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
    del STALL_ALERTS[: max(0, len(STALL_ALERTS) - _MAX_ALERTS)]


def gateway_base_url() -> str:
    return os.environ.get("OMNIROUTE_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def gateway_token() -> str:
    return os.environ.get("OMNIROUTE_TOKEN", DEFAULT_TOKEN)


class LLMError(RuntimeError):
    pass


def effective_model_with_pin(session: Any | None, requested: str) -> str:
    """B5: pin thắng forced khi còn sống (unpin_after > now)."""
    if session is not None and getattr(session, "pin_active", lambda: False)():
        return session.provider_pin
    return requested


@dataclass
class LLMClient:
    base_url: str = field(default_factory=gateway_base_url)
    token: str = field(default_factory=gateway_token)
    timeout: int = 120
    max_retries: int = 2
    breaker: Breaker = field(default_factory=lambda: default_breaker)

    @property
    def provider(self) -> str:
        """Provider key cho breaker/spend (host của gateway)."""
        host = self.base_url.split("//")[-1].split(":")[0]
        return host or "omniroute"

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

    def _attempt(self, body: dict[str, Any], timeout: int) -> dict[str, Any]:
        """One HTTP POST. Raises HTTPError (retryable statuses handled by chat)."""
        req = urllib.request.Request(
            self.base_url + "/api/v1/chat/completions",
            json.dumps(body).encode(),
            self._headers(),
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            # B7: học rate limits từ headers (nếu gateway expose)
            remaining = resp.headers.get("X-RateLimit-Remaining")
            reset = resp.headers.get("X-RateLimit-Reset")
            if remaining or reset:
                try:
                    self.breaker.record_rate_limit(
                        body.get("model", "?"),
                        remaining=float(remaining) if remaining else None,
                        reset_in=float(reset) if reset else None,
                    )
                except ValueError:
                    pass
            return json.loads(resp.read().decode())

    def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 4096,
        tools: list[dict[str, Any]] | None = None,
        timeout: int | None = None,
        pin: str = "",
        caller: str = "",
    ) -> dict[str, Any]:
        """Single (non-streaming) chat completion. Returns the full response dict.

        A1: locked models are skipped (family fallback B4); retryable HTTP
        errors record failures with cooldown-aware waits capped by the
        per-request retry budget. B5: `pin` = session id whose provider_pin
        wins while alive; 429 unpins it. B7: rate-limit info is learned from
        error bodies / response headers.
        """
        budget_s = RETRY_BUDGET_MS / 1000.0
        start = time.monotonic()
        session = self._load_session(pin)
        requested = effective_model_with_pin(session, model)
        # B4: banned → fable; locked → sibling/family kế (guard qwen không bao giờ chạm)
        entry = resolve_or_fallback(
            requested, locked=lambda m: self.breaker.is_locked(self.provider, m)
        )
        current = entry.id
        candidates = [
            m for m in fallback_chain(entry.id)
            if not self.breaker.is_locked(self.provider, m)
        ]
        last_err: Exception | None = None

        for _attempt_n in range(self.max_retries + 1):
            # A1: locked → thử sibling (B4); hết candidate → raise luôn
            if self.breaker.is_locked(self.provider, current):
                while candidates and self.breaker.is_locked(self.provider, candidates[0]):
                    candidates.pop(0)
                if candidates:
                    current = candidates.pop(0)
                else:
                    remaining = self.breaker.remaining(self.provider, current)
                    raise LLMError(
                        f"model '{model}' locked ({remaining:.0f}s, breaker) — "
                        f"no unlocked family fallback"
                    ) from None

            body: dict[str, Any] = {
                "model": current,
                "messages": messages,
                "max_tokens": max_tokens,
            }
            if tools:
                body["tools"] = tools

            try:
                data = self._attempt(body, timeout or self.timeout)
                self.breaker.record_success(self.provider, current)
                self._record_usage(current, data, pin, caller)
                if session is not None:
                    session.last_model = current
                    self._save_session(session)
                return data
            except urllib.error.HTTPError as e:
                detail = e.read().decode()[:300]
                retry_after = parse_retry_after_seconds(
                    (e.headers or {}).get("Retry-After") if hasattr(e, "headers") else None
                ) or parse_retry_after_seconds(detail)
                self.breaker.record_rate_limit(
                    current, reset_in=retry_after, remaining=None
                )
                if e.code == 429:
                    # B5: 429 → unpin + ghi failure (sessionAffinityPin fix)
                    if session is not None:
                        session.unpin()
                        self._save_session(session)
                    self.breaker.record_failure(
                        self.provider, current, retry_after=retry_after, reason="HTTP 429"
                    )
                last_err = LLMError(f"HTTP {e.code}: {detail}")
                if e.code in (429, 502, 503, 504):
                    if e.code != 429:
                        self.breaker.record_failure(
                            self.provider, current, retry_after=retry_after,
                            reason=f"HTTP {e.code}",
                        )
                    wait = self.breaker.remaining(self.provider, current) or 1.0
                    if time.monotonic() - start + wait > budget_s:
                        raise LLMError(
                            f"retry budget exhausted ({budget_s:.0f}s cap) after "
                            f"HTTP {e.code} on '{current}'"
                        ) from last_err
                    time.sleep(wait)
                    continue
                raise last_err from None
            except (socket.timeout, TimeoutError):
                # A3: stall → abort + record_failure (không retry)
                self.breaker.record_failure(
                    self.provider, current, reason="stall/timeout"
                )
                raise LLMError(
                    f"stall: no response from '{current}' within "
                    f"{timeout or self.timeout}s (socket timeout)"
                ) from None
            except Exception as e:  # noqa: BLE001 — network hiccup → retry
                self.breaker.record_failure(self.provider, current, reason="network")
                last_err = LLMError(str(e)[:300])
                if time.monotonic() - start >= budget_s:
                    raise last_err from None
        raise last_err or LLMError("unknown failure")

    # ── A3: watchdog (non-streaming variant) ─────────────────

    def chat_with_watchdog(
        self,
        model: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 4096,
        tools: list[dict[str, Any]] | None = None,
        pin: str = "",
        caller: str = "",
        stall_seconds: int = WATCHDOG_STALL_S,
        hard_timeout: int = WATCHDOG_HARD_S,
    ) -> dict[str, Any]:
        """Two-tier watchdog wrapper: stall detection + hard timeout.

        Tier 1 (stall): socket timeout = stall_seconds — response không về trong
        60s đầu → abort + record_failure + stall_alert.
        Tier 2 (hard): worker bị treo quá hard_timeout → abort + record_failure.
        """
        result: dict[str, Any] = {}
        errors: list[Exception] = []

        def worker() -> None:
            try:
                result.update(
                    self.chat(
                        model, messages, max_tokens=max_tokens, tools=tools,
                        timeout=stall_seconds, pin=pin, caller=caller,
                    )
                )
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        t.join(timeout=hard_timeout)
        if t.is_alive():
            self.breaker.record_failure(self.provider, model, reason="watchdog-hard-timeout")
            _stall_alert(
                f"hard timeout: '{model}' exceeded {hard_timeout}s — aborted + failure recorded"
            )
            raise LLMError(f"watchdog hard timeout after {hard_timeout}s ('{model}')")
        if errors:
            e = errors[0]
            if isinstance(e, LLMError) and "stall" in str(e):
                _stall_alert(f"stall: '{model}' no response within {stall_seconds}s — failure recorded")
            raise e
        return result

    # ── helpers ──────────────────────────────────────────────

    def _record_usage(
        self, model: str, data: dict[str, Any], pin: str = "", caller: str = ""
    ) -> None:
        """A2: ghi spend mỗi response (token counts + cost estimate)."""
        usage = data.get("usage") or {}
        in_tok = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
        out_tok = usage.get("completion_tokens") or usage.get("output_tokens") or 0
        if not in_tok and not out_tok:
            return
        from .spend import record_spend

        record_spend(
            self.provider, model, int(in_tok), int(out_tok),
            caller=caller or pin,
        )

    def _load_session(self, pin: str) -> Any | None:
        if not pin:
            return None
        try:
            from .session import SessionStore

            return SessionStore().get(pin)
        except Exception:  # noqa: BLE001 — pin không tồn tại → bỏ qua
            return None

    def _save_session(self, session: Any) -> None:
        try:
            from .session import SessionStore

            SessionStore().save(session)
        except Exception:  # noqa: BLE001
            pass

    def text(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> str:
        """Convenience: return just the assistant text."""
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        data = self.chat(model, messages, max_tokens=max_tokens)
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError):
            return json.dumps(data)[:500]

    def ping(self, model: str = "claude-fable-5") -> tuple[bool, str]:
        """Health check for one model. Returns (ok, detail).

        Models often reply something other than an exact PONG; any short
        non-error reply proves the round-trip works.
        """
        try:
            reply = self.text(model, "Reply exactly: PONG", max_tokens=16)
            ok = bool(reply.strip()) and "error" not in reply.lower()[:40]
            return ok, f"ok ({reply.strip()[:40]})"
        except Exception as e:
            return False, str(e)[:120]
