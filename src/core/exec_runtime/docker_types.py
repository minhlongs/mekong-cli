# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Configuration, runner protocols, and process facade for Docker execution runtime."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .docker import DockerExecutionRuntime

_DEFAULT_TIMEOUT_S = 60.0
_DAEMON_PROBE_TIMEOUT_S = 5.0


class DockerRunner(Protocol):
    """Injected runner for docker CLI invocations.

    Mirrors ``subprocess.run`` semantics for the subset this runtime uses.
    Defaults to the real CLI runner; tests inject a fake to stay hermetic.
    """

    def run(
        self,
        args: list[str],
        *,
        timeout: float | None = None,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]: ...


class CliDockerRunner:
    """Default runner: real docker CLI via subprocess (never used in tests)."""

    def run(
        self,
        args: list[str],
        *,
        timeout: float | None = None,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # noqa: S603 — args built from validated argv, no shell
            args,
            timeout=timeout,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )


@dataclass(frozen=True)
class ContainerConfig:
    """Spec-to-container translation: what ``docker run`` receives."""

    image: str
    command: list[str]
    shell: bool
    workdir: str
    env: dict[str, str]
    network: str
    timeout_s: float

    def to_run_args(self) -> list[str]:
        """Build the full ``docker run`` argv for this config."""
        args = [
            "docker",
            "run",
            "--rm",
            "--workdir",
            self.workdir,
            "--network",
            self.network,
        ]
        for key, value in sorted(self.env.items()):
            args.extend(["--env", f"{key}={value}"])
        args.append(self.image)
        args.extend(self.command)
        return args


class DockerProcessControl:
    """Process facade for the container runtime."""

    def __init__(self, runtime: DockerExecutionRuntime) -> None:
        self._runtime = runtime

    def active_pids(self) -> list[int]:
        return []

    def terminate(self, pid: int) -> bool:
        return False

    def terminate_all(self) -> int:
        return 0


def docker_daemon_available() -> bool:
    """Cheap daemon probe for test gating (skip-if-no-daemon)."""
    if shutil.which("docker") is None:
        return False
    try:
        probe = subprocess.run(  # noqa: S603 — fixed argv, no shell
            ["docker", "info"],
            timeout=_DAEMON_PROBE_TIMEOUT_S,
            capture_output=True,
            text=True,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return probe.returncode == 0


__all__ = [
    "DockerRunner",
    "CliDockerRunner",
    "ContainerConfig",
    "DockerProcessControl",
    "docker_daemon_available",
    "_DEFAULT_TIMEOUT_S",
    "_DAEMON_PROBE_TIMEOUT_S",
]
