"""Shared tool framework for Mekong CLI v6.0.

Base tool abstractions, validators, type guards, and error wrappers
usable by any tool module across seed/tree/forest/land layers.

Usage:
    from src.tools.base import BaseTool, ToolResult, validate_output, retry_on_error
"""

from __future__ import annotations

import functools
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

_F = TypeVar("_F", bound=Callable[..., Any])


# ── Result / Error ───────────────────────────────────────────────────


@dataclass
class ToolError:
    """Structured error from a tool execution."""

    code: str
    message: str
    retryable: bool = False
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "detail": self.detail,
        }


@dataclass
class ToolResult:
    """Uniform return type for all tool executions."""

    success: bool
    data: Any = None
    error: ToolError | None = None
    duration_ms: float = 0.0

    @classmethod
    def ok(cls, data: Any = None, duration_ms: float = 0.0) -> ToolResult:
        return cls(success=True, data=data, duration_ms=duration_ms)

    @classmethod
    def fail(
        cls,
        code: str,
        message: str,
        retryable: bool = False,
        detail: dict[str, Any] | None = None,
        duration_ms: float = 0.0,
    ) -> ToolResult:
        return cls(
            success=False,
            error=ToolError(
                code=code,
                message=message,
                retryable=retryable,
                detail=detail or {},
            ),
            duration_ms=duration_ms,
        )


# ── Base Tool ─────────────────────────────────────────────────────────

class BaseTool:
    """Base class for all Mekong CLI tools.

    Subclasses override `run()` to implement tool logic.
    The wrapper handles timing, error normalization, and retry policy.
    """

    name: str = "base"
    description: str = "Base tool"
    retries: int = 0
    retry_delay: float = 0.5

    def run(self, **kwargs: Any) -> ToolResult:
        """Override this: execute the tool and return a ToolResult."""
        raise NotImplementedError("Tools must implement run()")

    def __call__(self, **kwargs: Any) -> ToolResult:
        t0 = time.perf_counter()
        attempt = 0
        last_err: ToolError | None = None

        while True:
            result = self.run(**kwargs)
            result.duration_ms = (time.perf_counter() - t0) * 1000
            if result.success or attempt >= self.retries:
                return result
            if not result.error or not result.error.retryable:
                return result
            last_err = result.error
            attempt += 1
            logger.warning(
                "tool=%s retry=%d code=%s",
                self.name,
                attempt,
                last_err.code,
            )
            time.sleep(self.retry_delay)


# ── Validators ────────────────────────────────────────────────────────

def validate_output(result: ToolResult) -> None:
    """Wallet-side guard: ensure a ToolResult is well-formed.

    Raises ValueError if the result is malformed. In production,
    call this at the boundary where a tool result becomes a
    downstream input so bad data fails fast and loudly.
    """
    if not isinstance(result, ToolResult):
        raise TypeError(
            f"expected ToolResult, got {type(result).__name__}"
        )
    if not result.success and result.error is None:
        # A failure without an error object means the tool swallowed
        # its real error — surface this so devs fix the tool, not
        # the caller
        raise ValueError("ToolResult.fail must include a ToolError")


def validate_types(value: Any, expected: type | dict[str, type], path: str = "value") -> list[str]:
    """Recursively check that *value* matches *expected* shape.

    Returns a (possibly empty) list of human-readable mismatch reports.
    Caller decides whether to raise or just log.

    Args:
        value:   The value to check.
        expected: A type (for scalars) or dict mapping field names to
                  types (for objects / dicts).
        path:    Dotted path into the value for error messages.
    """
    issues: list[str] = []
    if isinstance(expected, dict):
        if not isinstance(value, dict):
            issues.append(f"{path}: expected object, got {type(value).__name__}")
            return issues
        for key, vtype in expected.items():
            if key not in value:
                issues.append(f"{path}.{key}: missing required field")
            else:
                issues.extend(validate_types(value[key], vtype, f"{path}.{key}"))
    else:
        if not isinstance(value, expected):
            issues.append(
                f"{path}: expected {expected.__name__}, got {type(value).__name__}"
            )
    return issues


# ── Retry Decorator ───────────────────────────────────────────────────

def retry_on_error(
    max_attempts: int = 3,
    delay: float = 0.5,
    backoff: float = 2.0,
    retryable_codes: set[str] | None = None,
) -> Callable[[_F], _F]:
    """Function decorator that retries on failure ToolResults.

    Inspects the return value; if it is a ToolResult with
    success=False and a retryable error, it sleeps *delay* seconds
    (multiplied by *backoff* ** attempt) and tries again.

    Args:
        max_attempts: Total attempts (first call + retries).
        delay:        Initial wait in seconds.
        backoff:      Multiplier applied per retry (exponential backoff).
        retryable_codes: Optional set of error codes that are safe to
                         retry. Defaults to None which retries everything
                         marked retryable in the ToolError.
    """
    def decorator(func: _F) -> _F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            wait = delay
            last: ToolResult | None = None
            for attempt in range(1, max_attempts + 1):
                result = func(*args, **kwargs)
                if not isinstance(result, ToolResult):
                    return result
                if result.success:
                    return result
                if result.error is None or not result.error.retryable:
                    return result
                if retryable_codes is not None and result.error.code not in retryable_codes:
                    return result
                last = result
                if attempt < max_attempts:
                    logger.warning(
                        "retry attempt=%d/%d tool=%s code=%s",
                        attempt,
                        max_attempts,
                        getattr(func, "__name__", func),
                        result.error.code,
                    )
                    time.sleep(wait)
                    wait *= backoff
            return last  # type: ignore[return-value]
        return wrapper  # type: ignore[return-value]
    return decorator
