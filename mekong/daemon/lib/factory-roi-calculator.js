'use strict';

/**
 * factory-roi-calculator.js
 * Reads /tmp/factory-metrics.log and calculates ROI score per project.
 * ROI = success_count / total_dispatches * 100, weighted by avg duration.
 * Lower ROI = project needs more help = higher dispatch priority.
 */

const fs = require('fs');
const path = require('path');

const METRICS_FILE = '/tmp/factory-metrics.log';
const BRAIN_STATE_FILE = path.join(__dirname, '..', 'brain-learning-state.json');

/**
 * Parse factory-metrics.log into structured events.
 * Format: ISO_TIMESTAMP | event | pane | project | status | duration | command
 * @returns {Array<{ts: string, event: string, pane: string, project: string, status: string, duration: number, command: string}>}
 */
function parseMetrics() {
  if (!fs.existsSync(METRICS_FILE)) return [];

  const lines = fs.readFileSync(METRICS_FILE, 'utf-8').trim().split('\n');
  return lines.map(line => {
    const parts = line.split('|').map(s => s.trim());
    if (parts.length < 7) return null;
    return {
      ts: parts[0],
      event: parts[1],
      pane: parts[2],
      project: parts[3],
      status: parts[4],
      duration: parseInt(parts[5]) || 0,
      command: parts[6],
    };
  }).filter(Boolean);
}

/**
 * Calculate ROI scores per project.
 * @returns {Object<string, {dispatches: number, successes: number, timeouts: number, crashes: number, avgDuration: number, roi: number}>}
 */
function calculateProjectROI() {
  const events = parseMetrics();
  const projects = {};

  for (const e of events) {
    if (e.project === '-') continue;
    if (!projects[e.project]) {
      projects[e.project] = { dispatches: 0, successes: 0, timeouts: 0, crashes: 0, totalDuration: 0, durationCount: 0 };
    }
    const p = projects[e.project];

    if (e.event === 'dispatch') p.dispatches++;
    if (e.event === 'command_complete' && e.status === 'success') {
      p.successes++;
      p.totalDuration += e.duration;
      p.durationCount++;
    }
    if (e.event === 'command_timeout') p.timeouts++;
    if (e.event === 'crash') p.crashes++;
  }

  // Calculate ROI and avg duration
  const result = {};
  for (const [name, p] of Object.entries(projects)) {
    const roi = p.dispatches > 0 ? Math.round((p.successes / p.dispatches) * 100) : 0;
    const avgDuration = p.durationCount > 0 ? Math.round(p.totalDuration / p.durationCount) : 0;
    result[name] = { ...p, avgDuration, roi };
    delete result[name].totalDuration;
    delete result[name].durationCount;
  }

  return result;
}

/**
 * Get projects sorted by ROI (lowest first = needs most help).
 * @returns {Array<{project: string, roi: number, dispatches: number}>}
 */
function getProjectsByPriority() {
  const scores = calculateProjectROI();
  return Object.entries(scores)
    .map(([project, data]) => ({ project, ...data }))
    .sort((a, b) => a.roi - b.roi);
}

// ═══════════════════════════════════════════════════════════════
// BRAIN LEARNING STATE — Persists command effectiveness across restarts
// ═══════════════════════════════════════════════════════════════

/**
 * Load brain learning state from disk.
 * @returns {{ commandEffectiveness: Object, projectStates: Object, lastUpdated: string }}
 */
function loadBrainState() {
  try {
    if (fs.existsSync(BRAIN_STATE_FILE)) {
      return JSON.parse(fs.readFileSync(BRAIN_STATE_FILE, 'utf-8'));
    }
  } catch (e) { /* corrupt file, reset */ }
  return { commandEffectiveness: {}, projectStates: {}, lastUpdated: new Date().toISOString() };
}

/**
 * Save brain learning state to disk.
 * @param {Object} state
 */
function saveBrainState(state) {
  state.lastUpdated = new Date().toISOString();
  const tmp = `${BRAIN_STATE_FILE}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(state, null, 2));
  fs.renameSync(tmp, BRAIN_STATE_FILE);
}

/**
 * Record command outcome for learning.
 * Tracks which commands work best for which project states.
 * @param {string} project - Project name
 * @param {string} projectState - empty|scaffolded|deployed
 * @param {string} command - Command dispatched (first 60 chars)
 * @param {boolean} success - Whether it succeeded
 * @param {number} durationSec - Duration in seconds
 */
function recordCommandOutcome(project, projectState, command, success, durationSec) {
  const state = loadBrainState();
  const cmdKey = command.replace(/\s+/g, ' ').slice(0, 60);

  // Track per-command effectiveness
  if (!state.commandEffectiveness[cmdKey]) {
    state.commandEffectiveness[cmdKey] = { total: 0, success: 0, avgDuration: 0 };
  }
  const ce = state.commandEffectiveness[cmdKey];
  ce.total++;
  if (success) ce.success++;
  ce.avgDuration = Math.round((ce.avgDuration * (ce.total - 1) + durationSec) / ce.total);

  // Track per-project best commands
  const psKey = `${project}:${projectState}`;
  if (!state.projectStates[psKey]) {
    state.projectStates[psKey] = { bestCommands: [], worstCommands: [] };
  }
  const ps = state.projectStates[psKey];
  if (success && !ps.bestCommands.includes(cmdKey)) {
    ps.bestCommands.push(cmdKey);
    if (ps.bestCommands.length > 5) ps.bestCommands.shift();
  }
  if (!success && !ps.worstCommands.includes(cmdKey)) {
    ps.worstCommands.push(cmdKey);
    if (ps.worstCommands.length > 5) ps.worstCommands.shift();
  }

  saveBrainState(state);
}

/**
 * Get best command for a project+state combination.
 * @param {string} project
 * @param {string} projectState
 * @returns {string|null} Best command or null
 */
function getBestCommand(project, projectState) {
  const state = loadBrainState();
  const psKey = `${project}:${projectState}`;
  const ps = state.projectStates[psKey];
  if (!ps || !ps.bestCommands.length) return null;
  return ps.bestCommands[ps.bestCommands.length - 1]; // Most recent best
}

/**
 * Check if a command should be avoided for this project+state.
 * @param {string} project
 * @param {string} projectState
 * @param {string} command
 * @returns {boolean}
 */
function shouldAvoidCommand(project, projectState, command) {
  const state = loadBrainState();
  const psKey = `${project}:${projectState}`;
  const ps = state.projectStates[psKey];
  if (!ps) return false;
  const cmdKey = command.replace(/\s+/g, ' ').slice(0, 60);
  return ps.worstCommands.includes(cmdKey);
}

/**
 * Get dashboard data: brain health summary.
 * @returns {{ projectROI: Object, brainState: Object, metricsLineCount: number }}
 */
function getDashboardData() {
  const projectROI = calculateProjectROI();
  const brainState = loadBrainState();
  let metricsLineCount = 0;
  try {
    if (fs.existsSync(METRICS_FILE)) {
      metricsLineCount = fs.readFileSync(METRICS_FILE, 'utf-8').trim().split('\n').length;
    }
  } catch (e) {}
  return {
    projectROI,
    brainState: {
      commandsLearned: Object.keys(brainState.commandEffectiveness).length,
      projectStatesTracked: Object.keys(brainState.projectStates).length,
      lastUpdated: brainState.lastUpdated,
    },
    metricsLineCount,
  };
}

module.exports = {
  parseMetrics,
  calculateProjectROI,
  getProjectsByPriority,
  loadBrainState,
  saveBrainState,
  recordCommandOutcome,
  getBestCommand,
  shouldAvoidCommand,
  getDashboardData,
};
