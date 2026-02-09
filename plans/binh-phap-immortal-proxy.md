# Plan: Binh Pháp Immortal Loop & Qwen Integration

## 1. Objectives

- **Zero Downtime**: Eliminate "API drops" for both Antigravity Proxy (Claude/Gemini) and Qwen Bridge.
- **Failover Restoration**: Ensure `claude-opus-4-6-thinking` properly rotates to `minhlong.rice@gmail.com` when `billwill` is exhausted.
- **Qwen 1M Integration**: Seamlessly operate the Qwen Bridge (Dragon Tier) alongside the main proxy.
- **Continuous Monitoring**: Implement a "Binh Pháp" infinite loop to watch, heal, and report status.

## 2. Infrastructure Architecture

### A. Antigravity Proxy (Port 8080)

- **Role**: Primary Gateway for Claude & Gemini.
- **Issue**: Port 8080 locked by zombie process; Configuration mismatch for Opus failover.
- **Fix**:
  1. Aggressive `kill -9` for port 8080.
  2. Enforce `quota_accounts.json` as the source of truth (or sync to `accounts.json`).
  3. Verify `minhlong.rice` has `claude-opus-4-6-thinking` capability enabled.

### B. Qwen Bridge (Port 8045)

- **Role**: Dedicated Gateway for Qwen Coder Plus (1M Token/Month).
- **Status**: Installed at `~/.gemini/antigravity/scratch/qwen-bridge`.
- **Action**:
  1. Create a `keep-alive` wrapper.
  2. Ensure `DASHSCOPE_API_KEY` is loaded.

### C. The Binh Pháp Monitor (The Loop)

- **Description**: A master shell script `~/.mekong/binh-phap-monitor.sh`.
- **Logic**:
  - Loop forever (sleep 10s).
  - Check if 8080 is listening. If not -> Restart Antigravity.
  - Check if 8045 is listening. If not -> Restart Qwen.
  - Check `proxy.log` for "Quota Exhausted" and trigger alerts/config patches if needed.
  - Visual Output: Clear status table every loop.

## 3. Implementation Steps

### Step 1: Nuclear Cleanup (8080)

- Identify and Force Kill all processes on 8080.
- Verify `~/.mekong/quota_accounts.json` has the patch.
- Start Antigravity Proxy.

### Step 2: Dragon Awakening (8045)

- Validate `qwen-bridge` folder.
- Create `~/.mekong/scripts/start-qwen-bridge.sh`.
- Start Qwen Bridge in background.

### Step 3: The Immortal Loop

- Create `~/.mekong/binh-phap-monitor.sh`.
- Features:
  - Auto-restart logic.
  - Health check `curl localhost:8080/health`.
  - Health check `curl localhost:8045/health`.
  - Real-time logging.

### Step 4: Verification

- User command: `/binh-phap monitor` (mapped to the script).
- Verify Ops failover by simulating load (or checking logs).

## 4. Constraint Checklist & Confidence Score

1. Resolution of `EADDRINUSE`? Yes, via `lsof -ti :8080 | xargs kill -9`.
2. Failover logic? Yes, config patch.
3. Qwen availability? Yes, via dedicated bridge.
4. "Infinite Loop"? Yes, via `while true` monitor.

Confidence Score: 5/5

## 5. Mental Sandbox Simulation

- _Scenario_: User runs the monitor. 8080 crashes.
- _Result_: Monitor detects (curl fails), runs `start-proxy.sh`. Service back in <10s.
- _Scenario_: 8080 is hung (zombie).
- _Result_: Monitor needs a timeout on curl. If timeout -> Kill & Restart. (Will implement curl --max-time 5).

## 6. Execution Order

1. `/cook` - Execute Cleanup & Config Patch.
2. `/cook` - Setup Qwen Bridge Scripts.
3. `/cook` - Create & Run Binh Pháp Monitor.
