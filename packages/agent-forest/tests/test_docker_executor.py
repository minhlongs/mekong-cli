"""Tests for docker_executor — all Docker SDK calls are mocked.

No Docker daemon required. Patches `agent_forest.worker.docker_executor.docker`
(the module-level attribute) so tests pass even without the `docker` extra installed.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ImageNotFound = type("ImageNotFound", (Exception,), {})
_DockerException = type("DockerException", (Exception,), {})
_APIError = type("APIError", (Exception,), {})


def _make_mock_docker(exit_code: int = 0, log_bytes: bytes = b"") -> MagicMock:
    """Return a mock `docker` module with a pre-configured containers.run path."""
    mock_docker = MagicMock()

    mock_container = MagicMock()
    mock_container.wait.return_value = {"StatusCode": exit_code}
    mock_container.logs.return_value = log_bytes
    mock_container.kill.return_value = None
    mock_container.remove.return_value = None

    mock_client = MagicMock()
    mock_client.containers.run.return_value = mock_container
    mock_docker.from_env.return_value = mock_client

    # Wire error classes so isinstance checks / except clauses resolve correctly.
    mock_docker.errors.DockerException = _DockerException
    mock_docker.errors.APIError = _APIError
    mock_docker.errors.ImageNotFound = _ImageNotFound

    return mock_docker


def _make_settings(docker_image: str = "agent-core:latest", timeout: int = 30):
    """Return a minimal ForestSettings with docker fields."""
    from agent_forest.config import ForestSettings

    return ForestSettings(
        jwt_secret_key="test-key",
        testing=True,
        worker_executor="docker",
        docker_image=docker_image,
        docker_timeout_seconds=timeout,
    )


# ---------------------------------------------------------------------------
# Test 1: success — exit 0, JSON log line → JobOutcome(completed, result=...)
# ---------------------------------------------------------------------------

def test_successful_run_returns_completed():
    log_payload = json.dumps({"status": "completed", "result": "hello"}).encode()
    mock_docker = _make_mock_docker(exit_code=0, log_bytes=log_payload)

    with patch("agent_forest.worker.docker_executor.docker", mock_docker):
        from agent_forest.worker.docker_executor import execute_in_container

        outcome = execute_in_container("hello world", "/tmp/sandbox", settings=_make_settings())

    assert outcome.status == "completed"
    assert outcome.result == "hello"


# ---------------------------------------------------------------------------
# Test 2: non-zero exit → JobOutcome(failed, error contains stderr)
# ---------------------------------------------------------------------------

def test_container_nonzero_exit_returns_failed():
    stderr = b"Traceback (most recent call last):\n  File ...\nValueError: bad input"
    mock_docker = _make_mock_docker(exit_code=1, log_bytes=stderr)

    with patch("agent_forest.worker.docker_executor.docker", mock_docker):
        from agent_forest.worker.docker_executor import execute_in_container

        outcome = execute_in_container("bad prompt", "/tmp/sandbox", settings=_make_settings())

    assert outcome.status == "failed"
    assert outcome.error is not None and len(outcome.error) > 0


# ---------------------------------------------------------------------------
# Test 3: container.wait raises TimeoutError → container.kill() called, failed
# ---------------------------------------------------------------------------

def test_container_timeout_kills_container():
    mock_docker = _make_mock_docker()
    container = mock_docker.from_env.return_value.containers.run.return_value
    container.wait.side_effect = TimeoutError("timed out waiting for container")

    with patch("agent_forest.worker.docker_executor.docker", mock_docker):
        from agent_forest.worker.docker_executor import execute_in_container

        outcome = execute_in_container("x", "/tmp/sandbox", settings=_make_settings(timeout=1))

    assert outcome.status == "failed"
    assert "timeout" in (outcome.error or "").lower()
    container.kill.assert_called_once()


# ---------------------------------------------------------------------------
# Test 4: docker.from_env raises DockerException → failed, no raise
# ---------------------------------------------------------------------------

def test_docker_unavailable_returns_failed():
    mock_docker = MagicMock()
    mock_docker.errors.DockerException = _DockerException
    mock_docker.errors.ImageNotFound = _ImageNotFound
    mock_docker.from_env.side_effect = _DockerException("Cannot connect to Docker daemon")

    with patch("agent_forest.worker.docker_executor.docker", mock_docker):
        from agent_forest.worker.docker_executor import execute_in_container

        outcome = execute_in_container("x", "/tmp/sandbox", settings=_make_settings())

    assert outcome.status == "failed"
    assert "docker" in (outcome.error or "").lower()


# ---------------------------------------------------------------------------
# Test 5: env passthrough — only whitelisted vars reach container
# ---------------------------------------------------------------------------

def test_env_passthrough_to_container(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.example.com")
    monkeypatch.setenv("LLM_API_KEY", "sk-test-key")
    monkeypatch.setenv("LLM_MODEL", "gpt-4")
    monkeypatch.setenv("SECRET_PASSWORD", "should-not-appear")

    log_payload = json.dumps({"status": "completed", "result": "ok"}).encode()
    mock_docker = _make_mock_docker(exit_code=0, log_bytes=log_payload)

    with patch("agent_forest.worker.docker_executor.docker", mock_docker):
        from agent_forest.worker.docker_executor import execute_in_container

        execute_in_container("test", "/tmp/sandbox", settings=_make_settings())

    run_call = mock_docker.from_env.return_value.containers.run
    # environment kwarg may be positional or keyword — inspect call_args.
    call_args = run_call.call_args
    env_passed = call_args.kwargs.get("environment") or {}
    if not env_passed and call_args.args:
        # Fallback: shouldn't happen given our explicit kwargs, but be safe.
        env_passed = {}

    assert env_passed.get("AGENT_CORE_OUTPUTS") == "/outputs"
    assert "LLM_BASE_URL" in env_passed
    assert "LLM_API_KEY" in env_passed
    assert "LLM_MODEL" in env_passed
    assert "SECRET_PASSWORD" not in env_passed
    assert "PATH" not in env_passed


# ---------------------------------------------------------------------------
# Test 6: docker module absent at import time → no ImportError on module load
# ---------------------------------------------------------------------------

def test_import_stable_without_docker_module():
    """Module must import cleanly even when docker package is absent.

    The executor sets `docker = None` on ImportError. Calling
    execute_in_container when docker is None returns a failed JobOutcome.
    """
    import importlib
    import sys

    # Save and remove cached modules.
    original_docker = sys.modules.pop("docker", None)
    sys.modules.pop("agent_forest.worker.docker_executor", None)

    # Block the docker import by inserting None sentinel.
    sys.modules["docker"] = None  # type: ignore[assignment]

    try:
        mod = importlib.import_module("agent_forest.worker.docker_executor")
        assert mod.docker is None  # type: ignore[attr-defined]

        outcome = mod.execute_in_container("test", "/tmp/x")
        assert outcome.status == "failed"
        assert "docker" in (outcome.error or "").lower()
    finally:
        sys.modules.pop("docker", None)
        if original_docker is not None:
            sys.modules["docker"] = original_docker
        sys.modules.pop("agent_forest.worker.docker_executor", None)
