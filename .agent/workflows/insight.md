---
description: Tôm Hùm Brain Surgery — Self-evolution protocol. Forces CTO agent to introspect, critique, and evolve its own source code.
---

# /insight — BRAIN SURGERY SELF-EVOLUTION

> 📜 Binh Pháp Ch.3 謀攻: 「知己知彼，百戰不殆」— Biết mình biết người, trăm trận không nguy

## KEY: CC CLI has `/insights` built-in command!
- `/insights` → Tổng hợp workflow history, patterns, mọi thứ đã làm
- Tôm Hùm PHẢI dùng `/insights` TRƯỚC KHI tự phê bình
- Ánh xạ Antigravity artifacts để sync context across sessions

## Workflow Steps

### Step 1: Dispatch Brain Surgery Mission to CC CLI

// turbo
Run the following command to dispatch the self-evolution mission:

```bash
rm -f /Users/macbookprom1/mekong-cli/apps/openclaw-worker/.mission-active.lock
cat > /Users/macbookprom1/mekong-cli/tasks/CRITICAL_brain_surgery.txt << 'BRAIN_SURGERY'
[MISSION: BRAIN_SURGERY — 自知之明]
Working Dir: /Users/macbookprom1/mekong-cli/apps/openclaw-worker

STEP 1: INTROSPECTION (Soi gương — 知己)
- Read ALL files in 'lib/' directory (brain-tmux.js, mission-dispatcher.js, task-queue.js, etc.)
- Read config.js, ecosystem.config.js
- Read BINH_PHAP_MASTER.md, DOANH_TRAI.md, QUAN_LUAT.md, AGI_EVOLUTION.md
- Analyze your own System Prompts and Decision Algorithms
- Map current capabilities vs ideal capabilities

STEP 2: CRITIQUE (Tự phê bình — 知彼)
- Find 3-5 CONCRETE weaknesses in current logic:
  * Token efficiency? Wasted API calls?
  * Memory/context management? Do you forget lessons?
  * Error handling? Silent failures?
  * Decision quality? Wrong model/complexity routing?
  * Mission success rate? What fails most?
- Ask: 'Is this code worthy of a $1M RaaS Empire?'
- Score each weakness: SEVERITY (1-10) × FIXABILITY (1-10)

STEP 3: EVOLUTION (Tiến hóa — 善之善者)
- Pick TOP 3 weaknesses by score (highest = fix first)
- For each: implement CONCRETE code fix (not just plan)
- Focus on:
  * 🧠 Chain-of-Thought: Better prompt templates in mission dispatch
  * 🔄 Self-Correction: Auto-detect + fix common failures
  * 💾 Memory: Persist lessons across sessions (wins.jsonl, lessons.md)
  * ⚡ Speed: Reduce unnecessary API calls, smarter routing

STEP 4: COMMIT + CHANGELOG
- Apply changes to actual files
- Create/update: knowledge/brain-surgery-changelog.md with:
  * Date, BEFORE state, AFTER state, reasoning
  * Improvement metrics (expected impact)
- Git commit with message: "🧬 BRAIN SURGERY: [summary of evolution]"

OUTPUT FORMAT:
```
## 🧬 BRAIN SURGERY REPORT
### BEFORE (Weaknesses Found)
1. [weakness] — Score: X/100
2. [weakness] — Score: X/100
3. [weakness] — Score: X/100

### AFTER (Fixes Applied)
1. [fix description] — File: [path]
2. [fix description] — File: [path]
3. [fix description] — File: [path]

### EVOLUTION METRICS
- Expected improvement: [%]
- Files changed: [N]
- Lines modified: [N]
```
BRAIN_SURGERY
```

### Step 2: Clear mission lock if stuck

// turbo
```bash
rm -f /Users/macbookprom1/mekong-cli/apps/openclaw-worker/.mission-active.lock
```

### Step 3: Monitor mission progress

Wait 60 seconds then check CTO log and CC CLI pane:

// turbo
```bash
sleep 60 && echo "=== CTO ===" && tail -n 10 /Users/macbookprom1/tom_hum_cto.log && echo "=== CC CLI ===" && tmux capture-pane -t tom_hum_brain:0.0 -p -S -15 | col -b | tail -n 15
```

### Step 4: Verify evolution results

After mission completes, check the changelog:

// turbo
```bash
cat /Users/macbookprom1/mekong-cli/apps/openclaw-worker/knowledge/brain-surgery-changelog.md 2>/dev/null || echo "No changelog yet"
git -C /Users/macbookprom1/mekong-cli log --oneline -3
```

## Notes

- Mission priority: CRITICAL (processed before HIGH/MEDIUM)
- Expected duration: 45-60 min (🔥 LỬA mode — Complex)
- This is a SELF-MODIFYING mission — Tôm Hùm rewrites its own code
- Safety: post-mission-gate.js will block if >15 files changed or >500 lines deleted
