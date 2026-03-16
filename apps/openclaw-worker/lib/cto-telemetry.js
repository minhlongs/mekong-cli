'use strict';

/**
 * cto-telemetry.js — Structured telemetry for CTO factory system
 * Reads factory-metrics.log and brain-learning-state.json,
 * exports unified telemetry to /tmp/cto-telemetry.json
 */

const fs = require('fs');
const path = require('path');

const METRICS_FILE = '/tmp/factory-metrics.log';
const TELEMETRY_FILE = '/tmp/cto-telemetry.json';
const BRAIN_FILE = path.join(__dirname, '..', 'brain-learning-state.json');

function parseMetricsLines() {
  if (!fs.existsSync(METRICS_FILE)) return [];
  return fs.readFileSync(METRICS_FILE, 'utf-8').trim().split('\n').map(line => {
    const p = line.split('|').map(s => s.trim());
    if (p.length < 6) return null;
    return { ts: p[0], event: p[1], pane: p[2], project: p[3], status: p[4], duration: parseInt(p[5]) || 0 };
  }).filter(Boolean);
}

/**
 * Generate full telemetry snapshot.
 * @returns {Object} telemetry data
 */
function generateTelemetry() {
  const events = parseMetricsLines();
  const now = new Date().toISOString();

  // Dispatch stats
  const dispatches = events.filter(e => e.event === 'dispatch');
  const completions = events.filter(e => e.event === 'command_complete');
  const timeouts = events.filter(e => e.event === 'command_timeout');
  const crashes = events.filter(e => e.event === 'crash');
  const dedups = events.filter(e => e.event === 'dedup_skip');
  const evolutions = events.filter(e => e.event === 'brain_evolution');

  // Avg dispatch latency (from completions with duration > 0)
  const durations = completions.filter(e => e.duration > 0).map(e => e.duration);
  const avgLatency = durations.length > 0 ? Math.round(durations.reduce((s, d) => s + d, 0) / durations.length) : 0;

  // Pane utilization
  const paneDispatches = {};
  for (const d of dispatches) {
    paneDispatches[d.pane] = (paneDispatches[d.pane] || 0) + 1;
  }

  // Project breakdown
  const projectStats = {};
  for (const e of events) {
    if (e.project === '-') continue;
    if (!projectStats[e.project]) projectStats[e.project] = { dispatches: 0, successes: 0, errors: 0 };
    if (e.event === 'dispatch') projectStats[e.project].dispatches++;
    if (e.status === 'success' || e.status === 'code_written') projectStats[e.project].successes++;
    if (e.event === 'crash' || e.event === 'command_timeout') projectStats[e.project].errors++;
  }

  // Brain state
  let brainStats = { commandsLearned: 0, evolutionEvents: 0, lastUpdated: null };
  try {
    if (fs.existsSync(BRAIN_FILE)) {
      const brain = JSON.parse(fs.readFileSync(BRAIN_FILE, 'utf-8'));
      brainStats.commandsLearned = Object.keys(brain.commandEffectiveness || {}).length;
      brainStats.evolutionEvents = (brain.evolutionLog || []).length;
      brainStats.lastUpdated = brain.lastUpdated;
    }
  } catch (e) {}

  const telemetry = {
    timestamp: now,
    summary: {
      totalEvents: events.length,
      dispatches: dispatches.length,
      completions: completions.length,
      timeouts: timeouts.length,
      crashes: crashes.length,
      dedups: dedups.length,
      avgLatencySeconds: avgLatency,
      successRate: dispatches.length > 0 ? Math.round(completions.length / dispatches.length * 100) : 0,
    },
    paneUtilization: paneDispatches,
    projectStats,
    brain: brainStats,
    evolutions: evolutions.length,
  };

  // Write to file
  fs.writeFileSync(TELEMETRY_FILE, JSON.stringify(telemetry, null, 2));
  return telemetry;
}

module.exports = { generateTelemetry, parseMetricsLines };
