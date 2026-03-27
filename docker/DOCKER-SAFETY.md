# Docker Desktop Safety — Mekong CLI + CashClaw

## CRITICAL: Two containers, one Docker engine

This M1 Max runs two containerized systems:
- `mekong-dev` — AI development workstation (this)
- `cashclaw-bot` — Polymarket market-making bot with REAL MONEY positions

Both share:
- Docker Desktop engine (restart kills both)
- LLM servers on host (:11435 DeepSeek R1, :11436 Nemotron Nano)
- Metal GPU (indirect, via LLM API calls)

## Step 1: Disable Docker Desktop Auto-Update

Docker Desktop → Settings → Software Updates → UNCHECK all auto-update options.

WHY: Auto-update restarts Docker engine → kills cashclaw-bot mid-trade → GTC orders stay on Polymarket book → stale orders fill at adverse prices → loss of real money.

## Step 2: Pin Docker Desktop Version

Current: Docker Desktop 4.38+ (verify with `docker version`)
Do NOT upgrade unless:
1. `docker compose -f algo-trader/docker/docker-compose.yaml down` (CashClaw FIRST)
2. Verify ALL Polymarket orders cancelled manually
3. `docker compose -f docker/docker-compose.yaml down` (Mekong second)
4. Upgrade Docker Desktop
5. Restart CashClaw first, then Mekong

## Step 3: Startup Order

Always start in this order:
1. LLM servers (already running as bare-metal processes)
2. CashClaw container (trading bot — needs LLM for fair value)
3. Mekong container (dev workstation — can wait)

Always stop in reverse:
1. Mekong container (safe to kill anytime)
2. CashClaw container (needs 30s grace period for order cancellation)
3. LLM servers (only if shutting down machine)

## Step 4: Alternative — Colima

Replace Docker Desktop entirely to eliminate auto-update risk:
```bash
brew install colima docker docker-compose
colima start --cpu 4 --memory 4 --disk 60 --arch aarch64
# Everything else works the same
```

## Port Map

| Port  | Service        | Container    |
|-------|----------------|--------------|
| 3001  | CloudCLI UI    | mekong-dev   |
| 8000  | Mekong Gateway | mekong-dev   |
| 11435 | DeepSeek R1    | bare metal   |
| 11436 | Nemotron Nano  | bare metal   |
| —     | CashClaw bot   | cashclaw-bot (no exposed ports) |

## LLM Contention

Both containers call the same two MLX servers. mlx_lm.server serializes requests per-model.

Low-risk scenario (99% of the time):
- CashClaw calls Nemotron every 5 min for fair value (~1s each)
- Mekong calls DeepSeek when you run `mekong cook` (different model, no conflict)

Edge case (<1%):
- Mekong PEV planning uses DeepSeek + CashClaw deep analysis uses DeepSeek simultaneously
- Second request queues behind first (~30-60s wait)
- CashClaw has 90s timeout, will retry — NOT a crash

## Recovery Checklist

If Docker crashes or restarts unexpectedly:
1. Check CashClaw logs: `docker logs cashclaw-bot --tail 50`
2. CashClaw auto-cancels all open orders on startup (crash recovery)
3. Manually verify Polymarket positions at polymarket.com
4. Check LLM servers still running: `curl http://localhost:11435/v1/models`
5. Restart containers: CashClaw first, Mekong second
