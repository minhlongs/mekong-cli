/**
 * model-router.cjs — Intelligent Model Routing Engine
 *
 * Routes requests between DeepSeek V4 Flash (Executor) and V4 Pro (Architect)
 * based on task complexity analysis and failure context.
 *
 * Architecture:
 *   - Always default to Flash (85-95% of requests)
 *   - Escalate to Pro only when complexity exceeds threshold
 *   - Track failures for auto-escalation on retry
 *   - Never start with Pro unless explicitly requested
 *
 * Usage:
 *   const router = require('./model-router.cjs');
 *   const decision = router.shouldEscalate('Refactor the auth module');
 *   // → { escalate: false, tier: 'flash', score: 0, reason: null }
 *
 *   const decision = router.shouldEscalate('Design the database schema');
 *   // → { escalate: true, tier: 'pro', score: 12, reason: 'schema-change' }
 *
 * @module model-router
 */
'use strict';

const config = require('./model-router-config.cjs');
const { ESCALATION_SIGNALS, THRESHOLDS, TIERS, COST_LADDER } = config;
// TASK_MODEL_MAP and MODEL_SUGGESTION_THRESHOLD removed — no China models

// Cross-process failure store — shared across hook invocations
const failureStore = require('./flash-failure-store.cjs');

// ═════════════════════════════════════════════════════════════════════════════
// WEIGHT MAP
// ═════════════════════════════════════════════════════════════════════════════

const SIGNAL_WEIGHTS = Object.freeze({
  exact:   10,
  strong:   7,
  pattern:  5,
  weak:     2,
});

// ═════════════════════════════════════════════════════════════════════════════
// ANALYSIS CACHE
// ═════════════════════════════════════════════════════════════════════════════

/**
 * In-memory failure tracking. Resets on session restart.
 * Keyed by task signature (first ~80 chars of prompt).
 */
const failureTracker = new Map();

// ═════════════════════════════════════════════════════════════════════════════
// PROMPT ANALYSIS
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Analyze a user prompt against escalation signals.
 *
 * Returns a structured analysis with matched signals, their weights,
 * and the cumulative complexity score.
 *
 * @param {string} prompt - User's request text
 * @returns {{ signals: Array<{label:string, weight:number}>, totalScore: number }}
 */
function analyzePrompt(prompt) {
  if (!prompt || typeof prompt !== 'string') {
    return { signals: [], totalScore: 0 };
  }

  const matched = [];

  // Check exact triggers (weight: 10)
  for (const s of ESCALATION_SIGNALS.exact) {
    if (s.pattern.test(prompt)) {
      matched.push({ label: s.label, weight: SIGNAL_WEIGHTS.exact });
    }
  }

  // Check strong triggers (weight: 7)
  for (const s of ESCALATION_SIGNALS.strong) {
    if (s.pattern.test(prompt)) {
      matched.push({ label: s.label, weight: SIGNAL_WEIGHTS.strong });
    }
  }

  // Check pattern triggers (weight: 5)
  for (const s of ESCALATION_SIGNALS.pattern) {
    if (s.pattern.test(prompt)) {
      matched.push({ label: s.label, weight: SIGNAL_WEIGHTS.pattern });
    }
  }

  // Check weak triggers (weight: 2)
  for (const s of ESCALATION_SIGNALS.weak) {
    if (s.pattern.test(prompt)) {
      matched.push({ label: s.label, weight: SIGNAL_WEIGHTS.weak });
    }
  }

  const totalScore = matched.reduce((sum, s) => sum + s.weight, 0);

  return { signals: matched, totalScore };
}

// ═════════════════════════════════════════════════════════════════════════════
// ROUTING DECISION
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Make a routing decision for a user prompt.
 *
 * @param {string} prompt - User's request text
 * @param {Object} [context] - Additional routing context
 * @param {number} [context.flashRetries=0] - How many times Flash failed on this task
 * @param {boolean} [context.hasCompilationErrors=false] - Unresolved compilation errors
 * @param {boolean} [context.hasTestFailures=false] - Repeated test failures
 * @param {number} [context.fileCount=0] - Number of files touched
 * @param {number} [context.flashConfidence=100] - Flash confidence score (0-100)
 * @returns {{
 *   escalate: boolean,
 *   tier: string,
 *   score: number,
 *   reason: string|null,
 *   signals: Array<{label:string, weight:number}>,
 *   failureContext: Object|null
 * }}
 */
function shouldEscalate(prompt, context = {}) {
  // ═══════════════════════════════════════════════════════════════════════════
  // RULE 1: Always default to Flash unless explicitly requesting Pro
  // ═══════════════════════════════════════════════════════════════════════════

  const explicitPro = /use\s+pro\b/i.test(prompt) || /use\s+architect\b/i.test(prompt);

  // ═══════════════════════════════════════════════════════════════════════════
  // RULE 2: Analyze prompt for complexity signals
  // ═══════════════════════════════════════════════════════════════════════════

  const { signals, totalScore } = analyzePrompt(prompt);

  // ═══════════════════════════════════════════════════════════════════════════
  // RULE 2.5: Check global Flash instability (cross-task failure pattern)
  // When Flash fails on 2+ different tasks, it's a systemic instability —
  // pre-emptively force Pro to avoid showing "Invalid tool parameters".
  // ═══════════════════════════════════════════════════════════════════════════

  const instability = failureStore.isFlashUnstable();
  const forcePro = instability.unstable && !explicitPro;
  // If Flash is globally unstable AND user didn't explicitly request Flash,
  // AND the prompt would normally route to Flash → force Pro silently

  // ═══════════════════════════════════════════════════════════════════════════
  // RULE 3: Check failure-based escalation
  // ═══════════════════════════════════════════════════════════════════════════

  const failureContext = {
    flashRetries: context.flashRetries || 0,
    hasCompilationErrors: context.hasCompilationErrors || false,
    hasTestFailures: context.hasTestFailures || false,
    flashConfidence: context.flashConfidence ?? 100,
    aboveMaxRetries: (context.flashRetries || 0) >= THRESHOLDS.maxFlashRetries,
  };

  let failureScore = 0;
  const failureReasons = [];

  if (failureContext.aboveMaxRetries) {
    failureScore += 10;
    failureReasons.push('repeated-execution-failures');
  }
  if (failureContext.hasCompilationErrors) {
    failureScore += 10;
    failureReasons.push('unresolved-compile-errors');
  }
  if (failureContext.hasTestFailures) {
    failureScore += 8;
    failureReasons.push('repeated-test-failures');
  }
  if (failureContext.flashConfidence < THRESHOLDS.flashConfidenceFloor) {
    failureScore += 7;
    failureReasons.push('flash-confidence-below-threshold');
  }

  const totalWithFailure = totalScore + failureScore;

  // ═══════════════════════════════════════════════════════════════════════════
  // RULE 4: Check file count threshold
  // ═══════════════════════════════════════════════════════════════════════════

  const highFileCount = (context.fileCount || 0) > THRESHOLDS.maxFilesForFlash;

  // ═══════════════════════════════════════════════════════════════════════════
  // DECISION
  // ═══════════════════════════════════════════════════════════════════════════

  const shouldEscalatePro = (
    explicitPro ||
    forcePro ||
    totalWithFailure >= THRESHOLDS.escalationThreshold ||
    highFileCount
  );

  // Build reason string
  const reasons = [];
  if (explicitPro) reasons.push('explicit-pro-request');
  if (forcePro) reasons.push('flash-globally-unstable');
  for (const s of signals) {
    if (!reasons.includes(s.label)) reasons.push(s.label);
  }
  reasons.push(...failureReasons);
  if (highFileCount) reasons.push('high-file-count');

  return {
    escalate: shouldEscalatePro,
    tier: shouldEscalatePro ? 'pro' : 'flash',
    score: totalWithFailure,
    signals,
    failureContext,
    reason: reasons.length > 0 ? reasons.slice(0, 3).join(', ') : null,
    source: shouldEscalatePro
      ? (explicitPro ? 'explicit' : (forcePro ? 'instability' : (totalScore >= THRESHOLDS.escalationThreshold ? 'complexity' : 'failure')))
      : 'default'
  };
}

// ═════════════════════════════════════════════════════════════════════════════
// RETRY TRACKING
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Track a Flash failure for subsequent auto-escalation.
 *
 * @param {string} taskSignature - Unique task identifier (e.g., prompt prefix)
 */
function trackFlashFailure(taskSignature) {
  if (!taskSignature) return;
  const key = taskSignature.slice(0, 80);
  const current = failureTracker.get(key) || 0;
  failureTracker.set(key, current + 1);
}

/**
 * Get the retry count for a task.
 *
 * @param {string} taskSignature - Unique task identifier
 * @returns {number} Number of recorded failures
 */
function getFlashRetries(taskSignature) {
  if (!taskSignature) return 0;
  return failureTracker.get(taskSignature.slice(0, 80)) || 0;
}

/**
 * Clear failure tracking for a task (e.g., after successful execution).
 *
 * @param {string} taskSignature - Unique task identifier
 */
function clearFlashFailures(taskSignature) {
  if (!taskSignature) return;
  failureTracker.delete(taskSignature.slice(0, 80));
}

// ═════════════════════════════════════════════════════════════════════════════
// FULL TASK ROUTING
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Full task routing with failure tracking context.
 *
 * @param {string} prompt - User's request text
 * @param {Object} [context] - Additional routing context
 * @returns {{
 *   tier: string,
 *   model: string,
 *   role: string,
 *   decision: Object,
 *   costStrategy: string
 * }}
 */
function routeTask(prompt, context = {}) {
  // Check failure tracker for this task
  const retries = getFlashRetries(prompt);

  const decision = shouldEscalate(prompt, {
    ...context,
    flashRetries: context.flashRetries ?? retries
  });

  const tierInfo = decision.tier === 'pro' ? TIERS.PRO : TIERS.FLASH;

  // Determine cost strategy step
  let costStep = 'flash';
  if (decision.tier === 'pro') {
    if (decision.source === 'failure') {
      costStep = decision.score >= 20 ? 'pro' : 'flash-retry';
    } else {
      costStep = 'pro';
    }
  }

  return {
    tier: tierInfo.name,
    model: tierInfo.model,
    role: tierInfo.role,
    decision,
    costStep,
    costDescription: COST_LADDER.find(s => s.tier === costStep)?.description || 'unknown'
  };
}

// ═════════════════════════════════════════════════════════════════════════════
// INTEGRATION: WORKFLOW ORCHESTRATION STRATEGY
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Build a workflow strategy string for agent prompts.
 * Injected into subagent context to guide model usage.
 *
 * @returns {string} Workflow routing guidance
 */
function buildRoutingGuidance() {
  const lines = [
    '## Model Routing (STRICT — VIOLATIONS WASTE COST)',
    `- DEFAULT: ${TIERS.FLASH.model} (${TIERS.FLASH.role}) — use for ALL routine work`,
    `- ARCHITECT: ${TIERS.PRO.model} (${TIERS.PRO.role}) — ONLY for explicit architectural decisions`,
    `- Target: ${TIERS.FLASH.percentTarget.min}-${TIERS.FLASH.percentTarget.max}% Flash usage`,
    `- Cost: ~$${TIERS.FLASH.costPerMTokens}/M (Flash) vs ~$${TIERS.PRO.costPerMTokens}/M (Pro) — 47x difference`,
    '',
    '### DEFAULT TO FLASH — DO NOT ESCALATE WITHOUT EXPLICIT REASON',
    '- Reading, searching, editing files → Flash',
    '- Writing tests, docs, boilerplate → Flash',
    '- Running commands, git, installs → Flash',
    '- Debugging, fixing bugs → Flash',
    '- Research, scouting, exploration → Flash',
    '- Planning, brainstorming, designing → Flash',
    '- Even complex multi-step work → Flash first, reassess only if Flash fails',
    '',
    '### Pro ONLY when ALL of these are true:',
    '  1. Task requires fundamental system design or architecture decision',
    '  2. User explicitly requested Pro/Architect, OR Flash has demonstrably failed 1+ times',
    '  3. The work cannot be decomposed into smaller Flash-executable steps',
    '',
    '### Anti-Escalation Guard',
    '- If you are unsure whether to use Pro → use Flash',
    '- After Pro creates a plan → return execution to Flash immediately',
    '- Never escalate because the task "seems complex" — try Flash first',
    '- Thinking about using Pro? Answer: use Flash',
    '',
    ''
  ];

  return lines.join('\n');
}

// ═════════════════════════════════════════════════════════════════════════════
// HYBRID CHINA MODEL SUGGESTION
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Analyze a prompt and suggest the best non-Opus model for the task type.
 *
 * Each TASK_MODEL_MAP entry has patterns that, when matched, contribute
 * weight toward suggesting that model. The first model meeting the threshold
 * wins (first-match priority for specificity).
 *
 * Returns null if no model meets the threshold — Opus remains default.
 *
 * @param {string} prompt - User's request text
 * @returns {{ model: string, label: string, category: string, reason: string }|null}
 */
function suggestModel() {
  // No alternative models available (China models removed).
  // ZuneF uses pure Opus-only (4.8/4.7/4.6).
  // DeepSeek uses Flash/Pro via main router.
  return null;
}

// ═════════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═════════════════════════════════════════════════════════════════════════════

/**
 * Routing decision log filename (JSON Lines format, append-only).
 * Written by user-prompt-routing.cjs hook, read by kv-cache-metrics.cjs.
 * Consumers join with os.tmpdir() to get the full path.
 * Shared constant prevents path drift between producer and consumer.
 */
const ROUTING_LOG_FILENAME = 'ck-routing-log.jsonl';

module.exports = {
  analyzePrompt,
  shouldEscalate,
  routeTask,
  trackFlashFailure,
  getFlashRetries,
  clearFlashFailures,
  buildRoutingGuidance,
  suggestModel,
  // Constants for direct use
  THRESHOLDS,
  TIERS,
  ROUTING_LOG_FILENAME,
  // Cross-process failure store
  recordFailure: failureStore.recordFailure,
  getFailureCount: failureStore.getFailureCount,
  clearFailures: failureStore.clearFailures,
  pruneFailures: failureStore.pruneFailures,
  isFlashUnstable: failureStore.isFlashUnstable,
  getGlobalFailureCount: failureStore.getGlobalFailureCount
};
