# Code Review: OpenClaw Worker lib/ Full Review

**Date:** 2026-02-28
**Scope:** 14 core modules in `/apps/openclaw-worker/lib/`
**LOC reviewed:** ~3,500 lines across core modules
**Focus:** Logic bugs, security, resource leaks, silent catch blocks, crash risks

---

## CRITICAL Issues

```
brain-boot-sequence.js:18-37 — [CRITICAL] generateClaudeCommand() duplicated
  Hoan toan copy-paste tu brain-spawn-manager.js:62-82.
  Hai ban doc lap — sửa 1 noi se KHONG cap nhat noi kia.
  FIX: Import tu brain-spawn-manager thay vi inline.
  Hien tai comment noi "avoid circular dep" nhung spawnBrain() da lazy-require
  brain-boot-sequence, vay nen co the import nguoc lai.

brain-system-monitor.js:38 — [CRITICAL] execSync('sleep 10') blocks event loop
  isOverheating() goi execSync('sleep 10') — CHẶN TOAN BO Node.js 10 giay.
  Module nay duoc goi trong brain-mission-runner.js:172 MOI POLL ITERATION.
  Neu load > 4.0, moi poll bi block 10s. Voi threshold 4.0 tren M1,
  day co the xay ra THUONG XUYEN, block task queue va moi timer.
  FIX: Dung async sleep (setTimeout) hoac loai bo hoan toan — m1-cooling-daemon
  da xu ly thermal management rieng. Threshold 4.0 qua thap cho M1 8-core.

post-mission-gate.js:157 — [CRITICAL] 'git add .' auto-commits ALL files
  Sau khi build GREEN, gate chay 'git add .' + commit + push.
  Dieu nay co the commit:
  - File .env, API keys, credentials neu bi tao trong mission
  - File tam (.tmp, .bak, log files)
  - File khong lien quan den mission hien tai
  FIX: Dung 'git add -u' (chi staged files da tracked) hoac parse git diff
  de chi add cac file mission thuc su thay doi.

post-mission-gate.js:159 — [CRITICAL] Command injection via missionId
  commitMsg chua missionId duoc truyen truc tiep vao shell command.
  Regex replace chi loai bo `"$\\ nhung khong loai bo backtick, semicolon, pipe.
  Vi du: missionId = "test; rm -rf /" → git commit -m "mission complete: test; rm -rf /"
  FIX: Dung execSync voi args array (execFileSync) hoac escape day du.
```

## HIGH Priority Issues

```
brain-spawn-manager.js:88-92 — [HIGH] spawnBrain() starts heartbeat/watchdog unconditionally
  spawnBrain() goi startHeartbeat() va startOutputHashWatchdog() SAU khi
  await brain-boot-sequence.spawnBrain(). Nhung neu boot-sequence return
  som (session da ton tai, line 49), heartbeat/watchdog van start
  cho process hien tai (process.pid) — co the conflict voi instance cu.

brain-spawn-manager.js:113 — [HIGH] Silent catch in isBrainAlive()
  catch(e) { return false; } — khong log bat ky loi gi.
  Khi tmux command fail vi loi khac (permission, timeout), ham tra ve false
  va brain bi coi nhu "dead" → trigger respawn khong can thiet.
  FIX: Log error truoc khi return false.

brain-mission-runner.js:187 — [HIGH] Silent catch blocks (6 instances)
  Nhieu cho trong _handleIdleState va runMission:
  - Line 187: try { require('./learning-engine').recordOutcome(...) } catch (e) { }
  - Line 252-257: 2 nested try-catch voi catch(e){} — nuot loi hoan toan
  - Line 255: learning-engine.recordOutcome bi nuot
  - Line 271: learning-engine.recordOutcome bi nuot
  - Line 280: learning-engine.recordOutcome bi nuot
  FIX: It nhat log(e.message) de debug khi learning-engine fail.

brain-mission-runner.js:87,91 — [HIGH] Lazy require() inside hot path
  token-tracker va m1-cooling-daemon duoc require() MOI LAN runMission chay.
  Node.js cache require() nhung lookup van co overhead. Chuyen len top of file.

brain-mission-runner.js:172 — [HIGH] Lazy require brain-system-monitor inside poll loop
  require('./brain-system-monitor') duoc goi MOI 500ms poll iteration.
  Nen move len top hoac cache reference.

task-queue.js:193 — [HIGH] archiveProcessedMissions imported but never exported
  task-watcher.js:193 goi require('./lib/task-queue').archiveProcessedMissions
  nhung task-queue.js KHONG export ham nay. → archiveProcessedMissions = undefined.
  Khong crash vi safeBoot() catch loi, nhung WAL recovery khong hoat dong.

auto-cto-pilot.js:348-351 — [HIGH] execSync trong LLM-VISION co the block event loop
  Moi 120s, auto-CTO chay execSync('tmux capture-pane...') cho MOI pane.
  Neu tmux hang, execSync block toan bo daemon cho den timeout 3s.
  Nen dung execFile (async) thay vi execSync.

learning-engine.js:27 — [HIGH] appendFileSync tren moi log call
  Moi log() call goi fs.appendFileSync — I/O dong bo, block event loop.
  Voi nhieu module goi log() lien tuc, day la bottleneck.
  FIX: Dung brain-logger.js (da co) thay vi tao log() rieng.

learning-engine.js:33 — [HIGH] Silent catch blocks (4 instances)
  - Line 33: loadOutcomes() catch(e){} → tra ve [] khi JSON parse fail
  - Line 39: saveOutcomes() catch(e){} → mat data khi write fail
  - Line 44: loadLessons() catch(e){} → nuot parse error
  - Line 51: saveLessons() catch(e){} → nuot write error
  FIX: Log e.message de biet khi data file bi corrupt.

evolution-engine.js:33 — [HIGH] Silent catch block
  log() function co catch {} (empty) — neu log file write fail,
  toan bo module chay "mù" khong co observability.
  FIX: fallback console.error() khi appendFileSync fail.

m1-cooling-daemon.js:172-178 — [HIGH] rm -rf voi tilde expansion khong hoat dong
  execSync('rm -rf ~/Library/Caches/...') — tilde (~) KHONG duoc expand
  boi execSync khi dung string form (khong qua shell expansion).
  Thuc te, lenh nay khong xoa gi ca.
  FIX: Dung process.env.HOME thay vi ~, hoac wrap trong sh -c.

m1-cooling-daemon.js:177 — [HIGH] 'purge' command can root/sudo tren macOS moi
  execSync('purge') can quyen elevated. Neu fail, bi nuot boi catch(e){}.
  Khong gay crash nhung ghi log misleading "Background RAM purge initiated"
  TRUOC khi purge thuc su chay (va co the fail).
```

## MEDIUM Priority Issues

```
brain-boot-sequence.js:75 — [MEDIUM] Shell injection via command string
  cmdPro va cmdApi chua hardcoded paths nhung tmux send-keys voi
  single quotes. Neu command chua single quote → break tmux syntax.
  Hien tai khong khai thac duoc vi gia tri la constants.

brain-respawn-controller.js:53 — [MEDIUM] killBrain truyen sessionName nhung killBrain
  nhan default config.TMUX_SESSION
  respawnBrain tinh toan sessionName (PRO hoac API) nhung killBrain(sessionName)
  → kill session PRO/API, roi spawnBrain() tao lai TOAN BO session.
  Logic khong match: muon kill 1 session nhung respawn toan bo.

circuit-breaker.js — [MEDIUM] Breakers Map grows indefinitely
  Map 'breakers' khong bao gio duoc clean. Moi circuit name moi → entry moi.
  Trong thuc te chi co vai circuit nen khong nghiem trong,
  nhung khong co mechanism de cleanup.

mission-dispatcher.js:437 — [MEDIUM] execSync voi space truoc ls
  `ls - t "${projectDir}/plans"/*/plan.md` — co space giua `ls` va `-t`.
  Day la loi syntax: `ls` chay khong co flag, `-t` bi truyen nhu argument.
  FIX: Sua thanh `ls -t "${projectDir}/plans"/*/plan.md`.

mission-dispatcher.js:42-52 — [MEDIUM] Silent catch blocks
  - try { require('./mission-complexity-classifier') } catch(e) { log(...) }
  Nay OK (co log), nhung:
  - Line 193: catch(e){} — lan 2 cua execSync

task-queue.js:64 — [MEDIUM] Silent catch in getQueueStats
  dlqCount calculation co catch(e) { /* dir may not exist */ }
  Nen dung fs.existsSync truoc thay vi swallow error.

post-mortem-reflector.js:328-364 — [MEDIUM] Module re-exports overridden AFTER initial export
  module.exports duoc set 2 lan:
  - Line 323: module.exports = { reflectOnMission, getTopLessons }
  - Line 364: module.exports = { reflectOnMission: enhancedReflect, getTopLessons }
  Hoat dong dung (override) nhung confusing. Nen dung 1 export duy nhat.

token-tracker.js:44 — [MEDIUM] String comparison cho time filtering
  countTokensBetween() so sanh HH:MM:SS strings. Dung cho cung ngay
  nhung KHONG hoat dong khi mission span qua nua dem (23:59 → 00:01).
  endHMS < startHMS → khong match gi ca.

config.js:28 — [MEDIUM] POLL_INTERVAL_MS = 100 (100ms polling)
  Task queue poll moi 100ms — 600 filesystem reads/minute.
  Ket hop voi fs.watch da co, day la overhead khong can thiet.
  FIX: Tang len 5000ms (5s) vi fs.watch da handle instant detection.

config.js:22 — [MEDIUM] TASK_PATTERN regex qua rong
  Pattern /^(?:CRITICAL_|HIGH_|MEDIUM_|LOW_)?(?:mission_)?.+\.txt$/
  Match BAT KY file .txt nao. Vi du: "readme.txt", "notes.txt"
  deu match. Nen require it nhat "mission_" prefix.
```

## LOW Priority Issues

```
brain-spawn-manager.js:49-51 — [LOW] Inefficient array filter-rebuild
  canRespawn() filter → clear → push loop. Co the dung splice hoac
  don gian respawnTimestamps = filtered (nhung la const).

brain-state-machine.js:103 — [LOW] findLastIndex polyfill?
  findLastIndex() can Node 18+. Neu chay tren Node 16, se throw.
  Hien tai khong phai van de neu dung Node 18/20.

brain-heartbeat.js — [LOW] Heartbeat file o /tmp global
  /tmp/tom_hum_heartbeat khong namespaced. Neu 2 instance chay,
  se overwrite nhau. Nen dung PID trong filename.

mission-journal.js:101-126 — [LOW] countTokensBetween duplicate
  Ca token-tracker.js va mission-journal.js deu co countTokensBetween().
  2 ham KHAC nhau: 1 doc proxy log, 1 doc tmux output.
  Confusing cho caller — brain-mission-runner.js dung token-tracker version.
```

---

## Positive Observations

- **Facade pattern** (`brain-process-manager.js`) giu backward compat tot — 37 lines re-export.
- **Circuit breaker** (`circuit-breaker.js`) clean, simple, dung state machine pattern.
- **Dead Letter Queue** trong task-queue.js xu ly fail missions tot voi metadata.
- **Safety Gate v2.0** trong post-mission-gate.js co 3-tier protection (file count, deletions, forbidden files).
- **Deduplication** trong brain-mission-runner.js ngan duplicate missions hieu qua.
- **Rate limiting** (canRespawn, API_RATE_GATE) bao ve chong spam.
- **Graceful shutdown** trong task-watcher.js xu ly SIGTERM/SIGINT dung cach.
- **Self-healing boot** (safeBoot pattern) cho phep modules fail doc lap.

---

## Top 5 Recommended Actions (uu tien)

1. **[CRITICAL] Fix command injection** trong post-mission-gate.js:159 — dung execFileSync hoac escape missionId day du
2. **[CRITICAL] Fix 'git add .'** trong post-mission-gate.js:157 — chuyen sang 'git add -u'
3. **[CRITICAL] Fix blocking execSync('sleep 10')** trong brain-system-monitor.js:38 — dung async hoac loai bo
4. **[HIGH] Fix generateClaudeCommand duplication** — xoa inline copy trong brain-boot-sequence.js
5. **[HIGH] Add logging** cho tat ca silent catch blocks (it nhat 15 instances)

---

## Metrics

- **Silent catch blocks found:** 15+
- **Code duplication:** 1 major (generateClaudeCommand 20 lines x2)
- **Potential crash vectors:** 3 (command injection, blocking sleep, git add)
- **Resource leak risks:** 0 (timers duoc clean trong stop functions)
- **Security issues:** 2 (command injection, git add overshoot)

---

## Unresolved Questions

1. `archiveProcessedMissions` duoc import trong task-watcher.js nhung khong ton tai trong task-queue.js exports — co phai dead code?
2. `brain-system-monitor.js` isOverheating() voi threshold 4.0 co bi conflict voi m1-cooling-daemon.js threshold 30? Hai module deu check load nhung thresholds rat khac nhau.
3. Tren Node 16, `findLastIndex()` trong brain-state-machine.js se crash — project yeu cau Node version nao?
