# Smoke Tests — Live Gateway Health

Read-only synthetic monitoring scripts. Run against the live gateway to verify
endpoint health, schema correctness, and auth gate enforcement. Safe for cron
and pre-call gates (e.g., before weekly Zalo OPC pilot calls).

## Why `infra/smoke/` not `scripts/`

Root-level `scripts/` is gitignored (per-machine founder ops). These smoke
scripts ship with the repo so any clone (laptop, CI runner, second machine)
can verify production health without manual port-over.

## Available

| Script | Tests |
|--------|-------|
| `smoke-pilot-flow.sh` | VN Pilot endpoints (6 GETs + 1 POST auth gate enforcement). Validates schemas + `trial+converted==active` invariant. |

## Run

```bash
# Production (default)
./infra/smoke/smoke-pilot-flow.sh

# Local dev gateway
GATEWAY=http://localhost:8000 ./infra/smoke/smoke-pilot-flow.sh

# Dump response bodies on failure for debugging
VERBOSE=1 ./infra/smoke/smoke-pilot-flow.sh

# Longer timeout for slow networks
TIMEOUT=20 ./infra/smoke/smoke-pilot-flow.sh
```

Exit codes: `0` all pass · `1` any fail · `2` missing dependency (`curl`/`jq`).

## Cron Setup (Optional)

Add to crontab to alert on production drift:

```cron
# Every 5 minutes — log to file, alert via osascript if fail
*/5 * * * * /Users/macbook/mekong-cli/infra/smoke/smoke-pilot-flow.sh >> /var/log/mekong-smoke.log 2>&1 || osascript -e 'display notification "Gateway smoke failed" with title "Mekong"'
```

## Design Rules

1. **Read-only** — no `POST /signup`, `/response`, or authenticated `/convert`.
   Don't pollute `pilots.jsonl` / `conversions.jsonl` (those are append-only,
   no DELETE endpoint).
2. **Fast** — full run < 5s against prod.
3. **Schema-aware** — validates required keys are present, not just HTTP 200.
4. **Invariant checks** — verifies cross-endpoint logic (e.g.,
   `trial_pilots + converted_pilots == active_pilots`).
5. **Cron-safe** — deterministic, no flaky retries, no side effects.

Write-path regression coverage lives in `tests/vn/test_vn_pilot_routes.py`
(111 pytest cases). These smoke scripts complement that by verifying the
deployed gateway, not just the code.
