# Swarm Auth Gate — 2026-08-19

## Defect

`AUTONOMY_GAPS.md` priority #7: swarm node operations had no auth. Any
client that could reach the gateway could register a remote node and dispatch
arbitrary goals to it — unauthorized swarm access and remote command execution.

`verify_token()` existed in `gateway_main.py` but was never called by any
endpoint; only `/cmd` and `/halt` checked tokens, and those checked them in the
request body, not a header.

## Fix

| File | Change |
|------|--------|
| `src/core/gateway/gateway_main.py` | Added `require_swarm_token(request)` dependency: reads `X-API-Key` header, fails-closed on missing header (401), then calls `verify_token()`. Wired it as a `Depends` on all 4 swarm endpoints: `/swarm/register`, `/swarm/nodes`, `/swarm/dispatch`, `/swarm/nodes/{id}`. Added `Depends` and `Request` to the FastAPI import. |
| `tests/core/gateway/test_gateway_main.py` | `TestSwarmEndpoints` grew from 3 to 10 tests. Existing 3 now send `X-API-Key`. Added: missing header → 401, wrong token → 401, list/dispatch without token → 401. |

## Verification

- `tests/core/gateway/test_gateway_main.py`: **49 passed** (was 40; +9)
- `ruff check src/core/gateway/gateway_main.py tests/core/gateway/test_gateway_main.py`: clean
- CI-gated subset (`tests/core tests/cli tests/seed tests/commands tests/auth tests/unit tests/daemon tests/vn`): **2246 passed, 0 failed** (baseline 2242)

## Design notes

- Reuses the existing `verify_token()` + `MEKONG_API_TOKEN` env var rather than
  inventing a new credential scheme.
- Follows the `X-API-Key` header convention already used by
  `src/core/gateway_api.py`, so the same client code works against both
  surfaces.
- Fail-closed: a missing header is a 401, not a pass-through. A misconfigured
  server (no `MEKONG_API_TOKEN`) returns 500, matching `/cmd` behavior.
- CLI side (`src/cli/swarm_commands.py`) is unchanged — it stores a node's
  *own* token locally and sends it in the request body when dispatching, which
  is the client-to-node credential, not the client-to-gateway credential.

## Status

Verified, not committed.