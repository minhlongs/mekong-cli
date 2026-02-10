/**
 * Mission Recovery Helpers — Model failover & context overflow handling
 *
 * Extracted from brain-process-manager.js to keep files < 200 lines.
 * Used by runMissionDirect() for automatic retry on recoverable errors.
 */

const config = require('../config');

const FALLBACK_MODELS = {
  antigravity: 'claude-sonnet-4-20250514',
  qwen: 'qwen-max',
};

const MODEL_ERROR_PATTERNS = [
  /\b400\b/,
  /model_not_found/i,
  /overloaded/i,
  /invalid_model/i,
  /model.*unavailable/i,
];

const CONTEXT_OVERFLOW_PATTERNS = [
  /context.*overflow/i,
  /context.*too\s+long/i,
  /token\s+limit/i,
  /maximum\s+context/i,
  /prompt.*too\s+long/i,
];

const TRUNCATED_PROMPT_LENGTH = 8000;

/**
 * Check if error output indicates a model-related failure (HTTP 400, etc.)
 */
function isModelError(output) {
  return MODEL_ERROR_PATTERNS.some((pat) => pat.test(output));
}

/**
 * Check if error output indicates context overflow
 */
function isContextOverflow(output) {
  return CONTEXT_OVERFLOW_PATTERNS.some((pat) => pat.test(output));
}

/**
 * Get the fallback model name for the current engine.
 */
function getFallbackModel() {
  return FALLBACK_MODELS[config.ENGINE] || FALLBACK_MODELS.antigravity;
}

/**
 * Truncate prompt to fit within context limits.
 * Keeps the first TRUNCATED_PROMPT_LENGTH chars to preserve intent.
 */
function truncatePrompt(prompt) {
  if (prompt.length <= TRUNCATED_PROMPT_LENGTH) return prompt;
  return prompt.slice(0, TRUNCATED_PROMPT_LENGTH) + '\n\n[TRUNCATED — original prompt exceeded context limit]';
}

/**
 * Determine recovery action from mission failure output.
 * Returns: { action: 'model_failover' | 'context_truncate' | null, ... }
 */
function diagnoseFailure(output) {
  if (isModelError(output)) {
    return { action: 'model_failover', model: getFallbackModel() };
  }
  if (isContextOverflow(output)) {
    return { action: 'context_truncate' };
  }
  return { action: null };
}

module.exports = {
  diagnoseFailure,
  getFallbackModel,
  truncatePrompt,
  TRUNCATED_PROMPT_LENGTH,
};
