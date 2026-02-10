#!/usr/bin/env node
/**
 * TOM HUM (OpenClaw) Task Watcher — v25.1 DAEMON MODE
 *
 * Thin orchestrator: imports modules, wires lifecycle, handles shutdown.
 * Runs FOREVER as a daemon — never exits after queue empties.
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
const { startWatching, stopWatching } = require('./lib/task-queue');
const { startAutoCTO, stopAutoCTO } = require('./lib/auto-cto-pilot');
const { startCooling, stopCooling } = require('./lib/m1-cooling-daemon');

// --- Boot ---
log('--- MISSION CONTROL v25.1 ONLINE (Daemon Mode) ---');

spawnBrain();
startWatching();
startAutoCTO();
startCooling();

log('Persistent Brain + File Watcher + Auto-CTO + M1 Cooling ACTIVE');

// --- Keepalive: prevent Node from exiting when event loop is idle ---
const keepalive = setInterval(() => {}, 60000);

// --- Unhandled error protection: log but do NOT crash the daemon ---
process.on('uncaughtException', (err) => {
  log(`UNCAUGHT EXCEPTION (daemon stays alive): ${err.stack || err.message}`);
});
process.on('unhandledRejection', (reason) => {
  log(`UNHANDLED REJECTION (daemon stays alive): ${reason}`);
});

// --- Graceful Shutdown ---
let shuttingDown = false;

function shutdown(sig) {
  if (shuttingDown) return;
  shuttingDown = true;
  log(`Received ${sig} — shutting down gracefully`);
  clearInterval(keepalive);
  stopWatching();
  stopAutoCTO();
  stopCooling();
  killBrain();
  log('All modules stopped. Goodbye.');
  process.exit(0);
}

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));
