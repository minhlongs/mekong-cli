'use strict';

/**
 * model-router.js — Smart model routing for CTO dispatch
 *
 * Routes tasks to the best model based on complexity and type.
 * Reads PANE_CONFIG from config.js for model assignments.
 */

const MODELS = {
  'qwen3.5-plus': { tier: 'opus', strengths: ['architecture', 'planning', 'complex-debug', 'refactor'], contextWindow: '1M', speed: 'slow' },
  'qwen3-max': { tier: 'sonnet', strengths: ['code-gen', 'analysis', 'review', 'moderate-tasks'], contextWindow: '128K', speed: 'medium' },
  'qwen3-coder-plus': { tier: 'haiku', strengths: ['repetitive-code', 'simple-fix', 'formatting', 'tests'], contextWindow: '128K', speed: 'fast' },
};

const TASK_COMPLEXITY = {
  // Complex → needs strongest model
  complex: [/architect/i, /refactor.*large/i, /redesign/i, /migrate/i, /security.*audit/i, /deep.*debug/i],
  // Medium → balanced model
  medium: [/cook/i, /feature/i, /build/i, /implement/i, /review/i, /analysis/i],
  // Simple → fast model
  simple: [/fix.*lint/i, /format/i, /test/i, /rename/i, /update.*dep/i, /scaffold/i],
};

/**
 * Classify task complexity.
 * @param {string} taskText
 * @returns {'complex'|'medium'|'simple'}
 */
function classifyComplexity(taskText) {
  for (const pattern of TASK_COMPLEXITY.complex) {
    if (pattern.test(taskText)) return 'complex';
  }
  for (const pattern of TASK_COMPLEXITY.simple) {
    if (pattern.test(taskText)) return 'simple';
  }
  return 'medium';
}

/**
 * Recommend best model for a task.
 * @param {string} taskText
 * @returns {{ model: string, tier: string, reason: string }}
 */
function recommendModel(taskText) {
  const complexity = classifyComplexity(taskText);
  switch (complexity) {
    case 'complex':
      return { model: 'qwen3.5-plus', tier: 'opus', reason: 'Complex task needs strongest reasoning' };
    case 'simple':
      return { model: 'qwen3-coder-plus', tier: 'haiku', reason: 'Simple task — fast model sufficient' };
    default:
      return { model: 'qwen3-max', tier: 'sonnet', reason: 'Balanced task — standard model' };
  }
}

/**
 * Recommend best pane for a task based on model assignment.
 * @param {string} taskText
 * @param {Object} paneConfig - From config.js PANE_CONFIG
 * @returns {{ paneIdx: number, model: string, reason: string }}
 */
function recommendPane(taskText, paneConfig) {
  const rec = recommendModel(taskText);
  // Find pane with matching or closest model
  for (const [idx, conf] of Object.entries(paneConfig || {})) {
    if (conf.model === rec.model) {
      return { paneIdx: parseInt(idx), model: rec.model, reason: rec.reason };
    }
  }
  // Fallback: first pane
  return { paneIdx: 0, model: rec.model, reason: `${rec.reason} (no exact pane match)` };
}

/**
 * Get model matrix for /model-matrix command.
 * @returns {Array}
 */
function getModelMatrix() {
  return Object.entries(MODELS).map(([name, info]) => ({
    model: name,
    tier: info.tier,
    speed: info.speed,
    context: info.contextWindow,
    strengths: info.strengths.join(', '),
  }));
}

module.exports = { classifyComplexity, recommendModel, recommendPane, getModelMatrix, MODELS };
