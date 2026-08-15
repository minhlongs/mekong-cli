/**
 * brain-process-manager.js — THIN RE-EXPORT SHELL
 *
 * This file is now a backward-compatible facade. All logic has been
 * split into focused sub-modules:
 *
 *   brain-logger.js             — log() utility
 *   brain-tmux-controller.js    — tmux operations, capturePane, pasteText
 *   brain-state-machine.js      — BUSY/IDLE/COMPLETE pattern detection
 *   brain-spawn-manager.js      — spawnBrain, killBrain, isBrainAlive, canRespawn
 *   brain-respawn-controller.js — respawnBrain (bug fixed: no args to spawnBrain)
 *   brain-mission-runner.js     — runMission, state machine polling loop
 *   brain-system-monitor.js     — getSystemMetrics, isOverheating, checkStuckIntervention
 *
 * Public API unchanged:
 *   spawnBrain, killBrain, isBrainAlive, runMission,
 *   log, isOverheating, getSystemMetrics, checkStuckIntervention, capturePane
 */

const { log } = require('../_bridge/brain-logger');
const { capturePane } = require('../_bridge/brain-tmux-controller');
const { spawnBrain, killBrain, isBrainAlive } = require('./brain-spawn-manager');
const { runMission } = require('./brain-mission-runner');
const { isOverheating, getSystemMetrics, checkStuckIntervention } = require('../reliability/brain-system-monitor');

module.exports = {
	spawnBrain,
	killBrain,
	isBrainAlive,
	runMission,
	log,
	isOverheating,
	getSystemMetrics,
	checkStuckIntervention,
	capturePane,
};
