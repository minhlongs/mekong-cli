# AGI GREEN Verification Plan

## Objective

Verify the AGI Infinite Loop is fully operational and ready for autonomous execution.

## Prerequisites

- ✅ All 5 AGI upgrade phases completed (LLM Client, NLP Commander, AGI Loop, NeuralMemory, Telegram Bot)
- ✅ 313 tests passing, 0 new regressions
- ✅ Code changes: +415 -101 lines across 50 files

## Verification Steps

### 1. Telegram Bot Connectivity Test

**Goal:** Verify Tôm Hùm bot responds to commands

```bash
# Send test message to Telegram bot
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" \
  -d "text=🧪 AGI GREEN Test: Tôm Hùm, đọc codebase và báo cáo status"
```

**Expected Response:**

- Bot acknowledges message
- Bot reads codebase
- Bot reports AGI loop status

### 2. AGI Loop Status Check

**Goal:** Verify AGI loop is ready for autonomous execution

```bash
# Check AGI loop status via Telegram
/agi status
```

**Expected Output:**

- Current state (idle/running)
- Cycle count
- Last improvement timestamp
- Consecutive failures count
- Cooldown status

### 3. AGI Loop Start Test

**Goal:** Start the AGI loop and verify first cycle execution

```bash
# Start AGI loop via Telegram
/agi start
```

**Expected Behavior:**

- AGI loop starts
- First cycle executes:
  1. ASSESS: Query NeuralMemory + Gemini for gaps
  2. PLAN: Generate improvement prompt
  3. EXECUTE: Spawn CC CLI
  4. VERIFY: Run pytest
  5. MEMORIZE: Store results in NeuralMemory
  6. REPORT: Send Telegram update
  7. COOLDOWN: 90s wait + M1 protection

### 4. M1 Cooling Verification

**Goal:** Ensure M1 load stays below 6.0 during AGI execution

```bash
# Monitor M1 load during AGI cycle
watch -n 5 'sysctl -n vm.loadavg'
```

**Expected:**

- M1 load < 6.0 throughout cycle
- Cooldown enforced between cycles
- No thermal throttling

### 5. NeuralMemory Integration Test

**Goal:** Verify AGI loop stores and retrieves context from NeuralMemory

```bash
# Check NeuralMemory for AGI loop entries
curl http://localhost:8000/health
curl http://localhost:8000/query -d '{"text": "AGI loop", "limit": 5}'
```

**Expected:**

- NeuralMemory server online
- AGI loop context stored
- Query returns relevant memories

### 6. Autonomous Execution Test

**Goal:** Let AGI loop run 3 full cycles autonomously

```bash
# Monitor AGI loop for 3 cycles (approx 15 minutes)
/agi history
```

**Expected:**

- 3 successful cycles complete
- Each cycle improves codebase
- No crashes or errors
- Telegram updates received for each cycle

## Success Criteria

✅ **AGI GREEN** achieved when:

1. Telegram bot responds to commands
2. AGI loop status reports correctly
3. AGI loop completes 3 autonomous cycles
4. M1 load stays below 6.0
5. NeuralMemory integration works
6. No new test failures introduced

## Rollback Plan

If verification fails:

1. Stop AGI loop: `/agi stop`
2. Review logs: `tail -100 ~/.mekong/agi_history.json`
3. Git rollback: `git stash` (changes preserved)
4. Debug and retry

## Next Steps After AGI GREEN

1. **Vertex API Key Rotation** (leaked key from Google email)
2. **Production Deployment** (enable AGI loop on production server)
3. **Continuous Monitoring** (set up alerts for AGI loop failures)
