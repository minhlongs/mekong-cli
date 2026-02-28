# RaaS SDK Guide

Python client for integrating with the Mekong RaaS API.

---

## Installation

```bash
pip install mekong-cli
```

Or from source:

```bash
git clone https://github.com/mekong-ai/mekong-cli
cd mekong-cli && pip install -e .
```

---

## Quickstart

```python
from src.raas.sdk import MekongClient

client = MekongClient(
    base_url="http://localhost:8000",
    api_key="mk_your_api_key_here",
)

# Create a mission
mission = client.create_mission("Generate Q1 revenue report as CSV")
print(mission.id)        # f47ac10b-...
print(mission.status)    # queued
print(mission.credits_cost)  # 1

# Poll status
status = client.get_mission(mission.id)
print(status.status)     # queued | running | completed | failed
```

---

## SSE Streaming

Subscribe to real-time mission status updates via Server-Sent Events:

```python
from src.raas.sdk import MekongClient

client = MekongClient(
    base_url="http://localhost:8000",
    api_key="mk_your_api_key_here",
)

print("Listening for events...")
for event in client.stream_dashboard():
    print(f"Event: {event}")
    # {'type': 'mission.status', 'mission_id': '...', 'status': 'completed'}
```

The `stream_dashboard()` method uses `httpx` with `iter_lines()` and yields
one parsed dict per SSE `data:` line. The loop runs until the connection drops.

---

## Error Handling

All non-2xx responses raise `MekongAPIError`:

```python
from src.raas.sdk import MekongClient, MekongAPIError

client = MekongClient(base_url="http://localhost:8000", api_key="mk_abc")

try:
    mission = client.create_mission("Deploy to prod")
except MekongAPIError as e:
    if e.status_code == 402:
        print("Not enough credits — top up via Polar.sh")
    elif e.status_code == 401:
        print("Invalid API key")
    else:
        print(f"Unexpected error {e.status_code}: {e.detail}")
```

`MekongAPIError` attributes:
- `status_code` — HTTP status integer
- `detail` — error message string from the API

---

## Client Reference

### `MekongClient(base_url, api_key, timeout=30)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | str | — | Root URL, e.g. `http://localhost:8000` |
| `api_key` | str | — | Bearer token starting with `mk_` |
| `timeout` | float | 30 | HTTP request timeout in seconds |

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `create_mission(goal, complexity=None)` | `Mission` | POST /raas/missions |
| `get_mission(mission_id)` | `Mission` | GET /raas/missions/{id} |
| `list_missions(limit=20, offset=0)` | `list[Mission]` | GET /raas/missions |
| `cancel_mission(mission_id)` | `Mission` | POST /raas/missions/{id}/cancel |
| `get_logs(mission_id)` | `str` | GET /raas/missions/{id}/logs |
| `stream_dashboard()` | `Iterator[dict]` | GET /raas/dashboard/stream (SSE) |
