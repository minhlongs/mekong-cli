# Phase 03 — Regex Policy Router + Stats Writer + Tests

## Context Links

- Plan: [plan.md](./plan.md)
- Phase 01 (stats schema): [phase-01-scaffold.md](./phase-01-scaffold.md)
- Phase 02 (MLX proxy): [phase-02-mlx-proxy.md](./phase-02-mlx-proxy.md)
- Research: [research-260417-1024-qwen36-solo-company.md](../reports/research-260417-1024-qwen36-solo-company.md)

## Overview

- **Priority:** P1 (final MVP phase)
- **Status:** pending (blocked by Phase 02)
- **Description:** Add regex-based router (system-prompt + model patterns → local vs cloud), cloud fallback via httpx, stats writer on every request, and full test suite (unit router + integration proxy+router+stats). Completes MVP v0.

## Key Insights

- Research Option C: route **explore/search/reformat** subagent calls to Qwen; keep **plan/opus/review** on cloud. Regex on system-prompt content identifies subagent type.
- CC CLI subagents set distinct system prompts — see `.claude/agents/*.md` (researcher, scout, debugger → local; planner, code-reviewer → cloud).
- Router must be fail-open: unknown pattern → cloud (safe default, never downgrade silent).
- Cost estimation: Anthropic Sonnet 4.5 = $3/MTok input, $15/MTok output; Qwen local = $0. `est_cost_usd` column stores hypothetical cloud cost saved.
- Stats writes are fire-and-forget (background task) — never block response.

## Requirements

### Functional

- New `router.py` exposes `decide(request: MessagesRequest, policy: RoutingPolicy) -> Literal["local","cloud"]`.
- Default `RoutingPolicy` includes regex rules:
  - system matches `(?i)you are (a )?(researcher|scout|debugger|tester)` → local
  - system matches `(?i)you are (a )?(planner|code.?reviewer|architect)` → cloud
  - model ends with `-haiku` or contains `haiku` → local
  - model contains `opus` → cloud
  - else → cloud (fail-safe)
- `/v1/messages` handler calls `decide()` → dispatches to `runtime.stream_tokens` (local) OR `cloud.forward()` (cloud).
- Cloud path uses `httpx.AsyncClient` to forward to `settings.cloud_base_url` with `x-api-key: settings.cloud_api_key`.
- After response complete (stream or not), background task writes `routing_events` row via `stats.record()`.
- `mekongd stats` output now includes: local count, cloud count, total tokens each, estimated $ saved (local_output_tokens * $15/MTok).
- `mekongd stats --since 1h|24h|7d` filters window.

### Non-Functional

- Router decision < 1ms (pure regex on short strings).
- Stats write failure never propagates to HTTP response (swallow like `local_store.py`).
- Cloud forward preserves SSE stream chunks byte-for-byte (no re-encoding).
- Test coverage for `router.py` ≥ 95% (pure function, easy target).

## Architecture

```
     POST /v1/messages
            |
            v
    +----------------+
    |   proxy.py     |
    |   handler      |
    +-------+--------+
            |
            v
    +----------------+     (local)      +-------------+
    |   router.py    |----------------->| runtime.py  |
    |   decide()     |                  | (MLX Qwen)  |
    | regex policy   |                  +------+------+
    +-------+--------+                         |
            |                                  |
            | (cloud)                          |
            v                                  |
    +----------------+                         |
    |  cloud.py      |                         |
    |  httpx POST to |                         |
    |  anthropic api |                         |
    +-------+--------+                         |
            |                                  |
            +------------------+---------------+
                               |
                               v
                    +---------------------+
                    | stats.record()      |
                    | (background task)   |
                    | INSERT routing_events|
                    +---------------------+
```

## Related Code Files

### To Create

- `/Users/macbookprom1/mekong-cli/packages/mekongd/mekongd/router.py`
- `/Users/macbookprom1/mekong-cli/packages/mekongd/mekongd/cloud.py` (httpx forwarder — small)
- `/Users/macbookprom1/mekong-cli/packages/mekongd/tests/test_router.py`

### To Modify

- `/Users/macbookprom1/mekong-cli/packages/mekongd/mekongd/stats.py` — add `record(path, route, model, input_tokens, output_tokens, latency_ms, est_cost_usd)` + enhanced `summarize(since)` with filter
- `/Users/macbookprom1/mekong-cli/packages/mekongd/mekongd/proxy.py` — inject router decision before dispatch, add background stats task
- `/Users/macbookprom1/mekong-cli/packages/mekongd/mekongd/cli.py` — `stats --since` flag
- `/Users/macbookprom1/mekong-cli/packages/mekongd/tests/test_proxy.py` — add test for cloud route (mock httpx) + stats row assertion
- `/Users/macbookprom1/mekong-cli/packages/mekongd/tests/test_stats.py` — add `test_record` + `test_summarize_with_since`

## Implementation Steps

1. Implement `router.py`:
   ```python
   @dataclass(frozen=True)
   class RoutingRule:
       pattern: re.Pattern[str]
       target: Literal["local","cloud"]
       field: Literal["system","model"]
   class RoutingPolicy(BaseModel):
       rules: list[RoutingRule]
       default: Literal["local","cloud"] = "cloud"
   DEFAULT_POLICY = RoutingPolicy(rules=[
       RoutingRule(re.compile(r"(?i)you are (a )?(researcher|scout|debugger|tester)"), "local", "system"),
       RoutingRule(re.compile(r"(?i)you are (a )?(planner|code.?reviewer|architect)"), "cloud", "system"),
       RoutingRule(re.compile(r"(?i)haiku"), "local", "model"),
       RoutingRule(re.compile(r"(?i)opus"), "cloud", "model"),
   ])
   def decide(req: MessagesRequest, policy: RoutingPolicy = DEFAULT_POLICY) -> Literal["local","cloud"]:
       for rule in policy.rules:
           haystack = req.system or "" if rule.field == "system" else req.model
           if rule.pattern.search(haystack): return rule.target
       return policy.default
   ```
2. Implement `cloud.py`:
   ```python
   async def forward_non_stream(req: MessagesRequest, settings: Settings) -> dict: ...  # httpx.AsyncClient.post
   async def forward_stream(req: MessagesRequest, settings: Settings) -> AsyncIterator[bytes]: ...  # stream_iter
   ```
3. Extend `stats.py`:
   ```python
   def record(path: Path, route: str, model: str, input_tokens: int, output_tokens: int, latency_ms: int, est_cost_usd: float) -> bool: ...
   def summarize(path: Path, since: timedelta | None = None) -> dict: ...
   def estimate_saved_usd(local_out_tokens: int) -> float: return (local_out_tokens / 1_000_000) * 15.0
   ```
4. Update `proxy.py` `/v1/messages`:
   ```python
   route = decide(req)
   start = time.monotonic()
   if route == "local":
       result = await _handle_local(rt, req)
   else:
       result = await _handle_cloud(req, settings)
   latency_ms = int((time.monotonic() - start) * 1000)
   background_tasks.add_task(stats.record, settings.db_path, route, req.model, result.input_tokens, result.output_tokens, latency_ms, estimate_saved_usd(result.output_tokens) if route=="local" else 0.0)
   return result.response
   ```
5. Update `cli.py` `stats` to accept `--since` and pretty-print rich table: route | count | in_tok | out_tok | saved_usd.
6. Write `tests/test_router.py`:
   - Researcher system prompt → local
   - Planner system prompt → cloud
   - Model `claude-3-5-haiku-20241022` → local
   - Model `claude-opus-4-6` → cloud
   - Empty system + unknown model → default cloud
   - Custom policy override works
7. Extend `tests/test_proxy.py`:
   - Mock `cloud.forward_non_stream` → assert called when system="you are a planner"
   - Assert 1 row written to stats DB with `route='cloud'`
   - Local path: assert `route='local'` + `est_cost_usd > 0`
8. Extend `tests/test_stats.py`:
   - `record()` then `summarize()` matches
   - `summarize(since=timedelta(hours=1))` excludes older rows
9. Run full suite: `pytest packages/mekongd/tests/ -v` → all green (excluding `requires_model` marker).
10. Update `README.md` with router policy table + example `curl` + stats CLI output sample.

## Todo List

- [ ] Implement `router.py` with `RoutingPolicy` + `decide()` + `DEFAULT_POLICY`
- [ ] Implement `cloud.py` httpx forwarder (stream + non-stream)
- [ ] Extend `stats.py` with `record()` + `summarize(since)` + `estimate_saved_usd()`
- [ ] Rewire `proxy.py` `/v1/messages` with router + background stats task
- [ ] Add `stats --since` flag to `cli.py` with rich table output
- [ ] Write `tests/test_router.py` (≥6 cases)
- [ ] Extend `tests/test_proxy.py` cloud + stats integration
- [ ] Extend `tests/test_stats.py` record + windowed summarize
- [ ] Update `README.md` policy + examples
- [ ] Full `pytest -v` green

## Success Criteria

- `pytest packages/mekongd/tests/` all green (router + proxy + stats + config).
- `curl` with researcher system prompt → routes local, DB row `route='local'` present.
- `curl` with planner system prompt → routes cloud (mock), DB row `route='cloud'` present.
- `mekongd stats --since 1h` prints rich table with correct totals.
- Coverage on `router.py` ≥ 95%.
- CI gates G1-G5 green.
- PR mergeable to main (no changes outside `packages/mekongd/`).

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Regex false-positive (planner prompt matches researcher rule by accident) | Rule ordering: specific cloud rules before local rules in policy; test with real CC CLI agent prompts |
| Background task DB contention | SQLite WAL mode (already set); single writer per request; `check_same_thread=False` |
| httpx timeout on cloud fallback | Set `timeout=httpx.Timeout(connect=5, read=120)`; surface 504 on timeout |
| Stats drift between real tokens and MLX tokenizer count | Document as "approximate"; add note in README |
| SSE stream proxying breaks on disconnect | Use `httpx.AsyncClient.stream()` with proper context manager; test cancel scenario |

## Security Considerations

- Cloud path: `settings.cloud_api_key` required when route="cloud" — return HTTP 500 w/ clear error if missing (don't leak "cloud=None").
- Never log `cloud_api_key` value (even at DEBUG).
- Router MUST NOT execute regex from user-supplied request body — policy is config-time only.
- Stats DB path user-scoped 0700 (inherited from Phase 01).
- Cloud forward preserves client's request body as-is — no injection of extra system prompts.

## Next Steps

- MVP v0 complete after Phase 03 merges.
- Post-MVP (out of scope, future phases):
  - OpenAI-compat `/v1/chat/completions` (research Q follow-up)
  - Polar billing integration + $19/mo SaaS tier
  - CF Tunnel public exposure + auth
  - Embedding-based router (replace regex)
  - Web dashboard

## Unresolved Questions

1. When cloud path fails (network error), should router retry local as fallback? (defer: v0 returns error; solves later with retry policy)
2. Per-repo `.mekongd/policy.yaml` override file — v0 or later? (defer; v0 uses hardcoded `DEFAULT_POLICY`)
3. Stats retention — auto-vacuum rows > 90 days? (defer; v0 keeps all)
4. Cost estimation formula — include input tokens too ($3/MTok input) or only output? (include both in v0 for accuracy; simple sum)
