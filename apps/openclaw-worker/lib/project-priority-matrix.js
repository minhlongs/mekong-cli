'use strict';

/**
 * project-priority-matrix.js — Ranks projects by business impact
 *
 * Combines: ROI from factory-metrics.log + code maturity from filesystem
 * Higher score = higher priority for CTO dispatch.
 *
 * Score formula:
 *   maturity_score (0-40) + roi_score (0-30) + activity_score (0-30)
 *
 * Maturity: deployed=40, scaffolded=25, needs_install=15, empty=5
 * ROI: success_rate * 30
 * Activity: min(dispatches, 30) — more activity = more investment
 */

const path = require('path');
const { detectProjectState } = require('./factory-throughput-optimizer');
const { calculateProjectROI } = require('./factory-roi-calculator');

const MATURITY_SCORES = {
  deployed: 40,
  scaffolded: 25,
  needs_install: 15,
  empty: 5,
};

// All known projects with their directories
const PROJECT_REGISTRY = [
  { name: 'sophia-proposal', dir: 'apps/sophia-proposal', tier: 'revenue' },
  { name: 'well', dir: 'apps/well', tier: 'revenue' },
  { name: 'algo-trader', dir: 'apps/algo-trader', tier: 'revenue' },
  { name: 'mekong-cli', dir: '.', tier: 'core' },
  { name: 'openclaw-worker', dir: 'apps/openclaw-worker', tier: 'core' },
  { name: 'agencyos-web', dir: 'apps/agencyos-web', tier: 'network' },
  { name: 'raas-gateway', dir: 'apps/raas-gateway', tier: 'infra' },
];

/**
 * Calculate priority score for a single project.
 * @param {string} name
 * @param {string} dir
 * @returns {{ name, dir, state, maturity, roi, activity, total, tier }}
 */
function scoreProject(name, dir) {
  const state = detectProjectState(dir);
  const maturity = MATURITY_SCORES[state] || 5;

  const allROI = calculateProjectROI();
  const projROI = allROI[name] || { roi: 0, dispatches: 0, successes: 0 };

  const roi = Math.round((projROI.roi / 100) * 30); // 0-30
  const activity = Math.min(projROI.dispatches, 30); // 0-30

  return {
    name,
    dir,
    state,
    tier: PROJECT_REGISTRY.find(p => p.name === name)?.tier || 'other',
    maturity,
    roi,
    activity,
    total: maturity + roi + activity,
    dispatches: projROI.dispatches,
    successRate: projROI.roi,
  };
}

/**
 * Get all projects ranked by priority (highest first).
 * @returns {Array<{name, dir, state, total, tier, maturity, roi, activity}>}
 */
function getProjectMatrix() {
  return PROJECT_REGISTRY
    .map(p => scoreProject(p.name, p.dir))
    .sort((a, b) => b.total - a.total);
}

/**
 * Get top N projects to focus on.
 * @param {number} n
 * @returns {Array}
 */
function getTopProjects(n = 3) {
  return getProjectMatrix().slice(0, n);
}

module.exports = { scoreProject, getProjectMatrix, getTopProjects, PROJECT_REGISTRY };
