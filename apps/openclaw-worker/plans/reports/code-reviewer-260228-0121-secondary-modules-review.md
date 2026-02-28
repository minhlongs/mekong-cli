# Code Review — Secondary Modules (openclaw-worker)
**Date:** 260228-0121
**Reviewer:** code-reviewer
**Scope:** 14 files — RELIABILITY + OBSERVABILITY + AUTONOMOUS modules
**LOC Total:** 3022 lines

---

## Scope

| File | LOC | Status |
|------|-----|--------|
| brain-heartbeat.js | 58 | OK |
| brain-output-hash-stagnation-watchdog.js | 90 | Issues |
| brain-system-monitor.js | 63 | Issues |
| brain-health-server.js | 117 | Issues |
| agi-score-calculator.js | 59 | OK |
| api-rate-gate.js | 90 | Issues |
| auto-cto-pilot.js | **610** | CRITICAL — cần split |
| project-scanner.js | 154 | Issues |
| learning-engine.js | 207 | Issues |
| evolution-engine.js | 421 | Issues |
| post-mission-gate.js | 252 | Issues |
| mission-journal.js | 161 | Issues |
| mission-complexity-classifier.js | 397 | Issues |
| m1-cooling-daemon.js | 343 | Issues |

---

## Issues theo file

### 1. `brain-heartbeat.js`

**Line 23 — Silent catch block:**
```js
} catch (e) { /* non-critical */ }
```
Mất thông tin debug khi `/tmp` không writable. Dùng `log()` với level warn thay vì im lặng.

---

### 2. `brain-output-hash-stagnation-watchdog.js`

**Line 63 — Logic bug trong post-kickstart check:**
```js
if (hashHistory.length > 0 && newHash === hashHistory[0])
```
`hashHistory` vừa bị reset thành `[]` ở line 50 → `hashHistory.length > 0` luôn `false` → nhánh "Kickstart ineffective, triggering respawn" sẽ KHÔNG BAO GIỜ được kích hoạt. Cần so sánh với `newHash` trực tiếp hoặc lưu hash trước kickstart vào biến riêng.

**Fix:**
```js
const hashBeforeKickstart = hashOutput(capturePane(WATCHDOG_PANE));
hashHistory = [];
// ... kickstart ...
const newHash = hashOutput(capturePane(WATCHDOG_PANE));
if (newHash === hashBeforeKickstart) {
  // Kickstart ineffective
}
```

---

### 3. `brain-system-monitor.js`

**Line 36-37 — Silent catch + emoji trong log file:**
```js
} catch (e) { }
```
Lỗi write `THERMAL_LOG` bị nuốt hoàn toàn. Nên dùng `log()`.

**Line 34 — Emoji trong log file gây encoding issues trên một số terminals:**
```js
`[${new Date().toISOString()}] 🔥 HIGH LOAD...`
```
Nhất quán với `brain-logger.js` (không dùng emoji trực tiếp trong file log).

**Line 38 — `execSync('sleep ...')` block toàn bộ event loop:**
```js
execSync(`sleep ${coolingTime / 1000}`);
```
Hàm `isOverheating()` block node process 10s mỗi lần gọi. Nên dùng `await new Promise(r => setTimeout(r, coolingTime))` và mark function `async`. Hoặc chỉ return flag, để caller handle sleep — `m1-cooling-daemon.js` đã làm đúng pattern này.

---

### 4. `brain-health-server.js`

**Line 34 — Silent catch block:**
```js
try { brainAlive = require('./brain-spawn-manager').isBrainAlive(); } catch (e) { }
```
Tương tự lines 37, 40 — 3 catch blocks im lặng. Khi module fail load, không có gì báo lỗi. Dùng `/* optional module */` comment hoặc log ở level debug.

**Line 50 — Hardcoded default mode:**
```js
mode: process.env.TOM_HUM_BRAIN_MODE || 'tmux'
```
Trong `config.js` không có `BRAIN_MODE` field nào export ra. Default thực tế trong CLAUDE.md là `'direct'`, không phải `'tmux'`. Sửa thành `'direct'`.

**Line 83 — URL `/` trả về health response:**
Endpoint `/` và `/health` trả về cùng response. Không phải bug nhưng `/` nên trả về 404 hoặc redirect để tránh confusion với monitoring tools.

---

### 5. `api-rate-gate.js`

**Line 56 — `while (true)` thiếu log khi bị block lâu:**
```js
while (true) {
  // ... poll ...
}
```
Nếu bị block gần `MAX_WAIT_MS` (60s), không có log nào cảnh báo. Nên log sau mỗi 10s waiting.

**Line 16 — Hardcoded `/tmp/tom_hum_api.lock`:**
```js
const LOCK_FILE = '/tmp/tom_hum_api.lock';
```
Không dùng `config.OPENCLAW_HOME` hay `config.MEKONG_DIR`. Nếu `/tmp` bị full hoặc readonly, lỗi sẽ bị nuốt silently (lines 43-45). Nên đưa path vào `config.js`.

---

### 6. `auto-cto-pilot.js` — CRITICAL: 610 LOC, cần split

**File 610 LOC** — vi phạm quy tắc 200 LOC. Cần tách thành:
- `auto-cto-scanner.js` — scanProject + parseBuildErrors + parseLintErrors + parseTestErrors
- `auto-cto-mission-generator.js` — generateFixMission + dedup logic
- `auto-cto-phase-handlers.js` — handleScan + handleFix + handleVerify + advanceProject
- `auto-cto-pilot.js` — chỉ giữ startAutoCTO + stopAutoCTO + LLM vision loop

**Line 78 — Silent catch trong `loadState()`:**
```js
} catch (e) { }
```
JSON parse error bị nuốt hoàn toàn. Nếu `.cto-scan-state.json` corrupt, trả về default state mà không log warning.

**Line 87 — Silent catch trong `saveState()`:**
```js
} catch (e) { }
```
Mất state khi write fail, không ai biết.

**Line 534 — Silent catch trong web-researcher fallback:**
```js
} catch (e) { }
```
Line 523 có log, line 534 (DDG fallback) không có log nào khi fail.

**Line 344-367 — Inline `require('child_process').execSync` thay vì import:**
```js
const paneOutput = require('child_process').execSync(...)
```
Inline require trong tight loop 2x mỗi cycle. Nên import `execSync` ở top của file.

**Line 552 — `fs.writeFileSync` không atomic:**
```js
fs.writeFileSync(path.join(config.WATCH_DIR, filename), prompt);
```
`saveState()` dùng atomic rename pattern nhưng mission file write thì không. Nếu process crash giữa chừng, task file sẽ incomplete.

---

### 7. `project-scanner.js`

**Line 26 — Local `log()` function thay vì dùng `brain-logger`:**
```js
const { log } = require('./brain-process-manager');
```
Thực ra đây OK vì import từ facade. Nhưng trong `learning-engine.js` thì tự định nghĩa `log()` riêng (xem bên dưới).

**Line 59 — `execSync('npm run build 2>&1')` không có error output capture:**
```js
execSync('npm run build 2>&1', { cwd: projectDir, timeout: 60000 });
```
Khi build fail, `catch (e)` có `e.stdout` nhưng `execSync` mặc định pipe stdout/stderr → không có output trong exception. Nên thêm `encoding: 'utf-8'` để nhận output.

**Line 99 — Hardcoded report path:**
```js
const reportPath = path.join(config.MEKONG_DIR, 'apps/openclaw-worker/data/health-report.json');
```
Nên dùng `path.join(config.MEKONG_DIR, 'apps', 'openclaw-worker', 'data', 'health-report.json')` để cross-platform safe (mặc dù macOS ok với `/`).

**Line 142 — `runFullScan()` gọi ngay khi `startScanner()` — blocking:**
```js
runFullScan(); // Chạy ngay lần đầu
```
`runFullScan()` là async nhưng không await → fire-and-forget. Nếu lần chạy đầu chưa xong mà interval đã trigger (interval 30min) thì không overlap được, nhưng nếu ai đó giảm interval thì sẽ gặp race condition.

---

### 8. `learning-engine.js`

**Lines 23-27 — Tự định nghĩa `log()` thay vì dùng `brain-logger`:**
```js
function log(msg) {
  const ts = new Date().toLocaleTimeString('en-US', { hour12: false });
  const line = `[${ts}] [tom-hum] [LEARNING] ${msg}`;
  try { fs.appendFileSync('/Users/macbookprom1/tom_hum_cto.log', line + '\n'); } catch (e) { }
}
```
**Hardcoded path `/Users/macbookprom1/tom_hum_cto.log`** — không dùng `config.LOG_FILE`. Khi chạy trên máy khác hoặc user khác sẽ lỗi silently. Đây là violation nghiêm trọng — fix bằng cách import `{ log } from './brain-logger'` (hoặc ít nhất dùng `config.LOG_FILE`).

**Line 207 — LOC 207:** Sát ngưỡng 200. Xem xét extract `analyzePatterns()` và `getTaskAdjustments()` ra file riêng nếu phát triển thêm.

---

### 9. `evolution-engine.js`

**Lines 27-35 — Tự định nghĩa `log()` với `console.log`:**
```js
function log(msg) {
  // ...
  console.log(line);  // <-- console.log trong production code
  try {
    const logFile = process.env.TOM_HUM_LOG || path.join(process.env.HOME, 'tom_hum_cto.log');
    fs.appendFileSync(logFile, line + '\n');
  } catch { }
}
```
Hai vấn đề:
1. `console.log` trong production code — vi phạm Binh Pháp Front 1 (Tech Debt)
2. Tự định nghĩa log thay vì import `brain-logger` — code trùng lặp (vi phạm DRY)
3. Silent `catch { }` khi file append fail

**Line 34 — `catch { }` thiếu binding variable:**
```js
} catch { }
```
Valid ES2019+ nhưng không nhất quán với style `catch (e) {}` của các file khác.

**Line 421 — LOC 421:** Cần split. Đề xuất:
- `evolution-triggers.js` — `checkEvolutionTriggers()`, BENIGN_FAILURES set
- `evolution-skill-generator.js` — `generateSkill()`
- `evolution-token-optimizer.js` — `optimizeTokenRouting()`
- `evolution-brain-surgery.js` — `triggerBrainSurgery()`
- `evolution-engine.js` — façade re-export

**Line 353 — Hardcoded path trong mission content:**
```js
`Working dir: /Users/macbookprom1/mekong-cli/apps/openclaw-worker`
```
Dùng `config.MEKONG_DIR` hoặc `__dirname` thay vì hardcode path tuyệt đối.

---

### 10. `post-mission-gate.js`

**Lines 233-249 — Dead code:**
```js
function runBuildGate(project) { ... }
function runFullGate(project, missionId) {
  // This is a bridge to the new async function if needed,
  // but for now we'll keep it as is...
  return { build: true, pushed: false };  // <-- luôn return hardcoded value
}
```
`runFullGate()` luôn return `{ build: true, pushed: false }` — **hoàn toàn vô dụng**. `runBuildGate()` vẫn dùng blocking `execSync` trong khi `runPostMissionGate()` đã dùng async spawn. Cả 2 là dead code nếu không ai gọi chúng — cần xác nhận và remove.

**Line 157-160 — `git commit` với string interpolation không escaped:**
```js
const commitMsg = `mission complete: ${missionId}`;
execSync(`git commit -m "${commitMsg}"`, { ... });
```
Nếu `missionId` chứa ký tự `"` hoặc backtick, command injection risk. Nên dùng array form: `execSync('git', ['commit', '-m', commitMsg])` hoặc spawn với args array.

**Line 219 — Fix mission file không có tiền tố `/cook`:**
```js
const fixContent = `
MISSION: Fix build failure for ${missionId}
...
TASK:
1. Phân tích lỗi build bên trên.
```
Mission file được tạo không có `/cook` command prefix — vi phạm "NO COMMAND = NO ACTION" rule từ `task-delegation-require-command.md`. Task watcher sẽ nhận file này và inject trực tiếp vào CC CLI mà không có `/cook` wrapper.

---

### 11. `mission-journal.js`

**Lines 101-124 — `countTokensBetween()` hardcoded tmux session name:**
```js
execSync('tmux capture-pane -p -S -2000 -t tom_hum_brain 2>/dev/null', ...)
```
Session name `tom_hum_brain` hardcoded — nhưng `config.js` định nghĩa `TMUX_SESSION = 'tom_hum'`. Session name sai có thể dẫn đến count 0 tokens mọi lúc. Dùng `config.TMUX_SESSION`.

**Line 120 — Hardcoded model name:**
```js
return { tokens, model: 'claude-opus-4-6-thinking' }
```
Model hardcoded, không phản ánh model thực đang chạy. Dùng `config.MODEL_NAME`.

**Line 150 — `recentTaskTypes` thực ra là project names:**
```js
const taskTypes = recent.map(m => m.project || 'unknown');
```
Field tên `recentTaskTypes` nhưng trả về danh sách project names, không phải task types. Khi được feed vào `scoreTaskDiversity()` trong `agi-score-calculator.js`, diversity score sẽ dựa trên số project khác nhau thay vì loại task — có thể không đúng ý muốn (chỉ có 2 project: `openclaw-worker`, `well` → score luôn ≤ 6/20).

---

### 12. `mission-complexity-classifier.js`

**LOC 397 — vượt ngưỡng 200:**
Cần split thành:
- `thiet-ke-assessment.js` — `assessThietKe()` (100 lines)
- `mission-prompt-builder.js` — `generateMissionPrompt()`, `buildAgentTeamBlock()`, `buildDecomposedPrompt()`
- `mission-complexity-classifier.js` — chỉ giữ `classifyComplexity()`, `classifyContentTimeout()`, `detectIntent()`, `isTeamMission()`

**Lines 110-121 — JSDoc duplicate:**
```js
/**
 * Build Agent Team instruction block...
 */
/**
 * Build Agent Team instruction block...   <-- comment thứ 2 cho cùng function
 */
function buildAgentTeamBlock(...)
```
JSDoc comment bị duplicate (lines 110-112 và 113-121). Remove comment đầu tiên.

**Lines 55-57 — Silent catch trong `adjustTimeout()`:**
```js
} catch (e) {
  return baseTimeout || config.TIMEOUT_SIMPLE;
}
```
JSON parse error khi `HISTORY_FILE` corrupt bị nuốt. Nên log warning.

**Line 357 — `require('./quota-tracker')` có thể throw nếu module không tồn tại:**
```js
const qt = require('./quota-tracker');
```
Được wrap trong try/catch nhưng error bị nuốt (`score++` vẫn được chạy). Nếu `quota-tracker` không tồn tại thì logic fallback là đúng, nhưng nên comment rõ là optional module.

---

### 13. `m1-cooling-daemon.js`

**Line 173 — Shell expansion với `~` trong `execSync` có thể không hoạt động:**
```js
execSync(`rm -rf ${cachePaths.join(' ')} 2>/dev/null &`, { timeout: 2000 });
```
`~` không được expand trong Node.js `execSync` nếu không dùng `shell: true`. Nhưng `execSync` với string mặc định đã dùng shell, nên OK. Tuy nhiên nên dùng `os.homedir()` cho explicit hơn.

**Line 246 — Potential infinite penalty trong `waitForSafeTemperature()`:**
```js
const penalty = subagents > 2 ? Math.pow(2, subagents) * COHERENCE_PENALTY_FACTOR : 0;
```
Nếu `subagents = 20`, penalty = `2^20 * 1000 = 1,048,576,000ms ≈ 291 giờ`. Không có cap. Cần clamp: `Math.min(Math.pow(2, subagents) * COHERENCE_PENALTY_FACTOR, 60000)`.

**Line 207 — Magic number `4` không có constant:**
```js
subagents > (config.AGENT_TEAM_SIZE_DEFAULT * 4)
```
Multiplier `4` nên là named constant trong config.

**Line 75 — `pgrep` count cả node process của chính daemon:**
```js
execSync('pgrep -c -f "claudekit|node" 2>/dev/null', ...)
```
Pattern `node` match cả `task-watcher.js` process chính. `getSubagentCount()` sẽ luôn >= 1 ngay cả khi không có subagent nào, làm sai lệch overheat detection.

---

## Tổng hợp issues ưu tiên

### P0 — Logic Bug (gây chức năng sai)
| ID | File | Line | Vấn đề |
|----|------|------|--------|
| B1 | `brain-output-hash-stagnation-watchdog.js` | 63 | hashHistory reset trước khi compare → respawn không bao giờ trigger |
| B2 | `post-mission-gate.js` | 219 | Fix mission file không có `/cook` prefix → vi phạm delegation rule |
| B3 | `mission-journal.js` | 120 | Model hardcoded `claude-opus-4-6-thinking` — không phản ánh thực tế |
| B4 | `mission-journal.js` | 150 | `recentTaskTypes` trả về project names → AGI diversity score luôn thấp |

### P1 — Hardcoded Values (portability, correctness)
| ID | File | Line | Vấn đề |
|----|------|------|--------|
| H1 | `learning-engine.js` | 26 | Hardcoded `/Users/macbookprom1/tom_hum_cto.log` — dùng `config.LOG_FILE` |
| H2 | `evolution-engine.js` | 353 | Hardcoded `/Users/macbookprom1/mekong-cli/apps/openclaw-worker` |
| H3 | `mission-journal.js` | 105 | Tmux session `tom_hum_brain` ≠ `config.TMUX_SESSION` (`tom_hum`) |
| H4 | `brain-health-server.js` | 50 | Default brain mode `'tmux'` nhưng thực tế là `'direct'` |

### P2 — console.log / Log DRY violations
| ID | File | Line | Vấn đề |
|----|------|------|--------|
| L1 | `evolution-engine.js` | 30 | `console.log` trong production — dùng `brain-logger` |
| L2 | `evolution-engine.js` | 27-35 | Tự định nghĩa `log()` thay vì import `brain-logger` |
| L3 | `learning-engine.js` | 23-27 | Tự định nghĩa `log()` với hardcoded path |

### P3 — Silent Catch Blocks
| ID | File | Line | Vấn đề |
|----|------|------|--------|
| S1 | `brain-heartbeat.js` | 23 | `catch (e) { /* non-critical */ }` — nên log |
| S2 | `brain-system-monitor.js` | 36 | `catch (e) { }` khi write thermal log |
| S3 | `auto-cto-pilot.js` | 78 | `catch (e) { }` trong loadState |
| S4 | `auto-cto-pilot.js` | 87 | `catch (e) { }` trong saveState |
| S5 | `auto-cto-pilot.js` | 534 | `catch (e) { }` DDG fallback — không log |
| S6 | `evolution-engine.js` | 34 | `catch { }` khi append log file |

### P4 — Dead Code
| ID | File | Line | Vấn đề |
|----|------|------|--------|
| D1 | `post-mission-gate.js` | 233-249 | `runBuildGate()` + `runFullGate()` — dead code (luôn return hardcoded) |

### P5 — File Size (cần split)
| ID | File | LOC | Split proposal |
|----|------|-----|---------------|
| F1 | `auto-cto-pilot.js` | **610** | scanner + mission-generator + phase-handlers + pilot |
| F2 | `evolution-engine.js` | 421 | triggers + skill-generator + token-optimizer + brain-surgery |
| F3 | `mission-complexity-classifier.js` | 397 | thiet-ke-assessment + prompt-builder + classifier |

### P6 — Minor/Potential Issues
| ID | File | Line | Vấn đề |
|----|------|------|--------|
| M1 | `m1-cooling-daemon.js` | 246 | `Math.pow(2, subagents)` không có cap → potential giờ delay |
| M2 | `m1-cooling-daemon.js` | 75 | `pgrep -c node` count cả process chính |
| M3 | `post-mission-gate.js` | 159 | `git commit -m "${commitMsg}"` — command injection risk nếu missionId có quotes |
| M4 | `mission-complexity-classifier.js` | 110-121 | JSDoc duplicate |
| M5 | `api-rate-gate.js` | 16 | LOCK_FILE hardcoded `/tmp/` thay vì config |
| M6 | `brain-system-monitor.js` | 38 | `execSync('sleep ...')` block event loop 10s |

---

## Actions cần làm (thứ tự ưu tiên)

1. **[P0-B1]** Fix `brain-output-hash-stagnation-watchdog.js:63` — lưu hash trước kickstart vào biến riêng
2. **[P0-B2]** Fix `post-mission-gate.js:219` — wrap fix mission content với `/cook "..." --auto`
3. **[P1-H1]** Fix `learning-engine.js:26` — thay hardcoded path bằng `config.LOG_FILE`, import `brain-logger`
4. **[P1-H3]** Fix `mission-journal.js:105` — tmux session name dùng `config.TMUX_SESSION`
5. **[P2-L1]** Fix `evolution-engine.js:30` — remove `console.log`, import `brain-logger`
6. **[P0-B4]** Fix `mission-journal.js:150` — rename `recentTaskTypes` hoặc đổi logic map sang task type thực
7. **[P4-D1]** Remove `runBuildGate()` + `runFullGate()` dead code trong `post-mission-gate.js`
8. **[P6-M1]** Cap `penalty` trong `m1-cooling-daemon.js:246` tối đa 60000ms
9. **[P5-F1]** Split `auto-cto-pilot.js` (610 LOC) thành 4 modules
10. **[P5-F2]** Split `evolution-engine.js` (421 LOC) thành 4 modules
11. **[P5-F3]** Split `mission-complexity-classifier.js` (397 LOC) thành 3 modules
12. **[P3]** Thêm `log()` vào các silent catch blocks P3-S1 đến S6

---

## Unresolved Questions

1. **`runBuildGate()` và `runFullGate()`** có caller nào không? Cần grep toàn bộ codebase trước khi xóa.
2. **`mission-journal.js:150` `recentTaskTypes`** — AGI score cần "task type diversity" hay "project diversity"? Nếu là project diversity thì score 6/20 với 2 projects là đúng thiết kế, cần document lại.
3. **`countTokensBetween()`** — function có được gọi không? Tmux session name sai có thể là lý do tokens luôn = 0. Confirm xem function có active không.
4. **`purgeSystemCaches()`** — `rm -rf ~/Library/Caches/com.apple.dt.*` dùng glob pattern trong shell. Nếu pattern không match file nào, `rm -rf` sẽ return non-zero nhưng bị catch. Confirm behavior trên macOS mới.
