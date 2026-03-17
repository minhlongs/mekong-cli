/**
 * Auto-CTO Pilot v4 — Thin facade (Phase 3 decomposition)
 *
 * Sub-modules:
 *   cto-cycle-manager.js    — Main loop: scan → fix → verify
 *   cto-pane-evaluator.js   — Pane state evaluation, LLM vision
 *   cto-task-generator.js   — Project scanning, error parsing, mission generation
 *   cto-context-optimizer.js — State, dedup, failure tracking
 *   cto-reporting.js        — Green path: revenue, trading, RaaS, ship pipeline
 */

'use strict';

const { startAutoCTO, stopAutoCTO } = require('./cto-cycle-manager');
const { onProjectMissionFailed, onProjectMissionSuccess } = require('./cto-context-optimizer');
const { generateJsonMission } = require('./cto-task-generator');

module.exports = { startAutoCTO, stopAutoCTO, onProjectMissionFailed, onProjectMissionSuccess, generateJsonMission };
