#!/usr/bin/env node
/**
 * Stop checkpoint hook — runs at session end.
 *
 * Emits a concise "did you ship?" reminder to stderr so it appears in the
 * transcript. Non-blocking (exit 0). Lightweight — runs in <100ms.
 */

'use strict';

const { execSync } = require('child_process');

function safe(cmd, dflt = '') {
  try {
    return execSync(cmd, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], timeout: 1500 })
      .trim();
  } catch {
    return dflt;
  }
}

function main() {
  // Uncommitted work check
  const dirty = safe('git status --porcelain 2>/dev/null');
  const branch = safe('git branch --show-current 2>/dev/null');
  const ahead = safe('git rev-list --count @{u}..HEAD 2>/dev/null', '0');

  const dirtyCount = dirty ? dirty.split('\n').filter(Boolean).length : 0;
  const aheadNum = parseInt(ahead || '0', 10);

  const reminders = [];
  if (dirtyCount > 0) {
    reminders.push(`🔸 ${dirtyCount} file(s) modified — consider commit`);
  }
  if (aheadNum > 0) {
    reminders.push(`🔸 ${aheadNum} commit(s) ahead of origin/${branch || 'HEAD'} — consider push`);
  }

  // Open PR check via gh (best-effort, 2s timeout)
  const openPRs = safe(
    `gh pr list --author @me --state open --json number --jq '. | length' 2>/dev/null`,
    ''
  );
  if (openPRs && parseInt(openPRs, 10) > 0) {
    reminders.push(`🔸 ${openPRs} open PR(s) — check CI + merge when green`);
  }

  if (reminders.length === 0) {
    process.stderr.write('✅ Session checkpoint — working tree clean + up to date.\n');
  } else {
    process.stderr.write(
      '\n--- Session checkpoint ---\n' + reminders.join('\n') + '\n-------------------------\n'
    );
  }
  process.exit(0);
}

main();
