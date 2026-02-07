# OpenClaw Orchestration Plan: Company-Wide Command

> **Date:** 2026-02-07
> **Objective:** Activate "Hybrid Commander" mode to orchestrate the entire company via OpenClaw (Cloudflare) and Mekong CLI (Local).

## 1. The Architecture: "Hybrid Commander"

The system uses a **Cloud-to-Local Bridge** architecture (The "Giao Việc" Wiring).

- **Cloud Brain (OpenClaw):** `raas.agencyos.network` (Cloudflare Worker). Receives commands (Telegram, Webhooks).
- **Secure Tunnel:** Cloudflare Argo Tunnel (Cloudflared).
- **Local Bridge:** `openclaw-service.sh` running `bridge-server.js` + `task-watcher.js`.
- **Execution Engine:** Mekong CLI (T1) acting as the "Supreme Commander" listening to the Local Bridge.

## 2. Activation Protocol

### Step A: Verify & Start Local Bridge (T1)

The Supreme Commander (T1) must ensure the local bridge is running.

```bash
# Check if running
ps aux | grep openclaw

# If not, start it
cd apps/openclaw-worker
./openclaw-service.sh
```

### Step B: Verify Cloud Connection

1. `openclaw-service.sh` automatically updates the `BRIDGE_URL` secret in `raas-gateway` via `wrangler`.
2. Verify via Telegram Bot: "🌉 OpenClaw Bridge Online!"

### Step C: Command Loop (The "Giao việc" Protocol)

1. **User Action:** Send command to OpenClaw (Telegram).
   - `/cmd mekong Deploy all apps`
2. **Routing (The "Wiring"):**
   - Telegram Webhook -> `https://raas.agencyos.network/telegram`
   - **`raas-gateway` (Worker):**
     - Intercepts `/telegram` POST.
     - Verifies Secret Token.
     - Extracts message text.
     - Forwards to `${env.OPENCLAW_URL}/task` using the `BRIDGE_URL` (Tunnel).
3. **Local Bridge:** Receives `/task`, writes to file (`/tmp/openclaw_task_*.txt`).
4. **Task Watcher:** Executes via `claude` or Shell.

## 3. Implementation Plan

1. **T1 Action:** Inspect `apps/openclaw-worker` health (DONE).
2. **T1 Action:** Start `openclaw-service.sh` (DONE).
3. **Validation:** Local Execution Verified (`/tmp/openclaw_bridge_verified.txt`).
4. **Gateway Upgrade:**
   - Modify `apps/raas-gateway/index.js` to handle `/telegram`.
   - Deploy `raas-gateway`.
   - Set Telegram Webhook.
5. **Verification:** Send `/cmd test` in Telegram.

## 4. User Instruction

To command the entire company:

1. Use **OpenClaw Telegram Bot**.
2. Format: `/cmd [target] [instruction]`
   - e.g. `/cmd mekong Deploy all apps`

3. **Using Skills:**
   - **GitHub:** `/cmd mekong Create PR for feature X`
   - **Vercel:** `/cmd mekong Deploy staging environment`
   - **Optimization:** `/cmd mekong Analyze database performance`

## 5. Skills Reference

- `github-cli`: Manage repos, issues, PRs.
- `vercel-cli`: Deploy, manage env vars.
- `senior-backend`: Database optimization.
- `vpn-rotate-skill`: Network resilience.
