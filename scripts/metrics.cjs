#!/usr/bin/env node
/**
 * metrics.cjs — AARRR Metrics Dashboard for Mekong CLI
 * Reads SQLite ledger + trial data → calculates key metrics
 * Usage: node scripts/metrics.cjs [--json]
 */
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');

const HOME = os.homedir();
const MEKONG_DIR = path.join(HOME, '.mekong');
const TRIAL_FILE = path.join(MEKONG_DIR, 'trial.json');
const LEDGER_FILE = path.join(MEKONG_DIR, 'mcu_ledger.db');

function readJSON(filepath) {
  try { return JSON.parse(fs.readFileSync(filepath, 'utf8')); }
  catch { return null; }
}

function calculateAARRR() {
  const metrics = {
    acquisition: { installs: 0, uniqueUsers: 0, period: '7d' },
    activation: { trialsStarted: 0, configured: 0, conversionRate: 0 },
    retention: { d7: 0, d30: 0, activeUsers: 0 },
    revenue: { mrr: 0, mrrTarget: 99000, subscribers: 0, arpu: 0 },
    referral: { invites: 0, conversion: 0 },
    northStar: { workflowsPerDay: 0, target: 100 },
    score: 0,
  };

  // Calculate from trial data
  const trials = readJSON(TRIAL_FILE);
  if (trials) {
    const users = Object.values(trials);
    metrics.acquisition.installs = users.length;
    metrics.acquisition.uniqueUsers = users.length;

    const active = users.filter(u => !u.expired && u.credits > (u.creditsUsed || 0));
    const configured = users.filter(u => (u.creditsUsed || 0) > 0);

    metrics.activation.trialsStarted = users.length;
    metrics.activation.configured = configured.length;
    metrics.activation.conversionRate = users.length > 0
      ? Math.round((configured.length / users.length) * 100) : 0;

    metrics.retention.activeUsers = active.length;
    const oldUsers = users.filter(u => {
      const days = (Date.now() - new Date(u.startedAt).getTime()) / 86400000;
      return days >= 7;
    });
    const retainedD7 = oldUsers.filter(u => !u.expired);
    metrics.retention.d7 = oldUsers.length > 0
      ? Math.round((retainedD7.length / oldUsers.length) * 100) : 0;

    // Workflows per day (estimate from credits used)
    const totalWorkflows = users.reduce((s, u) => s + (u.creditsUsed || 0), 0);
    const earliest = users.reduce((min, u) =>
      !min || u.startedAt < min ? u.startedAt : min, null);
    if (earliest) {
      const daysSince = Math.max(1, (Date.now() - new Date(earliest).getTime()) / 86400000);
      metrics.northStar.workflowsPerDay = Math.round(totalWorkflows / daysSince);
    }
  }

  // Calculate score (0-100)
  const activationScore = Math.min(25, metrics.activation.conversionRate * 0.5);
  const retentionScore = Math.min(25, metrics.retention.d7 * 0.3);
  const acquisitionScore = Math.min(25, metrics.acquisition.uniqueUsers * 2);
  const northStarScore = metrics.northStar.target > 0
    ? Math.min(25, (metrics.northStar.workflowsPerDay / metrics.northStar.target) * 25) : 0;
  metrics.score = Math.round(activationScore + retentionScore + acquisitionScore + northStarScore);

  return metrics;
}

function renderDashboard(m) {
  const bar = (label, value, max, unit) => {
    const pct = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0;
    const filled = Math.round(pct / 10);
    const empty = 10 - filled;
    return `${label.padEnd(16)} ${String(value).padStart(6)} ${unit || ''} [${'█'.repeat(filled)}${'░'.repeat(empty)}] ${pct}%`;
  };

  console.log(`
╔══════════════════════════════════════════╗
║     MEKONG CLI — AARRR Dashboard        ║
║     ${new Date().toISOString().slice(0, 10)}                          ║
╠══════════════════════════════════════════╣
║ ACQUISITION                              ║
║  ${bar('Installs', m.acquisition.installs, 100, 'users')}
║                                          ║
║ ACTIVATION                               ║
║  ${bar('Trials', m.activation.trialsStarted, 50, 'users')}
║  ${bar('Configured', m.activation.configured, 50, 'users')}
║  Conversion: ${String(m.activation.conversionRate).padStart(3)}%${m.activation.conversionRate >= 20 ? ' ✅' : ' ⚠️'}
║                                          ║
║ RETENTION                                ║
║  ${bar('Active', m.retention.activeUsers, 50, 'users')}
║  ${bar('D7 Retention', m.retention.d7, 100, '%')}
║                                          ║
║ REVENUE                                  ║
║  ${bar('MRR', m.revenue.mrr, m.revenue.mrrTarget, '$')}
║  Target: $${(m.revenue.mrrTarget / 1000).toFixed(1)}K MRR
║                                          ║
║ NORTH STAR                               ║
║  ${bar('Workflows/day', m.northStar.workflowsPerDay, m.northStar.target, 'wf')}
║                                          ║
║ OVERALL SCORE: ${String(m.score).padStart(2)}/100${m.score >= 70 ? ' 🟢' : m.score >= 40 ? ' 🟡' : ' 🔴'}
╚══════════════════════════════════════════╝
`);
}

const m = calculateAARRR();
if (process.argv.includes('--json')) {
  console.log(JSON.stringify(m, null, 2));
} else {
  renderDashboard(m);
}
