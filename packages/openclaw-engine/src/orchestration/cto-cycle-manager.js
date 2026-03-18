/**
 * cto-cycle-manager.js — Main Auto-CTO loop: scan → fix → verify phase routing
 * Extracted from auto-cto-pilot.js (Phase 3 decomposition)
 *
 * 3-Phase cycle per project (Binh Pháp):
 *   Phase 1: 始計 SCAN — run build/lint/test, detect real issues
 *   Phase 2: 謀攻 FIX — dispatch targeted fix missions
 *   Phase 3: 軍形 VERIFY — re-scan, GREEN → advance, RED → retry
 */

'use strict';

const fs = require('fs');
const path = require('path');
const config = require('../_bridge/config');
const { log, isBrainAlive } = require('../core/brain-process-manager');
const { isOverheating, isSafeToScan } = require('../safety/m1-cooling-daemon');
const { isQueueEmpty } = require('../_bridge/task-queue');

const { loadState, saveState, isMissionDuplicate, markMissionDispatched, onProjectMissionFailed, onProjectMissionSuccess } = require('./cto-context-optimizer');
const { scanProject, generateFixMission } = require('./cto-task-generator');
const { dispatchQueuedTasks, evaluateAllPanes } = require('./cto-pane-evaluator');
const { handleShipPipeline, handleGreenProject } = require('./cto-reporting');

const SCAN_INTERVAL_MS = 60000;
const FIX_INTERVAL_MS = 15000;
const MAX_FIX_CYCLES = 3;

/** Project priority queue — higher priority = scanned first (revenue potential) */
const PROJECT_PRIORITY = {
	'sophia-ai-factory': 1, // highest — active SaaS product
	'algo-trader': 2,       // trading revenue
	'well': 3,              // wellnexus
	'mekong-cli': 4,        // platform itself
	'openclaw-worker': 5,   // internal tooling
};

function getProjectPriority(projectName) {
	return PROJECT_PRIORITY[projectName] || 99;
}

/** Sort projects by priority (lower number = higher priority) */
function sortByPriority(projects) {
	return [...projects].sort((a, b) => getProjectPriority(a) - getProjectPriority(b));
}

let intervalRef = null;

function getPhaseInterval(phase) {
	return phase === 'fix' || phase === 'verify' ? FIX_INTERVAL_MS : SCAN_INTERVAL_MS;
}

function startAutoCTO() {
	// Catch unhandled rejections from scan/fix/verify
	process.on('unhandledRejection', (reason) => {
		log(`AUTO-CTO unhandledRejection: ${reason?.message || reason}`);
	});

	let currentPhase = 'scan';

	function scheduleNext() {
		const interval = getPhaseInterval(currentPhase);
		if (intervalRef) clearTimeout(intervalRef);

		intervalRef = setTimeout(async () => {
			try {
				if (!isBrainAlive()) { scheduleNext(); return; }
				if (isOverheating()) { scheduleNext(); return; }

				// DISPATCH FIRST — fast regex-only idle check
				const taskCount = fs.readdirSync(config.WATCH_DIR).filter((f) => config.TASK_PATTERN.test(f)).length;
				log(`🦞 DISPATCH-CHECK: ${taskCount} tasks in queue`);

				if (taskCount > 0) {
					const dispatched = dispatchQueuedTasks();
					if (dispatched > 0) {
						log(`🦞 DISPATCHED ${dispatched} task(s) — skipping LLM Vision this cycle`);
						scheduleNext();
						return;
					}
					log(`AUTO-CTO: ${taskCount} tasks pending, all target panes busy — falling through to LLM Vision`);
				}

				// LLM VISION: evaluate all panes
				const isApiBusy = await evaluateAllPanes();
				if (isApiBusy) { scheduleNext(); return; }
				if (!isQueueEmpty()) { scheduleNext(); return; }

				const state = loadState();
				currentPhase = state.phase;

				// Dynamic project discovery from live tmux panes
				const { getActivePaneProjects } = require('../_bridge/brain-tmux-controller');
				const paneMap = getActivePaneProjects(config.TMUX_SESSION);
				const liveProjects = sortByPriority(Object.values(paneMap).map((p) => p.projectName));
				if (liveProjects.length === 0) { scheduleNext(); return; }

				const projectIdx = state.currentProjectIdx % liveProjects.length;
				const project = liveProjects[projectIdx];
				if (!project) { state.currentProjectIdx = 0; saveState(state); scheduleNext(); return; }

				let projectDir = path.join(config.MEKONG_DIR, project);
				if (!fs.existsSync(projectDir)) projectDir = path.join(config.MEKONG_DIR, 'apps', project);
				if (!fs.existsSync(projectDir)) {
					const { detectProjectDir } = require('./mission-dispatcher');
					projectDir = detectProjectDir(project);
				}
				if (!fs.existsSync(projectDir)) {
					advanceProject(state);
					scheduleNext();
					return;
				}

				// Phase Router
				switch (state.phase) {
					case 'scan':
						if (!isSafeToScan()) { scheduleNext(); return; }
						await handleScan(state, project, projectDir);
						break;
					case 'fix':
						await handleFix(state, project);
						break;
					case 'verify':
						await handleVerify(state, project, projectDir);
						break;
					default:
						state.phase = 'scan';
						saveState(state);
				}
				currentPhase = state.phase;
			} catch (e) {
				log(`AUTO-CTO error: ${e.message}`);
			}
			scheduleNext();
		}, interval);
	}

	log(`AUTO-CTO [九變 v2]: Adaptive reflex — scan ${SCAN_INTERVAL_MS / 1000}s, fix/verify ${FIX_INTERVAL_MS / 1000}s`);
	scheduleNext();
}

async function handleScan(state, project, projectDir) {
	if (handleShipPipeline(project)) return;

	log(`AUTO-CTO [始計 SCAN]: Scanning ${project} (cycle ${state.cycle + 1}/${MAX_FIX_CYCLES})...`);
	const errors = scanProject(projectDir);

	if (errors === null) { advanceProject(state); return; }
	if (errors.length === 0) {
		handleGreenProject(project);
		advanceProject(state);
		return;
	}

	log(`AUTO-CTO [始計]: ${project} — ${errors.length} issue(s) found. Entering FIX phase.`);
	state.phase = 'fix';
	state.errors = errors;
	state.fixIndex = 0;
	state.cycle++;
	saveState(state);
}

async function handleFix(state, project) {
	if (!isQueueEmpty()) return;
	if (state.fixIndex >= state.errors.length) {
		state.phase = 'verify';
		saveState(state);
		return;
	}

	const error = state.errors[state.fixIndex];

	// Web research for critical errors
	let webIntel = '';
	if (error.severity === 'critical' || error.type === 'build') {
		try {
			const { researchErrorWithGemini } = require('../_bridge/gemini-agentic');
			webIntel = await researchErrorWithGemini(error.message, project) || '';
		} catch (e) {}
		if (!webIntel) {
			try {
				const { researchError } = require('../_bridge/web-researcher');
				webIntel = await researchError(error.message, project) || '';
			} catch (e) {}
		}
	}

	const { prompt: basePrompt, filename } = generateFixMission(error, project);
	const dedupKey = `${error.file || error.message}:${error.code || error.type}`;
	if (isMissionDuplicate(dedupKey)) {
		state.fixIndex++;
		saveState(state);
		return;
	}

	const prompt = webIntel ? basePrompt + '\n' + webIntel : basePrompt;
	fs.writeFileSync(path.join(config.WATCH_DIR, filename), prompt);
	markMissionDispatched(dedupKey);
	log(`AUTO-CTO [謀攻 FIX]: ${error.type} — ${error.file || error.message} → ${filename}${webIntel ? ' [+WEB]' : ''}`);
	state.fixIndex++;
	saveState(state);
}

async function handleVerify(state, project, projectDir) {
	log(`AUTO-CTO [軍形 VERIFY]: Re-scanning ${project}...`);
	let errors = scanProject(projectDir);

	if (errors === null || errors.length === 0) {
		onProjectMissionSuccess(project);
		advanceProject(state);
		return;
	}

	if (state.cycle >= MAX_FIX_CYCLES) {
		for (const e of errors.slice(0, 3)) log(`  BLOCKER: [${e.type}] ${e.file || ''} — ${e.message}`);
		onProjectMissionFailed(project);
		advanceProject(state);
		return;
	}

	// Aider self-heal attempt
	try {
		const { tryAiderFix, isAiderAvailable } = require('../_bridge/aider-bridge');
		if (isAiderAvailable()) {
			const errorSummary = errors.map((e) => `${e.file || ''}: ${e.message}`).join('\n');
			const aiderResult = await tryAiderFix({ projectDir, errorLog: errorSummary, testCmd: 'npm run build' });
			if (aiderResult.success) {
				const recheck = scanProject(projectDir);
				if (recheck === null || recheck.length === 0) {
					onProjectMissionSuccess(project);
					advanceProject(state);
					return;
				}
				errors = recheck;
			}
		}
	} catch (e) {}

	state.phase = 'fix';
	state.errors = errors;
	state.fixIndex = 0;
	saveState(state);
}

function advanceProject(state) {
	let totalProjects = config.PROJECTS.length;
	try {
		const { getActivePaneProjects } = require('../_bridge/brain-tmux-controller');
		const paneMap = getActivePaneProjects(config.TMUX_SESSION);
		const liveCount = Object.keys(paneMap).length;
		if (liveCount > 0) totalProjects = liveCount;
	} catch (e) {}
	state.currentProjectIdx = (state.currentProjectIdx + 1) % totalProjects;
	state.phase = 'scan';
	state.cycle = 0;
	state.errors = [];
	state.fixIndex = 0;
	saveState(state);
}

function stopAutoCTO() {
	if (intervalRef) { clearTimeout(intervalRef); intervalRef = null; }
}

module.exports = { startAutoCTO, stopAutoCTO, handleScan, handleFix, handleVerify, advanceProject, PROJECT_PRIORITY, getProjectPriority, sortByPriority };
