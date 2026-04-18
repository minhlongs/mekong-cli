"""Minimal HTTP client for agent-forest gateway ops endpoints.

Separated from LLMClient so it has zero mekongd coupling — forest-status may
target a different base URL than the LLM backend, and reading public metrics
does not need auth or retries.
"""

from __future__ import annotations

import httpx

_METRIC_NAMES = (
    "agent_forest_queue_depth",
    "agent_forest_up",
    "agent_forest_workers_alive",
    "agent_forest_worker_last_seen_timestamp",
)


def parse_prom_metrics(text: str, names: tuple[str, ...] = _METRIC_NAMES) -> dict[str, float]:
    """Parse Prometheus text exposition; return {metric_name: value} for requested names.

    Ignores comment/help lines. Skips unparseable values silently — operator
    output should never crash on malformed upstream data.
    """
    out: dict[str, float] = {}
    wanted = set(names)
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        name, raw = parts
        # Strip optional "{labels}" suffix from metric name.
        if "{" in name:
            name = name.split("{", 1)[0]
        if name not in wanted:
            continue
        try:
            out[name] = float(raw.split()[0])
        except ValueError:
            continue
    return out


def _status_json_to_metrics(body: dict) -> dict[str, float]:
    """Map agent-forest /status JSON keys into the Prom-metric shape the
    formatter already knows how to render."""
    return {
        "agent_forest_queue_depth": float(body.get("queue_depth", 0)),
        "agent_forest_up": 1.0 if body.get("up") else 0.0,
        "agent_forest_workers_alive": float(body.get("workers_alive", 0)),
        "agent_forest_worker_last_seen_timestamp": float(
            body.get("worker_last_seen_ts", 0)
        ),
    }


def fetch_forest_status(base_url: str, *, timeout: float = 5.0) -> dict:
    """Hit /healthz + /status (JSON, preferred) + /metrics (fallback) and return
    a compact summary.

    Never raises: connection/HTTP errors are reported in the returned dict so the
    CLI can print a clean error row rather than a traceback. Prefers the JSON
    endpoint added in PR #128; falls back to Prom-text parsing for older gateway
    versions that only expose /metrics.
    """
    base = base_url.rstrip("/")
    result: dict = {"base_url": base, "healthz": None, "metrics": {}, "error": None}
    try:
        with httpx.Client(timeout=timeout) as client:
            health = client.get(f"{base}/healthz")
            result["healthz"] = {"status_code": health.status_code, "body": health.json()}
            status = client.get(f"{base}/status")
            if status.status_code == 200:
                try:
                    result["metrics"] = _status_json_to_metrics(status.json())
                    return result
                except Exception:  # noqa: BLE001 — malformed JSON → fall through
                    pass
            metrics = client.get(f"{base}/metrics")
            result["metrics"] = parse_prom_metrics(metrics.text)
    except Exception as exc:  # noqa: BLE001 — ops CLI, never traceback
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result
