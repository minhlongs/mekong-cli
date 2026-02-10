const { execSync } = require('child_process');
const config = require('../config');
const { log } = require('./brain-process-manager');

let coolingCycle = 0;
let intervalRef = null;

function startCooling() {
  intervalRef = setInterval(() => {
    coolingCycle++;
    try {
      // Check system load
      const loadRaw = execSync('sysctl -n vm.loadavg 2>/dev/null', { encoding: 'utf-8' }).trim();
      const loadMatch = loadRaw.match(/([\d.]+)\s+([\d.]+)\s+([\d.]+)/);
      const load1 = loadMatch ? parseFloat(loadMatch[1]) : 0;

      // Check free RAM
      const memRaw = execSync('vm_stat 2>/dev/null | head -5', { encoding: 'utf-8' });
      const freeMatch = memRaw.match(/Pages free:\s+(\d+)/);
      const freeMB = freeMatch ? Math.round((parseInt(freeMatch[1]) * 16384) / 1024 / 1024) : -1;

      const emoji = load1 > 8 ? '🔴' : load1 > 5 ? '🟡' : '🟢';
      log(`❄️ COOLING #${coolingCycle} ${emoji} Load: ${load1} | Free RAM: ${freeMB}MB`);

      // Kill known resource hogs
      for (const proc of ['pyrefly', 'pyright']) {
        try {
          const pids = execSync(`pgrep -f "${proc}" 2>/dev/null`, { encoding: 'utf-8' }).trim();
          if (pids) {
            execSync(`pkill -f "${proc}" 2>/dev/null`);
            log(`🔪 KILLED ${proc}`);
          }
        } catch(e) {}
      }

      // Hard cooling on high load or low RAM
      if (load1 > 8 || (freeMB >= 0 && freeMB < 200)) {
        log('🧊 HARD COOL');
        try {
          execSync('rm -rf ~/Library/Caches/com.apple.dt.* ~/Library/Caches/node* ~/Library/Caches/typescript 2>/dev/null');
        } catch(e) {}
      }
    } catch (e) {}
  }, config.COOLING_INTERVAL_MS);
}

function stopCooling() {
  if (intervalRef) {
    clearInterval(intervalRef);
    intervalRef = null;
  }
}

module.exports = { startCooling, stopCooling };
