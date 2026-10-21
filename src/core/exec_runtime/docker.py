# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Docker execution runtime: container-backed adapter via the docker CLI."""

from __future__ import annotations

import logging
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from src.core.command_sanitizer import CommandSanitizer
from src.core.exec_runtime.local import LocalFilesystem
from src.core.exec_runtime.types import ExecResult, NetworkPolicy, SandboxSpec

from .docker_types import (
    _DAEMON_PROBE_TIMEOUT_S,
    _DEFAULT_TIMEOUT_S,
    CliDockerRunner,
    ContainerConfig,
    DockerProcessControl,
    DockerRunner,
    docker_daemon_available,
)

logger = logging.getLogger(__name__)


class DockerExecutionRuntime:
    """Concrete ExecutionRuntime running commands inside one-shot containers."""

    def __init__(
        self,
        root_dir: str | Path,
        *,
        image: str,
        runner: DockerRunner | None = None,
        env_overrides: dict[str, str] | None = None,
        allow_outbound: bool = False,
        default_timeout_s: float = _DEFAULT_TIMEOUT_S,
    ) -> None:
        if not image:
            raise ValueError("image must be a non-empty string")
        self._root = Path(root_dir).resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        self._spec = SandboxSpec(root_dir=self._root)
        self._fs = LocalFilesystem(spec=self._spec)
        self._sanitizer = CommandSanitizer(strict_mode=True)
        self._network_policy = NetworkPolicy(
            allow_outbound=allow_outbound,
            description="bridge network (outbound allowed)" if allow_outbound else "deny-all outbound (--network none)",
        )
        self._image = image
        self._runner: DockerRunner = runner or CliDockerRunner()
        self._env_overrides = dict(env_overrides or {})
        self._default_timeout_s = float(default_timeout_s)
        self._runs = 0
        self._destroyed = False
        self._lock = threading.Lock()

    def execute(self, command: list[str] | str, *, timeout_s: float | None = None) -> ExecResult:
        """Run one command in a container. Never raises for failure."""
        if self._destroyed:
            raise RuntimeError("DockerExecutionRuntime was destroyed")
        effective_timeout = float(timeout_s) if timeout_s is not None else self._default_timeout_s
        if effective_timeout <= 0:
            raise ValueError(f"timeout_s must be positive, got {timeout_s}")
        if isinstance(command, str):
            check = self._sanitizer.sanitize(command)
            if not check.is_safe:
                return ExecResult(
                    ok=False, exit_code=None, stdout="", stderr="",
                    error=f"blocked by sanitizer: {check.blocked_reason}",
                )
            shell_command, shell = str(check.sanitized_command), True
        else:
            if not command:
                raise ValueError("argv command must be a non-empty list of strings")
            shell_command, shell = "", False
        config = self._build_config(command, shell, shell_command, effective_timeout)
        start = time.monotonic()
        try:
            completed = self._runner.run(
                config.to_run_args(), timeout=effective_timeout,
                cwd=str(self._root), env=self.environment(),
            )
        except subprocess.TimeoutExpired:
            return ExecResult(
                ok=False, exit_code=None, stdout="", stderr="",
                duration_ms=(time.monotonic() - start) * 1000,
                timed_out=True, error=f"timed out after {effective_timeout:.1f}s",
            )
        except OSError as exc:
            return ExecResult(
                ok=False, exit_code=None, stdout="", stderr="",
                duration_ms=(time.monotonic() - start) * 1000, error=f"launch failed: {exc}",
            )
        with self._lock:
            self._runs += 1
        return ExecResult(
            ok=completed.returncode == 0, exit_code=completed.returncode,
            stdout=completed.stdout or "", stderr=completed.stderr or "",
            duration_ms=(time.monotonic() - start) * 1000,
        )

    def filesystem(self) -> LocalFilesystem:
        return self._fs

    def process(self) -> DockerProcessControl:
        return DockerProcessControl(self)

    def network_policy(self) -> NetworkPolicy:
        return self._network_policy

    def environment(self) -> dict[str, str]:
        return dict(self._env_overrides)

    def preview(self, request: dict[str, Any]) -> dict[str, Any]:
        cmd = request.get("command", "")
        chk = self._sanitizer.sanitize(str(cmd)) if isinstance(cmd, str) else None
        return {
            "command": cmd, "shell": isinstance(cmd, str), "image": self._image,
            "workdir": str(self._root),
            "timeout_s": float(request.get("timeout_s", self._default_timeout_s)),
            "network": self._network_flag(), "network_policy": self._network_policy.description,
            "would_execute": chk.is_safe if chk else True,
            "blocked_reason": "" if (chk and chk.is_safe) else (chk.blocked_reason if chk else ""),
        }

    def health(self) -> dict[str, Any]:
        daemon = False
        if self._destroyed:
            status = "destroyed"
        elif shutil.which("docker") is None:
            status = "degraded"
        else:
            try:
                probe = self._runner.run(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=_DAEMON_PROBE_TIMEOUT_S)
                daemon = probe.returncode == 0
            except (subprocess.TimeoutExpired, OSError):
                daemon = False
            status = "ok" if daemon else "degraded"
        return {
            "status": status, "runtime": "docker", "daemon_available": daemon,
            "image": self._image, "root_dir": str(self._root), "runs": self._runs,
            "network_policy": self._network_policy.description,
        }

    def destroy(self) -> dict[str, Any]:
        self._destroyed = True
        return {"status": "destroyed", "terminated_processes": 0}

    @property
    def destroyed(self) -> bool:
        return self._destroyed

    def _network_flag(self) -> str:
        return "bridge" if self._network_policy.allow_outbound else "none"

    def _build_config(self, command: list[str] | str, shell: bool, shell_cmd: str, timeout_s: float) -> ContainerConfig:
        mapped = ["/bin/sh", "-c", shell_cmd] if shell else [str(p) for p in command]
        return ContainerConfig(
            image=self._image, command=mapped, shell=shell, workdir=str(self._root),
            env=self.environment(), network=self._network_flag(), timeout_s=timeout_s,
        )


__all__ = [
    "CliDockerRunner",
    "ContainerConfig",
    "DockerExecutionRuntime",
    "DockerProcessControl",
    "DockerRunner",
    "docker_daemon_available",
]
