# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Dataclasses, protocols, and process facades for Cloudflare execution runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from .cloudflare import CloudflareExecutionRuntime

_DEFAULT_TIMEOUT_S = 60.0


class CloudflareTransport(Protocol):
    """Injected transport for remote execution calls.

    Implementations own the wire protocol (HTTP, RPC, in-memory fake).
    ``dispatch`` must return a JSON-shaped dict and must raise
    ``TimeoutError`` when the remote side exceeds its deadline.
    """

    def dispatch(self, payload: dict[str, Any]) -> dict[str, Any]: ...


@dataclass(frozen=True)
class WorkerConfig:
    """Spec-to-worker translation: what the remote worker receives."""

    account_id: str
    script_name: str
    command: list[str]
    shell: bool
    cwd: str
    env: dict[str, str]
    timeout_s: float

    def to_payload(self) -> dict[str, Any]:
        return {
            "account_id": self.account_id,
            "script_name": self.script_name,
            "command": list(self.command),
            "shell": self.shell,
            "cwd": self.cwd,
            "env": dict(self.env),
            "timeout_s": self.timeout_s,
        }


class CloudflareProcessControl:
    """Process facade for the remote runtime.

    The worker is stateless and each dispatch is synchronous, so no child
    processes are tracked locally; terminate is a no-op that reports False.
    """

    def __init__(self, runtime: CloudflareExecutionRuntime) -> None:
        self._runtime = runtime

    def active_pids(self) -> list[int]:
        return []

    def terminate(self, pid: int) -> bool:
        return False

    def terminate_all(self) -> int:
        return 0


__all__ = [
    "CloudflareTransport",
    "WorkerConfig",
    "CloudflareProcessControl",
    "_DEFAULT_TIMEOUT_S",
]
