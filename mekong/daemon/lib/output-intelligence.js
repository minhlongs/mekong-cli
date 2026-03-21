'use strict';

/**
 * output-intelligence.js — Smart CC CLI output classifier
 *
 * Detects output patterns from tmux pane captures to classify what
 * a command actually produced: code, tests, builds, or just reports.
 *
 * Categories:
 *   code_written  — src/ files created/modified (Write/Edit tool calls)
 *   test_passed   — test suite ran and passed
 *   build_success — npm run build succeeded
 *   deploy_success — deployed to production
 *   analysis_only — only produced reports/analysis (no code)
 *   error         — command failed with errors
 *   timeout       — command timed out
 *   unknown       — couldn't classify
 */

const PATTERNS = {
  code_written: [
    /Write\(.+\.tsx?\)/i,
    /Edit\(.+\.tsx?\)/i,
    /Write\(.+\.jsx?\)/i,
    /Write\(.+\.py\)/i,
    /Created.*src\//i,
    /wrote.*\.ts/i,
    /file.*created/i,
    /saved.*src\//i,
  ],
  test_passed: [
    /Tests?:?\s*\d+\s*passed/i,
    /test.*passed/i,
    /✅.*test/i,
    /PASS\s+src\//i,
    /All tests passed/i,
    /vitest.*passed/i,
    /jest.*passed/i,
  ],
  build_success: [
    /build.*success/i,
    /build.*complete/i,
    /✅.*build/i,
    /compiled.*successfully/i,
    /exit code 0/i,
    /Built in \d/i,
  ],
  deploy_success: [
    /deploy.*success/i,
    /deployed to/i,
    /production.*ready/i,
    /✅.*deploy/i,
    /wrangler.*deploy/i,
    /vercel.*ready/i,
  ],
  analysis_only: [
    /report saved/i,
    /analysis complete/i,
    /saved.*report/i,
    /saved.*\.md/i,
    /terrain.*score/i,
    /thesis.*updated/i,
    /momentum.*score/i,
    /content.*plan/i,
    /market.*analysis/i,
  ],
  error: [
    /error:/i,
    /failed:/i,
    /exception/i,
    /traceback/i,
    /FAIL\s/i,
    /Build failed/i,
    /❌/,
    /fatal:/i,
  ],
};

/**
 * Classify CC CLI output into categories.
 * Returns array of detected categories, ordered by confidence.
 * @param {string} output - tmux pane captured output (last 45 lines)
 * @returns {{ primary: string, categories: string[], scores: Object<string, number> }}
 */
function classifyOutput(output) {
  if (!output || output.trim().length < 10) {
    return { primary: 'unknown', categories: ['unknown'], scores: {} };
  }

  const scores = {};

  for (const [category, patterns] of Object.entries(PATTERNS)) {
    let score = 0;
    for (const pattern of patterns) {
      const matches = output.match(new RegExp(pattern.source, 'gi'));
      if (matches) {
        score += matches.length;
      }
    }
    if (score > 0) scores[category] = score;
  }

  // Sort by score descending
  const sorted = Object.entries(scores)
    .sort((a, b) => b[1] - a[1])
    .map(([cat]) => cat);

  if (sorted.length === 0) {
    return { primary: 'unknown', categories: ['unknown'], scores: {} };
  }

  // Error takes precedence if present (even with other signals)
  if (scores.error && scores.error >= 2) {
    return { primary: 'error', categories: sorted, scores };
  }

  return { primary: sorted[0], categories: sorted, scores };
}

/**
 * Quick check: did this output produce real code?
 * @param {string} output
 * @returns {boolean}
 */
function producedCode(output) {
  const result = classifyOutput(output);
  return result.categories.includes('code_written');
}

/**
 * Quick check: was this just analysis/reports?
 * @param {string} output
 * @returns {boolean}
 */
function wasAnalysisOnly(output) {
  const result = classifyOutput(output);
  return result.primary === 'analysis_only' && !result.categories.includes('code_written');
}

/**
 * Generate a summary string for logging.
 * @param {string} output
 * @returns {string} e.g., "code_written(3) + test_passed(1)"
 */
function summarize(output) {
  const result = classifyOutput(output);
  if (result.primary === 'unknown') return 'unknown';
  return Object.entries(result.scores)
    .sort((a, b) => b[1] - a[1])
    .map(([cat, score]) => `${cat}(${score})`)
    .join(' + ');
}

module.exports = { classifyOutput, producedCode, wasAnalysisOnly, summarize };
