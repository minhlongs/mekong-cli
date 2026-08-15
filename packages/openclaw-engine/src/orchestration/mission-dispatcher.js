/**
 * Mission Dispatcher v3 — Thin facade (Phase 3 decomposition)
 *
 * Sub-modules:
 *   dispatch-router.js    — Project routing, priority classification
 *   dispatch-queue.js     — Mission loading, task splitting
 *   dispatch-executor.js  — Prompt building, task execution with retries
 *   dispatch-validator.js — Sanitization, plan lookup, safety/learning checks
 */

'use strict';

const { executeTask, buildPrompt, buildPromptFromMission } = require('./dispatch-executor');
const { detectProjectDir, classifyPriority, isComplexRawMission } = require('./dispatch-router');
const { loadMission, shouldChainCooks, splitTaskIntoSubtasks } = require('./dispatch-queue');
const { stripPollution } = require('./dispatch-validator');

module.exports = {
	executeTask,
	buildPrompt,
	buildPromptFromMission,
	loadMission,
	detectProjectDir,
	classifyPriority,
	isComplexRawMission,
	shouldChainCooks,
	splitTaskIntoSubtasks,
	stripPollution,
};
