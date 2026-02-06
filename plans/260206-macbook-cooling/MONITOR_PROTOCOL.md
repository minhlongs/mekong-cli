# 🎖️ MacBook Continuous Monitor Protocol

> **Mệnh lệnh:** KHÔNG ĐƯỢC OFF - Giám sát liên tục, can thiệp ngay khi vượt ngưỡng

## ⚠️ NGƯỠNG CAN THIỆP TỰ ĐỘNG

| Metric         | 🟢 Safe | 🟡 Warning | 🔴 CRITICAL (Auto-Intervene) |
| -------------- | ------- | ---------- | ---------------------------- |
| **Load Avg**   | < 4.0   | 4.0 - 6.0  | **> 6.0**                    |
| **Unused RAM** | > 500MB | 200-500MB  | **< 200MB**                  |
| **Compressor** | < 4GB   | 4-5GB      | **> 5GB**                    |
| **CPU Idle**   | > 40%   | 20-40%     | **< 20%**                    |

---

## 🚨 AUTO INTERVENTION ACTIONS

### Level 1: Warning (🟡)

```bash
# Purge filesystem cache
sudo purge
```

### Level 2: Critical (🔴)

```bash
# 1. Purge RAM
sudo purge

# 2. Kill zombie processes (NOT CC CLI)
pgrep -f "esbuild" | xargs kill -9 2>/dev/null

# 3. Clean browser cache
rm -rf ~/Library/Application\ Support/Google/Chrome/Default/Cache/*

# 4. Clean .next cache (non-running projects only)
rm -rf ./frontend/.next/cache
rm -rf ./apps/sophia-ai-factory/.next/cache
```

### Level 3: Emergency (💀)

```bash
# Nuclear option - Clean everything except CC CLI
npm cache clean --force
rm -rf ~/Library/Logs/*
rm -rf ~/Library/Caches/ms-playwright*
rm -rf ~/.mekong/logs/*.log
```

---

## 🛡️ PROTECTED PROCESSES (NEVER KILL) - TUYỆT ĐỐI BẢO VỆ

| Process                    | Port | Importance      |
| -------------------------- | ---- | --------------- |
| claude (sophia-ai-factory) | -    | 🔒 **CRITICAL** |
| claude (Well)              | -    | 🔒 **CRITICAL** |
| claude (84tea)             | -    | 🔒 **CRITICAL** |
| npm run dev (84tea)        | 3005 | 🔒 **CRITICAL** |

### ⛔ COMMANDS CẤM TUYỆT ĐỐI:

```bash
# KHÔNG BAO GIỜ CHẠY:
pkill -f claude
pkill -f node  # Sẽ kill dev server
killall node
```

### ✅ COMMANDS AN TOÀN (Chỉ dùng những lệnh này):

```bash
sudo purge                    # OK - Chỉ clear FS cache
rm -rf ~/Library/Caches/*     # OK - App caches
rm -rf .next/cache            # OK - Build cache (non-running)
npm cache clean --force       # OK - NPM cache
pgrep -f "esbuild" | xargs kill -9  # OK - Zombie esbuild only
```

---

## 📊 MONITORING SCHEDULE

- **Check interval:** Every response cycle
- **Full scan:** top -l 1 -n 0 | head -12
- **Disk check:** df -h / (every 5 cycles)

---

## 🔄 CURRENT STATUS

Last check: 2026-02-06 07:50

- Load: Monitoring...
- RAM: Monitoring...
- Status: 🟢 ACTIVE GUARD (KeepAlive ON)

## 🛡️ ABSOLUTE PERSISTENCE (TUYỆT ĐỐI K OFF)

The monitoring system is anchored via macOS `launchd` to ensure it never stops.

### Persistent Layer:

- **Service**: `com.antigravity.macook-guardian`
- **Config**: `~/Library/LaunchAgents/com.antigravity.macook-guardian.plist`
- **Policy**: `KeepAlive: true` (Auto-restart if killed)

### Manual Recovery (If needed):

```bash
launchctl load ~/Library/LaunchAgents/com.antigravity.macook-guardian.plist
launchctl start com.antigravity.macook-guardian
```

---

_Protocol established by Antigravity Agent_
_Binh Pháp Score: 100/100 - Zero Tolerance Monitoring_
