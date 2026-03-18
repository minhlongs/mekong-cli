/**
 * cto-pane-evaluator.js — Pane state evaluation, LLM vision, auto-respawn, auto-compact
 * Extracted from auto-cto-pilot.js (Phase 3 decomposition)
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const config = require('../_bridge/config');
const { log } = require('../core/brain-process-manager');
const { incrementPaneQuestionCount, resetPaneQuestionCount } = require('./cto-context-optimizer');

const TOTAL_PANES = 4; // P0-P3 only — M1 16GB limit

// Per-pane cooldown tracking (prevent dispatch spam)
const COOLDOWN_MS = 120_000; // 2 minutes
const paneCooldowns = new Map(); // paneIdx → lastDispatchTimestamp

// Per-pane error tracking (auto-respawn after consecutive errors)
const paneErrorCounts = new Map(); // paneIdx → consecutive error count
const MAX_CONSECUTIVE_ERRORS = 3;

// Stuck detection: track last-seen output hash per pane
const paneOutputHashes = new Map(); // paneIdx → { hash, since }
const STUCK_THRESHOLD_MS = 5 * 60_000; // 5 minutes

/** Simple string hash for stuck detection */
function hashOutput(str) {
	let h = 0;
	for (let i = 0; i < str.length; i++) h = ((h << 5) - h + str.charCodeAt(i)) | 0;
	return h;
}

/** Check if pane is in cooldown */
function isPaneCoolingDown(paneIdx) {
	const lastDispatch = paneCooldowns.get(paneIdx);
	if (!lastDispatch) return false;
	return Date.now() - lastDispatch < COOLDOWN_MS;
}

/** Mark pane as just dispatched */
function markPaneDispatched(paneIdx) {
	paneCooldowns.set(paneIdx, Date.now());
}

/** Track pane errors; returns true if should auto-respawn */
function trackPaneError(paneIdx) {
	const count = (paneErrorCounts.get(paneIdx) || 0) + 1;
	paneErrorCounts.set(paneIdx, count);
	return count >= MAX_CONSECUTIVE_ERRORS;
}

/** Reset pane error count on success */
function resetPaneErrors(paneIdx) {
	paneErrorCounts.set(paneIdx, 0);
}

/** Check if pane output is stuck (same hash for >5 min) */
function checkStuck(paneIdx, output) {
	const h = hashOutput(output);
	const prev = paneOutputHashes.get(paneIdx);
	if (prev && prev.hash === h) {
		return Date.now() - prev.since >= STUCK_THRESHOLD_MS;
	}
	paneOutputHashes.set(paneIdx, { hash: h, since: Date.now() });
	return false;
}

/**
 * Determine target pane index from task filename keywords.
 */
function getTargetPane(filename) {
	const lower = filename.toLowerCase();
	if (/openclaw|brain|cto|factory/.test(lower)) return 0;
	if (/algo.?trader|algotrader|trading/.test(lower)) return 1;
	if (/sophia|vibe|core|package|mekong-cli/.test(lower)) return 2;
	if (/well|wellnexus|84tea|apex/.test(lower)) return 3;
	// Distribute between P0-P3 based on hash
	const hash = filename.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
	return hash % TOTAL_PANES;
}

/**
 * Dispatch queued task files to idle panes.
 * Returns number of tasks dispatched.
 */
function dispatchQueuedTasks() {
	const tasks = fs.readdirSync(config.WATCH_DIR).filter((f) => config.TASK_PATTERN.test(f));
	if (tasks.length === 0) return 0;

	const sorted = tasks.sort((a, b) => {
		const aCrit = a.startsWith('CRITICAL') ? 0 : 1;
		const bCrit = b.startsWith('CRITICAL') ? 0 : 1;
		if (aCrit !== bCrit) return aCrit - bCrit;
		return fs.statSync(path.join(config.WATCH_DIR, a)).mtimeMs - fs.statSync(path.join(config.WATCH_DIR, b)).mtimeMs;
	});

	let dispatched = 0;
	const dispatching = new Set();

	for (const taskFile of sorted) {
		const targetIdx = getTargetPane(taskFile);
		if (dispatching.has(targetIdx)) continue;
		if (isPaneCoolingDown(targetIdx)) continue; // Cooldown: skip recently dispatched panes

		const pane = `${config.TMUX_SESSION}:0.${targetIdx}`;
		try {
			const paneCheck = execSync(`tmux capture-pane -t ${pane} -p 2>/dev/null`, { encoding: 'utf-8', timeout: 8000 });
			const pLines = paneCheck.split('\n').filter((l) => l.trim());
			const tail5 = pLines.slice(-5).join('\n');
			const hasPrompt = /❯/.test(tail5);
			const isBusy = /Cooking|Brewing|Frosting|Moonwalking|Concocting|Sautéing|Churning|Orbiting|thinking|Compacting|Ebbing|Hatching|queued messages|Press up to edit/i.test(tail5);
			const needsCompact = /until auto-compact|0%\s*until|auto-compact will|context.*(full|limit|exceeded)/i.test(paneCheck);
			const isIdle = hasPrompt && !isBusy && !needsCompact;

			if (isIdle) {
				const taskPath = path.join(config.WATCH_DIR, taskFile);
				const taskContent = fs.readFileSync(taskPath, 'utf-8').trim();
				const firstLine = taskContent.split('\n')[0].trim();
				const command = firstLine.startsWith('/') ? firstLine : `/cook ${firstLine}`;

				const MODEL_POOL = Object.fromEntries(Object.entries(config.PANE_CONFIG).map(([k, v]) => [k, v.model]));
				const paneModel = MODEL_POOL[targetIdx] || MODEL_POOL[0];
				log(`🦞 DISPATCHING: "${taskFile}" → P${targetIdx} [${paneModel}]`);

				// Use temp file + tmux load-buffer to avoid shell escaping issues
				const tmpCmdFile = path.join(require('os').tmpdir(), `.cto-cmd-${Date.now()}.txt`);
				fs.writeFileSync(tmpCmdFile, command);
				try {
					execSync(`tmux load-buffer ${tmpCmdFile}`, { timeout: 5000 });
					execSync(`tmux paste-buffer -t ${pane}`, { timeout: 5000 });
				} finally {
					try { fs.unlinkSync(tmpCmdFile); } catch (e) {}
				}
				execSync(`tmux send-keys -t ${pane} Enter`, { timeout: 3000 });

				const doneDir = path.join(config.WATCH_DIR, '..', 'tasks-done');
				if (!fs.existsSync(doneDir)) fs.mkdirSync(doneDir, { recursive: true });
				fs.renameSync(taskPath, path.join(doneDir, `${Date.now()}_${taskFile}`));
				dispatched++;
				dispatching.add(targetIdx);
				markPaneDispatched(targetIdx);
				resetPaneErrors(targetIdx);
			}
		} catch (dispatchErr) {
			log(`AUTO-CTO DISPATCH P${targetIdx} ERROR: ${dispatchErr.message}`);
		}
	}
	return dispatched;
}

/**
 * Evaluate all panes via LLM vision, auto-respawn, auto-compact.
 * Returns true if any pane is busy/active.
 */
async function evaluateAllPanes() {
	let isApiBusy = false;
	try {
		const { interpretState, clearCache } = require('../_bridge/llm-interpreter');
		for (let pIdx = 0; pIdx < TOTAL_PANES; pIdx++) {
			try {
				const paneOutput = execSync(`tmux capture-pane -t tom_hum:0.${pIdx} -p -S -50 2>/dev/null`, { encoding: 'utf-8', timeout: 3000 });

				// Auto-respawn: shell-only detected
				const lastLines = paneOutput.trim().split('\n').slice(-3).join(' ');
				const hasCCCLI = /❯|bypass permissions|✻|Cooking|Brewing|Frosting|Moonwalking|Concocting|Sautéing|thinking|Hatching|Ebbing/i.test(lastLines);
				const isShellPrompt = /[$%]\s*$/.test(lastLines) && !hasCCCLI;

				if (isShellPrompt) {
					log(`[🩺 RESPAWN][P${pIdx}] Shell-only detected — auto-restarting CC CLI`);
					try {
						execSync(`tmux send-keys -t tom_hum:0.${pIdx} "export CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50 && claude --dangerously-skip-permissions --continue"`, { timeout: 8000 });
						execSync(`tmux send-keys -t tom_hum:0.${pIdx} Enter`, { timeout: 3000 });
					} catch (e) { log(`[🩺 RESPAWN][P${pIdx}] restart failed: ${e.message}`); }
					isApiBusy = true;
					continue;
				}

				// Auto-compact: context full
				if (/until auto-compact|0%\s*until|auto-compact will|context.*(full|limit|exceeded)/i.test(paneOutput)) {
					log(`[🧹 COMPACT][P${pIdx}] Context full detected — sending /compact`);
					try { execSync(`tmux send-keys -t tom_hum:0.${pIdx} "/compact" Enter`, { timeout: 5000 }); } catch (e) {}
					isApiBusy = true;
					continue;
				}

				// Stuck detection: same output for >5 minutes
				if (checkStuck(pIdx, paneOutput)) {
					log(`[STUCK][P${pIdx}] Same output >5min — sending Escape + /compact`);
					try {
						execSync(`tmux send-keys -t tom_hum:0.${pIdx} Escape`, { timeout: 2000 });
						execSync(`tmux send-keys -t tom_hum:0.${pIdx} "/compact" Enter`, { timeout: 5000 });
					} catch (e) {}
					paneOutputHashes.delete(pIdx);
					isApiBusy = true;
					continue;
				}

				const llmResult = await interpretState(paneOutput);

				if (llmResult.state !== 'question') resetPaneQuestionCount(pIdx);

				if (llmResult.state === 'busy') {
					log(`[LLM-VISION][P${pIdx}] CC CLI BUSY: ${llmResult.summary}`);
					isApiBusy = true;
				} else if (llmResult.state === 'question') {
					log(`[LLM-VISION][P${pIdx}] CC CLI QUESTION: ${llmResult.summary}`);
					const currentCount = incrementPaneQuestionCount(pIdx);
					if (llmResult.confidence >= 0.8) {
						if (currentCount >= 3) {
							log(`[LLM-VISION][P${pIdx}] LOOP BREAK: ${currentCount} questions — sending Escape`);
							try { execSync(`tmux send-keys -t tom_hum:0.${pIdx} Escape`, { timeout: 2000 }); } catch (e) {}
							resetPaneQuestionCount(pIdx);
						} else {
							log(`[LLM-VISION][P${pIdx}] AUTO-APPROVE: Sending Enter`);
							try { execSync(`tmux send-keys -t tom_hum:0.${pIdx} Enter`, { timeout: 2000 }); } catch (e) {}
						}
						clearCache();
					}
					isApiBusy = true;
				} else if (llmResult.state === 'error') {
					const shouldRespawn = trackPaneError(pIdx);
					if (shouldRespawn) {
						log('[HEALTH][P' + pIdx + '] ' + MAX_CONSECUTIVE_ERRORS + ' consecutive errors — auto /exit + respawn');
						try {
							execSync('tmux send-keys -t tom_hum:0.' + pIdx + ' "/exit" Enter', { timeout: 3000 });
						} catch (e) {}
						resetPaneErrors(pIdx);
					}
					isApiBusy = true;
				} else if (!['idle', 'complete', 'unknown'].includes(llmResult.state)) {
					isApiBusy = true;
				} else if (llmResult.state === 'unknown') {
					const hasIdlePrompt = paneOutput.includes('❯') || paneOutput.includes('%') || paneOutput.trim().split('\n').slice(-5).some((l) => /^>\s*$/.test(l.trim()));
					if (!hasIdlePrompt) isApiBusy = true;
				}
			} catch (innerE) {
				isApiBusy = true;
			}
		}
	} catch (e) {
		log(`[LLM-VISION] Fatal error: ${e.message}`);
		isApiBusy = true;
	}
	return isApiBusy;
}

module.exports = {
	getTargetPane,
	dispatchQueuedTasks,
	evaluateAllPanes,
	TOTAL_PANES,
	isPaneCoolingDown,
	markPaneDispatched,
	resetPaneErrors,
	checkStuck,
	COOLDOWN_MS,
};
