#!/usr/bin/env node
/**
 * SessionEnd Hook — append a one-line session record on graceful close.
 *
 * Fires: when the Claude Code session terminates (user exit / crash / idle).
 * Purpose: lightweight local telemetry — duration, working dir, branch,
 *          last sha — written to .claude/agent-memory/session-end.log.
 *          No network calls; observability only.
 *
 * Exit codes:
 *   0 — always; never delay session shutdown.
 *
 * Spec: docs.claude.com/en/docs/claude-code/hooks#sessionend
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

try {
  const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const memDir = path.join(projectDir, '.claude', 'agent-memory');
  fs.mkdirSync(memDir, { recursive: true });

  const branch = safeExec('git rev-parse --abbrev-ref HEAD');
  const sha = safeExec('git rev-parse --short HEAD');

  // Pull session id + reason from stdin payload if Claude Code provides it.
  let sessionId = '';
  let reason = 'unknown';
  try {
    const stdin = fs.readFileSync(0, { encoding: 'utf8', maxLength: 4096 });
    const payload = JSON.parse(stdin);
    sessionId = payload.session_id || payload.sessionId || '';
    reason = payload.reason || payload.exit_reason || 'unknown';
  } catch { /* no stdin — fine */ }

  const line = JSON.stringify({
    ts: new Date().toISOString(),
    sessionId,
    reason,
    cwd: projectDir,
    branch,
    sha,
  });
  fs.appendFileSync(path.join(memDir, 'session-end.log'), line + '\n');

  process.exit(0);
} catch {
  process.exit(0);
}

function safeExec(cmd) {
  try {
    return execSync(cmd, {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore'],
      cwd: process.env.CLAUDE_PROJECT_DIR || process.cwd(),
    }).trim();
  } catch {
    return '';
  }
}
