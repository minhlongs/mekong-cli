# Phase 02 — Gateway: Auth, Users, Models, Rate Limiter

## Context Links

- Upstream: `phase-01-setup-pyproject-readme.md`
- DeepSeek doc sections: "BƯỚC 2.2.2 (Gateway main.py)" + "BƯỚC 3.2.3 (auth.py)" — we cherry-pick JWT from Phase 3 and skip Postgres.
- agent-core reference: `packages/agent-core/src/agent_core/tools/file_system.py` (path-traversal pattern).

## Overview

- Priority: P0
- Status: pending
- Build auth primitives and data contracts for the gateway. Zero FastAPI routes in this phase — routes land in Phase 03. Keeps each module <200 LOC and testable in isolation.

## Key Insights

- Static users loaded from YAML (or in-code default) with bcrypt-hashed passwords. Layout: `{username: {id, hashed_password}}`.
- JWT `sub` claim = `user_id` (not username) so future Postgres migration doesn't break tokens.
- Pydantic v2 `BaseModel` with `model_config = ConfigDict(extra="forbid")` for strict request validation.
- Rate limiting: `slowapi` with key_func derived from JWT `sub`. Memory storage OK for single-process dev; Phase 3 can swap for Redis-backed.
- Webhook URL SSRF guard: reject `http://`, reject RFC 1918 / loopback / link-local / reserved via `ipaddress.ip_address(socket.gethostbyname(host))`.

## Requirements

### Functional

- R1: `hash_password(plain) -> str` and `verify_password(plain, hashed) -> bool` using bcrypt.
- R2: `create_access_token(user_id, extra_claims) -> str` + `decode_token(jwt_str) -> dict` raising on expiry/invalid.
- R3: `UsersStore.authenticate(username, password) -> User | None` backed by YAML or built-in defaults.
- R4: Pydantic models: `LoginRequest`, `TokenResponse`, `MeResponse`, `TaskRequest`, `TaskResponse`, `JobStatus`, `JobSummary`.
- R5: `validate_webhook_url(url) -> None` raising `ValueError` on scheme≠https, private IP, loopback, or DNS fail.
- R6: `RateLimiter` helper exposing `slowapi.Limiter` instance keyed by `sub` claim.

### Non-functional

- N1: Each module <200 LOC.
- N2: 100% unit coverage on auth utils, webhook validator, users store.
- N3: No network calls from tests; webhook validator uses injectable resolver for testing.

## Architecture

```
gateway/
├── __init__.py
├── auth_jwt.py           # JWT encode/decode, HS256
├── auth_passwords.py     # bcrypt wrapper (passlib)
├── users_store.py        # YAML-backed static users, authenticate()
├── models.py             # Pydantic request/response schemas
├── security_webhook.py   # SSRF guard for webhook_url
└── rate_limit.py         # slowapi Limiter + key_func
```

Component graph:

```
LoginRequest ─┐
              ├─> UsersStore.authenticate ─> User ─> auth_jwt.create_access_token ─> TokenResponse
TokenBearer ──┘                                         │
                                                        ▼
                                            auth_jwt.decode_token ─> user_id
                                                        │
                                                        ▼
                                            UsersStore.get_by_id ─> User
```

## Related Code Files

### Create

- `packages/agent-forest/src/agent_forest/gateway/auth_jwt.py` (~80 LOC)
- `packages/agent-forest/src/agent_forest/gateway/auth_passwords.py` (~30 LOC)
- `packages/agent-forest/src/agent_forest/gateway/users_store.py` (~120 LOC)
- `packages/agent-forest/src/agent_forest/gateway/models.py` (~80 LOC)
- `packages/agent-forest/src/agent_forest/gateway/security_webhook.py` (~80 LOC)
- `packages/agent-forest/src/agent_forest/gateway/rate_limit.py` (~40 LOC)
- `packages/agent-forest/tests/test_auth_jwt.py` (~70 LOC)
- `packages/agent-forest/tests/test_auth_passwords.py` (~30 LOC)
- `packages/agent-forest/tests/test_users_store.py` (~90 LOC)
- `packages/agent-forest/tests/test_models.py` (~60 LOC)
- `packages/agent-forest/tests/test_security_webhook.py` (~90 LOC)

### Modify

- `packages/agent-forest/src/agent_forest/gateway/__init__.py`: export public surface.

## Implementation Steps

1. `auth_passwords.py`: thin wrapper over `passlib.context.CryptContext(schemes=["bcrypt"])`. Two functions.
2. `auth_jwt.py`:
   - `create_access_token(user_id: str, settings: ForestSettings, extra: dict | None = None) -> str`
   - `decode_token(token: str, settings: ForestSettings) -> dict` — raises `JWTError` subclass for expired vs invalid.
3. `users_store.py`:
   - `@dataclass User(id, username, hashed_password)`.
   - `UsersStore.from_yaml(path)` — parse YAML `users: [{id, username, password_hash}]`. Validate no duplicate ids/usernames.
   - `UsersStore.default()` — two seed users `founder1/secret1` and `founder2/secret2` (bcrypt-hashed at load time). Matches doc's mock but hashed.
   - Methods: `authenticate(username, password) -> User | None`, `get_by_id(user_id) -> User | None`, `list() -> list[User]`.
4. `models.py`:
   - `LoginRequest(username: str, password: str)` with constrained lengths.
   - `TokenResponse(access_token, token_type="bearer", expires_in: int)`.
   - `MeResponse(id, username)`.
   - `TaskRequest(prompt: str, webhook_url: HttpUrl | None)` with prompt ≤8000 chars.
   - `TaskResponse(job_id, status, created_at)`.
   - `JobStatus(job_id, status, result, error, created_at, updated_at)`.
   - `JobSummary(job_id, status, created_at)` for listing.
   - Enum: `JobState = Literal["queued","running","completed","failed"]`.
5. `security_webhook.py`:
   - `validate_webhook_url(url: str, *, resolver=socket.gethostbyname) -> None`.
   - Checks: parse via `urllib.parse`, require `https` scheme, require host, resolve host via resolver, reject if resolved IP is `ip.is_private or is_loopback or is_link_local or is_reserved or is_multicast`.
   - Raise `ValueError` with specific messages for each failure mode (useful for HTTP 400 detail).
6. `rate_limit.py`:
   - `def user_key_func(request) -> str`: pull `sub` from verified JWT cached on `request.state.user_id`. Fallback to remote_addr.
   - Expose `limiter = Limiter(key_func=user_key_func, default_limits=[f"{N}/minute"])` built from `ForestSettings`.
7. Tests:
   - `test_auth_passwords.py`: round-trip hash+verify, wrong password returns False.
   - `test_auth_jwt.py`: encode/decode round-trip, expired token raises, tampered signature raises, wrong algorithm raises.
   - `test_users_store.py`: defaults load with 2 users, YAML load/validate, duplicate-id rejected, authenticate happy+wrong-pw+missing-user.
   - `test_models.py`: TaskRequest rejects >8000 char prompt, extra fields forbidden.
   - `test_security_webhook.py`: accepts `https://example.com` (mocked resolver), rejects `http://`, `https://127.0.0.1`, `https://10.0.0.1`, `https://169.254.169.254` (AWS metadata), unknown DNS.

## Todo List

- [x] `auth_passwords.py` + tests.
- [x] `auth_jwt.py` + tests (4 cases).
- [x] `users_store.py` + tests (5 cases).
- [x] `models.py` + tests (3 cases).
- [x] `security_webhook.py` + tests (6 cases: happy + 5 rejection modes).
- [x] `rate_limit.py` (no unit tests; integration via Phase 03).
- [x] `gateway/__init__.py` exports.
- [x] `ruff check` clean.
- [x] `pytest` green for all Phase 02 tests.

## Success Criteria

- All Phase 02 tests pass.
- Each module <200 LOC.
- `python -c "from agent_forest.gateway import users_store; s=users_store.UsersStore.default(); assert s.authenticate('founder1','secret1')"` works.
- Webhook validator rejects AWS metadata endpoint IP `169.254.169.254`.

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| bcrypt hashing slow in unit tests (80ms/op) | Medium | Use `rounds=4` test override via settings; prod default `rounds=12`. |
| DNS resolution during tests leaks network | High | Always inject `resolver=` in tests; real `socket.gethostbyname` only in prod path. |
| JWT algorithm confusion (HS256 vs RS256) | High | Hard-pin HS256 in decode; reject `alg: none` and `alg: RS256`. |

## Security Considerations

- Bcrypt work factor from env (`FOREST_BCRYPT_ROUNDS`, default 12, test default 4). Never hash with rounds <10 in prod.
- JWT secret MUST be ≥32 bytes; `config.from_env()` enforces.
- Tokens expire (default 7d); refresh not in scope.
- `users_store.UsersStore.default()` intended for dev only — log warning when used.
- Webhook validator is the sole defense against SSRF; 5s timeout enforced downstream in worker.

## Next Steps

- Phase 03 imports every module here to wire FastAPI routes.
- Phase 05 smoke-tests the full login→task flow via `TestClient`.
