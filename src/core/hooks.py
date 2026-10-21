# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
"""Mekong CLI - Hooks Middleware Pipeline."""

from __future__ import annotations
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class HookPhase(Enum):
    PRE_REQUEST = "pre_request"
    POST_REQUEST = "post_request"
    ON_ERROR = "on_error"


@dataclass
class HookContext:
    messages: list[dict[str, str]] = field(default_factory=list)
    model: str = ""
    provider: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    response_content: str = ""
    response_model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    error: Exception | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    start_time: float = 0.0


@dataclass
class HookResult:
    passed: bool = True
    modified_context: HookContext | None = None
    error_message: str = ""
    hook_name: str = ""
    duration_ms: float = 0.0


class Hook(ABC):
    def __init__(self, name: str, config: dict[str, Any] | None = None) -> None:
        self.name, self.config, self.enabled = name, config or {}, True

    @abstractmethod
    def execute(self, ctx: HookContext) -> HookResult: ...

    @property
    def phase(self) -> HookPhase:
        return HookPhase.PRE_REQUEST


class InputValidationHook(Hook):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__("input_validation", config)
        self.max_message_length = self.config.get("max_message_length", 100_000)
        self.max_messages = self.config.get("max_messages", 100)

    def execute(self, ctx: HookContext) -> HookResult:
        if not ctx.messages:
            return HookResult(passed=False, error_message="Empty messages", hook_name=self.name)
        if len(ctx.messages) > self.max_messages:
            return HookResult(passed=False, error_message=f"Too many messages: {len(ctx.messages)} > {self.max_messages}", hook_name=self.name)
        for i, msg in enumerate(ctx.messages):
            content = msg.get("content", "")
            if len(content) > self.max_message_length:
                return HookResult(passed=False, error_message=f"Message {i} too long: {len(content)} > {self.max_message_length}", hook_name=self.name)
        return HookResult(passed=True, hook_name=self.name)


class OutputValidationHook(Hook):
    phase = HookPhase.POST_REQUEST  # type: ignore[assignment]

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__("output_validation", config)
        self.min_length = self.config.get("min_length", 1)
        self.max_length = self.config.get("max_length", 500_000)

    def execute(self, ctx: HookContext) -> HookResult:
        content = ctx.response_content
        if len(content) < self.min_length:
            return HookResult(passed=False, error_message=f"Response too short: {len(content)} < {self.min_length}", hook_name=self.name)
        if len(content) > self.max_length:
            return HookResult(passed=False, error_message=f"Response too long: {len(content)} > {self.max_length}", hook_name=self.name)
        return HookResult(passed=True, hook_name=self.name)


class TokenCounterHook(Hook):
    phase = HookPhase.POST_REQUEST  # type: ignore[assignment]

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__("token_counter", config)
        self.max_input_tokens, self.total_tokens_used = self.config.get("max_input_tokens", 0), 0

    def execute(self, ctx: HookContext) -> HookResult:
        total = ctx.usage.get("total_tokens", 0)
        self.total_tokens_used += total
        ctx.metadata.update({"tokens_this_call": total, "tokens_cumulative": self.total_tokens_used})
        return HookResult(passed=True, hook_name=self.name, modified_context=ctx)


class LatencyMonitorHook(Hook):
    phase = HookPhase.POST_REQUEST  # type: ignore[assignment]

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__("latency_monitor", config)
        self.warn_threshold_ms = self.config.get("warn_threshold_ms", 10_000)

    def execute(self, ctx: HookContext) -> HookResult:
        if ctx.start_time > 0:
            latency_ms = (time.time() - ctx.start_time) * 1000
            ctx.metadata["latency_ms"] = round(latency_ms, 2)
            if latency_ms > self.warn_threshold_ms:
                logger.warning(f"[Hook] High latency: {latency_ms:.0f}ms > {self.warn_threshold_ms}ms (provider={ctx.provider}, model={ctx.model})")
        return HookResult(passed=True, hook_name=self.name, modified_context=ctx)


class ErrorLoggerHook(Hook):
    phase = HookPhase.ON_ERROR  # type: ignore[assignment]

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__("error_logger", config)

    def execute(self, ctx: HookContext) -> HookResult:
        if ctx.error:
            logger.error(f"[Hook] LLM error: provider={ctx.provider} model={ctx.model} error={ctx.error}")
        return HookResult(passed=True, hook_name=self.name)


class HookPipeline:
    def __init__(self) -> None:
        self._hooks: dict[HookPhase, list[Hook]] = {HookPhase.PRE_REQUEST: [], HookPhase.POST_REQUEST: [], HookPhase.ON_ERROR: []}

    def register(self, hook: Hook) -> None:
        self._hooks[hook.phase].append(hook)

    def run_phase(self, phase: HookPhase, ctx: HookContext) -> list[HookResult]:
        results = []
        for hook in [h for h in self._hooks[phase] if h.enabled]:
            start = time.time()
            try:
                result = hook.execute(ctx)
                result.duration_ms = (time.time() - start) * 1000
                ctx = result.modified_context or ctx
            except Exception as e:
                result = HookResult(passed=False, error_message=f"Hook {hook.name} crashed: {e}", hook_name=hook.name, duration_ms=(time.time() - start) * 1000)
            results.append(result)
            if phase == HookPhase.PRE_REQUEST and not result.passed:
                break
        return results

    def list_hooks(self) -> dict[str, list[str]]:
        return {phase.value: [h.name for h in hooks] for phase, hooks in self._hooks.items()}


def create_default_pipeline() -> HookPipeline:
    pipeline = HookPipeline()
    for h in (InputValidationHook(), OutputValidationHook(), TokenCounterHook(), LatencyMonitorHook(), ErrorLoggerHook()):
        pipeline.register(h)
    return pipeline


__all__ = ["ErrorLoggerHook", "Hook", "HookContext", "HookPhase", "HookPipeline", "HookResult", "InputValidationHook", "LatencyMonitorHook", "OutputValidationHook", "TokenCounterHook", "create_default_pipeline"]
