'use strict';

/**
 * factory-throughput-optimizer.js — Adaptive dispatch interval tuning
 *
 * Reads factory-metrics.log to calculate avg response time per pane,
 * then recommends optimal dispatch intervals. Faster panes = shorter cooldown.
 *
 * Also provides workforce status by combining:
 * - doanh-trai-registry.js (division structure)
 * - factory-metrics.log (throughput data)
 * - factory-roi-calculator.js (ROI scores)
 * - detect_project_state (from filesystem)
 */

const fs = require('fs');
const path = require('path');

const METRICS_FILE = '/tmp/factory-metrics.log';
const MEKONG_DIR = process.env.MEKONG_DIR || path.join(process.env.HOME || '', 'mekong-cli');

/**
 * Calculate avg response time per pane from metrics.
 * @returns {Object<string, {avgDuration: number, dispatches: number, successes: number}>}
 */
function getPaneThroughput() {
  if (!fs.existsSync(METRICS_FILE)) return {};

  const lines = fs.readFileSync(METRICS_FILE, 'utf-8').trim().split('\n');
  const panes = {};

  for (const line of lines) {
    const parts = line.split('|').map(s => s.trim());
    if (parts.length < 6) continue;

    const pane = parts[2]; // e.g., "P0"
    const event = parts[1];
    const duration = parseInt(parts[5]) || 0;

    if (!panes[pane]) panes[pane] = { totalDuration: 0, count: 0, dispatches: 0, successes: 0 };

    if (event === 'dispatch') panes[pane].dispatches++;
    if (event === 'command_complete') {
      panes[pane].successes++;
      if (duration > 0) {
        panes[pane].totalDuration += duration;
        panes[pane].count++;
      }
    }
  }

  const result = {};
  for (const [pane, data] of Object.entries(panes)) {
    result[pane] = {
      avgDuration: data.count > 0 ? Math.round(data.totalDuration / data.count) : 0,
      dispatches: data.dispatches,
      successes: data.successes,
      successRate: data.dispatches > 0 ? Math.round(data.successes / data.dispatches * 100) : 0,
    };
  }

  return result;
}

/**
 * Recommend cooldown interval per pane based on throughput.
 * Fast panes (avg < 120s) get 120s cooldown.
 * Medium panes (120-300s) get 180s cooldown.
 * Slow panes (> 300s) get 300s cooldown.
 * @returns {Object<string, number>} pane → recommended cooldown in seconds
 */
function getRecommendedCooldowns() {
  const throughput = getPaneThroughput();
  const cooldowns = {};

  for (const [pane, data] of Object.entries(throughput)) {
    if (data.avgDuration === 0) {
      cooldowns[pane] = 180; // default
    } else if (data.avgDuration < 120) {
      cooldowns[pane] = 120; // fast worker
    } else if (data.avgDuration < 300) {
      cooldowns[pane] = 180; // medium
    } else {
      cooldowns[pane] = 300; // slow
    }
  }

  return cooldowns;
}

/**
 * Detect project state from filesystem (mirrors factory-loop.sh logic).
 * @param {string} dir - Relative path from mekong-cli root
 * @returns {string} empty|needs_install|scaffolded|deployed
 */
function detectProjectState(dir) {
  const fullDir = path.join(MEKONG_DIR, dir);

  if (!fs.existsSync(fullDir)) return 'empty';

  const hasSrc = fs.existsSync(path.join(fullDir, 'src'));
  const hasApp = fs.existsSync(path.join(fullDir, 'app'));
  if (!hasSrc && !hasApp) return 'empty';

  if (!fs.existsSync(path.join(fullDir, 'node_modules'))) return 'needs_install';

  const hasOut = fs.existsSync(path.join(fullDir, 'out'));
  const hasNext = fs.existsSync(path.join(fullDir, '.next'));
  const hasDist = fs.existsSync(path.join(fullDir, 'dist'));
  if (hasOut || hasNext || hasDist) return 'deployed';

  return 'scaffolded';
}

/**
 * Get full workforce status for /cto-workforce command.
 * @returns {{ panes: Array, divisions: number, totalFiles: number }}
 */
function getWorkforceStatus() {
  // Pane config (hardcoded to match factory-loop.sh)
  const paneConfig = [
    { idx: 0, project: 'sophia-proposal', dir: 'apps/sophia-proposal', name: 'Sophia AI Video Factory' },
    { idx: 1, project: 'well', dir: 'apps/well', name: 'WellNexus Healthcare B2B' },
  ];

  const throughput = getPaneThroughput();
  const cooldowns = getRecommendedCooldowns();

  const panes = paneConfig.map(p => {
    const paneKey = `P${p.idx}`;
    const tp = throughput[paneKey] || { avgDuration: 0, dispatches: 0, successes: 0, successRate: 0 };
    return {
      ...p,
      state: detectProjectState(p.dir),
      throughput: tp,
      recommendedCooldown: cooldowns[paneKey] || 180,
    };
  });

  // Count divisions from doanh-trai-registry
  let divisions = 0;
  let totalFiles = 0;
  try {
    const registry = require('./doanh-trai-registry');
    if (registry.DIVISIONS) {
      divisions = Object.keys(registry.DIVISIONS).length;
      totalFiles = Object.values(registry.DIVISIONS).reduce((sum, d) => sum + (d.files || []).length, 0);
    }
  } catch (e) {
    // Registry not available
  }

  return { panes, divisions, totalFiles };
}

module.exports = {
  getPaneThroughput,
  getRecommendedCooldowns,
  detectProjectState,
  getWorkforceStatus,
};
