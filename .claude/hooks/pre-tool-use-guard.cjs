#!/usr/bin/env node
/**
 * PreToolUse guard — blocks dangerous bash ops before they execute.
 *
 * Reads tool input JSON from stdin. Emits block message to stderr + exits 1
 * when a blocked pattern is detected; otherwise exits 0.
 *
 * Matches Mekong PUBLIC repo boundary + binh-phap-cicd.md safety rules.
 */

'use strict';

const DANGER_PATTERNS = [
  // Filesystem nukes
  { re: /rm\s+(-[rfRF]+\s+)?(\/|~\s|\/\*|\$HOME\s*\/?\*?)\s*$/, msg: 'refusing rm on root/$HOME — specify precise path' },
  { re: /rm\s+-[rfRF]+\s+--no-preserve-root/, msg: 'refusing rm --no-preserve-root' },
  { re: /:\(\)\s*\{\s*:\|:&\s*\}\s*;:/, msg: 'refusing fork-bomb pattern' },
  // Git destructive on protected branches
  { re: /git\s+push\s+(--force|-f)\b.*\b(origin\s+)?(main|master)\b/, msg: 'refusing force-push to main/master — use feat branch + PR' },
  { re: /git\s+push\s+(--force|-f)\b.*\b(origin\s+)?(main|master)\b/, msg: 'refusing force-push to main/master' },
  { re: /git\s+reset\s+--hard\b.*\b(HEAD~[5-9]|HEAD~\d{2,})/, msg: 'refusing hard-reset > 4 commits — confirm with user first' },
  // SQL mass mutate
  { re: /\bDROP\s+(TABLE|DATABASE|SCHEMA)\b/i, msg: 'refusing DROP TABLE/DATABASE/SCHEMA — confirm with user first' },
  { re: /\bTRUNCATE\s+TABLE\b/i, msg: 'refusing TRUNCATE — confirm with user first' },
  // Piping untrusted to shell
  { re: /curl\s+[^|]+\|\s*(bash|sh|zsh)\b/, msg: 'refusing curl|bash — download + inspect before execute' },
  // Chmod on system paths
  { re: /chmod\s+(-R\s+)?777\s+(\/|\/usr|\/etc|\/var)/, msg: 'refusing chmod 777 on system paths' },
  // Mekong PUBLIC repo boundary (per CLAUDE.md)
  { re: /git\s+add\s+(apps\/|mekong\/daemon\/|mekong\/hooks\/|\.env\b|\.env\s|\.env$)/, msg: 'refusing to stage apps/ or mekong/daemon/ or .env — PUBLIC repo boundary' },
  { re: /git\s+commit\s+.*--no-verify/, msg: 'refusing --no-verify — fix pre-commit hook instead' },
  // Vercel (banned per memory)
  { re: /\bvercel\s+(deploy|--prod|--force)\b/, msg: 'Vercel BANNED (2026-03-27) — use Cloudflare Pages: git push origin main' },
];

let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (c) => (input += c));
process.stdin.on('end', () => {
  let toolInput;
  try {
    const payload = JSON.parse(input || '{}');
    toolInput = payload.tool_input || payload.input || {};
  } catch {
    process.exit(0); // malformed → non-blocking
  }

  const cmd = String(toolInput.command || '');
  if (!cmd) return process.exit(0);

  for (const { re, msg } of DANGER_PATTERNS) {
    if (re.test(cmd)) {
      process.stderr.write(
        JSON.stringify({
          decision: 'block',
          reason: `🚨 PreToolUse guard: ${msg}\n\nCommand: ${cmd.slice(0, 200)}`,
        }) + '\n'
      );
      process.exit(2); // exit 2 = block tool execution (per Claude Code hook spec)
    }
  }
  process.exit(0);
});
