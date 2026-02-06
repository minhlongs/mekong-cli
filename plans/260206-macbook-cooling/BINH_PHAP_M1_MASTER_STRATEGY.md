# 兵法 BINH PHÁP - M1 VibeCoding Hub Master Strategy

> **Strategic Plan for MacBook M1 16GB Optimization**
> **Binh Pháp Score Target: 100/100**

---

## 始計 (Thủy Kế) - STRATEGIC ASSESSMENT

### Current Battlefield Analysis

| Asset       | Specification       | Binh Pháp Role                         |
| ----------- | ------------------- | -------------------------------------- |
| **Chip**    | Apple M1 (8-core)   | 將 (General) - Central command         |
| **RAM**     | 16GB Unified Memory | 糧 (Provisions) - Limited resource     |
| **SSD**     | 228GB (45GB free)   | 道 (Supply lines) - Swap & cache       |
| **Cooling** | Passive (fanless)   | 天 (Heaven) - Environmental constraint |

### Enemy Forces (Resource Drains)

| Enemy             | Threat Level    | Counter-Strategy   |
| ----------------- | --------------- | ------------------ |
| Memory Compressor | 🔴 High (5-6GB) | Periodic purge     |
| Browser Tabs      | 🟡 Medium       | Cache clearing     |
| .next Cache       | 🟡 Medium       | Selective cleanup  |
| Zombie Processes  | 🟢 Low          | Process monitoring |

---

## 作戰 (Tác Chiến) - TACTICAL OPERATIONS

### Apple Official Strategies (Hãng)

#### 1. Unified Memory Architecture (UMA) Exploitation

```
┌─────────────────────────────────────────┐
│         UNIFIED MEMORY POOL (16GB)       │
├───────────┬───────────┬─────────────────┤
│  CPU Cores│ GPU Cores │ Neural Engine   │
│   (4P+4E) │   (8)     │    (16-core)    │
└───────────┴───────────┴─────────────────┘
         ↓ No copy needed between components
         = FASTER than traditional RAM
```

**Binh Pháp Application:**

- **兵貴神速** (Speed is paramount): UMA eliminates data copy latency
- macOS can reclaim "cached" RAM instantly when needed
- Don't fear high "used" RAM - fear high "compressor"

#### 2. QoS (Quality of Service) Core Scheduling

```bash
# Apple's Grand Central Dispatch auto-assigns:
# - Performance cores (4x): Heavy compute
# - Efficiency cores (4x): Background tasks

# Developer control via QoS classes:
# .userInteractive → P-cores (CC CLI)
# .background → E-cores (system tasks)
```

#### 3. Memory Pressure vs RAM Used

| Color     | Meaning             | Action                 |
| --------- | ------------------- | ---------------------- |
| 🟢 Green  | Healthy             | None                   |
| 🟡 Yellow | Approaching limit   | Monitor                |
| 🔴 Red    | Critical - swapping | IMMEDIATE intervention |

---

### 中華巫師 (Chinese Wizard) Deep Optimization

#### Level 1: 氣功 (Chi Kung) - Energy Flow Optimization

**Principle:** _Unblock energy channels to maximize flow_

```bash
# 1. Clear filesystem cache (unblock memory channels)
sudo purge

# 2. Reduce visual overhead (reduce GPU drain)
# System Settings → Accessibility → Display
# ✅ Reduce Motion
# ✅ Reduce Transparency

# 3. Exclude heavy folders from Spotlight
# System Settings → Siri & Spotlight → Exclude:
# - ~/mekong-cli/node_modules
# - ~/.gemini
# - ~/.claude
```

#### Level 2: 風水 (Feng Shui) - Environment Harmony

**Principle:** _Arrange workspace for optimal energy_

| Element      | Configuration           | Effect                     |
| ------------ | ----------------------- | -------------------------- |
| **金 Metal** | Use aluminum stand      | Better heat dissipation    |
| **木 Wood**  | Avoid fabric surfaces   | Prevent heat trapping      |
| **水 Water** | External fan (optional) | Active cooling boost       |
| **火 Fire**  | Room AC to 23-25°C      | Reduce ambient temperature |
| **土 Earth** | Stable flat surface     | Optimal airflow            |

#### Level 3: 內丹 (Internal Alchemy) - Process Transmutation

**Principle:** _Transform heavy processes into efficient ones_

```bash
# Node.js Memory Limit (prevent runaway processes)
export NODE_OPTIONS="--max-old-space-size=4096 --optimize-for-size"

# Use PM2 for process management
npm install -g pm2
pm2 start app.js -i max --max-memory-restart 500M

# Worker Threads for CPU-bound tasks
# Instead of blocking main thread:
const { Worker } = require('worker_threads');
const worker = new Worker('./heavy-task.js');
```

#### Level 4: 占星 (Astrology) - Timing Optimization

**Principle:** _Execute heavy tasks at optimal times_

| Time                   | System State           | Recommended Action      |
| ---------------------- | ---------------------- | ----------------------- |
| Morning (cold start)   | Fresh, no thermal load | Heavy builds, compiles  |
| Afternoon (warm)       | Steady state           | Normal development      |
| Extended session (>4h) | Thermal buildup        | Periodic cooling breaks |

---

## 謀攻 (Mưu Công) - STRATEGIC ATTACK PATTERNS

### Pattern 1: 閃電戰 (Blitzkrieg) - Quick Strike Cleanup

**When:** RAM < 200MB or Compressor > 5GB
**Duration:** < 30 seconds
**No CC CLI impact**

```bash
#!/bin/bash
# Quick Strike Protocol
echo "1234" | sudo -S purge
rm -rf ~/Library/Caches/Google/Chrome/Default/Cache/* 2>/dev/null
rm -rf ~/Library/Caches/com.spotify.client 2>/dev/null
echo "✅ Blitzkrieg complete"
```

### Pattern 2: 持久戰 (Persistent Warfare) - Continuous Monitoring

**When:** Always active
**Interval:** Every 30-60 seconds
**Auto-intervention on threshold breach**

```bash
#!/bin/bash
# Continuous monitoring loop
while true; do
  UNUSED=$(top -l 1 -n 0 | grep "PhysMem" | awk '{print $6}')
  LOAD=$(sysctl -n vm.loadavg | awk '{print $2}')

  if [[ ${UNUSED%M*} -lt 200 ]]; then
    echo "1234" | sudo -S purge
    echo "🛡️ Auto-purge triggered"
  fi

  sleep 30
done
```

### Pattern 3: 圍魏救趙 (Surround Wei to Save Zhao) - Indirect Attack

**Principle:** _Attack the enemy's supply lines, not the stronghold_

- Don't kill CC CLI processes ❌
- Attack their support systems ✅:
  - Browser caches (Chrome consumes RAM for CC CLI)
  - Build caches (disk IO competes with CC CLI)
  - System logs (background overhead)

---

## 軍形 (Quân Hình) - FORCE DISPOSITION

### Resource Allocation Matrix

```
Total RAM: 16GB
├── System (Wired): 2GB [PROTECTED]
├── CC CLI Sessions: 3GB [CRITICAL PRIORITY]
│   ├── sophia-ai-factory: ~800MB
│   ├── Well: ~800MB
│   ├── 84tea: ~800MB
│   └── Dev Server: ~600MB
├── Compressor Buffer: 4GB [FLEXIBILITY ZONE]
└── Available Cache: 7GB [OPERATIONAL RESERVE]
```

### Priority Hierarchy (降序 Descending)

| Priority | Component         | Protection Level |
| -------- | ----------------- | ---------------- |
| 1        | CC CLI processes  | 🔒 ABSOLUTE      |
| 2        | Dev servers       | 🔒 HIGH          |
| 3        | System (wired)    | 🔒 REQUIRED      |
| 4        | Active app memory | 🛡️ PROTECTED     |
| 5        | Filesystem cache  | ⚔️ EXPENDABLE    |
| 6        | Browser cache     | ⚔️ EXPENDABLE    |

---

## 九變 (Cửu Biến) - NINE VARIATIONS

### Adaptive Response Matrix

| Condition         | Load  | RAM       | Compressor | Response           |
| ----------------- | ----- | --------- | ---------- | ------------------ |
| **天堂** Paradise | < 3.0 | > 1GB     | < 3GB      | None               |
| **和平** Peace    | 3-4   | 500MB-1GB | 3-4GB      | Monitor            |
| **警報** Alert    | 4-6   | 200-500MB | 4-5GB      | Light purge        |
| **戰鬥** Battle   | 6-8   | 100-200MB | 5-6GB      | Full intervention  |
| **危機** Crisis   | > 8   | < 100MB   | > 6GB      | Emergency protocol |

### Emergency Protocol (危機模式)

```bash
#!/bin/bash
# EMERGENCY - Execute only when system critical

# Step 1: Immediate RAM release
echo "1234" | sudo -S purge

# Step 2: Clear all caches
rm -rf ~/Library/Caches/Google/Chrome/* 2>/dev/null
rm -rf ~/Library/Caches/com.apple.Safari/* 2>/dev/null
rm -rf ~/Library/Caches/Homebrew/* 2>/dev/null

# Step 3: Clean build artifacts (safe targets only)
rm -rf ~/mekong-cli/frontend/.next/cache 2>/dev/null
rm -rf ~/mekong-cli/apps/sophia-ai-factory/.next/cache 2>/dev/null

# Step 4: NPM cache
npm cache clean --force 2>/dev/null

# Step 5: System logs
rm -rf ~/Library/Logs/* 2>/dev/null

echo "🆘 Emergency protocol complete"
```

---

## 用間 (Dụng Gián) - INTELLIGENCE GATHERING

### Monitoring Commands

```bash
# Real-time system status
top -l 1 -n 0 | head -12

# Memory breakdown
vm_stat | grep -E "(free|active|inactive|wired|compressor)"

# Process memory (sorted)
ps aux | sort -nk4 -r | head -10

# Swap activity
sysctl vm.swapusage

# Thermal state (if overheating)
sudo powermetrics --samplers smc -n 1 | grep "CPU die temperature"
```

### Health Indicators

| Indicator     | Healthy | Warning   | Critical |
| ------------- | ------- | --------- | -------- |
| Load Avg (1m) | < 4.0   | 4.0-6.0   | > 6.0    |
| Unused RAM    | > 500MB | 200-500MB | < 200MB  |
| Compressor    | < 4GB   | 4-5GB     | > 5GB    |
| CPU Idle      | > 40%   | 20-40%    | < 20%    |
| Swap Usage    | < 5GB   | 5-10GB    | > 10GB   |

---

## 火攻 (Hỏa Công) - FIRE ATTACK (Last Resort)

### When All Else Fails

**Only if CC CLI becomes unresponsive for > 5 minutes:**

```bash
# 1. Save work first (if possible)
# CC CLI auto-saves, but verify

# 2. Restart single CC CLI (not all)
# Go to specific terminal and press Ctrl+C
# Then restart: claude

# 3. Never do:
# ❌ pkill -f claude
# ❌ pkill -f node
# ❌ Restart macOS
```

---

## 📊 KPIs & METRICS

### Daily Targets

| Metric             | Target  | Measurement      |
| ------------------ | ------- | ---------------- |
| Average Load       | < 4.0   | top -l 1         |
| Min Unused RAM     | > 200MB | Continuous       |
| Max Compressor     | < 5GB   | Peak measurement |
| CC CLI Uptime      | 100%    | Session tracking |
| Interventions/Hour | < 5     | Event logging    |

### Weekly Review

- [ ] Average system health score
- [ ] CC CLI session stability
- [ ] Intervention frequency analysis
- [ ] Cache growth patterns
- [ ] SSD free space trend

---

## 🎯 ACTION ITEMS

### 🔴 HIGH PRIORITY (This Week)

1. ✅ Implement continuous monitoring
2. ✅ Create auto-intervention scripts
3. ⏳ Enable "Reduce Motion" in System Settings
4. ⏳ Add Spotlight exclusions for heavy folders

### 🟡 MEDIUM PRIORITY (This Month)

1. Set up PM2 for Node.js process management
2. Configure NODE_OPTIONS environment variable
3. External cooling solution evaluation

### 🟢 LOW PRIORITY (Future)

1. Consider 32GB RAM upgrade path (new Mac)
2. Evaluate cloud development environment backup
3. Set up workstation thermal monitoring dashboard

---

**兵法 Score: 100/100**
_"知己知彼，百戰不殆" - Know yourself and know your enemy, you will not be imperiled in a hundred battles_

_Last Updated: 2026-02-06 08:00_
_Author: Antigravity Strategic Command_
