# Tom Hum Knowledge Base

**Last Updated:** 2026-02-17

---

## CTO Response Time Optimization (2026-02-17)

**Context:** Tom Hum có latency ~200ms khi detect task mới

**Root Cause:**
1. Poll interval 200ms (backup poll cho fs.watch)
2. Boot order: brain spawn TRƯỚC task queue → waste AG proxy health check time (~3-15s)

**Fix Applied:**
1. Poll interval 200 → 100ms (config.js:28)
2. Boot order: `startWatching` → `spawnBrain` (task-watcher.js:166)

**Impact:**
- Response time cải thiện ~50%
- Task queue active sớm hơn ~10s
- Task detection worst-case latency giảm từ 200ms → 100ms

**Verified Existing Features (NO CHANGE NEEDED):**
- Crash protection: `uncaughtException` + `unhandledRejection` handlers (task-watcher.js:80-87)
- Auto-restart: SIGUSR1 handler cho in-process restart (task-watcher.js:210-225)

**Version:** v2026.2.17

**Ref:** plans/reports/debugger-260217-2025-cto-slow-response.md

---

## Future Optimization Candidates

1. **fs.watch reliability**: Consider inotify-based watching (Linux) hoặc FSEvents (macOS) nếu backup poll vẫn cần < 100ms
2. **Brain spawn parallelization**: Explore spawning brain TRONG startWatching callback để tận dụng AG proxy boot time
3. **Mission file IPC alternative**: Socket-based IPC có thể nhanh hơn file polling

---

**End of Memory**
