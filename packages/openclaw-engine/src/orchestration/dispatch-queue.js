/**
 * dispatch-queue.js — Mission loading, task splitting, chain detection
 * Extracted from mission-dispatcher.js (Phase 3 decomposition)
 */

'use strict';

const fs = require('fs');
const path = require('path');

let log = console.log;
try { const bpm = require('../core/brain-process-manager'); if (bpm.log) log = bpm.log; } catch (e) {}

/**
 * Load a mission from a file — supports .txt (legacy) and .json (v4 contracts).
 */
function loadMission(missionFile) {
	const ext = path.extname(missionFile).toLowerCase();
	const raw = fs.readFileSync(missionFile, 'utf-8').trim();

	if (ext === '.json') {
		let parsed;
		try { parsed = JSON.parse(raw); } catch (e) {
			log(`WARN: loadMission parse failed ${missionFile}: ${e.message}`);
			return { type: 'text', _legacy: true, goal: raw, id: path.basename(missionFile, '.json') };
		}
		return {
			type: 'json', id: parsed.id || path.basename(missionFile, '.json'),
			command: parsed.command || null, goal: parsed.goal || parsed.description || raw,
			project: parsed.project || null, layer: parsed.layer || null,
			timeout: parsed.timeout || null, creditBudget: parsed.creditBudget || null,
			requiresApproval: parsed.requiresApproval || false,
			verification: parsed.verification || null, context: parsed.context || null,
			_legacy: false,
		};
	}

	return {
		type: 'text', _legacy: true, id: path.basename(missionFile, '.txt'),
		goal: raw, command: null, project: null, layer: null,
		timeout: null, creditBudget: null, requiresApproval: false,
		verification: null, context: null,
	};
}

/**
 * Detect if task should be split into multiple /cook commands.
 */
function shouldChainCooks(text) {
	if (text.length < 100) return false;
	const hasMultipleSentences = (text.match(/\.\s+[A-Z]/g) || []).length > 1;
	const hasSeparators = /;\s+|và|va\s+|and\s+/i.test(text);
	return hasMultipleSentences || hasSeparators;
}

/**
 * Split task into multiple subtasks based on separators.
 */
function splitTaskIntoSubtasks(text) {
	let subtasks = text.split(/;\s+|và|and\s+|\.\s+(?=[A-Z])/i);
	subtasks = subtasks.filter((s) => s.trim().length > 10);
	if (subtasks.length > 5) {
		const chunk1 = subtasks.slice(0, 2).join('; ');
		const chunk2 = subtasks.slice(2, 4).join('; ');
		const chunk3 = subtasks.slice(4).join('; ');
		subtasks = [chunk1, chunk2, chunk3].filter((s) => s.length > 0);
	}
	return subtasks;
}

module.exports = { loadMission, shouldChainCooks, splitTaskIntoSubtasks };
