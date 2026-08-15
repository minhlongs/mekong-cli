# API Documentation Style Guide

This guide defines standards for all API documentation in the Mekong CLI project.

---

## Principles

1. **Clarity over completeness** — Be concise but thorough
2. **Examples first** — Show usage before detailed specs
3. **Progressive disclosure** — Basic → advanced topics
4. **Maintainability** — Easy to update, avoid duplication
5. **User-centric** — Answer "How do I...?" questions

---

## File Organization

```
docs/
├── api/
│   ├── README.md              # API overview (this doc)
│   ├── STYLE_GUIDE.md         # This document
│   ├── AUTHENTICATION.md      # Auth mechanisms
│   ├── ERROR_CODES.md         # Standard error responses
│   ├── RATE_LIMITING.md       # Rate limit policies
│   ├── VERSIONING.md          # API versioning strategy
│   ├── mekongd-openapi.yaml   # Core gateway spec
│   ├── agent-forest-openapi.yaml
│   └── partner-monitoring-openapi.yaml
└── reference/
    └── API_REFERENCE.md       # User-facing API reference
```

---

## Content Standards

### 1. OpenAPI Specifications

All public APIs MUST have an OpenAPI 3.1.0 specification in YAML format.

**Requirements:**

- File: `docs/api/<service>-openapi.yaml`
- Version: `openapi: 3.1.0`
- Format: YAML with 2-space indentation (no tabs)
- Schema: Complete with all endpoints, parameters, request/response bodies
- Examples: Every field should have example values

**Minimal info block:**

```yaml
openapi: 3.1.0
info:
  title: Mekongd API
  description: |
    Core gateway API for Mekong CLI. Provides command execution,
    billing, plugin management, and user operations.
  version: 1.0.0
  contact:
    name: Mekong Team
    email: api@mekong.cli
  license:
    name: MIT
```

**Servers block:**

```yaml
servers:
  - url: http://localhost:8000
    description: Development server
  - url: https://api.mekong.cli
    description: Production server
```

### 2. Endpoint Documentation

Every endpoint must document:

- **Summary** (brief, < 80 chars)
- **Description** (detailed, markdown)
- **Parameters** (path, query, header) with type, description, example
- **Request body** schema (if POST/PUT)
- **Responses** for all status codes (200, 201, 400, 401, 402, 403, 404, 429, 500)
- **Authentication** requirements
- **Rate limiting** impact (if special)
- **Example cURL** request and response

**Example endpoint:**

```yaml
/health:
  get:
    summary: Health check endpoint
    description: |
      Returns system health status. Used for liveness probes
      by load balancers and Kubernetes.
    operationId: health_check
    tags:
      - infra
    security: []  # No auth required
    responses:
      '200':
        description: System healthy
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/HealthResponse'
            examples:
              healthy:
                summary: Healthy response
                value:
                  status: healthy
                  timestamp: "2026-06-21T08:30:00Z"
                  services:
                    database: up
                    redis: up
      '503':
                description: Service unavailable
                content:
                  application/json:
                    schema:
                      $ref: '#/components/schemas/ErrorResponse'
```

### 3. Schema Definitions

Use `components/schemas/` for reusable data structures.

**Requirements:**

- Descriptive property names (snake_case)
- `description:` for every property (unless obvious like `id`, `timestamp`)
- `example:` for every field
- Appropriate types (`string`, `integer`, `boolean`, `array`, `object`)
- Use `format:` for specialized strings (email, uuid, date-time)
- Enumerations: list all possible values with descriptions

**Example schema:**

```yaml
Command:
  type: object
  required:
    - id
    - name
    - description
  properties:
    id:
      type: string
      format: uuid
      description: Unique command identifier
      example: "550e8400-e29b-41d4-a716-446655440000"
    name:
      type: string
      description: Command name (slash command path)
      example: "/founder/annual"
    description:
      type: string
      description: Human-readable description
      example: "Generate annual business plan"
    layer:
      type: string
      enum:
        - founder
        - business
        - product
        - engineering
        - ops
      description: Business layer this command belongs to
      example: "founder"
    mcu_cost:
      type: integer
      minimum: 0
      description: Credits deducted on execution
      example: 5
```

### 4. Error Responses

Standardize error format across all APIs:

```yaml
ErrorResponse:
  type: object
  required:
    - detail
  properties:
    detail:
      type: string
      description: Human-readable error message
      example: "Invalid command: /unknown/command"
    code:
      type: string
      description: Machine-readable error code (optional)
      example: "COMMAND_NOT_FOUND"
    request_id:
      type: string
      description: Request identifier for support
      example: "req_abc123def456"
```

**Standard HTTP codes:**

| Code | Use For | Example |
|------|---------|---------|
| 200 | Success | Command executed, data returned |
| 201 | Created | Plugin installed, user created |
| 202 | Accepted | Async task queued (e.g., long-running cook) |
| 400 | Bad Request | Validation error, missing required field |
| 401 | Unauthorized | Missing/invalid/expired token |
| 402 | Payment Required | Insufficient MCU balance |
| 403 | Forbidden | User lacks permission for resource |
| 404 | Not Found | Command, plugin, or user doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Error | Unhandled exception |
| 503 | Service Unavailable | Backend service down |

**Document each error code** in the endpoint's `responses` section.

### 5. Authentication

All endpoints (except `/health`, `/ready`) require authentication via Bearer token.

**Security schemes definition:**

```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |
        API token from `mekong auth token` or dashboard.
        Token must be passed in Authorization header:
        `Authorization: Bearer <token>`
```

Apply globally:

```yaml
security:
  - bearerAuth: []
```

Or per-endpoint:

```yaml
/commands/execute:
  post:
    security:
      - bearerAuth: []
```

### 6. Rate Limiting

Document rate limits in endpoint description if non-standard.

Standard limits (apply globally):

| Tier | Requests/min | Burst |
|------|--------------|-------|
| Starter | 60 | 10 |
| Growth | 300 | 50 |
| Pro | 1000 | 200 |

**Response headers** (include in docs):

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1624267200
```

When rate limited, response includes `429` status and `Retry-After` header.

### 7. Pagination

For list endpoints, use cursor-based pagination (preferred) or offset-based.

**Cursor-based (recommended):**

```yaml
GET /api/v1/commands
parameters:
  - name: cursor
    in: query
    description: Pagination cursor from previous response
    schema:
      type: string
  - name: page_size
    in: query
    description: Items per page (max 100, default 50)
    schema:
      type: integer
      minimum: 1
      maximum: 100
      default: 50
```

Response:

```yaml
ListCommandsResponse:
  type: object
  properties:
    items:
      type: array
      items:
        $ref: '#/components/schemas/Command'
    next_cursor:
      type: string
      description: Cursor for next page, null if last page
      example: "cursor_abc123"
    has_more:
      type: boolean
      description: True if more items exist
```

**Offset-based (legacy):**

```yaml
parameters:
  - name: page
    in: query
    schema:
      type: integer
      minimum: 1
      default: 1
  - name: page_size
    in: query
    schema:
      type: integer
      minimum: 1
      maximum: 100
      default: 50
```

### 8. Filtering & Sorting

Document available filters and sort options for list endpoints.

**Example:**

```yaml
GET /api/v1/plugins
parameters:
  - name: category
    in: query
    description: Filter by category
    schema:
      type: string
      enum: [billing, productivity, vietnam, integration]
  - name: installed
    in: query
    description: Show only installed plugins
    schema:
      type: boolean
  - name: sort
    in: query
    description: Sort field and direction
    schema:
      type: string
      enum: [-name, name, -installed_at, installed_at]
      default: -installed_at
```

### 9. Request/Response Examples

Every operation needs at least one example.

**For successful response:**

```yaml
responses:
  '200':
    description: Command executed successfully
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/CommandResult'
        examples:
          simple_echo:
            summary: Echo command example
            value:
              execution_id: "exec_abc123"
              command: "/test/echo"
              result:
                message: "Hello, World!"
                timestamp: "2026-06-21T08:30:00Z"
              execution_time_ms: 245
```

**For error response:**

```yaml
'400':
  description: Validation error
  content:
    application/json:
      schema:
        $ref: '#/components/schemas/ErrorResponse'
      example:
        detail: "Invalid argument: amount must be positive"
        code: "VALIDATION_ERROR"
        request_id: "req_abc123"
```

### 10. Field Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| ID fields | `{resource}_id` | `command_id`, `user_id`, `plugin_id` |
| Timestamps | `created_at`, `updated_at` | `created_at`, `deleted_at` |
| Counts | `{noun}_count` | `command_count`, `user_count` |
| Booleans | `is_`, `has_`, `can_` | `is_active`, `has_children`, `can_edit` |
| Foreign keys | `{resource}_id` | `parent_id`, `owner_id` |

**JSON format:** Always snake_case, never camelCase.

---

## Writing Style

### Voice

- **Active voice:** "The API returns..." not "A return will be generated..."
- **Present tense:** "The endpoint returns..." not "The endpoint will return..."
- **Second person:** "You can..." not "The user can..."

### Punctuation

- End sentences with periods (even in descriptions)
- Use Oxford comma in lists
- Colons inside strings must be quoted (YAML requirement)
  - ❌ `description: Time window in hours (default: 168 = 1 week)` → parse error
  - ✅ `description: "Time window in hours (default: 168 = 1 week)"`

### Code Formatting

- Inline code: `` `code` ``
- Code blocks: Use triple backticks with language identifier
- URLs: Full URLs with `https://` prefix
- Command examples: Use `$` prefix for shell

```markdown
To execute a command:

```bash
$ mekong /founder/annual --year 2026
```
```

### Tables

Use tables for enumerating options, enums, or multiple fields:

```markdown
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `command` | string | Yes | Command path (e.g., `/founder/annual`) |
| `arguments` | object | No | Command arguments as key-value pairs |
| `async` | boolean | No | Run asynchronously (default: false) |
```

---

## Validation

Before committing:

1. **YAML syntax check:**

   ```bash
   python3 -c "import yaml; yaml.safe_load(open('docs/api/mekongd-openapi.yaml'))"
   ```

2. **OpenAPI linter:**

   ```bash
   npx @redocly/cli lint docs/api/*.yaml
   ```

3. **Generate HTML to preview:**

   ```bash
   npx redoc-cli bundle docs/api/mekongd-openapi.yaml -o docs/api/preview.html
   open docs/api/preview.html
   ```

4. **Verify all endpoints documented:**

   ```bash
   # Compare routes in code vs spec
   python3 scripts/api-docs/verify-coverage.py
   ```

---

## Updating Specifications

When API changes:

1. Update FastAPI route with proper docstrings and Pydantic models
2. Start service locally: `uvicorn src.api.gateway:app --reload --port 8000`
3. Export spec:

   ```bash
   curl http://localhost:8000/openapi.json > docs/api/mekongd-openapi.json
   ```

4. Convert to YAML:

   ```bash
   yq eval -o y docs/api/mekongd-openapi.json > docs/api/mekongd-openapi.yaml
   ```

5. Manually review and reformat to match style guide
6. Update this style guide if conventions change
7. Commit with message: `docs(api): update <service> spec for <feature>`

---

## Common Pitfalls

| Problem | Solution |
|---------|----------|
| YAML parse error due to colon in string | Quote the string or use `|` for multiline |
| Missing example causes warning | Add `example:` or `examples:` to every field |
| Schema doesn't match actual response | Update spec to match implementation |
| Authentication not documented | Add `security:` section to endpoint |
| Circular `$ref` references | Break cycle with `allOf` or separate schema |
| Duplicate operationId | Ensure unique operationId across all paths |

---

## Resources

- [OpenAPI Specification 3.1.0](https://spec.openapis.org/oas/v3.1.0)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Redocly Style Guide](https://redocly.com/docs/guides/style-guide/)
- [API Documentation Standards](../../../.claude/rules/api-documentation-standards.md) (internal)

---

**Questions?** Ask in #api-docs on Discord or open an issue in the repository.
