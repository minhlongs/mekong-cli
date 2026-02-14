# Code Review: brain-tmux v29 Multi-Pane Refactoring

**Reviewer:** code-reviewer (a4dbfb6)
**Date:** 2026-02-11
**Scope:** 5 files, brain-tmux-v2 multi-pane concurrent dispatch

## Files Reviewed

| File | LOC | Focus |
|------|-----|-------|
| `config.js` | 67 | PANE_COUNT, TMUX_SESSION added |
| `lib/brain-tmux.js` | 469 | Core multi-pane refactoring |
| `lib/task-queue.js` | 100 | Concurrent processing, re-queue |
| `lib/m1-cooling-daemon.js` | 210 | getMaxActivePanes() added |
| `task-watcher.js` | 99 | Version bump v29.0 |

## Overall Assessment

Refactoring well-structured. State machine preserved identically from v28, made pane-aware correctly. Named paste buffers, per-pane context management, acquire/release pattern -- all sound. Backward compat PANE_COUNT=1 verified correct.

Three issues need attention: a spin loop on re-queue, dead code that should be integrated, and a stale docstring.

---

## HIGH Priority

### H1. Spin loop khi all_panes_busy (task-queue.js:36-41)

**Van de:** Khi `runMission()` tra ve `all_panes_busy`, task duoc re-queue va `processQueue()` goi lai ngay trong `finally` block (line 50). Khong co backoff/delay. Vong lap:

```
processQueue() -> executeTask() -> runMission() -> acquirePane() = -1
  -> return {all_panes_busy}
  -> re-queue
  -> finally: activeCount-- -> processQueue() -> lap lai
```

Moi vong lap thuc hien: readFileSync, classifyContentTimeout, executeTask (tra ve ngay). Spin loop nay chay lien tuc cho den khi 1 pane duoc giai phong.

**Impact:** Tieu hao CPU/IO khong can thiet tren M1 16GB. Spam log file. Co the gop phan overheat.

**Fix:** Them delay truoc khi retry:

```js
if (result && result.result === 'all_panes_busy') {
  log(`Re-queuing (all panes busy): ${taskFile}`);
  queue.unshift(taskFile);
  await new Promise(r => setTimeout(r, 10000)); // 10s backoff
  return;
}
```

### H2. respawnPane() defined but never called (brain-tmux.js:235-248)

**Van de:** Function `respawnPane()` co logic respawn 1 pane doc lap nhung:
- Khong duoc export (line 469: khong co trong module.exports)
- Khong duoc goi bat ky dau

**Impact:** Neu 1 pane's CC CLI process crash ma tmux session van song, khong co co che recovery per-pane. Mission se timeout sau 15-45 phut roi moi duoc retry. Voi 4 panes, mat 1 pane = giam 25% throughput.

**Fix:** Integrate respawnPane vao state machine. Khi `detectState()` tra ve `idle` lien tuc nhung pane khong responsive, hoac khi `capturePane()` cho thay shell prompt thay vi CC CLI prompt, goi `respawnPane()`.

### H3. getMaxActivePanes() exported nhung khong duoc dung (m1-cooling-daemon.js:141-147)

**Van de:** Function duoc define, export, va mention trong task-watcher.js comment (line 12), nhung KHONG DUOC GOI bat ky dau. task-queue.js van su dung `config.PANE_COUNT` co dinh (line 16), khong co load-based throttling.

**Impact:** Feature "load-based pane throttling" advertised trong v29 changelog nhung chua hoat dong. Khi load cao, tat ca 4 panes van co the chay dong thoi.

**Fix:** Integrate vao task-queue.js:

```js
const { getMaxActivePanes } = require('./m1-cooling-daemon');

async function processQueue() {
  const maxPanes = getMaxActivePanes();
  if (activeCount >= maxPanes || queue.length === 0) return;
  // ...
}
```

---

## MEDIUM Priority

### M1. Stale docstring waitForSafeTemperature (m1-cooling-daemon.js:152)

Docstring noi "blocks until load < 7 AND free RAM > 300MB" nhung threshold thuc te la `OVERHEAT_RAM_MB = 50`. Da thay doi trong diff nhung quen update docstring.

### M2. isBrainAlive() false positive (brain-tmux.js:299)

```js
execSync('pgrep -f "claude"', { timeout: 3000 });
```

Match BAT KY process nao co "claude" trong command line. Khi user dang chay claude code session khac (vi du: session review nay), `isBrainAlive()` tra ve true du brain's claude processes da chet.

**Fix:** Filter theo tmux session:

```js
function isBrainAlive() {
  if (!isSessionAlive()) return false;
  // Check if at least 1 pane has a running claude process
  for (let i = 0; i < PANE_COUNT; i++) {
    const output = capturePane(i);
    if (hasPrompt(output) || isBusy(output)) return true;
  }
  return false;
}
```

### M3. spawnBrain() khong verify pane count khi reuse (brain-tmux.js:268-272)

Khi session da ton tai, `spawnBrain()` chi log "reusing" ma khong kiem tra so pane thuc te co khop voi `PANE_COUNT` config. Neu user thay doi `TOM_HUM_PANE_COUNT` env var va restart daemon, session cu co the co so pane khac.

**Fix:** Them pane count verification:

```js
if (isSessionAlive()) {
  const actual = parseInt(tmuxExec(`tmux list-panes -t ${SESSION} | wc -l`)) || 0;
  if (actual !== PANE_COUNT) {
    log(`BRAIN: Pane count mismatch (actual=${actual}, config=${PANE_COUNT}) -- recreating`);
    killBrain();
    // fall through to create new session
  } else {
    log(`BRAIN: tmux session already exists -- reusing (${PANE_COUNT} panes)`);
    return;
  }
}
```

### M4. CLEAR_EVERY_N=3 va COMPACT_EVERY_N=5 overlap

Tren mission #15 (va moi boi so cua 15): ca `/clear` va `/compact` deu trigger. Sau `/clear`, `/compact` la redundant. Khong hai gi nhung mat 10-15s cho moi pane.

---

## LOW Priority

### L1. Shell injection potential (brain-tmux.js:245, 283)

`buildClaudeCmd()` output duoc wrap trong single quotes trong tmux send-keys. Neu model name hoac proxy URL chua single quote, command se break. Hien tai khong xay ra nhung fragile.

### L2. Redundant require trong getMaxActivePanes (m1-cooling-daemon.js:143)

`require('../config').PANE_COUNT` khi `config` da import o dau file. Minor, khong anh huong gi.

---

## Backward Compatibility: PANE_COUNT=1

Verified correct:
- `paneStates` = 1 entry, `acquirePane()` luon tra ve 0 hoac -1
- `spawnBrain()`: no split-window, no select-layout (cac loop khong chay khi PANE_COUNT=1)
- State machine khong thay doi: DISPATCHED -> BUSY -> DONE
- Named paste buffer `pane_0` thay vi shared buffer -- cai thien so voi v28
- `task-queue.js`: `activeCount >= 1` cho phep toi da 1 task -- giong v28 `isProcessing`

**Ket luan:** v28 behavior duoc bao toan hoan toan.

---

## Concurrency Safety

Node.js single-threaded nen khong co race condition thuc su giua `activeCount` (task-queue) va `paneStates` (brain-tmux). Hai counter nay dong bo vi:
1. `processQueue` increment activeCount -> goi `executeTask` -> `runMission` -> `acquirePane` (set pane busy)
2. `runMission` finally -> `releasePane` -> return -> `processQueue` finally -> activeCount--

Named tmux paste buffers (`pane_0`, `pane_1`...) ngan buffer contamination giua cac pane. Correct.

Duy nhat van de la spin loop khi `all_panes_busy` (H1).

---

## Positive Observations

- try/finally pattern cho acquirePane/releasePane dam bao khong leak pane state
- Per-pane missionCount cho phep context management doc lap
- detectState() state machine sach, de hieu, khong thay doi tu v28
- stripAnsi() da duoc them vao -- fix van de ANSI sequence can thiep pattern matching
- Pane target format `session:window.pane` dung chuan tmux
- Log messages co paneIdx -- de debug

---

## Recommended Actions (Uu tien)

1. **[CRITICAL FIX]** Them backoff delay khi re-queue `all_panes_busy` trong task-queue.js
2. **[INTEGRATE]** Goi `getMaxActivePanes()` trong task-queue.js thay vi `config.PANE_COUNT` co dinh
3. **[INTEGRATE]** Export va su dung `respawnPane()` cho per-pane crash recovery
4. **[FIX]** Update docstring waitForSafeTemperature (300MB -> 50MB)
5. **[IMPROVE]** Fix isBrainAlive() de chi match tmux brain's claude processes

## Metrics

- Type Coverage: N/A (JavaScript, khong co TypeScript)
- Test Coverage: 0% (daemon, no automated tests -- documented in CLAUDE.md)
- Linting Issues: 0 syntax errors
- Dead Code: 2 functions (respawnPane, getMaxActivePanes unused)

## Unresolved Questions

1. `respawnPane()` co duoc design de integrate sau hay la code con sot lai tu development?
2. `getMaxActivePanes()` threshold `min(2, paneCount)` cho load 5-7 -- tai sao 2 ma khong phai `Math.ceil(paneCount / 2)`?
3. Neu 1 pane crash va respawnBrain() kill toan bo session, cac mission dang chay tren pane khac se bi mat -- co chap nhan duoc khong?
