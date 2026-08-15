/**
 * cto-reporting.js — Green project handlers: revenue, trading cadence, RaaS missions, ship pipeline
 * Extracted from auto-cto-pilot.js (Phase 3 decomposition)
 */

'use strict';

const fs = require('fs');
const path = require('path');
const config = require('../_bridge/config');
const { log } = require('../core/brain-process-manager');
const { scanRevenueHealth, generateRevenueMission } = require('../_bridge/revenue-health-scanner');
const { dispatchDueTradingMissions } = require('../_bridge/trading-cadence-scheduler');
const shipPipeline = require('../_bridge/ship-pipeline');

const RAAS_COOLDOWN_MS = 30 * 60 * 1000;

const RAAS_MISSIONS = {
	'mekong-cli':
		'/cook "始計 Open Source RaaS Hub: audit secrets → .env.example, README for contributors, MIT LICENSE, npm audit fix, CI/CD pipeline for open-source, map binh_phap_master.md 13 chapters to architecture. Target: production-ready open-source RaaS AGI CTO brain." --auto',
	'algo-trader':
		'/cook "始計 Open Source AGI Trading Bot: audit credentials → .env.example, document AGI strategies in README, clean tests, error handling for missing env vars, security audit for open-source RaaS marketplace release." --auto',
	well: '/cook "始計 Open Source Health Platform: audit Supabase keys, complete i18n vi/en, PayOS integration docs, zero console errors, README for RaaS open-source health platform release." --auto',
	'84tea':
		'/cook "始計 Open Source F&B Platform: audit secrets, menu system docs, PWA optimization, README open-source contribution guide for RaaS F&B vertical." --auto',
};

/**
 * Handle ship pipeline priority task for a project.
 * Returns true if a pipeline task was dispatched.
 */
function handleShipPipeline(project) {
	const pipelineCmd = shipPipeline.getNextPhaseCommand(project);
	if (pipelineCmd && !shipPipeline.isShipComplete(project)) {
		const phaseName = shipPipeline.getPhaseName((shipPipeline.getPipelineStatus(project) || { currentPhase: 1 }).currentPhase);
		log(`AUTO-CTO [SHIP PIPELINE]: ${project} — phase ${phaseName} not complete`);
		const filename = `HIGH_mission_${project.replace(/-/g, '_')}_pipeline_${phaseName.toLowerCase()}_${Date.now()}.txt`;
		fs.writeFileSync(path.join(config.WATCH_DIR, filename), pipelineCmd);
		shipPipeline.advancePhase(project, 'PASS');
		return true;
	}
	return false;
}

/**
 * Handle green project: revenue scan, trading cadence, RaaS missions.
 * Returns true if a mission was dispatched.
 */
function handleGreenProject(project) {
	// Revenue health scan
	const revHealth = scanRevenueHealth();
	if (revHealth && !revHealth.healthy && revHealth.issues.length > 0) {
		const issue = revHealth.issues[0];
		const { prompt, filename } = generateRevenueMission(issue);
		fs.writeFileSync(path.join(config.WATCH_DIR, filename), prompt);
		log(`AUTO-CTO [作戰 REVENUE]: Dispatched revenue fix — ${issue.module}: ${issue.message}`);
		return true;
	}

	// Trading cadence for algo-trader
	if (project === 'algo-trader') {
		const tradingDispatched = dispatchDueTradingMissions();
		if (tradingDispatched > 0) {
			log(`AUTO-CTO [🏢 TRADING COMPANY]: ${tradingDispatched} cadence mission(s) dispatched`);
			return true;
		}
	}

	// RaaS AGI missions (with cooldown)
	const raasStateFile = path.join(__dirname, '..', `.raas-last-${project}.json`);
	let raasRecentlyDispatched = false;
	try {
		if (fs.existsSync(raasStateFile)) {
			const last = JSON.parse(fs.readFileSync(raasStateFile, 'utf-8'));
			raasRecentlyDispatched = Date.now() - last.ts < RAAS_COOLDOWN_MS;
		}
	} catch (e) {}

	if (!raasRecentlyDispatched) {
		const mission = RAAS_MISSIONS[project];
		if (mission) {
			const filename = `HIGH_mission_${project}_open_source_raas_${Date.now()}.txt`;
			fs.writeFileSync(path.join(config.WATCH_DIR, filename), `${project}: ${mission}`);
			fs.writeFileSync(raasStateFile, JSON.stringify({ ts: Date.now(), project }));
			log(`AUTO-CTO [🚀 OPEN SOURCE RaaS AGI]: ${project} GREEN → Dispatched RaaS mission`);
			return true;
		}
		log(`AUTO-CTO [軍形 GREEN]: ${project} — ALL CLEAR ✅ (no RaaS mission defined)`);
	} else {
		log(`AUTO-CTO [軍形 GREEN]: ${project} — RaaS cooldown active ⏳`);
	}
	return false;
}

module.exports = {
	handleShipPipeline,
	handleGreenProject,
	RAAS_MISSIONS,
	RAAS_COOLDOWN_MS,
};
