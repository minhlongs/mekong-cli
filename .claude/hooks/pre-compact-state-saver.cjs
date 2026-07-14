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

// ── Enhanced: full pre-compact snapshot ──────────────────────────────────
// Writes a structured handoff to pre-compact-handoff.md for post-compact resume.
try {
  const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const handoffDir = path.join(projectDir, '.claude', 'agent-memory');
  fs.mkdirSync(handoffDir, { recursive: true });

  const gitInfo = safeExec('git rev-parse --abbrev-ref HEAD');
  const gitSha = safeExec('git rev-parse --short HEAD');
  const dirtyCount = safeExec('git status --porcelain | wc -l');

  // Collect Task/TodoWrite from hook stdin (tool_use blocks)
  let todos = [];
  let recentDecisions = [];
  try {
    const stdin = fs.readFileSync(0, { encoding: 'utf8', maxLength: 8192 });
    const payload = JSON.parse(stdin);
    const text = JSON.stringify(payload);

    // Extract todos from ToolUseBlock with name=TodoWrite
    const todoRe = /"name":"TodoWrite"\s*,\s*"input":\s*\{[^}]*"todos":\s*(\[[^\]]*\])/g;
    let m = todoRe.exec(text);
    if (m) {
      try { todos = JSON.parse(m[1]).slice(0, 20); } catch { todos = []; }
    }

    // Extract recent user decisions from AskUserQuestion answers
    const decisionRe = /"AskUserQuestion"\s*,\s*"input":\s*\{[^}]*"questions":/g;
    const decisionMatches = text.match(decisionRe);
    if (decisionMatches) {
      recentDecisions = decisionMatches.slice(0, 3).map((_, i) => `[Decision ${i+1}] User responded to a request`);
    }
  } catch { /* stdin unavailable or non-JSON — fine */ }

  const handoff = {
    ts: new Date().toISOString(),
    source: 'pre-compact-saver',
    branch: gitInfo,
    sha: gitSha,
    dirtyFiles: Number(dirtyCount) || 0,
    lastPromptDigest: lastPrompt,
    todos: todos.filter(t => t && t.status !== 'completed'),
    completedTodos: todos.filter(t => t && t.status === 'completed'),
    recentDecisions,
  };

  const handoffPath = path.join(handoffDir, 'pre-compact-handoff.json');
  fs.writeFileSync(handoffPath, JSON.stringify(handoff, null, 2) + '\n');
} catch {
  // Never block compaction — this is best-effort recovery data.
}

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
