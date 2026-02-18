/**
 * 🩺 Self-Healer — Auto-recovery daemon
 * 
 * Monitors system health and auto-recovers from common failures.
 * 
 * Features:
 * - Detects stuck tmux sessions
 * - Auto-restarts crashed brain process
 * - Cleans stale lock files
 * - Reports failures via Telegram
 * - Pre-flight checks before mission dispatch
 * 
 * Usage:
 *   const { startMonitor, stopMonitor, preFlightCheck, reportFailure } = require('./self-healer');
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');
const config = require('../config');
const { sendTelegram } = require('./telegram-client');

let _log;
function log(msg) {
    if (!_log) {
        try { _log = require('./brain-process-manager').log; } catch (e) { _log = console.log; }
    }
    _log(`[healer] ${msg}`);
}

let monitorInterval = null;
let consecutiveFailures = 0;
const MAX_CONSECUTIVE_FAILURES = 5;

// ═══════════════════════════════════════════════════════════════
// Health Checks
// ═══════════════════════════════════════════════════════════════

function isTmuxAlive() {
    try {
        const result = execSync('tmux has-session -t tom_hum_brain 2>&1', { encoding: 'utf8', timeout: 5000 });
        return true;
    } catch (e) {
        return false;
    }
}

function isProxyAlive() {
    try {
        const proxyUrl = config.CLOUD_BRAIN_URL || 'http://127.0.0.1:11436';
        execSync(`curl -sf -m 3 ${proxyUrl}/health`, { timeout: 5000, stdio: 'pipe' });
        return true;
    } catch (e) {
        return false;
    }
}

function restartProxy() {
    log('🩺 Restarting Anthropic Adapter (port 11436)...');
    try {
        execSync('pkill -f "anthropic-adapter.js"', { timeout: 3000 }).toString();
    } catch (e) { /* may not be running */ }

    try {
        const adapterPath = path.join(config.MEKONG_DIR, 'scripts', 'anthropic-adapter.js');
        const logPath = '/tmp/adapter_11436.log';
        const out = fs.openSync(logPath, 'a');
        const err = fs.openSync(logPath, 'a');
        const child = spawn('node', [adapterPath, '11436'], {
            detached: true,
            stdio: ['ignore', out, err],
        });
        child.unref();
        log(`🩺 Adapter spawned (PID ${child.pid})`);
        return true;
    } catch (e) {
        log(`🩺 ❌ Failed to restart adapter: ${e.message}`);
        return false;
    }
}

function isProcessStuck() {
    try {
        const lockFile = path.join(config.MEKONG_DIR, 'tasks', '.mission_lock');
        if (!fs.existsSync(lockFile)) return false;
        const stat = fs.statSync(lockFile);
        const ageMs = Date.now() - stat.mtimeMs;
        // If lock is older than 30 minutes = stuck
        return ageMs > 30 * 60 * 1000;
    } catch (e) {
        return false;
    }
}

function clearStaleLocks() {
    try {
        const lockFile = path.join(config.MEKONG_DIR, 'tasks', '.mission_lock');
        if (fs.existsSync(lockFile)) {
            fs.unlinkSync(lockFile);
            log('Cleared stale mission lock');
            return true;
        }
        return false;
    } catch (e) {
        return false;
    }
}

// ═══════════════════════════════════════════════════════════════
// Recovery Actions
// ═══════════════════════════════════════════════════════════════

function attemptRecovery() {
    log('🩺 Attempting auto-recovery...');

    // Clear stale locks
    clearStaleLocks();

    // Check and restart proxy if needed
    if (!isProxyAlive()) {
        log('🩺 Proxy is down — restarting as part of recovery');
        restartProxy();
    }

    // Reset consecutive failure counter on successful recovery
    consecutiveFailures = 0;
    log('🩺 Recovery complete');
}

// ═══════════════════════════════════════════════════════════════
// Pre-flight Check (called before each mission)
// ═══════════════════════════════════════════════════════════════

function preFlightCheck() {
    const issues = [];

    // Check tmux
    if (!isTmuxAlive()) {
        issues.push('Tmux session not found');
    }

    // Check proxy
    if (!isProxyAlive()) {
        issues.push('Proxy 11436 is down');
        restartProxy();
    }

    // Check for stale locks
    if (isProcessStuck()) {
        issues.push('Mission lock is stale (>30min)');
        clearStaleLocks();
    }

    // Check disk space (basic)
    try {
        const tasksDir = path.join(config.MEKONG_DIR, 'tasks');
        const files = fs.readdirSync(tasksDir).filter(f => f.endsWith('.md'));
        if (files.length > 100) {
            issues.push(`Task queue has ${files.length} files — possible buildup`);
        }
    } catch (e) { }

    if (issues.length > 0) {
        log(`⚠️ Pre-flight: ${issues.join(', ')}`);
    }

    return issues.length === 0;
}

// ═══════════════════════════════════════════════════════════════
// Failure Reporting
// ═══════════════════════════════════════════════════════════════

function reportFailure(missionName, error) {
    consecutiveFailures++;
    log(`❌ Mission failed: ${missionName} — ${error} (${consecutiveFailures}/${MAX_CONSECUTIVE_FAILURES})`);

    if (consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
        log(`🚨 ${MAX_CONSECUTIVE_FAILURES} consecutive failures — triggering recovery`);
        sendTelegram(`🚨 ${MAX_CONSECUTIVE_FAILURES} consecutive failures — auto-recovery triggered`);
        attemptRecovery();
    }
}

// ═══════════════════════════════════════════════════════════════
// Monitor Loop
// ═══════════════════════════════════════════════════════════════

function healthCheck() {
    // Check 1: Stuck process
    if (isProcessStuck()) {
        log('🩺 Detected stuck process — clearing locks');
        clearStaleLocks();
    }

    // Check 2: Proxy health
    if (!isProxyAlive()) {
        log('🩺 Proxy 11436 DOWN — auto-restarting...');
        const ok = restartProxy();
        if (ok) {
            sendTelegram('🩺 Self-Healer: Adapter 11436 auto-restarted');
        } else {
            sendTelegram('🚨 Self-Healer: Adapter 11436 FAILED to restart!');
        }
    }
}

function startMonitor() {
    if (monitorInterval) return;
    log('🩺 Self-Healer monitor started');
    monitorInterval = setInterval(healthCheck, 5 * 60 * 1000); // Every 5 minutes
}

function stopMonitor() {
    if (monitorInterval) {
        clearInterval(monitorInterval);
        monitorInterval = null;
        log('🩺 Self-Healer monitor stopped');
    }
}

module.exports = {
    startMonitor,
    stopMonitor,
    preFlightCheck,
    reportFailure,
    healthCheck,
    clearStaleLocks,
};
