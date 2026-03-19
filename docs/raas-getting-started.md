# Getting Started with RaaS — From Signup to First AI Task

**Robotics-as-a-Service (RaaS)** — AI automation platform that executes tasks as missions. Pay per outcome, not per hour.

---

## Table of Contents

1. [Quick Start (5 minutes)](#quick-start)
2. [Step 1: Create Your Account](#step-1-create-your-account)
3. [Step 2: Get Your API Key](#step-2-get-your-api-key)
4. [Step 3: Install the SDK](#step-3-install-the-sdk)
5. [Step 4: Submit Your First Mission](#step-4-submit-your-first-mission)
6. [Step 5: Monitor & Retrieve Results](#step-5-monitor--retrieve-results)
7. [Next Steps](#next-steps)

---

## Quick Start

```bash
# 1. Install the SDK
pip install mekong-cli

# 2. Set your API key
export MEKONG_API_KEY="mk_your_api_key_here"

# 3. Run your first mission
python -c "
from src.raas.sdk import MekongClient
client = MekongClient(base_url='https://api.mekong-cli.io', api_key='$MEKONG_API_KEY')
mission = client.create_mission('Generate Q1 revenue report as CSV')
print(f'Mission ID: {mission.id} | Status: {mission.status}')
"
```

---

## Step 1: Create Your Account

### Option A: Web Dashboard (Recommended)

1. Visit [agencyos.network](https://agencyos.network)
2. Click **Sign Up** in the top right
3. Enter your email and create a password
4. Verify your email address

### Option B: CLI Registration

```bash
# Install mekong-cli
pip install mekong-cli

# Create your first tenant (organization)
mekong tenant:create "My Company"
```

Output:
```
✓ Tenant created: "My Company"
  Tenant ID: 550e8400-e29b-41d4-a716-446655440000
  API Key: mk_a1b2c3d4e5f6...

  ⚠️ Save your API key — it won't be shown again!
```

---

## Step 2: Get Your API Key

### From Web Dashboard

1. Log in to [agencyos.network/dashboard](https://agencyos.network/dashboard)
2. Navigate to **Settings → API Keys**
3. Click **Generate New Key**
4. Copy the key (starts with `mk_`)

### From CLI

If you used CLI registration, your API key was displayed during tenant creation.

To list existing keys:

```bash
mekong tenant:list
```

---

## Step 3: Install the SDK

### Python SDK

```bash
# From PyPI (recommended)
pip install mekong-cli

# Or from source
git clone https://github.com/mekong-ai/mekong-cli
cd mekong-cli && pip install -e .
```

### Verify Installation

```bash
python -c "from src.raas.sdk import MekongClient; print('SDK ready!')"
```

---

## Step 4: Submit Your First Mission

### What is a Mission?

A **Mission** is an AI-executed task. Examples:
- "Generate Q1 revenue report as CSV"
- "Deploy frontend to Cloudflare Pages"
- "Fix all TypeScript errors in src/"
- "Create user authentication with OAuth2"

### Basic Mission Submission

```python
from src.raas.sdk import MekongClient

# Initialize client
client = MekongClient(
    base_url="https://api.mekong-cli.io",  # Production
    # base_url="http://localhost:8000",   # Local dev
    api_key="mk_your_api_key_here",
)

# Create a mission
mission = client.create_mission(
    goal="Generate Q1 revenue report as CSV",
    # Optional: specify complexity
    # complexity="simple"    # < 50 chars (1 credit)
    # complexity="standard"  # 50-149 chars (3 credits)
    # complexity="complex"   # ≥ 150 chars (5 credits)
)

print(f"Mission ID: {mission.id}")
print(f"Status: {mission.status}")        # queued | running | completed | failed
print(f"Credits Cost: {mission.credits_cost}")
```

### Mission Complexity & Credits

| Complexity | Goal Length | Credits | Example |
|------------|-------------|---------|---------|
| `simple` | < 50 chars | 1 | "Fix typo in README" |
| `standard` | 50-149 chars | 3 | "Add user login with email/password" |
| `complex` | ≥ 150 chars | 5 | "Build complete authentication system with OAuth2, JWT tokens, session management, and password reset flow" |

**Note:** Complexity is auto-detected from goal length if not specified.

---

## Step 5: Monitor & Retrieve Results

### Check Mission Status

```python
# Poll status
status = client.get_mission(mission.id)
print(f"Status: {status.status}")
print(f"Progress: {status.started_at} → {status.completed_at}")

if status.error_message:
    print(f"Error: {status.error_message}")
```

### Stream Real-Time Updates (SSE)

```python
# Subscribe to real-time events
print("Listening for mission events...")
for event in client.stream_dashboard():
    print(f"Event: {event}")
    # Example: {'type': 'mission.status', 'status': 'completed'}
```

### Retrieve Execution Logs

```python
# Get full execution logs
logs = client.get_logs(mission.id)
print(logs)
# Output:
# Step 1: Planning...
# Step 2: Executing...
# Step 3: Testing...
# Step 4: Verifying...
```

### List All Missions

```python
# List recent missions
missions = client.list_missions(limit=10)
for m in missions:
    print(f"{m.id[:8]}... | {m.status} | {m.goal[:50]}")
```

### Cancel a Queued Mission

```python
# Cancel and refund credits (only works for queued missions)
cancelled = client.cancel_mission(mission.id)
print(f"Mission {cancelled.id} cancelled. Credits refunded.")
```

---

## Complete Example: End-to-End Workflow

```python
#!/usr/bin/env python3
"""
Complete RaaS workflow: Submit → Monitor → Retrieve Results
"""
import time
from src.raas.sdk import MekongClient

# Initialize
client = MekongClient(
    base_url="https://api.mekong-cli.io",
    api_key="mk_your_api_key_here",
)

# Submit mission
print("=== Submitting Mission ===")
mission = client.create_mission("Generate Q1 revenue report as CSV")
print(f"Mission ID: {mission.id}")
print(f"Status: {mission.status}")
print(f"Credits: {mission.credits_cost}")

# Poll until completion
print("\n=== Waiting for Completion ===")
while mission.status not in ["completed", "failed", "cancelled"]:
    time.sleep(5)
    mission = client.get_mission(mission.id)
    print(f"Status: {mission.status}...")

# Handle results
if mission.status == "completed":
    print("\n=== Mission Completed! ===")
    logs = client.get_logs(mission.id)
    print(f"Logs:\n{logs}")
elif mission.status == "failed":
    print(f"\n=== Mission Failed ===")
    print(f"Error: {mission.error_message}")
else:
    print(f"\n=== Mission {mission.status} ===")
```

---

## Dashboard Overview

Access your dashboard at [agencyos.network/dashboard](https://agencyos.network/dashboard)

### Dashboard Features

- **Mission List**: View all missions with status filters
- **Credit Balance**: Track earned/spent credits
- **Real-Time Stream**: Live mission execution updates
- **Cost Analytics**: Credit breakdown by complexity
- **API Keys**: Manage and rotate keys
- **Usage History**: Export mission logs as CSV

---

## Billing & Credits

### Credit Packs

| Product | Credits | Price |
|---------|---------|-------|
| Starter | 10 | $5 (one-time) |
| Growth | 50 | $20 (one-time) |
| Pro | 100 | $35 (one-time) |

### Subscription Plans

| Plan | Credits/Month | Price |
|------|---------------|-------|
| Starter | 50 | $29/mo |
| Growth | 200 | $99/mo |
| Pro | 500 | $199/mo |
| Enterprise | 2000 | $599/mo |

### Add Credits via Polar.sh

1. Visit [agencyos.network/billing](https://agencyos.network/billing)
2. Select a credit pack or subscription
3. Complete checkout with Polar.sh
4. Credits auto-added to your account

---

## Troubleshooting

### Error: 401 Unauthorized

**Cause:** Invalid or missing API key

**Fix:**
```python
# Ensure API key starts with "mk_"
client = MekongClient(api_key="mk_...")

# Check environment variable
export MEKONG_API_KEY="mk_your_key"
```

### Error: 402 Payment Required

**Cause:** Insufficient credits

**Fix:**
1. Visit dashboard → Billing
2. Purchase credit pack or subscription
3. Retry mission

### Error: 403 Forbidden

**Cause:** Tenant account deactivated

**Fix:** Contact support at support@mekong-cli.io

### Mission Stuck in "Queued"

**Cause:** High platform load

**Fix:**
- Wait 1-2 minutes for daemon pickup
- Check dashboard for system status
- Cancel and resubmit if stuck > 5 minutes

---

## Next Steps

### After Your First Mission

- **Explore Recipes**: Pre-built automation templates in `/recipes`
- **Advanced SDK**: SSE streaming, error handling, batch operations
- **Custom Agents**: Build specialized agents for your domain
- **Team Collaboration**: Multi-tenant workspaces

### Documentation

- [RaaS API Reference](./raas-api.md) — Full endpoint documentation
- [RaaS SDK Guide](./raas-sdk-guide.md) — SDK patterns and examples
- [RaaS Billing Setup](./raas-billing-setup.md) — Polar.sh integration
- [RaaS Deployment Guide](./raas-deployment-guide.md) — Self-hosting

### Community

- **GitHub**: [github.com/mekong-ai/mekong-cli](https://github.com/mekong-ai/mekong-cli)
- **Discord**: [mekong-cli.io/discord](https://mekong-cli.io/discord)
- **Support**: support@mekong-cli.io

---

© 2026 Binh Phap Venture Studio. *"The supreme art of war is to subdue the enemy without fighting."*
