/**
 * dispatch-router.js — Project routing and priority classification
 * Extracted from mission-dispatcher.js (Phase 3 decomposition)
 */

'use strict';

const fs = require('fs');
const path = require('path');
const config = require('../_bridge/config');

let log = console.log;
try { const bpm = require('../core/brain-process-manager'); if (bpm.log) log = bpm.log; } catch (e) {}

/**
 * Detect project directory from task content keywords.
 */
function detectProjectDir(taskContent, taskFile = '') {
	const lowerContent = taskContent.toLowerCase();
	const lowerFile = (taskFile || '').toLowerCase();

	const routes = {
		well: 'apps/well',
		'com-anh-duong': 'apps/com-anh-duong-10x',
		'doanh-trai': 'doanh-trai-tom-hum',
		'84tea': 'apps/84tea',
		'algo-trader': 'apps/algo-trader',
		'apex-os': 'apps/apex-os',
		anima119: 'apps/anima119',
		'sophia-ai-factory': 'apps/sophia-ai-factory',
		'agencyos-web': 'apps/agencyos-web',
		'sa-dec-flower-hunt': 'apps/sa-dec-flower-hunt',
		'openclaw-worker': '.',
		'mekong-cli': '.',
	};

	// 1. Filename match first
	for (const [key, dir] of Object.entries(routes)) {
		if (lowerFile.includes(key)) {
			const target = path.join(config.MEKONG_DIR, dir);
			if (fs.existsSync(target)) { log(`[ROUTING] Filename match: ${key} -> ${target}`); return target; }
		}
	}

	// 2. Content keyword match
	for (const [keyword, dir] of Object.entries(routes)) {
		const target = path.join(config.MEKONG_DIR, dir);
		if (keyword.length <= 3 && lowerContent === keyword) {
			if (fs.existsSync(target)) return target;
		}
		if (keyword.length > 3 && lowerContent.includes(keyword)) {
			if (fs.existsSync(target)) { log(`[ROUTING] Content match: ${keyword} -> ${target}`); return target; }
		}
	}

	// 3. Iron Focus fallback
	if (config.PROJECTS && config.PROJECTS.length > 0) {
		const defaultProj = config.PROJECTS[0];
		const routePath = routes[defaultProj];
		const target = routePath
			? path.join(config.MEKONG_DIR, routePath === '.' ? '' : routePath)
			: path.join(config.MEKONG_DIR, `apps/${defaultProj}`);
		if (fs.existsSync(target)) return target;
	}

	return config.MEKONG_DIR;
}

/**
 * Classify mission priority: P0 (critical), P1 (important), P2 (routine).
 */
function classifyPriority(taskContent, complexity = 'simple') {
	const lower = taskContent.toLowerCase();
	if (/\bagi\b|openclaw-worker|production down|security|critical/i.test(taskContent)) return { priority: 'P0', reason: 'AGI/security/critical keyword' };
	if (lower.includes('deep 10x') || lower.includes('urgent') || lower.includes('hotfix')) return { priority: 'P0', reason: 'Urgent/deep task' };
	if (complexity === 'complex' || lower.includes('refactor') || lower.includes('architecture')) return { priority: 'P1', reason: 'Complex task' };
	return { priority: 'P2', reason: 'Routine' };
}

function isComplexRawMission(text) {
	return config.COMPLEXITY.COMPLEX_KEYWORDS.some((kw) => text.includes(kw));
}

module.exports = { detectProjectDir, classifyPriority, isComplexRawMission };
