# API Documentation

This directory contains standardized API documentation for Mekong CLI services.

## Available APIs

| Service | Port | Description | Spec |
|---------|------|-------------|------|
| Agent Forest Gateway | 8000 | Task queue and worker management | [OpenAPI](agent-forest-openapi.yaml) |
| Mekongd | 8001 | LLM proxy with Anthropic compatibility | [OpenAPI](mekongd-openapi.yaml) |

## Quick Start

### View Interactive Documentation (Swagger UI)

```bash
# Start the service
uvicorn agent_forest.gateway.app:app --reload --port 8000

# Open Swagger UI
open http://localhost:8000/docs
```

### Export OpenAPI Spec from Running Service

```bash
# Agent Forest
curl http://localhost:8000/openapi.json > docs/api/agent-forest-openapi.json

# Mekongd
curl http://localhost:8001/openapi.json > docs/api/mekongd-openapi.json
```

### Generate Static HTML Documentation

```bash
# Using redoc-cli
npx redoc-cli bundle docs/api/agent-forest-openapi.yaml -o docs/api/agent-forest.html

# Using widdershins (for Markdown)
npx widdershins --search false docs/api/agent-forest-openapi.yaml -o docs/api/agent-forest.md
```

## Authentication

Most API endpoints require JWT Bearer authentication:

```
Authorization: Bearer <access_token>
```

Obtain tokens via:
- `POST /auth/register` - Create new user
- `POST /auth/login` - Login with credentials

## API Conventions

### Response Format

Successful responses return JSON:

```json
{
  "key": "value",
  "nested": {
    "data": "here"
  }
}
```

Error responses follow the format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET/PUT |
| 201 | Created | Successful POST creating resource |
| 202 | Accepted | Async operation accepted |
| 400 | Bad Request | Validation error, invalid input |
| 401 | Unauthorized | Missing or invalid auth token |
| 402 | Payment Required | Budget/credit limit exceeded |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Pagination

List endpoints support pagination via query parameters:

- `limit` (integer, default 20, max 100) - Number of items to return
- `cursor` (string, optional) - Pagination cursor for next page

Results are returned in reverse chronological order (newest first).

### Rate Limiting

API requests are rate-limited per user/token. Default: 60 requests/minute.

Rate limit headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1703047200
```

## Error Handling

The API returns standard HTTP status codes. Error responses include a `detail` field with a human-readable message:

```json
{
  "detail": "Prompt injection pattern detected: ['ignore previous instructions']"
}
```

Common error scenarios:

| Status | Scenario |
|--------|----------|
| 400 | Invalid JSON, missing required fields, validation failure |
| 401 | Missing Authorization header, expired/invalid token |
| 402 | Cloud budget exceeded (mekongd), zero balance (agent-forest) |
| 404 | Job not found, unknown endpoint |
| 429 | Rate limit exceeded |
| 500 | Provider failure, internal error |

## Development

### Regenerate OpenAPI Specs

If API schemas change, regenerate the spec files:

```bash
# From a running service
curl http://localhost:8000/openapi.json | jq '.' > docs/api/agent-forest-openapi.json

# Or export directly from FastAPI app
python -c "
from agent_forest.gateway.app import app
import json
print(json.dumps(app.openapi(), indent=2))
" > docs/api/agent-forest-openapi.json
```

### Validate Specs

```bash
# Using redocly
npx @redocly/cli lint docs/api/agent-forest-openapi.yaml

# Using spectral
npx @stoplight/spectral lint docs/api/agent-forest-openapi.yaml
```

### Standardization Guidelines

When adding new API endpoints:

1. **Use FastAPI** with Pydantic models for request/response validation
2. **Document all parameters** with descriptive docstrings
3. **Add examples** in the OpenAPI spec (see existing files)
4. **Follow naming conventions**:
   - Endpoints: plural nouns (`/tasks`, not `/task`)
   - Query params: `snake_case`
   - JSON fields: `snake_case`
5. **Version APIs** via URL prefix when making breaking changes (`/v2/messages`)
6. **Add tags** for logical grouping in Swagger UI
7. **Include response examples** for clarity


## Testing

Run API tests:

```bash
# Agent Forest
cd packages/agent-forest
poetry run pytest tests/gateway/ -v

# Mekongd
cd packages/mekongd
poetry run pytest tests/ -v
```

## See Also

- [Agent Forest OpenAPI Spec](agent-forest-openapi.yaml)
- [Mekongd OpenAPI Spec](mekongd-openapi.yaml)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAPI Specification](https://spec.openapis.org/oas/v3.1.0)
