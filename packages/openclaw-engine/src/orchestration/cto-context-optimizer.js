/**
 * cto-context-optimizer.js — State management, dedup, failure tracking, question loop control
 * Extracted from auto-cto-pilot.js (Phase 3 decomposition)
 */

'use strict';

const fs = require('fs');
const path = require('path');

const SCAN_RESULT_FILE = path.join(__dirname, '..', '.cto-scan-state.json');

// Mission dedup: prevent re-dispatching same error within 30min
const _dispatchedMissions = new Map();
const MISSION_DEDUP_TTL_MS = 30 * 60 * 1000;

function isMissionDuplicate(errorKey) {
	const lastSent = _dispatchedMissions.get(errorKey);
	if (!lastSent) return false;
	if (Date.now() - lastSent < MISSION_DEDUP_TTL_MS) return true;
	_dispatchedMissions.delete(errorKey);
	return false;
}

function markMissionDispatched(errorKey) {
	_dispatchedMissions.set(errorKey, Date.now());
}

// Per-project consecutive failure tracking (BUG #11)
const projectFailureCount = new Map();
const MAX_CONSECUTIVE_FAILURES = 3;

function onProjectMissionFailed(projectName) {
	const count = (projectFailureCount.get(projectName) || 0) + 1;
	projectFailureCount.set(projectName, count);
	if (count >= MAX_CONSECUTIVE_FAILURES) {
		projectFailureCount.set(projectName, 0);
		return true; // Signal to skip
	}
	return false;
}

function onProjectMissionSuccess(projectName) {
	projectFailureCount.set(projectName, 0);
}

// Per-pane question loop tracking (P0-P9)
const _paneQuestionCounts = new Map();

function getPaneQuestionCount(pIdx) {
	return _paneQuestionCounts.get(pIdx) || 0;
}

function incrementPaneQuestionCount(pIdx) {
	const count = (getPaneQuestionCount(pIdx)) + 1;
	_paneQuestionCounts.set(pIdx, count);
	return count;
}

function resetPaneQuestionCount(pIdx) {
	_paneQuestionCounts.set(pIdx, 0);
}

// Scan state persistence
function loadState() {
	try {
		if (fs.existsSync(SCAN_RESULT_FILE)) {
			return JSON.parse(fs.readFileSync(SCAN_RESULT_FILE, 'utf-8'));
		}
	} catch (e) {}
	return { currentProjectIdx: 0, phase: 'scan', cycle: 0, errors: [], fixIndex: 0 };
}

function saveState(state) {
	try {
		const tempFile = `${SCAN_RESULT_FILE}.tmp`;
		fs.writeFileSync(tempFile, JSON.stringify(state, null, 2));
		fs.renameSync(tempFile, SCAN_RESULT_FILE);
	} catch (e) {}
}

module.exports = {
	isMissionDuplicate,
	markMissionDispatched,
	onProjectMissionFailed,
	onProjectMissionSuccess,
	getPaneQuestionCount,
	incrementPaneQuestionCount,
	resetPaneQuestionCount,
	loadState,
	saveState,
	MISSION_DEDUP_TTL_MS,
	MAX_CONSECUTIVE_FAILURES,
};
