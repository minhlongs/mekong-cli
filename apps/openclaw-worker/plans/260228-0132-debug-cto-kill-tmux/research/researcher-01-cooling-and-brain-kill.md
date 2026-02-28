# Research: M1 Cooling Daemon & Brain Kill/Tmux Termination Patterns

**Date:** 2026-02-28
**Files Read:** m1-cooling-daemon.js, brain-respawn-controller.js, brain-boot-sequence.js, brain-spawn-manager.js
**Grep scope:** all `lib/` files for `tmux kill|kill-session|process.kill|exec.*kill`

---

## 1. m1-cooling-daemon.js — Does NOT kill tmux

**Kills:** `pyrefly, pyright, eslint_d, prettierd, rust-analyzer, solc, tailwind, ts-server, tsserver` ONLY.

Conditions to kill: process must BOTH match `RESOURCE_HOGS` list AND have CPU > 20%.

```js
// lib/m1-cooling-daemon.js:114-155
const RESOURCE_HOGS = [
  'pyrefly', 'pyright', 'eslint_d', 'prettierd',
  'rust-analyzer', 'solc', 'tailwind', 'ts-server', 'tsserver'
];
// ...
const isTarget = RESOURCE_HOGS.some(hog => cmd.includes(hog));
if (!isTarget) continue;
if (cpu < 20.0) continue;
process.kill(pid, 'SIGTERM');  // SIGTERM only, not SIGKILL
```

**Verdict:** Cooling daemon CANNOT kill tmux. Whitelist is explicit and tmux is not in it.

---

## 2. brain-spawn-manager.js — killBrain() IS the tmux killer

```js
// lib/brain-spawn-manager.js:94-101
function killBrain(sessionName = config.TMUX_SESSION) {
  stopHeartbeat();
  stopOutputHashWatchdog();
  if (isSessionAlive(sessionName)) {
    tmuxExec(`tmux kill-session -t ${sessionName}`, sessionName);
    log(`BRAIN: tmux session ${sessionName} killed`);
  }
}
```

`killBrain()` is called from **brain-respawn-controller.js** (see §3).

---

## 3. brain-respawn-controller.js — Triggers killBrain on every respawn

```js
// lib/brain-respawn-controller.js:42-62
async function respawnBrain(intent = 'EXECUTION', useContinue = true) {
  const sessionName = isPlanning ? TMUX_SESSION_PRO : TMUX_SESSION_API;

  if (!canRespawn()) {
    // ... rate limit cooldown (5/hr max)
  }
  respawnTimestamps.push(Date.now());

  killBrain(sessionName);              // ← KILLS tmux session here
  await new Promise(r => setTimeout(r, 2000));

  await spawnBrain();                  // ← Immediately recreates session
  // ...
}
```

**Trigger conditions for `respawnBrain()`:** called by higher-level crash handlers (brain-mission-runner.js, brain-output-hash-stagnation-watchdog.js, etc.) — not read here, but this is the kill path.

Rate limit: max 5 respawns/hour via `canRespawn()`.

---

## 4. brain-boot-sequence.js — Kills session during pane REPAIR

This is a subtle kill path triggered during `spawnBrain()` if session exists but has wrong pane count:

```js
// lib/brain-boot-sequence.js:42-56
if (isSessionAlive(TMUX_SESSION)) {
  const paneCount = parseInt(
    execSync(`tmux list-panes -t ${TMUX_SESSION} | wc -l`, ...)
  );
  if (paneCount >= 2) {
    log(`BRAIN: tmux session exists (Panes: ${paneCount}/2) — reusing`);
    return;  // Safe path — no kill
  }
  log(`BRAIN: Session exists but has ${paneCount}/2 panes. REPAIRING...`);
  tmuxExec(`tmux kill-session -t ${TMUX_SESSION}`, TMUX_SESSION);  // ← KILLS here
}
```

**Risk:** If tmux session exists with 1 pane (e.g. user manually split a window), `spawnBrain()` will kill it and recreate as dual-pane.

---

## 5. Additional Kill Patterns Found (grep results)

| File | Line | Pattern | Scope |
|------|------|---------|-------|
| `brain-spawn-manager.js` | 98 | `tmux kill-session -t ${sessionName}` | killBrain() |
| `brain-boot-sequence.js` | 52 | `tmux kill-session -t ${TMUX_SESSION}` | pane repair |
| `m1-cooling-daemon.js` | 150 | `process.kill(pid, 'SIGTERM')` | RESOURCE_HOGS only |
| `resource-governor.js` | 80 | `process.kill(pid, 'SIGTERM')` | similar whitelist |
| `brain-vscode-terminal.js` | 99 | `kill ${pid}` | VS Code terminal pane PID |
| `lobster-proxy-pilot.js` | 65 | `process.kill(pid, 'SIGKILL')` | proxy process |
| `team-mutex.js` | 62 | `process.kill(lockData.pid, 0)` | liveness check only (signal 0) |

---

## Summary: Kill Paths That Can Terminate Tmux Sessions

### Path A — `respawnBrain()` (PRIMARY suspect)
`brain-output-hash-stagnation-watchdog.js` or `brain-mission-runner.js`
→ calls `respawnBrain(intent)`
→ calls `killBrain(sessionName)`
→ executes `tmux kill-session -t <session>`

### Path B — `spawnBrain()` pane repair (SECONDARY suspect)
On boot or respawn, if existing session has < 2 panes:
→ `spawnBrain()` in `brain-boot-sequence.js`
→ `tmux kill-session -t ${TMUX_SESSION}`

### Path C — `brain-vscode-terminal.js:99` (narrow scope)
Kills PID of a specific VS Code terminal pane, not whole session.

---

## Unresolved Questions

1. What calls `respawnBrain()`? Need to read `brain-output-hash-stagnation-watchdog.js` and `brain-mission-runner.js` to find all callers.
2. `resource-governor.js:80` — does it have a broader RESOURCE_HOGS list than cooling-daemon? Not read.
3. `lobster-proxy-pilot.js:65` — SIGKILL target: is it the CC CLI process or a separate proxy? Not read.
4. `TMUX_SESSION_PRO` vs `TMUX_SESSION_API` exact values — defined in `brain-tmux-controller.js`, not read.
