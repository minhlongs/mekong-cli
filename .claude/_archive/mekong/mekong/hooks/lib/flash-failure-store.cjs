/**
 * Flash Failure Store — Cross-process failure persistence for model routing.
 *
 * Stores failure counts in a shared temp file so that when a subagent fails
 * with Flash, subsequent user prompts auto-escalate to Pro.
 *
 * File location: os.tmpdir()/ck:flash-failures.json
 * Format: { "entries": { "<sig80>": { "count": N, "lastFailure": timestamp }, ... } }
 *
 * All functions are fail-open (errors return 0 or no-op).
 *
 * @module flash-failure-store
 */
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');

const STORE_PATH = path.join(os.tmpdir(), 'ck-flash-failures.json');
const DEFAULT_MAX_AGE_MS = 30 * 60 * 1000; // 30 minutes

/**
 * Read the store file. Returns default structure on any error.
 * @returns {{ entries: Record<string, { count: number, lastFailure: number }> }}
 */
function readStore() {
  try {
    if (!fs.existsSync(STORE_PATH)) return { entries: {} };
    const raw = fs.readFileSync(STORE_PATH, 'utf8');
    return JSON.parse(raw);
  } catch {
    return { entries: {} };
  }
}

/**
 * Atomic write: write to .tmp file then rename.
 * Avoids partial reads from concurrent hook invocations.
 * @param {Object} data - Store data to persist
 */
function writeStore(data) {
  try {
    const tmp = `${STORE_PATH}.${process.pid}.${Math.random().toString(36).slice(2)}.tmp`;
    fs.writeFileSync(tmp, JSON.stringify(data));
    fs.renameSync(tmp, STORE_PATH);
  } catch {
    /* fail-open */
  }
}

/**
 * Remove entries older than maxAgeMs. Called automatically by get/record.
 * Pruning happens on read so stale entries don't accumulate indefinitely.
 *
 * @param {number} [maxAgeMs=1800000] - Max age in milliseconds (default 30 min)
 */
function pruneFailures(maxAgeMs) {
  try {
    maxAgeMs = maxAgeMs || DEFAULT_MAX_AGE_MS;
    const store = readStore();
    const now = Date.now();
    let changed = false;

    for (const key of Object.keys(store.entries)) {
      if (now - store.entries[key].lastFailure > maxAgeMs) {
        delete store.entries[key];
        changed = true;
      }
    }

    if (changed) writeStore(store);
  } catch {
    /* fail-open */
  }
}

/**
 * Get the failure count for a task signature.
 *
 * @param {string} taskSignature - Task identifier (first 80 chars used as key)
 * @returns {number} Failure count (0 if none or on error)
 */
function getFailureCount(taskSignature) {
  try {
    if (!taskSignature) return 0;
    pruneFailures();
    const store = readStore();
    const key = taskSignature.slice(0, 80);
    return store.entries[key]?.count || 0;
  } catch {
    return 0;
  }
}

/**
 * Increment failure count for a task signature.
 *
 * @param {string} taskSignature - Task identifier (first 80 chars used as key)
 */
function recordFailure(taskSignature) {
  try {
    if (!taskSignature) return;
    pruneFailures();
    const store = readStore();
    const key = taskSignature.slice(0, 80);

    if (store.entries[key]) {
      store.entries[key].count += 1;
      store.entries[key].lastFailure = Date.now();
    } else {
      store.entries[key] = { count: 1, lastFailure: Date.now() };
    }

    writeStore(store);
  } catch {
    /* fail-open */
  }
}

/**
 * Clear (reset) failure count for a task signature.
 *
 * @param {string} taskSignature - Task identifier (first 80 chars used as key)
 */
function clearFailures(taskSignature) {
  try {
    if (!taskSignature) return;
    const store = readStore();
    const key = taskSignature.slice(0, 80);
    delete store.entries[key];
    writeStore(store);
  } catch {
    /* fail-open */
  }
}

/**
 * Check if Flash is globally unstable across the session.
 *
 * Returns true when Flash has failed on 2+ different task signatures
 * within the expiry window, indicating general instability rather than
 * a single difficult task. This is used to pre-emptively force Pro
 * without requiring the user to see repeated "Invalid tool parameters".
 *
 * @returns {{ unstable: boolean, totalFailures: number, affectedTasks: number }}
 */
function isFlashUnstable() {
  try {
    pruneFailures();
    const store = readStore();
    const entries = Object.values(store.entries).filter(e => e.count > 0);
    const totalFailures = entries.reduce((s, e) => s + e.count, 0);
    const affectedTasks = entries.length;
    return {
      unstable: affectedTasks >= 2,
      totalFailures,
      affectedTasks
    };
  } catch {
    return { unstable: false, totalFailures: 0, affectedTasks: 0 };
  }
}

/**
 * Get total failure count across ALL tasks in current window.
 * @returns {number}
 */
function getGlobalFailureCount() {
  try {
    pruneFailures();
    const store = readStore();
    return Object.values(store.entries).reduce((s, e) => s + e.count, 0);
  } catch {
    return 0;
  }
}

module.exports = {
  recordFailure,
  getFailureCount,
  clearFailures,
  pruneFailures,
  isFlashUnstable,
  getGlobalFailureCount
};
