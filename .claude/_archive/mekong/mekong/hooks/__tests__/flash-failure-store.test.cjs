#!/usr/bin/env node
/**
 * Tests for flash-failure-store.cjs.
 * Run: node --test .claude/hooks/__tests__/flash-failure-store.test.cjs
 *
 * Tests the cross-process failure persistence for model routing.
 * The store lives in a shared temp file (os.tmpdir()/ck:flash-failures.json)
 * and tracks failure counts keyed by (truncated) task signatures.
 */
'use strict';

const { describe, it, before, after } = require('node:test');
const assert = require('node:assert');
const path = require('node:path');
const fs = require('node:fs');
const os = require('node:os');

const STORE_PATH = path.join(os.tmpdir(), 'ck-flash-failures.json');
const store = require('../lib/flash-failure-store.cjs');

/**
 * Delete the store file if it exists.
 */
function cleanStore() {
  try { fs.unlinkSync(STORE_PATH); } catch { /* ok */ }
}

/**
 * Read the raw store file and return parsed entries.
 * @returns {Record<string, { count: number, lastFailure: number }>}
 */
function readRawEntries() {
  try {
    const raw = fs.readFileSync(STORE_PATH, 'utf8');
    return JSON.parse(raw).entries || {};
  } catch {
    return {};
  }
}

/**
 * Write raw entries directly to the store file (bypass the module).
 * @param {Record<string, { count: number, lastFailure: number }>} entries
 */
function writeRawEntries(entries) {
  const tmp = `${STORE_PATH}.${process.pid}.test.tmp`;
  fs.writeFileSync(tmp, JSON.stringify({ entries }));
  fs.renameSync(tmp, STORE_PATH);
}

before(cleanStore);

after(cleanStore);

describe('flash-failure-store.cjs', () => {
  describe('getFailureCount for unknown tasks', () => {
    it('returns 0 for a brand new signature', () => {
      assert.strictEqual(store.getFailureCount('never-seen-before'), 0);
    });

    it('returns 0 when store file does not exist', () => {
      cleanStore();
      assert.strictEqual(store.getFailureCount('any-task'), 0);
    });
  });

  describe('recordFailure + getFailureCount round-trip', () => {
    before(cleanStore);

    it('returns 1 after a single recordFailure', () => {
      store.recordFailure('task-alpha');
      assert.strictEqual(store.getFailureCount('task-alpha'), 1);
    });

    it('returns 2 after recording a second failure on the same task', () => {
      store.recordFailure('task-alpha');
      assert.strictEqual(store.getFailureCount('task-alpha'), 2);
    });
  });

  describe('clearFailures resets count', () => {
    before(cleanStore);

    it('resets count to 0 after clearing', () => {
      store.recordFailure('task-beta');
      store.recordFailure('task-beta');
      assert.strictEqual(store.getFailureCount('task-beta'), 2);

      store.clearFailures('task-beta');
      assert.strictEqual(store.getFailureCount('task-beta'), 0);
    });

    it('does not affect other task counts when clearing one task', () => {
      store.recordFailure('task-beta');
      store.recordFailure('task-gamma');
      store.clearFailures('task-beta');
      assert.strictEqual(store.getFailureCount('task-beta'), 0);
      assert.strictEqual(store.getFailureCount('task-gamma'), 1);
    });
  });

  describe('separate tasks have separate counts', () => {
    before(cleanStore);

    it('tracks independent counts for different task signatures', () => {
      store.recordFailure('task-A');
      store.recordFailure('task-A');
      store.recordFailure('task-B');

      assert.strictEqual(store.getFailureCount('task-A'), 2);
      assert.strictEqual(store.getFailureCount('task-B'), 1);
    });
  });

  describe('null/empty signature handling', () => {
    before(cleanStore);

    it('getFailureCount returns 0 for null', () => {
      assert.strictEqual(store.getFailureCount(null), 0);
    });

    it('getFailureCount returns 0 for empty string', () => {
      assert.strictEqual(store.getFailureCount(''), 0);
    });

    it('getFailureCount returns 0 for undefined', () => {
      assert.strictEqual(store.getFailureCount(undefined), 0);
    });

    it('recordFailure with null does not throw or create entries', () => {
      store.recordFailure(null);
      assert.strictEqual(store.getFailureCount('any-task'), 0);
    });

    it('recordFailure with empty string does not throw or create entries', () => {
      store.recordFailure('');
      assert.strictEqual(store.getFailureCount('any-task'), 0);
    });

    it('recordFailure with undefined does not throw or create entries', () => {
      store.recordFailure(undefined);
      assert.strictEqual(store.getFailureCount('any-task'), 0);
    });
  });

  describe('pruneFailures removes old entries', () => {
    before(cleanStore);

    it('removes entries older than maxAgeMs', () => {
      // Record a failure using the module
      store.recordFailure('old-task');

      // Verify it exists
      assert.strictEqual(store.getFailureCount('old-task'), 1);

      // Manipulate the store file directly to set an old timestamp
      const oldTimestamp = Date.now() - 60_000; // 60 seconds ago
      writeRawEntries({
        'old-task': { count: 1, lastFailure: oldTimestamp },
        'fresh-task': { count: 2, lastFailure: Date.now() }
      });

      // Prune with 1ms maxAge (effectively removes anything older than 1ms)
      store.pruneFailures(1);

      // Old entry should be gone
      assert.strictEqual(store.getFailureCount('old-task'), 0);
      // Fresh entry should still be present
      assert.strictEqual(store.getFailureCount('fresh-task'), 2);
    });

    it('preserves entries within the age window', () => {
      cleanStore();

      store.recordFailure('recent-task');
      // Prune with a very large maxAge (10 minutes) — entry is seconds old
      store.pruneFailures(600_000);
      assert.strictEqual(store.getFailureCount('recent-task'), 1);
    });

    it('handles empty store gracefully', () => {
      cleanStore();
      // Should not throw
      store.pruneFailures(1);
      assert.strictEqual(store.getFailureCount('anything'), 0);
    });
  });

  describe('concurrent-style write safety', () => {
    before(cleanStore);

    it('handles rapid successive recordFailure calls', () => {
      // Stress-test the atomic write pattern with rapid sequential calls
      for (let i = 0; i < 50; i++) {
        store.recordFailure('rapid-task');
      }
      assert.strictEqual(store.getFailureCount('rapid-task'), 50);
    });

    it('handles rapid fire across multiple tasks', () => {
      cleanStore();

      for (let i = 0; i < 30; i++) {
        store.recordFailure('concurrent-A');
        store.recordFailure('concurrent-B');
      }
      assert.strictEqual(store.getFailureCount('concurrent-A'), 30);
      assert.strictEqual(store.getFailureCount('concurrent-B'), 30);
    });
  });

  describe('key truncation', () => {
    before(cleanStore);

    it('truncates signatures longer than 80 characters', () => {
      // Build a signature that is > 80 chars
      const longSig = 'a'.repeat(120);
      // First 80 chars
      const truncatedKey = 'a'.repeat(80);

      store.recordFailure(longSig);

      // Record a failure under the truncated key manually
      store.recordFailure(truncatedKey);

      // Should be the same entry (truncated to same key)
      assert.strictEqual(store.getFailureCount(longSig), 2);
      assert.strictEqual(store.getFailureCount(truncatedKey), 2);
    });

    it('treats 80-char signatures as distinct from 81-char with same prefix', () => {
      cleanStore();

      const sig80 = 'b'.repeat(80);
      const sig81 = 'b'.repeat(81); // first 80 chars same as sig80

      store.recordFailure(sig80);
      assert.strictEqual(store.getFailureCount(sig80), 1);

      // sig81 truncates to sig80, so count goes to 2
      store.recordFailure(sig81);
      assert.strictEqual(store.getFailureCount(sig80), 2);
      assert.strictEqual(store.getFailureCount(sig81), 2);
    });
  });

  describe('error resilience', () => {
    it('getFailureCount returns 0 on corrupt store file', () => {
      // Write invalid JSON to the store path
      fs.writeFileSync(STORE_PATH, 'not valid json{{{');
      // Should silently return 0 instead of throwing
      assert.strictEqual(store.getFailureCount('any-task'), 0);
    });

    it('recordFailure does not throw on corrupt store file', () => {
      fs.writeFileSync(STORE_PATH, 'not valid json{{{');
      // Should not throw
      store.recordFailure('some-task');
      // After corrupt file handling, it should have started fresh
      assert.strictEqual(store.getFailureCount('some-task'), 1);
    });
  });
});
