/**
 * dispatch-executor.js — executeTask + buildPrompt + buildPromptFromMission
 * Extracted from mission-dispatcher.js (Phase 3 decomposition)
 */

'use strict';

const fs = require('fs');
const path = require('path');
const config = require('../_bridge/config');
const { isProAvailable } = require('../_bridge/system-status-registry');

let log = console.log;
try { const bpm = require('../core/brain-process-manager'); if (bpm.log) log = bpm.log; } catch (e) {}

let runMission;
try { runMission = require('../core/brain-process-manager').runMission; } catch (e) {
	runMission = async () => ({ success: false, result: 'no_brain_module', elapsed: 0 });
}

let isTeamMission = () => false;
let buildAgentTeamBlock = () => '';
let buildDecomposedPrompt = () => '';
let detectIntent = () => 'COOK';
try {
	const mcc = require('../intelligence/mission-complexity-classifier');
	isTeamMission = mcc.isTeamMission || isTeamMission;
	buildAgentTeamBlock = mcc.buildAgentTeamBlock || buildAgentTeamBlock;
	buildDecomposedPrompt = mcc.buildDecomposedPrompt || buildDecomposedPrompt;
	detectIntent = mcc.detectIntent || detectIntent;
} catch (e) {}

let matchRole = null;
try { matchRole = require('../_bridge/hands-registry').matchRole; } catch (e) {}
let getTopLessons = () => '';
try { getTopLessons = require('../_bridge/post-mortem-reflector').getTopLessons || getTopLessons; } catch (e) {}

const { detectProjectDir, classifyPriority, isComplexRawMission } = require('./dispatch-router');
const { stripPollution, findLatestPlan, checkSafety, getDispatchHints, getProjectHealthScore, optimizeStrategy, classifyError } = require('./dispatch-validator');
const { preemptiveCool } = require('../safety/m1-cooling-daemon');

// --- Prompt Building ---

function formatCmd(cmd, text, flags = '') {
	// CC CLI colon-syntax fix: convert /cmd:sub to correct format
	// Skills (/plan, /bootstrap, /docs, /review, /test) → space args: /plan hard
	// Commands (/cto, /studio, /pm, /ops, etc.) → hyphen filename: /cto-architect
	const SKILL_BASES = ['/plan', '/bootstrap', '/docs', '/review', '/test', '/cook'];
	const base = cmd.split(':')[0];
	if (cmd.includes(':')) {
		cmd = SKILL_BASES.includes(base) ? cmd.replace(/:/g, ' ') : cmd.replace(/:/g, '-');
	}
	const escapedText = text.replace(/"/g, '\\"').trim();
	const isPlanCmd = cmd.startsWith('/plan') || cmd === '/bootstrap';
	const finalMandate = isPlanCmd
		? 'WORKFLOW: THINK DEEP -> PLAN FIRST. RESEARCH AND PLAN ONLY (plan.md). ABSOLUTELY DO NOT FIX/COOK. Stop after plan is done. '
		: 'Prioritize /cook and verify thoroughly. ';
	const payload = escapedText ? `\n\n${escapedText} Fix < 5 files per mission.` : '';
	return `${cmd} "${finalMandate.trim()}${payload}" ${flags}`.trim();
}

function buildPrompt(taskContent, projectDir = null) {
	let clean = taskContent.replace(/\\!/g, '!').replace(/\\"/g, '"').trim();
	clean = clean.replace(/^[a-z0-9_-]+:\s*/i, '');
	const leanContent = stripPollution(clean);
	const safe = leanContent.replace(/[()$`\\!]/g, ' ').replace(/\s+/g, ' ').trim();
	const lowerSafe = safe.toLowerCase();
	const isDeepTask = lowerSafe.includes('deep 10x') || lowerSafe.includes('deep scan') || lowerSafe.includes('map');
	const isPro = isProAvailable();

	let load = 0;
	try { load = require('os').loadavg()[0]; } catch (e) {}
	const isHanBangMode = load > 30;

	// Parse explicit command
	let parsedCmd = null, parsedText = safe, parsedFlags = '';
	const cmdMatch = safe.match(/^(\/[a-z0-9:-]+)(?:\s+"([^"]+)")?(?:\s+(.*))?$/i);
	if (cmdMatch) {
		parsedCmd = cmdMatch[1];
		if (cmdMatch[2]) { parsedText = cmdMatch[2]; parsedFlags = cmdMatch[3] || ''; }
		else {
			const rest = safe.substring(parsedCmd.length).trim();
			const flagIdx = rest.indexOf('--');
			if (flagIdx >= 0) { parsedText = rest.substring(0, flagIdx).trim(); parsedFlags = rest.substring(flagIdx).trim(); }
			else parsedText = rest;
		}
	} else if (safe.startsWith('/')) {
		const spaceIdx = safe.indexOf(' ');
		if (spaceIdx > 0) { parsedCmd = safe.substring(0, spaceIdx); parsedText = safe.substring(spaceIdx + 1); }
		else { parsedCmd = safe; parsedText = ''; }
	}

	if (isDeepTask && (parsedCmd === '/cook' || !parsedCmd) && isPro) return formatCmd('/plan:hard', parsedText, parsedFlags);

	// Plan infiltration: auto-link latest plan.md for /cook
	if ((parsedCmd === '/cook' || parsedCmd === '/plan:fast') && projectDir && projectDir !== config.MEKONG_DIR) {
		const planPath = findLatestPlan(projectDir);
		if (planPath && !parsedText.includes('plan.md')) {
			const planRelPath = `./plans/${path.basename(path.dirname(planPath))}/plan.md`;
			return formatCmd(parsedCmd, `Using plan from ${planRelPath}: ${parsedText}`, parsedFlags);
		}
	}

	if (parsedCmd) return formatCmd(parsedCmd, parsedText, parsedFlags);

	const intent = detectIntent(safe);

	// ROIaaS Command Stack — level-based routing
	if (intent === 'PORTFOLIO' || lowerSafe.includes('portfolio') || lowerSafe.includes('investor report') || lowerSafe.includes('fund allocation')) return formatCmd('/studio:audit', safe);
	if (intent === 'ARCHITECTURE' || lowerSafe.includes('architecture decision') || lowerSafe.includes('adr') || lowerSafe.includes('tech stack')) return formatCmd('/cto:architect', safe);
	if (intent === 'INCIDENT' || lowerSafe.includes('incident') || lowerSafe.includes('outage') || lowerSafe.includes('p0')) return formatCmd('/cto:incident', safe);
	if (intent === 'SPRINT' || lowerSafe.includes('sprint plan') || lowerSafe.includes('backlog groom')) return formatCmd('/pm:sprint', safe);
	if (intent === 'MILESTONE' || lowerSafe.includes('milestone') || lowerSafe.includes('progress track')) return formatCmd('/pm:milestone', safe);
	if (intent === 'DEPLOY' || lowerSafe.includes('deploy prod') || lowerSafe.includes('ship to prod')) return formatCmd('/cto:deploy', safe);

	// 105-Hands role injection
	let roleInjectedText = safe;
	if (matchRole) {
		try {
			const { role, score, fallback } = matchRole(safe, intent);
			if (!fallback && role && role.systemPrompt) roleInjectedText = `[ROLE: ${role.displayName}] ${role.systemPrompt} | Task: ${safe}`;
		} catch (e) {}
	}

	if (lowerSafe.includes('ci/cd') || lowerSafe.includes('pipeline') || lowerSafe.includes('build fail')) return formatCmd('/plan:ci', roleInjectedText);
	if (lowerSafe.includes('new project') || lowerSafe.includes('bootstrap') || lowerSafe.includes('khoi tao')) return formatCmd('/bootstrap', roleInjectedText, isHanBangMode ? '--auto' : '--parallel --auto');
	if (lowerSafe.includes('test') || lowerSafe.includes('kiem thu')) return formatCmd('/test', roleInjectedText);
	if (intent === 'MULTI_FIX') return formatCmd('/cook', roleInjectedText + (isHanBangMode ? ' [HAN BANG MODE]' : ' MUST use 10+ parallel subagents.'), isHanBangMode ? '--auto' : '--parallel --auto');
	if (intent === 'STRATEGIC') return formatCmd(isHanBangMode ? '/plan:hard' : '/plan:parallel', roleInjectedText);

	if (isComplexRawMission(lowerSafe)) {
		const decomposed = buildDecomposedPrompt(safe, 'default');
		if (intent === 'FIX') return formatCmd('/debug', roleInjectedText, '--parallel');
		if (intent === 'PLAN' || intent === 'RESEARCH') return formatCmd('/plan:hard', roleInjectedText);
		if (intent === 'REVIEW') return formatCmd('/review', roleInjectedText, '--parallel');
		return formatCmd('/plan:parallel', roleInjectedText + '\n\n' + decomposed);
	}

	if (intent === 'FIX') return formatCmd('/debug', roleInjectedText, isHanBangMode ? '' : '--parallel');
	if (intent === 'REVIEW') return formatCmd('/review', roleInjectedText, isHanBangMode ? '' : '--parallel');
	return formatCmd('/plan:hard', roleInjectedText, isHanBangMode ? '' : '--parallel');
}

function buildPromptFromMission(mission, projectDir = null) {
	if (mission._legacy) return buildPrompt(mission.goal, projectDir);

	let contractHints = '', verificationBlock = '';
	if (mission.command) {
		const contractPath = path.join(config.MEKONG_DIR, 'factory', 'contracts', 'commands', `${mission.command}.json`);
		try {
			if (fs.existsSync(contractPath)) {
				const contract = JSON.parse(fs.readFileSync(contractPath, 'utf-8'));
				if (contract.agentHints) contractHints = `\n[AGENT HINTS: ${Array.isArray(contract.agentHints) ? contract.agentHints.join(', ') : contract.agentHints}]`;
			}
		} catch (e) {}
	}
	if (mission.verification) {
		const criteria = Array.isArray(mission.verification.criteria) ? mission.verification.criteria.join('; ') : mission.verification;
		verificationBlock = `\n[VERIFICATION: ${criteria}]`;
	}
	const contextBlock = mission.context ? `\n[CONTEXT: ${JSON.stringify(mission.context)}]` : '';
	return buildPrompt(`${mission.goal || ''}${contractHints}${verificationBlock}${contextBlock}`, projectDir);
}

// --- Task Execution ---

async function executeTask(taskContent, taskFile, timeoutMs, complexity) {
	const safety = await checkSafety(taskContent);
	if (safety.status === 'UNSAFE') { log(`🚫 BLOCKED: ${taskFile} — ${safety.reason}`); return { success: false, result: 'unsafe_blocked', elapsed: 0 }; }

	const { priority, reason: priorityReason } = classifyPriority(taskContent, complexity);
	log(`📊 PRIORITY: ${priority} — ${priorityReason} [${taskFile}]`);

	const hints = getDispatchHints(taskContent);
	if (hints.shouldSkip) { log(`🧠 LEARNING SKIP: ${taskFile} — ${hints.reason}`); return { success: false, result: 'learning_skip', elapsed: 0 }; }

	const projectDir = detectProjectDir(taskContent, taskFile);
	const projectName = path.basename(projectDir);
	const health = getProjectHealthScore(projectName);
	if (health.totalMissions > 0) log(`🏥 HEALTH: ${projectName} — score:${health.score}/100`);

	let intent = detectIntent(taskContent);
	const isPro = isProAvailable();
	const lowerContent = taskContent.toLowerCase();
	if ((lowerContent.includes('deep 10x') || lowerContent.includes('deep scan')) && isPro) intent = 'PLAN';
	if (/\bagi\b|openclaw-worker|mekong-cli/i.test(taskContent) && isPro) intent = 'PRO';

	const prompt = buildPrompt(taskContent, projectDir);
	const baseTimeout = timeoutMs || (isTeamMission(prompt) ? config.AGENT_TEAM_TIMEOUT_MS : config.MISSION_TIMEOUT_MS);
	const finalTimeout = Math.round(baseTimeout * (hints.timeoutMultiplier || 1.0));

	await preemptiveCool(complexity);
	let modelOverride = null;
	if (complexity === 'complex') { modelOverride = config.OPUS_MODEL; log(`🔥 OPUS: ${modelOverride}`); }

	let currentPrompt = prompt;
	const MAX_RETRIES = 2;
	for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
		const result = await runMission(currentPrompt, projectDir, finalTimeout, modelOverride, complexity, intent);
		if (result.success || result.result === 'success') {
			if (/^\/(plan:|bootstrap)/.test(currentPrompt)) {
				try {
					const latestPlan = require('child_process').execSync(`ls -t "${projectDir}/plans"/*/plan.md 2>/dev/null | head -n 1`, { encoding: 'utf8' }).trim();
					if (latestPlan) log(`[PLAN-FIRST] Plan at: ${latestPlan}`);
				} catch (e) {}
			}
			return result;
		}
		const noRetry = ['all_workers_busy', 'busy_blocked', 'mission_locked', 'unsafe_blocked', 'brain_died', 'brain_died_fatal', 'no_brain_module', 'max_retries_exhausted', 'duplicate_rejected', 'queued_abort', 'failed_to_start'];
		if (noRetry.includes(result.result)) return result;
		const errorInfo = classifyError(result.result || '');
		if (!errorInfo.recoverable) return result;
		if (attempt < MAX_RETRIES) {
			log(`🔄 RETRY ${attempt + 1}/${MAX_RETRIES}: ${taskFile}`);
			currentPrompt = await optimizeStrategy(prompt, result.result || '', attempt + 1);
		}
	}
	return { success: false, result: 'max_retries_exhausted', elapsed: 0 };
}

module.exports = { executeTask, buildPrompt, buildPromptFromMission, formatCmd };
