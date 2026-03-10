# Mekong SDK

Python SDK for Mekong CLI API - AI-powered task execution engine.

## Installation

```bash
pip install mekong-sdk
```

For development:

```bash
pip install mekong-sdk[dev]
```

## Quick Start

### Sync Client

```python
from mekong_sdk import MekongClient

client = MekongClient(api_key="your-api-key")

# Execute a goal
mission = client.cook("Deploy landing page with Next.js")
print(f"Mission {mission.id} status: {mission.status}")
print(f"Result: {mission.result}")

# Get mission status
mission = client.get_mission(mission.id)
```

### Async Client with Streaming

```python
import asyncio
from mekong_sdk import MekongClientAsync

async def main():
    async with MekongClientAsync(api_key="your-api-key") as client:
        async for event in client.cook_async("Create FastAPI CRUD endpoint"):
            print(f"Event: {event.event_type}")
            print(f"Data: {event.data}")

asyncio.run(main())
```

### Webhook Subscription

```python
from mekong_sdk import MekongClient

def on_mission_completed(event):
    print(f"Mission completed: {event.data}")

client = MekongClient(api_key="your-api-key")
client.subscribe("mission.completed", on_mission_completed)

mission = client.cook("Build React component", webhook_url="https://your-app.com/webhook")
```

## API Reference

### MekongClient

Synchronous client for Mekong CLI API.

#### Constructor

```python
MekongClient(
    api_key: str,           # Required: API authentication key
    base_url: str = "https://api.mekong.run",  # API base URL
    tenant_id: str = None   # Optional: Multi-tenant support
)
```

#### Methods

- `cook(goal: str, priority: str = "normal", webhook_url: str = None, **kwargs) -> Mission`
  Execute a goal synchronously.

- `get_mission(mission_id: str) -> Mission`
  Retrieve mission status and result.

- `subscribe(event: str, handler: Callable) -> None`
  Register event handler for webhooks.

- `close() -> None`
  Close HTTP client connection.

### MekongClientAsync

Asynchronous client with streaming support.

#### Constructor

Same parameters as `MekongClient`.

#### Methods

- `cook_async(goal: str, priority: str = "normal", webhook_url: str = None, **kwargs) -> AsyncIterator[MissionEvent]`
  Execute goal asynchronously with event streaming.

- `get_mission(mission_id: str) -> Mission`
  Retrieve mission status asynchronously.

- `close() -> None`
  Close async HTTP client connection.

### Data Classes

#### Mission

```python
@dataclass
class Mission:
    id: str
    goal: str
    status: str
    tenant_id: Optional[str]
    created_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: dict
    error: Optional[str]
```

#### MissionEvent

```python
@dataclass
class MissionEvent:
    event_type: str       # e.g., "mission.step.completed"
    mission_id: str
    data: dict
    timestamp: datetime
```

## Event Types

Supported events for webhook subscription:

| Event | Description |
|-------|-------------|
| `mission.created` | Mission created successfully |
| `mission.planning` | Plan steps generated |
| `mission.step.started` | A step execution started |
| `mission.step.completed` | A step completed |
| `mission.step.failed` | A step failed (includes retry info) |
| `mission.completed` | Mission completed successfully |
| `mission.failed` | Mission failed (includes error) |
| `credits.low` | Tenant balance below threshold |

## Error Handling

```python
import httpx
from mekong_sdk import MekongClient

client = MekongClient(api_key="invalid-key")

try:
    mission = client.cook("Invalid goal")
except httpx.HTTPStatusError as e:
    print(f"HTTP error: {e.response.status_code}")
except httpx.RequestError as e:
    print(f"Request failed: {e}")
```

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `MEKONG_API_KEY` | API authentication key | Required |
| `MEKONG_BASE_URL` | API base URL | `https://api.mekong.run` |
| `MEKONG_TENANT_ID` | Tenant identifier | None |

## Development

```bash
# Clone repository
git clone https://github.com/longtho638-jpg/mekong-cli
cd mekong-cli/packages/sdk

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check mekong_sdk/

# Type check
mypy mekong_sdk/
```

## License

MIT License - See LICENSE file for details.

## Support

- Documentation: https://github.com/longtho638-jpg/mekong-cli#readme
- Issues: https://github.com/longtho638-jpg/mekong-cli/issues
- Discord: https://discord.gg/mekong-cli
