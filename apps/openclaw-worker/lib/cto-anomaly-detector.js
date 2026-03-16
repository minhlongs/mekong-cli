'use strict';

/**
 * cto-anomaly-detector.js — Detects factory dispatch anomalies
 *
 * Anomalies: dispatch loops, rising error rate, pane starvation,
 * context exhaustion patterns. Returns severity: ok|warn|critical.
 */

const fs = require('fs');
const DISPATCH_HISTORY = '/tmp/factory-dispatch-history.log';
const METRICS_FILE = '/tmp/factory-metrics.log';

/**
 * Detect all anomalies from metrics and dispatch history.
 * @returns {{ severity: string, anomalies: Array<{type, severity, message}> }}
 */
function detectAnomalies() {
  const anomalies = [];

  // 1. Dispatch loops: same hash >3x in history
  if (fs.existsSync(DISPATCH_HISTORY)) {
    const lines = fs.readFileSync(DISPATCH_HISTORY, 'utf-8').trim().split('\n');
    const hashCounts = {};
    const cutoff = Date.now() / 1000 - 7200; // last 2h
    for (const line of lines) {
      const parts = line.split('|');
      if (parts.length < 4) continue;
      if (parseInt(parts[0]) < cutoff) continue;
      const hash = parts[2];
      hashCounts[hash] = (hashCounts[hash] || 0) + 1;
    }
    const loops = Object.entries(hashCounts).filter(([, c]) => c > 3);
    if (loops.length > 0) {
      anomalies.push({
        type: 'dispatch_loop',
        severity: 'critical',
        message: `${loops.length} command(s) dispatched >3x in 2h — possible infinite loop`,
      });
    }
  }

  // 2-4: Metrics-based anomalies
  if (fs.existsSync(METRICS_FILE)) {
    const lines = fs.readFileSync(METRICS_FILE, 'utf-8').trim().split('\n');
    const recent = lines.slice(-50); // last 50 events

    // 2. Rising error rate: >40% of last 50 events are errors/timeouts
    const errors = recent.filter(l => /command_timeout|crash|error/.test(l)).length;
    const errorRate = recent.length > 0 ? errors / recent.length : 0;
    if (errorRate > 0.4) {
      anomalies.push({
        type: 'high_error_rate',
        severity: 'critical',
        message: `Error rate ${Math.round(errorRate * 100)}% in last 50 events (>40% threshold)`,
      });
    } else if (errorRate > 0.2) {
      anomalies.push({
        type: 'elevated_error_rate',
        severity: 'warn',
        message: `Error rate ${Math.round(errorRate * 100)}% in last 50 events (>20%)`,
      });
    }

    // 3. Pane starvation: one pane >80% of dispatches
    const paneCounts = {};
    const dispatchLines = recent.filter(l => l.includes('dispatch'));
    for (const l of dispatchLines) {
      const pane = (l.split('|')[2] || '').trim();
      if (pane) paneCounts[pane] = (paneCounts[pane] || 0) + 1;
    }
    const total = dispatchLines.length;
    for (const [pane, count] of Object.entries(paneCounts)) {
      if (total > 5 && count / total > 0.8) {
        anomalies.push({
          type: 'pane_starvation',
          severity: 'warn',
          message: `${pane} handles ${Math.round(count / total * 100)}% of dispatches — other panes starved`,
        });
      }
    }

    // 4. Context exhaustion: multiple respawns in short window
    const respawns = recent.filter(l => l.includes('respawn')).length;
    if (respawns > 5) {
      anomalies.push({
        type: 'context_exhaustion',
        severity: 'critical',
        message: `${respawns} respawns in recent events — possible context limit loop`,
      });
    }
  }

  // Overall severity
  const hasCritical = anomalies.some(a => a.severity === 'critical');
  const hasWarn = anomalies.some(a => a.severity === 'warn');
  const severity = hasCritical ? 'critical' : hasWarn ? 'warn' : 'ok';

  return { severity, anomalies };
}

module.exports = { detectAnomalies };
