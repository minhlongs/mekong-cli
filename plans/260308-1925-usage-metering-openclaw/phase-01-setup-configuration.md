---
phase: 1
title: "Setup & Configuration"
status: pending
effort: 1h
---

# Phase 1: Setup & Configuration

## Overview

Configure environment variables and KV namespace bindings for both OpenClaw Worker and RaaS Gateway.

## Key Insights

- RaaS Gateway already has KV namespaces defined but with placeholder IDs
- OpenClaw Worker needs new env vars for RaaS Gateway integration
- KV namespaces must be created via Wrangler CLI before deployment

## Requirements

### Functional
1. Create KV namespaces: `RAAS_USAGE_KV`, `SUSPENSION_CACHE`
2. Update wrangler.toml files with correct KV IDs
3. Configure environment variables for OpenClaw → RaaS communication

### Non-Functional
1. No secrets in code — use wrangler secrets or .dev.vars
2. Consistent KV key naming across environments

## Related Code Files

### Files to Modify
- `apps/raas-gateway/wrangler.toml` — Update KV namespace IDs
- `apps/openclaw-worker/wrangler.jsonc` — Add RaaS Gateway bindings
- `apps/openclaw-worker/src/index.ts` — Add env var types

### Files to Create
- `apps/openclaw-worker/.dev.vars` — Local dev env vars (if not exists)

## Implementation Steps

### Step 1: Create KV Namespaces

```bash
# Navigate to RaaS Gateway
cd apps/raas-gateway

# Create RAAS_USAGE_KV (if not exists)
wrangler kv:namespace create "RAAS_USAGE_KV"
# Output: id = "xxx" — copy this

# Create SUSPENSION_CACHE (if not exists)
wrangler kv:namespace create "SUSPENSION_CACHE"
# Output: id = "yyy" — copy this
```

### Step 2: Update RaaS Gateway wrangler.toml

Replace placeholder IDs with actual IDs from Step 1:

```toml
[[kv_namespaces]]
binding = "RAAS_USAGE_KV"
id = "actual_id_from_step_1"
preview_id = "actual_id_from_step_1"

[[kv_namespaces]]
binding = "SUSPENSION_CACHE"
id = "actual_id_from_step_2"
preview_id = "actual_id_from_step_2"
```

### Step 3: Configure OpenClaw Worker Env Vars

Add to `apps/openclaw-worker/.dev.vars`:

```
RAAS_GATEWAY_URL=http://localhost:8787
RAAS_SERVICE_TOKEN=mk_local_dev_token
```

Add to `apps/openclaw-worker/wrangler.jsonc` vars section:

```json
{
  "vars": {
    "RAAS_GATEWAY_URL": "https://raas.agencyos.network",
    "USE_RAAS_METERING": "true"
  }
}
```

### Step 4: Configure RaaS Gateway Secrets

```bash
cd apps/raas-gateway

# Set SERVICE_TOKEN (if not exists)
wrangler secret put SERVICE_TOKEN
# Enter: mk_your_service_token_here

# Set MK_API_KEYS (format: "mk_key1:tenant1:pro,mk_key2:tenant2:free")
wrangler secret put MK_API_KEYS
# Enter: mk_abc123:tenant1:pro,mk_xyz789:tenant2:free
```

## Success Criteria

- [ ] KV namespaces created with valid IDs
- [ ] wrangler.toml files updated with correct IDs
- [ ] Local dev env vars configured
- [ ] Secrets set in Cloudflare Workers dashboard
- [ ] `wrangler dev` starts without KV errors

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| KV namespace ID typo | High — runtime errors | Copy/paste IDs directly from wrangler output |
| Secrets not propagated | Medium — auth failures | Wait 30s after `wrangler secret put`, verify in dashboard |
| Local dev vs prod mismatch | Medium — works locally, fails in prod | Use same KV namespace structure in both environments |

## Security Considerations

- **mk_ API keys**: Store in `MK_API_KEYS` secret, never in code
- **SERVICE_TOKEN**: Use `wrangler secret put`, not plain text
- **KV access**: Ensure proper Cloudflare account permissions

## Next Steps

After setup complete, proceed to [Phase 2: OpenClaw Worker Integration](./phase-02-openclaw-integration.md)
