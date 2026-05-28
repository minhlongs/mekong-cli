#!/usr/bin/env node
/**
 * PreCompact Hook — persist a tiny state snapshot before Claude Code
 * compacts the conversation context.
 *
 * Fires: just before context compaction (manual /compact or auto).
 * Purpose: write a one-line breadcrumb to .claude/agent-memory/pre-compact.log
 *          so the post-compact session can resume with a hint of what was
 *          in flight (active branch, last commit, last user message digest).
 *
 * Exit codes:
 *   0 — never block compaction; this is observability-only.
 *
 * Spec: docs.claude.com/en/docs/claude-code/hooks#precompact
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
  const dirty = safeExec('git status --porcelain | wc -l').trim();

  // Read incoming hook payload (first 4KB is enough for a digest)
  let lastPrompt = '';
  try {
    const stdin = fs.readFileSync(0, { encoding: 'utf8', maxLength: 4096 });
    const payload = JSON.parse(stdin);
    lastPrompt = (payload.lastUserMessage || payload.summary || '').slice(0, 200);
  } catch { /* no stdin or non-JSON — fine */ }

  const line = JSON.stringify({
    ts: new Date().toISOString(),
    branch,
    sha,
    dirtyFiles: Number(dirty) || 0,
    lastPromptDigest: lastPrompt,
  });
  fs.appendFileSync(path.join(memDir, 'pre-compact.log'), line + '\n');

  // Stay silent on success; Claude Code prefers quiet hooks.
  process.exit(0);
} catch {
  // Never block compaction on hook failure.
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
