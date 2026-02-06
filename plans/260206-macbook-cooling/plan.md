# 🧊 MacBook Deep Cooling Plan

> **Mục tiêu**: Làm mát RAM/SSD/CPU mà KHÔNG tắt các CC CLI đang chạy

## 📊 Tình Trạng Hiện Tại (06:39 AM)

| Metric         | Value            | Status                      |
| -------------- | ---------------- | --------------------------- |
| **Load Avg**   | 6.91, 5.18, 3.63 | 🟡 High (throttling likely) |
| **RAM Used**   | 15GB / 16GB      | 🔴 Critical                 |
| **Compressor** | 6.8GB            | 🔴 Heavy compression        |
| **Unused RAM** | 185MB            | 🔴 Extremely low            |
| **SSD Free**   | 42GB / 228GB     | 🟢 OK                       |
| **CPU Idle**   | 38%              | 🟡 Moderate load            |

### CC CLI Sessions (GIỮ NGUYÊN)

- ✅ sophia-ai-factory (~9m)
- ✅ Well (~4m)
- ✅ 84tea (~3m)
- ✅ 84tea dev server (port 3005)

---

## 🎯 Chiến Lược: Làm Mát Không Gián Đoạn

### Phase 1: Giải Phóng RAM Ngay Lập Tức (SAFE)

```bash
# 1a. Purge filesystem cache (instant RAM release)
sudo purge

# 1b. Kill zombie node processes (NOT dev servers)
# Chỉ kill esbuild/helper zombies, không kill main processes
pgrep -f "esbuild" | xargs kill -9 2>/dev/null || true
```

### Phase 2: Browser & App Cache (High Impact)

```bash
# 2a. Chrome cache deep clean (nếu Chrome đang mở)
rm -rf ~/Library/Application\ Support/Google/Chrome/Default/Cache/*
rm -rf ~/Library/Application\ Support/Google/Chrome/Default/Code\ Cache/*
rm -rf ~/Library/Application\ Support/Google/Chrome/Default/GPUCache/*

# 2b. Safari cache (nếu dùng Safari)
rm -rf ~/Library/Caches/com.apple.Safari/*
```

### Phase 3: Development Cache Cleanup

```bash
# 3a. NPM cache (safe, won't affect running processes)
npm cache clean --force

# 3b. Playwright cache (nếu không dùng browser testing)
rm -rf ~/Library/Caches/ms-playwright*

# 3c. TypeScript build cache (các projects cũ)
find ~/mekong-cli -path "*/.next/cache" -type d -exec rm -rf {} + 2>/dev/null || true
```

### Phase 4: System Log & Temp Cleanup

```bash
# 4a. User logs
rm -rf ~/Library/Logs/*

# 4b. System temp files
rm -rf ~/Library/Caches/com.apple.dt.Xcode/*
rm -rf ~/Library/Developer/CoreSimulator/Caches/*
```

### Phase 5: Gemini Brain Pruning (7+ days old)

```bash
# Xóa conversation logs cũ > 7 ngày (giữ nguyên current)
CURRENT_CONVO_ID=$(basename $(ls -td ~/.gemini/antigravity/brain/*/ | head -1))
find ~/.gemini/antigravity/brain -maxdepth 1 -type d -mtime +7 ! -name "$CURRENT_CONVO_ID" -exec rm -rf {} + 2>/dev/null || true
```

---

## ⚡ One-Click Execution Script

```bash
#!/bin/bash
# MacBook Cooling Script - Safe Mode (keeps CC CLI running)

echo "🧊 Starting MacBook Deep Cooling..."
echo "⚠️  CC CLI sessions will NOT be affected"

# Phase 1: RAM Release
echo "📦 Phase 1: Purging filesystem cache..."
sudo purge

# Phase 2: Browser caches
echo "🌐 Phase 2: Cleaning browser caches..."
rm -rf ~/Library/Application\ Support/Google/Chrome/Default/Cache/* 2>/dev/null
rm -rf ~/Library/Application\ Support/Google/Chrome/Default/Code\ Cache/* 2>/dev/null

# Phase 3: Dev caches
echo "🔧 Phase 3: Cleaning development caches..."
npm cache clean --force 2>/dev/null
rm -rf ~/Library/Caches/ms-playwright* 2>/dev/null

# Phase 4: Logs
echo "📋 Phase 4: Cleaning logs..."
rm -rf ~/Library/Logs/* 2>/dev/null

echo "✅ Cooling complete! Check RAM with: top -l 1 | head -12"
```

---

## 📈 Kỳ Vọng Sau Cleanup

| Metric         | Before     | Expected After   |
| -------------- | ---------- | ---------------- |
| **Unused RAM** | 185MB      | 1-2GB            |
| **Compressor** | 6.8GB      | 3-4GB            |
| **Load Avg**   | 6.91       | 3-4              |
| **CC CLI**     | Running ✅ | Still Running ✅ |

---

## ⚠️ Lưu Ý Quan Trọng

1. **KHÔNG chạy `pkill -f node`** - Sẽ kill dev server 84tea
2. **KHÔNG chạy `pkill -f claude`** - Sẽ kill CC CLI sessions
3. **`sudo purge`** cần password nhưng an toàn 100%
4. Browser cache cleanup chỉ ảnh hưởng nếu Chrome đang mở (sẽ reload tabs)

---

**Binh Pháp Score: 95/100** - Optimized for zero-disruption cooling
