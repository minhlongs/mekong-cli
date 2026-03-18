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

const { startAutoCTO, stopAutoCTO, PROJECT_PRIORITY, getProjectPriority, sortByPriority } = require('./cto-cycle-manager');
const { onProjectMissionFailed, onProjectMissionSuccess, loadState, saveState } = require('./cto-context-optimizer');
const { generateJsonMission } = require('./cto-task-generator');
const { TOTAL_PANES, isPaneCoolingDown, COOLDOWN_MS } = require('./cto-pane-evaluator');

/** Get CTO brain status for CLI display */
function getCtoStatus() {
	try {
		const state = loadState();
		return {
			phase: state.phase || 'scan',
			currentProjectIdx: state.currentProjectIdx || 0,
			cycle: state.cycle || 0,
			errorCount: state.errors?.length || 0,
			fixIndex: state.fixIndex || 0,
			totalPanes: TOTAL_PANES,
			cooldownMs: COOLDOWN_MS,
			priorities: PROJECT_PRIORITY,
		};
	} catch {
		return { phase: 'unknown', currentProjectIdx: 0, cycle: 0, errorCount: 0, fixIndex: 0, totalPanes: TOTAL_PANES, cooldownMs: COOLDOWN_MS, priorities: PROJECT_PRIORITY };
	}
}

/** Reset CTO state machine to clean state */
function resetCtoState() {
	const cleanState = { phase: 'scan', currentProjectIdx: 0, cycle: 0, errors: [], fixIndex: 0 };
	saveState(cleanState);
	return cleanState;
}

module.exports = {
	startAutoCTO, stopAutoCTO,
	onProjectMissionFailed, onProjectMissionSuccess,
	generateJsonMission,
	getCtoStatus, resetCtoState,
	PROJECT_PRIORITY, getProjectPriority, sortByPriority,
	TOTAL_PANES, isPaneCoolingDown, COOLDOWN_MS,
};
