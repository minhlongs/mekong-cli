# FastAPI Skill — Best Practices

## Standards
- Pydantic models for all request/response schemas
- Dependency injection via `Depends()`
- Async handlers for I/O-bound operations
- HTTPException for error responses with proper status codes

## Patterns
- Router separation: one router per domain
- Background tasks for non-blocking operations
- Lifespan context manager for startup/shutdown
- Middleware for cross-cutting concerns (auth, logging)

## Gotchas
- Don't use `sync` DB calls in `async` handlers
- Pydantic v2: use `model_validate()` not `parse_obj()`
- Always set `response_model` for type safety
- CORS middleware must be added before routes

## Security
- Validate all inputs via Pydantic
- Rate limiting on public endpoints
- JWT tokens with short expiry + refresh
- Never expose stack traces in production
