#!/usr/bin/env node
/**
 * 🦞 TÔM HÙM (OpenClaw) Task Watcher — v22.0 MODULAR BRAIN
 *
 * Thin orchestrator: imports modules, wires lifecycle, handles shutdown.
 * CC CLI stays alive via expect brain — persistent session across missions.
 *
 * Modules:
 *   config.js               — All constants, paths, env vars
 *   lib/brain-process-manager.js — Spawn/monitor/kill expect brain
 *   lib/mission-dispatcher.js    — Atomic file IPC, prompt building
 *   lib/task-queue.js            — File watching, queuing, archiving
 *   lib/auto-cto-pilot.js       — Binh Phap auto-task generation
 *   lib/m1-cooling-daemon.js     — M1 thermal management
 */

const { spawnBrain, killBrain, log } = require('./lib/brain-process-manager');
const { startWatching } = require('./lib/task-queue');
const { startAutoCTO } = require('./lib/auto-cto-pilot');
const { startCooling } = require('./lib/m1-cooling-daemon');

// --- Boot ---
log('--- MISSION CONTROL v25.0 ONLINE (Dual-Mode Brain) ---');

spawnBrain();
startWatching();
startAutoCTO();
startCooling();

log('🧠 Persistent Brain: CC CLI stays alive across missions');
log('❄️ M1 Cooling Daemon ACTIVE');
log('🧠 Self-CTO Auto-Pilot ACTIVE');

// --- Graceful Shutdown ---
['SIGTERM', 'SIGINT'].forEach(sig => {
  process.on(sig, () => {
    log(`Received ${sig} — shutting down`);
    killBrain();
    process.exit(0);
  });
});
