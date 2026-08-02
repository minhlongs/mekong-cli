#!/usr/bin/env node
/**
 * brainstorm-vn-inject.cjs — Khi /brainstorm thì auto reply Tiếng Việt
 * Hook: UserPromptSubmit
 */
'use strict';
const prompt = (process.argv[2] || '').toLowerCase();
if (prompt.includes('brainstorm') || prompt.includes('bàn luận') || prompt.includes('thảo luận')) {
  process.stdout.write('\n⚠️ LANGUAGE: Reply in Vietnamese (Tiếng Việt) for this brainstorm session. Other sessions: English.\n');
}
