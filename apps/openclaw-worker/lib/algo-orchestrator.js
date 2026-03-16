'use strict';

/**
 * algo-orchestrator.js — Algorithm discovery and health monitoring
 *
 * Scans project src/algorithms/ directories for TypeScript algorithm modules.
 * Reports on algorithm coverage per project: which algos exist, have tests,
 * lines of code, and export count.
 *
 * Feeds into project-priority-matrix for algorithm-aware scoring.
 */

const fs = require('fs');
const path = require('path');

const MEKONG_DIR = process.env.MEKONG_DIR || path.join(process.env.HOME || '', 'mekong-cli');

// Known algorithm types the factory generates
const ALGO_TYPES = [
  'scoring-engine',
  'pricing-engine',
  'recommendation-engine',
  'revenue-forecast',
  'unit-economics',
  'ab-test-engine',
  'feature-prioritizer',
  'health-score',
  'lead-qualifier',
  'moat-analyzer',
];

/**
 * Scan a project for algorithm files.
 * @param {string} projectDir - Relative path from mekong-cli root
 * @returns {{ total: number, withTests: number, totalLines: number, algorithms: Array }}
 */
function scanAlgorithms(projectDir) {
  const algoDir = path.join(MEKONG_DIR, projectDir, 'src', 'algorithms');
  const algorithms = [];

  if (!fs.existsSync(algoDir)) {
    return { total: 0, withTests: 0, totalLines: 0, algorithms };
  }

  for (const algoType of ALGO_TYPES) {
    const tsFile = path.join(algoDir, `${algoType}.ts`);
    const testFile = path.join(algoDir, `${algoType}.test.ts`);

    if (fs.existsSync(tsFile)) {
      const content = fs.readFileSync(tsFile, 'utf-8');
      const lines = content.split('\n').length;
      const exports = (content.match(/export/g) || []).length;
      const hasTest = fs.existsSync(testFile);

      algorithms.push({
        name: algoType,
        lines,
        exports,
        hasTest,
        path: `${projectDir}/src/algorithms/${algoType}.ts`,
      });
    }
  }

  const total = algorithms.length;
  const withTests = algorithms.filter(a => a.hasTest).length;
  const totalLines = algorithms.reduce((sum, a) => sum + a.lines, 0);

  return { total, withTests, totalLines, algorithms };
}

/**
 * Scan all known projects for algorithms.
 * @returns {Object<string, {total, withTests, totalLines, algorithms}>}
 */
function scanAllProjects() {
  const projects = ['apps/sophia-proposal', 'apps/well', 'apps/algo-trader'];
  const results = {};

  for (const dir of projects) {
    const name = path.basename(dir);
    results[name] = scanAlgorithms(dir);
  }

  return results;
}

/**
 * Calculate algorithm maturity score (0-20) for project-priority-matrix.
 * @param {string} projectDir
 * @returns {number} 0-20 score
 */
function getAlgoScore(projectDir) {
  const scan = scanAlgorithms(projectDir);
  if (scan.total === 0) return 0;

  // Score: coverage (0-10) + test coverage (0-10)
  const coverage = Math.min(scan.total, 10); // 1 point per algo, max 10
  const testCoverage = scan.total > 0
    ? Math.round((scan.withTests / scan.total) * 10)
    : 0;

  return coverage + testCoverage;
}

module.exports = { scanAlgorithms, scanAllProjects, getAlgoScore, ALGO_TYPES };
