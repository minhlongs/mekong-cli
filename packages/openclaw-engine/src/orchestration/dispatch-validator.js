/**
 * dispatch-validator.js — Pre-dispatch validation: sanitization, plan lookup, safety checks
 * Extracted from mission-dispatcher.js (Phase 3 decomposition)
 */

'use strict';

const fs = require('fs');
const path = require('path');
const config = require('../_bridge/config');

let log = console.log;
try { const bpm = require('../core/brain-process-manager'); if (bpm.log) log = bpm.log; } catch (e) {}

/**
 * Strip verbose orchestration/intel blocks from task content to save tokens.
 */
function stripPollution(content) {
	let clean = content;
	clean = clean.replace(/WORKFLOW ORCHESTRATION \(MANDATORY\):[\s\S]*?CORE PRINCIPLES:[\s\S]*?Avoid introducing bugs\./gi, '');
	clean = clean.replace(/GOOGLE ULTRA INTEL \(searched Drive\/Gmail\/Calendar\):[\s\S]*?━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━/gi, '');
	clean = clean.replace(/━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━/g, '');
	return clean.replace(/\n{3,}/g, '\n\n').trim();
}

/**
 * Find the latest plan.md in a project's plans directory.
 */
function findLatestPlan(projectDir) {
	if (!projectDir || projectDir === config.MEKONG_DIR) return null;
	const plansDir = path.join(projectDir, 'plans');
	if (!fs.existsSync(plansDir)) return null;
	try {
		const { execSync } = require('child_process');
		const planPath = execSync(`ls -t "${plansDir}"/*/plan.md 2>/dev/null | head -n 1`, { encoding: 'utf8' }).trim();
		return planPath || null;
	} catch (e) { return null; }
}

// Safety guard integration
let checkSafety = async () => ({ status: 'SAFE', reason: 'no_guard' });
try {
	const sg = require('../safety/safety-guard');
	checkSafety = sg.checkSafety;
} catch (e) {}

// Learning engine integration
let getDispatchHints = () => ({ timeoutMultiplier: 1.0, shouldSkip: false, preferredIntent: null, reason: 'no_learning_engine' });
let getProjectHealthScore = () => ({ score: 50 });
try {
	const le = require('../intelligence/learning-engine');
	getDispatchHints = le.getDispatchHints || getDispatchHints;
	getProjectHealthScore = le.getProjectHealthScore || getProjectHealthScore;
} catch (e) {}

// Strategy optimizer integration
let optimizeStrategy = async (p) => p;
let classifyError = () => ({ errorType: 'unknown', recoverable: false });
try {
	const so = require('../_bridge/strategy-optimizer');
	optimizeStrategy = so.optimizeStrategy;
	classifyError = so.classifyError;
} catch (e) {}

module.exports = {
	stripPollution,
	findLatestPlan,
	checkSafety,
	getDispatchHints,
	getProjectHealthScore,
	optimizeStrategy,
	classifyError,
};
