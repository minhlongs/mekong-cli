# 🚀 M1 VibeCoding Hub Optimization Protocol

> **Mục tiêu:** Biến MacBook M1 16GB thành trung tâm VibeCoding chạy nhiều CC CLI song song

## 📊 RESOURCE ALLOCATION FOR CC CLI

### Minimum RAM per CC CLI Session

| Component             | RAM Est.       | Notes                   |
| --------------------- | -------------- | ----------------------- |
| Claude CLI process    | ~200-400MB     | Node.js + IPC           |
| Antigravity Proxy     | ~100-200MB     | Model routing           |
| Context cache         | ~100-300MB     | Depends on conversation |
| **Total per session** | **~400-900MB** |                         |

### Current Setup (4 Sessions + Dev Server)

| Process             | Est. RAM   | Priority    |
| ------------------- | ---------- | ----------- |
| CC CLI x3           | ~1.5-2.5GB | 🔒 CRITICAL |
| Dev Server (84tea)  | ~300-500MB | 🔒 CRITICAL |
| System (macOS)      | ~2GB wired | Required    |
| Available for cache | ~10-11GB   | Flexible    |

---

## 🛠 M1 OPTIMIZATION TECHNIQUES (2025 Best Practices)

### 1. Node.js Memory Optimization

```bash
# Limit Node.js heap to prevent runaway memory
export NODE_OPTIONS="--max-old-space-size=4096"

# Enable better garbage collection for long-running processes
export NODE_OPTIONS="$NODE_OPTIONS --optimize-for-size"
```

### 2. Native ARM Priority

- ✅ Ensure VS Code/Cursor runs as Apple Silicon native
- ✅ Ensure all brew packages are ARM64
- ✅ Avoid Rosetta 2 emulation when possible

### 3. Aggressive Cache Management

```bash
# Scheduled cleanup every 30 min (can be cron)
# Clean .next cache for non-running projects
find ~/mekong-cli -path "*/.next/cache" -type d ! -path "*84tea*" -exec rm -rf {} + 2>/dev/null

# Clean npm cache weekly
npm cache clean --force

# Purge filesystem cache when RAM < 300MB
sudo purge
```

### 4. Process Priority (nice values)

```bash
# Give CC CLI higher priority (lower nice = higher priority)
# Find claude processes and renice them
pgrep -f "claude" | xargs sudo renice -5 2>/dev/null
```

### 5. Swap Optimization

- macOS handles swap automatically on M1
- Monitor swapins/swapouts - high numbers = RAM pressure
- Current: ~2.8M swapins (acceptable for long sessions)

---

## 📈 VIBECODING HUB THRESHOLDS

### Green Zone (Optimal for 4 CC CLI)

| Metric     | Target  | Action |
| ---------- | ------- | ------ |
| Load Avg   | < 4.0   | None   |
| Unused RAM | > 500MB | None   |
| Compressor | < 4GB   | None   |
| CPU Idle   | > 40%   | None   |

### Yellow Zone (Monitor Closely)

| Metric     | Range     | Action                 |
| ---------- | --------- | ---------------------- |
| Load Avg   | 4.0 - 6.0 | `sudo purge`           |
| Unused RAM | 200-500MB | Clean browser cache    |
| Compressor | 4-5GB     | Clean .next cache      |
| CPU Idle   | 20-40%    | Check zombie processes |

### Red Zone (Immediate Intervention)

| Metric     | Threshold | Action                       |
| ---------- | --------- | ---------------------------- |
| Load Avg   | > 6.0     | Full cache purge + purge     |
| Unused RAM | < 200MB   | Emergency purge              |
| Compressor | > 5GB     | Kill non-essential processes |
| CPU Idle   | < 20%     | Identify and throttle hogs   |

---

## 🔒 CC CLI PRESERVATION RULES

### NEVER DO:

```bash
❌ pkill -f claude
❌ pkill -f node
❌ killall node
❌ Reduce priority of claude processes
```

### SAFE INTERVENTIONS:

```bash
✅ sudo purge                 # RAM only
✅ rm -rf ~/Library/Caches/*  # App caches
✅ rm -rf .next/cache         # Build cache (non-active)
✅ npm cache clean --force    # NPM cache
✅ Clear browser caches       # Chrome/Safari
```

---

## 📊 MONITORING COMMANDS

```bash
# Quick status
top -l 1 -n 0 | head -12

# Memory breakdown
vm_stat | grep -E "(free|active|inactive|wired|compressor)"

# Process memory (sorted)
ps aux | sort -nk4 -r | head -10

# Swap activity
sysctl vm.swapusage
```

---

## 🎯 RECOMMENDED SETUP FOR VIBECODING HUB

1. **Max 4 CC CLI sessions** on 16GB M1
2. **1 dev server** at a time
3. **Browser**: Close unused tabs (each tab ~50-200MB)
4. **Auto-purge**: When RAM < 300MB
5. **Cache clean**: Every 2 hours of continuous operation

## 🛡️ AUTOMATED MONITOR: MACOOK GUARDIAN

The system is now continuously monitored and optimized by the `macook-guardian.sh` daemon.

### Guardian Features:

- **Interval**: 30 seconds
- **Logs**: `logs/macook-guardian.log`
- **Interventions**:
  - **Level 1 (Yellow)**: Auto-purge + Process Prioritization (`renice`).
  - **Level 2 (Red)**: Level 1 + Browser Cache Purge + Zombie Termination.
  - **Level 3 (Black)**: Level 2 + Deep cleanup (Weekly/Scheduled).

### Manual Control:

```bash
# View logs
tail -f logs/macook-guardian.log

# Manual Blitzkrieg
./scripts/cleanup_blitzkrieg.sh
```

---

_Protocol by Antigravity Agent - VibeCoding Hub Standard_
_Updated: 2026-02-06 - MACOOK Guardian Integrated_
