"""Docker-in-Docker executor (optional dep). execute_in_container -> JobOutcome."""

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING

from agent_forest.worker.runner import JobOutcome

if TYPE_CHECKING:
    from agent_forest.config import ForestSettings

log = logging.getLogger("agent_forest.worker.docker_executor")

# Module-level so tests can patch this attribute. No daemon contact at import.
try:
    import docker  # type: ignore[import]
except ImportError:
    docker = None  # type: ignore[assignment]

_ENV_WHITELIST = ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")


def _build_env(_sandbox: str) -> dict[str, str]:
    """Whitelisted env for container; no blanket os.environ pass-through."""
    env = {"AGENT_CORE_OUTPUTS": "/outputs"}
    env.update({k: v for k in _ENV_WHITELIST if (v := os.getenv(k)) is not None})
    return env


def _parse_outcome(raw_logs: bytes, exit_code: int) -> JobOutcome:
    text = raw_logs.decode("utf-8", errors="replace").strip() if raw_logs else ""
    last_line = next((ln.strip() for ln in reversed(text.splitlines()) if ln.strip()), "")
    if exit_code == 0:
        try:
            parsed = json.loads(last_line)
            if isinstance(parsed, dict):
                return JobOutcome(
                    status=parsed.get("status", "completed"),
                    result=parsed.get("result"),
                    error=parsed.get("error"),
                )
        except (json.JSONDecodeError, ValueError):
            pass
        return JobOutcome(status="completed", result=text or None)
    return JobOutcome(status="failed", error=(text or f"exit code {exit_code}")[:4000])


def execute_in_container(
    prompt: str,
    sandbox_str: str,
    *,
    settings: ForestSettings | None = None,
    max_rounds: int = 1,
) -> JobOutcome:
    """Run prompt in isolated container; return JobOutcome. Never raises."""
    if docker is None:
        return JobOutcome(
            status="failed",
            error="docker extra not installed — run `pip install agent-forest[docker]`",
        )

    if settings is None:
        from agent_forest.config import ForestSettings as _S
        settings = _S.from_env()

    DockerException = getattr(docker.errors, "DockerException", Exception)
    ImageNotFound = getattr(docker.errors, "ImageNotFound", Exception)

    try:
        client = docker.from_env()
    except DockerException as exc:
        return JobOutcome(status="failed", error=f"docker daemon unavailable: {exc}")

    container = None
    try:
        cmd = ["python", "-m", "agent_core.cli", "orchestrate", prompt]
        if max_rounds >= 2:
            cmd += ["--rounds", str(max_rounds)]
        container = client.containers.run(
            settings.docker_image,
            command=cmd,
            volumes={sandbox_str: {"bind": "/outputs", "mode": "rw"}},
            environment=_build_env(sandbox_str),
            mem_limit="2g",
            nano_cpus=2_000_000_000,
            user="1000:1000",
            network_mode="bridge",
            auto_remove=False,
            detach=True,
            stdin_open=False,
        )
        result = container.wait(timeout=settings.docker_timeout_seconds)
        exit_code: int = result.get("StatusCode", 1) if isinstance(result, dict) else 1
        raw_logs: bytes = container.logs(stdout=True, stderr=True)
        return _parse_outcome(raw_logs, exit_code)

    except ImageNotFound as exc:
        return JobOutcome(status="failed", error=f"docker image not found: {exc}")

    except (TimeoutError, Exception) as exc:  # noqa: BLE001
        exc_name = type(exc).__name__
        is_timeout = "timeout" in exc_name.lower() or "timeout" in str(exc).lower()
        msg = (
            f"container timeout after {settings.docker_timeout_seconds}s"
            if is_timeout
            else f"{exc_name}: {exc}"
        )
        if container is not None:
            try:
                container.kill()
            except Exception:  # noqa: BLE001
                pass
        return JobOutcome(status="failed", error=msg[:4000])

    finally:
        if container is not None:
            try:
                container.remove(force=True)
            except Exception:  # noqa: BLE001
                pass
