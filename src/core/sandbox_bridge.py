# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Secure Agent Sandboxing Bridge for Mekong CLI × Antigravity.

Coordinates execution of untrusted commands, tools, and code inside isolated
Docker/container environments with memory quotas, CPU limits, timeouts, and
workspace mounting. Provides a secure fallback using restricted subprocesses
with environment scrubbing when a container daemon is not present.

STRICT INVARIANT: Provider-neutral and standard-library-only. Zero external vendor
SDKs or heavy third-party packages (complies with tests/test_core_boundary.py).
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    """Security and resource constraint parameters for sandboxed execution."""

    image: str = "python:3.11-slim"
    timeout_seconds: int = 30
    memory_limit_mb: int = 512
    cpu_quota: float = 1.0
    workspace_dir: Optional[str] = None
    read_only_root: bool = True
    allow_network: bool = False
    env_vars: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)


@dataclass
class SandboxResult:
    """Outcome and telemetry of a sandboxed execution."""

    execution_id: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False
    isolation_backend: str = "container"  # "container" or "process_fallback"
    container_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "execution_id": self.execution_id,
            "command": self.command,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
            "timed_out": self.timed_out,
            "isolation_backend": self.isolation_backend,
            "container_id": self.container_id,
            "timestamp": self.timestamp,
        }


@dataclass
class SandboxStatus:
    """Runtime status of the sandboxing subsystem."""

    is_docker_available: bool
    active_sandboxes: int = 0
    total_executions: int = 0
    total_failures: int = 0
    default_image: str = "python:3.11-slim"
    recent_executions: List[SandboxResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert status to dictionary."""
        return {
            "is_docker_available": self.is_docker_available,
            "active_sandboxes": self.active_sandboxes,
            "total_executions": self.total_executions,
            "total_failures": self.total_failures,
            "default_image": self.default_image,
            "recent_executions": [r.to_dict() for r in self.recent_executions[-10:]],
        }


class SandboxHarness:
    """Coordinates isolated command execution across container and fallback backends."""

    def __init__(self, default_config: Optional[SandboxConfig] = None) -> None:
        self.default_config = default_config or SandboxConfig()
        self._lock = threading.Lock()
        self._active_count = 0
        self._total_executions = 0
        self._total_failures = 0
        self._recent_results: List[SandboxResult] = []

    def check_container_runtime(self) -> Tuple[bool, str]:
        """Probe whether Docker or Podman is available in the local PATH."""
        for runtime in ("docker", "podman"):
            cmd_path = shutil.which(runtime)
            if cmd_path:
                try:
                    res = subprocess.run(
                        [runtime, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=3.0,
                    )
                    if res.returncode == 0:
                        return True, runtime
                except Exception:
                    pass
        return False, ""

    def _broadcast_gateway_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Stream sandbox lifecycle events over Gateway broker if available."""
        try:
            from src.core.gateway.streaming import StreamEvent, get_streaming_broker
            broker = get_streaming_broker()
            broker.publish(StreamEvent(
                mission_id="sandbox_harness",
                event_type=event_type,
                data=data,
            ))
        except Exception:
            pass

    def execute(
        self,
        command: str,
        config: Optional[SandboxConfig] = None,
        prefer_fallback: bool = False,
    ) -> SandboxResult:
        """Execute command in container sandbox (or secure subprocess fallback)."""
        cfg = config or self.default_config
        execution_id = f"sandbox_{int(time.time() * 1000)}_{os.urandom(3).hex()}"
        start_t = time.time()

        with self._lock:
            self._active_count += 1
            self._total_executions += 1

        self._broadcast_gateway_event("sandbox_started", {
            "execution_id": execution_id,
            "command": command,
            "image": cfg.image,
        })

        is_docker, runtime_name = self.check_container_runtime()
        use_container = is_docker and not prefer_fallback

        if use_container:
            res = self._execute_in_container(execution_id, command, cfg, runtime_name, start_t)
        else:
            res = self._execute_in_fallback(execution_id, command, cfg, start_t)

        with self._lock:
            self._active_count = max(0, self._active_count - 1)
            if res.exit_code != 0:
                self._total_failures += 1
            self._recent_results.append(res)
            if len(self._recent_results) > 50:
                self._recent_results = self._recent_results[-50:]

        evt_name = "sandbox_completed" if res.exit_code == 0 else "sandbox_failed"
        self._broadcast_gateway_event(evt_name, res.to_dict())

        return res

    def _execute_in_container(
        self,
        execution_id: str,
        command: str,
        cfg: SandboxConfig,
        runtime_name: str,
        start_t: float,
    ) -> SandboxResult:
        """Run command in a lightweight, ephemeral container sandbox."""
        workspace = Path(cfg.workspace_dir or Path.cwd()).resolve()

        # Build container command args
        docker_args = [
            runtime_name,
            "run",
            "--rm",
            f"--name={execution_id}",
            f"--memory={cfg.memory_limit_mb}m",
            f"--cpus={cfg.cpu_quota}",
            f"-v", f"{workspace}:/workspace:rw",
            "-w", "/workspace",
        ]

        if not cfg.allow_network:
            docker_args.append("--network=none")

        if cfg.read_only_root:
            docker_args.extend(["--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m"])

        for k, v in cfg.env_vars.items():
            docker_args.extend(["-e", f"{k}={v}"])

        docker_args.extend([cfg.image, "sh", "-c", command])

        timed_out = False
        try:
            proc = subprocess.run(
                docker_args,
                capture_output=True,
                text=True,
                timeout=float(cfg.timeout_seconds),
            )
            duration_ms = (time.time() - start_t) * 1000.0
            return SandboxResult(
                execution_id=execution_id,
                command=command,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_ms=duration_ms,
                timed_out=False,
                isolation_backend="container",
                container_id=execution_id,
            )
        except subprocess.TimeoutExpired as exc:
            # Kill running container on timeout
            subprocess.run([runtime_name, "kill", execution_id], capture_output=True)
            duration_ms = (time.time() - start_t) * 1000.0
            return SandboxResult(
                execution_id=execution_id,
                command=command,
                exit_code=124,
                stdout=exc.stdout or "" if isinstance(exc.stdout, str) else "",
                stderr=(exc.stderr or "") + f"\nSandbox execution timed out after {cfg.timeout_seconds}s",
                duration_ms=duration_ms,
                timed_out=True,
                isolation_backend="container",
                container_id=execution_id,
            )
        except Exception as exc:
            duration_ms = (time.time() - start_t) * 1000.0
            return SandboxResult(
                execution_id=execution_id,
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Container execution error: {exc}",
                duration_ms=duration_ms,
                timed_out=False,
                isolation_backend="container",
                container_id=None,
            )

    def _execute_in_fallback(
        self,
        execution_id: str,
        command: str,
        cfg: SandboxConfig,
        start_t: float,
    ) -> SandboxResult:
        """Run command in a sanitized restricted subprocess fallback."""
        workspace = Path(cfg.workspace_dir or tempfile.mkdtemp(prefix="mekong_sandbox_")).resolve()
        workspace.mkdir(parents=True, exist_ok=True)

        # Scrub sensitive environment variables
        forbidden_env_keys = {
            "AWS_SECRET_ACCESS_KEY",
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "GITHUB_TOKEN",
            "STRIPE_SECRET_KEY",
        }
        clean_env = {
            k: v for k, v in os.environ.items()
            if k not in forbidden_env_keys
        }
        clean_env["PYTHONUNBUFFERED"] = "1"
        clean_env["MEKONG_SANDBOX"] = "1"
        clean_env.update(cfg.env_vars)

        try:
            proc = subprocess.run(
                ["sh", "-c", command],
                cwd=str(workspace),
                env=clean_env,
                capture_output=True,
                text=True,
                timeout=float(cfg.timeout_seconds),
            )
            duration_ms = (time.time() - start_t) * 1000.0
            return SandboxResult(
                execution_id=execution_id,
                command=command,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration_ms=duration_ms,
                timed_out=False,
                isolation_backend="process_fallback",
            )
        except subprocess.TimeoutExpired as exc:
            duration_ms = (time.time() - start_t) * 1000.0
            return SandboxResult(
                execution_id=execution_id,
                command=command,
                exit_code=124,
                stdout=exc.stdout or "" if isinstance(exc.stdout, str) else "",
                stderr=(exc.stderr or "") + f"\nSandbox execution timed out after {cfg.timeout_seconds}s",
                duration_ms=duration_ms,
                timed_out=True,
                isolation_backend="process_fallback",
            )
        except Exception as exc:
            duration_ms = (time.time() - start_t) * 1000.0
            return SandboxResult(
                execution_id=execution_id,
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Process fallback execution error: {exc}",
                duration_ms=duration_ms,
                timed_out=False,
                isolation_backend="process_fallback",
            )

    def get_status(self) -> SandboxStatus:
        """Return runtime status and metrics."""
        is_docker, _ = self.check_container_runtime()
        with self._lock:
            return SandboxStatus(
                is_docker_available=is_docker,
                active_sandboxes=self._active_count,
                total_executions=self._total_executions,
                total_failures=self._total_failures,
                default_image=self.default_config.image,
                recent_executions=list(self._recent_results[-10:]),
            )


# Global singleton instance
_GLOBAL_SANDBOX_HARNESS: Optional[SandboxHarness] = None
_GLOBAL_SANDBOX_LOCK = threading.Lock()


def get_sandbox_harness() -> SandboxHarness:
    """Get or initialize singleton SandboxHarness."""
    global _GLOBAL_SANDBOX_HARNESS
    with _GLOBAL_SANDBOX_LOCK:
        if _GLOBAL_SANDBOX_HARNESS is None:
            _GLOBAL_SANDBOX_HARNESS = SandboxHarness()
        return _GLOBAL_SANDBOX_HARNESS
