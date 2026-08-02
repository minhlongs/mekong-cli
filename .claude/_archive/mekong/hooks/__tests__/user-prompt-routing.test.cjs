#!/usr/bin/env node
/**
 * Tests for user-prompt-routing.cjs hook.
 * Run: node --test .claude/hooks/__tests__/user-prompt-routing.test.cjs
 *
 * Tests the UserPromptSubmit hook that analyzes prompts with the model router
 * and injects routing decisions (Flash vs Pro) as additional context.
 */
'use strict';

const { describe, it, before, after } = require('node:test');
const assert = require('node:assert');
const { spawn } = require('node:child_process');
const path = require('node:path');
const fs = require('node:fs');
const os = require('node:os');

const HOOK_PATH = path.join(__dirname, '..', 'user-prompt-routing.cjs');
const ROUTING_LOG = path.join(os.tmpdir(), 'ck-routing-log.jsonl');

/**
 * Execute the hook with given stdin data and return parsed output.
 *
 * @param {Object} inputData - JSON data to pass as stdin
 * @returns {Promise<{stdout: string, stderr: string, exitCode: number}>}
 */
/**
 * Parse JSON Lines file into array of objects.
 *
 * @param {string} filePath - Path to .jsonl file
 * @returns {Array<Object>} Parsed entries
 */
function parseJsonl(filePath) {
  const raw = fs.readFileSync(filePath, 'utf8').trim();
  if (!raw) return [];
  return raw.split('\n')
    .filter(Boolean)
    .map(line => JSON.parse(line));
}

function runHook(inputData) {
  return new Promise((resolve, reject) => {
    const proc = spawn('node', [HOOK_PATH], {
      cwd: path.join(__dirname, '..'),
      env: {
        ...process.env,
        CLAUDE_ENV_FILE: ''
      }
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', chunk => { stdout += chunk; });
    proc.stderr.on('data', chunk => { stderr += chunk; });

    proc.on('close', exitCode => {
      resolve({ stdout: stdout.trim(), stderr: stderr.trim(), exitCode });
    });
    proc.on('error', reject);

    if (inputData) {
      proc.stdin.write(JSON.stringify(inputData));
    }
    proc.stdin.end();
  });
}

// Clean up routing log before and after tests
before(() => {
  try { fs.unlinkSync(ROUTING_LOG); } catch { /* ok */ }
});

after(() => {
  try { fs.unlinkSync(ROUTING_LOG); } catch { /* ok */ }
});

describe('user-prompt-routing.cjs', () => {
  describe('defaults to Flash for simple prompts', () => {
    it('routes read requests to Flash', async () => {
      const result = await runHook({
        prompt: 'Read the file src/index.ts',
        session_id: 'test-1',
        hook_event_name: 'UserPromptSubmit'
      });
      assert.strictEqual(result.exitCode, 0);

      const output = JSON.parse(result.stdout);
      assert.ok(output.hookSpecificOutput);
      assert.strictEqual(output.hookSpecificOutput.hookEventName, 'UserPromptSubmit');
      assert.ok(output.hookSpecificOutput.additionalContext.includes('Flash'));
    });

    it('routes edit requests to Flash', async () => {
      const result = await runHook({
        prompt: 'Update the login form to add email validation',
        session_id: 'test-2',
        hook_event_name: 'UserPromptSubmit'
      });
      assert.strictEqual(result.exitCode, 0);

      const output = JSON.parse(result.stdout);
      assert.ok(output.hookSpecificOutput.additionalContext.includes('Flash'));
    });
  });

  describe('escalates to Pro for complex prompts', () => {
    it('routes architecture requests to Pro', async () => {
      const result = await runHook({
        prompt: 'Design the system architecture with trade-off analysis for our microservices',
        session_id: 'test-3',
        hook_event_name: 'UserPromptSubmit'
      });
      assert.strictEqual(result.exitCode, 0);

      const output = JSON.parse(result.stdout);
      assert.ok(output.hookSpecificOutput.additionalContext.includes('Pro'));
      assert.ok(output.hookSpecificOutput.additionalContext.includes('Architect'));
    });

    it('routes migration requests to Pro', async () => {
      const result = await runHook({
        prompt: 'Create a migration plan to migrate the database schema',
        session_id: 'test-4',
        hook_event_name: 'UserPromptSubmit'
      });
      assert.strictEqual(result.exitCode, 0);

      const output = JSON.parse(result.stdout);
      assert.ok(output.hookSpecificOutput.additionalContext.includes('Pro'));
    });

    it('routes explicit Pro requests to Pro', async () => {
      const result = await runHook({
        prompt: 'Use Pro to review the security architecture',
        session_id: 'test-5',
        hook_event_name: 'UserPromptSubmit'
      });
      assert.strictEqual(result.exitCode, 0);

      const output = JSON.parse(result.stdout);
      assert.ok(output.hookSpecificOutput.additionalContext.includes('Pro'));
    });
  });

  describe('edge cases', () => {
    it('exits gracefully on empty stdin', async () => {
      const result = await runHook(null);
      assert.strictEqual(result.exitCode, 0);
      assert.ok(result.stdout.includes('continue'));
    });

    it('exits gracefully on empty prompt', async () => {
      const result = await runHook({
        prompt: '',
        hook_event_name: 'UserPromptSubmit'
      });
      assert.strictEqual(result.exitCode, 0);
      assert.ok(result.stdout.includes('continue'));
    });
  });

  describe('routing log persistence', () => {
    it('creates routing log on first execution', async () => {
      try { fs.unlinkSync(ROUTING_LOG); } catch { /* ok */ }

      await runHook({
        prompt: 'Fix typo in README.md',
        session_id: 'test-log-1',
        hook_event_name: 'UserPromptSubmit'
      });

      assert.ok(fs.existsSync(ROUTING_LOG), 'Routing log should be created');
      const log = parseJsonl(ROUTING_LOG);
      assert.ok(Array.isArray(log));
      assert.ok(log.length >= 1);
      assert.ok(log[0].tier);
      assert.strictEqual(typeof log[0].score, 'number');
    });

    it('appends to existing routing log', async () => {
      // Log already exists from previous test
      await runHook({
        prompt: 'Design the API endpoints for user management',
        session_id: 'test-log-2',
        hook_event_name: 'UserPromptSubmit'
      });

      assert.ok(fs.existsSync(ROUTING_LOG));
      const log = parseJsonl(ROUTING_LOG);
      assert.ok(log.length >= 2, 'Should have at least 2 entries');
    });
  });
});
