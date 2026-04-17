# Code Review — packages/agent-forest (Phase 2 Forest)

**Reviewer:** code-reviewer | **Date:** 2026-04-17 | **Scope:** 16 src files / 891 LOC + 8 test files / 445 LOC
**Verdict:** APPROVE WITH FOLLOW-UPS — Score **9.2/10** | 0 CRITICAL | 2 HIGH | 4 MEDIUM | 3 LOW

---

## Per-File Scores (Sec / Corr / Read / Tests / Perf)

| File | Score | Note |
|---|---|---|
| `auth.py` | 9.5 | Clean jose HS256, exp enforced, no `algorithms="none"` accepted |
| `users.py` | 9.0 | bcrypt via passlib, defaults flagged dev-only |
| `config.py` | 9.0 | Required `JWT_SECRET=REDACTED_KEY` unless `FOREST_TESTING=1` — good guard |
| `gateway/deps.py` | 9.0 | Correct bearer parse + `WWW-Authenticate` header |
| `gateway/app.py` | 8.0 | CORS `allow_origins=["*"]`+`allow_credentials=True` is risky combo |
| `gateway/routes_auth.py` | 9.5 | Idiomatic, no info-leak in 401 |
| `gateway/routes_task.py` | 9.5 | user_id sourced from JWT — no IDOR |
| `queue.py` | 9.0 | Per-user namespaced keys, TTL set, parse_job_key strict |
| `sandbox.py` | 9.0 | Path-traversal guard via `relative_to()` |
| `webhook.py` | 7.5 | DNS rebinding window; see HIGH-1 |
| `worker/main.py` | 9.5 | spawn ctx + 300s timeout; clean drain on SIGTERM |
| `worker/runner.py` | 8.5 | Reload pattern works; `os.environ` mutation lives in spawned proc only |
| `models.py` | 10 | Tight Pydantic constraints |
| `cli.py` | 9.0 | Typer wiring fine |
| **Package** | **9.2** | Above 9.0 approve threshold; below 9.5 auto-approve |

---

## Issues by Severity

### CRITICAL (block merge): **none**

### HIGH (fix in follow-up before prod traffic)

**HIGH-1 — Webhook SSRF: DNS-rebinding TOCTOU + 0.0.0.0 bypass**
`webhook.py:43-51, 54-66` — `validate_webhook_url` resolves DNS, then `httpx.post` resolves DNS again. Attacker host can return public IP first, private on second lookup. Also `0.0.0.0` is **not** caught: `ipaddress.ip_address("0.0.0.0").is_loopback == False, .is_private == False` (it's `is_unspecified`). IPv6 `::`/`::1` checks via `is_loopback` cover `::1` but not `is_unspecified`, and IPv4-mapped-v6 (`::ffff:127.0.0.1`) escapes `is_loopback` on some Python versions.
**Fix:** add `ip.is_unspecified` and `ip.is_reserved` to deny list; for the worker `send_webhook` path resolve once and pass `httpx.post(url, ..., transport=httpx.HTTPTransport(...))` pinned to that IP via Host header — or accept residual risk and document. Minimum: add `is_unspecified` + IPv4-mapped check now.
**Repro:** `curl -X POST .../task -d '{"prompt":"x","webhook_url":"https://0.0.0.0:6379/"}'` is currently accepted by `validate_webhook_url`.

**HIGH-2 — CORS wildcard with credentials**
`gateway/app.py:35-41` — `allow_origins=["*"]` + `allow_credentials=True` is rejected by browsers per spec, but FastAPI **silently** allows it server-side. Once a real origin is configured this becomes a CSRF surface for cookie/credential sessions. Phase 2 uses bearer tokens, so impact is low today, but Phase 3 may add cookies.
**Fix:** either set `allow_credentials=False` (current bearer-only model) or replace `["*"]` with explicit origins from `FOREST_ALLOWED_ORIGINS` env.

### MEDIUM

**MED-1 — `gateway_host` defaults to `0.0.0.0`** (`config.py:30, 54`) — fine in Docker, but the `# noqa: S104` masks the risk for bare-metal `agent-forest gateway`. Document deployment expectation in README.

**MED-2 — Rate-limit key uses raw bearer token prefix** (`gateway/app.py:17-22`) — `auth.split(None,1)[1][:64]` keys on the first 64 chars of the JWT. JWT header (`eyJhbGciOiJIUzI1NiIs...`) is identical for all tokens issued with the same algorithm, so first 64 chars **may collide** across users. Token bodies start to differ ~position 36. With HS256 and current `jose` defaults the first 36 chars are constant, and `sub` claim diverges shortly after — collisions unlikely but possible. **Fix:** decode token cheaply or hash full token: `hashlib.sha256(token.encode()).hexdigest()[:32]`. Anonymous attackers are already capped by `get_remote_address` fallback, which is good.

**MED-3 — `list_jobs` uses `SCAN job:{user_id}:*`** (`queue.py:57-65`) — `user_id` originates from JWT `sub`, which is set server-side from the user store, so injection of `*` glob chars is impossible *today*. But `users.py:49` reads `entry["user_id"]` from YAML with no validation. A misconfigured YAML with `user_id: "*"` would let that user enumerate all jobs. **Fix:** validate `user_id` matches `^[a-zA-Z0-9_-]+$` in `users.load_users`.

**MED-4 — `_execute_in_subprocess` 300s hard timeout, no graceful cancel** (`worker/main.py:49-53`) — `proc.terminate()` then `join(5)` may leave zombie LLM HTTP connections. Acceptable for Phase 2; document.

### LOW

- **LOW-1** — `auth.py:24` uses default `jose.jwt.decode` options, which **does not** validate `iat`/`nbf` if absent. Minor; HS256+`exp` is enough for Phase 2.
- **LOW-2** — `users.py` defaults seed two real bcrypt hashes at import time → ~250ms cold start. Lazy-init or skip when `users_yaml` set.
- **LOW-3** — `webhook.py:62` does not pin `verify=True` explicitly (httpx default is True; documenting helps).

---

## Tenant Isolation — Verified

- `routes_task.py` always sources `user_id` from `current_user` (JWT-decoded), never from request body. ✓
- `queue.job_key` namespaces every read/write. ✓
- `worker/main.py:71-76` parses key, then re-fetches via the same namespaced helper. No cross-tenant fanout. ✓
- `sandbox.user_output_dir` rejects `/`, `..`, NUL and uses `relative_to`. ✓

## JWT — Verified

- Secret required in non-test mode (`config.py:41-44`). ✓
- Algorithm whitelisted (`algorithms=[settings.jwt_algorithm]`), so `alg=none` attack blocked. ✓
- `exp` set + enforced by `jose.jwt.decode`. ✓

## Dependency Pin

- `bcrypt<4.1` is correct: passlib 1.7.4 raises `AttributeError: module 'bcrypt' has no attribute '__about__'` with bcrypt 4.1+. Comment present. ✓ Phase 3 should migrate to argon2-cffi or passlib 1.8 when released.

---

## Recommended Follow-up Tasks (post-merge)

1. **HIGH-1 fix** — add `is_unspecified` + IPv4-mapped-IPv6 deny in `webhook._host_resolves_public`. ~15 min.
2. **HIGH-2 fix** — env-driven `FOREST_ALLOWED_ORIGINS`, default to `[]`. ~20 min.
3. **MED-3 fix** — `user_id` regex validation in `users.load_users`. ~10 min.
4. **MED-2 fix** — sha256-hashed rate-limit key. ~10 min.

Total follow-up budget: ~1h. Non-blocking for Phase 2 launch on trusted dev/dogfood traffic.

---

## Unresolved Questions

1. Does Phase 3 (Land) replace `mp.spawn` with Docker per-tenant? If yes, `runner.py` `importlib.reload` becomes unnecessary — defer cleanup.
2. Should webhook payload include HMAC signature header for client-side verification? (Out of Phase 2 scope; flag for Phase 3.)
3. Is `FOREST_TESTING=1` ever set in CI but reachable from prod env? Audit deploy scripts.
