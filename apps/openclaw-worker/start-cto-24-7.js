#!/usr/bin/env node
'use strict';

/**
 * 🏯 OpenClaw CTO 24/7 Launcher
 * Starts Auto-CTO Pilot + Self-Healer + Brain Spawn Manager
 * Run: node start-cto-24-7.js
 */

const path = require('path');
process.chdir(path.join(__dirname, '..', '..'));

// Set env defaults
process.env.MEKONG_DIR = process.env.MEKONG_DIR || process.cwd();
process.env.TOM_HUM_LOG = process.env.TOM_HUM_LOG || path.join(process.env.HOME, 'tom_hum_cto.log');

const config = require('./config');

console.log('═══════════════════════════════════════');
console.log('🏯 OpenClaw CTO — 24/7 AUTONOMOUS MODE');
console.log('═══════════════════════════════════════');
console.log(`TMUX: ${config.TMUX_SESSION}`);
console.log(`OPUS: ${config.OPUS_MODEL}`);
console.log(`WORKER: ${config.WORKER_MODEL_NAME}`);
console.log(`FALLBACK: ${config.FALLBACK_MODEL_NAME}`);
console.log(`PANES: P0=${config.PANE_CONFIG[0].project} P1=${config.PANE_CONFIG[1].project} P2=${config.PANE_CONFIG[2].project} P3=${config.PANE_CONFIG[3].project}`);
console.log('═══════════════════════════════════════');

// Ensure task dirs exist
const fs = require('fs');
[config.WATCH_DIR, config.PROCESSED_DIR, config.REJECTED_DIR].forEach(d => {
  if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true });
});

// Start Auto-CTO Pilot (core loop)
const { startAutoCTO } = require('./lib/auto-cto-pilot');

// Start Self-Healer (auto-respawn crashed panes)
let selfHealer;
try {
  selfHealer = require('./lib/self-healer');
  if (selfHealer.startSelfHealer) selfHealer.startSelfHealer();
  console.log('✅ Self-Healer started');
} catch (e) {
  console.log(`⚠️  Self-Healer unavailable: ${e.message}`);
}

// Start Brain Spawn Manager (rate-limited respawns)
let brainSpawn;
try {
  brainSpawn = require('./lib/brain-spawn-manager');
  console.log('✅ Brain Spawn Manager loaded');
} catch (e) {
  console.log(`⚠️  Brain Spawn unavailable: ${e.message}`);
}

// Launch Auto-CTO
startAutoCTO();
console.log('✅ Auto-CTO Pilot started — 24/7 autonomous');
console.log('Press Ctrl+C to stop');

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 CTO shutting down...');
  const { stopAutoCTO } = require('./lib/auto-cto-pilot');
  stopAutoCTO();
  process.exit(0);
});

process.on('uncaughtException', (err) => {
  console.error(`🚨 Uncaught: ${err.message}`);
  fs.appendFileSync(process.env.TOM_HUM_LOG, `[${new Date().toISOString()}] UNCAUGHT: ${err.stack}\n`);
});
