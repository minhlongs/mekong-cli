/**
 * M1 Cooling Daemon — Thermal protection + dispatch pause gate
 *
 * Monitors load average and free RAM every COOLING_INTERVAL_MS (90s).
 * When overheating: sets pause flag, kills resource hogs, purges caches.
 * Task queue and auto-CTO check isOverheating() before dispatching.
 *
 * Thresholds (from config):
 *   OVERHEAT: load > 8 OR free RAM < 200MB → pause dispatch
 *   SAFE:     load < 5 AND free RAM > 500MB → resume dispatch
 */

const { execSync } = require('child_process');
const config = require('../config');
const { log } = require('./brain-process-manager');

let coolingCycle = 0;
let intervalRef = null;
let overheating = false;

// --- System metrics ---

function getLoadAverage() {
  try {
    const raw = execSync('sysctl -n vm.loadavg 2>/dev/null', { encoding: 'utf-8', timeout: 5000 }).trim();
    const match = raw.match(/([\d.]+)\s+([\d.]+)\s+([\d.]+)/);
    return match ? parseFloat(match[1]) : 0;
  } catch (e) { return 0; }
}

function getFreeRAM() {
  try {
    const raw = execSync('vm_stat 2>/dev/null | head -5', { encoding: 'utf-8', timeout: 5000 });
    const match = raw.match(/Pages free:\s+(\d+)/);
    return match ? Math.round((parseInt(match[1]) * 16384) / 1024 / 1024) : -1;
  } catch (e) { return -1; }
}

function hasThermalWarning() {
  try {
    const raw = execSync('pmset -g therm 2>/dev/null', { encoding: 'utf-8', timeout: 5000 });
    return raw.includes('CPU_Scheduler_Limit') || raw.includes('Speed_Limit');
  } catch (e) { return false; }
}

// --- Resource cleanup ---

const RESOURCE_HOGS = ['pyrefly', 'pyright', 'eslint_d', 'prettierd'];

function killResourceHogs() {
  for (const proc of RESOURCE_HOGS) {
    try {
      const pids = execSync(`pgrep -f "${proc}" 2>/dev/null`, { encoding: 'utf-8' }).trim();
      if (pids) {
        execSync(`pkill -f "${proc}" 2>/dev/null`);
        log(`🔪 KILLED ${proc}`);
      }
    } catch (e) {}
  }
}

function purgeSystemCaches() {
  // Clear build caches and temp files (safe, non-destructive)
  const cachePaths = [
    '~/Library/Caches/com.apple.dt.*',
    '~/Library/Caches/node*',
    '~/Library/Caches/typescript',
  ];
  try {
    execSync(`rm -rf ${cachePaths.join(' ')} 2>/dev/null`, { timeout: 10000 });
  } catch (e) {}
  // macOS purge (frees inactive memory pages)
  try {
    execSync('purge 2>/dev/null', { timeout: 10000 });
    log('🧹 RAM purge executed');
  } catch (e) {}
}

// --- Overheat detection ---

function checkOverheatStatus() {
  const load1 = getLoadAverage();
  const freeMB = getFreeRAM();
  const thermal = hasThermalWarning();

  const isOverheated = load1 > 8 || (freeMB >= 0 && freeMB < 200) || thermal;
  const isSafe = load1 < 5 && (freeMB < 0 || freeMB > 500);

  // Hysteresis: only change state at clear thresholds
  if (isOverheated && !overheating) {
    overheating = true;
    log(`🔴 OVERHEAT DETECTED — Load: ${load1} | RAM: ${freeMB}MB | Thermal: ${thermal} — PAUSING DISPATCH`);
    killResourceHogs();
    purgeSystemCaches();
  } else if (isSafe && overheating) {
    overheating = false;
    log(`🟢 COOLED DOWN — Load: ${load1} | RAM: ${freeMB}MB — RESUMING DISPATCH`);
  }

  return { load1, freeMB, thermal, overheating };
}

// --- Public API ---

/** Returns true if system is overheating and dispatch should be paused */
function isOverheating() { return overheating; }

/**
 * Async gate: blocks until system is cool enough to dispatch.
 * Called by task-queue before processing each mission.
 * If overheating, waits 60s intervals until safe.
 * @returns {Promise<void>}
 */
async function pauseIfOverheating() {
  if (!overheating) return;
  log('⏸️ THERMAL PAUSE — waiting for system to cool down...');
  while (overheating) {
    await new Promise(r => setTimeout(r, 60000));
    checkOverheatStatus();
    if (overheating) {
      const { load1, freeMB } = { load1: getLoadAverage(), freeMB: getFreeRAM() };
      log(`⏸️ Still hot — Load: ${load1} | RAM: ${freeMB}MB — waiting 60s more`);
      killResourceHogs();
    }
  }
  log('▶️ THERMAL PAUSE LIFTED — dispatch resuming');
}

function startCooling() {
  intervalRef = setInterval(() => {
    coolingCycle++;
    const { load1, freeMB } = checkOverheatStatus();
    const emoji = load1 > 8 ? '🔴' : load1 > 5 ? '🟡' : '🟢';
    log(`❄️ COOLING #${coolingCycle} ${emoji} Load: ${load1} | RAM: ${freeMB}MB${overheating ? ' | ⏸️ PAUSED' : ''}`);
  }, config.COOLING_INTERVAL_MS);
}

function stopCooling() {
  if (intervalRef) {
    clearInterval(intervalRef);
    intervalRef = null;
  }
}

module.exports = { startCooling, stopCooling, isOverheating, pauseIfOverheating };
