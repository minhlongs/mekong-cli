# AgencyOS ↔ mekong-cli Integration

AgencyOS is the cloud dashboard that dispatches missions to mekong-cli running on the founder's machine.

## How It Works

```
AgencyOS Dashboard (cloud)
  → POST /v1/missions  (mekong-cli API Gateway, port 8000)
  → PEV Engine runs task
  → Result streamed back via WebSocket
  → MCU deducted on success
```

## Prerequisites

1. mekong-cli installed and running: `mekong status`
2. LLM provider configured via `LLM_BASE_URL` environment variable
3. Environment variables set (see below)

## Environment Setup

Copy `.env.example` to `.env` at project root and fill in:

```bash
# LLM Provider (any OpenAI-compatible endpoint)
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-v1-yourkey
LLM_MODEL=anthropic/claude-sonnet-4

# Supabase (database)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Polar.sh (billing)
POLAR_ACCESS_TOKEN=your-polar-token
POLAR_WEBHOOK_SECRET=your-webhook-secret
POLAR_ORGANIZATION_ID=your-org-id

# RaaS licensing
RAAS_LICENSE_KEY=your-license-key

# AgencyOS API
AGENCYOS_API_URL=https://api.agencyos.network
AGENCYOS_API_KEY=your-api-key
```

## Starting the API Gateway

```bash
# Start local gateway (port 8000)
mekong status          # verify system health
python -m src.api.main # start FastAPI gateway

# Or via mekong CLI
mekong deploy --local
```

## MCU Credit Flow

1. Founder purchases plan on AgencyOS (Polar.sh checkout)
2. Polar webhook → `POST /billing/polar` → credits added to account
3. Each mission deducts MCU based on complexity (see `pricing.json`)
4. Balance < 10 MCU → low balance warning
5. Balance = 0 → HTTP 402, mission rejected

## Agent Configuration

8 available agents defined in `agents.json`. Activate via:
```bash
mekong company/agent list
mekong company/agent enable <agent-name>
```

## Troubleshooting

- **LLM not responding**: verify `LLM_BASE_URL` is reachable with `curl $LLM_BASE_URL/models`
- **402 errors**: check MCU balance with `mekong company/billing`
- **Mission stuck**: check `~/tom_hum_cto.log`
