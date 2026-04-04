"""
Mekong AI OS — Unified Error Handling Framework
Every command wraps execution in this framework.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import traceback
import json
import hashlib
import datetime


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCode(Enum):
    # Infrastructure
    LLM_TIMEOUT = "E1001"
    LLM_RATE_LIMIT = "E1002"
    MODEL_UNAVAILABLE = "E1003"
    DISK_FULL = "E1004"
    # Business Logic
    INVALID_INPUT = "E2001"
    CONTRACT_VIOLATION = "E2002"
    ESCALATION_REQUIRED = "E2003"
    # External
    API_FAILURE = "E3001"
    PAYMENT_FAILED = "E3002"
    AUTH_EXPIRED = "E3003"


@dataclass
class MekongError:
    code: ErrorCode
    severity: ErrorSeverity
    message: str
    command: str
    context: dict
    timestamp: str = ""
    trace_id: str = ""

    def __post_init__(self) -> None:
        self.timestamp = datetime.datetime.utcnow().isoformat()
        raw = f"{self.code.value}{self.timestamp}{self.command}"
        self.trace_id = hashlib.sha256(raw.encode()).hexdigest()[:12]

    def to_audit_log(self) -> str:
        entry = json.dumps(
            {
                "trace_id": self.trace_id,
                "code": self.code.value,
                "severity": self.severity.value,
                "command": self.command,
                "message": self.message,
                "timestamp": self.timestamp,
            },
            separators=(",", ":"),
        )
        line_hash = hashlib.sha256(entry.encode()).hexdigest()
        return f"{line_hash}|{entry}"


MAX_RETRIES = {
    ErrorSeverity.LOW: 3,
    ErrorSeverity.MEDIUM: 1,
    ErrorSeverity.HIGH: 0,
    ErrorSeverity.CRITICAL: 0,
}


def classify_error(exc: Exception, command: str) -> MekongError:
    """Map common exceptions to MekongError with appropriate severity."""
    msg = str(exc)

    if "timeout" in msg.lower():
        return MekongError(
            code=ErrorCode.LLM_TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            message=msg,
            command=command,
            context={"exception_type": type(exc).__name__},
        )

    if "rate limit" in msg.lower() or "429" in msg:
        return MekongError(
            code=ErrorCode.LLM_RATE_LIMIT,
            severity=ErrorSeverity.LOW,
            message=msg,
            command=command,
            context={"exception_type": type(exc).__name__},
        )

    if "401" in msg or "403" in msg or "auth" in msg.lower():
        return MekongError(
            code=ErrorCode.AUTH_EXPIRED,
            severity=ErrorSeverity.HIGH,
            message=msg,
            command=command,
            context={"exception_type": type(exc).__name__},
        )

    return MekongError(
        code=ErrorCode.API_FAILURE,
        severity=ErrorSeverity.MEDIUM,
        message=msg,
        command=command,
        context={
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc()[-500:],
        },
    )


async def execute_with_retry(
    command_fn,
    command_name: str,
    **kwargs,
) -> dict:
    """Execute a command function with retry and error classification."""
    error: Optional[MekongError] = None

    for attempt in range(3):
        try:
            result = await command_fn(**kwargs)
            return {"ok": True, "result": result, "attempts": attempt + 1}
        except Exception as exc:
            error = classify_error(exc, command_name)
            error.context["attempt"] = attempt + 1

            max_retries = MAX_RETRIES.get(error.severity, 0)
            if attempt >= max_retries:
                break

    return {"ok": False, "error": error}
