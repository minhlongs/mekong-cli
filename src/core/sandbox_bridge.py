# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Secure Agent Sandboxing Bridge for Mekong CLI × Antigravity.

STRICT INVARIANT: Provider-neutral and standard-library-only.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    image: str = "python:3.11-slim"
    timeout_seconds: int = 30
    memory_limit_mb: int = 512
    cpu_quota: float = 1.0
    workspace_dir: Optional[str] = None
    read_only_root: bool = True
    allow_network: bool = False
    env_vars: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SandboxResult:
    execution_id: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False
    isolation_backend: str = "container"
    container_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SandboxStatus:
    is_docker_available: bool
    active_sandboxes: int = 0
    total_executions: int = 0
    total_failures: int = 0
    default_image: str = "python:3.11-slim"
    recent_executions: List[SandboxResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_docker_available": self.is_docker_available, "active_sandboxes": self.active_sandboxes,
            "total_executions": self.total_executions, "total_failures": self.total_failures,
            "default_image": self.default_image, "recent_executions": [r.to_dict() for r in self.recent_executions[-10:]],
        }


class SandboxHarness:
    """Coordinates isolated command execution across container and fallback backends."""

    FORBIDDEN_ENV = {"AWS_SECRET_ACCESS_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GITHUB_TOKEN", "STRIPE_SECRET_KEY"}

    def __init__(self, default_config: Optional[SandboxConfig] = None) -> None:
        self.default_config = default_config or SandboxConfig()
        self._lock = threading.Lock()
        self._active_count = self._total_executions = self._total_failures = 0
        self._recent_results: List[SandboxResult] = []

    def check_container_runtime(self) -> Tuple[bool, str]:
        for runtime in ("docker", "podman"):
            if shutil.which(runtime):
                try:
                    if subprocess.run([runtime, "--version"], capture_output=True, text=True, timeout=3.0).returncode == 0:
                        return True, runtime
                except Exception:
                    pass
        return False, ""

    def _broadcast_gateway_event(self, event_type: str, data: dict[str, Any]) -> None:
        try:
            from src.core.gateway.streaming import StreamEvent, get_streaming_broker
            get_streaming_broker().publish(StreamEvent(mission_id="sandbox_harness", event_type=event_type, data=data))
        except Exception:
            pass

    def execute(self, command: str, config: Optional[SandboxConfig] = None, prefer_fallback: bool = False) -> SandboxResult:
        cfg = config or self.default_config
        execution_id = f"sandbox_{int(time.time() * 1000)}_{os.urandom(3).hex()}"
        start_t = time.time()
        with self._lock:
            self._active_count += 1
            self._total_executions += 1
        self._broadcast_gateway_event("sandbox_started", {"execution_id": execution_id, "command": command, "image": cfg.image})
        is_docker, runtime_name = self.check_container_runtime()
        res = self._execute_in_container(execution_id, command, cfg, runtime_name, start_t) if is_docker and not prefer_fallback else self._execute_in_fallback(execution_id, command, cfg, start_t)
        with self._lock:
            self._active_count = max(0, self._active_count - 1)
            if res.exit_code != 0:
                self._total_failures += 1
            self._recent_results = (self._recent_results + [res])[-50:]
        self._broadcast_gateway_event("sandbox_completed" if res.exit_code == 0 else "sandbox_failed", res.to_dict())
        return res

    def _execute_in_container(self, execution_id: str, command: str, cfg: SandboxConfig, runtime_name: str, start_t: float) -> SandboxResult:
        workspace = Path(cfg.workspace_dir or Path.cwd()).resolve()
        args = [runtime_name, "run", "--rm", f"--name={execution_id}", f"--memory={cfg.memory_limit_mb}m", f"--cpus={cfg.cpu_quota}", "-v", f"{workspace}:/workspace:rw", "-w", "/workspace"]
        if not cfg.allow_network:
            args.append("--network=none")
        if cfg.read_only_root:
            args.extend(["--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m"])
        for k, v in cfg.env_vars.items():
            args.extend(["-e", f"{k}={v}"])
        args.extend([cfg.image, "sh", "-c", command])
        try:
            proc = subprocess.run(args, capture_output=True, text=True, timeout=float(cfg.timeout_seconds))
            return SandboxResult(execution_id, command, proc.returncode, proc.stdout, proc.stderr, (time.time() - start_t) * 1000.0, False, "container", execution_id)
        except subprocess.TimeoutExpired as exc:
            subprocess.run([runtime_name, "kill", execution_id], capture_output=True)
            return SandboxResult(execution_id, command, 124, exc.stdout if isinstance(exc.stdout, str) else "", (exc.stderr or "") + f"\nSandbox execution timed out after {cfg.timeout_seconds}s", (time.time() - start_t) * 1000.0, True, "container", execution_id)
        except Exception as exc:
            return SandboxResult(execution_id, command, -1, "", f"Container execution error: {exc}", (time.time() - start_t) * 1000.0, False, "container")

    def _execute_in_fallback(self, execution_id: str, command: str, cfg: SandboxConfig, start_t: float) -> SandboxResult:
        workspace = Path(cfg.workspace_dir or tempfile.mkdtemp(prefix="mekong_sandbox_")).resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        clean_env = {**{k: v for k, v in os.environ.items() if k not in self.FORBIDDEN_ENV}, "PYTHONUNBUFFERED": "1", "MEKONG_SANDBOX": "1", **cfg.env_vars}
        try:
            proc = subprocess.run(["sh", "-c", command], cwd=str(workspace), env=clean_env, capture_output=True, text=True, timeout=float(cfg.timeout_seconds))
            return SandboxResult(execution_id, command, proc.returncode, proc.stdout, proc.stderr, (time.time() - start_t) * 1000.0, False, "process_fallback")
        except subprocess.TimeoutExpired as exc:
            return SandboxResult(execution_id, command, 124, exc.stdout if isinstance(exc.stdout, str) else "", (exc.stderr or "") + f"\nSandbox execution timed out after {cfg.timeout_seconds}s", (time.time() - start_t) * 1000.0, True, "process_fallback")
        except Exception as exc:
            return SandboxResult(execution_id, command, -1, "", f"Process fallback execution error: {exc}", (time.time() - start_t) * 1000.0, False, "process_fallback")

    def get_status(self) -> SandboxStatus:
        is_docker, _ = self.check_container_runtime()
        with self._lock:
            return SandboxStatus(is_docker, self._active_count, self._total_executions, self._total_failures, self.default_config.image, list(self._recent_results[-10:]))


_GLOBAL_SANDBOX_HARNESS: Optional[SandboxHarness] = None
_GLOBAL_SANDBOX_LOCK = threading.Lock()


def get_sandbox_harness() -> SandboxHarness:
    global _GLOBAL_SANDBOX_HARNESS
    with _GLOBAL_SANDBOX_LOCK:
        if _GLOBAL_SANDBOX_HARNESS is None:
            _GLOBAL_SANDBOX_HARNESS = SandboxHarness()
        return _GLOBAL_SANDBOX_HARNESS
