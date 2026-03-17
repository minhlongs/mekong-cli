/**
 * cto-task-generator.js — Project scanning, error parsing, fix/JSON mission generation
 * Extracted from auto-cto-pilot.js (Phase 3 decomposition)
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const config = require('../_bridge/config');

const MAX_FIXES_PER_SCAN = 3; // Ch.6 虛實: focus force on fewer targets

// --- Phase 1: 始計 SCAN — Detect real issues ---

function scanProject(projectDir) {
	const errors = [];
	const projectName = path.basename(projectDir);
	const pkgPath = path.join(projectDir, 'package.json');
	if (!fs.existsSync(pkgPath)) return null;

	const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
	const scripts = pkg.scripts || {};

	// BUILD check
	if (scripts.build) {
		try {
			execSync('npm run build 2>&1', { cwd: projectDir, encoding: 'utf-8', timeout: 120000 });
		} catch (e) {
			const output = (e.stdout || '') + (e.stderr || '');
			const buildErrors = parseBuildErrors(output, projectName);
			if (buildErrors.length === 0) {
				buildErrors.push({
					type: 'build', severity: 'critical', file: 'package.json',
					message: `Build failed exit ${e.status}. ${output.slice(0, 200).replace(/\n/g, ' ')}...`,
					project: projectName,
				});
			}
			errors.push(...buildErrors);
		}
	}

	// LINT check (only if build passes)
	if (scripts.lint && errors.length === 0) {
		try {
			execSync('npm run lint 2>&1', { cwd: projectDir, encoding: 'utf-8', timeout: 60000 });
		} catch (e) {
			const output = (e.stdout || '') + (e.stderr || '');
			const lintErrors = parseLintErrors(output, projectName);
			if (lintErrors.length === 0) {
				lintErrors.push({
					type: 'lint', severity: 'medium', file: 'package.json',
					message: `Lint failed exit ${e.status}. ${output.slice(0, 200).replace(/\n/g, ' ')}...`,
					rule: 'general-lint-failure', project: projectName,
				});
			}
			errors.push(...lintErrors);
		}
	}

	// TEST check (only if build + lint pass)
	if (scripts.test && errors.length === 0) {
		try {
			execSync('npm test 2>&1', { cwd: projectDir, encoding: 'utf-8', timeout: 120000 });
		} catch (e) {
			const output = (e.stdout || '') + (e.stderr || '');
			const testErrors = parseTestErrors(output, projectName);
			if (testErrors.length === 0) {
				testErrors.push({
					type: 'test', severity: 'medium', file: 'package.json',
					message: `Test failed exit ${e.status}. ${output.slice(0, 200).replace(/\n/g, ' ')}...`,
					project: projectName,
				});
			}
			errors.push(...testErrors);
		}
	}

	return errors;
}

// --- Error Parsers ---

function parseBuildErrors(output, project) {
	const errors = [];
	for (const line of output.split('\n')) {
		const tsMatch = line.match(/^(.+\.tsx?)\((\d+),\d+\):\s*error\s+(TS\d+):\s*(.+)/);
		if (tsMatch) {
			errors.push({ type: 'build', severity: 'critical', file: tsMatch[1], line: parseInt(tsMatch[2]), code: tsMatch[3], message: tsMatch[4].trim(), project });
			continue;
		}
		const nextMatch = line.match(/^(?:Error|error):\s*(.+)/i);
		if (nextMatch && !line.includes('node_modules')) {
			errors.push({ type: 'build', severity: 'critical', file: null, message: nextMatch[1].trim(), project });
		}
	}
	const seen = new Set();
	return errors
		.filter((e) => {
			if (e.file && (e.file.includes('.claude/') || e.file.includes('node_modules/'))) return false;
			const key = `${e.file}:${e.code || e.message}`;
			if (seen.has(key)) return false;
			seen.add(key);
			return true;
		})
		.slice(0, MAX_FIXES_PER_SCAN);
}

function parseLintErrors(output, project) {
	const errors = [];
	for (const line of output.split('\n')) {
		const eslintMatch = line.match(/^\s*(.+\.\w+):(\d+):\d+\s+error\s+(.+?)\s{2,}(.+)/);
		if (eslintMatch) {
			errors.push({ type: 'lint', severity: 'medium', file: eslintMatch[1].trim(), line: parseInt(eslintMatch[2]), message: eslintMatch[3].trim(), rule: eslintMatch[4].trim(), project });
		}
	}
	const seen = new Set();
	return errors
		.filter((e) => {
			if (e.file && (e.file.includes('.claude/') || e.file.includes('node_modules/'))) return false;
			if (seen.has(e.rule)) return false;
			seen.add(e.rule);
			return true;
		})
		.slice(0, MAX_FIXES_PER_SCAN);
}

function parseTestErrors(output, project) {
	const errors = [];
	for (const line of output.split('\n')) {
		const failMatch = line.match(/^\s*(?:FAIL|✕|×)\s+(.+)/);
		if (failMatch) {
			errors.push({ type: 'test', severity: 'medium', file: failMatch[1].trim(), message: `Test suite failed: ${failMatch[1].trim()}`, project });
		}
	}
	return errors.filter((e) => !e.file.includes('.claude/') && !e.file.includes('node_modules/')).slice(0, MAX_FIXES_PER_SCAN);
}

// --- Fix Mission Generation ---

function generateFixMission(error, project) {
	let prompt;
	switch (error.type) {
		case 'build':
			prompt = error.file
				? `Fix build error in ${error.file}${error.line ? ` line ${error.line}` : ''}: ${error.code || ''} ${error.message}. Run npm run build after fixing to verify.`
				: `Fix build error: ${error.message}. Run npm run build after fixing to verify.`;
			break;
		case 'lint':
			prompt = `Fix lint error "${error.rule}" in ${error.file}: ${error.message}. Fix ALL instances of this rule in the file. Run npm run lint after fixing.`;
			break;
		case 'test':
			prompt = `Fix failing test: ${error.file}. Analyze the test failure, fix the source code or test. Run npm test after fixing.`;
			break;
		default:
			prompt = `Fix: ${error.message}`;
	}

	const fullPrompt = `/cook "${prompt} Fix at most 5 files per mission. CRITICAL: DO NOT run git commit, git push, or /check-and-commit. The CI/CD gate handles git operations." --auto`;
	const severity = error.severity === 'critical' ? 'HIGH' : 'MEDIUM';
	const filename = `${severity}_mission_${project.replace(/-/g, '_')}_fix_${error.type}_${Date.now()}.txt`;
	return { prompt: fullPrompt, filename };
}

// --- JSON Mission Generation (v4 contracts) ---

const USE_JSON_MISSIONS = process.env.MEKONG_JSON_MISSIONS !== 'false';

function generateJsonMission({ goal, command = null, project = null, layer = null, severity = 'MEDIUM', verificationType = null }) {
	const ts = Date.now();
	const safeProject = (project || 'generic').replace(/-/g, '_');

	if (!USE_JSON_MISSIONS) {
		const filename = `${severity}_mission_${safeProject}_${ts}.txt`;
		fs.writeFileSync(path.join(config.WATCH_DIR, filename), goal);
		return filename;
	}

	const id = `mission_${safeProject}_${ts}`;
	const contract = {
		id, command: command || 'cook', goal, project: project || null,
		layer: layer || null, timeout: null, creditBudget: null,
		requiresApproval: false,
		verification: verificationType ? { criteria: [verificationType] } : null,
		context: null,
	};
	const filename = `${severity}_${id}.json`;
	fs.writeFileSync(path.join(config.WATCH_DIR, filename), JSON.stringify(contract, null, 2));
	return filename;
}

module.exports = {
	scanProject,
	parseBuildErrors,
	parseLintErrors,
	parseTestErrors,
	generateFixMission,
	generateJsonMission,
	MAX_FIXES_PER_SCAN,
};
